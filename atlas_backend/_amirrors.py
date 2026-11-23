"""Asynchronous mirrors and revocation: the asyncio peers of :mod:`atlas_backend._mirrors`.

Generated from ``_mirrors.py`` by ``scripts/gen_async.py`` (do not edit). Stores, callbacks and API clients may be
sync or async: awaitables are awaited. Use these with :class:`~atlas_backend.AsyncAtlasClient`.
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

from ._api_key_assertion import parse_assertion, verify_assertion_signature
from ._transport import DEFAULT_BASE_URL
from ._verify import SIGNING_ALGS, JwksCache, _b64url_decode, jwk_public_key
from ._webhooks import WebhookVerification, verify_standard_webhook, verify_webhook


from ._async_support import AsyncJwksCache, _AsyncLock, _aw
from ._verify import JwksCache
from ._mirrors import (  # noqa: F401
    _now_ms,
    hash_api_key_secret,
    KeyMirrorStore,
    MemoryKeyMirrorStore,
    _expand,
    ip_in_allowlist,
    permission_covers_scope,
    intersect_scopes_with_permissions,
    _mirrored,
    _key_hash,
    KeyVerification,
    _MAX_DEPTH,
    _role_permissions,
    resolve_mirror_grants,
    MemoryResourceRoleStore,
    StatusListError,
    VerifiedStatusList,
    verify_status_list_token,
    WebhookDedupeStore,
    MemoryWebhookStore,
    WebhookVerificationError,
    DedupedWebhook,
    verify_and_dedupe,
    TxnTokenResult,
    verify_transaction_token,
)


class AsyncKeyMirror:
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
        self._used_jtis: dict[str, int] = {}
        self._jti_lock = _AsyncLock()

    async def last_sync_at(self) -> int | None:
        """Epoch ms of the last completed :meth:`sync`; ``None`` = never."""
        return (await _aw(self.store.get_last_sync_at()))

    async def mint(self, body: dict[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
        """Mint at Atlas, then mirror it. Returns the key with its one-time ``secret``."""
        created = (await _aw(self.api_keys.create(body, idempotency_key=idempotency_key)))
        (await _aw(self.store.put(_mirrored(created, _key_hash(created)))))
        return created

    async def rotate(self, key_id: str, body: dict[str, Any] | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        """Rotate at Atlas, then mirror both sides: the successor is added, the old key ends at the end of the overlap."""
        rotated = (await _aw(self.api_keys.rotate(key_id, body or {}, idempotency_key=idempotency_key)))
        (await _aw(self.store.put(_mirrored(rotated, _key_hash(rotated)))))
        old = (await _aw(self.store.get(key_id)))
        if old:
            prev = rotated.get("previous_key") or {}
            if prev.get("revoked"):
                (await _aw(self.store.mark_revoked(key_id, self._now(), "rotated")))
            else:
                (await _aw(self.store.put({**old, "expires_at": prev.get("expires_at", old.get("expires_at"))})))
        return rotated

    async def import_key(
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
            imported = (await _aw(self.api_keys.create(
                {**rest, "import": {"secret_hash": legacy, "hash_algorithm": "bcrypt" if bcrypt_hash else "argon2id", "prefix": prefix}},
                idempotency_key=idempotency_key,
            )))
            # No local sha256 yet: verify (with verify_at_atlas) fills it in on first use.
            if imported.get("outcome") != "already_present" or not (await _aw(self.store.get(imported["id"]))):
                (await _aw(self.store.put(_mirrored(imported, f"legacy:{imported['id']}"))))
            return {**imported, "outcome": imported.get("outcome", "created")}
        digest = secret_hash.lower() if secret_hash else (hash_api_key_secret(secret) if secret is not None else None)
        if not digest or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("import_key needs the full `secret` or its `secret_hash` (64 lowercase hex characters of sha256).")
        imported = (await _aw(self.api_keys.create(
            {**rest, "import": {"secret_hash": digest, "hash_algorithm": "sha256_hex", "prefix": prefix}},
            idempotency_key=idempotency_key,
        )))
        (await _aw(self.store.put(_mirrored(imported, digest))))
        return {**imported, "outcome": imported.get("outcome", "created")}

    async def revoke(self, key_id: str) -> None:
        """Revoke LOCALLY first (the key stops working here at once), then at Atlas. A key Atlas already
        revoked or no longer knows (404 / 409) counts as revoked; any other Atlas error is raised after the local revoke."""
        (await _aw(self.store.mark_revoked(key_id, self._now())))
        try:
            (await _aw(self.api_keys.revoke(key_id)))
        except Exception as e:
            if getattr(e, "status", None) not in (404, 409):
                raise

    async def _freshness(self) -> tuple[KeyVerification | None, bool]:
        """(a refusal when the mirror is too stale to answer, whether the answer is served stale)."""
        if self._max_staleness is None:
            return None, False
        at = (await self.last_sync_at())
        behind = float("inf") if at is None else self._now() - at - self._max_staleness
        if behind <= 0:
            return None, False
        if at is None or behind > self._serve_stale:
            return KeyVerification(False, code="stale", last_sync_at=at), False
        if self._on_serve_stale:
            self._on_serve_stale({"last_sync_at": at, "stale_for_ms": behind})
        return None, True

    async def verify(self, secret: str, *, required_scopes: Sequence[str] = (), client_ip: str | None = None) -> KeyVerification:
        """Verify a presented secret against the mirror: no network call (unless ``verify_at_atlas``)."""
        if not isinstance(secret, str) or not secret:
            return KeyVerification(False)
        refuse, served_stale = (await self._freshness())
        if refuse:
            return refuse
        digest = hash_api_key_secret(secret)
        key = (await _aw(self.store.get_by_hash(digest)))
        ip_arg = {"client_ip": client_ip} if client_ip else {}
        if key is None and self._verify_at_atlas:
            remote = (await _aw(self.api_keys.verify({"secret": secret, **ip_arg})))
            if remote.get("valid"):
                key = _mirrored((await _aw(self.api_keys.get(remote["id"]))), digest)
                (await _aw(self.store.put(key)))
        if key is None or key.get("revoked_at") is not None or key.get("enabled") is False:
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
                held = (await _aw(self._membership(key["subject_id"], key["organization_id"])))
                if not held:
                    return KeyVerification(False)
                organization = dict(held)
                effective = intersect_scopes_with_permissions(effective, held.get("permissions", []))
            elif hasattr(self.api_keys, "verify"):
                remote = (await _aw(self.api_keys.verify({"secret": secret, **ip_arg})))
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

    async def verify_assertion(self, token: str, *, required_scopes: Sequence[str] = (), client_ip: str | None = None) -> KeyVerification:
        """Verify a key-pair assertion (``sign_api_key_assertion``) locally with the checks Atlas verify makes:
        signature with the stored public key (``alg`` must fit its type), ``iss`` = ``kid``, ``aud``, ``iat``,
        ``exp`` and the lifetime cap, ``nbf``, ``scope`` (a subset of the key's, narrows the result), revocation,
        expiry, the IP allowlist, then the single-use ``jti``. A refusal carries the server's ``code``; a key the
        mirror does not hold answers ``valid=False`` with no code. The ``jti`` is claimed through the store's
        optional ``claim_assertion_jti(key_id, jti, expires_at_ms) -> bool``, else in this process's memory."""
        refuse, served_stale = (await self._freshness())
        if refuse:
            return refuse
        parsed = parse_assertion(token)
        if parsed is None:
            return KeyVerification(False, code="invalid_assertion")
        header, claims, signing_input, signature = parsed
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            return KeyVerification(False, code="invalid_assertion")
        key = (await _aw(self.store.get(kid)))
        if key is None:
            return KeyVerification(False)
        if key.get("credential") != "key_pair" or not key.get("public_key_pem"):
            return KeyVerification(False, code="invalid_assertion")
        if not verify_assertion_signature(header, signing_input, signature, key["public_key_pem"]) or claims.get("iss") != kid:
            return KeyVerification(False, code="invalid_assertion")
        if key.get("enabled") is False:
            return KeyVerification(False, code="invalid_assertion")
        if key.get("revoked_at") is not None:
            return KeyVerification(False)
        now_ms = self._now()
        if key.get("expires_at") is not None and key["expires_at"] <= now_ms:
            return KeyVerification(False)
        now_s = now_ms // 1000

        def num(v: Any) -> bool:
            return isinstance(v, (int, float)) and not isinstance(v, bool)

        aud, iat, exp, nbf, jti, scope = (claims.get(k) for k in ("aud", "iat", "exp", "nbf", "jti", "scope"))
        if not (aud == key.get("audience") if isinstance(aud, str) else isinstance(aud, list) and key.get("audience") in aud):
            return KeyVerification(False, code="wrong_audience")
        if not num(iat) or not num(exp) or ("nbf" in claims and not num(nbf)):
            return KeyVerification(False, code="invalid_assertion")
        if ("jti" in claims and (not isinstance(jti, str) or not jti)) or ("scope" in claims and not isinstance(scope, str)):
            return KeyVerification(False, code="invalid_assertion")
        if iat > now_s + 60 or (nbf is not None and nbf > now_s + 60):
            return KeyVerification(False, code="assertion_not_yet_valid")
        if exp <= now_s - 30:
            return KeyVerification(False, code="assertion_expired")
        if exp - iat > min(key.get("max_token_lifetime_seconds") or 3600, 86400):
            return KeyVerification(False, code="assertion_lifetime_too_long")
        if key.get("allowed_ips"):
            if not client_ip:
                return KeyVerification(False, code="client_ip_required")
            if not ip_in_allowlist(client_ip, key["allowed_ips"]):
                return KeyVerification(False, code="ip_not_allowed")
        effective = _expand(key.get("scopes") or [], self._implications, self._allowed)
        organization: dict[str, Any] | None = None
        if key.get("subject_type") == "user" and key.get("organization_id"):
            held = (await _aw(self._membership(key["subject_id"], key["organization_id"]))) if self._membership else None
            if not self._membership:
                return KeyVerification(False, code="membership_unresolved")
            if not held:
                return KeyVerification(False)
            organization = dict(held)
            effective = intersect_scopes_with_permissions(effective, held.get("permissions", []))
        if isinstance(scope, str) and scope.strip():
            asked = scope.split()
            not_granted = [x for x in asked if x not in effective]
            if not_granted:
                return KeyVerification(False, code="scope_not_granted", missing_scopes=not_granted)
            effective = [x for x in effective if x in asked]
        missing = [x for x in required_scopes if x not in effective]
        if missing:
            return KeyVerification(False, code="insufficient_scope", missing_scopes=missing)
        # Last, so a refused assertion never burns its jti.
        if isinstance(jti, str):
            until = int(exp * 1000)
            if hasattr(self.store, "claim_assertion_jti"):
                first = (await _aw(self.store.claim_assertion_jti(key["id"], jti, until)))
            else:
                with self._jti_lock:
                    self._used_jtis = {k: t for k, t in self._used_jtis.items() if t > now_ms}
                    ident = f"{key['id']}\n{jti}"
                    first = ident not in self._used_jtis
                    if first:
                        self._used_jtis[ident] = until
            if not first:
                return KeyVerification(False, code="assertion_replayed")
        return KeyVerification(
            True, key=key, effective_scopes=effective, organization=organization, stale=served_stale,
            credential="key_pair", jti=jti if isinstance(jti, str) else None, exp=int(exp),
        )

    async def sync(self) -> int:
        """Consume the revocation feed from the stored cursor, revoking each listed key locally.
        Call it on a timer (every few seconds to a minute). Returns how many ids it applied."""
        since = (await _aw(self.store.get_cursor()))
        revoked = 0
        while True:
            page = (await _aw(self.api_keys.list_revoked(**({"since": since} if since else {}), limit=100)))
            for ref in page.get("data", []):
                (await _aw(self.store.mark_revoked(ref["id"], ref.get("revoked_at") or self._now(), ref.get("revoked_reason"))))
                revoked += 1
            cursor = page.get("next_cursor")
            if cursor:
                since = cursor
                (await _aw(self.store.set_cursor(cursor)))
            if not page.get("has_more") or not cursor:
                (await _aw(self.store.set_last_sync_at(self._now())))
                return revoked

    async def apply_webhook(self, event: Mapping[str, Any]) -> bool:
        """Apply a VERIFIED ``api_key.*`` (or ``organization_membership.deleted``) webhook event. Returns
        whether it changed the mirror."""
        etype = event.get("type") if isinstance(event, Mapping) else None
        data = event.get("data") if isinstance(event, Mapping) else None
        if not isinstance(etype, str) or not isinstance(data, Mapping):
            return False
        if etype in ("organization_membership.deleted", "organizationMembership.deleted"):
            uid, oid = data.get("user_id"), data.get("organization_id")
            if isinstance(uid, str) and isinstance(oid, str):
                (await _aw(self.store.mark_membership_ended(uid, oid, self._now())))
                return True
            return False
        if not etype.startswith("api_key.") or not isinstance(data.get("id"), str):
            return False
        held = (await _aw(self.store.get(data["id"])))
        if not held:
            return False
        if etype == "api_key.restored":
            if held.get("revoked_at") is None:
                return False
            (await _aw(self.store.put({**held, "revoked_at": None, "revoked_reason": None, "expires_at": data.get("expires_at", held.get("expires_at"))})))
            return True
        if etype == "api_key.revoked" or (isinstance(data.get("revoked_at"), int) and held.get("revoked_at") is None):
            at = data["revoked_at"] if isinstance(data.get("revoked_at"), int) else self._now()
            (await _aw(self.store.mark_revoked(held["id"], at, data.get("revoked_reason"))))
            return True
        if etype in ("api_key.updated", "api_key.created"):
            (await _aw(self.store.put(
                {**held, **{k: data[k] for k in ("name", "scopes", "allowed_ips", "expires_at", "enabled") if k in data}}
            )))
            return True
        return False


class AsyncResourceRoleMirror:
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

    async def _chain(self, resource: dict[str, Any]) -> list[dict[str, Any]]:
        ancestors: list[dict[str, Any]] = []
        pid = resource.get("parent_id")
        for _ in range(_MAX_DEPTH):
            if not pid:
                break
            row = (await _aw(self.store.get_resource({"id": pid})))
            if not row or any(r["id"] == row["id"] for r in ancestors):
                break
            ancestors.append(row)
            pid = row.get("parent_id")
        rows = [resource, *ancestors]
        assigns = (await _aw(self.store.assignments_on(r["id"] for r in rows)))
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

    async def check(
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
        row = (await _aw(self.store.get_resource(resource)))
        if not row or not isinstance(permission, str) or not permission:
            out: dict[str, Any] = {"allowed": False, "resource_id": row["id"] if row else None, "grants": []}
            if not row:
                out["code"] = "unknown_resource"
            return out
        subjects = {f"{subject['type']}:{subject['id']}"}
        subjects |= {f"group:{g}" for g in groups}
        subjects |= {f"org:{o}" for o in orgs}
        grants = resolve_mirror_grants((await self._chain(row)), subjects, permission)
        out = {"allowed": bool(grants), "resource_id": row["id"], "grants": grants}
        if served_stale:
            out["stale"] = True
        return out

    async def can(self, subject: Mapping[str, str], permission: str, resource: Mapping[str, str], **kwargs: Any) -> bool:
        """May ``subject`` hold ``permission`` on ``resource``? Answered locally."""
        return bool((await self.check(subject, permission, resource, **kwargs))["allowed"])

    @staticmethod
    def _assignment(c: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": c["assignment_id"],
            "resource_id": c["resource_id"],
            "subject": f"{c['subject']['type']}:{c['subject']['id']}",
            "role": c["role"],
            "inherit": c["inherit"],
        }

    async def sync(self) -> int:
        """Pull the types and tree (when ``tree_refresh_ms`` has passed), then consume the assignment change
        feed from the stored cursor. Returns how many changes it applied."""
        if self._tree_at is None or self._now() - self._tree_at >= self._tree_refresh:
            # Tree first: an assignment the feed then delivers never names a resource this mirror lacks.
            types = {
                t["key"]: {"key": t["key"], "inherit": t["inherit"], "roles": t["roles"]}
                for t in (await _aw(self._client.resources.types.list()))["data"]
            }
            tree: dict[str, dict[str, Any]] = {}
            cursor: str | None = None
            while True:
                page = (await _aw(self._client.resources.list(limit=1000, **({"starting_after": cursor} if cursor else {}))))
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
            page = (await _aw(self._client.resource_role_assignments.list_changes(**({"after": after} if after else {}), limit=500)))
            (await _aw(self.store.apply_changes((c["change"], self._assignment(c)) for c in page["data"])))
            applied += len(page["data"])
            if page.get("next_cursor"):
                after = page["next_cursor"]
                self.store.cursor = after
            if not page.get("has_more"):
                self.store.last_sync_at = self._now()
                return applied

    async def apply_webhook(self, event: Mapping[str, Any]) -> bool:
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
        (await _aw(self.store.apply_changes(
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
        )))
        return True


class AsyncEdgeRevocationChecker:
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
        http_client: httpx.AsyncClient | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._key, self._issuer, self._base = secret_key, issuer, base_url.rstrip("/")
        self._window, self._refresh_ms, self._stale_after = window_seconds, refresh_ms, stale_after_ms
        self._serve_stale, self._on_stale, self._on_error, self._on_serve_stale = serve_stale_for_ms, on_stale, on_error, on_serve_stale
        self._http = http_client or httpx.AsyncClient(timeout=10.0)
        self._now = now or _now_ms
        self._jwks = AsyncJwksCache(jwks_url, http_client=self._http, now=self._now)
        self._current: VerifiedStatusList | None = None
        self.last_success_at: int | None = None
        self._lock = _AsyncLock()

    async def _refresh(self) -> None:
        try:
            res = (await _aw(self._http.get(
                f"{self._base}/v1/sessions/revocations/status-list",
                params={"window_seconds": self._window} if self._window else None,
                headers={"authorization": f"Bearer {self._key}"},
            )))
            if not res.is_success:
                raise RuntimeError(f"status list answered {res.status_code}")
            token = res.json().get("token")
            if not isinstance(token, str):
                raise RuntimeError("status list answer had no token")
            self._current = verify_status_list_token(token, jwks=await self._jwks.get(JwksCache.read_kid(token)), issuer=self._issuer, now=self._now)
            self.last_success_at = self._now()
        except Exception as e:
            if self._on_error:
                self._on_error(e)

    async def check(self, sid: str) -> str:
        async with self._lock:
            if self._current is None or self.last_success_at is None or self._now() - self.last_success_at >= self._refresh_ms:
                (await self._refresh())
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


class AsyncSidRevocationList:
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
        http_client: httpx.AsyncClient | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        self._key, self._base = secret_key, base_url.rstrip("/")
        self._interval = interval_ms
        self._lifetime = max_token_lifetime_seconds * 1000
        self._on_stale, self._stale_after, self._serve_stale = on_stale, stale_after_ms, serve_stale_for_ms
        self._on_serve_stale, self._on_error = on_serve_stale, on_error
        self._source, self._jwks_url, self._issuer = source, jwks_url, issuer
        self._http = http_client or httpx.AsyncClient(timeout=10.0)
        self._now = now or _now_ms
        self._revoked: dict[str, int] = {}
        self._since: int | None = None
        self._next_poll = 0
        self._last_success: int | None = None
        self._created = self._now()
        self._lock = _AsyncLock()
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

    async def is_revoked(self, sid: str) -> bool:
        if self._source == "status_list":
            if not self._jwks_url:
                raise ValueError("revocation source `status_list` needs `jwks_url`.")
            if self._edge is None:
                self._edge = AsyncEdgeRevocationChecker(
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
            verdict = (await _aw(self._edge.check(sid)))
            self._last_success = self._edge.last_success_at
            # A list that was cut short, or never fetched, cannot clear a session: ask the feed.
            if verdict != "unavailable":
                return verdict == "revoked"
        now = self._now()
        async with self._lock:
            if now >= self._next_poll:
                (await self._poll())
            expiry = self._revoked.get(sid)
        return expiry is not None and expiry > now

    async def _poll(self) -> None:
        started = self._now()
        self._next_poll = started + self._interval
        try:
            cursor: str | None = None
            server_time = started
            while True:
                q: dict[str, Any] = {"since": self._since if self._since is not None else started - self._lifetime, "limit": 5000}
                if cursor:
                    q["cursor"] = cursor
                res = (await _aw(self._http.get(f"{self._base}/v1/sessions/revoked", params=q, headers={"authorization": f"Bearer {self._key}"})))
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


class AsyncSqlWebhookDedupeStore:
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

    async def set_if_absent(self, key: str, ttl_seconds: int) -> bool:
        if self._dialect == "sqlite":
            now = _now_ms()
            rows, _ = (await _aw(self._exec(
                "insert into atlas_webhook_seen (key, expires_at) values (?, ?) "
                "on conflict (key) do update set expires_at = excluded.expires_at "
                "where atlas_webhook_seen.expires_at <= ? returning key",
                (key, now + ttl_seconds * 1000, now),
            )))
            return len(rows) > 0
        if self._dialect == "mysql":
            (await _aw(self._exec("delete from atlas_webhook_seen where `key` = %s and expires_at <= now()", (key,))))
            _, count = (await _aw(self._exec(
                "insert ignore into atlas_webhook_seen (`key`, expires_at) values (%s, now() + interval %s second)",
                (key, int(ttl_seconds)),
            )))
            return count > 0
        rows, _ = (await _aw(self._exec(
            "insert into atlas_webhook_seen (key, expires_at) values (%s, now() + (%s || ' seconds')::interval) "
            "on conflict (key) do update set expires_at = excluded.expires_at "
            "where atlas_webhook_seen.expires_at <= now() returning key",
            (key, str(ttl_seconds)),
        )))
        return len(rows) > 0

    async def delete(self, key: str) -> None:
        col = "`key`" if self._dialect == "mysql" else "key"
        ph = "?" if self._dialect == "sqlite" else "%s"
        (await _aw(self._exec(f"delete from atlas_webhook_seen where {col} = {ph}", (key,))))


class AsyncMemoryWebhookStore:
    """An async :class:`WebhookDedupeStore` for one process (the in-memory store behind an async interface).
    A shared store implements ``async def set_if_absent(key, ttl_seconds) -> bool`` and optionally ``async def delete(key)``."""

    def __init__(self, now: Callable[[], int] | None = None) -> None:
        self._inner = MemoryWebhookStore(now)

    async def set_if_absent(self, key: str, ttl_seconds: int) -> bool:
        return self._inner.set_if_absent(key, ttl_seconds)

    async def delete(self, key: str) -> None:
        self._inner.delete(key)


@dataclass
class AsyncDedupedWebhook:
    event: dict[str, Any]
    #: True when this delivery id was already seen: acknowledge with 2xx and do nothing.
    duplicate: bool
    delivery_id: str
    _release: Callable[[], Any] = field(default=lambda: None, repr=False)

    async def release(self) -> None:
        """Forget this delivery so Atlas's retry is processed, e.g. after your handler failed."""
        await _aw(self._release())


async def verify_and_dedupe_async(
    body: bytes | str,
    headers: Mapping[str, Any],
    secret: str,
    store: Any,
    *,
    ttl_seconds: int = 86_400,
    key_prefix: str = "atlas-webhook:",
    url: str | None = None,
    require_v2: bool = False,
    standard: bool = False,
    now_ms: int | None = None,
) -> AsyncDedupedWebhook:
    """:func:`verify_and_dedupe` over an async store (sync stores work too)."""
    if standard:
        res = verify_standard_webhook(body, headers, secret, now_s=None if now_ms is None else now_ms // 1000)
    else:
        res = verify_webhook(body, headers, secret, url=url, require_v2=require_v2, now_ms=now_ms)
    if not res.verified or not res.delivery_id:
        raise WebhookVerificationError(res.reason or "signature_mismatch")
    if res.event is None:
        raise WebhookVerificationError("invalid_body")
    key = f"{key_prefix}{res.delivery_id}"
    fresh = await _aw(store.set_if_absent(key, ttl_seconds))
    drop = getattr(store, "delete", None)
    return AsyncDedupedWebhook(res.event, not fresh, res.delivery_id, (lambda: drop(key)) if callable(drop) else (lambda: None))
