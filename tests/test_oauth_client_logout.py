"""Request shapes for the 0.23.0 surface: ``oauth_clients.logout``,
``refresh_touches_session`` / ``add_redirect_origins`` on OAuth client writes and
``site_key`` on ``instance.set_captcha_secret``. Each row asserts method, path and body
on both the sync and the async clients.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import httpx
import pytest
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient

API_URL = "https://api.example.test"

Row = tuple[str, str, Any, Callable[[Any], Any]]

ROWS: list[Row] = [
    (
        "POST",
        "/v1/oauth_clients/oac_1/logout",
        {"sid": "sess_1"},
        lambda c: c.oauth_clients.logout("oac_1", "sess_1"),
    ),
    (
        "POST",
        "/v1/oauth_clients",
        {"name": "App", "redirect_uris": ["https://app.example.com/cb"], "first_party": True,
         "refresh_touches_session": True, "add_redirect_origins": True},
        lambda c: c.oauth_clients.create(
            {"name": "App", "redirect_uris": ["https://app.example.com/cb"], "first_party": True,
             "refresh_touches_session": True, "add_redirect_origins": True}
        ),
    ),
    (
        "PATCH",
        "/v1/oauth_clients/oac_1",
        {"refresh_touches_session": False, "add_redirect_origins": True},
        lambda c: c.oauth_clients.update(
            "oac_1", {"refresh_touches_session": False, "add_redirect_origins": True}
        ),
    ),
    (
        "PUT",
        "/v1/instance/captcha_secret",
        {"secret": "0x4AAA", "provider": "turnstile", "site_key": "0x4BBB"},
        lambda c: c.instance.set_captcha_secret(
            {"secret": "0x4AAA", "provider": "turnstile", "site_key": "0x4BBB"}
        ),
    ),
]

LOGOUT = {
    "object": "oauth_client_logout",
    "client_id": "atlas_client_1",
    "sid": "sess_1",
    "session": "revoked",
    "grants_revoked": 2,
    "backchannel_logouts": 3,
}


def _check(route: respx.Route, method: str, path: str, body: Any) -> None:
    req = route.calls.last.request
    assert req.method == method
    assert req.url.path == path
    assert json.loads(req.content) == body


@pytest.mark.parametrize("row", ROWS)
def test_request_shapes(row: Row) -> None:
    method, path, body, call = row
    with respx.mock(base_url=API_URL) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
        call(AtlasClient("sk_test_x", base_url=API_URL))
        _check(route, method, path, body)

    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
            await call(AsyncAtlasClient("sk_test_x", base_url=API_URL))
            _check(route, method, path, body)

    asyncio.run(run())


def test_logout_result_and_idempotency_key() -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.post("/v1/oauth_clients/oac_1/logout").mock(
            return_value=httpx.Response(200, json=LOGOUT)
        )
        out = AtlasClient("sk_test_x", base_url=API_URL).oauth_clients.logout(
            "oac_1", "sess_1", idempotency_key="idem-1"
        )
        assert route.calls.last.request.headers["idempotency-key"] == "idem-1"
    assert out["session"] == "revoked"
    assert out["grants_revoked"] == 2 and out["backchannel_logouts"] == 3


def test_added_origins_and_captcha_switched_decode() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.post("/v1/oauth_clients").mock(
            return_value=httpx.Response(
                200,
                json={"object": "oauth_client", "id": "oac_1", "refresh_touches_session": True,
                      "added_origins": ["https://app.example.com"]},
            )
        )
        mock.put("/v1/instance/captcha_secret").mock(
            return_value=httpx.Response(
                200,
                json={"object": "captcha_secret", "provider": "turnstile", "set": True,
                      "switched": True, "captcha": {"provider": "turnstile", "siteKey": "0x4BBB"}},
            )
        )
        c = AtlasClient("sk_test_x", base_url=API_URL)
        created = c.oauth_clients.create({"name": "App", "redirect_uris": ["https://app.example.com/cb"]})
        assert created["added_origins"] == ["https://app.example.com"]
        assert created["refresh_touches_session"] is True
        out = c.instance.set_captcha_secret({"secret": "0x4AAA", "provider": "turnstile", "site_key": "0x4BBB"})
        assert out["switched"] is True and out["captcha"]["siteKey"] == "0x4BBB"
