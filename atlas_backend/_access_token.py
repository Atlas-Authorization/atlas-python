"""Access-token verification for your own API (an OAuth 2.0 resource server).

Atlas, acting as your authorization server, issues access tokens for the APIs you
register as resource servers. :class:`AccessTokenVerifier` checks one locally
against the instance JWKS (RS256 or ES256, nothing else): the issuer, expiry, that
it IS an access token, that its ``aud`` names your API (RFC 8707), and the scopes
the route needs. A refusal comes back with the RFC 6750 / RFC 9728
``WWW-Authenticate`` challenge to answer with, so an OAuth or MCP client can
discover Atlas from the 401 (``resource_metadata``) or ask for the missing scope.

DPoP-bound tokens (``cnf.jkt``) are refused: this verifier checks Bearer tokens
only.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from ._verify import CLOCK_SKEW_SECONDS, AtlasBackend, JwksCache, jwk_public_key

__all__ = [
    "AccessTokenVerifier",
    "AccessTokenResult",
    "build_www_authenticate",
    "protected_resource_metadata",
    "protected_resource_metadata_path",
]

_AUTHZ = re.compile(r"^(Bearer|DPoP)\s+([A-Za-z0-9\-._~+/]+=*)$", re.IGNORECASE)


@dataclass(frozen=True)
class AccessTokenResult:
    """The verdict. ``ok`` with ``claims`` / ``scopes`` / ``subject`` / ``client_id`` on
    success; otherwise ``status`` (400, 401 or 403), ``error`` (``None`` when no token
    was sent), ``description`` and ``www_authenticate`` (set it as the response header
    verbatim)."""

    ok: bool
    status: int = 200
    error: str | None = None
    description: str = ""
    www_authenticate: str = ""
    claims: dict[str, Any] = field(default_factory=dict)
    scopes: list[str] = field(default_factory=list)
    subject: str = ""
    client_id: str | None = None


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_www_authenticate(
    *,
    realm: str | None = None,
    error: str | None = None,
    description: str | None = None,
    scope: Sequence[str] | None = None,
    resource_metadata_url: str | None = None,
) -> str:
    """An RFC 6750 / RFC 9728 Bearer challenge. Without ``error`` it is the bare
    "authentication required" challenge (no token was sent), as RFC 6750 §3.1 asks."""
    parts: list[str] = []
    if realm:
        parts.append(f"realm={_quote(realm)}")
    if error:
        parts.append(f"error={_quote(error)}")
        if description:
            parts.append(f"error_description={_quote(description)}")
    if scope:
        parts.append(f"scope={_quote(' '.join(scope))}")
    if resource_metadata_url:
        parts.append(f"resource_metadata={_quote(resource_metadata_url)}")
    return "Bearer" + (" " + ", ".join(parts) if parts else "")


class AccessTokenVerifier:
    """Verifies Atlas-issued access tokens for one API. Build it once (it holds the
    JWKS cache) and call :meth:`verify` per request.

    Args:
        issuer: Your instance's issuer. Required.
        audience: Your API's identifier(s) (the resource server identifier); the
            token's ``aud`` must contain one. Pass ``False`` only to accept tokens
            without an audience check (userinfo-style tokens).
        required_scopes: Scopes every request must carry.
        jwks_url: Defaults to ``{issuer}/.well-known/jwks.json``.
        resource_metadata_url: Advertised in every challenge as ``resource_metadata``.
        realm: The ``WWW-Authenticate`` realm.
    """

    def __init__(
        self,
        *,
        issuer: str,
        audience: str | Sequence[str] | bool,
        required_scopes: Sequence[str] = (),
        jwks_url: str | None = None,
        resource_metadata_url: str | None = None,
        realm: str | None = None,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        if not issuer:
            raise ValueError("AccessTokenVerifier requires an issuer.")
        if audience is True or (not isinstance(audience, bool) and not audience):
            raise ValueError("AccessTokenVerifier requires an audience (or audience=False).")
        self._issuer = issuer.rstrip("/")
        self._audiences: list[str] | None = (
            None
            if audience is False
            else [audience]
            if isinstance(audience, str)
            else list(audience)
        )
        self._required = list(required_scopes)
        self._resource_metadata_url = resource_metadata_url
        self._realm = realm
        self._now = now
        self.jwks = JwksCache(
            jwks_url or f"{self._issuer}/.well-known/jwks.json", http_client=http_client, now=now
        )

    def verify(
        self, authorization: str | None, *, required_scopes: Sequence[str] = ()
    ) -> AccessTokenResult:
        """Verify an ``Authorization`` header value. Never raises for a bad token."""
        import jwt  # PyJWT

        required = [*self._required, *required_scopes]

        def fail(status: int, error: str | None, description: str) -> AccessTokenResult:
            return AccessTokenResult(
                ok=False,
                status=status,
                error=error,
                description=description,
                www_authenticate=build_www_authenticate(
                    realm=self._realm,
                    error=error,
                    description=description,
                    scope=required if error in (None, "insufficient_scope") else None,
                    resource_metadata_url=self._resource_metadata_url,
                ),
            )

        value = (authorization or "").strip()
        if not value:
            return fail(401, None, "Authentication required.")
        match = _AUTHZ.match(value)
        if not match:
            return fail(400, "invalid_request", "Malformed Authorization header.")
        if match.group(1).lower() == "dpop":
            return fail(401, "invalid_token", "DPoP-bound access tokens are not accepted here.")
        token = match.group(2)
        if token.count(".") != 2:
            return fail(401, "invalid_token", "The access token is malformed.")
        kid = JwksCache.read_kid(token)
        keyset = self.jwks.get(kid)
        if not keyset or not keyset.get("keys"):
            return fail(401, "invalid_token", "No signing keys are available to verify the token.")
        jwk = AtlasBackend._select_jwk(keyset["keys"], kid)
        invalid = "The access token is invalid or expired."
        if jwk is None:
            return fail(401, "invalid_token", invalid)
        try:
            key, alg = jwk_public_key(jwk)
            claims: dict[str, Any] = jwt.decode(
                token,
                key=key,
                algorithms=[alg],
                issuer=self._issuer,
                leeway=CLOCK_SKEW_SECONDS,
                options={"verify_aud": False, "require": ["exp"]},
            )
        except jwt.InvalidTokenError:
            return fail(401, "invalid_token", invalid)
        if self._now is not None:
            now_s = self._now() / 1000
            exp = claims.get("exp")
            if not isinstance(exp, (int, float)) or now_s > exp + CLOCK_SKEW_SECONDS:
                return fail(401, "invalid_token", invalid)
        token_use = claims.get("token_use")
        if token_use is not None and token_use != "access_token":
            return fail(401, "invalid_token", "The token is not an access token.")
        if self._audiences is not None:
            aud = claims.get("aud")
            auds = aud if isinstance(aud, list) else [aud] if isinstance(aud, str) else []
            if not any(a in self._audiences for a in auds):
                return fail(
                    401, "invalid_token", "The access token was not issued for this resource."
                )
        cnf = claims.get("cnf")
        if isinstance(cnf, dict) and "jkt" in cnf:
            return fail(401, "invalid_token", "DPoP-bound access tokens are not accepted here.")
        scope = claims.get("scope")
        scopes = scope.split() if isinstance(scope, str) else []
        granted = set(scopes)
        perms = claims.get("permissions")
        if isinstance(perms, list):
            granted.update(p for p in perms if isinstance(p, str))
        missing = [s for s in required if s not in granted]
        if missing:
            return fail(
                403,
                "insufficient_scope",
                f"The access token is missing the required scope(s): {' '.join(missing)}.",
            )
        client_id = claims.get("client_id") or claims.get("azp")
        return AccessTokenResult(
            ok=True,
            claims=claims,
            scopes=scopes,
            subject=str(claims.get("sub", "")),
            client_id=client_id if isinstance(client_id, str) else None,
        )


def protected_resource_metadata(
    *, resource: str, issuer: str, scopes_supported: Sequence[str] | None = None
) -> dict[str, Any]:
    """The RFC 9728 document for your API; serve it at
    :func:`protected_resource_metadata_path` and point ``resource_metadata_url`` at it."""
    doc: dict[str, Any] = {
        "resource": resource,
        "authorization_servers": [issuer.rstrip("/")],
        "bearer_methods_supported": ["header"],
    }
    if scopes_supported:
        doc["scopes_supported"] = list(scopes_supported)
    return doc


def protected_resource_metadata_path(resource: str) -> str:
    """The RFC 9728 well-known path for a resource identifier (path-inserted form)."""
    path = urlparse(resource).path.rstrip("/")
    return f"/.well-known/oauth-protected-resource{path}"
