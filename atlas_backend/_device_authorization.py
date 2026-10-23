"""Device sign-in approval (OAuth 2.0 Device Authorization Grant, RFC 8628) from your
own app: the signed-in user types — or scans — the code a TV, console or CLI shows, and
your app approves it instead of sending them to Atlas's hosted ``/oauth2/device`` page.

These calls run on the Frontend API as the signed-in USER: they need the user's session
token (a native app's session JWT), never a secret key, PAT or OAuth token.

    devices = DeviceAuthorizations("https://clerk.example.com", session_token)
    auth = devices.lookup(typed_code)
    # show auth["client"]["name"] and auth["scopes"], then
    devices.approve(auth)  # or devices.deny(auth)
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import httpx

__all__ = [
    "AsyncDeviceAuthorizations",
    "DeviceAuthorizations",
    "DeviceAuthorizationError",
    "format_user_code",
    "user_code_from_url",
]

_BASE = "/v1/client/me/device_authorizations"


class DeviceAuthorizationError(Exception):
    """A refused request; ``code`` is the server's stable error code (``NOT_FOUND``,
    ``RATE_LIMITED``, ``STEP_UP_REQUIRED``, …)."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        param: str | None = None,
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.param = param
        self.reason = reason

    @property
    def needs_reverification(self) -> bool:
        """Approving needs a fresh re-authentication first."""
        return self.code == "STEP_UP_REQUIRED"

    @property
    def is_invalid_code(self) -> bool:
        """The code is unknown, expired or already used."""
        return self.status in (404, 409)


def format_user_code(value: str) -> str:
    """Normalise what a person typed into the ``XXXX-XXXX`` form devices show; returns
    the trimmed input unchanged when it is not 8 letters or digits."""
    cleaned = re.sub(r"[^A-Z0-9]", "", value.upper())
    return f"{cleaned[:4]}-{cleaned[4:]}" if len(cleaned) == 8 else value.strip()


def user_code_from_url(url: str) -> str | None:
    """The ``user_code`` of a verification URL the device displayed, formatted."""
    parsed = urlparse(url)
    if not parsed.scheme:
        return None
    values = parse_qs(parsed.query).get("user_code")
    return format_user_code(values[0]) if values and values[0] else None


def _headers(token: str, publishable_key: str | None) -> dict[str, str]:
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}
    if publishable_key:
        headers["x-publishable-key"] = publishable_key
    return headers


def _result(res: httpx.Response) -> dict[str, Any]:
    try:
        data = res.json()
    except ValueError:
        data = None
    if res.status_code < 200 or res.status_code > 299:
        first: dict[str, Any] = {}
        if isinstance(data, dict) and isinstance(data.get("errors"), list) and data["errors"]:
            first = data["errors"][0] or {}
        raise DeviceAuthorizationError(
            res.status_code,
            first.get("code") or "UNKNOWN",
            first.get("message") or "The request failed.",
            first.get("param"),
            first.get("reason"),
        )
    return data if isinstance(data, dict) else {}


class DeviceAuthorizations:
    """Look up, approve or deny a pending device sign-in as the signed-in user."""

    def __init__(
        self,
        frontend_api: str,
        session_token: str,
        *,
        publishable_key: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base = frontend_api.rstrip("/")
        self._token = session_token
        self._pk = publishable_key
        self._http = http_client or httpx.Client(timeout=10.0)

    def _call(self, path: str, body: dict[str, str]) -> dict[str, Any]:
        res = self._http.post(self._base + path, json=body, headers=_headers(self._token, self._pk))
        return _result(res)

    def lookup(self, user_code: str) -> dict[str, Any]:
        """Find a pending device sign-in by the code the device shows."""
        return self._call(f"{_BASE}/lookup", {"user_code": format_user_code(user_code)})

    def approve(self, authorization: dict[str, Any]) -> dict[str, Any]:
        """Approve for the signed-in user; the device's next poll receives its tokens."""
        return self._call(
            f"{_BASE}/{quote(authorization['id'], safe='')}/approve",
            {"user_code": authorization["user_code"]},
        )

    def deny(self, authorization: dict[str, Any]) -> dict[str, Any]:
        """Deny; the device's next poll is told ``access_denied``."""
        return self._call(
            f"{_BASE}/{quote(authorization['id'], safe='')}/deny",
            {"user_code": authorization["user_code"]},
        )


class AsyncDeviceAuthorizations:
    """The async peer of :class:`DeviceAuthorizations`, over an ``httpx.AsyncClient``."""

    def __init__(
        self,
        frontend_api: str,
        session_token: str,
        *,
        publishable_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base = frontend_api.rstrip("/")
        self._token = session_token
        self._pk = publishable_key
        self._http = http_client or httpx.AsyncClient(timeout=10.0)

    async def _call(self, path: str, body: dict[str, str]) -> dict[str, Any]:
        res = await self._http.post(
            self._base + path, json=body, headers=_headers(self._token, self._pk)
        )
        return _result(res)

    async def lookup(self, user_code: str) -> dict[str, Any]:
        """Find a pending device sign-in by the code the device shows."""
        return await self._call(f"{_BASE}/lookup", {"user_code": format_user_code(user_code)})

    async def approve(self, authorization: dict[str, Any]) -> dict[str, Any]:
        """Approve for the signed-in user; the device's next poll receives its tokens."""
        return await self._call(
            f"{_BASE}/{quote(authorization['id'], safe='')}/approve",
            {"user_code": authorization["user_code"]},
        )

    async def deny(self, authorization: dict[str, Any]) -> dict[str, Any]:
        """Deny; the device's next poll is told ``access_denied``."""
        return await self._call(
            f"{_BASE}/{quote(authorization['id'], safe='')}/deny",
            {"user_code": authorization["user_code"]},
        )
