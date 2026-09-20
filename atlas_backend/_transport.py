"""The shared HTTP core every resource namespace calls.

One place decides how a BAPI request is authenticated, serialized, and how a
failure becomes an :class:`AtlasError` — so a namespace method is a one-liner
naming a method, a path, and its shapes. Built on ``httpx``, which gives us a
sync :class:`httpx.Client` and an async :class:`httpx.AsyncClient` from the same
request-building helpers below.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Union

import httpx

from ._errors import AtlasError, ErrorItem

#: The default BAPI origin, overridable per instance via ``base_url``.
DEFAULT_BASE_URL = "https://api.atlasauth.net"

QueryScalar = Union[str, int, float, bool, None]
QueryParams = Mapping[str, Union[QueryScalar, Sequence[QueryScalar]]]


def _join_url(base: str, path: str) -> str:
    """Join the base origin and a ``/v1/...`` path, tolerating trailing slashes."""
    trimmed = base.rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{trimmed}{suffix}"


def _serialize_query(query: QueryParams | None) -> list[tuple[str, Any]]:
    """Flatten a query mapping, dropping ``None`` values and spreading sequences."""
    if not query:
        return []
    params: list[tuple[str, Any]] = []
    for key, value in query.items():
        if value is None:
            continue
        values = list(value) if isinstance(value, (list, tuple)) else [value]
        for item in values:
            if item is None:
                continue
            if isinstance(item, bool):
                params.append((key, "true" if item else "false"))
            else:
                params.append((key, str(item)))
    return params


def _build_headers(
    secret_key: str,
    *,
    has_body: bool,
    idempotency_key: str | None,
) -> dict[str, str]:
    """Assemble request headers. The secret is only ever sent as a Bearer token."""
    headers: dict[str, str] = {
        "authorization": f"Bearer {secret_key}",
        "accept": "application/json",
    }
    if has_body:
        headers["content-type"] = "application/json"
    if idempotency_key:
        headers["idempotency-key"] = idempotency_key
    return headers


def _parse_success(status_code: int, text: str, *, raw: bool) -> Any:
    """Turn a 2xx response into a Python value (or ``None`` for empty bodies)."""
    if status_code == 204 or not text:
        return None
    if raw:
        return text
    return json.loads(text)


def _to_error(status_code: int, text: str) -> AtlasError:
    """Parse a non-2xx body into the §9.1 envelope, or synthesize one."""
    errors: list[ErrorItem] = []
    message: str | None = None
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            message = text[:500]
        else:
            envelope = parsed.get("errors") if isinstance(parsed, dict) else None
            if isinstance(envelope, list) and envelope:
                errors = envelope
            else:
                message = text[:500]
    if not errors:
        errors = [
            {
                "code": "UNKNOWN",
                "message": message
                or f"Atlas API request failed with status {status_code}",
            }
        ]
    return AtlasError(status_code, errors)


class _SyncTransport:
    """Config-bound synchronous requester handed to every resource namespace."""

    def __init__(
        self,
        secret_key: str,
        base_url: str,
        client: httpx.Client,
    ) -> None:
        self._secret_key = secret_key
        self._base_url = base_url
        self._client = client

    def request(
        self,
        *,
        method: str,
        path: str,
        query: QueryParams | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        raw: bool = False,
    ) -> Any:
        content = None if body is None else json.dumps(body)
        response = self._client.request(
            method,
            _join_url(self._base_url, path),
            params=_serialize_query(query),
            content=content,
            headers=_build_headers(
                self._secret_key,
                has_body=body is not None,
                idempotency_key=idempotency_key,
            ),
        )
        if not response.is_success:
            raise _to_error(response.status_code, response.text)
        return _parse_success(response.status_code, response.text, raw=raw)


class _AsyncTransport:
    """Config-bound asynchronous requester handed to every async namespace."""

    def __init__(
        self,
        secret_key: str,
        base_url: str,
        client: httpx.AsyncClient,
    ) -> None:
        self._secret_key = secret_key
        self._base_url = base_url
        self._client = client

    async def request(
        self,
        *,
        method: str,
        path: str,
        query: QueryParams | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        raw: bool = False,
    ) -> Any:
        content = None if body is None else json.dumps(body)
        response = await self._client.request(
            method,
            _join_url(self._base_url, path),
            params=_serialize_query(query),
            content=content,
            headers=_build_headers(
                self._secret_key,
                has_body=body is not None,
                idempotency_key=idempotency_key,
            ),
        )
        if not response.is_success:
            raise _to_error(response.status_code, response.text)
        return _parse_success(response.status_code, response.text, raw=raw)
