"""Verification primitives that keep working with no network call on the request path.

* :class:`KeyMirror` -- a local, authoritative mirror of end-user API keys (``ak_``).
* :class:`ResourceRoleMirror` -- resource-scoped role assignments, answered with the server's rules.
* :class:`SidRevocationList` / :class:`EdgeRevocationChecker` -- which session ids Atlas has revoked.
* :func:`verify_and_dedupe` -- verify an Atlas webhook and drop a delivery id seen before.
* :func:`verify_transaction_token` -- a Transaction Token (draft-ietf-oauth-transaction-tokens).

Each takes the sync :class:`~atlas_backend.AtlasClient` namespace it needs (so you can pass a fake in a
test) and a small store protocol with an in-memory implementation. Run ``sync()`` from a timer; from an
event loop use ``await asyncio.to_thread(mirror.sync)``.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import threading
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from ._transport import DEFAULT_BASE_URL
from ._verify import SIGNING_ALGS, JwksCache, _b64url_decode, jwk_public_key
from ._webhooks import WebhookVerification, verify_standard_webhook, verify_webhook


def _now_ms() -> int:
    return int(time.time() * 1000)


# --------------------------------------------------------------------------------------------
# End-user API key mirror
# --------------------------------------------------------------------------------------------


def hash_api_key_secret(secret: str) -> str:
    """sha256 hex of the full secret: the hash the mirror stores and Atlas imports as ``sha256_hex``."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class KeyMirrorStore(Protocol):
    """What the mirror keeps per key (a dict with ``id``, ``hash``, ``prefix``, ``subject_type``,
    ``subject_id``, ``name``, ``scopes``, ``allowed_ips``, ``expires_at``, ``revoked_at``,
    ``organization_id``, ``revoked_reason``); never the secret."""

    def put(self, key: dict[str, Any]) -> None: ...
    def get(self, key_id: str) -> dict[str, Any] | None: ...
    def get_by_hash(self, hash: str) -> dict[str, Any] | None: ...
    def mark_revoked(self, key_id: str, revoked_at: int, reason: str | None = None) -> None: ...
    def mark_membership_ended(self, user_id: str, organization_id: str, revoked_at: int) -> None: ...
    def get_cursor(self) -> str | None: ...
    def set_cursor(self, cursor: str) -> None: ...
    def get_last_sync_at(self) -> int | None: ...
    def set_last_sync_at(self, at: int) -> None: ...


class MemoryKeyMirrorStore:
    """An in-memory :class:`KeyMirrorStore` for tests and single-process apps."""

    def __init__(self) -> None:
        self.keys: dict[str, dict[str, Any]] = {}
        self._cursor: str | None = None
        self._last_sync: int | None = None
        self._lock = threading.Lock()

    def put(self, key: dict[str, Any]) -> None:
        with self._lock:
            self.keys[key["id"]] = dict(key)

    def get(self, key_id: str) -> dict[str, Any] | None:
        return self.keys.get(key_id)

    def get_by_hash(self, hash: str) -> dict[str, Any] | None:
        with self._lock:
            return next((k for k in self.keys.values() if k["hash"] == hash), None)

    def mark_revoked(self, key_id: str, revoked_at: int, reason: str | None = None) -> None:
        with self._lock:
            k = self.keys.get(key_id)
            if k and k.get("revoked_at") is None:
                k["revoked_at"] = revoked_at
                if reason:
                    k["revoked_reason"] = reason

    def mark_membership_ended(self, user_id: str, organization_id: str, revoked_at: int) -> None:
        with self._lock:
            for k in self.keys.values():
                if (
                    k.get("revoked_at") is None
                    and k.get("subject_type") == "user"
                    and k.get("subject_id") == user_id
                    and k.get("organization_id") == organization_id
                ):
                    k["revoked_at"] = revoked_at
                    k["revoked_reason"] = "membership_ended"

    def get_cursor(self) -> str | None:
        return self._cursor

    def set_cursor(self, cursor: str) -> None:
        self._cursor = cursor

    def get_last_sync_at(self) -> int | None:
        return self._last_sync

    def set_last_sync_at(self, at: int) -> None:
        self._last_sync = at


def _expand(held: Sequence[str], implications: Mapping[str, Sequence[str]], allowed: Sequence[str]) -> list[str]:
    vocab = set(allowed)
    for frm, tos in implications.items():
        vocab.add(frm)
        vocab.update(t for t in tos if t != "*")
    out = set(held)
    queue = list(held)
    while queue:
        for to in implications.get(queue.pop(), ()):
            for t in vocab if to == "*" else (to,):
                if t not in out:
                    out.add(t)
                    queue.append(t)
    return sorted(out)


def ip_in_allowlist(ip: str, cidrs: Iterable[str]) -> bool:
    """Whether ``ip`` is inside one of the addresses / CIDR ranges. Unparseable input is never inside."""
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False
    for entry in cidrs:
        try:
            net = ipaddress.ip_network(entry.strip(), strict=False)
        except ValueError:
            continue
        if net.version == addr.version and addr in net:
            return True
    return False


def permission_covers_scope(permission: str, scope: str) -> bool:
    """Whether a permission covers a key scope: same name, ``*``, or ``<prefix>:*``."""
    if permission in (scope, "*"):
        return True
    return permission.endswith(":*") and scope.startswith(permission[:-1])


def intersect_scopes_with_permissions(scopes: Iterable[str], permissions: Sequence[str]) -> list[str]:
    return sorted({s for s in scopes if any(permission_covers_scope(p, s) for p in permissions)})


def _mirrored(key: Mapping[str, Any], hash: str) -> dict[str, Any]:
    return {
        "id": key["id"],
        "hash": hash,
        "prefix": key.get("prefix"),
        "subject_type": key.get("subject_type"),
        "subject_id": key.get("subject_id"),
        "name": key.get("name"),
        "scopes": key.get("scopes"),
        "allowed_ips": key.get("allowed_ips"),
        "expires_at": key.get("expires_at"),
        "revoked_at": key.get("revoked_at"),
        "organization_id": key.get("organization_id"),
        "revoked_reason": key.get("revoked_reason"),
    }


@dataclass
class KeyVerification:
    """``valid`` plus, when valid, the mirrored ``key`` and ``effective_scopes``. Otherwise ``code`` may be
    ``insufficient_scope`` (with ``missing_scopes``), ``ip_not_allowed``, ``client_ip_required``,
    ``membership_unresolved`` or ``stale`` (the mirror is not fresh enough to answer: retry after ``sync()``)."""

    valid: bool
    key: dict[str, Any] | None = None
    effective_scopes: list[str] = field(default_factory=list)
    code: str | None = None
    missing_scopes: list[str] = field(default_factory=list)
    #: A bound key: the membership the scopes were narrowed by.
    organization: dict[str, Any] | None = None
    #: True when the answer came from the last synced data inside ``serve_stale_for_ms``.
    stale: bool = False
    last_sync_at: int | None = None


class KeyMirror:
    """A local mirror of end-user API keys with Atlas as the minting and revocation backstop.

    Your request path verifies a presented key against the LOCAL row (sha256 hash, scopes, expiry,
    revocation) with no network call. Revoking locally happens FIRST, so a failed Atlas call never
    leaves a key usable here. A revoke made anywhere else reaches the mirror through :meth:`sync`
    (the ``/v1/api_keys/revoked`` feed) or :meth:`apply_webhook`.

    Args:
        store: a :class:`KeyMirrorStore` (default :class:`MemoryKeyMirrorStore`).
        api_keys: ``client.api_keys`` (create, revoke, list_revoked; verify / get / rotate optional).
        scope_implications / allowed_scopes: ``auth_config.endUserApiKeys`` so a local scope check
            matches Atlas verify (``*`` = every scope).
        verify_at_atlas: on a local miss ask Atlas (needed for imported bcrypt / argon2id keys).
        max_staleness_ms: when set, ``verify`` answers ``code="stale"`` if the last ``sync()`` is older.
        serve_stale_for_ms / on_serve_stale: keep answering that much longer past the bound, flagged ``stale``.
        membership: ``(user_id, organization_id) -> {"permissions": [...]} | None`` for bound keys.
    """

    def __init__(
        self,
        *,
        api_keys: Any,
        store: KeyMirrorStore | None = None,
        scope_implications: Mapping[str, Sequence[str]] | None = None,
        allowed_scopes: Sequence[str] = (),
        verify_at_atlas: bool = False,
        max_staleness_ms: int | None = None,
        serve_stale_for_ms: int = 0,
        on_serve_stale: Callable[[dict[str, Any]], None] | None = None,
        membership: Callable[[str, str], Mapping[str, Any] | None] | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self.store: KeyMirrorStore = store or MemoryKeyMirrorStore()
        self.api_keys = api_keys
        self._implications = dict(scope_implications or {})
        self._allowed = list(allowed_scopes)
        self._verify_at_atlas = verify_at_atlas
        self._max_staleness = max_staleness_ms
        self._serve_stale = serve_stale_for_ms
        self._on_serve_stale = on_serve_stale
        self._membership = membership
        self._now = now or _now_ms

    def last_sync_at(self) -> int | None:
        """Epoch ms of the last completed :meth:`sync`; ``None`` = never."""
        return self.store.get_last_sync_at()

    def mint(self, body: dict[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
        """Mint at Atlas, then mirror it. Returns the key with its one-time ``secret``."""
        created = self.api_keys.create(body, idempotency_key=idempotency_key)
        self.store.put(_mirrored(created, hash_api_key_secret(created["secret"])))
        return created

    def rotate(self, key_id: str, body: dict[str, Any] | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        """Rotate at Atlas, then mirror both sides: the successor is added, the old key ends at the end of the overlap."""
        rotated = self.api_keys.rotate(key_id, body or {}, idempotency_key=idempotency_key)
        self.store.put(_mirrored(rotated, hash_api_key_secret(rotated["secret"])))
        old = self.store.get(key_id)
        if old:
            prev = rotated.get("previous_key") or {}
            if prev.get("revoked"):
                self.store.mark_revoked(key_id, self._now(), "rotated")
            else:
                self.store.put({**old, "expires_at": prev.get("expires_at", old.get("expires_at"))})
        return rotated

    def import_key(
        self,
        *,
        prefix: str,
        secret: str | None = None,
        secret_hash: str | None = None,
        bcrypt_hash: str | None = None,
        argon2id_hash: str | None = None,
        idempotency_key: str | None = None,
        **rest: Any,
    ) -> dict[str, Any]:
        """Import an existing key by its sha256 (hex) so customers keep their secret."""
        legacy = bcrypt_hash or argon2id_hash
        if legacy:
            imported = self.api_keys.create(
                {**rest, "import": {"secret_hash": legacy, "hash_algorithm": "bcrypt" if bcrypt_hash else "argon2id", "prefix": prefix}},
                idempotency_key=idempotency_key,
            )
            # No local sha256 yet: verify (with verify_at_atlas) fills it in on first use.
            if imported.get("outcome") != "already_present" or not self.store.get(imported["id"]):
                self.store.put(_mirrored(imported, f"legacy:{imported['id']}"))
            return {**imported, "outcome": imported.get("outcome", "created")}
        digest = secret_hash.lower() if secret_hash else (hash_api_key_secret(secret) if secret is not None else None)
        if not digest or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("import_key needs the full `secret` or its `secret_hash` (64 lowercase hex characters of sha256).")
        imported = self.api_keys.create(
            {**rest, "import": {"secret_hash": digest, "hash_algorithm": "sha256_hex", "prefix": prefix}},
            idempotency_key=idempotency_key,
        )
        self.store.put(_mirrored(imported, digest))
        return {**imported, "outcome": imported.get("outcome", "created")}

    def revoke(self, key_id: str) -> None:
        """Revoke LOCALLY first (the key stops working here at once), then at Atlas. A key Atlas already
        revoked or no longer knows (404 / 409) counts as revoked; any other Atlas error is raised after the local revoke."""
        self.store.mark_revoked(key_id, self._now())
        try:
            self.api_keys.revoke(key_id)
        except Exception as e:
            if getattr(e, "status", None) not in (404, 409):
                raise

    def verify(self, secret: str, *, required_scopes: Sequence[str] = (), client_ip: str | None = None) -> KeyVerification:
        """Verify a presented secret against the mirror: no network call (unless ``verify_at_atlas``)."""
        if not isinstance(secret, str) or not secret:
            return KeyVerification(False)
        served_stale = False
        if self._max_staleness is not None:
            at = self.last_sync_at()
            behind = float("inf") if at is None else self._now() - at - self._max_staleness
            if behind > 0:
                if at is None or behind > self._serve_stale:
                    return KeyVerification(False, code="stale", last_sync_at=at)
                served_stale = True
                if self._on_serve_stale:
                    self._on_serve_stale({"last_sync_at": at, "stale_for_ms": behind})
        digest = hash_api_key_secret(secret)
        key = self.store.get_by_hash(digest)
        ip_arg = {"client_ip": client_ip} if client_ip else {}
        if key is None and self._verify_at_atlas:
            remote = self.api_keys.verify({"secret": secret, **ip_arg})
            if remote.get("valid"):
                key = _mirrored(self.api_keys.get(remote["id"]), digest)
                self.store.put(key)
        if key is None or key.get("revoked_at") is not None:
            return KeyVerification(False)
        if key.get("expires_at") is not None and key["expires_at"] <= self._now():
            return KeyVerification(False)
        if key.get("allowed_ips"):
            if not client_ip:
                return KeyVerification(False, code="client_ip_required")
            if not ip_in_allowlist(client_ip, key["allowed_ips"]):
                return KeyVerification(False, code="ip_not_allowed")
        effective = _expand(key.get("scopes") or [], self._implications, self._allowed)
        organization: dict[str, Any] | None = None
        if key.get("subject_type") == "user" and key.get("organization_id"):
            # A bound key stands for the user's CURRENT membership; never answer from the key's own scopes.
            if self._membership:
                held = self._membership(key["subject_id"], key["organization_id"])
                if not held:
                    return KeyVerification(False)
                organization = dict(held)
                effective = intersect_scopes_with_permissions(effective, held.get("permissions", []))
            elif hasattr(self.api_keys, "verify"):
                remote = self.api_keys.verify({"secret": secret, **ip_arg})
                if not remote.get("valid") or not remote.get("organization"):
                    return KeyVerification(False)
                organization = remote["organization"]
                effective = list(remote.get("effective_scopes") or [])
            else:
                return KeyVerification(False, code="membership_unresolved")
        missing = [s for s in required_scopes if s not in effective]
        if missing:
            return KeyVerification(False, code="insufficient_scope", missing_scopes=missing)
        return KeyVerification(True, key=key, effective_scopes=effective, organization=organization, stale=served_stale)

    def sync(self) -> int:
        """Consume the revocation feed from the stored cursor, revoking each listed key locally.
        Call it on a timer (every few seconds to a minute). Returns how many ids it applied."""
        since = self.store.get_cursor()
        revoked = 0
        while True:
            page = self.api_keys.list_revoked(**({"since": since} if since else {}), limit=100)
            for ref in page.get("data", []):
                self.store.mark_revoked(ref["id"], ref.get("revoked_at") or self._now(), ref.get("revoked_reason"))
                revoked += 1
            cursor = page.get("next_cursor")
            if cursor:
                since = cursor
                self.store.set_cursor(cursor)
            if not page.get("has_more") or not cursor:
                self.store.set_last_sync_at(self._now())
                return revoked

    def apply_webhook(self, event: Mapping[str, Any]) -> bool:
        """Apply a VERIFIED ``api_key.*`` (or ``organization_membership.deleted``) webhook event. Returns
        whether it changed the mirror."""
        etype = event.get("type") if isinstance(event, Mapping) else None
        data = event.get("data") if isinstance(event, Mapping) else None
        if not isinstance(etype, str) or not isinstance(data, Mapping):
            return False
        if etype in ("organization_membership.deleted", "organizationMembership.deleted"):
            uid, oid = data.get("user_id"), data.get("organization_id")
            if isinstance(uid, str) and isinstance(oid, str):
                self.store.mark_membership_ended(uid, oid, self._now())
                return True
            return False
        if not etype.startswith("api_key.") or not isinstance(data.get("id"), str):
            return False
        held = self.store.get(data["id"])
        if not held:
            return False
        if etype == "api_key.restored":
            if held.get("revoked_at") is None:
                return False
            self.store.put({**held, "revoked_at": None, "revoked_reason": None, "expires_at": data.get("expires_at", held.get("expires_at"))})
            return True
        if etype == "api_key.revoked" or (isinstance(data.get("revoked_at"), int) and held.get("revoked_at") is None):
            at = data["revoked_at"] if isinstance(data.get("revoked_at"), int) else self._now()
            self.store.mark_revoked(held["id"], at, data.get("revoked_reason"))
            return True
        if etype in ("api_key.updated", "api_key.created"):
            self.store.put(
                {**held, **{k: data[k] for k in ("name", "scopes", "allowed_ips", "expires_at") if k in data}}
            )
            return True
        return False


# --------------------------------------------------------------------------------------------
# Resource-role mirror
# --------------------------------------------------------------------------------------------

_MAX_DEPTH = 16  # the server's ancestor-walk cap


def _role_permissions(roles: Sequence[Mapping[str, Any]], role_key: str, seen: set[str] | None = None) -> set[str]:
    seen = set() if seen is None else seen
    if role_key in seen:
        return set()
    seen.add(role_key)
    role = next((r for r in roles if r.get("key") == role_key), None)
    if role is None:
        return set()
    out = set(role.get("permissions", []))
    for inc in role.get("includes") or []:
        out |= _role_permissions(roles, inc, seen)
    return out


def resolve_mirror_grants(
    chain: Sequence[Mapping[str, Any]], subjects: Iterable[str], permission: str
) -> list[dict[str, Any]]:
    """The server's ``resolveResourceGrants`` over a chain of ``{resource_id, type: {inherit, roles},
    assignments: [{subject, role, inherit}]}`` links, resource first."""
    held = set(subjects)
    grants: list[dict[str, Any]] = []
    for i, link in enumerate(chain):
        for a in link["assignments"]:
            if a["subject"] not in held or (i > 0 and not a["inherit"]):
                continue
            perms = _role_permissions(link["type"]["roles"], a["role"])
            if permission in perms or "*" in perms:
                grants.append({"resource_id": link["resource_id"], "role": a["role"], "subject": a["subject"], "inherited": i > 0})
        # The next link up is only reachable when this resource's type inherits.
        if not link["type"]["inherit"]:
            break
    return grants


class MemoryResourceRoleStore:
    """An in-memory store for the resource-role mirror (types, tree, assignments, cursor)."""

    def __init__(self) -> None:
        self.assignments: dict[str, dict[str, Any]] = {}
        self.resources: dict[str, dict[str, Any]] = {}
        self.types: dict[str, dict[str, Any]] = {}
        self.cursor: str | None = None
        self.last_sync_at: int | None = None

    def get_resource(self, ref: Mapping[str, str]) -> dict[str, Any] | None:
        if "id" in ref:
            return self.resources.get(ref["id"])
        return next(
            (r for r in self.resources.values() if r["type"] == ref.get("type") and r["external_id"] == ref.get("external_id")),
            None,
        )

    def assignments_on(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        want = set(ids)
        return [a for a in self.assignments.values() if a["resource_id"] in want]

    def apply_changes(self, changes: Iterable[tuple[str, dict[str, Any]]]) -> None:
        for change, a in changes:
            if change == "deleted":
                self.assignments.pop(a["id"], None)
            else:
                self.assignments[a["id"]] = a


class ResourceRoleMirror:
    """A local mirror of resource-scoped role assignments, so ``can(user, permission, resource)`` is answered
    with no network call and the SAME inheritance rules as ``POST /v1/resource_checks``.

    ``sync()`` pulls the types and the tree, then consumes ``GET /v1/resource_role_assignments/changes``
    from the stored cursor. ``apply_webhook()`` applies the ``resource_role_assignment.created`` /
    ``.deleted`` events between syncs. Atlas adds the user's organizations and groups itself; offline you
    pass them: ``can(..., orgs=[...], groups=[...])``.

    Args:
        client: an :class:`~atlas_backend.AtlasClient` (uses ``resources.types.list``, ``resources.list`` and
            ``resource_role_assignments.list_changes``).
        max_staleness_ms / serve_stale_for_ms / on_serve_stale: as on :class:`KeyMirror`.
        tree_refresh_ms: re-pull the types and tree only when this long has passed since the last pull.
    """

    def __init__(
        self,
        *,
        client: Any,
        store: MemoryResourceRoleStore | None = None,
        max_staleness_ms: int | None = None,
        serve_stale_for_ms: int = 0,
        on_serve_stale: Callable[[dict[str, Any]], None] | None = None,
        tree_refresh_ms: int = 0,
        now: Callable[[], int] | None = None,
    ) -> None:
        self.store = store or MemoryResourceRoleStore()
        self._client = client
        self._max_staleness = max_staleness_ms
        self._serve_stale = serve_stale_for_ms
        self._on_serve_stale = on_serve_stale
        self._tree_refresh = tree_refresh_ms
        self._now = now or _now_ms
        self._tree_at: int | None = None

    def _chain(self, resource: dict[str, Any]) -> list[dict[str, Any]]:
        ancestors: list[dict[str, Any]] = []
        pid = resource.get("parent_id")
        for _ in range(_MAX_DEPTH):
            if not pid:
                break
            row = self.store.get_resource({"id": pid})
            if not row or any(r["id"] == row["id"] for r in ancestors):
                break
            ancestors.append(row)
            pid = row.get("parent_id")
        rows = [resource, *ancestors]
        assigns = self.store.assignments_on(r["id"] for r in rows)
        chain = []
        for r in rows:
            t = self.store.types.get(r["type"])
            chain.append(
                {
                    "resource_id": r["id"],
                    "type": {"inherit": t["inherit"] if t else True, "roles": t["roles"] if t else []},
                    "assignments": [
                        {"subject": a["subject"], "role": a["role"], "inherit": a["inherit"]}
                        for a in assigns
                        if a["resource_id"] == r["id"]
                    ],
                }
            )
        return chain

    def check(
        self,
        subject: Mapping[str, str],
        permission: str,
        resource: Mapping[str, str],
        *,
        orgs: Iterable[str] = (),
        groups: Iterable[str] = (),
    ) -> dict[str, Any]:
        """The verdict and the grants behind it, in the shape of ``POST /v1/resource_checks``.
        ``subject`` is ``{"type": "user", "id": ...}``; ``resource`` is ``{"id"}`` or ``{"type", "external_id"}``.
        ``code`` is ``unknown_resource`` or ``stale``."""
        served_stale = False
        if self._max_staleness is not None:
            at = self.store.last_sync_at
            behind = float("inf") if at is None else self._now() - at - self._max_staleness
            if behind > 0:
                if at is None or behind > self._serve_stale:
                    return {"allowed": False, "resource_id": None, "grants": [], "code": "stale"}
                served_stale = True
                if self._on_serve_stale:
                    self._on_serve_stale({"last_sync_at": at, "stale_for_ms": behind})
        row = self.store.get_resource(resource)
        if not row or not isinstance(permission, str) or not permission:
            out: dict[str, Any] = {"allowed": False, "resource_id": row["id"] if row else None, "grants": []}
            if not row:
                out["code"] = "unknown_resource"
            return out
        subjects = {f"{subject['type']}:{subject['id']}"}
        subjects |= {f"group:{g}" for g in groups}
        subjects |= {f"org:{o}" for o in orgs}
        grants = resolve_mirror_grants(self._chain(row), subjects, permission)
        out = {"allowed": bool(grants), "resource_id": row["id"], "grants": grants}
        if served_stale:
            out["stale"] = True
        return out

    def can(self, subject: Mapping[str, str], permission: str, resource: Mapping[str, str], **kwargs: Any) -> bool:
        """May ``subject`` hold ``permission`` on ``resource``? Answered locally."""
        return bool(self.check(subject, permission, resource, **kwargs)["allowed"])

    @staticmethod
    def _assignment(c: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": c["assignment_id"],
            "resource_id": c["resource_id"],
            "subject": f"{c['subject']['type']}:{c['subject']['id']}",
            "role": c["role"],
            "inherit": c["inherit"],
        }

    def sync(self) -> int:
        """Pull the types and tree (when ``tree_refresh_ms`` has passed), then consume the assignment change
        feed from the stored cursor. Returns how many changes it applied."""
        if self._tree_at is None or self._now() - self._tree_at >= self._tree_refresh:
            # Tree first: an assignment the feed then delivers never names a resource this mirror lacks.
            types = {
                t["key"]: {"key": t["key"], "inherit": t["inherit"], "roles": t["roles"]}
                for t in self._client.resources.types.list()["data"]
            }
            tree: dict[str, dict[str, Any]] = {}
            cursor: str | None = None
            while True:
                page = self._client.resources.list(limit=1000, **({"starting_after": cursor} if cursor else {}))
                for r in page["data"]:
                    tree[r["id"]] = {"id": r["id"], "type": r["type"], "external_id": r["external_id"], "parent_id": r.get("parent_id")}
                if not page.get("has_more") or not page.get("next_cursor"):
                    break
                cursor = page["next_cursor"]
            self.store.types, self.store.resources = types, tree
            self._tree_at = self._now()
        after = self.store.cursor
        applied = 0
        while True:
            page = self._client.resource_role_assignments.list_changes(**({"after": after} if after else {}), limit=500)
            self.store.apply_changes((c["change"], self._assignment(c)) for c in page["data"])
            applied += len(page["data"])
            if page.get("next_cursor"):
                after = page["next_cursor"]
                self.store.cursor = after
            if not page.get("has_more"):
                self.store.last_sync_at = self._now()
                return applied

    def apply_webhook(self, event: Mapping[str, Any]) -> bool:
        """Apply a VERIFIED ``resource_role_assignment.created`` / ``.deleted`` webhook."""
        etype = event.get("type") if isinstance(event, Mapping) else None
        d = event.get("data") if isinstance(event, Mapping) else None
        if etype not in ("resource_role_assignment.created", "resource_role_assignment.deleted") or not isinstance(d, Mapping):
            return False
        subj = d.get("subject")
        if not (
            isinstance(d.get("id"), str)
            and isinstance(d.get("resource_id"), str)
            and isinstance(d.get("role"), str)
            and isinstance(subj, Mapping)
            and isinstance(subj.get("type"), str)
            and isinstance(subj.get("id"), str)
        ):
            return False
        self.store.apply_changes(
            [
                (
                    "created" if etype.endswith("created") else "deleted",
                    {
                        "id": d["id"],
                        "resource_id": d["resource_id"],
                        "subject": f"{subj['type']}:{subj['id']}",
                        "role": d["role"],
                        "inherit": d.get("inherit") is not False,
                    },
                )
            ]
        )
        return True


# --------------------------------------------------------------------------------------------
# Session revocation: the paged feed, or the signed status list
# --------------------------------------------------------------------------------------------


class StatusListError(Exception):
    """A signed session status list that does not verify; ``reason`` is one of ``malformed``,
    ``unsupported``, ``no_key``, ``bad_signature``, ``bad_claims`` or ``expired``."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid session status list: {reason}")
        self.reason = reason


@dataclass
class VerifiedStatusList:
    """``has(sid)`` answers whether the session id's hash is in the list. ``truncated``: more sessions were
    revoked than fit, so a miss proves nothing and the feed must be asked."""

    count: int
    truncated: bool
    issued_at: int
    expires_at: int
    since: int
    _hashes: bytes
    _hash_bytes: int

    def has(self, sid: str) -> bool:
        needle = hashlib.sha256(sid.encode("utf-8")).digest()[: self._hash_bytes]
        lo, hi = 0, self.count - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            cur = self._hashes[mid * self._hash_bytes : (mid + 1) * self._hash_bytes]
            if cur == needle:
                return True
            if cur < needle:
                lo = mid + 1
            else:
                hi = mid - 1
        return False


def verify_status_list_token(
    token: str,
    *,
    jwks: Mapping[str, Any] | Callable[[str | None], Mapping[str, Any] | None],
    issuer: str | None = None,
    now: Callable[[], int] | None = None,
    skew_seconds: int = 30,
) -> VerifiedStatusList:
    """Verify ``GET /v1/sessions/revocations/status-list``'s signed list (RS256 / ES256). Raises
    :class:`StatusListError`; never returns a half-trusted list."""
    import jwt  # PyJWT

    parts = token.split(".")
    if len(parts) != 3 or len(token) > 4_000_000:
        raise StatusListError("malformed")
    try:
        header = json.loads(_b64url_decode(parts[0]))
    except ValueError:
        raise StatusListError("malformed") from None
    if not isinstance(header, dict) or header.get("typ") != "statuslist+jwt" or header.get("alg") not in SIGNING_ALGS:
        raise StatusListError("unsupported")
    kid = header.get("kid") if isinstance(header.get("kid"), str) else None
    keyset = jwks(kid) if callable(jwks) else jwks
    kty = {"RS256": "RSA", "PS256": "RSA", "ES256": "EC", "ES384": "EC", "EdDSA": "OKP"}[header["alg"]]
    jwk = next((k for k in (keyset or {}).get("keys", []) if (not kid or k.get("kid") == kid) and k.get("kty") == kty), None)
    if jwk is None:
        raise StatusListError("no_key")
    now_s = ((now or _now_ms)()) / 1000
    try:
        key, alg = jwk_public_key(jwk, header["alg"])
        claims = jwt.decode(
            token,
            key=key,
            algorithms=[alg],
            audience="atlas:session-status-list",
            leeway=skew_seconds,
            options={"verify_exp": False, "verify_iat": False, "verify_nbf": False},
        )
    except jwt.InvalidAudienceError:
        raise StatusListError("bad_claims") from None
    except Exception:
        raise StatusListError("bad_signature") from None

    def num(v: Any) -> float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise StatusListError("bad_claims")
        return v

    if claims.get("token_use") != "session_status_list" or (issuer is not None and claims.get("iss") != issuer):
        raise StatusListError("bad_claims")
    exp, iat = num(claims.get("exp")), num(claims.get("iat"))
    if exp + skew_seconds < now_s:
        raise StatusListError("expired")
    if iat - skew_seconds > now_s:
        raise StatusListError("bad_claims")
    hash_bytes, count = int(num(claims.get("hash_bytes"))), int(num(claims.get("count")))
    if not 4 <= hash_bytes <= 32 or not isinstance(claims.get("h"), str):
        raise StatusListError("bad_claims")
    try:
        raw = _b64url_decode(claims["h"])
    except ValueError:
        raise StatusListError("malformed") from None
    if len(raw) != count * hash_bytes:
        raise StatusListError("bad_claims")
    return VerifiedStatusList(count, claims.get("truncated") is True, int(iat * 1000), int(exp * 1000), int(num(claims.get("since"))), raw, hash_bytes)


class EdgeRevocationChecker:
    """A revocation check that holds the last VERIFIED signed status list in memory and refreshes it when
    older than ``refresh_ms``. :meth:`check` answers ``ok``, ``revoked`` or ``unavailable`` (the list is too
    old and ``on_stale`` is ``reject``, or it was truncated). Fail-closed on a bad signature."""

    def __init__(
        self,
        *,
        secret_key: str,
        jwks_url: str,
        issuer: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        window_seconds: int = 3600,
        refresh_ms: int = 30_000,
        stale_after_ms: int = 120_000,
        serve_stale_for_ms: int = 0,
        on_stale: str = "reject",
        on_error: Callable[[Exception], None] | None = None,
        on_serve_stale: Callable[[dict[str, Any]], None] | None = None,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._key, self._issuer, self._base = secret_key, issuer, base_url.rstrip("/")
        self._window, self._refresh_ms, self._stale_after = window_seconds, refresh_ms, stale_after_ms
        self._serve_stale, self._on_stale, self._on_error, self._on_serve_stale = serve_stale_for_ms, on_stale, on_error, on_serve_stale
        self._http = http_client or httpx.Client(timeout=10.0)
        self._now = now or _now_ms
        self._jwks = JwksCache(jwks_url, http_client=self._http, now=self._now)
        self._current: VerifiedStatusList | None = None
        self.last_success_at: int | None = None
        self._lock = threading.Lock()

    def _refresh(self) -> None:
        try:
            res = self._http.get(
                f"{self._base}/v1/sessions/revocations/status-list",
                params={"window_seconds": self._window} if self._window else None,
                headers={"authorization": f"Bearer {self._key}"},
            )
            if not res.is_success:
                raise RuntimeError(f"status list answered {res.status_code}")
            token = res.json().get("token")
            if not isinstance(token, str):
                raise RuntimeError("status list answer had no token")
            self._current = verify_status_list_token(token, jwks=lambda kid: self._jwks.get(kid), issuer=self._issuer, now=self._now)
            self.last_success_at = self._now()
        except Exception as e:
            if self._on_error:
                self._on_error(e)

    def check(self, sid: str) -> str:
        with self._lock:
            if self._current is None or self.last_success_at is None or self._now() - self.last_success_at >= self._refresh_ms:
                self._refresh()
            cur, at = self._current, self.last_success_at
        stale = float("inf") if at is None else self._now() - at - self._stale_after
        if cur is None:
            return "ok" if self._on_stale == "allow" else "unavailable"
        if cur.has(sid):
            return "revoked"
        if cur.truncated:
            return "unavailable"
        if stale > 0 and self._on_stale != "allow":
            if stale <= self._serve_stale:
                if self._on_serve_stale:
                    self._on_serve_stale({"last_success_at": at, "stale_for_ms": stale})
                return "ok"
            return "unavailable"
        return "ok"


class SidRevocationList:
    """One poller: an in-memory set of revoked session ids (``GET /v1/sessions/revoked``, needs ``sessions:read``),
    each kept until its token cannot be live any more. Pass the token's ``sid`` to :meth:`is_revoked` after
    verifying it; call :meth:`unavailable` to fail closed when the list is too old.

    Args:
        secret_key: an instance key with ``sessions:read``.
        interval_ms: how often to poll (default 15000). This plus the token lifetime is the worst-case window.
        max_token_lifetime_seconds: your longest-lived session token (default 3600).
        on_stale: ``allow`` (default) keeps trusting the last list; ``reject`` fails closed after ``stale_after_ms``.
        serve_stale_for_ms: with ``reject``, keep answering that long past ``stale_after_ms`` before failing closed.
        source: ``feed`` (default) or ``status_list`` (the signed list; needs ``jwks_url``, ``issuer``).
    """

    def __init__(
        self,
        *,
        secret_key: str,
        base_url: str = DEFAULT_BASE_URL,
        interval_ms: int = 15_000,
        max_token_lifetime_seconds: int = 3600,
        on_stale: str = "allow",
        stale_after_ms: int = 120_000,
        serve_stale_for_ms: int = 0,
        on_serve_stale: Callable[[dict[str, Any]], None] | None = None,
        source: str = "feed",
        jwks_url: str | None = None,
        issuer: str | None = None,
        on_error: Callable[[Exception], None] | None = None,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._key, self._base = secret_key, base_url.rstrip("/")
        self._interval = interval_ms
        self._lifetime = max_token_lifetime_seconds * 1000
        self._on_stale, self._stale_after, self._serve_stale = on_stale, stale_after_ms, serve_stale_for_ms
        self._on_serve_stale, self._on_error = on_serve_stale, on_error
        self._source, self._jwks_url, self._issuer = source, jwks_url, issuer
        self._http = http_client or httpx.Client(timeout=10.0)
        self._now = now or _now_ms
        self._revoked: dict[str, int] = {}
        self._since: int | None = None
        self._next_poll = 0
        self._last_success: int | None = None
        self._created = self._now()
        self._lock = threading.Lock()
        self._edge: EdgeRevocationChecker | None = None

    def unavailable(self) -> bool:
        """True when the list could not be refreshed for ``stale_after_ms`` and ``on_stale`` is ``reject``."""
        if self._on_stale != "reject":
            return False
        stale = self._now() - (self._last_success or self._created) - self._stale_after
        if stale <= 0:
            return False
        if self._last_success is not None and stale <= self._serve_stale:
            if self._on_serve_stale:
                self._on_serve_stale({"last_success_at": self._last_success, "stale_for_ms": stale})
            return False
        return True

    def is_revoked(self, sid: str) -> bool:
        if self._source == "status_list":
            if not self._jwks_url:
                raise ValueError("revocation source `status_list` needs `jwks_url`.")
            if self._edge is None:
                self._edge = EdgeRevocationChecker(
                    secret_key=self._key,
                    jwks_url=self._jwks_url,
                    issuer=self._issuer,
                    base_url=self._base,
                    window_seconds=min(86_400, max(60, -(-self._lifetime // 1000))),
                    refresh_ms=self._interval,
                    stale_after_ms=self._stale_after,
                    on_stale="allow",
                    on_error=self._on_error,
                    http_client=self._http,
                    now=self._now,
                )
            verdict = self._edge.check(sid)
            self._last_success = self._edge.last_success_at
            # A list that was cut short, or never fetched, cannot clear a session: ask the feed.
            if verdict != "unavailable":
                return verdict == "revoked"
        now = self._now()
        with self._lock:
            if now >= self._next_poll:
                self._poll()
            expiry = self._revoked.get(sid)
        return expiry is not None and expiry > now

    def _poll(self) -> None:
        started = self._now()
        self._next_poll = started + self._interval
        try:
            cursor: str | None = None
            server_time = started
            while True:
                q: dict[str, Any] = {"since": self._since if self._since is not None else started - self._lifetime, "limit": 5000}
                if cursor:
                    q["cursor"] = cursor
                res = self._http.get(f"{self._base}/v1/sessions/revoked", params=q, headers={"authorization": f"Bearer {self._key}"})
                if not res.is_success:
                    raise RuntimeError(f"GET /v1/sessions/revoked answered {res.status_code}")
                page = res.json()
                for r in page.get("data", []):
                    self._revoked[r["sid"]] = r["revoked_at"] + self._lifetime
                server_time = page.get("server_time", server_time)
                cursor = page.get("next_cursor") if page.get("has_more") else None
                if not cursor:
                    break
            # Re-ask from a little before the answer's own clock, so a row committed late is not missed.
            self._since = int(server_time) - 10_000
            self._last_success = started
            for sid in [s for s, exp in self._revoked.items() if exp <= started]:
                del self._revoked[sid]
        except Exception as e:
            if self._on_error:
                self._on_error(e)


# --------------------------------------------------------------------------------------------
# Webhook dedupe
# --------------------------------------------------------------------------------------------


class WebhookDedupeStore(Protocol):
    """``set_if_absent`` must be atomic: store ``key`` for ``ttl_seconds`` and return ``True`` when it was NOT
    there (Redis: ``SET key 1 EX ttl NX``). ``delete`` is optional: a failed handler can release the id."""

    def set_if_absent(self, key: str, ttl_seconds: int) -> bool: ...


class MemoryWebhookStore:
    """A single-process store. Use a shared one (Redis, a database) when you run more than one instance."""

    def __init__(self, now: Callable[[], int] | None = None) -> None:
        self._now = now or _now_ms
        self._seen: dict[str, int] = {}
        self._lock = threading.Lock()

    def set_if_absent(self, key: str, ttl_seconds: int) -> bool:
        with self._lock:
            t = self._now()
            for k in [k for k, exp in self._seen.items() if exp <= t]:
                del self._seen[k]
            if key in self._seen:
                return False
            self._seen[key] = t + ttl_seconds * 1000
            return True

    def delete(self, key: str) -> None:
        with self._lock:
            self._seen.pop(key, None)


class SqlWebhookDedupeStore:
    """A :class:`WebhookDedupeStore` on SQL. ``execute(sql, params)`` runs one statement and returns
    ``(rows, rowcount)`` (any DB-API cursor works behind a two-line wrapper). Create the table once::

        postgres: create table atlas_webhook_seen (key text primary key, expires_at timestamptz not null);
        sqlite:   create table atlas_webhook_seen (key text primary key, expires_at integer not null);  -- epoch ms
        mysql:    create table atlas_webhook_seen (`key` varchar(255) primary key, expires_at datetime not null);

    The statements use ``%s`` placeholders for ``postgres`` and ``mysql`` and ``?`` for ``sqlite``.
    A key whose row has expired counts as unseen and is claimed again.
    """

    def __init__(self, execute: Callable[[str, Sequence[Any]], tuple[list[Any], int]], dialect: str = "postgres") -> None:
        if dialect not in ("postgres", "sqlite", "mysql"):
            raise ValueError("dialect must be postgres, sqlite or mysql")
        self._exec, self._dialect = execute, dialect

    def set_if_absent(self, key: str, ttl_seconds: int) -> bool:
        if self._dialect == "sqlite":
            now = _now_ms()
            rows, _ = self._exec(
                "insert into atlas_webhook_seen (key, expires_at) values (?, ?) "
                "on conflict (key) do update set expires_at = excluded.expires_at "
                "where atlas_webhook_seen.expires_at <= ? returning key",
                (key, now + ttl_seconds * 1000, now),
            )
            return len(rows) > 0
        if self._dialect == "mysql":
            self._exec("delete from atlas_webhook_seen where `key` = %s and expires_at <= now()", (key,))
            _, count = self._exec(
                "insert ignore into atlas_webhook_seen (`key`, expires_at) values (%s, now() + interval %s second)",
                (key, int(ttl_seconds)),
            )
            return count > 0
        rows, _ = self._exec(
            "insert into atlas_webhook_seen (key, expires_at) values (%s, now() + (%s || ' seconds')::interval) "
            "on conflict (key) do update set expires_at = excluded.expires_at "
            "where atlas_webhook_seen.expires_at <= now() returning key",
            (key, str(ttl_seconds)),
        )
        return len(rows) > 0

    def delete(self, key: str) -> None:
        col = "`key`" if self._dialect == "mysql" else "key"
        ph = "?" if self._dialect == "sqlite" else "%s"
        self._exec(f"delete from atlas_webhook_seen where {col} = {ph}", (key,))


class WebhookVerificationError(Exception):
    """A delivery that does not verify (answer 400 / 401); ``reason`` is the verifier's reason or ``invalid_body``."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Atlas webhook verification failed: {reason}")
        self.reason = reason


@dataclass
class DedupedWebhook:
    #: The parsed envelope ``{id, type, timestamp, instance_id, data}``.
    event: dict[str, Any]
    #: True when this ``atlas-id`` was already seen: acknowledge with 2xx and do nothing.
    duplicate: bool
    #: The signed ``atlas-id``, identical on every retry of one event.
    delivery_id: str
    _release: Callable[[], None] = field(default=lambda: None, repr=False)

    def release(self) -> None:
        """Forget this delivery so Atlas's retry is processed, e.g. after your handler failed."""
        self._release()


def verify_and_dedupe(
    body: bytes | str,
    headers: Mapping[str, Any],
    secret: str,
    store: WebhookDedupeStore,
    *,
    ttl_seconds: int = 86_400,
    key_prefix: str = "atlas-webhook:",
    url: str | None = None,
    require_v2: bool = False,
    standard: bool = False,
    now_ms: int | None = None,
) -> DedupedWebhook:
    """Verify an Atlas webhook (signature and timestamp, exactly as :func:`verify_webhook`; with
    ``standard=True`` an application webhook as :func:`verify_standard_webhook`) and drop a delivery
    whose id was already seen. Raises :class:`WebhookVerificationError` for a delivery that does not verify;
    an unverified delivery never touches the store."""
    res: WebhookVerification
    if standard:
        res = verify_standard_webhook(body, headers, secret, now_s=None if now_ms is None else now_ms // 1000)
    else:
        res = verify_webhook(body, headers, secret, url=url, require_v2=require_v2, now_ms=now_ms)
    if not res.verified or not res.delivery_id:
        raise WebhookVerificationError(res.reason or "signature_mismatch")
    if res.event is None:
        raise WebhookVerificationError("invalid_body")
    key = f"{key_prefix}{res.delivery_id}"
    fresh = store.set_if_absent(key, ttl_seconds)
    drop = getattr(store, "delete", None)
    return DedupedWebhook(res.event, not fresh, res.delivery_id, (lambda: drop(key)) if callable(drop) else (lambda: None))


# --------------------------------------------------------------------------------------------
# Transaction tokens
# --------------------------------------------------------------------------------------------


@dataclass
class TxnTokenResult:
    ok: bool
    claims: dict[str, Any] = field(default_factory=dict)
    scopes: list[str] = field(default_factory=list)
    error: str | None = None


def verify_transaction_token(
    token: str,
    *,
    issuer: str,
    trust_domain: str,
    jwks: Mapping[str, Any] | None = None,
    jwks_url: str | None = None,
    http_client: httpx.Client | None = None,
    now: int | None = None,
) -> TxnTokenResult:
    """Verify a Transaction Token (draft-ietf-oauth-transaction-tokens) a service received: ``typ txntoken+jwt``,
    signed by the issuer's keys, for THIS trust domain (its ``aud``), unexpired, with ``txn``, ``sub``,
    ``scope``, ``req_wl``, ``iat`` and ``exp``. Never raises: check ``ok``."""
    import jwt  # PyJWT

    bad = TxnTokenResult(False, error="The transaction token is invalid, expired, or for another trust domain.")
    iss = issuer.rstrip("/")
    try:
        header = jwt.get_unverified_header(token)
        if str(header.get("typ", "")).lower() != "txntoken+jwt":
            return bad
        kid = header.get("kid") if isinstance(header.get("kid"), str) else None
        keyset = jwks if jwks is not None else JwksCache(jwks_url or f"{iss}/.well-known/jwks.json", http_client=http_client).get(kid)
        jwk = next((k for k in (keyset or {}).get("keys", []) if not kid or k.get("kid") == kid), None)
        if jwk is None:
            return bad
        if header.get("alg") not in SIGNING_ALGS:
            return bad
        key, alg = jwk_public_key(jwk, header["alg"])
        claims = jwt.decode(
            token,
            key=key,
            algorithms=[alg],
            issuer=iss,
            audience=trust_domain,
            leeway=5,
            options={"verify_exp": now is None, "verify_iat": False},
        )
        if now is not None and claims.get("exp", 0) + 5 < now:
            return bad
    except Exception:
        return bad
    for c in ("txn", "sub", "scope", "req_wl", "iat", "exp"):
        if claims.get(c) is None:
            return TxnTokenResult(False, error=f"The transaction token has no {c}.")
    return TxnTokenResult(True, claims=dict(claims), scopes=[s for s in str(claims["scope"]).split(" ") if s])
