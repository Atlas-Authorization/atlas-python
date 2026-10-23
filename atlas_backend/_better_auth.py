"""Moving from Better Auth to Atlas without signing anyone out.

During the migration window a returning user still carries their Better Auth
session cookie (``better-auth.session_token``, ``__Secure-`` prefixed over https).
It is HttpOnly, so only your server can read it. The bridge reads it, exchanges it
ONCE with Atlas through the Backend API (``POST /v1/migrations/better_auth/exchange``,
secret key, forwarding the end user's IP and user agent), sets the Atlas session as
your own first-party cookies and clears the Better Auth cookies. Atlas finds the
session in your import (or asks your old app, with the live fallback on) and runs
the normal sign-in path on it — MFA policy included: a user who still owes a second
factor is sent to finish it.

Framework-neutral: :class:`BetterAuthBridge` returns a :class:`BridgeDecision` with
the cookies to set and clear; the Django middleware and the Flask extension render
it (``ATLAS_BETTER_AUTH_BRIDGE``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from ._errors import AtlasError

if TYPE_CHECKING:
    from ._client import AsyncAtlasClient, AtlasClient

__all__ = [
    "BETTER_AUTH_COOKIE_PREFIX",
    "BETTER_AUTH_EXCHANGE_PATH",
    "BetterAuthBridge",
    "AsyncBetterAuthBridge",
    "BetterAuthExchangeResult",
    "BridgeCookie",
    "BridgeDecision",
    "better_auth_cookie_names",
    "read_better_auth_session_cookie",
    "exchange_better_auth_session",
    "async_exchange_better_auth_session",
    "serialize_bridge_cookie",
]

#: Better Auth's default cookie prefix (``advanced.cookiePrefix``).
BETTER_AUTH_COOKIE_PREFIX = "better-auth"
#: The Backend API path of the secret-key exchange.
BETTER_AUTH_EXCHANGE_PATH = "/v1/migrations/better_auth/exchange"

#: Refusal outcomes Atlas reports in ``meta.bridge_outcome``.
_KNOWN_OUTCOMES = frozenset(
    {
        "closed",
        "invalid",
        "signature_invalid",
        "expired",
        "reused",
        "user_unavailable",
        "rate_limited",
    }
)
#: Refusals that say the Better Auth session will never exchange: its cookies are cleared.
_FINAL_OUTCOMES = frozenset(
    {"invalid", "signature_invalid", "expired", "reused", "user_unavailable"}
)

Refusal = Literal[
    "closed",
    "invalid",
    "signature_invalid",
    "expired",
    "reused",
    "user_unavailable",
    "rate_limited",
    "unavailable",
]


def better_auth_cookie_names(prefix: str = BETTER_AUTH_COOKIE_PREFIX) -> dict[str, list[str]]:
    """The Better Auth cookies the bridge reads (``session_token``, the ``__Secure-``
    name first) and clears (``all``)."""
    base = [
        f"{prefix}.{n}" for n in ("session_token", "session_data", "account_data", "dont_remember")
    ]
    return {
        "session_token": [f"__Secure-{prefix}.session_token", f"{prefix}.session_token"],
        "all": [f"__Secure-{n}" for n in base] + base,
    }


def _parse_cookie_header(header: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    if not header:
        return out
    for part in header.split(";"):
        key, sep, value = part.strip().partition("=")
        if sep and key and key not in out:
            out[key] = value
    return out


def _cookies(source: str | Mapping[str, str] | None) -> Mapping[str, str]:
    if source is None or isinstance(source, str):
        return _parse_cookie_header(source)
    return source


def read_better_auth_session_cookie(
    cookies: str | Mapping[str, str] | None,
    *,
    cookie_prefix: str = BETTER_AUTH_COOKIE_PREFIX,
    cookie_name: str | None = None,
) -> str | None:
    """The raw Better Auth session cookie value from a ``Cookie`` header (or a parsed
    cookie mapping), the ``__Secure-`` name first; ``None`` when absent.
    ``cookie_name`` overrides the name when the old app set
    ``advanced.cookies.session_token.name``."""
    jar = _cookies(cookies)
    names = (
        [f"__Secure-{cookie_name}", cookie_name]
        if cookie_name
        else better_auth_cookie_names(cookie_prefix)["session_token"]
    )
    for name in names:
        value = jar.get(name)
        if value:
            return value
    return None


@dataclass(frozen=True)
class BetterAuthExchangeResult:
    """The classified outcome of an exchange.

    ``kind`` is ``"session"`` (``jwt``, ``refresh_token``, ``session_id``, ``user_id``,
    ``expires_in``), ``"needs_mfa"`` (``attempt_id`` and ``status``: the Better Auth
    session is spent, the user finishes the second factor) or ``"refused"``
    (``outcome``; ``http_status`` 0 for a transport failure)."""

    kind: Literal["session", "needs_mfa", "refused"]
    jwt: str = ""
    refresh_token: str = ""
    session_id: str = ""
    user_id: str = ""
    expires_in: int = 0
    attempt_id: str = ""
    status: str = ""
    outcome: Refusal | None = None
    http_status: int = 200


def _classify_success(data: Any) -> BetterAuthExchangeResult:
    if isinstance(data, dict):
        if data.get("object") == "session_tokens" and data.get("jwt") and data.get("refresh_token"):
            return BetterAuthExchangeResult(
                kind="session",
                jwt=str(data["jwt"]),
                refresh_token=str(data["refresh_token"]),
                session_id=str(data.get("session_id") or ""),
                user_id=str(data.get("user_id") or ""),
                expires_in=int(data.get("expires_in") or 0),
            )
        if (
            data.get("object") == "sign_in_attempt"
            and data.get("id")
            and data.get("status") in ("needs_second_factor", "needs_mfa_enrollment")
        ):
            return BetterAuthExchangeResult(
                kind="needs_mfa", attempt_id=str(data["id"]), status=str(data["status"])
            )
    return BetterAuthExchangeResult(kind="refused", outcome="unavailable", http_status=200)


def _classify_error(err: AtlasError) -> BetterAuthExchangeResult:
    if err.status == 429:
        return BetterAuthExchangeResult(kind="refused", outcome="rate_limited", http_status=429)
    meta = err.errors[0].get("meta") if err.errors else None
    outcome = meta.get("bridge_outcome") if isinstance(meta, dict) else None
    if outcome in _KNOWN_OUTCOMES:
        return BetterAuthExchangeResult(kind="refused", outcome=outcome, http_status=err.status)
    # Anything else (a 5xx, a guard refusal, an unparsable body) is not a verdict on
    # the Better Auth session: keep it and retry later.
    return BetterAuthExchangeResult(kind="refused", outcome="unavailable", http_status=err.status)


def exchange_better_auth_session(
    client: AtlasClient,
    token: str,
    *,
    client_ip: str | None = None,
    user_agent: str | None = None,
    remember: bool | None = None,
) -> BetterAuthExchangeResult:
    """Exchange a Better Auth session (the raw cookie value or the bare token) for an
    Atlas session over the Backend API. Never raises: a transport failure is
    ``refused``/``unavailable``, so the caller keeps the Better Auth cookie and tries
    again on a later request. Pass the END USER's ``client_ip`` and ``user_agent``."""
    try:
        data = client.better_auth_bridge.exchange(
            token, client_ip=client_ip, user_agent=user_agent, remember=remember
        )
    except AtlasError as err:
        return _classify_error(err)
    except (httpx.HTTPError, ValueError):
        return BetterAuthExchangeResult(kind="refused", outcome="unavailable", http_status=0)
    return _classify_success(data)


async def async_exchange_better_auth_session(
    client: AsyncAtlasClient,
    token: str,
    *,
    client_ip: str | None = None,
    user_agent: str | None = None,
    remember: bool | None = None,
) -> BetterAuthExchangeResult:
    """The async peer of :func:`exchange_better_auth_session`."""
    try:
        data = await client.better_auth_bridge.exchange(
            token, client_ip=client_ip, user_agent=user_agent, remember=remember
        )
    except AtlasError as err:
        return _classify_error(err)
    except (httpx.HTTPError, ValueError):
        return BetterAuthExchangeResult(kind="refused", outcome="unavailable", http_status=0)
    return _classify_success(data)


@dataclass(frozen=True)
class BridgeCookie:
    """A cookie to set (or, with ``max_age=0``, clear) on the response."""

    name: str
    value: str
    path: str = "/"
    domain: str | None = None
    http_only: bool = False
    same_site: Literal["lax", "strict", "none"] | None = None
    secure: bool = False
    max_age: int | None = None


def serialize_bridge_cookie(cookie: BridgeCookie) -> str:
    """A :class:`BridgeCookie` as a ``Set-Cookie`` header value."""
    parts = [f"{cookie.name}={cookie.value}", f"Path={cookie.path or '/'}"]
    if cookie.domain:
        parts.append(f"Domain={cookie.domain}")
    if cookie.max_age is not None:
        parts.append(f"Max-Age={cookie.max_age}")
        if cookie.max_age == 0:
            parts.append("Expires=Thu, 01 Jan 1970 00:00:00 GMT")
    if cookie.http_only:
        parts.append("HttpOnly")
    if cookie.secure:
        parts.append("Secure")
    if cookie.same_site:
        parts.append(f"SameSite={cookie.same_site.capitalize()}")
    return "; ".join(parts)


@dataclass(frozen=True)
class BridgeDecision:
    """What the bridge decided for one request.

    * ``none`` — no Better Auth cookie, or an Atlas session is already present.
    * ``signed_in`` — set ``cookies`` and re-enter (redirect to the same URL).
    * ``needs_mfa`` — send the browser to your sign-in page carrying the attempt
      (:meth:`continuation_url`); ``cookies`` clears the spent Better Auth cookies.
    * ``refused`` — carry on unauthenticated; ``cookies`` clears the Better Auth
      cookies only when the refusal is final (invalid, expired, reused, ...).
    """

    action: Literal["none", "signed_in", "needs_mfa", "refused"]
    cookies: list[BridgeCookie] = field(default_factory=list)
    session: BetterAuthExchangeResult | None = None
    attempt_id: str = ""
    status: str = ""
    outcome: Refusal | None = None

    def continuation_url(self, url: str) -> str:
        """``url`` with ``__atlas_attempt`` / ``__atlas_status`` set (``needs_mfa``)."""
        parts = urlsplit(url)
        query = [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k not in ("__atlas_attempt", "__atlas_status")
        ]
        query += [("__atlas_attempt", self.attempt_id), ("__atlas_status", self.status)]
        return urlunsplit(parts._replace(query=urlencode(query)))


def _client_ip_from(headers: Mapping[str, str] | None) -> str | None:
    if not headers:
        return None
    lowered = {k.lower(): v for k, v in headers.items()}
    xff = (lowered.get("x-forwarded-for") or "").split(",")[0].strip()
    return xff or (lowered.get("x-real-ip") or "").strip() or None


class _BridgeBase:
    def __init__(
        self,
        *,
        cookie_prefix: str = BETTER_AUTH_COOKIE_PREFIX,
        cookie_name: str | None = None,
        better_auth_cookie_domain: str | None = None,
        secure: bool = True,
    ) -> None:
        self.cookie_prefix = cookie_prefix
        self.cookie_name = cookie_name
        self.better_auth_cookie_domain = better_auth_cookie_domain
        self.secure = secure

    def _clear(self) -> list[BridgeCookie]:
        names = better_auth_cookie_names(self.cookie_prefix)["all"]
        if self.cookie_name:
            names = names + [self.cookie_name, f"__Secure-{self.cookie_name}"]
        return [
            BridgeCookie(
                name=n,
                value="",
                max_age=0,
                domain=self.better_auth_cookie_domain,
                # A `__Secure-` cookie can only be overwritten by a Secure Set-Cookie.
                secure=n.startswith("__Secure-"),
            )
            for n in names
        ]

    def _token(self, cookies: str | Mapping[str, str] | None) -> str | None:
        jar = _cookies(cookies)
        token = read_better_auth_session_cookie(
            jar, cookie_prefix=self.cookie_prefix, cookie_name=self.cookie_name
        )
        # Already on Atlas: leave the old cookie for the old app's own expiry.
        if not token or jar.get("__session") or jar.get("__atlas_rt"):
            return None
        return token

    def _decide(self, result: BetterAuthExchangeResult) -> BridgeDecision:
        if result.kind == "session":
            return BridgeDecision(
                action="signed_in",
                session=result,
                cookies=[
                    BridgeCookie("__session", result.jwt, same_site="lax", secure=self.secure),
                    BridgeCookie(
                        "__atlas_rt",
                        result.refresh_token,
                        http_only=True,
                        same_site="lax",
                        secure=self.secure,
                    ),
                    *self._clear(),
                ],
            )
        if result.kind == "needs_mfa":
            return BridgeDecision(
                action="needs_mfa",
                attempt_id=result.attempt_id,
                status=result.status,
                cookies=self._clear(),
            )
        outcome = result.outcome or "unavailable"
        return BridgeDecision(
            action="refused",
            outcome=outcome,
            cookies=self._clear() if outcome in _FINAL_OUTCOMES else [],
        )


class BetterAuthBridge(_BridgeBase):
    """The bridge as a function of a request: call it from middleware before your
    normal auth check. It does nothing (no network) for a request without a Better
    Auth cookie or with an Atlas session (``__session`` / ``__atlas_rt``) present.

    Args:
        client: An :class:`AtlasClient` on the instance secret key.
        cookie_prefix: Better Auth's ``advanced.cookiePrefix``.
        cookie_name: The session cookie's full name, when the old app overrode it.
        better_auth_cookie_domain: The ``domain`` the Better Auth cookies were set on
            (its ``crossSubDomainCookies.domain``), so they clear.
        secure: Mark the Atlas cookies ``Secure``. Set False only for plain-http
            local development.
    """

    def __init__(
        self,
        client: AtlasClient,
        *,
        cookie_prefix: str = BETTER_AUTH_COOKIE_PREFIX,
        cookie_name: str | None = None,
        better_auth_cookie_domain: str | None = None,
        secure: bool = True,
        exchange: Callable[..., BetterAuthExchangeResult] | None = None,
    ) -> None:
        super().__init__(
            cookie_prefix=cookie_prefix,
            cookie_name=cookie_name,
            better_auth_cookie_domain=better_auth_cookie_domain,
            secure=secure,
        )
        self._client = client
        self._exchange = exchange or exchange_better_auth_session

    def __call__(
        self,
        cookies: str | Mapping[str, str] | None,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> BridgeDecision:
        """Decide for one request. ``cookies`` is the ``Cookie`` header or a parsed
        mapping; ``client_ip`` is the end user's IP as your framework resolved it
        (falls back to the first ``X-Forwarded-For`` hop in ``headers``)."""
        token = self._token(cookies)
        if token is None:
            return BridgeDecision(action="none")
        result = self._exchange(
            self._client,
            token,
            client_ip=client_ip or _client_ip_from(headers),
            user_agent=user_agent,
        )
        return self._decide(result)


class AsyncBetterAuthBridge(_BridgeBase):
    """The async peer of :class:`BetterAuthBridge` (an :class:`AsyncAtlasClient`)."""

    def __init__(
        self,
        client: AsyncAtlasClient,
        *,
        cookie_prefix: str = BETTER_AUTH_COOKIE_PREFIX,
        cookie_name: str | None = None,
        better_auth_cookie_domain: str | None = None,
        secure: bool = True,
    ) -> None:
        super().__init__(
            cookie_prefix=cookie_prefix,
            cookie_name=cookie_name,
            better_auth_cookie_domain=better_auth_cookie_domain,
            secure=secure,
        )
        self._client = client

    async def __call__(
        self,
        cookies: str | Mapping[str, str] | None,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> BridgeDecision:
        token = self._token(cookies)
        if token is None:
            return BridgeDecision(action="none")
        result = await async_exchange_better_auth_session(
            self._client,
            token,
            client_ip=client_ip or _client_ip_from(headers),
            user_agent=user_agent,
        )
        return self._decide(result)


def bridge_from_setting(
    setting: Any, *, secret_key: str | None, base_url: str | None
) -> tuple[BetterAuthBridge, str | None] | None:
    """Build a bridge from a framework ``ATLAS_BETTER_AUTH_BRIDGE`` setting
    (``True`` or a mapping of ``cookie_prefix``, ``cookie_name``,
    ``better_auth_cookie_domain``, ``secure``, ``sign_in_url``). Returns the bridge
    and the sign-in URL, or ``None`` when the setting is off."""
    if not setting:
        return None
    if not secret_key:
        raise RuntimeError(
            "ATLAS_BETTER_AUTH_BRIDGE needs ATLAS_SECRET_KEY: the exchange goes through "
            "the Backend API with the instance secret key."
        )
    opts: Mapping[str, Any] = setting if isinstance(setting, Mapping) else {}
    from ._client import AtlasClient

    client = AtlasClient(secret_key, base_url=base_url) if base_url else AtlasClient(secret_key)
    bridge = BetterAuthBridge(
        client,
        cookie_prefix=opts.get("cookie_prefix") or BETTER_AUTH_COOKIE_PREFIX,
        cookie_name=opts.get("cookie_name"),
        better_auth_cookie_domain=opts.get("better_auth_cookie_domain"),
        secure=opts.get("secure", True) is not False,
    )
    return bridge, opts.get("sign_in_url")
