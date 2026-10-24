"""Request shapes for the origin move, instance connections and integrations, logout
fan-out endpoints, managed email, back-channel delivery logs and tests, the Sign in
with Atlas app lookups and the publisher. Each row asserts method, path, query and
body on both the sync and the async clients.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import httpx
import pytest
import respx

from atlas_backend import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasClient,
    AtlasPlatformClient,
)

API_URL = "https://api.example.test"
MOVE = {"from": "https://old.example.com", "to": "https://new.example.com", "dry_run": True}

Row = tuple[str, str, Any, Callable[[Any], Any]]

BAPI: list[Row] = [
    (
        "GET",
        "/v1/atlas_id_apps/app_1/preflight",
        None,
        lambda c: c.atlas_id_grants.preflight("app_1"),
    ),
    ("POST", "/v1/instance/move_origin", MOVE, lambda c: c.instance.move_origin(MOVE)),
    ("GET", "/v1/instance/connections", None, lambda c: c.instance.connections()),
    (
        "GET",
        "/v1/instance/integrations/chatly",
        None,
        lambda c: c.instance.integrations.get_chatly(),
    ),
    (
        "PUT",
        "/v1/instance/integrations/chatly",
        {"channel": "support"},
        lambda c: c.instance.integrations.set_chatly({"channel": "support"}),
    ),
    (
        "DELETE",
        "/v1/instance/integrations/chatly",
        None,
        lambda c: c.instance.integrations.delete_chatly(),
    ),
    (
        "GET",
        "/v1/instance/integrations/forumulate",
        None,
        lambda c: c.instance.integrations.get_forumulate(),
    ),
    (
        "PUT",
        "/v1/instance/integrations/forumulate",
        {"org_id": "org_1", "spaces": ["sp_1"]},
        lambda c: c.instance.integrations.set_forumulate({"org_id": "org_1", "spaces": ["sp_1"]}),
    ),
    (
        "DELETE",
        "/v1/instance/integrations/forumulate",
        None,
        lambda c: c.instance.integrations.delete_forumulate(),
    ),
    ("GET", "/v1/logout_notify_endpoints", None, lambda c: c.logout_notify_endpoints.list()),
    (
        "POST",
        "/v1/logout_notify_endpoints",
        {"url": "https://hooks.example.com/logout"},
        lambda c: c.logout_notify_endpoints.create({"url": "https://hooks.example.com/logout"}),
    ),
    (
        "GET",
        "/v1/logout_notify_endpoints/lne_1",
        None,
        lambda c: c.logout_notify_endpoints.get("lne_1"),
    ),
    (
        "PATCH",
        "/v1/logout_notify_endpoints/lne_1",
        {"description": "x"},
        lambda c: c.logout_notify_endpoints.update("lne_1", {"description": "x"}),
    ),
    (
        "DELETE",
        "/v1/logout_notify_endpoints/lne_1",
        None,
        lambda c: c.logout_notify_endpoints.delete("lne_1"),
    ),
    (
        "GET",
        "/v1/logout_notify_endpoints/lne_1/deliveries?limit=5",
        None,
        lambda c: c.logout_notify_endpoints.list_deliveries("lne_1", limit=5),
    ),
    (
        "GET",
        "/v1/messaging_providers/email/managed",
        None,
        lambda c: c.messaging_providers.managed_email.get(),
    ),
    (
        "POST",
        "/v1/messaging_providers/email/managed",
        {
            "from_address": "no-reply@example.com",
            "dns": {"provider": "cloudflare", "api_token": "t"},
        },
        lambda c: c.messaging_providers.managed_email.create(
            {
                "from_address": "no-reply@example.com",
                "dns": {"provider": "cloudflare", "api_token": "t"},
            }
        ),
    ),
    (
        "POST",
        "/v1/messaging_providers/email/managed/verify",
        None,
        lambda c: c.messaging_providers.managed_email.verify(),
    ),
    (
        "DELETE",
        "/v1/messaging_providers/email/managed?force=true",
        None,
        lambda c: c.messaging_providers.managed_email.delete(force=True),
    ),
    (
        "GET",
        "/v1/oauth_clients/oac_1/backchannel_deliveries?limit=10&starting_after=d_1",
        None,
        lambda c: c.oauth_clients.list_backchannel_deliveries(
            "oac_1", limit=10, starting_after="d_1"
        ),
    ),
    (
        "POST",
        "/v1/oauth_clients/oac_1/backchannel_logout/test",
        None,
        lambda c: c.oauth_clients.test_backchannel_logout("oac_1"),
    ),
]

PLATFORM: list[Row] = [
    (
        "GET",
        "/v1/platform/atlas_id_apps/app_1/backchannel_deliveries",
        None,
        lambda c: c.atlas_id_apps.list_backchannel_deliveries("app_1"),
    ),
    (
        "POST",
        "/v1/platform/atlas_id_apps/app_1/backchannel_logout/test",
        None,
        lambda c: c.atlas_id_apps.test_backchannel_logout("app_1"),
    ),
    (
        "GET",
        "/v1/platform/atlas_id_apps/app_1/preflight",
        None,
        lambda c: c.atlas_id_apps.preflight("app_1"),
    ),
    (
        "GET",
        "/v1/platform/atlas_id_apps/app_1/users?email=a%40example.com",
        None,
        lambda c: c.atlas_id_apps.find_users("app_1", "a@example.com"),
    ),
    (
        "DELETE",
        "/v1/platform/atlas_id_apps/app_1/grants/gr_1",
        None,
        lambda c: c.atlas_id_apps.revoke_grant("app_1", "gr_1"),
    ),
    (
        "POST",
        "/v1/platform/atlas_id_apps/app_1/move_origin",
        MOVE,
        lambda c: c.atlas_id_apps.move_origin("app_1", MOVE),
    ),
    (
        "PUT",
        "/v1/platform/atlas_id_apps/app_1/managed_by",
        {"instance_id": "ins_1"},
        lambda c: c.atlas_id_apps.set_managed_by("app_1", "ins_1"),
    ),
    (
        "PUT",
        "/v1/platform/atlas_id_apps/app_1/managed_by",
        {"instance_id": None},
        lambda c: c.atlas_id_apps.set_managed_by("app_1", None),
    ),
    (
        "POST",
        "/v1/platform/atlas_id_apps/app_1/webhook/rotate_secret",
        None,
        lambda c: c.atlas_id_apps.rotate_webhook_secret("app_1"),
    ),
    ("GET", "/v1/platform/atlas_id_publisher", None, lambda c: c.atlas_id_publisher.get()),
    (
        "PUT",
        "/v1/platform/atlas_id_publisher",
        {"name": "Acme", "domain": "example.com"},
        lambda c: c.atlas_id_publisher.set({"name": "Acme", "domain": "example.com"}),
    ),
    (
        "PATCH",
        "/v1/platform/atlas_id_publisher",
        {"skip_consent": True},
        lambda c: c.atlas_id_publisher.update({"skip_consent": True}),
    ),
    ("DELETE", "/v1/platform/atlas_id_publisher", None, lambda c: c.atlas_id_publisher.delete()),
    (
        "POST",
        "/v1/platform/atlas_id_publisher/verify",
        None,
        lambda c: c.atlas_id_publisher.verify(),
    ),
    (
        "GET",
        "/v1/platform/config_changelog?action=atlas_id_app.updated&limit=5",
        None,
        lambda c: c.config_changelog.list(action="atlas_id_app.updated", limit=5),
    ),
]


def _check(route: respx.Route, method: str, path: str, body: Any) -> None:
    req = route.calls.last.request
    assert req.method == method
    url = req.url.raw_path.decode()
    assert url == path
    if body is None:
        assert not req.content
    else:
        assert json.loads(req.content) == body


@pytest.mark.parametrize(("method", "path", "body", "call"), BAPI)
def test_bapi_sync(method: str, path: str, body: Any, call: Callable[[Any], Any]) -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
        call(AtlasClient("sk_test_x", base_url=API_URL))
        _check(route, method, path, body)


@pytest.mark.parametrize(("method", "path", "body", "call"), BAPI)
def test_bapi_async(method: str, path: str, body: Any, call: Callable[[Any], Any]) -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
            await call(AsyncAtlasClient("sk_test_x", base_url=API_URL))
            _check(route, method, path, body)

    asyncio.run(run())


@pytest.mark.parametrize(("method", "path", "body", "call"), PLATFORM)
def test_platform_sync(method: str, path: str, body: Any, call: Callable[[Any], Any]) -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
        call(AtlasPlatformClient("psk_test_x", base_url=API_URL))
        _check(route, method, path, body)


@pytest.mark.parametrize(("method", "path", "body", "call"), PLATFORM)
def test_platform_async(method: str, path: str, body: Any, call: Callable[[Any], Any]) -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
            await call(AsyncAtlasPlatformClient("psk_test_x", base_url=API_URL))
            _check(route, method, path, body)

    asyncio.run(run())


def test_strict_move_origin_and_decoding() -> None:
    move = {
        "object": "origin_move",
        **MOVE,
        "applied": False,
        "changes": [
            {
                "object": "oauth_client",
                "id": "oac_1",
                "field": "redirect_uris",
                "before": ["https://old.example.com/cb"],
                "after": ["https://new.example.com/cb"],
            }
        ],
        "problems": [],
    }
    with respx.mock(base_url=API_URL) as mock:
        route = mock.post("/v1/instance/move_origin").mock(
            return_value=httpx.Response(200, json=move)
        )
        out = AtlasClient("sk_test_x", base_url=API_URL, strict=True).instance.move_origin(MOVE)
        assert route.calls.last.request.headers["Atlas-Strict"] == "true"
        assert out["changes"][0]["after"] == ["https://new.example.com/cb"]
