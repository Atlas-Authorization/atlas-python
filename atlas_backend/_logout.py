"""OpenID Connect Back-Channel Logout 1.0 — verify a ``logout_token``.

When a user signs out of Atlas, Atlas POSTs a signed ``logout_token`` (form
field ``logout_token``) to each app's ``backchannel_logout_uri``. Your endpoint
verifies it with :class:`LogoutTokenVerifier`, ends the matching local
session(s) by ``sid`` (or every session of ``sub`` when there is no ``sid``),
and answers ``200`` with ``Cache-Control: no-store`` (``400`` when invalid).

    from atlas_backend import LogoutTokenVerifier, logout_token_from_form

    verifier = LogoutTokenVerifier(
        issuer="https://atlasauth.net",
        client_id="your_client_id",
    )
    claims = verifier.verify(logout_token_from_form(request_body))

The checks follow §2.6 of the spec: RS256 signature against the issuer's JWKS
(the same cached, throttled JWKS fetch the session verifier uses), ``iss``,
``aud`` contains your client id, ``iat`` present and not in the future,
``exp`` when present, ``jti`` present, the back-channel logout event present,
``sid`` and/or ``sub`` present, no ``nonce``, and ``typ: logout+jwt`` when the
header carries a ``typ``.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import parse_qs

import httpx

from ._verify import (
    CLOCK_SKEW_SECONDS,
    DEFAULT_TTL_MS,
    REFETCH_INTERVAL_MS,
    AtlasBackend,
    JwksCache,
    VerificationError,
    _b64url_decode,
)

#: The event a logout_token must carry (OIDC Back-Channel Logout 1.0 §2.4).
BACKCHANNEL_LOGOUT_EVENT = "http://schemas.openid.net/event/backchannel-logout"

#: The JOSE ``typ`` Atlas sets on a logout_token (§2.4 explicit typing).
LOGOUT_TOKEN_TYPE = "logout+jwt"


@dataclass(frozen=True)
class LogoutTokenClaims:
    """The verified claims of a ``logout_token``.

    At least one of :attr:`sid` and :attr:`sub` is set. With a ``sid``, end that
    one session; with only ``sub``, end every session that user holds at your app.
    """

    jti: str
    iat: int
    sub: str | None = None
    sid: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


def logout_token_from_form(body: bytes | str | Mapping[str, Any]) -> str:
    """Pull ``logout_token`` out of an ``application/x-www-form-urlencoded`` body.

    Accepts the raw body (bytes or str) or an already-parsed form mapping (e.g.
    ``request.form`` / ``request.POST``). Returns ``""`` when it is missing, which
    :meth:`LogoutTokenVerifier.verify` rejects as malformed.
    """
    if isinstance(body, Mapping):
        value = body.get("logout_token")
        if isinstance(value, (list, tuple)):
            value = value[0] if value else ""
        return value if isinstance(value, str) else ""
    text = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    values = parse_qs(text, keep_blank_values=True).get("logout_token") or [""]
    return values[0]


class LogoutTokenVerifier:
    """Verifies OIDC back-channel ``logout_token`` JWTs against the issuer's JWKS.

    Args:
        issuer: The issuer your app's id_tokens carry (for a Sign in with Atlas
            app, ``https://atlasauth.net``; for an instance OAuth client, the
            instance's issuer). Required.
        client_id: Your app's client id; the token's ``aud`` must contain it.
        jwks_url: The issuer's JWKS URL. Defaults to
            ``<issuer>/.well-known/jwks.json``.
        jti_seen: Optional replay guard, called with each verified token's
            ``jti``. Return ``True`` if you have seen it before (the token is then
            refused with reason ``"replayed"``) and record it otherwise. Keep
            entries for at least a few minutes; Atlas logout tokens live two.
        leeway: Clock-skew tolerance in seconds for ``iat`` / ``exp``.
        http_client / now / ttl_ms / refetch_interval_ms: JWKS-cache tuning, as
            on :class:`AtlasBackend`.
    """

    def __init__(
        self,
        *,
        issuer: str,
        client_id: str,
        jwks_url: str | None = None,
        jti_seen: Callable[[str], bool] | None = None,
        http_client: httpx.Client | None = None,
        leeway: int = CLOCK_SKEW_SECONDS,
        now: Callable[[], int] | None = None,
        ttl_ms: int = DEFAULT_TTL_MS,
        refetch_interval_ms: int = REFETCH_INTERVAL_MS,
    ) -> None:
        if not issuer:
            raise ValueError("LogoutTokenVerifier requires an issuer.")
        if not client_id:
            raise ValueError("LogoutTokenVerifier requires a client_id.")
        self._issuer = issuer
        self._client_id = client_id
        self._leeway = leeway
        self._jti_seen = jti_seen
        self._now_ms = now or (lambda: int(time.time() * 1000))
        self.jwks = JwksCache(
            jwks_url or f"{issuer.rstrip('/')}/.well-known/jwks.json",
            http_client=http_client,
            now=now,
            ttl_ms=ttl_ms,
            refetch_interval_ms=refetch_interval_ms,
        )

    def verify(self, logout_token: str) -> LogoutTokenClaims:
        """Verify a ``logout_token``; raises :class:`VerificationError` on failure."""
        import jwt  # PyJWT
        from jwt.algorithms import RSAAlgorithm

        if not logout_token or logout_token.count(".") != 2:
            raise VerificationError(VerificationError.MALFORMED)
        try:
            header = json.loads(_b64url_decode(logout_token.split(".")[0]))
        except (ValueError, json.JSONDecodeError):
            raise VerificationError(VerificationError.MALFORMED) from None
        if not isinstance(header, dict):
            raise VerificationError(VerificationError.MALFORMED)
        typ = header.get("typ")
        if typ is not None and (
            not isinstance(typ, str)
            or typ.lower() not in (LOGOUT_TOKEN_TYPE, f"application/{LOGOUT_TOKEN_TYPE}")
        ):
            raise VerificationError(VerificationError.INVALID)

        kid = header.get("kid") if isinstance(header.get("kid"), str) else None
        keyset = self.jwks.get(kid)
        if not keyset or not keyset.get("keys"):
            raise VerificationError(VerificationError.NO_KEYS)
        jwk = AtlasBackend._select_jwk(keyset["keys"], kid)
        if jwk is None:
            raise VerificationError(VerificationError.INVALID)

        try:
            key: Any = RSAAlgorithm.from_jwk(json.dumps(jwk))
            claims = jwt.decode(
                logout_token,
                key=key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=self._client_id,
                leeway=self._leeway,
                options={"require": ["iat", "jti"], "verify_iat": False},
            )
        except jwt.InvalidTokenError:
            raise VerificationError(VerificationError.INVALID) from None

        iat = claims.get("iat")
        now_s = self._now_ms() / 1000
        if not isinstance(iat, (int, float)) or iat > now_s + self._leeway:
            raise VerificationError(VerificationError.INVALID)
        jti = claims.get("jti")
        if not isinstance(jti, str) or not jti:
            raise VerificationError(VerificationError.INVALID)
        events = claims.get("events")
        if not isinstance(events, dict) or not isinstance(
            events.get(BACKCHANNEL_LOGOUT_EVENT), dict
        ):
            raise VerificationError(VerificationError.INVALID)
        if "nonce" in claims:
            raise VerificationError(VerificationError.INVALID)
        sub = claims.get("sub")
        sid = claims.get("sid")
        sub = sub if isinstance(sub, str) and sub else None
        sid = sid if isinstance(sid, str) and sid else None
        if sub is None and sid is None:
            raise VerificationError(VerificationError.INVALID)

        if self._jti_seen is not None and self._jti_seen(jti):
            raise VerificationError(VerificationError.REPLAYED)

        return LogoutTokenClaims(jti=jti, iat=int(iat), sub=sub, sid=sid, raw=claims)
