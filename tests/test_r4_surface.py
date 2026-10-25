"""Test and review accounts, platform domains, new app fields and error codes."""

from __future__ import annotations

import asyncio
import json

import httpx
import respx

from atlas_backend import (
    AsyncAtlasPlatformClient,
    AtlasError,
    AtlasPlatformClient,
    ErrorCode,
)

API_URL = "https://api.example.test"
PASSWORD = "Sup3r-secret-pw-123"
ACCT = {"object": "atlas_id_provisioned_account", "id": "pa_1", "password": PASSWORD}
SEALED = {"object": "atlas_id_provisioned_account", "id": "pa_1", "sealed_password": "sealed:abc"}


def _got(mock: respx.MockRouter) -> list[tuple[str, str]]:
    return [(c.request.method, c.request.url.raw_path.decode()) for c in mock.calls]


EXPECTED = [
    ("GET", "/v1/platform/atlas_id_apps/app1/provisioned_accounts"),
    ("POST", "/v1/platform/atlas_id_apps/app1/provisioned_accounts"),
    ("GET", "/v1/platform/atlas_id_apps/app1/provisioned_accounts/pa_1"),
    ("DELETE", "/v1/platform/atlas_id_apps/app1/provisioned_accounts/pa_1"),
    ("POST", "/v1/platform/atlas_id_apps/app1/provisioned_accounts/pa_1/password"),
    ("GET", "/v1/platform/domains"),
    ("POST", "/v1/platform/domains"),
    ("POST", "/v1/platform/domains/d1/verify"),
    ("POST", "/v1/platform/domains/d1/verify"),
    ("DELETE", "/v1/platform/domains/d1"),
]


def test_sync_routes_and_sealed_password() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json=ACCT))
        c = AtlasPlatformClient("psk_test", base_url=API_URL)
        pa = c.atlas_id_apps.provisioned_accounts
        pa.list("app1")
        made = pa.create("app1", {"email": "a@x.test", "label": "r"}, secret_recipient="x25519:AAAA")
        pa.get("app1", "pa_1")
        pa.remove("app1", "pa_1")
        pa.rotate_password("app1", "pa_1")
        c.domains.list()
        c.domains.claim("x.test")
        c.domains.check("d1")
        c.domains.verify("d1")
        c.domains.remove("d1")
        assert _got(mock) == EXPECTED
        assert mock.calls[1].request.headers["X-Secret-Recipient"] == "x25519:AAAA"
        assert "X-Secret-Recipient" not in mock.calls[4].request.headers
        assert json.loads(mock.calls[6].request.content) == {"domain": "x.test"}
        assert made["password"] == PASSWORD


def test_sealed_response_has_no_plaintext() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json=SEALED))
        c = AtlasPlatformClient("psk_test", base_url=API_URL)
        out = c.atlas_id_apps.provisioned_accounts.rotate_password(
            "app1", "pa_1", secret_recipient="x25519:AAAA"
        )
        assert "password" not in out and out["sealed_password"] == "sealed:abc"
        assert PASSWORD not in repr(c) and PASSWORD not in repr(c.atlas_id_apps.provisioned_accounts)


def test_async_routes() -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            mock.route().mock(return_value=httpx.Response(200, json=ACCT))
            c = AsyncAtlasPlatformClient("psk_test", base_url=API_URL)
            pa = c.atlas_id_apps.provisioned_accounts
            await pa.list("app1")
            await pa.create("app1", {"email": "a@x.test", "label": "r"})
            await pa.get("app1", "pa_1")
            await pa.remove("app1", "pa_1")
            await pa.rotate_password("app1", "pa_1", {"password": "twelve-chars-ok"})
            await c.domains.list()
            await c.domains.claim("x.test")
            await c.domains.check("d1")
            await c.domains.verify("d1")
            await c.domains.remove("d1")
            assert _got(mock) == EXPECTED

    asyncio.run(run())


def test_error_codes() -> None:
    assert ErrorCode.TEST_ACCOUNT_RESTRICTED == "TEST_ACCOUNT_RESTRICTED"
    assert ErrorCode.PROVISIONED_ACCOUNT_LIMIT_REACHED == "PROVISIONED_ACCOUNT_LIMIT_REACHED"
    assert ErrorCode.DOMAIN_NOT_VERIFIED == "DOMAIN_NOT_VERIFIED"
    with respx.mock(base_url=API_URL) as mock:
        body = {"errors": [{"code": "DOMAIN_NOT_VERIFIED", "message": "x"}]}
        mock.route().mock(return_value=httpx.Response(422, json=body))
        c = AtlasPlatformClient("psk_test", base_url=API_URL)
        try:
            c.atlas_id_apps.update("app1", {"test_mode": True})
        except AtlasError as e:
            assert e.code == ErrorCode.DOMAIN_NOT_VERIFIED
        else:
            raise AssertionError("expected AtlasError")
