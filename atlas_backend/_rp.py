"""A relying party for Atlas's hosted sign-in: your server sends the user to Atlas, verifies who
came back and keeps its own session.

    from atlas_backend import RelyingParty

    rp = RelyingParty(
        issuer="https://id.example.com",          # https:// + your Frontend API host
        client_id="client_...",
        client_secret="...",
        redirect_uri="https://app.example.com/auth/callback",
        secret=os.environ["SESSION_SECRET"],       # 32+ characters; seals the short-lived flow cookie
        on_signed_in=create_my_session,            # (user, tokens, request, result) -> RpResponse | None
    )
    response = rp.handle(request)                  # GET /auth/sign-in, GET /auth/callback, POST /auth/sign-out

Authorization code with PKCE (S256), a ``state`` and a ``nonce`` held in one AES-GCM sealed,
httpOnly, 10-minute cookie. The ID token's algorithm is pinned (RS256 / ES256 from the published
key) and ``iss``, ``aud`` / ``azp``, ``exp`` / ``iat``, ``nonce`` and ``at_hash`` are checked.
Step-up (:meth:`RelyingParty.require_recent_auth`), keep-alive (:meth:`~RelyingParty.touch_if_due`),
server-side sign-out and back-channel logout with a sid store are included. The Django, Flask and
FastAPI/Starlette adapters turn :class:`RpRequest` / :class:`RpResponse` into their own types.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import parse_qs, quote, urlencode, urlsplit

import httpx

from ._logout import LogoutTokenClaims, LogoutTokenVerifier, logout_token_from_form
from ._transport import DEFAULT_BASE_URL
from ._verify import SIGNING_ALGS, JwksCache, VerificationError, jwk_public_key

FLOW_COOKIE = "atlas_oidc"
FLOW_MAX_AGE_SECONDS = 600
CONFIRM_NOW_WINDOW_SECONDS = 60
_SEALED = "s1."
_NOT_FORWARDABLE = frozenset(
    "response_type client_id redirect_uri state nonce code_challenge code_challenge_method "
    "scope return_to id_token_hint request request_uri".split()
)
_PASSTHROUGH = (
    ("prompt", "prompt"),
    ("login_hint", "login_hint"),
    ("ui_locales", "ui_locales"),
    ("organization", "organization"),
    ("return_to", "return_to"),
)
_OWNED = frozenset(
    "response_type client_id redirect_uri state nonce code_challenge code_challenge_method".split()
)


def is_safe_return_to(value: str) -> bool:
    """A plain same-site path: one leading ``/``, no scheme or authority, no backslash or control characters."""
    return bool(re.fullmatch(r"/(?![/\\])[^\\\x00-\x1f\x7f]*", value))


class OidcError(Exception):
    """A sign-in failure. ``code`` is one of ``state_mismatch``, ``issuer_mismatch``,
    ``invalid_request``, ``invalid_token``, ``token_exchange_failed``, ``access_denied``,
    ``discovery_failed``, ``reauthentication_required`` or ``subject_mismatch``."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        oauth_error: str | None = None,
        description: str | None = None,
        status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.oauth_error = oauth_error
        self.description = description
        self.status = status
        #: A ``Set-Cookie`` value that removes the flow cookie; send it with your error response.
        self.clear_cookie: str | None = None


@dataclass
class RpRequest:
    """The request fields the relying party reads, framework-neutral."""

    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    #: The parsed form body (POST), when there is one (the back-channel ``logout_token``).
    form: Mapping[str, str] | None = None

    def header(self, name: str) -> str | None:
        for k, v in self.headers.items():
            if k.lower() == name:
                return v
        return None


@dataclass
class RpResponse:
    """An HTTP answer as data: status, header pairs (``Set-Cookie`` may repeat), body."""

    status: int = 200
    headers: list[tuple[str, str]] = field(default_factory=list)
    body: bytes = b""

    def header(self, name: str) -> str | None:
        for k, v in self.headers:
            if k.lower() == name.lower():
                return v
        return None

    def append_cookie(self, cookie: str | None) -> RpResponse:
        if cookie:
            self.headers.append(("set-cookie", cookie))
        return self

    @property
    def location(self) -> str | None:
        return self.header("location")


def _redirect(location: str, cookies: Sequence[str] = ()) -> RpResponse:
    out = RpResponse(302, [("location", location), ("cache-control", "no-store")])
    for c in cookies:
        out.append_cookie(c)
    return out


@dataclass(frozen=True)
class RelyingPartyUser:
    sub: str
    #: The Atlas session id. Keep it on your session: touch, revoke and back-channel logout name it.
    sid: str | None
    email: str | None
    #: True only when the ID token says so. Never match accounts on an unverified email.
    email_verified: bool
    name: str | None
    auth_time: int | None
    external_id: str | None = None
    org_id: str | None = None
    org_role: str | None = None


@dataclass(frozen=True)
class RelyingPartyTokens:
    id_token: str
    access_token: str
    #: When the access token expires, epoch milliseconds.
    expires_at: int
    refresh_token: str | None = None


@dataclass
class CallbackResult:
    user: RelyingPartyUser
    tokens: RelyingPartyTokens
    #: Every verified ID-token claim.
    claims: dict[str, Any]
    #: The ``returnTo`` path ``start`` was given, or ``None``.
    return_to: str | None
    #: A 302 to the return path (or ``after_sign_in_path``) that already clears the flow cookie;
    #: append your own session cookie to its headers.
    response: RpResponse
    clear_cookie: str = ""


class SidStore(Protocol):
    """Maps an Atlas ``sid`` to the session ids of YOUR app so a back-channel logout can end them."""

    def bind(self, sid: str, app_session_id: str, expires_at_ms: int) -> None: ...

    def take(self, sid: str) -> list[str]:
        """Return AND remove every unexpired app session bound to ``sid``."""
        ...


class MemorySidStore:
    """An in-process :class:`SidStore`; fine for one server, use a shared store for several."""

    def __init__(self, now: Callable[[], int] | None = None) -> None:
        self._now = now or (lambda: int(time.time() * 1000))
        self._by_sid: dict[str, dict[str, int]] = {}
        self._lock = threading.Lock()

    def _sweep(self) -> None:
        t = self._now()
        for sid in list(self._by_sid):
            apps = {k: v for k, v in self._by_sid[sid].items() if v > t}
            if apps:
                self._by_sid[sid] = apps
            else:
                del self._by_sid[sid]

    def bind(self, sid: str, app_session_id: str, expires_at_ms: int) -> None:
        with self._lock:
            self._sweep()
            self._by_sid.setdefault(sid, {})[app_session_id] = int(expires_at_ms)

    def take(self, sid: str) -> list[str]:
        with self._lock:
            self._sweep()
            return list(self._by_sid.pop(sid, {}))


class SqlSidStore:
    """A :class:`SidStore` on SQL, for several servers. ``execute(sql, params)`` runs one statement and returns
    ``(rows, rowcount)``: use ``dbapi_executor(connection)`` (any DB-API 2.0 driver) or
    ``sqlalchemy_executor(engine)`` from :mod:`atlas_backend._sql`. Create the table once::

        create table atlas_rp_sessions (
          sid text not null,
          app_session_id text not null,
          expires_at bigint not null,          -- epoch milliseconds
          primary key (sid, app_session_id)
        );

    (``varchar(191)`` instead of ``text`` for the key columns on MySQL.) Statements use ``%s`` placeholders
    (``postgres``, ``mysql``) or ``?`` (``sqlite``); ``take`` is one atomic ``delete ... returning`` on
    postgres and sqlite (3.35+), and a select followed by a delete on mysql.
    """

    def __init__(self, execute: Callable[[str, Sequence[Any]], tuple[list[Any], int]], dialect: str = "postgres",
                 now: Callable[[], int] | None = None) -> None:
        if dialect not in ("postgres", "sqlite", "mysql"):
            raise ValueError("dialect must be postgres, sqlite or mysql")
        self._exec, self._dialect = execute, dialect
        self._now = now or (lambda: int(time.time() * 1000))
        self._ph = "?" if dialect == "sqlite" else "%s"

    def bind(self, sid: str, app_session_id: str, expires_at_ms: int) -> None:
        p = self._ph
        self._exec(f"delete from atlas_rp_sessions where sid = {p} and app_session_id = {p}", (sid, app_session_id))
        self._exec(
            f"insert into atlas_rp_sessions (sid, app_session_id, expires_at) values ({p}, {p}, {p})",
            (sid, app_session_id, int(expires_at_ms)),
        )
        self._exec(f"delete from atlas_rp_sessions where expires_at <= {p}", (self._now(),))

    def take(self, sid: str) -> list[str]:
        p = self._ph
        if self._dialect == "mysql":
            rows, _ = self._exec(f"select app_session_id, expires_at from atlas_rp_sessions where sid = {p}", (sid,))
            self._exec(f"delete from atlas_rp_sessions where sid = {p}", (sid,))
        else:
            rows, _ = self._exec(
                f"delete from atlas_rp_sessions where sid = {p} returning app_session_id, expires_at", (sid,)
            )
        now = self._now()
        return [r[0] for r in rows if int(r[1]) > now]


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_dec(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _flow_key(secret: str) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    if len(secret) < 32:
        raise ValueError("The sign-in cookie `secret` must be at least 32 characters.")
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=b"atlas-oidc-flow-cookie", info=b"v1"
    ).derive(secret.encode("utf-8"))


def _seal(payload: dict[str, Any], secret: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    iv = secrets.token_bytes(12)
    sealed = AESGCM(_flow_key(secret)).encrypt(iv, json.dumps(payload).encode("utf-8"), None)
    return f"{_SEALED}{_b64u(iv)}.{_b64u(sealed)}"


def _open(value: str, secret: str) -> dict[str, Any] | None:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    try:
        if not value.startswith(_SEALED):
            return None
        iv, data = value[len(_SEALED) :].split(".")
        parsed = json.loads(AESGCM(_flow_key(secret)).decrypt(_b64u_dec(iv), _b64u_dec(data), None))
    except Exception:
        return None
    if not isinstance(parsed, dict) or not all(
        isinstance(parsed.get(f), str) for f in ("s", "n", "v", "r", "i", "c")
    ):
        return None
    if not isinstance(parsed.get("t"), (int, float)):
        return None
    for opt in ("u", "x"):
        if opt in parsed and not isinstance(parsed[opt], str):
            return None
    if "m" in parsed and (not isinstance(parsed["m"], int) or parsed["m"] < 0):
        return None
    return parsed


def _cookie(name: str, value: str, *, path: str, max_age: int, secure: bool) -> str:
    parts = [f"{name}={value}", f"Path={path}", f"Max-Age={max_age}", "HttpOnly", "SameSite=Lax"]
    if max_age == 0:
        parts.append("Expires=Thu, 01 Jan 1970 00:00:00 GMT")
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def _read_cookie(header: str | None, name: str) -> str | None:
    for part in (header or "").split(";"):
        key, _, value = part.strip().partition("=")
        if key == name and value:
            return value
    return None


def _strip(value: str) -> str:
    return value.rstrip("/")


def _is_loopback(host: str) -> bool:
    return host in ("localhost", "127.0.0.1", "[::1]", "::1")


def _secure_url(value: str) -> bool:
    p = urlsplit(value)
    return p.scheme == "https" or (p.scheme == "http" and _is_loopback(p.hostname or ""))


@dataclass
class TouchResult:
    """``status``: ``skipped`` (touched recently), ``touched`` or ``ended`` (``reason``:
    ``revoked`` / ``idle_expired`` / ``expired`` / ``not_found``: end your own session)."""

    status: str
    last_touched_at: int | None = None
    idle_expires_at: str | None = None
    reason: str | None = None


class RelyingParty:
    """Create once at startup and reuse it for every request. Thread-safe.

    Args:
        issuer: ``https://`` + your Frontend API host (``https://atlasauth.net`` for Sign in with Atlas).
        client_id: The OAuth client id.
        redirect_uri: The callback URL, registered on the client exactly.
        secret: At least 32 characters: seals the sign-in cookie.
        client_secret: A confidential client's secret; without ``secret_key`` it also authenticates
            :meth:`touch_if_due` and :meth:`end_app_session` (the app's own sign-in).
        client_auth: ``client_secret_basic`` (default with a secret), ``client_secret_post`` or ``none``.
        secret_key: The instance secret key (``sk_``, scope ``sessions:write``) for server-side revoke.
        server_sign_out: Sign out with one call, ``POST /v1/oauth_clients/{client_id}/logout``.
        forward_params: Extra sign-in query parameters passed on to ``/oauth2/authorize``.
        routes: ``sign_in`` / ``callback`` / ``sign_out`` / ``backchannel_logout`` paths for :meth:`handle`.
        sid_store / on_backchannel_logout: see :meth:`bind_session` and :meth:`backchannel_logout`.
        on_signed_in: ``(user, tokens, request, result)`` after a verified sign-in; create your session
            there. Return an :class:`RpResponse` to answer with it, or ``None`` to answer with ``result.response``.
        on_sign_in_error: ``(error, request)`` -> :class:`RpResponse`; default a plain 400.
        on_sign_out: ``(request)`` -> ``dict`` with ``id_token``, ``sid``, ``set_cookies``.
    """

    def __init__(
        self,
        *,
        issuer: str,
        client_id: str,
        redirect_uri: str,
        secret: str,
        client_secret: str | None = None,
        client_auth: str | None = None,
        scope: str = "openid profile email",
        after_sign_in_path: str = "/",
        post_logout_redirect_uri: str | None = None,
        secret_key: str | None = None,
        api_url: str = DEFAULT_BASE_URL,
        cookie_name: str = FLOW_COOKIE,
        server_sign_out: bool = False,
        touch_interval_ms: int = 300_000,
        forward_params: Sequence[str] = (),
        routes: Mapping[str, str] | None = None,
        sid_store: SidStore | None = None,
        on_backchannel_logout: Callable[[list[str], LogoutTokenClaims], None] | None = None,
        on_signed_in: Callable[..., RpResponse | None] | None = None,
        on_sign_in_error: Callable[[OidcError, RpRequest], RpResponse] | None = None,
        on_sign_out: Callable[[RpRequest], Mapping[str, Any] | None] | None = None,
        clock_tolerance_seconds: int = 60,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
    ) -> None:
        if not isinstance(secret, str) or len(secret) < 32:
            raise ValueError("RelyingParty: `secret` (at least 32 characters) is required to seal the sign-in cookie.")
        if not is_safe_return_to(after_sign_in_path):
            raise ValueError("RelyingParty: `after_sign_in_path` must be a path starting with a single `/`.")
        for name in forward_params:
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", name) or name in _NOT_FORWARDABLE:
                raise ValueError(f"RelyingParty: `forward_params` cannot forward {name!r}.")
        redirect = urlsplit(redirect_uri)
        if not (redirect.scheme == "https" or (redirect.scheme == "http" and _is_loopback(redirect.hostname or ""))):
            raise ValueError("RelyingParty: `redirect_uri` must be https (http is accepted only for localhost).")
        self.issuer = _strip(issuer)
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self._secret = secret
        self.client_secret = client_secret
        self.client_auth = client_auth or ("client_secret_basic" if client_secret else "none")
        self.scope = scope
        self.after_sign_in_path = after_sign_in_path
        self.post_logout_redirect_uri = post_logout_redirect_uri
        self.secret_key = secret_key
        self.api_url = _strip(api_url)
        self.cookie_name = cookie_name
        self.server_sign_out = server_sign_out
        self.touch_interval_ms = touch_interval_ms
        self.forward_params = tuple(forward_params)
        self.routes = dict(routes or {})
        self.sid_store = sid_store
        self.on_backchannel_logout = on_backchannel_logout
        self.on_signed_in = on_signed_in
        self.on_sign_in_error = on_sign_in_error
        self.on_sign_out = on_sign_out
        self.tolerance = clock_tolerance_seconds
        self._http = http_client or httpx.Client(timeout=10.0)
        self._now = now or (lambda: int(time.time() * 1000))
        self._cb_path = redirect.path or "/"
        self._cb_secure = redirect.scheme == "https"
        self._discovery: tuple[dict[str, Any], int] | None = None
        self._failed: tuple[OidcError, int] | None = None
        self._jwks: JwksCache | None = None
        self._lock = threading.Lock()
        self._verifier: LogoutTokenVerifier | None = None

    # -- discovery ---------------------------------------------------------------------------

    def _discover(self) -> dict[str, Any]:
        now = self._now()
        with self._lock:
            if self._discovery and now - self._discovery[1] < 3_600_000:
                return self._discovery[0]
            if self._failed and now - self._failed[1] < 60_000 and not self._discovery:
                raise self._failed[0]
            url = f"{self.issuer}/.well-known/openid-configuration"

            def fail(why: str) -> OidcError:
                return OidcError("discovery_failed", f"OIDC discovery at {url} failed: {why}.")

            try:
                res = self._http.get(url, headers={"accept": "application/json"})
                if res.status_code != 200:
                    raise fail(f"HTTP {res.status_code}")
                doc = res.json()
                if not isinstance(doc, dict):
                    raise fail("the response is not JSON")
                if not isinstance(doc.get("issuer"), str) or _strip(doc["issuer"]) != self.issuer:
                    raise fail(f"its issuer ({doc.get('issuer')}) is not {self.issuer}")
                for f in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
                    if not isinstance(doc.get(f), str):
                        raise fail(f"it has no {f}")
                    if not _secure_url(doc[f]):
                        raise fail(f"its {f} is not an https URL")
                if "end_session_endpoint" in doc and not isinstance(doc["end_session_endpoint"], str):
                    raise fail("its end_session_endpoint is not a string")
            except OidcError as e:
                if self._discovery:  # keep serving the document we had through an outage
                    return self._discovery[0]
                self._failed = (e, now)
                raise
            except (httpx.HTTPError, ValueError) as e:
                err = fail(str(e))
                if self._discovery:
                    return self._discovery[0]
                self._failed = (err, now)
                raise err from e
            self._discovery = (doc, now)
            return doc

    # -- start --------------------------------------------------------------------------------

    def start(self, request: RpRequest | None = None, **overrides: Any) -> RpResponse:
        """Begin sign-in: a 302 to ``/oauth2/authorize`` with the flow cookie set.

        ``prompt``, ``login_hint``, ``ui_locales``, ``max_age``, ``organization`` and ``return_to``
        on the request's query are passed through, as are the ``forward_params`` you configured;
        keyword ``overrides`` (the same names, plus ``scope``, ``expected_sub`` and ``extra_params``) win.
        """
        query = _query(request.url) if request else {}
        opts: dict[str, Any] = {}
        for param, key in _PASSTHROUGH:
            v = query.get(param)
            # A bad return_to from the query is dropped, never an error page.
            if v and (key != "return_to" or is_safe_return_to(v)):
                opts[key] = v
        max_age = query.get("max_age")
        if max_age is not None and re.fullmatch(r"\d{1,9}", max_age):
            opts["max_age"] = int(max_age)
        extra = {n: query[n] for n in self.forward_params if query.get(n) and len(query[n]) <= 512}
        extra.update(overrides.pop("extra_params", None) or {})
        opts.update({k: v for k, v in overrides.items() if v is not None})
        url, cookie = self._start(extra_params=extra, **opts)
        return _redirect(url, [cookie])

    def _start(
        self,
        *,
        scope: str | None = None,
        prompt: str | None = None,
        login_hint: str | None = None,
        organization: str | None = None,
        ui_locales: str | None = None,
        max_age: int | None = None,
        return_to: str | None = None,
        expected_sub: str | None = None,
        extra_params: Mapping[str, str] | None = None,
    ) -> tuple[str, str]:
        disc = self._discover()
        if return_to is not None and not is_safe_return_to(return_to):
            raise ValueError("`return_to` must be a path on this site, starting with a single `/`.")
        if max_age is not None and (not isinstance(max_age, int) or max_age < 0):
            raise ValueError("`max_age` must be a whole number of seconds, 0 or more.")
        state, nonce = _b64u(secrets.token_bytes(32)), _b64u(secrets.token_bytes(32))
        verifier = _b64u(secrets.token_bytes(32))
        challenge = _b64u(hashlib.sha256(verifier.encode("ascii")).digest())
        parts = (scope or self.scope).split()
        if "openid" not in parts:
            parts.insert(0, "openid")
        params: dict[str, str] = {k: v for k, v in (extra_params or {}).items() if v and k not in _OWNED}
        params.update(
            response_type="code",
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=" ".join(dict.fromkeys(parts)),
            state=state,
            nonce=nonce,
            code_challenge=challenge,
            code_challenge_method="S256",
        )
        for key, value in (
            ("prompt", prompt),
            ("login_hint", login_hint),
            ("organization", organization),
            ("ui_locales", ui_locales),
        ):
            if value:
                params[key] = value
        if max_age is not None:
            params["max_age"] = str(max_age)
        payload: dict[str, Any] = {
            "s": state,
            "n": nonce,
            "v": verifier,
            "r": self.redirect_uri,
            "i": self.issuer,
            "c": self.client_id,
            "t": self._now() // 1000,
        }
        if max_age is not None:
            payload["m"] = max_age
        if return_to is not None:
            payload["u"] = return_to
        if expected_sub:
            payload["x"] = expected_sub
        cookie = _cookie(
            self.cookie_name,
            _seal(payload, self._secret),
            path=self._cb_path,
            max_age=FLOW_MAX_AGE_SECONDS,
            secure=self._cb_secure,
        )
        sep = "&" if "?" in disc["authorization_endpoint"] else "?"
        return disc["authorization_endpoint"] + sep + urlencode(params, quote_via=quote), cookie

    def _clear_cookie(self) -> str:
        return _cookie(self.cookie_name, "", path=self._cb_path, max_age=0, secure=self._cb_secure)

    # -- callback -----------------------------------------------------------------------------

    def callback(self, request: RpRequest) -> CallbackResult:
        """Finish a sign-in: check ``state``, exchange the code (PKCE + client auth), verify the ID
        token. Raises :class:`OidcError` (its ``clear_cookie`` removes the flow cookie)."""
        clear = self._clear_cookie()
        try:
            result = self._callback(request)
        except OidcError as e:
            e.clear_cookie = clear
            raise
        except Exception as e:  # anything unexpected is a failed sign-in, never a 500 with a half state
            err = OidcError("invalid_request", str(e))
            err.clear_cookie = clear
            raise err from e
        result.clear_cookie = clear
        result.response.append_cookie(clear)
        return result

    def _callback(self, request: RpRequest) -> CallbackResult:
        query = _query(request.url)
        raw = _read_cookie(request.header("cookie"), self.cookie_name)
        if not raw:
            raise OidcError("state_mismatch", "The sign-in flow cookie is missing or expired. Start sign-in again.")
        flow = _open(raw, self._secret)
        if not flow:
            raise OidcError("state_mismatch", "The sign-in flow cookie could not be read. Start sign-in again.")
        state = query.get("state")
        if not state or not hmac.compare_digest(state.encode(), flow["s"].encode()):
            raise OidcError("state_mismatch", "The `state` returned to the callback does not match this browser's sign-in.")
        now_s = self._now() // 1000
        if now_s - flow["t"] > FLOW_MAX_AGE_SECONDS:
            raise OidcError("state_mismatch", "This sign-in took longer than 10 minutes. Start sign-in again.")
        if flow["i"] != self.issuer or flow["c"] != self.client_id or flow["r"] != self.redirect_uri:
            raise OidcError("state_mismatch", "This sign-in was started for a different issuer, client or redirect URI.")
        returned_iss = query.get("iss")  # RFC 9207
        if returned_iss is not None and _strip(returned_iss) != self.issuer:
            raise OidcError("issuer_mismatch", f"The callback came from {returned_iss}, not {self.issuer}.")
        if query.get("error"):
            desc = query.get("error_description")
            raise OidcError(
                "access_denied",
                f"Sign-in did not complete: {query['error']}{f' ({desc})' if desc else ''}.",
                oauth_error=query["error"],
                description=desc,
            )
        code = query.get("code")
        if not code:
            raise OidcError("invalid_request", "The callback has no `code` parameter.")

        disc = self._discover()
        tokens = self._exchange(disc, code, flow["v"])
        claims = self._verify_id_token(tokens["id_token"], disc, flow["n"], tokens["access_token"])
        sub = claims["sub"]
        auth_time = claims.get("auth_time")
        auth_time = int(auth_time) if isinstance(auth_time, (int, float)) and not isinstance(auth_time, bool) else None
        if "m" in flow and (auth_time is None or now_s - auth_time > flow["m"] + self.tolerance):
            raise OidcError(
                "reauthentication_required",
                f"The sign-in is older than the {flow['m']} seconds this request allowed (max_age). Ask the user to sign in again.",
            )
        if "x" in flow and not hmac.compare_digest(sub.encode(), flow["x"].encode()):
            raise OidcError("subject_mismatch", "A different user signed in than the one asked to confirm it is them.")
        try:
            expires_in = float(tokens.get("expires_in"))
        except (TypeError, ValueError):
            expires_in = 0.0
        expires_at = self._now() + int(expires_in * 1000) if expires_in > 0 else int(claims["exp"]) * 1000
        user = RelyingPartyUser(
            sub=sub,
            sid=claims["sid"] if isinstance(claims.get("sid"), str) and claims["sid"] else None,
            email=claims["email"] if isinstance(claims.get("email"), str) else None,
            email_verified=claims.get("email_verified") is True,
            name=claims["name"] if isinstance(claims.get("name"), str) else None,
            auth_time=auth_time,
            external_id=claims["external_id"] if isinstance(claims.get("external_id"), str) and claims["external_id"] else None,
            org_id=claims["org_id"] if isinstance(claims.get("org_id"), str) else None,
            org_role=claims["org_role"] if isinstance(claims.get("org_role"), str) and "org_id" in claims else None,
        )
        out_tokens = RelyingPartyTokens(
            id_token=tokens["id_token"],
            access_token=tokens["access_token"],
            expires_at=expires_at,
            refresh_token=tokens["refresh_token"] if isinstance(tokens.get("refresh_token"), str) else None,
        )
        return_to = flow.get("u") if isinstance(flow.get("u"), str) and is_safe_return_to(flow["u"]) else None
        return CallbackResult(
            user=user,
            tokens=out_tokens,
            claims=claims,
            return_to=return_to,
            response=_redirect(return_to or self.after_sign_in_path),
        )

    def _client_headers(self, body: dict[str, str]) -> dict[str, str]:
        headers = {"content-type": "application/x-www-form-urlencoded", "accept": "application/json"}
        method = self.client_auth
        if method != "none" and not self.client_secret:
            raise OidcError("token_exchange_failed", f"client_auth '{method}' needs `client_secret`.")
        if method == "client_secret_basic":
            pair = f"{quote(self.client_id, safe='')}:{quote(self.client_secret or '', safe='')}"
            headers["authorization"] = "Basic " + base64.b64encode(pair.encode()).decode()
        else:
            body["client_id"] = self.client_id
            if method == "client_secret_post":
                body["client_secret"] = self.client_secret or ""
        return headers

    def _exchange(self, disc: dict[str, Any], code: str, verifier: str) -> dict[str, Any]:
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": verifier,
        }
        headers = self._client_headers(body)
        try:
            res = self._http.post(disc["token_endpoint"], headers=headers, data=body)
        except httpx.HTTPError as e:
            raise OidcError("token_exchange_failed", f"The token endpoint could not be reached: {e}.") from e
        try:
            out = res.json()
        except ValueError:
            out = None
        out = out if isinstance(out, dict) else None
        if res.status_code >= 400:
            err = out.get("error") if out else None
            desc = out.get("error_description") if out else None
            raise OidcError(
                "token_exchange_failed",
                f"The token endpoint answered {res.status_code}{f' {err}' if err else ''}{f': {desc}' if desc else ''}.",
                oauth_error=err if isinstance(err, str) else None,
                description=desc if isinstance(desc, str) else None,
                status=res.status_code,
            )
        if not out or not isinstance(out.get("id_token"), str) or not isinstance(out.get("access_token"), str):
            raise OidcError("token_exchange_failed", "The token response has no `id_token`. Request the `openid` scope.", status=res.status_code)
        return out

    def _verify_id_token(self, id_token: str, disc: dict[str, Any], nonce: str, access_token: str) -> dict[str, Any]:
        import jwt  # PyJWT

        def invalid(why: str) -> OidcError:
            return OidcError("invalid_token", f"The ID token was refused: {why}.")

        try:
            header = jwt.get_unverified_header(id_token)
        except jwt.PyJWTError:
            raise invalid("it is not a JWT") from None
        # Pinned before any key lookup, so `none` and HS* never get near a key.
        if header.get("alg") not in SIGNING_ALGS:
            raise invalid(f"its algorithm is {header.get('alg')}, not RS256 or ES256")
        if self._jwks is None:
            self._jwks = JwksCache(disc["jwks_uri"], http_client=self._http, now=self._now)
        kid = header.get("kid") if isinstance(header.get("kid"), str) else None
        keyset = self._jwks.get(kid)
        if not keyset or not keyset.get("keys"):
            raise OidcError("discovery_failed", f"The issuer's signing keys could not be fetched from {disc['jwks_uri']}.")
        candidates = [k for k in keyset["keys"] if not kid or k.get("kid") == kid]
        key_alg = None
        for jwk in candidates:
            try:
                key, alg = jwk_public_key(jwk, header["alg"])
            except Exception:
                continue
            if alg == header["alg"]:
                key_alg = (key, alg)
                break
        if key_alg is None:
            raise invalid("no published key matches it")
        try:
            claims = jwt.decode(
                id_token,
                key=key_alg[0],
                algorithms=[key_alg[1]],
                audience=self.client_id,
                issuer=disc["issuer"],
                leeway=self.tolerance,
                options={"require": ["sub", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError:
            raise invalid("it has expired") from None
        except jwt.InvalidAudienceError:
            raise invalid("its audience is not this client") from None
        except jwt.InvalidIssuerError:
            raise invalid("its issuer is not the configured issuer") from None
        except jwt.InvalidTokenError as e:
            raise invalid(str(e)) from None
        aud = claims.get("aud")
        if isinstance(aud, list) and len(aud) > 1 and "azp" not in claims:
            raise invalid("it has several audiences and no azp")
        if "azp" in claims and claims["azp"] != self.client_id:
            raise invalid(f"its azp is {claims['azp']}, not this client")
        if not isinstance(claims.get("nonce"), str) or not hmac.compare_digest(claims["nonce"].encode(), nonce.encode()):
            raise invalid("its nonce does not match this sign-in")
        if isinstance(claims.get("at_hash"), str):
            want = _b64u(hashlib.sha256(access_token.encode()).digest()[:16])
            if not hmac.compare_digest(want.encode(), claims["at_hash"].encode()):
                raise invalid("its at_hash does not match the access token")
        return dict(claims)

    # -- step-up -----------------------------------------------------------------------------

    def require_recent_auth(
        self,
        request: RpRequest,
        max_age_seconds: int,
        *,
        sub: str,
        auth_time: int | None,
        return_to: str | None = None,
    ) -> RpResponse | None:
        """``None`` when the user authenticated within ``max_age_seconds``; otherwise a 302 that
        re-authenticates them (as ``sub``) and comes back. ``0`` means "confirm now"."""
        if not isinstance(max_age_seconds, int) or max_age_seconds < 0:
            raise ValueError("`max_age_seconds` must be a whole number of seconds, 0 or more.")
        if not sub:
            raise ValueError("`sub` is required.")
        # 0 still passes for a minute after the confirmation, or the request that comes back
        # from it would be sent to confirm again, forever.
        allowed = CONFIRM_NOW_WINDOW_SECONDS if max_age_seconds == 0 else max_age_seconds
        if isinstance(auth_time, (int, float)) and self._now() / 1000 - auth_time <= allowed:
            return None
        if return_to is None:
            here = urlsplit(request.url)
            return_to = here.path + (f"?{here.query}" if here.query else "")
        url, cookie = self._start(
            max_age=max_age_seconds,
            expected_sub=sub,
            prompt="login" if max_age_seconds == 0 else None,
            return_to=return_to if is_safe_return_to(return_to) else None,
        )
        return _redirect(url, [cookie])

    # -- sessions ----------------------------------------------------------------------------

    def _session_call(self, sid: str, action: str) -> httpx.Response:
        if not self.secret_key:
            raise ValueError(f"{'touch_if_due' if action == 'touch' else 'revoke_session'}: `secret_key` is not configured.")
        if not sid:
            raise ValueError("A session id (`sid`) is required.")
        return self._http.post(
            f"{self.api_url}/v1/sessions/{quote(sid, safe='')}/{action}",
            headers={"authorization": f"Bearer {self.secret_key}", "accept": "application/json"},
        )

    def _app_session_call(self, sid: str, action: str, caller: str) -> httpx.Response:
        if self.client_auth == "none" or not self.client_secret:
            raise ValueError(f"{caller}: configure `client_secret` (the app's client credentials); a public client cannot call it.")
        if not sid:
            raise ValueError("A session id (`sid`) is required.")
        body = {"sid": sid}
        headers = self._client_headers(body)
        return self._http.post(f"{self.issuer}/oauth2/session/{action}", headers=headers, data=body)

    @staticmethod
    def _json(res: httpx.Response) -> dict[str, Any] | None:
        try:
            out = res.json()
        except ValueError:
            return None
        return out if isinstance(out, dict) else None

    def _api_error(self, res: httpx.Response, body: dict[str, Any] | None) -> Exception:
        """The OAuth error body of ``/oauth2/session/*`` or the Backend API ``errors`` envelope."""
        from ._errors import AtlasError

        errs = (body or {}).get("errors")
        if isinstance(errs, list) and errs and all(isinstance(e, dict) for e in errs):
            return AtlasError(res.status_code, errs)
        code = (body or {}).get("error")
        message = (body or {}).get("error_description")
        return AtlasError(
            res.status_code,
            [
                {
                    "code": code if isinstance(code, str) else "request_failed",
                    "message": message if isinstance(message, str) else f"The issuer answered {res.status_code}.",
                }
            ],
        )

    def touch_if_due(self, sid: str, last_touched_at: int | None = None) -> TouchResult:
        """Slide the idle window of the Atlas session (or your app's own sign-in without a
        ``secret_key``), at most once per ``touch_interval_ms``. ``ended`` means end your own session."""
        now = self._now()
        if isinstance(last_touched_at, int) and 0 <= now - last_touched_at < self.touch_interval_ms:
            return TouchResult("skipped", last_touched_at=last_touched_at)
        if not self.secret_key:
            res = self._app_session_call(sid, "touch", "touch_if_due")
            body = self._json(res)
            if res.is_success:
                idle = (body or {}).get("idle_expires_at")
                return TouchResult("touched", last_touched_at=now, idle_expires_at=idle if isinstance(idle, str) else None)
            if res.status_code == 404 and (body or {}).get("error") == "session_not_found":
                return TouchResult("ended", reason="not_found")
            raise self._api_error(res, body)
        res = self._session_call(sid, "touch")
        body = self._json(res)
        if res.is_success:
            idle = (body or {}).get("idle_expires_at")
            return TouchResult("touched", last_touched_at=now, idle_expires_at=idle if isinstance(idle, str) else None)
        if res.status_code == 404:
            return TouchResult("ended", reason="not_found")
        if res.status_code == 409:
            errs = (body or {}).get("errors")
            code = errs[0].get("code") if isinstance(errs, list) and errs and isinstance(errs[0], dict) else None
            return TouchResult("ended", reason={"SESSION_REVOKED": "revoked", "SESSION_IDLE_EXPIRED": "idle_expired"}.get(code, "expired"))
        # A key, scope or availability problem is not "signed out": say so loudly.
        raise self._api_error(res, body)

    def revoke_session(self, sid: str) -> str:
        """Revoke the Atlas session server-side (needs ``secret_key``): ``revoked`` or ``not_found``."""
        res = self._session_call(sid, "revoke")
        if res.is_success:
            return "revoked"
        if res.status_code == 404:
            return "not_found"
        raise self._api_error(res, self._json(res))

    def end_app_session(self, sid: str) -> str:
        """End your app's own sign-in under ``sid`` (``POST /oauth2/session/end``): ``ended`` or ``not_found``."""
        res = self._app_session_call(sid, "end", "end_app_session")
        body = self._json(res)
        if res.is_success:
            return "ended"
        if res.status_code == 404 and (body or {}).get("error") == "session_not_found":
            return "not_found"
        raise self._api_error(res, body)

    def bind_session(self, sid: str, app_session_id: str, expires_at: int) -> None:
        """Record that ``app_session_id`` is backed by Atlas session ``sid`` (``expires_at`` epoch ms)."""
        if self.sid_store is None:
            raise ValueError("bind_session: `sid_store` is not configured.")
        if not sid or not app_session_id:
            raise ValueError("bind_session: `sid` and `app_session_id` are required.")
        self.sid_store.bind(sid, app_session_id, expires_at)

    def backchannel_logout(self, request: RpRequest) -> RpResponse:
        """Verify an Atlas ``logout_token`` and end the app sessions its ``sid`` backs. Answers 200,
        400 for a bad token (not retried) or 503 when keys could not be loaded or your callback
        raised (Atlas retries; the bindings are kept)."""
        if self.on_backchannel_logout is None:
            raise ValueError("backchannel_logout: `on_backchannel_logout` is not configured.")
        headers = [("cache-control", "no-store")]
        try:
            token = logout_token_from_form(request.form or {})
        except Exception:
            return RpResponse(400, headers)
        if self._verifier is None:
            self._verifier = LogoutTokenVerifier(
                issuer=self.issuer, client_id=self.client_id, http_client=self._http, now=self._now
            )
        try:
            claims = self._verifier.verify(token)
        except VerificationError as e:
            return RpResponse(503, headers + [("retry-after", "30")]) if e.retryable else RpResponse(400, headers)
        ids = self.sid_store.take(claims.sid) if claims.sid and self.sid_store else []
        try:
            self.on_backchannel_logout(ids, claims)
        except Exception:
            # Put the bindings back so Atlas's retry finds them.
            for i in ids:
                self.sid_store.bind(claims.sid, i, self._now() + 86_400_000)  # type: ignore[union-attr,arg-type]
            return RpResponse(503, headers + [("retry-after", "30")])
        return RpResponse(200, headers)

    # -- sign out ----------------------------------------------------------------------------

    def sign_out(
        self,
        *,
        id_token: str | None = None,
        sid: str | None = None,
        post_logout_redirect_uri: str | None = None,
        state: str | None = None,
        set_cookies: Sequence[str] = (),
    ) -> RpResponse:
        """End the Atlas session: revoke it server-side when a ``secret_key`` is set, then redirect
        to the issuer's ``end_session_endpoint`` (or, with ``server_sign_out``, straight back)."""
        target_uri = post_logout_redirect_uri or self.post_logout_redirect_uri
        if self.server_sign_out and sid and self.secret_key:
            res = self._http.post(
                f"{self.api_url}/v1/oauth_clients/{quote(self.client_id, safe='')}/logout",
                headers={"authorization": f"Bearer {self.secret_key}", "accept": "application/json"},
                json={"sid": sid},
            )
            # 404: this instance has no such session any more, so there is nothing left to end.
            if not res.is_success and res.status_code != 404:
                raise self._api_error(res, self._json(res))
            to = target_uri or "/"
            if state:
                to += ("&" if "?" in to else "?") + urlencode({"state": state})
            return _redirect(to, list(set_cookies))
        if sid and self.secret_key:
            self.revoke_session(sid)
        disc = self._discover()
        if not disc.get("end_session_endpoint"):
            raise OidcError("discovery_failed", "The issuer does not advertise an end_session_endpoint.")
        params = {"client_id": self.client_id}
        if id_token:
            params["id_token_hint"] = id_token
        if target_uri:
            params["post_logout_redirect_uri"] = target_uri
        if state:
            params["state"] = state
        sep = "&" if "?" in disc["end_session_endpoint"] else "?"
        return _redirect(disc["end_session_endpoint"] + sep + urlencode(params, quote_via=quote), list(set_cookies))

    # -- one entry point ---------------------------------------------------------------------

    def handle(self, request: RpRequest) -> RpResponse | None:
        """Answer the sign-in, callback, sign-out and back-channel routes; ``None`` for any other path."""
        if self.on_signed_in is None:
            raise ValueError("handle: `on_signed_in` is not configured; it is where your app creates its session.")
        path = urlsplit(request.url).path
        method = request.method.upper()
        routes = self.routes
        if method == "POST" and routes.get("backchannel_logout") and path == routes["backchannel_logout"]:
            return self.backchannel_logout(request)
        if method == "GET" and path == routes.get("sign_in", "/auth/sign-in"):
            return self.start(request)
        if method == "GET" and path == routes.get("callback", self._cb_path):
            try:
                result = self.callback(request)
            except OidcError as e:
                failed = (
                    self.on_sign_in_error(e, request)
                    if self.on_sign_in_error
                    else RpResponse(
                        400,
                        [("content-type", "text/plain; charset=utf-8"), ("cache-control", "no-store")],
                        b"Sign-in failed. Please try again.",
                    )
                )
                return failed.append_cookie(e.clear_cookie)
            own = self.on_signed_in(result.user, result.tokens, request, result)
            return own.append_cookie(result.clear_cookie) if isinstance(own, RpResponse) else result.response
        if method in ("POST", "GET") and path == routes.get("sign_out", "/auth/sign-out"):
            opts = (self.on_sign_out(request) if self.on_sign_out else None) or {}
            return self.sign_out(
                id_token=opts.get("id_token"),
                sid=opts.get("sid"),
                post_logout_redirect_uri=opts.get("post_logout_redirect_uri"),
                state=opts.get("state"),
                set_cookies=opts.get("set_cookies", ()),
            )
        return None

    def close(self) -> None:
        self._http.close()


def _query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query, keep_blank_values=True).items()}


def authenticated_within(claims: Mapping[str, Any], max_age_seconds: float, now_ms: int | None = None) -> bool:
    """Whether ``auth_time`` is within ``max_age_seconds`` of now. A token without ``auth_time`` never is."""
    at = claims.get("auth_time")
    if isinstance(at, bool) or not isinstance(at, (int, float)):
        return False
    now = time.time() * 1000 if now_ms is None else now_ms
    return now / 1000 - at <= max_age_seconds


def used_multi_factor(claims: Mapping[str, Any]) -> bool:
    """Whether the session proved a second factor (``acr`` is mfa, or ``amr`` includes ``mfa``)."""
    if claims.get("acr") == "urn:atlas:acr:mfa":
        return True
    amr = claims.get("amr")
    return isinstance(amr, list) and "mfa" in amr


def mfa_satisfied(claims: Mapping[str, Any]) -> bool:
    """Whether the session satisfies a "requires MFA" rule: the server's ``mfa_satisfied`` verdict when
    the token carries it, else ``mfa`` true, :func:`used_multi_factor`, or an enterprise SSO sign-in."""
    if isinstance(claims.get("mfa_satisfied"), bool):
        return bool(claims["mfa_satisfied"])
    return claims.get("mfa") is True or used_multi_factor(claims) or isinstance(claims.get("sso_connection_id"), str)


def mfa_org_satisfied(claims: Mapping[str, Any], org_id_or_external_id: str | None = None) -> bool:
    """Whether the session meets the active organization's MFA policy (see ``org_mfa_required`` /
    ``org_mfa_ok``). Pass the organization you are authorizing for: a token whose active
    organization is another one answers ``False``."""
    required = claims.get("org_mfa_required") is True
    if org_id_or_external_id is None:
        return not required or claims.get("org_mfa_ok") is True
    matches = org_id_or_external_id in (claims.get("org_id"), claims.get("org_external_id"))
    if required:
        return claims.get("org_mfa_ok") is True and (matches or "org_id" not in claims)
    return matches
