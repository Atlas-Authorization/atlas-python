"""OAuth client ``skip_logout_confirmation``, the cookie-consent settings link,
``force`` on messaging-provider delete, and the session fields on
``users.list_sessions``.

All HTTP is mocked with respx; each test asserts the method, path and body the
SDK sends, and that the response decodes.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient, AtlasError, ErrorCode

SECRET = "sk_test_placeholder"
API_URL = "https://api.example.test"

OAUTH_CLIENT = {
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
    "skip_logout_confirmation": True,
    "created_at": 0,
    "updated_at": 1,
}

SETTINGS_LINK = {
    "label": "Cookie settings",
    "preset": "cookiebot",
    "attributes": {"class": "footer-link"},
    "rendered_attributes": {"class": "footer-link", "data-cc": "c-settings"},
}

CONSENT = {
    "object": "cookie_consent",
    "enabled": True,
    "script_url": "https://cmp.example/s.js",
    "script_id": None,
    "site_id": "site_1",
    "blocking_mode": "auto",
    "extra_origins": [],
    "settings_link": SETTINGS_LINK,
}

DELETED = {"object": "messaging_provider", "channel": "email", "deleted": True}


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


def body_of(route: respx.Route) -> object:
    return json.loads(route.calls.last.request.content)


# --------------------------------------------------------------------------- #
# OAuth clients                                                                #
# --------------------------------------------------------------------------- #


@respx.mock
def test_oauth_client_create_update_and_read_skip_logout_confirmation() -> None:
    create = respx.post(f"{API_URL}/v1/oauth_clients").mock(
        return_value=httpx.Response(201, json={**OAUTH_CLIENT, "client_secret": "cs_x"})
    )
    update = respx.patch(f"{API_URL}/v1/oauth_clients/oac_1").mock(
        return_value=httpx.Response(200, json={**OAUTH_CLIENT, "skip_logout_confirmation": False})
    )
    respx.get(f"{API_URL}/v1/oauth_clients/oac_1").mock(
        return_value=httpx.Response(200, json=OAUTH_CLIENT)
    )
    c = client()
    c.oauth_clients.create(
        {
            "name": "Dashboard",
            "redirect_uris": ["https://app.example.test/callback"],
            "first_party": True,
            "post_logout_redirect_uris": ["https://app.example.test/"],
            "skip_logout_confirmation": True,
        }
    )
    assert body_of(create) == {
        "name": "Dashboard",
        "redirect_uris": ["https://app.example.test/callback"],
        "first_party": True,
        "post_logout_redirect_uris": ["https://app.example.test/"],
        "skip_logout_confirmation": True,
    }
    updated = c.oauth_clients.update("oac_1", {"skip_logout_confirmation": False})
    assert body_of(update) == {"skip_logout_confirmation": False}
    assert updated["skip_logout_confirmation"] is False
    assert c.oauth_clients.get("oac_1")["skip_logout_confirmation"] is True


@respx.mock
def test_oauth_client_skip_logout_confirmation_refused_on_third_party() -> None:
    respx.patch(f"{API_URL}/v1/oauth_clients/oac_1").mock(
        return_value=httpx.Response(
            422,
            json={
                "errors": [
                    {
                        "code": "VALIDATION_FAILED",
                        "message": "first-party clients only",
                        "param": "skip_logout_confirmation",
                    }
                ]
            },
        )
    )
    with pytest.raises(AtlasError) as exc:
        client().oauth_clients.update("oac_1", {"skip_logout_confirmation": True})
    assert exc.value.status == 422
    assert exc.value.has_code(ErrorCode.VALIDATION_FAILED)
    assert exc.value.errors[0]["param"] == "skip_logout_confirmation"


# --------------------------------------------------------------------------- #
# Cookie consent settings link                                                 #
# --------------------------------------------------------------------------- #


@respx.mock
def test_cookie_consent_settings_link_set_and_decode() -> None:
    put = respx.put(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json=CONSENT)
    )
    respx.get(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json=CONSENT)
    )
    c = client()
    out = c.instance.cookie_consent.set(
        {
            "script_url": "https://cmp.example/s.js",
            "settings_link": {
                "label": "Cookie settings",
                "preset": "cookiebot",
                "attributes": {"class": "footer-link"},
            },
        }
    )
    assert body_of(put) == {
        "script_url": "https://cmp.example/s.js",
        "settings_link": {
            "label": "Cookie settings",
            "preset": "cookiebot",
            "attributes": {"class": "footer-link"},
        },
    }
    link = out["settings_link"]
    assert link is not None
    assert link["preset"] == "cookiebot"
    assert link["rendered_attributes"]["data-cc"] == "c-settings"
    assert c.instance.cookie_consent.get()["settings_link"] == SETTINGS_LINK


@respx.mock
def test_cookie_consent_settings_link_cleared_with_none_and_unknown_preset_decodes() -> None:
    put = respx.put(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json={**CONSENT, "settings_link": None})
    )
    respx.delete(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(
            200,
            json={
                **CONSENT,
                "enabled": False,
                "settings_link": {**SETTINGS_LINK, "preset": "some_future_cmp"},
            },
        )
    )
    c = client()
    out = c.instance.cookie_consent.set(
        {"script_url": "https://cmp.example/s.js", "settings_link": None}
    )
    assert body_of(put) == {"script_url": "https://cmp.example/s.js", "settings_link": None}
    assert out["settings_link"] is None
    link = c.instance.cookie_consent.delete()["settings_link"]
    assert link is not None
    assert link["preset"] == "some_future_cmp"


# --------------------------------------------------------------------------- #
# Messaging provider delete                                                    #
# --------------------------------------------------------------------------- #


@respx.mock
def test_messaging_provider_delete_sends_no_query_by_default() -> None:
    route = respx.delete(f"{API_URL}/v1/messaging_providers/email").mock(
        return_value=httpx.Response(200, json=DELETED)
    )
    out = client().messaging_providers.delete("email")
    assert route.calls.last.request.url.query == b""
    assert out == DELETED


@respx.mock
def test_messaging_provider_delete_force() -> None:
    route = respx.delete(f"{API_URL}/v1/messaging_providers/email").mock(
        return_value=httpx.Response(200, json=DELETED)
    )
    out = client().messaging_providers.delete("email", force=True)
    assert route.calls.last.request.url.params["force"] == "true"
    assert out["deleted"] is True
    client().messaging_providers.delete("email", force=False)
    assert route.calls.last.request.url.query == b""


@respx.mock
def test_messaging_provider_delete_email_in_use_raises() -> None:
    respx.delete(f"{API_URL}/v1/messaging_providers/email").mock(
        return_value=httpx.Response(
            409,
            json={
                "errors": [
                    {
                        "code": "EMAIL_PROVIDER_IN_USE",
                        "message": "email is in use",
                        "meta": {"features": ["emailCode", "passwordReset"]},
                    }
                ]
            },
        )
    )
    with pytest.raises(AtlasError) as exc:
        client().messaging_providers.delete("email")
    assert exc.value.has_code(ErrorCode.EMAIL_PROVIDER_IN_USE)
    assert exc.value.errors[0]["meta"]["features"] == ["emailCode", "passwordReset"]


def test_email_provider_error_codes() -> None:
    assert ErrorCode.EMAIL_PROVIDER_IN_USE == "EMAIL_PROVIDER_IN_USE"
    assert ErrorCode.EMAIL_PROVIDER_REQUIRED == "EMAIL_PROVIDER_REQUIRED"


# --------------------------------------------------------------------------- #
# Sessions                                                                     #
# --------------------------------------------------------------------------- #

SESSION = {
    "object": "session",
    "id": "sess_1",
    "user_id": "user_1",
    "status": "active",
    "last_active_organization_id": "org_1",
    "impersonated_by": "user_admin",
    "last_active_at": 1,
    "expire_at": 3,
    "abandon_at": 2,
    "idle_expires_at": 2,
    "created_at": 0,
}


@respx.mock
def test_user_sessions_decode_idle_expiry_org_and_impersonator() -> None:
    respx.get(f"{API_URL}/v1/users/user_1/sessions").mock(
        return_value=httpx.Response(
            200, json={"object": "list", "data": [SESSION], "has_more": False}
        )
    )
    respx.get(f"{API_URL}/v1/sessions/sess_1").mock(return_value=httpx.Response(200, json=SESSION))
    c = client()
    item = c.users.list_sessions("user_1")["data"][0]
    assert item["idle_expires_at"] == item["abandon_at"] == 2
    assert item["last_active_organization_id"] == "org_1"
    assert item["impersonated_by"] == "user_admin"
    s = c.sessions.get("sess_1")
    assert s["idle_expires_at"] == 2


@respx.mock
async def test_async_skip_logout_settings_link_force_and_user_sessions() -> None:
    create = respx.post(f"{API_URL}/v1/oauth_clients").mock(
        return_value=httpx.Response(201, json=OAUTH_CLIENT)
    )
    put = respx.put(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json=CONSENT)
    )
    delete = respx.delete(f"{API_URL}/v1/messaging_providers/email").mock(
        return_value=httpx.Response(200, json=DELETED)
    )
    respx.get(f"{API_URL}/v1/users/user_1/sessions").mock(
        return_value=httpx.Response(
            200, json={"object": "list", "data": [SESSION], "has_more": False}
        )
    )
    async with AsyncAtlasClient(SECRET, base_url=API_URL) as atlas:
        out = await atlas.oauth_clients.create(
            {"name": "Dashboard", "redirect_uris": [], "skip_logout_confirmation": True}
        )
        assert body_of(create)["skip_logout_confirmation"] is True  # type: ignore[index]
        assert out["skip_logout_confirmation"] is True
        consent = await atlas.instance.cookie_consent.set(
            {
                "script_url": "https://cmp.example/s.js",
                "settings_link": {"label": "Cookie settings", "preset": "custom"},
            }
        )
        assert body_of(put)["settings_link"] == {  # type: ignore[index]
            "label": "Cookie settings",
            "preset": "custom",
        }
        assert consent["settings_link"] == SETTINGS_LINK
        await atlas.messaging_providers.delete("email")
        assert delete.calls.last.request.url.query == b""
        await atlas.messaging_providers.delete("email", force=True)
        assert delete.calls.last.request.url.params["force"] == "true"
        page = await atlas.users.list_sessions("user_1")
        assert page["data"][0]["idle_expires_at"] == 2


# --- captcha is bring-your-own-keys ---------------------------------------------


@respx.mock
def test_set_captcha_secret_for_a_provider_before_enabling() -> None:
    route = respx.put(f"{API_URL}/v1/instance/captcha_secret").mock(
        return_value=httpx.Response(200, json={"object": "captcha_secret", "provider": "turnstile", "set": True})
    )
    out = client().instance.set_captcha_secret({"secret": "s3cret", "provider": "turnstile"})
    assert json.loads(route.calls.last.request.content) == {"secret": "s3cret", "provider": "turnstile"}
    assert out["provider"] == "turnstile"


@respx.mock
def test_delete_captcha_secret_force_and_provider() -> None:
    route = respx.delete(f"{API_URL}/v1/instance/captcha_secret").mock(
        return_value=httpx.Response(
            200,
            json={"object": "captcha_secret", "provider": "hcaptcha", "deleted": True, "flows_turned_off": ["signUp"]},
        )
    )
    out = client().instance.delete_captcha_secret(provider="hcaptcha", force=True)
    params = route.calls.last.request.url.params
    assert params["provider"] == "hcaptcha" and params["force"] == "true"
    assert out["flows_turned_off"] == ["signUp"]
    client().instance.delete_captcha_secret()
    assert route.calls.last.request.url.query == b""


@respx.mock
def test_captcha_in_use_and_keys_required_codes() -> None:
    respx.delete(f"{API_URL}/v1/instance/captcha_secret").mock(
        return_value=httpx.Response(
            409, json={"errors": [{"code": "CAPTCHA_IN_USE", "message": "in use", "meta": {"flows": ["signUp"]}}]}
        )
    )
    with pytest.raises(AtlasError) as exc:
        client().instance.delete_captcha_secret()
    assert exc.value.has_code(ErrorCode.CAPTCHA_IN_USE)
    assert exc.value.errors[0]["meta"]["flows"] == ["signUp"]
    assert ErrorCode.CAPTCHA_KEYS_REQUIRED == "CAPTCHA_KEYS_REQUIRED"
