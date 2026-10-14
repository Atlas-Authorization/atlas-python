"""Request shapes for the newer surfaces: strict bodies, unknown-field reporting,
raw uploads, the platform client, design, cookie consent, messaging providers,
OAuth providers, webhooks, entitlements and org policy.

All HTTP is mocked with respx; each test asserts the method, path, query,
headers and body the SDK sends, and that the response decodes.
"""

from __future__ import annotations

import json
import logging

import httpx
import pytest
import respx

from atlas_backend import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasClient,
    AtlasError,
    AtlasPlatformClient,
    ErrorCode,
)

SECRET = "sk_test_placeholder"
PLATFORM_KEY = "psk_test_placeholder"
API_URL = "https://api.example.test"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 16


def client(**kw: object) -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL, **kw)  # type: ignore[arg-type]


def platform(**kw: object) -> AtlasPlatformClient:
    return AtlasPlatformClient(PLATFORM_KEY, base_url=API_URL, **kw)  # type: ignore[arg-type]


def body_of(route: respx.Route) -> object:
    return json.loads(route.calls.last.request.content)


# --------------------------------------------------------------------------- #
# Strict bodies (Atlas-Strict) and Atlas-Unknown-Fields                        #
# --------------------------------------------------------------------------- #


@respx.mock
def test_strict_client_sends_header_on_writes_only() -> None:
    post = respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(201, json={"id": "u"})
    )
    get = respx.get(f"{API_URL}/v1/users/u").mock(return_value=httpx.Response(200, json={}))
    delete = respx.delete(f"{API_URL}/v1/users/u").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    c = client(strict=True)
    c.users.create({"email_address": "a@b.co"})
    c.users.get("u")
    c.users.delete("u")

    assert post.calls.last.request.headers["atlas-strict"] == "true"
    assert delete.calls.last.request.headers["atlas-strict"] == "true"
    assert "atlas-strict" not in get.calls.last.request.headers


@respx.mock
def test_strict_defaults_to_no_header_and_false_opts_out() -> None:
    route = respx.patch(f"{API_URL}/v1/users/u").mock(return_value=httpx.Response(200, json={}))
    client().users.update("u", {"first_name": "A"})
    assert "atlas-strict" not in route.calls.last.request.headers

    client(strict=False).users.update("u", {"first_name": "A"})
    assert route.calls.last.request.headers["atlas-strict"] == "false"


@respx.mock
def test_with_options_overrides_strict_per_call_and_shares_connection() -> None:
    route = respx.post(f"{API_URL}/v1/roles").mock(return_value=httpx.Response(200, json={}))
    base = client()
    strict = base.with_options(strict=True)
    strict.roles.create({"key": "k", "name": "n"})
    assert route.calls.last.request.headers["atlas-strict"] == "true"

    base.roles.create({"key": "k", "name": "n"})
    assert "atlas-strict" not in route.calls.last.request.headers
    assert strict._http is base._http
    # Closing the copy must not close the shared connection.
    strict.close()
    base.roles.create({"key": "k", "name": "n"})

    lenient = client(strict=True).with_options(strict=False)
    lenient.roles.create({"key": "k", "name": "n"})
    assert route.calls.last.request.headers["atlas-strict"] == "false"


@respx.mock
def test_strict_refusal_surfaces_unknown_field_code() -> None:
    respx.patch(f"{API_URL}/v1/users/u").mock(
        return_value=httpx.Response(
            422,
            json={
                "errors": [
                    {
                        "code": "UNKNOWN_FIELD",
                        "message": "Unknown field nickname",
                        "param": "nickname",
                    }
                ]
            },
        )
    )
    with pytest.raises(AtlasError) as info:
        client(strict=True).users.update("u", {"first_name": "A"})
    assert info.value.status == 422
    assert info.value.has_code(ErrorCode.UNKNOWN_FIELD)
    assert info.value.errors[0]["param"] == "nickname"


@respx.mock
def test_unknown_fields_header_reaches_hook() -> None:
    respx.patch(f"{API_URL}/v1/users/u").mock(
        return_value=httpx.Response(
            200, json={"id": "u"}, headers={"Atlas-Unknown-Fields": "nickname, profile.age"}
        )
    )
    seen: list[tuple[list[str], str, str]] = []
    c = client(on_unknown_fields=lambda f, m, p: seen.append((f, m, p)))
    out = c.users.update("u", {"first_name": "A"})
    assert out["id"] == "u"
    assert seen == [(["nickname", "profile.age"], "PATCH", "/v1/users/u")]


@respx.mock
def test_unknown_fields_header_is_logged_without_a_hook(caplog: pytest.LogCaptureFixture) -> None:
    respx.post(f"{API_URL}/v1/permissions").mock(
        return_value=httpx.Response(200, json={}, headers={"Atlas-Unknown-Fields": "colour"})
    )
    with caplog.at_level(logging.WARNING, logger="atlas_backend"):
        client().permissions.create({"key": "a:b"})
    assert "colour" in caplog.text
    assert "/v1/permissions" in caplog.text


@respx.mock
async def test_async_strict_and_hook() -> None:
    route = respx.put(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json={}, headers={"Atlas-Unknown-Fields": "x"})
    )
    seen: list[list[str]] = []
    async with AsyncAtlasClient(
        SECRET, base_url=API_URL, strict=True, on_unknown_fields=lambda f, m, p: seen.append(f)
    ) as atlas:
        await atlas.instance.cookie_consent.set({"script_url": "https://cmp.example/s.js"})
        assert route.calls.last.request.headers["atlas-strict"] == "true"
        await atlas.with_options(strict=False).instance.cookie_consent.set(
            {"script_url": "https://cmp.example/s.js"}
        )
        assert route.calls.last.request.headers["atlas-strict"] == "false"
    assert seen == [["x"], ["x"]]


# --------------------------------------------------------------------------- #
# Raw uploads                                                                  #
# --------------------------------------------------------------------------- #


@respx.mock
def test_design_asset_upload_sends_raw_bytes_with_sniffed_type() -> None:
    route = respx.post(f"{API_URL}/v1/design/assets").mock(
        return_value=httpx.Response(
            201,
            json={
                "object": "design_asset",
                "asset_id": "dasset_1",
                "kind": "logo",
                "url": "https://cdn.example/a.webp",
                "width": 10,
                "height": 10,
                "dominant_color": None,
                "bytes": 99,
                "created_at": 1,
            },
        )
    )
    asset = client(strict=True).design.assets.upload(PNG, kind="logo")
    req = route.calls.last.request
    assert req.content == PNG
    assert req.headers["content-type"] == "image/png"
    assert req.url.params["kind"] == "logo"
    assert asset["asset_id"] == "dasset_1"

    client().design.assets.upload(JPEG)
    assert route.calls.last.request.headers["content-type"] == "image/jpeg"
    assert "kind" not in route.calls.last.request.url.params

    client().design.assets.upload(WEBP, content_type="image/webp", kind="background")
    assert route.calls.last.request.headers["content-type"] == "image/webp"


def test_upload_of_unknown_bytes_needs_a_content_type() -> None:
    with pytest.raises(ValueError, match="content_type"):
        client().design.assets.upload(b"not an image")


@respx.mock
def test_platform_design_asset_upload_and_delete() -> None:
    up = respx.post(f"{API_URL}/v1/platform/design/assets").mock(
        return_value=httpx.Response(201, json={"asset_id": "dasset_2"})
    )
    rm = respx.delete(f"{API_URL}/v1/platform/design/assets/dasset_2").mock(
        return_value=httpx.Response(200, json={"object": "design_asset", "deleted": True})
    )
    p = platform()
    p.design_assets.upload(PNG, kind="background")
    assert up.calls.last.request.headers["authorization"] == f"Bearer {PLATFORM_KEY}"
    assert up.calls.last.request.headers["content-type"] == "image/png"
    assert up.calls.last.request.url.params["kind"] == "background"
    assert p.design_assets.delete("dasset_2")["deleted"] is True
    assert rm.called


# --------------------------------------------------------------------------- #
# Sign in with Atlas apps (platform key)                                       #
# --------------------------------------------------------------------------- #


APP = {
    "object": "atlas_id_app",
    "id": "aia_1",
    "client_id": "cid_1",
    "name": "Demo",
    "redirect_uris": ["https://app.example/cb"],
    "post_logout_redirect_uris": ["https://app.example/bye"],
    "backchannel_logout_uri": "https://app.example/bcl",
    "backchannel_logout_session_required": True,
    "frontchannel_logout_uri": None,
    "frontchannel_logout_session_required": False,
    "allowed_scopes": ["openid", "email"],
    "type": "confidential",
    "created_at": 1,
    "updated_at": 2,
    "client_secret": "secret_once",
}


@respx.mock
def test_atlas_id_app_create_sends_logout_and_branding_fields() -> None:
    route = respx.post(f"{API_URL}/v1/platform/atlas_id_apps").mock(
        return_value=httpx.Response(200, json=APP)
    )
    app = platform(strict=True).atlas_id_apps.create(
        {
            "name": "Demo",
            "redirect_uris": ["https://app.example/cb"],
            "post_logout_redirect_uris": ["https://app.example/bye"],
            "backchannel_logout_uri": "https://app.example/bcl",
            "backchannel_logout_session_required": True,
            "frontchannel_logout_uri": None,
            "branding": {
                "theme": "dark",
                "accent_color": "#112233",
                "privacy_policy_url": "https://app.example/privacy",
                "copy": {"sign_in_title": "Welcome back"},
                "design": {"preset": "midnight"},
            },
        },
        idempotency_key="create-demo",
    )
    req = route.calls.last.request
    assert req.headers["authorization"] == f"Bearer {PLATFORM_KEY}"
    assert req.headers["idempotency-key"] == "create-demo"
    assert req.headers["atlas-strict"] == "true"
    sent = body_of(route)
    assert isinstance(sent, dict)
    assert sent["backchannel_logout_session_required"] is True
    assert sent["frontchannel_logout_uri"] is None
    assert sent["branding"]["copy"] == {"sign_in_title": "Welcome back"}
    assert app["client_secret"] == "secret_once"


@respx.mock
def test_atlas_id_app_list_update_rotate_delete_preview() -> None:
    respx.get(f"{API_URL}/v1/platform/atlas_id_apps").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "list",
                "data": [APP],
                "issuer": "https://atlasauth.net",
                "discovery_url": "https://atlasauth.net/.well-known/openid-configuration",
                "limit": 25,
            },
        )
    )
    patch = respx.patch(f"{API_URL}/v1/platform/atlas_id_apps/aia_1").mock(
        return_value=httpx.Response(200, json=APP)
    )
    rotate = respx.post(f"{API_URL}/v1/platform/atlas_id_apps/aia_1/rotate_secret").mock(
        return_value=httpx.Response(200, json=APP)
    )
    delete = respx.delete(f"{API_URL}/v1/platform/atlas_id_apps/aia_1").mock(
        return_value=httpx.Response(
            200, json={"object": "atlas_id_app", "id": "aia_1", "deleted": True}
        )
    )
    preview = respx.post(f"{API_URL}/v1/platform/atlas_id_apps/design/preview").mock(
        return_value=httpx.Response(200, json={"object": "design_preview", "html": "<html/>"})
    )
    p = platform()
    listing = p.atlas_id_apps.list()
    assert listing["issuer"] == "https://atlasauth.net"
    assert listing["data"][0]["client_id"] == "cid_1"

    p.atlas_id_apps.update(
        "aia_1", {"branding": None, "frontchannel_logout_session_required": True}
    )
    assert body_of(patch) == {"branding": None, "frontchannel_logout_session_required": True}
    assert p.atlas_id_apps.rotate_secret("aia_1")["client_secret"] == "secret_once"
    assert rotate.called
    assert p.atlas_id_apps.delete("aia_1")["deleted"] is True
    assert delete.called
    out = p.atlas_id_apps.preview_design({"design": {"preset": "glass"}})
    assert body_of(preview) == {"design": {"preset": "glass"}}
    assert out["html"] == "<html/>"


@respx.mock
async def test_async_platform_client_apps() -> None:
    route = respx.get(f"{API_URL}/v1/platform/apps").mock(
        return_value=httpx.Response(200, json={"object": "list", "data": []})
    )
    async with AsyncAtlasPlatformClient(PLATFORM_KEY, base_url=API_URL) as p:
        await p.apps.list(tag="prod", include_archived=True)
    req = route.calls.last.request
    assert req.headers["authorization"] == f"Bearer {PLATFORM_KEY}"
    assert req.url.params["tag"] == "prod"
    assert req.url.params["include_archived"] == "true"


def test_platform_client_requires_a_key() -> None:
    with pytest.raises(ValueError):
        AtlasPlatformClient("")


# --------------------------------------------------------------------------- #
# Preflight, design, cookie consent                                            #
# --------------------------------------------------------------------------- #


@respx.mock
def test_preflight_decodes_typed_findings() -> None:
    respx.get(f"{API_URL}/v1/instance/preflight").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "preflight",
                "ok": False,
                "checked_at": 1700000000000,
                "findings": [
                    {
                        "severity": "error",
                        "code": "oauth_provider_missing_credentials",
                        "message": "Google is on but has no client id.",
                        "fix": "Add the client id and secret.",
                        "subject": {"provider": "google"},
                    }
                ],
            },
        )
    )
    report = client().instance.preflight()
    assert report["ok"] is False
    finding = report["findings"][0]
    assert finding["severity"] == "error"
    assert finding["subject"] == {"provider": "google"}


@respx.mock
def test_instance_and_org_design_routes() -> None:
    settings = {"object": "design_settings", "design": {"preset": "atlas"}}
    get = respx.get(f"{API_URL}/v1/instance/design").mock(
        return_value=httpx.Response(200, json=settings)
    )
    put = respx.put(f"{API_URL}/v1/instance/design").mock(
        return_value=httpx.Response(200, json=settings)
    )
    patch = respx.patch(f"{API_URL}/v1/instance/design").mock(
        return_value=httpx.Response(200, json=settings)
    )
    preview = respx.post(f"{API_URL}/v1/instance/design/preview").mock(
        return_value=httpx.Response(200, json={"object": "design_preview"})
    )
    org_patch = respx.patch(f"{API_URL}/v1/organizations/org_1/design").mock(
        return_value=httpx.Response(200, json=settings)
    )
    catalog = respx.get(f"{API_URL}/v1/design/catalog").mock(
        return_value=httpx.Response(200, json={"presets": []})
    )
    c = client()
    assert c.design.get()["design"] == {"preset": "atlas"}
    c.design.replace({"design": {"version": 1, "preset": "glass", "colorScheme": "dark"}})
    assert body_of(put) == {"design": {"version": 1, "preset": "glass", "colorScheme": "dark"}}
    c.design.update({"design": {"palette": {"primary": "#ff0000", "accent": None}}})
    assert body_of(patch) == {"design": {"palette": {"primary": "#ff0000", "accent": None}}}
    c.design.preview({"design": {"preset": "bold"}})
    assert preview.called
    c.organizations.design.update("org_1", {"design": {"preset": "forest"}})
    assert body_of(org_patch) == {"design": {"preset": "forest"}}
    assert c.design.catalog() == {"presets": []}
    assert get.called and catalog.called


@respx.mock
def test_cookie_consent_get_set_delete() -> None:
    state = {
        "object": "cookie_consent",
        "enabled": True,
        "script_url": "https://cmp.example/s.js",
        "script_id": None,
        "site_id": "site_1",
        "blocking_mode": "auto",
        "extra_origins": [],
    }
    respx.get(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json=state)
    )
    put = respx.put(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json=state)
    )
    respx.delete(f"{API_URL}/v1/instance/cookie_consent").mock(
        return_value=httpx.Response(200, json={**state, "enabled": False})
    )
    c = client()
    assert c.instance.cookie_consent.get()["site_id"] == "site_1"
    c.instance.cookie_consent.set(
        {"script_url": "https://cmp.example/s.js", "site_id": "site_1", "extra_origins": []}
    )
    assert body_of(put) == {
        "script_url": "https://cmp.example/s.js",
        "site_id": "site_1",
        "extra_origins": [],
    }
    assert c.instance.cookie_consent.delete()["enabled"] is False


# --------------------------------------------------------------------------- #
# Messaging providers, OAuth providers                                         #
# --------------------------------------------------------------------------- #


@respx.mock
def test_messaging_provider_typed_bodies() -> None:
    email = respx.put(f"{API_URL}/v1/messaging_providers/email").mock(
        return_value=httpx.Response(200, json={"object": "messaging_provider", "channel": "email"})
    )
    sms = respx.put(f"{API_URL}/v1/messaging_providers/sms").mock(
        return_value=httpx.Response(200, json={"object": "messaging_provider", "channel": "sms"})
    )
    test = respx.post(f"{API_URL}/v1/messaging_providers/email/test").mock(
        return_value=httpx.Response(200, json={"object": "messaging_test", "ok": True})
    )
    c = client()
    c.messaging_providers.set_email(
        {
            "transport": "smtp",
            "from_address": "Acme <no-reply@acme.test>",
            "config": {"host": "smtp.acme.test", "port": 587, "username": "u", "password": "p"},
        }
    )
    assert body_of(email)["transport"] == "smtp"  # type: ignore[index]
    c.messaging_providers.set_sms(
        {"transport": "twilio", "config": {"account_sid": "AC1", "auth_token": "t"}}
    )
    assert body_of(sms)["transport"] == "twilio"  # type: ignore[index]
    c.messaging_providers.test("email", {"to": "ops@acme.test"})
    assert body_of(test) == {"to": "ops@acme.test"}


@respx.mock
def test_oauth_provider_list_filters_and_upsert_clearing() -> None:
    lst = respx.get(f"{API_URL}/v1/oauth_providers").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "object": "oauth_provider",
                        "provider": "siwe",
                        "display_name": "Ethereum",
                        "configured": True,
                        "enabled": True,
                        "allow_sign_in": True,
                        "allow_sign_up": True,
                        "icon_url": None,
                        "mode": "redirect",
                        "setting_values": {"domain": "app.example.com"},
                    }
                ],
                "has_more": False,
            },
        )
    )
    put = respx.put(f"{API_URL}/v1/oauth_providers/siwe").mock(
        return_value=httpx.Response(200, json={"object": "oauth_provider", "provider": "siwe"})
    )
    c = client()
    page = c.oauth_providers.list(provider=["google", "siwe"], configured=True)
    params = lst.calls.last.request.url.params
    assert params["provider"] == "google,siwe"
    assert params["configured"] == "true"
    assert page["data"][0]["setting_values"] == {"domain": "app.example.com"}

    c.oauth_providers.upsert(
        "siwe",
        {
            "settings": {"domain": "app.example.com", "chain_ids": [1, 10], "rpc_url": None},
            "display_name": "Ethereum",
            "icon_url": None,
            "mode": None,
        },
    )
    assert body_of(put) == {
        "settings": {"domain": "app.example.com", "chain_ids": [1, 10], "rpc_url": None},
        "display_name": "Ethereum",
        "icon_url": None,
        "mode": None,
    }


# --------------------------------------------------------------------------- #
# Webhooks                                                                     #
# --------------------------------------------------------------------------- #


@respx.mock
def test_webhook_endpoint_lifecycle() -> None:
    base = f"{API_URL}/v1/webhook_endpoints/we_1"
    patch = respx.patch(base).mock(return_value=httpx.Response(200, json={"id": "we_1"}))
    reveal = respx.post(f"{base}/reveal_secret").mock(
        return_value=httpx.Response(200, json={"object": "webhook_secret", "secret": "whsec_1"})
    )
    rotate = respx.post(f"{base}/rotate_secret").mock(
        return_value=httpx.Response(200, json={"secret": "whsec_2"})
    )
    test = respx.post(f"{base}/test").mock(
        return_value=httpx.Response(200, json={"status": "queued"})
    )
    deliveries = respx.get(f"{base}/deliveries").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )
    redeliver = respx.post(f"{base}/deliveries/whd_9/redeliver").mock(
        return_value=httpx.Response(200, json={"status": "queued"})
    )
    ep = client().webhooks.endpoints
    ep.update("we_1", {"enabled_events": ["user.created"], "active": False})
    assert body_of(patch) == {"enabled_events": ["user.created"], "active": False}
    assert ep.reveal_secret("we_1")["secret"] == "whsec_1"
    assert ep.rotate_secret("we_1")["secret"] == "whsec_2"
    ep.test("we_1")
    ep.list_deliveries("we_1", limit=5)
    assert deliveries.calls.last.request.url.params["limit"] == "5"
    ep.redeliver("we_1", "whd_9")
    assert all(r.called for r in (reveal, rotate, test, redeliver))


# --------------------------------------------------------------------------- #
# Entitlements, org policy                                                     #
# --------------------------------------------------------------------------- #


@respx.mock
def test_entitlement_overrides_and_org_entitlements() -> None:
    create = respx.post(f"{API_URL}/v1/entitlement_overrides").mock(
        return_value=httpx.Response(200, json={"id": "eo_1"})
    )
    lst = respx.get(f"{API_URL}/v1/entitlement_overrides").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )
    rm = respx.delete(f"{API_URL}/v1/entitlement_overrides/eo_1").mock(
        return_value=httpx.Response(
            200, json={"object": "entitlement_override", "id": "eo_1", "deleted": True}
        )
    )
    ent = respx.get(f"{API_URL}/v1/organizations/org_1/entitlements").mock(
        return_value=httpx.Response(200, json={"plan": "pro", "features": [], "limits": {}})
    )
    c = client()
    c.entitlement_overrides.create(
        {"subject_type": "org", "subject_id": "org_1", "limits": {"seats": -1}},
        idempotency_key="eo-1",
    )
    assert body_of(create) == {
        "subject_type": "org",
        "subject_id": "org_1",
        "limits": {"seats": -1},
    }
    assert create.calls.last.request.headers["idempotency-key"] == "eo-1"
    c.entitlement_overrides.list(subject_type="org", subject_id="org_1")
    assert dict(lst.calls.last.request.url.params) == {"subject_type": "org", "subject_id": "org_1"}
    assert c.entitlement_overrides.delete("eo_1")["deleted"] is True
    assert c.organizations.get_entitlements("org_1")["plan"] == "pro"
    assert rm.called and ent.called


@respx.mock
def test_org_policy_patch_sends_typed_fields_nulls_and_extra_keys() -> None:
    route = respx.patch(f"{API_URL}/v1/organizations/org_1/policy").mock(
        return_value=httpx.Response(200, json={"object": "organization_policy", "policy": {}})
    )
    c = client()
    c.organizations.update_policy(
        "org_1",
        {
            "requireMfa": True,
            "allowedSignInMethods": ["password", "oauth:google"],
            "ipAllowlist": None,
            "maxSessionAgeSeconds": 3600,
            "endUserPool": {"enabled": True, "requireApproval": False},
        },
    )
    assert body_of(route) == {
        "requireMfa": True,
        "allowedSignInMethods": ["password", "oauth:google"],
        "ipAllowlist": None,
        "maxSessionAgeSeconds": 3600,
        "endUserPool": {"enabled": True, "requireApproval": False},
    }
    # A field this release does not know yet still goes through as a plain dict.
    c.organizations.update_policy("org_1", {"futureSetting": 1})
    assert body_of(route) == {"futureSetting": 1}


# --------------------------------------------------------------------------- #
# Query helpers, cursor lists, extended legacy methods                         #
# --------------------------------------------------------------------------- #


@respx.mock
def test_csv_and_json_query_filters() -> None:
    audit = respx.get(f"{API_URL}/v1/audit_events").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False, "next_cursor": None})
    )
    machines = respx.get(f"{API_URL}/v1/machines").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False, "next_cursor": None})
    )
    c = client()
    c.audit_events.list(
        action=["doc.read", "doc.write"], from_=1700000000000, any_of=True, limit=10
    )
    params = audit.calls.last.request.url.params
    assert params["action"] == "doc.read,doc.write"
    assert params["from"] == "1700000000000"
    assert params["any_of"] == "true"
    assert params["limit"] == "10"
    c.machines.list(metadata={"site": "lab"}, status="active")
    params = machines.calls.last.request.url.params
    assert json.loads(params["metadata"]) == {"site": "lab"}
    assert params["status"] == "active"


@respx.mock
def test_extended_legacy_methods_send_new_options() -> None:
    ban = respx.post(f"{API_URL}/v1/users/u/ban").mock(return_value=httpx.Response(200, json={}))
    revoke = respx.post(f"{API_URL}/v1/users/u/sessions/revoke").mock(
        return_value=httpx.Response(200, json={})
    )
    role_del = respx.delete(f"{API_URL}/v1/roles/r1").mock(
        return_value=httpx.Response(200, json={})
    )
    get = respx.get(f"{API_URL}/v1/users/u").mock(return_value=httpx.Response(200, json={}))
    c = client()
    c.users.ban("u")
    assert ban.calls.last.request.content == b""
    c.users.ban("u", reason="spam", note="ticket 9")
    assert body_of(ban) == {"reason": "spam", "note": "ticket 9"}
    c.users.revoke_sessions("u", all=True, revoke_grants=True)
    assert body_of(revoke) == {"all": True, "revoke_grants": True}
    c.roles.delete("r1", reassign_to="r2")
    assert role_del.calls.last.request.url.params["reassign_to"] == "r2"
    c.users.get("u", include_deleted=True)
    assert get.calls.last.request.url.params["include_deleted"] == "true"


@respx.mock
def test_export_returns_raw_text() -> None:
    respx.get(f"{API_URL}/v1/audit_events/export").mock(
        return_value=httpx.Response(200, text='{"id":"e1"}\n{"id":"e2"}\n')
    )
    out = client().audit_events.export(format="jsonl")
    assert out.splitlines() == ['{"id":"e1"}', '{"id":"e2"}']
