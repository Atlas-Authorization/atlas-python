"""Regenerate ``atlas_backend/aresources.py`` from ``atlas_backend/resources.py``.

The async namespaces are a mechanical mirror of the sync ones: every class gains
an ``Async`` prefix, every method becomes ``async def`` and awaits the transport.
Keeping one hand-edited source and deriving the other guarantees the two clients
never drift. Edit ``resources.py``, then run::

    python scripts/gen_async.py && ruff format atlas_backend/aresources.py

``tests/test_parity.py`` fails if the two modules disagree.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "atlas_backend" / "resources.py"
ASYNC = ROOT / "atlas_backend" / "aresources.py"

HEADER = '''"""Asynchronous resource namespaces — the async peer of :mod:`resources`.

Same method↔endpoint map, same shapes, over an :class:`httpx.AsyncClient`.
Generated from :mod:`resources` by ``scripts/gen_async.py``; edit the sync
module and regenerate rather than editing this file.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Sequence
from typing import Any, Literal
from urllib.parse import urlencode

from . import _acatalog as ac
from . import models as m
from ._transport import _AsyncTransport
from ._types import JSON, CursorPage, DeletedObject, ListPage
from .resources import (
    BETTER_AUTH_IMPORT_IN_FLIGHT,
    BETTER_AUTH_IMPORT_PART_BYTES,
    _audience_query,
    _csv,
    _dry,
    _enc,
    _json,
    _meta,
    _q,
    _sniff_image_type,
    split_bundle_parts,
)

'''


def async_name(name: str) -> str:
    return f"_Async{name[1:]}" if name.startswith("_") else f"Async{name}"


def convert(src: str) -> str:
    body = src[src.index("\nclass ") + 1 :]
    names = re.findall(r"^class (\w+)\b", body, re.M)
    for name in sorted(names, key=len, reverse=True):
        # Only the definition and constructor calls: the same word in a docstring stays as written.
        body = re.sub(rf"(?<![.\w])(class )?{re.escape(name)}\b(?=\(|:)", lambda mo: (mo.group(1) or "") + async_name(name), body)
    body = re.sub(r"\(c\.(\w+)\)", lambda mo: f"(ac.{async_name(mo.group(1))})", body)
    body = body.replace("_SyncTransport", "_AsyncTransport")
    body = re.sub(r"^    def (?!__init__|_wire_catalog)", "    async def ", body, flags=re.M)
    body = body.replace("return self._t.request(", "return await self._t.request(")
    # Composite helpers (upload / wait_for) call sibling methods and sleep between polls.
    body = re.sub(r"(?<=[ (=])self\.(?!_t\b)([a-z]\w*)\(", r"await self.\1(", body)
    body = body.replace("time.sleep(", "await asyncio.sleep(")
    return HEADER + "\n" + body


CATALOG_HEADER = '''"""Generated async Backend API / Platform API operations (do not edit).

The async peer of ``_catalog.py``, derived from it by ``scripts/gen_async.py``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Literal

from . import catalog_models as cm
from ._transport import _AsyncTransport
from ._util import _enc, _qd

'''


def convert_catalog(src: str) -> str:
    """Mirror the generated sync catalog (``_catalog.py``) into its async twin."""
    body = src[src.index("\nclass ") + 1 :]
    names = re.findall(r"^class (\w+)\b", body, re.M)
    for name in sorted(names, key=len, reverse=True):
        body = re.sub(rf"(?<![.\w])(class )?{re.escape(name)}\b(?=\(|:)", lambda mo: (mo.group(1) or "") + async_name(name), body)
        body = re.sub(rf"^(    \w+: ){re.escape(name)}$", rf"\1{async_name(name)}", body, flags=re.M)
    body = body.replace("_SyncTransport", "_AsyncTransport").replace("Iterator[", "AsyncIterator[")
    body = re.sub(r"^    def (?!__init__|_wire_catalog)", "    async def ", body, flags=re.M)
    body = body.replace("return self._t.request(", "return await self._t.request(")
    body = re.sub(r"(?<=[ (=])self\.(?!_t\b)([a-z]\w*)\(", r"await self.\1(", body)
    return CATALOG_HEADER + "\n" + body


# -- relying party and mirrors: mechanical async twins of ``_rp.py`` / ``_mirrors.py`` ------------------

import ast  # noqa: E402

_EXT_WRAP = r"self\.(?:store|api_keys|sid_store)\.\w+\(|self\._client\.[\w.]+\(|self\._exec\(|self\._membership\(|self\.on_(?:signed_in|sign_in_error|sign_out|backchannel_logout)\(|self\._http\.(?:get|post)\(|self\._edge\.check\(|self\._verifier\.verify\(|self\._jwks\.get\("


def _wrap(text: str, pattern: str, prefix: str, skip: tuple[str, ...]) -> str:
    """Wrap every call matching ``pattern`` as ``(prefix<call>)`` + ``)`` so ``await`` binds to the whole call."""
    rx = re.compile(pattern)
    while True:
        hit = None
        for mo in rx.finditer(text):
            if not text[: mo.start()].endswith(skip):
                hit = mo
        if hit is None:
            return text
        depth, i, quote = 1, hit.end(), ""
        while depth:
            c = text[i]
            if quote:
                if c == "\\":
                    i += 1
                elif c == quote:
                    quote = ""
            elif c in "\"'":
                quote = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            i += 1
        text = f"{text[:hit.start()]}({prefix}{text[hit.start():i]}{')' * (1 + prefix.count('('))}{text[i:]}"


def _top_level(src: str) -> tuple[str, list[str], dict[str, str]]:
    """(import section, names defined at module level, class name -> class source)."""
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    first = next(n for n in tree.body if not isinstance(n, (ast.Expr, ast.ImportFrom, ast.Import)))
    imports = "".join(lines[tree.body[1].lineno - 1 : first.lineno - 1]) if isinstance(tree.body[0], ast.Expr) else ""
    names, classes = [], {}
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            classes[n.name] = "".join(lines[n.lineno - 1 : n.end_lineno])
        if isinstance(n, (ast.ClassDef, ast.FunctionDef)):
            names.append(n.name)
        elif isinstance(n, ast.Assign):
            names += [t.id for t in n.targets if isinstance(t, ast.Name)]
    return imports, names, classes


def _asyncify(block: str, methods: set[str], renames: list[str]) -> str:
    block = block.replace("jwks=lambda kid: self._jwks.get(kid)", "jwks=await self._jwks.get(JwksCache.read_kid(token))")
    for name in methods:
        block = re.sub(rf"^    def {name}\(", f"    async def {name}(", block, flags=re.M)
    block = _wrap(block, rf"self\.(?:{'|'.join(sorted(methods))})\(", "await ", ("await ", "def "))
    block = _wrap(block, _EXT_WRAP, "await _aw(", ("await _aw(", "await "))
    for old, new in [
        ("threading.Lock()", "_AsyncLock()"),
        ("with self._lock:", "async with self._lock:"),
        ("httpx.Client", "httpx.AsyncClient"),
        ("self._http.close()", "await self._http.aclose()"),
        ("jwks=lambda kid: self._jwks.get(kid)", "jwks=await self._jwks.get(JwksCache.read_kid(token))"),
        ("LogoutTokenVerifier(", "AsyncLogoutTokenVerifier("),
        (" JwksCache(", " AsyncJwksCache("),
    ]:
        block = block.replace(old, new)
    for name in renames:
        block = re.sub(rf"\b{name}\b(?=\()|(?<=class ){name}\b", f"Async{name}", block)
    return block


_ASYNC_HEAD = '''"""{doc}

Generated from ``{src}`` by ``scripts/gen_async.py`` (do not edit). Stores, callbacks and API clients may be
sync or async: awaitables are awaited. Use these with :class:`~atlas_backend.AsyncAtlasClient`.
"""

'''

_MIRROR_EXTRAS = '''

class AsyncMemoryWebhookStore:
    """An async :class:`WebhookDedupeStore` for one process (the in-memory store behind an async interface).
    A shared store implements ``async def set_if_absent(key, ttl_seconds) -> bool`` and optionally ``async def delete(key)``."""

    def __init__(self, now: Callable[[], int] | None = None) -> None:
        self._inner = MemoryWebhookStore(now)

    async def set_if_absent(self, key: str, ttl_seconds: int) -> bool:
        return self._inner.set_if_absent(key, ttl_seconds)

    async def delete(self, key: str) -> None:
        self._inner.delete(key)


@dataclass
class AsyncDedupedWebhook:
    event: dict[str, Any]
    #: True when this delivery id was already seen: acknowledge with 2xx and do nothing.
    duplicate: bool
    delivery_id: str
    _release: Callable[[], Any] = field(default=lambda: None, repr=False)

    async def release(self) -> None:
        """Forget this delivery so Atlas's retry is processed, e.g. after your handler failed."""
        await _aw(self._release())


async def verify_and_dedupe_async(
    body: bytes | str,
    headers: Mapping[str, Any],
    secret: str,
    store: Any,
    *,
    ttl_seconds: int = 86_400,
    key_prefix: str = "atlas-webhook:",
    url: str | None = None,
    require_v2: bool = False,
    standard: bool = False,
    now_ms: int | None = None,
) -> AsyncDedupedWebhook:
    """:func:`verify_and_dedupe` over an async store (sync stores work too)."""
    if standard:
        res = verify_standard_webhook(body, headers, secret, now_s=None if now_ms is None else now_ms // 1000)
    else:
        res = verify_webhook(body, headers, secret, url=url, require_v2=require_v2, now_ms=now_ms)
    if not res.verified or not res.delivery_id:
        raise WebhookVerificationError(res.reason or "signature_mismatch")
    if res.event is None:
        raise WebhookVerificationError("invalid_body")
    key = f"{key_prefix}{res.delivery_id}"
    fresh = await _aw(store.set_if_absent(key, ttl_seconds))
    drop = getattr(store, "delete", None)
    return AsyncDedupedWebhook(res.event, not fresh, res.delivery_id, (lambda: drop(key)) if callable(drop) else (lambda: None))
'''

_RP_EXTRAS = '''

class AsyncMemorySidStore(MemorySidStore):
    """:class:`MemorySidStore` behind the async :class:`SidStore` interface (``async bind`` / ``async take``)."""

    async def bind(self, sid: str, app_session_id: str, expires_at_ms: int) -> None:  # type: ignore[override]
        MemorySidStore.bind(self, sid, app_session_id, expires_at_ms)

    async def take(self, sid: str) -> list[str]:  # type: ignore[override]
        return MemorySidStore.take(self, sid)
'''


def _convert_ext(src: str, name: str, doc: str, classes: dict[str, set[str]], extra_imports: str, extras: str) -> str:
    imports, names, blocks = _top_level(src)
    keep = [n for n in names if n not in classes]
    body = "\n\n".join(_asyncify(blocks[c], m, list(classes)) for c, m in classes.items())
    return (
        _ASYNC_HEAD.format(doc=doc, src=name)
        + imports
        + extra_imports
        + "from ." + name.removesuffix(".py") + " import (  # noqa: F401\n"
        + "".join(f"    {n},\n" for n in keep)
        + ")\n\n\n"
        + body
        + extras
    )


def convert_rp(src: str) -> str:
    return _convert_ext(
        src, "_rp.py", "Asynchronous relying party: the asyncio peer of :mod:`atlas_backend._rp`.",
        {
            "RelyingParty": {"_discover", "start", "_start", "callback", "_callback", "_exchange", "_verify_id_token",
                             "require_recent_auth", "_session_call", "_app_session_call", "touch_if_due", "revoke_session",
                             "end_app_session", "bind_session", "backchannel_logout", "sign_out", "handle", "close"},
            "SqlSidStore": {"bind", "take"},
        },
        "from ._async_support import AsyncJwksCache, AsyncLogoutTokenVerifier, _AsyncLock, _aw\n",
        _RP_EXTRAS,
    )


def convert_mirrors(src: str) -> str:
    return _convert_ext(
        src, "_mirrors.py", "Asynchronous mirrors and revocation: the asyncio peers of :mod:`atlas_backend._mirrors`.",
        {
            "KeyMirror": {"_freshness", "verify_assertion", "last_sync_at", "mint", "rotate", "import_key", "revoke", "verify", "sync", "apply_webhook"},
            "ResourceRoleMirror": {"_chain", "check", "can", "sync", "apply_webhook"},
            "EdgeRevocationChecker": {"_refresh", "check"},
            "SidRevocationList": {"is_revoked", "_poll"},
            "SqlWebhookDedupeStore": {"set_if_absent", "delete"},
        },
        "from ._async_support import AsyncJwksCache, _AsyncLock, _aw\nfrom ._verify import JwksCache\n",
        _MIRROR_EXTRAS,
    )


def main() -> None:
    ASYNC.write_bytes((convert(SYNC.read_text(encoding="utf-8"))).encode("utf-8"))
    pkg = ROOT / "atlas_backend"
    (pkg / "_arp.py").write_bytes((convert_rp((pkg / "_rp.py").read_text(encoding="utf-8"))).encode("utf-8"))
    (pkg / "_amirrors.py").write_bytes((convert_mirrors((pkg / "_mirrors.py").read_text(encoding="utf-8"))).encode("utf-8"))
    cat = ROOT / "atlas_backend" / "_catalog.py"
    if cat.exists():
        (ROOT / "atlas_backend" / "_acatalog.py").write_bytes((convert_catalog(cat.read_text(encoding="utf-8"))).encode("utf-8"))


if __name__ == "__main__":
    main()
