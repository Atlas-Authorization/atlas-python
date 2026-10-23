"""Every Backend API and Platform API operation is reachable from the SDK.

``openapi_operations.txt`` is the list of ``METHOD /path`` operations tagged BAPI
or PLATFORM in the public OpenAPI document (refresh it when the API grows). This
test calls every public method of every namespace — on both the sync and the
async clients — against a catch-all mock, records the method and path each one
sends, and checks the union covers every listed operation.
"""

from __future__ import annotations

import asyncio
import inspect
import re
from pathlib import Path
from typing import Any

import httpx
import respx

from atlas_backend import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasClient,
    AtlasPlatformClient,
)

API_URL = "https://api.example.test"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
OPS_FILE = Path(__file__).with_name("openapi_operations.txt")
#: Composite helpers built from the operations above (tested on their own), not
#: operations themselves: ``upload`` needs a real import id, ``wait_for`` polls.
COMPOSITES = {"BetterAuthImports": {"upload", "wait_for"}}


def _composite(ns: Any, name: str) -> bool:
    return name in COMPOSITES.get(type(ns).__name__.removeprefix("Async"), set())


def _spec_ops() -> set[tuple[str, str]]:
    out = set()
    for line in OPS_FILE.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            method, path = line.split()
            out.add((method, re.sub(r"\{[^}]+\}", "{}", path)))
    return out


def _namespaces(root: Any) -> list[Any]:
    """Every namespace object reachable from a client (depth-first)."""
    out: list[Any] = []
    seen: set[int] = set()

    def walk(obj: Any) -> None:
        for name, value in vars(obj).items():
            if name.startswith("_") or id(value) in seen:
                continue
            if type(value).__module__.startswith("atlas_backend.") and hasattr(value, "_t"):
                seen.add(id(value))
                out.append(value)
                walk(value)

    walk(root)
    return out


def _args_for(fn: Any) -> tuple[list[Any], dict[str, Any], list[str]]:
    """Placeholder arguments for a resource method, plus the path-segment values used."""
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    placeholders: list[str] = []
    for p in inspect.signature(fn).parameters.values():
        if p.default is not inspect.Parameter.empty:
            continue
        if p.kind is inspect.Parameter.KEYWORD_ONLY:
            kwargs[p.name] = "https://app.example.test"
        elif p.name == "body":
            args.append({})
        elif p.name == "data":
            args.append(PNG)
        elif p.name in ("claims", "permissions"):
            args.append({} if p.name == "claims" else [])
        elif p.name in ("email_address", "identifier", "role"):
            args.append("value")
        else:
            value = f"ph{len(placeholders)}x"
            placeholders.append(value)
            args.append(value)
    return args, kwargs, placeholders


def _normalize(path: str, placeholders: list[str]) -> str:
    segments = ["{}" if s in placeholders else s for s in path.split("/")]
    return "/".join(segments)


def _record(calls: list[tuple[str, str]], placeholders: list[str], route: respx.Route) -> None:
    req = route.calls.last.request
    calls.append((req.method, _normalize(req.url.path, placeholders)))


def _sync_ops(client: Any) -> set[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    with respx.mock(base_url=API_URL, assert_all_called=False) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={}))
        for ns in _namespaces(client):
            for name, fn in inspect.getmembers(ns, inspect.ismethod):
                if name.startswith("_") or _composite(ns, name):
                    continue
                args, kwargs, ph = _args_for(fn)
                fn(*args, **kwargs)
                _record(seen, ph, route)
    return set(seen)


def _async_ops(client: Any) -> set[tuple[str, str]]:
    seen: list[tuple[str, str]] = []

    async def run() -> None:
        with respx.mock(base_url=API_URL, assert_all_called=False) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={}))
            for ns in _namespaces(client):
                for name, fn in inspect.getmembers(ns, inspect.ismethod):
                    if name.startswith("_") or _composite(ns, name):
                        continue
                    args, kwargs, ph = _args_for(fn)
                    await fn(*args, **kwargs)
                    _record(seen, ph, route)

    asyncio.run(run())
    return set(seen)


def test_sync_clients_cover_every_operation() -> None:
    covered = _sync_ops(AtlasClient("sk_test", base_url=API_URL)) | _sync_ops(
        AtlasPlatformClient("psk_test", base_url=API_URL)
    )
    missing = sorted(_spec_ops() - covered)
    assert not missing, f"{len(missing)} operations have no SDK method: {missing}"


def test_async_clients_cover_every_operation() -> None:
    covered = _async_ops(AsyncAtlasClient("sk_test", base_url=API_URL)) | _async_ops(
        AsyncAtlasPlatformClient("psk_test", base_url=API_URL)
    )
    missing = sorted(_spec_ops() - covered)
    assert not missing, f"{len(missing)} operations have no SDK method: {missing}"
