"""The generated catalog: request shapes, cursor iterators, async mirror and freshness."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import httpx
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient

API_URL = "https://api.example.test"
ROOT = Path(__file__).resolve().parent.parent


def test_write_sends_idempotency_key_and_encodes_the_path_segment() -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.delete("/v1/app_catalog/custom_presets/a%2Fb").mock(
            return_value=httpx.Response(200, json={})
        )
        AtlasClient("sk_t", base_url=API_URL).app_catalog.delete_custom_preset(
            "a/b", idempotency_key="k1"
        )
    assert route.calls.last.request.headers["idempotency-key"] == "k1"


def test_dry_run_and_body() -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.post("/v1/iga/bundles").mock(return_value=httpx.Response(200, json={}))
        AtlasClient("sk_t", base_url=API_URL).iga.create_bundle({"name": "b"}, dry_run=True)  # type: ignore[typeddict-item]
    req = route.calls.last.request
    assert req.url.params["dry_run"] == "true"
    assert json.loads(req.content) == {"name": "b"}


def test_iter_follows_the_cursor() -> None:
    pages = [
        httpx.Response(200, json={"data": [{"id": "a"}], "has_more": True, "next_cursor": "a"}),
        httpx.Response(200, json={"data": [{"id": "b"}], "has_more": False, "next_cursor": None}),
    ]
    with respx.mock(base_url=API_URL) as mock:
        route = mock.get("/v1/iga/bundles").mock(side_effect=pages)
        items = list(AtlasClient("sk_t", base_url=API_URL).iga.iter_list_bundles(limit=1))
    assert [i["id"] for i in items] == ["a", "b"]
    assert route.calls[1].request.url.params["starting_after"] == "a"


def test_async_iter_follows_the_cursor() -> None:
    pages = [
        httpx.Response(200, json={"data": [{"id": "a"}], "has_more": True, "next_cursor": "a"}),
        httpx.Response(200, json={"data": [{"id": "b"}], "has_more": False, "next_cursor": None}),
    ]

    async def run() -> list[str]:
        with respx.mock(base_url=API_URL) as mock:
            mock.get("/v1/iga/bundles").mock(side_effect=pages)
            client = AsyncAtlasClient("sk_t", base_url=API_URL)
            return [i["id"] async for i in client.iga.iter_list_bundles()]

    assert asyncio.run(run()) == ["a", "b"]


def test_hand_written_namespace_inherits_generated_methods() -> None:
    client = AtlasClient("sk_t", base_url=API_URL)
    assert callable(client.billing.delete_coupon)
    assert callable(AsyncAtlasClient("sk_t", base_url=API_URL).billing.delete_coupon)


def test_generated_files_are_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_catalog.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_jwt_template_update_carries_settings() -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.patch("/v1/jwt_templates/t1").mock(return_value=httpx.Response(200, json={}))
        AtlasClient("sk_t", base_url=API_URL).jwt_templates.update("t1", settings={"lifetime_seconds": 300})
    assert json.loads(route.calls.last.request.content) == {"settings": {"lifetime_seconds": 300}}


def test_patch_body_can_clear_a_field_with_explicit_null() -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.patch("/v1/authenticator_policies/p1").mock(return_value=httpx.Response(200, json={}))
        client = AtlasClient("sk_t", base_url=API_URL)
        client.authenticator_policies.update("p1", {"grace_until": None})
        assert json.loads(route.calls.last.request.content) == {"grace_until": None}
        client.authenticator_policies.update("p1", {"name": "x"})  # an unset key is omitted
        assert json.loads(route.calls.last.request.content) == {"name": "x"}
