"""OAuth client secret rotation with overlap, the development email sender, managed
email on your own provider account, the issuer fields, login-readiness integration and
the new error codes.

All HTTP is mocked with respx; each test asserts the method, path and body the SDK
sends, and that the response decodes.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient, ErrorCode

SECRET = "sk_test_placeholder"
API_URL = "https://api.example.test"
DEV_PATH = f"{API_URL}/v1/messaging_providers/email/development"

ROTATION = {
    "object": "oauth_client",
    "id": "oac_1",
    "client_id": "cl_1",
    "name": "Dashboard",
    "logo_url": None,
    "redirect_uris": ["https://app.example.test/callback"],
    "allowed_scopes": ["openid"],
    "grant_types": ["authorization_code"],
    "token_endpoint_auth_method": "client_secret_basic",
    "secret_prefix": "cs_",
    "is_public": False,
    "first_party": True,
    "created_at": 0,
    "updated_at": 1,
    "client_secret": "cs_new",
    "overlap_seconds": 86400,
    "previous_secret_expires_at": 1_800_000_000_000,
    "note": "Store the secret now.",
}

DEVELOPMENT_EMAIL = {
    "object": "development_email",
    "provider_id": "mp_1",
    "enabled": True,
    "active": True,
    "transport": "resend",
    "from_address": "onboarding@resend.dev",
    "subject_prefix": "[Atlas test] ",
    "footer": "Sent by a development instance.",
    "templates": ["verification_code", "magic_link"],
    "limits": {"daily": 100, "per_recipient_hourly": 10},
    "note": "Resend delivers it only to your Resend account address.",
    "updated_at": 5,
}


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


def body_of(route: respx.Route) -> object:
    return json.loads(route.calls.last.request.content)


@respx.mock
def test_rotate_secret_sends_overlap_and_decodes_the_rotation() -> None:
    route = respx.post(f"{API_URL}/v1/oauth_clients/oac_1/rotate_secret").mock(
        return_value=httpx.Response(200, json=ROTATION)
    )
    out = client().oauth_clients.rotate_secret("oac_1", {"overlap_seconds": 0})
    assert body_of(route) == {"overlap_seconds": 0}
    assert out["client_secret"] == "cs_new"
    assert out["overlap_seconds"] == 86400
    assert out["previous_secret_expires_at"] == 1_800_000_000_000

    # No body keeps the server default (24 hours) and sends nothing.
    client().oauth_clients.rotate_secret("oac_1", idempotency_key="idem-1")
    request = route.calls.last.request
    assert request.content == b""
    assert request.headers["idempotency-key"] == "idem-1"


@respx.mock
def test_development_email_get_enable_disable() -> None:
    get = respx.get(DEV_PATH).mock(return_value=httpx.Response(200, json=DEVELOPMENT_EMAIL))
    post = respx.post(DEV_PATH).mock(return_value=httpx.Response(201, json=DEVELOPMENT_EMAIL))
    delete = respx.delete(DEV_PATH).mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "development_email",
                "deleted": True,
                "provider_id": "mp_1",
                "mode": "standard",
            },
        )
    )
    dev = client().messaging_providers.development_email
    assert dev.get()["limits"]["per_recipient_hourly"] == 10
    assert get.called
    out = dev.enable({"provider_id": "mp_1"})
    assert body_of(post) == {"provider_id": "mp_1"}
    assert out["subject_prefix"] == "[Atlas test] "
    dev.enable(
        {"transport": "brevo", "config": {"api_key": "xkeysib-x"}, "from_address": "me@example.com"}
    )
    assert body_of(post) == {
        "transport": "brevo",
        "config": {"api_key": "xkeysib-x"},
        "from_address": "me@example.com",
    }
    gone = dev.disable()
    assert delete.called and gone["mode"] == "standard"


@respx.mock
async def test_async_development_email_and_rotation() -> None:
    respx.get(DEV_PATH).mock(return_value=httpx.Response(200, json=DEVELOPMENT_EMAIL))
    rotate = respx.post(f"{API_URL}/v1/oauth_clients/oac_1/rotate_secret").mock(
        return_value=httpx.Response(200, json=ROTATION)
    )
    async with AsyncAtlasClient(SECRET, base_url=API_URL) as c:
        dev = await c.messaging_providers.development_email.get()
        assert dev["provider_id"] == "mp_1"
        await c.oauth_clients.rotate_secret("oac_1", {"overlap_seconds": 3600})
    assert body_of(rotate) == {"overlap_seconds": 3600}


@respx.mock
def test_managed_email_on_your_own_account_and_provider_mode() -> None:
    managed = {
        "object": "managed_email",
        "id": "me_1",
        "from_address": "hi@acme.example",
        "domain": "acme.example",
        "provider": "brevo",
        "backend": "brevo",
        "provider_id": "mp_2",
        "region": None,
        "status": "pending",
        "verified": False,
        "records": [
            {"purpose": "ownership", "type": "TXT", "name": "acme.example", "value": "brevo-code:1"}
        ],
        "limits": None,
        "usage": {
            "sent": 0,
            "bounces": 0,
            "complaints": 0,
            "last_bounce_at": None,
            "last_complaint_at": None,
        },
        "reputation": "your_provider_account",
        "feedback_webhook": "registered",
        "dns": None,
        "failure_reason": None,
        "last_checked_at": None,
        "verified_at": None,
        "created_at": 0,
        "updated_at": 0,
    }
    route = respx.post(f"{API_URL}/v1/messaging_providers/email/managed").mock(
        return_value=httpx.Response(201, json=managed)
    )
    out = client().messaging_providers.managed_email.create(
        {
            "from_address": "hi@acme.example",
            "transport": "brevo",
            "config": {"api_key": "xkeysib-x"},
        }
    )
    assert body_of(route) == {
        "from_address": "hi@acme.example",
        "transport": "brevo",
        "config": {"api_key": "xkeysib-x"},
    }
    assert out["limits"] is None and out["provider_id"] == "mp_2"
    assert out["feedback_webhook"] == "registered"

    provider = {
        "object": "messaging_provider",
        "id": "mp_1",
        "channel": "email",
        "mode": "development",
        "transport": "resend",
        "from_address": None,
        "status": "active",
        "config": {},
        "secrets_set": {"api_key": True},
        "updated_at": 1,
    }
    put = respx.put(f"{API_URL}/v1/messaging_providers/email").mock(
        return_value=httpx.Response(200, json=provider)
    )
    got = client().messaging_providers.set_email(
        {"transport": "resend", "mode": "development", "config": {"api_key": "re_x"}}
    )
    assert body_of(put)["mode"] == "development"
    assert got["id"] == "mp_1" and got["mode"] == "development"


@respx.mock
def test_instance_issuer_fields_and_origin_integrations() -> None:
    instance = {
        "object": "instance",
        "id": "ins_1",
        "environment": "production",
        "publishable_key": "pk_live_x",
        "frontend_api_host": "auth.acme.example",
        "issuer": "https://auth.acme.example",
        "discovery_url": "https://auth.acme.example/.well-known/openid-configuration",
        "jwks_uri": "https://auth.acme.example/.well-known/jwks.json",
        "allowed_origins": ["https://app.acme.example"],
        "allowed_origin_integrations": {"https://app.acme.example": "redirect"},
        "auth_config": {},
    }
    respx.get(f"{API_URL}/v1/instance").mock(return_value=httpx.Response(200, json=instance))
    patch = respx.patch(f"{API_URL}/v1/instance").mock(
        return_value=httpx.Response(200, json=instance)
    )
    got = client().instance.get()
    assert got["issuer"] == "https://auth.acme.example"
    assert got["allowed_origin_integrations"]["https://app.acme.example"] == "redirect"
    client().instance.update(
        {
            "allowed_origins": [
                "https://a.example",
                {"origin": "https://app.acme.example", "integration": "redirect"},
            ]
        }
    )
    assert body_of(patch) == {
        "allowed_origins": [
            "https://a.example",
            {"origin": "https://app.acme.example", "integration": "redirect"},
        ]
    }


@respx.mock
def test_login_readiness_integration_and_applies() -> None:
    respx.get(f"{API_URL}/v1/diagnostics/login_readiness").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "login_readiness",
                "origin": "https://app.acme.example",
                "live": False,
                "ready": True,
                "integration": {
                    "assumed": "redirect",
                    "source": "declared",
                    "reason": "Declared in allowed_origins.",
                },
                "checks": [
                    {
                        "name": "cors",
                        "pass": False,
                        "applies": False,
                        "observed": {},
                        "detail": "n/a",
                    }
                ],
            },
        )
    )
    out = client().diagnostics.login_readiness(origin="https://app.acme.example")
    assert out["integration"]["assumed"] == "redirect"
    assert out["checks"][0]["applies"] is False


@pytest.mark.parametrize(
    "code",
    [
        "READ_ONLY_FIELD",
        "DEVELOPMENT_EMAIL_NOT_ALLOWED",
        "DEVELOPMENT_EMAIL_UNAVAILABLE",
        "DEVELOPMENT_EMAIL_LIMIT_REACHED",
        "DEVELOPMENT_EMAIL_TEMPLATE_NOT_ALLOWED",
    ],
)
def test_new_error_codes(code: str) -> None:
    assert getattr(ErrorCode, code) == code
