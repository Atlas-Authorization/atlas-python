"""Browser sign-in for a command-line tool of your own: the device authorization flow (RFC 8628) or a
loopback redirect (RFC 8252) against your instance, with a stored, refreshing session.

    from atlas_backend import CliLogin

    cli = CliLogin(issuer="https://id.example.com", client_id="client_...", app_name="mytool")
    cli.login()                       # opens the browser; falls back to a code to confirm over SSH
    token = cli.get_access_token()    # refreshed first when it expires within 60 seconds

``start_device_authorization`` / ``poll_device_authorization`` are the bare device-flow primitives.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import threading
import time
import webbrowser
from collections.abc import Callable, Mapping
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx


class OAuthFlowError(Exception):
    """A device-flow or token-endpoint failure. ``code`` is the OAuth ``error`` (``access_denied``, ``expired_token`` ...)."""

    def __init__(self, code: str, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class CliLoginRequiredError(Exception):
    def __init__(self, app_name: str) -> None:
        super().__init__(f"Not signed in. Run `{app_name} login`.")


class CliSessionStore(Protocol):
    """Where the session lives (``access_token``, ``refresh_token``, ``expires_at`` epoch ms, ``scope``,
    ``issuer``, ``client_id``); implement it to use an OS keychain."""

    def load(self) -> dict[str, Any] | None: ...
    def save(self, session: dict[str, Any]) -> None: ...
    def clear(self) -> None: ...


class FileCliSessionStore:
    """``$XDG_CONFIG_HOME/<app_name>/atlas-session.json`` (``%APPDATA%`` on Windows), written 0600 in a 0700 directory."""

    def __init__(self, app_name: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", app_name) or ".." in app_name:
            raise ValueError(f'Invalid app_name "{app_name}": use letters, digits, ".", "_" or "-".')
        env = os.environ
        if sys.platform == "win32":
            base = Path(env.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        else:
            base = Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        self.path = base / app_name / "atlas-session.json"

    def load(self) -> dict[str, Any] | None:
        try:
            value = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError):
            return None
        return value if isinstance(value, dict) else None

    def save(self, session: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix="atlas-session.")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(session))
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _form(client: httpx.Client, url: str, body: Mapping[str, str]) -> tuple[int, dict[str, Any]]:
    res = client.post(url, data=dict(body), headers={"accept": "application/json"})
    try:
        out = res.json()
    except ValueError:
        out = {}
    return res.status_code, out if isinstance(out, dict) else {}


def start_device_authorization(
    *,
    issuer: str,
    client_id: str,
    client_secret: str | None = None,
    scope: str | None = None,
    resource: str | None = None,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Start the device flow. Show the person ``verification_uri_complete`` (or ``verification_uri`` +
    ``user_code``), then :func:`poll_device_authorization`. Returns the answer plus ``config``."""
    base = issuer.rstrip("/")
    config = {
        "token_endpoint": f"{base}/oauth2/token",
        "client_id": client_id,
        **({"client_secret": client_secret} if client_secret else {}),
    }
    body = {"client_id": client_id, **({"client_secret": client_secret} if client_secret else {}), **({"scope": scope} if scope else {}), **({"resource": resource} if resource else {})}
    client = http_client or httpx.Client(timeout=30.0)
    try:
        status, out = _form(client, f"{base}/oauth2/device_authorization", body)
    finally:
        if http_client is None:
            client.close()
    if status != 200:
        raise OAuthFlowError(str(out.get("error", "error")), str(out.get("error_description", "Device authorization failed.")), status)
    return {**out, "config": config}


def poll_device_authorization(
    start: Mapping[str, Any],
    *,
    http_client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.time,
) -> dict[str, Any]:
    """Poll the token endpoint until the person approves (returns the tokens), denies (``access_denied``) or the
    code expires (``expired_token``); both raise :class:`OAuthFlowError`. Honours ``interval``, adds 5 s on ``slow_down``."""
    cfg = start["config"]
    interval = max(1, int(start.get("interval", 5)))
    deadline = now() + int(start["expires_in"])
    client = http_client or httpx.Client(timeout=30.0)
    try:
        while now() < deadline:
            sleep(interval)
            body = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": start["device_code"],
                "client_id": cfg["client_id"],
                **({"client_secret": cfg["client_secret"]} if cfg.get("client_secret") else {}),
            }
            status, out = _form(client, cfg["token_endpoint"], body)
            if status == 200:
                return out
            if out.get("error") == "authorization_pending":
                continue
            if out.get("error") == "slow_down":
                interval += 5
                continue
            raise OAuthFlowError(str(out.get("error", "error")), str(out.get("error_description", "Sign-in failed.")), status)
    finally:
        if http_client is None:
            client.close()
    raise OAuthFlowError("expired_token", "The sign-in code expired. Run the login again.", 400)


_RESERVED = frozenset("response_type client_id redirect_uri scope state code_challenge code_challenge_method resource".split())


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _wait_for_loopback_code(path: str, state: str, timeout: float, on_listening: Callable[[str], None]) -> tuple[str, str]:
    """A one-shot HTTP server on 127.0.0.1 and a random port waits for ONE valid redirect carrying the right
    ``state``; anything else gets a 4xx and the wait continues until the timeout. Returns ``(code, redirect_uri)``."""
    result: dict[str, Any] = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:
            pass

        def _reply(self, status: int, title: str, body: str) -> None:
            page = f"<!doctype html><meta charset=utf-8><title>{title}</title><h1>{title}</h1><p>{body}</p>".encode()
            self.send_response(status)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def do_GET(self) -> None:  # noqa: N802
            u = urlsplit(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            if u.path != path:
                return self._reply(404, "Not found", "This is not the sign-in callback.")
            import hmac

            if not hmac.compare_digest(q.get("state", "").encode(), state.encode()):
                return self._reply(400, "Sign-in failed", "The state did not match. Run the login again.")
            if done.is_set():
                return self._reply(400, "Sign-in failed", "This sign-in already finished.")
            if q.get("error"):
                desc = q.get("error_description")
                result["error"] = "Sign-in was refused: " + q["error"] + (f" ({desc})" if desc else "") + "."
            elif q.get("code"):
                result["code"] = q["code"]
            else:
                result["error"] = "The sign-in redirect carried no code."
            done.set()
            if "error" in result:
                return self._reply(400, "Sign-in failed", "You can close this tab and try again.")
            self._reply(200, "Signed in", "You can close this tab and return to your terminal.")

    server = HTTPServer(("127.0.0.1", 0), Handler)
    redirect_uri = f"http://127.0.0.1:{server.server_address[1]}{path}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        on_listening(redirect_uri)
        if not done.wait(timeout):
            raise TimeoutError("Timed out waiting for the browser sign-in.")
    finally:
        time.sleep(0.25)  # let the page reach the browser, then stop listening: one sign-in per server
        server.shutdown()
        server.server_close()
    if "error" in result:
        raise OAuthFlowError("access_denied", result["error"])
    return result["code"], redirect_uri


class CliLogin:
    """Sign a command-line tool in through the browser and keep the session fresh.

    Args:
        issuer / client_id: your instance and an OAuth client (with the ``device_code`` grant for the device flow, and
            ``http://127.0.0.1/callback`` registered for loopback).
        app_name: names the session directory (one plain segment) and the ``<app> login`` hint.
        mode: ``auto`` (loopback when a browser can open on this machine, else device), ``loopback`` or ``device``.
        resource: the API the token is for (RFC 8707); Atlas binds a sign-in to ONE API.
        open_browser: ``False`` never opens one (it is never opened in CI or over SSH anyway).
    """

    def __init__(
        self,
        *,
        issuer: str,
        client_id: str,
        app_name: str,
        scope: str | list[str] = "openid profile email offline_access",
        store: CliSessionStore | None = None,
        open_browser: bool = True,
        resource: str | list[str] | None = None,
        mode: str = "auto",
        extra_authorize_params: Mapping[str, str] | None = None,
        loopback_timeout_seconds: float = 300.0,
        loopback_path: str = "/callback",
        open: Callable[[str], Any] | None = None,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
        print_fn: Callable[[str], None] = print,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        resources = {r for r in ([resource] if isinstance(resource, str) else resource or []) if r}
        if len(resources) > 1:
            raise ValueError("CliLogin: Atlas binds a sign-in to one resource; pass a single `resource`.")
        self.resource = next(iter(resources), None)
        self.issuer = issuer.rstrip("/")
        self.client_id, self.app_name, self.mode = client_id, app_name, mode
        self.scope = scope if isinstance(scope, str) else " ".join(scope)
        self.store: CliSessionStore = store or FileCliSessionStore(app_name)
        self._open_browser, self._extra = open_browser, dict(extra_authorize_params or {})
        self._timeout, self._path = loopback_timeout_seconds, loopback_path
        self._opener = open
        self._http = http_client or httpx.Client(timeout=30.0)
        self._now = now or (lambda: int(time.time() * 1000))
        self._print, self._sleep = print_fn, sleep
        self._refresh_lock = threading.Lock()

    # -- helpers --------------------------------------------------------------------------------

    def _load(self) -> dict[str, Any] | None:
        s = self.store.load()
        return s if s and s.get("issuer") == self.issuer and s.get("client_id") == self.client_id else None

    def _session(self, t: Mapping[str, Any], prev: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "access_token": t["access_token"],
            "refresh_token": t.get("refresh_token") or (prev or {}).get("refresh_token"),
            "expires_at": self._now() + int(t["expires_in"]) * 1000,
            "scope": t.get("scope") or (prev or {}).get("scope") or self.scope,
            "issuer": self.issuer,
            "client_id": self.client_id,
        }

    def _post(self, path: str, body: Mapping[str, str]) -> httpx.Response:
        return self._http.post(f"{self.issuer}/oauth2/{path}", data=dict(body))

    def _can_open_browser(self) -> bool:
        if not self._open_browser:
            return False
        return self._opener is not None or (sys.stdout.isatty() and not os.environ.get("CI") and not os.environ.get("SSH_CONNECTION"))

    def _open(self, url: str) -> None:
        # Only web URLs: never hand anything else to the OS.
        if not re.fullmatch(r'https?://[^\s"]+', url, re.I):
            return
        try:
            (self._opener or webbrowser.open)(url)
        except Exception:
            pass  # ignored on purpose: the URL is printed anyway

    # -- flows ----------------------------------------------------------------------------------

    def _login_device(self) -> dict[str, Any]:
        start = start_device_authorization(
            issuer=self.issuer, client_id=self.client_id, scope=self.scope, resource=self.resource, http_client=self._http
        )
        self._print(f"Open {start['verification_uri_complete']}")
        self._print(f"and confirm the code {start['user_code']}.")
        if self._can_open_browser():
            self._open(start["verification_uri_complete"])
        tokens = poll_device_authorization(start, http_client=self._http, sleep=self._sleep)
        session = self._session(tokens)
        self.store.save(session)
        return session

    def _login_loopback(self) -> dict[str, Any]:
        verifier, state = _b64u(secrets.token_bytes(32)), _b64u(secrets.token_bytes(16))
        challenge = _b64u(hashlib.sha256(verifier.encode()).digest())

        def listening(redirect_uri: str) -> None:
            params = {k: v for k, v in self._extra.items() if k not in _RESERVED}
            params.update(
                response_type="code",
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                scope=self.scope,
                state=state,
                code_challenge=challenge,
                code_challenge_method="S256",
            )
            if self.resource:
                params["resource"] = self.resource
            url = f"{self.issuer}/oauth2/authorize?{urlencode(params)}"
            self._print(f"Open {url}")
            self._print("and sign in; this window continues when you are done.")
            if self._can_open_browser():
                self._open(url)

        code, redirect_uri = _wait_for_loopback_code(self._path, state, self._timeout, listening)
        res = self._post(
            "token",
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "code_verifier": verifier,
                **({"resource": self.resource} if self.resource else {}),
            },
        )
        try:
            out = res.json()
        except ValueError:
            out = {}
        if not res.is_success or not isinstance(out.get("access_token"), str):
            raise OAuthFlowError("token_exchange_failed", f"Sign-in failed: {out.get('error_description') or out.get('error') or res.status_code}.", res.status_code)
        session = self._session(out)
        self.store.save(session)
        return session

    def login(self) -> dict[str, Any]:
        """Sign in through the browser and store the session."""
        if self.mode == "device":
            return self._login_device()
        if self.mode == "loopback":
            return self._login_loopback()
        # auto: loopback when a browser can open on this machine, else the device flow. A loopback port that
        # cannot be opened (a locked-down host) falls back to the device flow too.
        if not self._can_open_browser():
            return self._login_device()
        try:
            return self._login_loopback()
        except OSError:
            return self._login_device()

    def get_access_token(self) -> str:
        """A valid access token, refreshed first when it expires within 60 seconds."""
        s = self._load()
        if not s:
            raise CliLoginRequiredError(self.app_name)
        if s["expires_at"] - self._now() > 60_000:
            return s["access_token"]
        if not s.get("refresh_token"):
            raise CliLoginRequiredError(self.app_name)
        with self._refresh_lock:
            s = self._load() or s  # another thread may have refreshed meanwhile
            if s["expires_at"] - self._now() > 60_000:
                return s["access_token"]
            return self._refresh(s)["access_token"]

    def _refresh(self, old: Mapping[str, Any]) -> dict[str, Any]:
        try:
            res = self._post(
                "token",
                {"grant_type": "refresh_token", "refresh_token": old["refresh_token"], "client_id": self.client_id, **({"resource": self.resource} if self.resource else {})},
            )
        except httpx.HTTPError:
            res = None
        out: dict[str, Any] = {}
        if res is not None:
            try:
                out = res.json()
            except ValueError:
                out = {}
        if res is not None and res.is_success and isinstance(out.get("access_token"), str):
            nxt = self._session(out, old)
            self.store.save(nxt)
            return nxt
        # Only a refusal ends the session; a network blip or 5xx keeps it for the next try.
        if res is not None and 400 <= res.status_code < 500:
            self.store.clear()
        raise CliLoginRequiredError(self.app_name)

    def logout(self) -> None:
        """Revoke at the issuer (best effort), then forget the session. Never raises on network failure."""
        s = self._load()
        if s:
            tokens = ([(s["refresh_token"], "refresh_token")] if s.get("refresh_token") else []) + [(s["access_token"], "access_token")]
            for token, hint in tokens:
                try:
                    self._post("revoke", {"token": token, "token_type_hint": hint, "client_id": self.client_id})
                except httpx.HTTPError:
                    pass
        self.store.clear()

    def status(self) -> dict[str, Any]:
        """What is stored, without any network call: ``signed_in``, ``expires_at``, ``scope``."""
        s = self._load()
        return {"signed_in": s is not None, "expires_at": s["expires_at"] if s else None, "scope": s.get("scope") if s else None}
