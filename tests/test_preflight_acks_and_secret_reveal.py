"""Request shapes for the rest of the 0.23.0 surface: preflight acknowledgements,
``oauth_clients.reveal_secret`` / chosen ``client_secret`` / ``require_verified_email``,
the ``platform.apps.list`` finders, invitation expiry and the hook's ``fail_closed``.
Each row asserts method, path, query and body on both the sync and the async clients.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import httpx
import pytest
import respx

from atlas_backend import AsyncAtlasClient, AsyncAtlasPlatformClient, AtlasClient, AtlasPlatformClient

API_URL = "https://api.example.test"

# (client kind, method, path, query, body, call)
Row = tuple[str, str, str, dict[str, str], Any, Callable[[Any], Any]]

ROWS: list[Row] = [
    ("app", "GET", "/v1/instance/preflight/acks", {}, None, lambda c: c.instance.list_preflight_acks()),
    (
        "app",
        "PUT",
        "/v1/instance/preflight/acks/webhook_endpoint_off_origin",
        {},
        {"reason": "ops host", "expires_at": 1893456000000},
        lambda c: c.instance.acknowledge_preflight(
            "webhook_endpoint_off_origin", {"reason": "ops host", "expires_at": 1893456000000}
        ),
    ),
    (
        "app",
        "PUT",
        "/v1/instance/preflight/acks/pkce_not_required",
        {"dry_run": "true"},
        {"reason": "legacy client"},
        lambda c: c.instance.acknowledge_preflight("pkce_not_required", {"reason": "legacy client"}, dry_run=True),
    ),
    (
        "app",
        "DELETE",
        "/v1/instance/preflight/acks/pkce_not_required",
        {},
        None,
        lambda c: c.instance.delete_preflight_ack("pkce_not_required"),
    ),
    ("app", "POST", "/v1/oauth_clients/oac_1/secret/reveal", {}, None, lambda c: c.oauth_clients.reveal_secret("oac_1")),
    (
        "app",
        "POST",
        "/v1/oauth_clients",
        {},
        {"name": "App", "redirect_uris": ["https://app.example.com/cb"], "client_secret": "s" * 40,
         "require_verified_email": True},
        lambda c: c.oauth_clients.create(
            {"name": "App", "redirect_uris": ["https://app.example.com/cb"], "client_secret": "s" * 40,
             "require_verified_email": True}
        ),
    ),
    (
        "app",
        "PATCH",
        "/v1/oauth_clients/oac_1",
        {},
        {"require_verified_email": False},
        lambda c: c.oauth_clients.update("oac_1", {"require_verified_email": False}),
    ),
    (
        "app",
        "POST",
        "/v1/invitations",
        {},
        {"email_address": "a@example.com", "expires_in_days": 30},
        lambda c: c.invitations.create({"email_address": "a@example.com", "expires_in_days": 30}),
    ),
    (
        "app",
        "PATCH",
        "/v1/instance/hooks/before_user_create",
        {},
        {"fail_closed": True},
        lambda c: c.instance.hooks.update_before_user_create({"fail_closed": True}),
    ),
    (
        "platform",
        "GET",
        "/v1/platform/apps",
        {"name_prefix": "acme", "external_ref": "acme/prod", "limit": "50", "starting_after": "ins_9"},
        None,
        lambda c: c.apps.list(name_prefix="acme", external_ref="acme/prod", limit=50, starting_after="ins_9"),
    ),
    ("platform", "GET", "/v1/platform/apps", {"name": "Acme"}, None, lambda c: c.apps.list(name="Acme")),
]


def _check(route: respx.Route, method: str, path: str, query: dict[str, str], body: Any) -> None:
    req = route.calls.last.request
    assert req.method == method
    assert req.url.path == path
    assert dict(req.url.params) == query
    if body is None:
        assert not req.content
    else:
        assert json.loads(req.content) == body


def _sync(kind: str) -> Any:
    if kind == "platform":
        return AtlasPlatformClient("psk_test_x", base_url=API_URL)
    return AtlasClient("sk_test_x", base_url=API_URL)


def _async(kind: str) -> Any:
    if kind == "platform":
        return AsyncAtlasPlatformClient("psk_test_x", base_url=API_URL)
    return AsyncAtlasClient("sk_test_x", base_url=API_URL)


@pytest.mark.parametrize("row", ROWS)
def test_request_shapes(row: Row) -> None:
    kind, method, path, query, body, call = row
    with respx.mock(base_url=API_URL) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
        call(_sync(kind))
        _check(route, method, path, query, body)

    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
            await call(_async(kind))
            _check(route, method, path, query, body)

    asyncio.run(run())


def test_reveal_and_acknowledged_finding_decode() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.post("/v1/oauth_clients/oac_1/rotate_secret").mock(
            return_value=httpx.Response(
                200,
                json={"object": "oauth_client", "id": "oac_1", "client_secret": "s1",
                      "client_secret_reveal": {"path": "/v1/oauth_clients/oac_1/secret/reveal",
                                               "expires_at": 1893456000000}},
            )
        )
        mock.post("/v1/oauth_clients/oac_1/secret/reveal").mock(
            return_value=httpx.Response(
                200,
                json={"object": "oauth_client_secret", "id": "oac_1", "client_id": "atlas_client_1",
                      "client_secret": "s1", "secret_prefix": "s1", "client_secret_expires_at": None,
                      "note": "shown once"},
            )
        )
        mock.get("/v1/instance/preflight").mock(
            return_value=httpx.Response(
                200,
                json={"object": "preflight", "ok": True, "checked_at": 1, "findings": [
                    {"severity": "warning", "code": "pkce_not_required", "message": "m", "fix": "f",
                     "acknowledged": {"reason": "legacy", "by": "ak_1", "at": 1, "expires_at": None}},
                ]},
            )
        )
        c = AtlasClient("sk_test_x", base_url=API_URL)
        rotated = c.oauth_clients.rotate_secret("oac_1")
        assert rotated["client_secret_reveal"]["path"] == "/v1/oauth_clients/oac_1/secret/reveal"
        assert c.oauth_clients.reveal_secret("oac_1")["client_secret"] == "s1"
        findings = c.instance.preflight()["findings"]
        assert [f for f in findings if "acknowledged" not in f] == []
