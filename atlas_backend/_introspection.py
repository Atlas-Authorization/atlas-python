"""RFC 7662 token introspection at Atlas, for opaque (reference) access tokens.

An API, client or instance set to the ``opaque`` access-token format gets ``oat_…``
tokens only Atlas can read. :class:`Introspector` asks Atlas's introspection endpoint
with your API's own client credentials (``client_secret_basic``) and caches the answer
by the token's SHA-256 (the token itself is never kept). The client must be a
confidential client the API lists in ``introspection_client_ids`` (or the client the
tokens are issued to).
"""

from __future__ import annotations

import base64
import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote_plus

import httpx

__all__ = ["IntrospectionOptions", "Introspector", "IntrospectionError"]


class IntrospectionError(Exception):
    """Atlas could not be reached, or answered with a non-2xx status."""


@dataclass(frozen=True)
class IntrospectionOptions:
    """``endpoint`` defaults to ``{issuer}/oauth2/introspect``. ``cache_ttl_seconds``
    (default 60, never past the token's ``exp``) and ``negative_cache_ttl_seconds``
    (default 10; 0 disables) bound how long an answer is reused; ``cache_max`` (default
    10 000) bounds how many are kept. ``introspect_jwts`` also sends JWT access tokens
    to Atlas, so a revoked grant or a banned user is refused before the token expires."""

    client_id: str
    client_secret: str
    endpoint: str | None = None
    cache_ttl_seconds: float = 60
    negative_cache_ttl_seconds: float = 10
    cache_max: int = 10_000
    introspect_jwts: bool = False


class Introspector:
    def __init__(
        self,
        issuer: str,
        options: IntrospectionOptions,
        *,
        http_client: httpx.Client | None = None,
        now: Callable[[], float] | None = None,
    ) -> None:
        if not options.client_id or not options.client_secret:
            raise ValueError("introspection needs client_id and client_secret.")
        self.options = options
        self._endpoint = options.endpoint or f"{issuer.rstrip('/')}/oauth2/introspect"
        self._http = http_client or httpx.Client(timeout=10.0)
        self._now = now or time.time
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, tuple[dict[str, Any] | None, float]] = OrderedDict()
        creds = f"{quote_plus(options.client_id)}:{quote_plus(options.client_secret)}"
        self._basic = "Basic " + base64.b64encode(creds.encode()).decode()

    @staticmethod
    def cache_key(token: str) -> str:
        digest = hashlib.sha256(token.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def introspect(self, token: str) -> dict[str, Any] | None:
        """The claims of an active access token, or ``None`` for an inactive one (also
        for a refresh token). Raises :class:`IntrospectionError` when Atlas could not be
        asked."""
        key = self.cache_key(token)
        now = self._now()
        with self._lock:
            hit = self._cache.get(key)
            if hit is not None:
                if hit[1] > now:
                    return hit[0]
                del self._cache[key]
        try:
            res = self._http.post(
                self._endpoint,
                data={"token": token, "token_type_hint": "access_token"},
                headers={"authorization": self._basic, "accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise IntrospectionError(str(exc)) from exc
        if res.status_code < 200 or res.status_code > 299:
            raise IntrospectionError(f"Introspection failed with HTTP {res.status_code}.")
        try:
            body = res.json()
        except ValueError as exc:
            raise IntrospectionError("Introspection answered with invalid JSON.") from exc
        claims = (
            body
            if isinstance(body, dict)
            and body.get("active") is True
            and body.get("token_use") != "refresh_token"
            else None
        )
        now = self._now()
        if claims is not None:
            until = now + self.options.cache_ttl_seconds
            exp = claims.get("exp")
            if isinstance(exp, (int, float)):
                until = min(until, float(exp))
        else:
            until = now + self.options.negative_cache_ttl_seconds
        if until > now:
            with self._lock:
                self._cache[key] = (claims, until)
                self._cache.move_to_end(key)
                if len(self._cache) > self.options.cache_max:
                    for k in [k for k, v in self._cache.items() if v[1] <= now]:
                        del self._cache[k]
                    while len(self._cache) > self.options.cache_max:
                        self._cache.popitem(last=False)
        return claims
