"""Partner platforms, per-call audiences, privacy orchestrator fields, include_deleted."""

from __future__ import annotations

import asyncio
import json
import logging

import httpx
import pytest
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient, AtlasError, ErrorCode
from atlas_backend import models as m

API_URL = "https://api.example.test"
SECRET_TOKEN = "ptok_super_secret_value_123"

PLATFORM: m.PartnerPlatform = {
    "object": "partner_platform",
    "partner": "acme-consent",
    "token_set": True,
    "token_prefix": "ptok_sup",
}


def _calls(mock: respx.MockRouter) -> list[tuple[str, str, bytes]]:
    return [
        (c.request.method, c.request.url.raw_path.decode(), c.request.content) for c in mock.calls
    ]


def test_partner_platforms_sync_routes() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json=PLATFORM))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        c.partner_platforms.list()
        c.partner_platforms.get("acme-consent")
        c.partner_platforms.set("acme-consent", {"enabled": True})
        c.partner_platforms.delete("acme-consent")
        c.partner_platforms.registration("acme-consent")
        c.partner_platforms.store_token(
            "acme-consent", SECRET_TOKEN, rotate=True, api_base_url="https://p.example"
        )
        c.partner_platforms.deliveries("acme-consent", limit=5)
        got = [(mth, path) for mth, path, _ in _calls(mock)]
        assert got == [
            ("GET", "/v1/partner_platforms"),
            ("GET", "/v1/partner_platforms/acme-consent"),
            ("PUT", "/v1/partner_platforms/acme-consent"),
            ("DELETE", "/v1/partner_platforms/acme-consent"),
            ("GET", "/v1/partner_platforms/acme-consent/registration"),
            ("POST", "/v1/partner_platforms/acme-consent/token"),
            ("GET", "/v1/partner_platforms/acme-consent/deliveries?limit=5"),
        ]
        assert json.loads(_calls(mock)[5][2]) == {
            "token": SECRET_TOKEN,
            "rotate": True,
            "api_base_url": "https://p.example",
        }


def test_partner_platforms_async_routes() -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            mock.route().mock(return_value=httpx.Response(200, json=PLATFORM))
            c = AsyncAtlasClient("sk_test_x", base_url=API_URL)
            await c.partner_platforms.store_token("acme-consent", SECRET_TOKEN)
            await c.partner_platforms.deliveries("acme-consent")
            assert [(a, b) for a, b, _ in _calls(mock)] == [
                ("POST", "/v1/partner_platforms/acme-consent/token"),
                ("GET", "/v1/partner_platforms/acme-consent/deliveries"),
            ]
            assert json.loads(_calls(mock)[0][2]) == {"token": SECRET_TOKEN}

    asyncio.run(run())


def test_partner_token_never_in_response_repr_or_log(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json=PLATFORM))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        out = c.partner_platforms.store_token("acme-consent", SECRET_TOKEN)
    assert SECRET_TOKEN not in repr(out) and SECRET_TOKEN not in json.dumps(out)
    assert "token" not in out
    assert SECRET_TOKEN not in caplog.text
    assert SECRET_TOKEN not in repr(c)
    assert "token" not in m.PartnerPlatform.__annotations__
    assert "token" not in m.PartnerPlatformRegistration.__annotations__


def test_partner_token_not_in_error_text() -> None:
    err = {"errors": [{"code": "VALIDATION_FAILED", "message": "bad token"}]}
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(422, json=err))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        with pytest.raises(AtlasError) as ei:
            c.partner_platforms.store_token("acme-consent", SECRET_TOKEN)
    assert SECRET_TOKEN not in str(ei.value) and SECRET_TOKEN not in repr(ei.value)


def test_per_call_audience_query() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json={"jwt": "x"}))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        c.sessions.get_token("sess_1", "cookiemunch", cbid="dv-1")
        c.sessions.get_token("sess_1", "acme", audience="acme:t1", audience_params={"tenant": "t1"})
        c.integrations.get_token("sess_1", "acme", audience_params={"tenant": "t2"})
        c.sessions.get_token("sess_1", "chatly")
        paths = [p for _, p, _ in _calls(mock)]
        assert paths == [
            "/v1/sessions/sess_1/integration_tokens/cookiemunch?cbid=dv-1",
            "/v1/sessions/sess_1/integration_tokens/acme?tenant=t1&audience=acme%3At1",
            "/v1/sessions/sess_1/integration_tokens/acme?tenant=t2",
            "/v1/sessions/sess_1/integration_tokens/chatly",
        ]


def test_per_call_audience_async() -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            mock.route().mock(return_value=httpx.Response(200, json={"jwt": "x"}))
            c = AsyncAtlasClient("sk_test_x", base_url=API_URL)
            await c.sessions.get_token("s", "cookiemunch", cbid="dv-1")
            await c.integrations.get_token("s", "acme", audience="acme:t1")
            assert [p for _, p, _ in _calls(mock)] == [
                "/v1/sessions/s/integration_tokens/cookiemunch?cbid=dv-1",
                "/v1/sessions/s/integration_tokens/acme?audience=acme%3At1",
            ]

    asyncio.run(run())


def test_integration_per_call_audience_body_and_off() -> None:
    pca: m.PerCallAudience = {"param": "tenant", "template": "acme:{tenant}", "allowed": ["t1"]}
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json={}))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        c.integrations.set("acme", {"audience": "acme:t0", "per_call_audience": pca})
        c.integrations.set("acme", {"per_call_audience": None})
        assert json.loads(_calls(mock)[0][2])["per_call_audience"] == pca
        assert json.loads(_calls(mock)[1][2]) == {"per_call_audience": None}


def test_privacy_orchestrator_fields() -> None:
    body: m.PrivacyOrchestratorInput = {
        "provider": "acme-consent",
        "site_id": "site-1",
        "partner_link_id": "pl_1",
        "cancel_deletion_on_sign_in": True,
    }
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json={"site_id": "site-1"}))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        c.privacy.orchestrator.set(body)
        assert json.loads(_calls(mock)[0][2]) == body


def test_users_list_include_deleted_and_operator() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(
            return_value=httpx.Response(200, json={"data": [], "audiences": ["acme"]})
        )
        c = AtlasClient("sk_test_x", base_url=API_URL)
        c.users.list(include_deleted=True)
        c.users.list(include_deleted=False)
        c.users.list()
        paths = [p for _, p, _ in _calls(mock)]
        assert paths == [
            "/v1/users?include_deleted=true",
            "/v1/users?include_deleted=false",
            "/v1/users",
        ]
        assert c.keys.operator()["audiences"] == ["acme"]


def test_managed_waf_error_code() -> None:
    assert ErrorCode.MANAGED_WAF_NOT_CONFIGURED == "MANAGED_WAF_NOT_CONFIGURED"
    item = {"code": "MANAGED_WAF_NOT_CONFIGURED", "message": "x", "meta": {"action": "provision"}}
    body = {"errors": [item]}
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(422, json=body))
        c = AtlasClient("sk_test_x", base_url=API_URL)
        with pytest.raises(AtlasError) as ei:
            c.managed_waf.provision()
    assert ei.value.code == ErrorCode.MANAGED_WAF_NOT_CONFIGURED
