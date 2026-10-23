"""Accepting your OLD auth provider's JWTs during a cutover — today, Better Auth's
``jwt`` plugin tokens.

When you move to Atlas, API clients may still hold short-lived JWTs your Better
Auth app minted. With ``legacy_issuers`` on an :class:`~atlas_backend.AtlasBackend`,
a token whose ``iss`` is one of these issuers is verified against THAT issuer's key
set (the JWKS you imported into Atlas, or the old app's ``/api/auth/jwks``) for a
bounded window, and its ``sub`` (the Better Auth user id) is mapped to the Atlas
user id — Atlas keeps the Better Auth id as the user's ``external_id``. After
``until``, those tokens are refused like any other foreign token.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

import httpx

#: Better Auth's ``jwt`` plugin key algorithms.
BETTER_AUTH_JWT_ALGS: tuple[str, ...] = ("EdDSA", "ES256", "ES512", "RS256", "PS256")

#: How long a resolved sub → Atlas id mapping is reused.
SUBJECT_TTL_MS = 5 * 60_000
#: Cap on cached subjects, so a stream of distinct tokens cannot grow memory unbounded.
SUBJECT_CACHE_MAX = 10_000

DEFAULT_API_URL = "https://api.atlasauth.net"


@dataclass(frozen=True)
class LegacyIssuer:
    """One old issuer accepted during the cutover.

    Args:
        issuer: The ``iss`` the old tokens carry (Better Auth: its ``baseURL``,
            unless ``jwt.issuer`` was set).
        until: End of the acceptance window (a :class:`datetime`, epoch ms, or an
            ISO-8601 string). Required: a legacy issuer is never accepted forever.
        jwks: The imported key set (``{"keys": [...]}``). Exactly one of
            ``jwks`` / ``jwks_url``.
        jwks_url: Where to fetch the old key set
            (e.g. ``https://app.example.com/api/auth/jwks``).
        audience: Expected ``aud`` (unchecked when unset).
        algorithms: Accepted algorithms; default Better Auth's (EdDSA, ES256,
            ES512, RS256, PS256).
        resolve_subject: Map the old ``sub`` to the Atlas user id. Default: look the
            user up by ``external_id`` through the Backend API (needs
            ``secret_key`` on the backend), cached for 5 minutes. Return ``None``
            to refuse the token.
    """

    issuer: str
    until: datetime | int | float | str
    jwks: Mapping[str, Any] | None = None
    jwks_url: str | None = None
    audience: str | Sequence[str] | None = None
    algorithms: Sequence[str] | None = None
    resolve_subject: Callable[[str, dict[str, Any]], str | None] | None = None
    kind: str = "better_auth"


def until_ms(until: datetime | int | float | str) -> int:
    """The window end in epoch ms (0 when unparseable)."""
    try:
        if isinstance(until, datetime):
            return int(until.timestamp() * 1000)
        if isinstance(until, (int, float)):
            return int(until)
        text = until.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return int(datetime.fromisoformat(text).timestamp() * 1000)
    except (ValueError, TypeError, OverflowError):
        return 0


def peek_issuer(token: str) -> str | None:
    """The UNVERIFIED ``iss`` of a compact JWT, for routing only."""
    import base64

    try:
        segment = token.split(".")[1]
        padded = segment + "=" * (-len(segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (IndexError, ValueError, TypeError):
        return None
    iss = payload.get("iss") if isinstance(payload, dict) else None
    return iss if isinstance(iss, str) else None


def _key_algs(jwk: Mapping[str, Any]) -> tuple[str, ...]:
    """The algorithms a JWK's type can verify."""
    kty = jwk.get("kty")
    if kty == "RSA":
        return ("RS256", "PS256")
    if kty == "EC":
        return {"P-256": ("ES256",), "P-521": ("ES512",)}.get(str(jwk.get("crv")), ())
    if kty == "OKP" and jwk.get("crv") == "Ed25519":
        return ("EdDSA",)
    return ()


class LegacyIssuerVerifier:
    """Verifies legacy-issuer tokens (used by :class:`~atlas_backend.AtlasBackend`)."""

    def __init__(
        self,
        issuers: Sequence[LegacyIssuer],
        *,
        secret_key: str | None = None,
        api_url: str = DEFAULT_API_URL,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
        leeway: int = 5,
    ) -> None:
        from ._verify import JwksCache

        self._issuers = list(issuers)
        self._secret_key = secret_key
        self._api_url = api_url.rstrip("/")
        self._http = http_client
        self._now = now or (lambda: int(time.time() * 1000))
        self._leeway = leeway
        self._lock = threading.Lock()
        self._subjects: dict[str, tuple[str | None, int]] = {}
        self._caches: dict[str, Any] = {}
        for entry in self._issuers:
            if not entry.issuer:
                raise ValueError("legacy_issuers: every entry needs `issuer`.")
            if bool(entry.jwks_url) == (entry.jwks is not None):
                raise ValueError(
                    f'legacy_issuers: "{entry.issuer}" needs exactly one of `jwks` or `jwks_url`.'
                )
            if not until_ms(entry.until):
                raise ValueError(
                    f'legacy_issuers: "{entry.issuer}" needs a valid `until` '
                    "(the end of the window)."
                )
            if entry.resolve_subject is None and not secret_key:
                raise ValueError(
                    f'legacy_issuers: "{entry.issuer}" maps its `sub` to an Atlas user through '
                    "the Backend API, which needs `secret_key` on AtlasBackend — or give the "
                    "issuer a `resolve_subject`."
                )
            if entry.jwks_url:
                self._caches[entry.issuer] = JwksCache(
                    entry.jwks_url, http_client=http_client, now=now
                )
            else:
                self._caches[entry.issuer] = dict(entry.jwks or {})

    def match(self, iss: str | None) -> LegacyIssuer | None:
        """The configured entry for this ``iss``, when its window is still open."""
        if not iss:
            return None
        for entry in self._issuers:
            if entry.issuer == iss:
                return entry if until_ms(entry.until) > self._now() else None
        return None

    def _keys(self, entry: LegacyIssuer, kid: str | None) -> list[dict[str, Any]]:
        cache = self._caches[entry.issuer]
        keyset = cache if isinstance(cache, dict) else cache.get(kid)
        keys = (keyset or {}).get("keys") or []
        return [k for k in keys if isinstance(k, dict)]

    def verify(self, token: str, entry: LegacyIssuer) -> tuple[str, dict[str, Any] | None]:
        """``("ok", claims)``, ``("no_keys", None)`` or ``("invalid", None)``."""
        import jwt  # PyJWT

        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            return "invalid", None
        alg = header.get("alg")
        kid = header.get("kid") if isinstance(header.get("kid"), str) else None
        allowed = tuple(entry.algorithms or BETTER_AUTH_JWT_ALGS)
        if not isinstance(alg, str) or alg not in allowed:
            return "invalid", None
        keys = self._keys(entry, kid)
        if not keys:
            return "no_keys", None
        candidates = [
            k
            for k in keys
            if (not kid or k.get("kid") == kid)
            and alg in _key_algs(k)
            and k.get("alg") in (None, alg)
        ]
        if not candidates:
            return "invalid", None
        aud = entry.audience
        audience = [aud] if isinstance(aud, str) else (list(aud) if aud is not None else None)
        payload: dict[str, Any] | None = None
        for jwk in candidates:
            try:
                key = jwt.PyJWK(dict(jwk), algorithm=alg).key
                payload = jwt.decode(
                    token,
                    key=key,
                    algorithms=[alg],
                    issuer=entry.issuer,
                    audience=audience,
                    leeway=self._leeway,
                    options={"verify_aud": audience is not None, "require": ["exp"]},
                )
                break
            except (jwt.PyJWTError, ValueError, TypeError):
                continue
        if payload is None:
            return "invalid", None
        # A legacy token without an expiry would outlive the window it is accepted in.
        if not isinstance(payload.get("exp"), (int, float)):
            return "invalid", None
        legacy_sub = payload.get("sub") if isinstance(payload.get("sub"), str) else ""
        if not legacy_sub and isinstance(payload.get("id"), str):
            legacy_sub = payload["id"]
        if not legacy_sub:
            return "invalid", None
        atlas_id = self._resolve(legacy_sub, payload, entry)
        if not atlas_id:
            return "invalid", None
        claims = dict(payload)
        claims["sub"] = atlas_id
        claims["sid"] = payload.get("sid") if isinstance(payload.get("sid"), str) else ""
        claims["external_id"] = legacy_sub
        claims["legacy"] = {"kind": entry.kind, "issuer": entry.issuer, "sub": legacy_sub}
        return "ok", claims

    def _resolve(self, legacy_sub: str, claims: dict[str, Any], entry: LegacyIssuer) -> str | None:
        if entry.resolve_subject is not None:
            try:
                return entry.resolve_subject(legacy_sub, claims) or None
            except Exception:
                return None
        key = f"{entry.issuer}\0{legacy_sub}"
        now = self._now()
        with self._lock:
            hit = self._subjects.get(key)
            if hit is not None and now - hit[1] < SUBJECT_TTL_MS:
                return hit[0]
        owns = self._http is None
        client = self._http or httpx.Client(timeout=10.0)
        try:
            resp = client.get(
                f"{self._api_url}/v1/users",
                params={"external_id": legacy_sub, "limit": "1"},
                headers={
                    "authorization": f"Bearer {self._secret_key}",
                    "accept": "application/json",
                },
            )
            if not resp.is_success:
                return None  # not cached: a transient failure should not stick
            data = resp.json().get("data") or []
            found = data[0].get("id") if data and isinstance(data[0], dict) else None
            atlas_id = found if isinstance(found, str) and found else None
        except (httpx.HTTPError, ValueError, AttributeError):
            return None
        finally:
            if owns:
                client.close()
        with self._lock:
            if len(self._subjects) >= SUBJECT_CACHE_MAX:
                self._subjects.clear()
            self._subjects[key] = (atlas_id, now)
        return atlas_id
