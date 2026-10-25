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
        body = re.sub(rf"(?<![.\w]){re.escape(name)}\b", async_name(name), body)
    body = body.replace("_SyncTransport", "_AsyncTransport")
    body = re.sub(r"^    def (?!__init__)", "    async def ", body, flags=re.M)
    body = body.replace("return self._t.request(", "return await self._t.request(")
    # Composite helpers (upload / wait_for) call sibling methods and sleep between polls.
    body = re.sub(r"(?<=[ (=])self\.(?!_t\b)([a-z]\w*)\(", r"await self.\1(", body)
    body = body.replace("time.sleep(", "await asyncio.sleep(")
    return HEADER + "\n" + body


def main() -> None:
    ASYNC.write_text(convert(SYNC.read_text()))


if __name__ == "__main__":
    main()
