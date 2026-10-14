"""The async namespaces are exactly the sync ones, made async.

``aresources.py`` is generated from ``resources.py`` by ``scripts/gen_async.py``.
Comparing ASTs (not text) makes this independent of formatting: if someone edits
one module without regenerating the other, this fails.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_generator():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("gen_async", ROOT / "scripts" / "gen_async.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_async_module_matches_the_sync_module() -> None:
    gen = _load_generator()
    expected = gen.convert((ROOT / "atlas_backend" / "resources.py").read_text())
    actual = (ROOT / "atlas_backend" / "aresources.py").read_text()
    assert ast.dump(ast.parse(expected)) == ast.dump(ast.parse(actual)), (
        "aresources.py is stale: run `python scripts/gen_async.py && "
        "ruff format atlas_backend/aresources.py`"
    )


def test_every_sync_client_namespace_has_an_async_twin() -> None:
    from atlas_backend import (
        AsyncAtlasClient,
        AsyncAtlasPlatformClient,
        AtlasClient,
        AtlasPlatformClient,
    )

    pairs = [
        (AtlasClient("sk_x"), AsyncAtlasClient("sk_x")),
        (AtlasPlatformClient("psk_x"), AsyncAtlasPlatformClient("psk_x")),
    ]
    for sync, async_ in pairs:
        sync_ns = {k for k in vars(sync) if not k.startswith("_")}
        async_ns = {k for k in vars(async_) if not k.startswith("_")}
        assert sync_ns == async_ns
        for name in sync_ns:
            s_methods = {m for m in dir(getattr(sync, name)) if not m.startswith("_")}
            a_methods = {m for m in dir(getattr(async_, name)) if not m.startswith("_")}
            assert s_methods == a_methods, name
