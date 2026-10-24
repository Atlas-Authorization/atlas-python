"""The shared HTTP core every resource namespace calls.

One place decides how a BAPI request is authenticated, serialized, and how a
failure becomes an :class:`AtlasError` — so a namespace method is a one-liner
naming a method, a path, and its shapes. Built on ``httpx``, which gives us a
sync :class:`httpx.Client` and an async :class:`httpx.AsyncClient` from the same
request-building helpers below.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Callable, Union

import httpx

from ._errors import AtlasError, ErrorItem

#: The default BAPI origin, overridable per instance via ``base_url``.
DEFAULT_BASE_URL = "https://api.atlasauth.net"

#: Called with ``(fields, method, path)`` when a write succeeded but Atlas
#: ignored body fields the endpoint does not accept (the ``Atlas-Unknown-Fields``
#: response header). ``fields`` are the ignored names, nested ones as
#: ``parent.child``.
UnknownFieldsHook = Callable[[list[str], str, str], None]

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

logger = logging.getLogger("atlas_backend")

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
    content_type: str | None = None,
    strict: bool | None = None,
    method: str = "GET",
) -> dict[str, str]:
    """Assemble request headers. The secret is only ever sent as a Bearer token."""
    headers: dict[str, str] = {
        "authorization": f"Bearer {secret_key}",
        "accept": "application/json",
    }
    if has_body:
        headers["content-type"] = content_type or "application/json"
    if idempotency_key:
        headers["idempotency-key"] = idempotency_key
    if strict is not None and method.upper() in _WRITE_METHODS:
        headers["atlas-strict"] = "true" if strict else "false"
    return headers


def _report_unknown_fields(
    response: httpx.Response,
    method: str,
    path: str,
    hook: UnknownFieldsHook | None,
) -> None:
    """Surface the ``Atlas-Unknown-Fields`` header through the hook (or a log line)."""
    header = response.headers.get("atlas-unknown-fields")
    if not header:
        return
    fields = [f.strip() for f in header.split(",") if f.strip()]
    if not fields:
        return
    if hook is not None:
        hook(fields, method, path)
    else:
        logger.warning(
            "Atlas ignored unknown body field(s) on %s %s: %s",
            method,
            path,
            ", ".join(fields),
        )


def _encode_body(body: Any, content: bytes | None) -> tuple[bytes | str | None, bool]:
    """Pick the wire payload: raw bytes win over a JSON body."""
    if content is not None:
        return content, True
    if body is None:
        return None, False
    return json.dumps(body), True


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
                "message": message or f"Atlas API request failed with status {status_code}",
            }
        ]
    return AtlasError(status_code, errors)


class _BaseTransport:
    """Config shared by the sync and async requesters."""

    def __init__(
        self,
        secret_key: str,
        base_url: str,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        self._secret_key = secret_key
        self._base_url = base_url
        self._strict = strict
        self._on_unknown_fields = on_unknown_fields
        self._traceparent = traceparent
        self._secret_recipient = secret_recipient

    def _prepare(
        self,
        method: str,
        path: str,
        query: QueryParams | None,
        body: Any,
        idempotency_key: str | None,
        content: bytes | None,
        content_type: str | None,
        strict: bool | None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        payload, has_body = _encode_body(body, content)
        built = _build_headers(
            self._secret_key,
            has_body=has_body,
            idempotency_key=idempotency_key,
            content_type=content_type,
            strict=self._strict if strict is None else strict,
            method=method,
        )
        if self._traceparent:
            # W3C Trace Context: Atlas carries the trace id onto the webhooks, logouts and
            # privacy cases the call causes.
            built["traceparent"] = self._traceparent
        if self._secret_recipient:
            # Ask Atlas to seal every shown-once secret in the answer to this key
            # (``x25519:<base64 public key>``); open the ``sealed_*`` fields with SealedBox.
            built["X-Secret-Recipient"] = self._secret_recipient
        if headers:
            # Extra per-call headers (e.g. the end user's forwarded IP). They can
            # never replace the Bearer secret.
            built.update({k: v for k, v in headers.items() if k.lower() != "authorization"})
        return {
            "method": method,
            "url": _join_url(self._base_url, path),
            "params": _serialize_query(query),
            "content": payload,
            "headers": built,
        }

    def _finish(self, response: httpx.Response, method: str, path: str, raw: bool) -> Any:
        if not response.is_success:
            raise _to_error(response.status_code, response.text)
        _report_unknown_fields(response, method, path, self._on_unknown_fields)
        return _parse_success(response.status_code, response.text, raw=raw)


class _SyncTransport(_BaseTransport):
    """Config-bound synchronous requester handed to every resource namespace."""

    def __init__(
        self,
        secret_key: str,
        base_url: str,
        client: httpx.Client,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        super().__init__(
            secret_key,
            base_url,
            strict=strict,
            on_unknown_fields=on_unknown_fields,
            traceparent=traceparent,
            secret_recipient=secret_recipient,
        )
        self._client = client

    def with_options(
        self,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> _SyncTransport:
        return _SyncTransport(
            self._secret_key,
            self._base_url,
            self._client,
            strict=self._strict if strict is None else strict,
            on_unknown_fields=on_unknown_fields or self._on_unknown_fields,
            traceparent=traceparent or self._traceparent,
            secret_recipient=secret_recipient or self._secret_recipient,
        )

    def request(
        self,
        *,
        method: str,
        path: str,
        query: QueryParams | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        raw: bool = False,
        content: bytes | None = None,
        content_type: str | None = None,
        strict: bool | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self._client.request(
            **self._prepare(
                method, path, query, body, idempotency_key, content, content_type, strict, headers
            )
        )
        return self._finish(response, method, path, raw)


class _AsyncTransport(_BaseTransport):
    """Config-bound asynchronous requester handed to every async namespace."""

    def __init__(
        self,
        secret_key: str,
        base_url: str,
        client: httpx.AsyncClient,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        super().__init__(
            secret_key,
            base_url,
            strict=strict,
            on_unknown_fields=on_unknown_fields,
            traceparent=traceparent,
            secret_recipient=secret_recipient,
        )
        self._client = client

    def with_options(
        self,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> _AsyncTransport:
        return _AsyncTransport(
            self._secret_key,
            self._base_url,
            self._client,
            strict=self._strict if strict is None else strict,
            on_unknown_fields=on_unknown_fields or self._on_unknown_fields,
            traceparent=traceparent or self._traceparent,
            secret_recipient=secret_recipient or self._secret_recipient,
        )

    async def request(
        self,
        *,
        method: str,
        path: str,
        query: QueryParams | None = None,
        body: Any = None,
        idempotency_key: str | None = None,
        raw: bool = False,
        content: bytes | None = None,
        content_type: str | None = None,
        strict: bool | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = await self._client.request(
            **self._prepare(
                method, path, query, body, idempotency_key, content, content_type, strict, headers
            )
        )
        return self._finish(response, method, path, raw)
