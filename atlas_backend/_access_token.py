"""Access-token verification for your own API (an OAuth 2.0 resource server).

Atlas, acting as your authorization server, issues access tokens for the APIs you
register as resource servers. :class:`AccessTokenVerifier` checks one locally
against the instance JWKS (RS256 or ES256, nothing else): the issuer, expiry, that
it IS an access token, that its ``aud`` names your API (RFC 8707), and the scopes
the route needs. A refusal comes back with the RFC 6750 / RFC 9728
``WWW-Authenticate`` challenge to answer with, so an OAuth or MCP client can
discover Atlas from the 401 (``resource_metadata``) or ask for the missing scope.

Sender-constrained tokens (RFC 9449 DPoP) are enforced: a token bound to a key
(``cnf.jkt``) is accepted only with the ``DPoP`` scheme and a valid DPoP proof from that
key, never as a plain Bearer token. ``require_dpop`` refuses unbound tokens altogether,
and ``dpop_nonces`` demands a server nonce.
"""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from ._dpop import (
    DPOP_ALGS,
    DpopNonceSource,
    DpopReplayStore,
    MemoryDpopReplayStore,
    check_dpop_proof,
)
from ._introspection import IntrospectionError, IntrospectionOptions, Introspector
from ._verify import CLOCK_SKEW_SECONDS, AtlasBackend, JwksCache, jwk_public_key

__all__ = [
    "AccessTokenVerifier",
    "AccessTokenResult",
    "build_www_authenticate",
    "protected_resource_metadata",
    "protected_resource_metadata_path",
    "dpop_header",
]

_AUTHZ = re.compile(r"^(Bearer|DPoP)\s+([A-Za-z0-9\-._~+/]+=*)$", re.IGNORECASE)


@dataclass(frozen=True)
class AccessTokenResult:
    """The verdict. ``ok`` with ``claims`` / ``scopes`` / ``subject`` / ``client_id`` /
    ``dpop_bound`` on success; otherwise ``status`` (400, 401 or 403), ``error`` (``None``
    when no token was sent), ``description`` and ``www_authenticate`` (set it as the
    response header verbatim). ``dpop_nonce``, when set, goes in the ``DPoP-Nonce``
    response header (on success and refusal alike)."""

    ok: bool
    status: int = 200
    error: str | None = None
    description: str = ""
    www_authenticate: str = ""
    claims: dict[str, Any] = field(default_factory=dict)
    scopes: list[str] = field(default_factory=list)
    subject: str = ""
    client_id: str | None = None
    dpop_bound: bool = False
    dpop_nonce: str | None = None


def dpop_header(values: Sequence[str] | None) -> str | None:
    """The single ``DPoP`` header value from all of a request's ``DPoP`` headers; more
    than one is no proof at all."""
    vals = [v for v in (values or []) if v is not None]
    return vals[0] if len(vals) == 1 else None


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_www_authenticate(
    *,
    realm: str | None = None,
    error: str | None = None,
    description: str | None = None,
    scope: Sequence[str] | None = None,
    resource_metadata_url: str | None = None,
    scheme: str = "Bearer",
) -> str:
    """An RFC 6750 / RFC 9449 / RFC 9728 challenge (``scheme`` ``Bearer`` or ``DPoP``;
    a DPoP challenge also lists the accepted proof algorithms). Without ``error`` it is
    the bare "authentication required" challenge (no token was sent), as RFC 6750 §3.1
    asks."""
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
    if scheme == "DPoP":
        parts.append(f"algs={_quote(' '.join(DPOP_ALGS))}")
    else:
        scheme = "Bearer"
    return scheme + (" " + ", ".join(parts) if parts else "")


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
        require_dpop: Refuse every token that is not DPoP-bound (never accept a plain
            Bearer token) and challenge with the ``DPoP`` scheme.
        public_origin: This API's public origin (``https://api.example.com``), used to
            build the DPoP ``htu`` when the request URL is a path. Set it behind a proxy.
        dpop_replay_store: Records DPoP proof ``jti``s; default an in-memory store (one
            process). Share one store when the API runs on several.
        dpop_nonces: When set, every DPoP proof must carry a nonce it issued (RFC 9449
            §9); a proof without a current one is refused with ``use_dpop_nonce`` and
            every result carries ``dpop_nonce`` for the ``DPoP-Nonce`` header.
        introspection: Validate opaque access tokens (and, with ``introspect_jwts``,
            JWTs too) at Atlas's RFC 7662 introspection endpoint, cached briefly. See
            :class:`~atlas_backend.IntrospectionOptions`.
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
        require_dpop: bool = False,
        public_origin: str | None = None,
        dpop_replay_store: DpopReplayStore | None = None,
        dpop_nonces: DpopNonceSource | None = None,
        introspection: IntrospectionOptions | None = None,
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
        self._require_dpop = require_dpop
        self._public_origin = public_origin
        self._nonces = dpop_nonces
        self._replay: DpopReplayStore = dpop_replay_store or MemoryDpopReplayStore(
            now=(lambda: now() / 1000) if now is not None else None
        )
        self.introspector: Introspector | None = (
            Introspector(
                self._issuer,
                introspection,
                http_client=http_client,
                now=(lambda: now() / 1000) if now is not None else None,
            )
            if introspection is not None
            else None
        )
        self.jwks = JwksCache(
            jwks_url or f"{self._issuer}/.well-known/jwks.json", http_client=http_client, now=now
        )

    def verify(
        self,
        authorization: str | None,
        *,
        required_scopes: Sequence[str] = (),
        method: str = "GET",
        url: str = "",
        dpop: str | None = None,
    ) -> AccessTokenResult:
        """Verify an ``Authorization`` header value (``Bearer`` or ``DPoP`` scheme).
        ``method``, ``url`` (absolute, or a path resolved against ``public_origin``) and
        ``dpop`` (the ``DPoP`` header) are what a DPoP proof is checked against. Never
        raises for a bad token."""
        import jwt  # PyJWT

        required = [*self._required, *required_scopes]
        default_scheme = "DPoP" if self._require_dpop else "Bearer"
        nonce = self._nonces.current() if self._nonces is not None else None

        def fail(
            status: int, error: str | None, description: str, scheme: str | None = None
        ) -> AccessTokenResult:
            return AccessTokenResult(
                ok=False,
                status=status,
                error=error,
                description=description,
                dpop_nonce=nonce,
                www_authenticate=build_www_authenticate(
                    realm=self._realm,
                    error=error,
                    description=description,
                    scope=required if error in (None, "insufficient_scope") else None,
                    resource_metadata_url=self._resource_metadata_url,
                    scheme=scheme or default_scheme,
                ),
            )

        value = (authorization or "").strip()
        if not value:
            return fail(401, None, "Authentication required.")
        match = _AUTHZ.match(value)
        if not match:
            return fail(400, "invalid_request", "Malformed Authorization header.")
        presented_dpop = match.group(1).lower() == "dpop"
        token = match.group(2)
        invalid = "The access token is invalid or expired."
        is_jwt = token.count(".") == 2
        introspector = self.introspector
        claims: dict[str, Any]
        if not is_jwt or (introspector is not None and introspector.options.introspect_jwts):
            # An opaque token (or a JWT the caller wants checked live) is validated by
            # Atlas itself.
            if introspector is None:
                return fail(
                    401,
                    "invalid_token",
                    "The access token is not a JWT; configure `introspection` to accept "
                    "opaque tokens.",
                )
            try:
                active = introspector.introspect(token)
            except IntrospectionError:
                return fail(
                    401, "invalid_token", "The access token could not be validated right now."
                )
            if active is None:
                return fail(401, "invalid_token", invalid)
            if "iss" in active and str(active["iss"]).rstrip("/") != self._issuer:
                return fail(
                    401,
                    "invalid_token",
                    "The access token was issued by another authorization server.",
                )
            exp = active.get("exp")
            now_s = self._now() / 1000 if self._now is not None else time.time()
            if isinstance(exp, (int, float)) and exp + CLOCK_SKEW_SECONDS <= now_s:
                return fail(401, "invalid_token", invalid)
            claims = active
        else:
            kid = JwksCache.read_kid(token)
            keyset = self.jwks.get(kid)
            if not keyset or not keyset.get("keys"):
                return fail(
                    401, "invalid_token", "No signing keys are available to verify the token."
                )
            jwk = AtlasBackend._select_jwk(keyset["keys"], kid)
            if jwk is None:
                return fail(401, "invalid_token", invalid)
            try:
                key, alg = jwk_public_key(jwk)
                claims = jwt.decode(
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
        # Sender constraint (RFC 9449). A bound token is only ever a DPoP token.
        cnf = claims.get("cnf")
        jkt: str | None = None
        if isinstance(cnf, dict) and "jkt" in cnf:
            jkt = cnf["jkt"] if isinstance(cnf["jkt"], str) and cnf["jkt"] else None
            if jkt is None:
                return fail(401, "invalid_token", invalid)
        if jkt or self._require_dpop or presented_dpop:
            if not jkt:
                return fail(
                    401,
                    "invalid_token",
                    "This resource requires a DPoP-bound access token.",
                    "DPoP",
                )
            if not presented_dpop:
                return fail(
                    401,
                    "invalid_token",
                    "A DPoP-bound access token must be sent with the DPoP scheme.",
                    "DPoP",
                )
            if not dpop:
                return fail(401, "invalid_dpop_proof", "A DPoP proof is required.", "DPoP")
            now_s = self._now() / 1000 if self._now is not None else time.time()
            refusal = check_dpop_proof(
                dpop.strip(),
                token=token,
                jkt=jkt,
                method=(method or "GET").upper(),
                url=url or "",
                public_origin=self._public_origin,
                now=now_s,
                replay=self._replay,
                nonces=self._nonces,
            )
            if refusal is not None:
                return fail(401, refusal[0], refusal[1], "DPoP")
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
            dpop_bound=bool(jkt),
            dpop_nonce=nonce,
        )

    def request_url(self, absolute_url: str, path_with_query: str) -> str:
        """The URL to check a DPoP ``htu`` against: the path when ``public_origin`` is
        set (it is resolved against it), else the framework's absolute request URL."""
        return path_with_query if self._public_origin else absolute_url


def protected_resource_metadata(
    *,
    resource: str,
    issuer: str,
    scopes_supported: Sequence[str] | None = None,
    dpop_bound_access_tokens_required: bool = False,
) -> dict[str, Any]:
    """The RFC 9728 document for your API; serve it at
    :func:`protected_resource_metadata_path` and point ``resource_metadata_url`` at it.
    ``dpop_bound_access_tokens_required`` advertises that tokens must be DPoP-bound
    (pair it with ``require_dpop``)."""
    doc: dict[str, Any] = {
        "resource": resource,
        "authorization_servers": [issuer.rstrip("/")],
        "bearer_methods_supported": ["header"],
    }
    if scopes_supported:
        doc["scopes_supported"] = list(scopes_supported)
    doc["dpop_signing_alg_values_supported"] = list(DPOP_ALGS)
    if dpop_bound_access_tokens_required:
        doc["dpop_bound_access_tokens_required"] = True
    return doc


def protected_resource_metadata_path(resource: str) -> str:
    """The RFC 9728 well-known path for a resource identifier (path-inserted form)."""
    path = urlparse(resource).path.rstrip("/")
    return f"/.well-known/oauth-protected-resource{path}"
