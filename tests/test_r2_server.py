"""Round-2 server surface: sealed-secret recipient option, SSO claims, new model shapes."""

from __future__ import annotations

import asyncio

import httpx
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient, ErrorCode
from atlas_backend import models as m
from atlas_backend._verify import SessionClaims

API_URL = "https://api.example.test"


def test_secret_recipient_header_sync() -> None:
    with respx.mock(base_url=API_URL) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={}))
        AtlasClient("sk_test_x", base_url=API_URL, secret_recipient="x25519:abc").users.list()
        assert route.calls.last.request.headers["x-secret-recipient"] == "x25519:abc"
        AtlasClient("sk_test_x", base_url=API_URL).users.list()
        assert "x-secret-recipient" not in route.calls.last.request.headers
        base = AtlasClient("sk_test_x", base_url=API_URL, secret_recipient="x25519:abc")
        base.with_options(strict=True).users.list()
        assert route.calls.last.request.headers["x-secret-recipient"] == "x25519:abc"


def test_secret_recipient_header_async() -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={}))
            c = AsyncAtlasClient("sk_test_x", base_url=API_URL, secret_recipient="x25519:abc")
            await c.users.list()
            assert route.calls.last.request.headers["x-secret-recipient"] == "x25519:abc"

    asyncio.run(run())


def test_session_claims_sso() -> None:
    c = SessionClaims.from_raw(
        {
            "sub": "u",
            "sso_connection_id": "sso_1",
            "sso_organization_id": "org_1",
            "sso_connection_type": "saml",
        }
    )
    assert (c.sso_connection_id, c.sso_organization_id, c.sso_connection_type) == (
        "sso_1",
        "org_1",
        "saml",
    )
    bare = SessionClaims.from_raw({"sub": "u", "sso_connection_type": "ldap"})
    assert bare.sso_organization_id == "" and bare.sso_connection_type == ""


def test_new_shapes_exist() -> None:
    result: m.DryRunResult = {
        "object": "dry_run",
        "dry_run": True,
        "mode": "rollback",
        "validated": True,
        "method": "POST",
        "path": "/v1/users",
        "changes": [],
        "note": "",
        "would_return_status": 201,
        "suppressed": ["email"],
    }
    assert result["mode"] == "rollback"
    assert ErrorCode.ORIGIN_NOT_ALLOWED == "ORIGIN_NOT_ALLOWED"
    assert "sealed_secret" in m.SealedSecrets.__optional_keys__
    assert "managed_via" in m.AtlasIdApp.__optional_keys__
    assert "button_rendered_origins" in m.AtlasIdAppPreflightDetail.__optional_keys__
