"""Billing add-ons / settings / checks, custom OAuth providers, the Actions gallery,
session custom data, sign-in settings, SAML SLO + encryption keys, dormant accounts,
token formats / lifetimes, KMS signing keys, opaque-token introspection, device
approval and BotID attestations.

HTTP is mocked with respx.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token

from atlas_backend import (
    BOTID_ATTESTATION_PREFIX,
    CAPTCHA_PROVIDERS,
    WEBHOOK_EVENT_SESSION_UPDATED,
    WEBHOOK_EVENT_USER_REACTIVATED,
    AccessTokenVerifier,
    AsyncAtlasClient,
    AsyncDeviceAuthorizations,
    AtlasClient,
    DeviceAuthorizationError,
    DeviceAuthorizations,
    IntrospectionOptions,
    Introspector,
    create_botid_attestation,
    format_user_code,
    user_code_from_url,
)

SECRET = "sk_test_placeholder"
API_URL = "https://api.example.test"
OK: dict[str, Any] = {"object": "x", "id": "x_1", "data": [], "has_more": False}


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


def body_of(route: respx.Route) -> Any:
    content = route.calls.last.request.content
    return json.loads(content) if content else None


def _run(calls: list[tuple[str, str, Any]]) -> list[respx.Route]:
    routes = []
    for method, path, call in calls:
        route = respx.request(method, f"{API_URL}{path}").mock(
            return_value=httpx.Response(200, json=OK)
        )
        call()
        assert route.called, (method, path)
        routes.append(route)
    return routes


@respx.mock
def test_billing_surface() -> None:
    c = client()
    routes = _run(
        [
            (
                "GET",
                "/v1/billing/subscriptions/bsub_1",
                lambda: c.billing.subscriptions.get("bsub_1"),
            ),
            (
                "POST",
                "/v1/billing/plans/bp_1/sync_entitlements",
                lambda: c.billing.plans.sync_entitlements("bp_1"),
            ),
            ("GET", "/v1/billing/settings", lambda: c.billing.get_settings()),
            (
                "PUT",
                "/v1/billing/settings",
                lambda: c.billing.update_settings(
                    {"default_limit_merge": "sum", "limit_merge": {"seats": "max"}}
                ),
            ),
            (
                "POST",
                "/v1/billing/check",
                lambda: c.billing.check_feature(
                    {"subject_type": "org", "subject_id": "org_1", "feature": "api", "required": 2}
                ),
            ),
            (
                "POST",
                "/v1/billing/usage",
                lambda: c.billing.record_usage(
                    {
                        "subject_type": "user",
                        "subject_id": "u_1",
                        "quantity": 1,
                        "idempotency_key": "k",
                        "feature": "api",
                        "subscription_id": "bsub_2",
                    }
                ),
            ),
            (
                "PATCH",
                "/v1/billing/plans/bp_1",
                lambda: c.billing.plans.update("bp_1", {"kind": "addon", "seat_feature_id": None}),
            ),
        ]
    )
    assert body_of(routes[3]) == {"default_limit_merge": "sum", "limit_merge": {"seats": "max"}}
    assert body_of(routes[4])["required"] == 2
    assert body_of(routes[5])["subscription_id"] == "bsub_2"
    assert body_of(routes[6]) == {"kind": "addon", "seat_feature_id": None}


@respx.mock
def test_custom_oauth_providers_and_sso_rp() -> None:
    c = client()
    mapping = {
        "fields": {"email": "mail", "first_name": {"from": ["given_name"], "transforms": ["trim"]}}
    }
    routes = _run(
        [
            ("GET", "/v1/custom_oauth_providers", lambda: c.custom_oauth_providers.list()),
            (
                "POST",
                "/v1/custom_oauth_providers",
                lambda: c.custom_oauth_providers.create(
                    {
                        "provider_key": "custom_acme",
                        "display_name": "Acme",
                        "issuer": "https://idp.test",
                        "token_endpoint_auth_method": "private_key_jwt",
                        "profile_mapping": mapping,
                    }
                ),
            ),
            (
                "GET",
                "/v1/custom_oauth_providers/coap_1",
                lambda: c.custom_oauth_providers.get("coap_1"),
            ),
            (
                "PATCH",
                "/v1/custom_oauth_providers/coap_1",
                lambda: c.custom_oauth_providers.update("coap_1", {"icon_url": None}),
            ),
            (
                "DELETE",
                "/v1/custom_oauth_providers/coap_1",
                lambda: c.custom_oauth_providers.delete("coap_1"),
            ),
            (
                "POST",
                "/v1/custom_oauth_providers/discover",
                lambda: c.custom_oauth_providers.discover("https://idp.test"),
            ),
            (
                "POST",
                "/v1/custom_oauth_providers/profile_mapping/preview",
                lambda: c.custom_oauth_providers.preview_profile_mapping(
                    {"userinfo": {"mail": "a"}}
                ),
            ),
            (
                "POST",
                "/v1/custom_oauth_providers/coap_1/profile_mapping/preview",
                lambda: c.custom_oauth_providers.preview_provider_profile_mapping(
                    "coap_1", {"id_token": "a.b.c"}
                ),
            ),
            (
                "GET",
                "/v1/custom_oauth_providers/coap_1/signing_keys",
                lambda: c.custom_oauth_providers.list_signing_keys("coap_1"),
            ),
            (
                "POST",
                "/v1/custom_oauth_providers/coap_1/signing_keys",
                lambda: c.custom_oauth_providers.rotate_signing_key("coap_1", alg="PS256"),
            ),
            (
                "POST",
                "/v1/custom_oauth_providers/coap_1/signing_keys/k1/retire",
                lambda: c.custom_oauth_providers.retire_signing_key("coap_1", "k1"),
            ),
            (
                "POST",
                "/v1/sso_connections/sso_1/profile_mapping/preview",
                lambda: c.sso_connections.preview_profile_mapping("sso_1", {"userinfo": {}}),
            ),
            (
                "GET",
                "/v1/sso_connections/sso_1/signing_keys",
                lambda: c.sso_connections.list_signing_keys("sso_1"),
            ),
            (
                "POST",
                "/v1/sso_connections/sso_1/signing_keys",
                lambda: c.sso_connections.rotate_signing_key("sso_1"),
            ),
            (
                "POST",
                "/v1/sso_connections/sso_1/signing_keys/k2/retire",
                lambda: c.sso_connections.retire_signing_key("sso_1", "k2"),
            ),
            (
                "GET",
                "/v1/sso_connections/sso_1/saml_encryption_key",
                lambda: c.sso_connections.get_saml_encryption_key("sso_1"),
            ),
            (
                "POST",
                "/v1/sso_connections/sso_1/saml_encryption_key",
                lambda: c.sso_connections.create_saml_encryption_key("sso_1"),
            ),
            (
                "DELETE",
                "/v1/sso_connections/sso_1/saml_encryption_key/previous",
                lambda: c.sso_connections.retire_previous_saml_encryption_key("sso_1"),
            ),
            (
                "DELETE",
                "/v1/sso_connections/sso_1/saml_encryption_key",
                lambda: c.sso_connections.delete_saml_encryption_key("sso_1"),
            ),
            (
                "PATCH",
                "/v1/sso_connections/sso_1",
                lambda: c.sso_connections.update(
                    "sso_1",
                    {
                        "saml_single_logout": True,
                        "saml_idp_slo_soap_url": "https://idp.test/soap",
                        "saml_require_encrypted_assertions": True,
                        "saml_idp_slo_response_url": None,
                    },
                ),
            ),
        ]
    )
    assert body_of(routes[1])["profile_mapping"] == mapping
    assert body_of(routes[3]) == {"icon_url": None}
    assert body_of(routes[5]) == {"issuer": "https://idp.test"}
    assert body_of(routes[9]) == {"alg": "PS256"}
    assert body_of(routes[13]) == {}
    assert body_of(routes[19])["saml_idp_slo_soap_url"] == "https://idp.test/soap"


@respx.mock
def test_action_gallery_surface() -> None:
    c = client()
    routes = _run(
        [
            ("GET", "/v1/action_gallery", lambda: c.action_gallery.list(q="geo", source="builtin")),
            ("GET", "/v1/action_gallery/geo-fence", lambda: c.action_gallery.get("geo-fence")),
            (
                "POST",
                "/v1/action_gallery/geo-fence/install",
                lambda: c.action_gallery.install("geo-fence", {"secrets": {"K": "v"}}),
            ),
            ("GET", "/v1/action_gallery_installs", lambda: c.action_gallery.installs()),
            ("POST", "/v1/actions/act_1/gallery_update", lambda: c.action_gallery.update("act_1")),
            ("GET", "/v1/action_templates", lambda: c.action_templates.list()),
            (
                "POST",
                "/v1/action_templates",
                lambda: c.action_templates.create(
                    {"slug": "mine", "name": "Mine", "author_name": "Me", "trigger": "post_login"}
                ),
            ),
            ("GET", "/v1/action_templates/atpl_1", lambda: c.action_templates.get("atpl_1")),
            (
                "PATCH",
                "/v1/action_templates/atpl_1",
                lambda: c.action_templates.update("atpl_1", {"summary": "s"}),
            ),
            ("DELETE", "/v1/action_templates/atpl_1", lambda: c.action_templates.delete("atpl_1")),
            (
                "POST",
                "/v1/action_templates/atpl_1/versions",
                lambda: c.action_templates.add_version("atpl_1", {"version": "1.0.0", "code": "x"}),
            ),
            (
                "POST",
                "/v1/action_templates/atpl_1/versions/1.0.0/submit",
                lambda: c.action_templates.submit_version("atpl_1", "1.0.0"),
            ),
            (
                "DELETE",
                "/v1/action_templates/atpl_1/versions/1.0.0",
                lambda: c.action_templates.delete_version("atpl_1", "1.0.0"),
            ),
            (
                "POST",
                "/v1/action_templates/atpl_1/publish",
                lambda: c.action_templates.publish("atpl_1"),
            ),
            (
                "POST",
                "/v1/action_templates/atpl_1/unlist",
                lambda: c.action_templates.unlist("atpl_1"),
            ),
        ]
    )
    assert parse_qs(routes[0].calls.last.request.url.query.decode()) == {
        "q": ["geo"],
        "source": ["builtin"],
    }
    assert body_of(routes[2]) == {"secrets": {"K": "v"}}
    assert body_of(routes[4]) == {}


@respx.mock
def test_sign_in_items_and_enterprise_and_op() -> None:
    c = client()
    routes = _run(
        [
            (
                "PUT",
                "/v1/sessions/sess_1/custom_data",
                lambda: c.sessions.set_custom_data("sess_1", None),
            ),
            (
                "PATCH",
                "/v1/sessions/sess_1/custom_data",
                lambda: c.sessions.update_custom_data("sess_1", {"plan": None, "seat": 2}),
            ),
            (
                "PUT",
                "/v1/instance/wallet_rpc_secret",
                lambda: c.instance.security.set_wallet_rpc_secret(
                    chain_id=1, url="https://rpc.test"
                ),
            ),
            (
                "PATCH",
                "/v1/rate_limit_policy",
                lambda: c.rate_limit_policy.update(
                    {
                        "rules": [
                            {"group": "fapi.sign_in", "window_seconds": 60, "max": 5, "key": "ip"}
                        ]
                    }
                ),
            ),
            (
                "PATCH",
                "/v1/instance",
                lambda: c.instance.set_account_linking_trust({"google": "always", "*": "verified"}),
            ),
            (
                "GET",
                "/v1/instance/signing_key_provider",
                lambda: c.instance.security.get_signing_key_provider(),
            ),
            (
                "PUT",
                "/v1/instance/signing_key_provider",
                lambda: c.instance.security.set_signing_key_provider(
                    {
                        "provider": "gcp_kms",
                        "config": {"crypto_key": "projects/p/locations/l/keyRings/r/cryptoKeys/k"},
                        "credentials": {"service_account_json": "{}"},
                    }
                ),
            ),
            (
                "DELETE",
                "/v1/instance/signing_key_provider",
                lambda: c.instance.security.remove_signing_key_provider({"emergency": True}),
            ),
            (
                "PATCH",
                "/v1/attack_protection",
                lambda: c.attack_protection.update(
                    {"dormant_accounts": {"enabled": True, "threshold_days": 120}}
                ),
            ),
            (
                "PATCH",
                "/v1/resource_servers/rs_1",
                lambda: c.resource_servers.update(
                    "rs_1",
                    {"access_token_format": "opaque", "introspection_client_ids": ["oc_api"]},
                ),
            ),
            (
                "PATCH",
                "/v1/oauth_clients/oc_1",
                lambda: c.oauth_clients.update(
                    "oc_1",
                    {
                        "access_token_format": None,
                        "token_lifetimes": {"access_token_ttl_seconds": 600},
                    },
                ),
            ),
        ]
    )
    assert body_of(routes[0]) == {"custom_data": None}
    assert body_of(routes[1]) == {"custom_data": {"plan": None, "seat": 2}}
    assert body_of(routes[2]) == {"chain_id": 1, "url": "https://rpc.test"}
    assert body_of(routes[3])["rules"][0]["window_seconds"] == 60
    assert body_of(routes[4]) == {
        "auth_config": {"accountLinkingTrust": {"google": "always", "*": "verified"}}
    }
    assert body_of(routes[6])["provider"] == "gcp_kms"
    assert body_of(routes[7]) == {"emergency": True}
    assert body_of(routes[8])["dormant_accounts"]["threshold_days"] == 120
    assert body_of(routes[10])["access_token_format"] is None
    assert "captchafox" in CAPTCHA_PROVIDERS and "vercel_botid" in CAPTCHA_PROVIDERS
    assert WEBHOOK_EVENT_SESSION_UPDATED == "session.updated"
    assert WEBHOOK_EVENT_USER_REACTIVATED == "user.reactivated"


@respx.mock
async def test_async_client_mirrors_new_namespaces() -> None:
    route = respx.get(f"{API_URL}/v1/custom_oauth_providers/coap_1/signing_keys").mock(
        return_value=httpx.Response(200, json=OK)
    )
    gal = respx.get(f"{API_URL}/v1/action_gallery_installs").mock(
        return_value=httpx.Response(200, json=OK)
    )
    async with AsyncAtlasClient(SECRET, base_url=API_URL) as c:
        await c.custom_oauth_providers.list_signing_keys("coap_1")
        await c.action_gallery.installs()
    assert route.called and gal.called


def test_botid_attestation() -> None:
    secret = "k" * 32
    tok = create_botid_attestation(secret, is_bot=False, ttl_seconds=3600, now=1_800_000_000)
    assert tok.startswith(BOTID_ATTESTATION_PREFIX)
    payload, sig = tok[len(BOTID_ATTESTATION_PREFIX) :].rsplit(".", 1)
    expect = hmac.new(
        secret.encode(), (BOTID_ATTESTATION_PREFIX + payload).encode(), hashlib.sha256
    ).digest()
    assert sig == base64.urlsafe_b64encode(expect).rstrip(b"=").decode()
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assert data["v"] == 1 and data["is_bot"] is False and data["verified_bot"] is False
    assert data["iat"] == 1_800_000_000 and data["exp"] - data["iat"] == 300
    assert len(data["jti"]) >= 20
    with pytest.raises(ValueError):
        create_botid_attestation("short", is_bot=False)


def test_device_authorizations() -> None:
    seen: list[httpx.Request] = []
    status = {"code": 200}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if status["code"] != 200:
            return httpx.Response(
                403, json={"errors": [{"code": "STEP_UP_REQUIRED", "message": "Re-authenticate."}]}
            )
        return httpx.Response(
            200,
            json={
                "object": "device_authorization",
                "id": "da_1",
                "user_code": "WDJB-MJHT",
                "status": "pending",
                "client": {"client_id": "oc_tv", "name": "TV", "first_party": True},
                "scopes": [],
                "requires_step_up": True,
            },
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))
    d = DeviceAuthorizations(
        "https://fapi.test/", "sess_jwt", publishable_key="pk_x", http_client=http
    )
    auth = d.lookup(" wdjb mjht ")
    req = seen[-1]
    assert req.url.path == "/v1/client/me/device_authorizations/lookup"
    assert (
        req.headers["authorization"] == "Bearer sess_jwt"
        and req.headers["x-publishable-key"] == "pk_x"
    )
    assert json.loads(req.content) == {"user_code": "WDJB-MJHT"}
    assert auth["client"]["name"] == "TV"
    d.approve(auth)
    assert seen[-1].url.path == "/v1/client/me/device_authorizations/da_1/approve"
    d.deny(auth)
    assert seen[-1].url.path == "/v1/client/me/device_authorizations/da_1/deny"
    status["code"] = 403
    with pytest.raises(DeviceAuthorizationError) as err:
        d.approve(auth)
    assert (
        err.value.needs_reverification and err.value.status == 403 and not err.value.is_invalid_code
    )
    assert format_user_code("abc") == "abc" and format_user_code("wdjbmjht") == "WDJB-MJHT"
    assert user_code_from_url("https://x.test/d?user_code=wdjbmjht") == "WDJB-MJHT"
    assert user_code_from_url("nope") is None


def test_access_token_introspection() -> None:
    now_ms = int(time.time() * 1000)
    calls: list[httpx.Request] = []
    state = {"active": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/jwks"):
            return httpx.Response(200, json=jwks_document())
        calls.append(request)
        form = parse_qs(request.content.decode())
        token = form["token"][0]
        if token == "oat_down":
            return httpx.Response(500)
        if not state["active"] or token == "oat_dead":
            return httpx.Response(200, json={"active": False})
        iss = "https://other.test" if token == "oat_foreign" else ISSUER
        return httpx.Response(
            200,
            json={
                "active": True,
                "iss": iss,
                "sub": "u_1",
                "aud": "https://api.test",
                "scope": "read",
                "client_id": "oc_1",
                "exp": now_ms // 1000 + 3600,
            },
        )

    http = httpx.Client(transport=httpx.MockTransport(handler))
    v = AccessTokenVerifier(
        issuer=ISSUER,
        audience="https://api.test",
        jwks_url=JWKS_URL,
        introspection=IntrospectionOptions(
            client_id="oc_api", client_secret="s3cret", endpoint="https://iss.test/introspect"
        ),
        http_client=http,
    )
    ok = v.verify("Bearer oat_live", required_scopes=["read"])
    assert ok.ok and ok.subject == "u_1" and ok.client_id == "oc_1"
    req = calls[-1]
    assert req.headers["authorization"] == "Basic " + base64.b64encode(b"oc_api:s3cret").decode()
    assert parse_qs(req.content.decode())["token_type_hint"] == ["access_token"]
    v.verify("Bearer oat_live")
    assert len(calls) == 1  # cached
    assert v.verify("Bearer oat_live", required_scopes=["admin"]).status == 403
    assert not v.verify("Bearer oat_dead").ok
    n = len(calls)
    v.verify("Bearer oat_dead")
    assert len(calls) == n  # negative answer cached
    foreign = v.verify("Bearer oat_foreign")
    assert not foreign.ok and "another authorization server" in foreign.description
    down = v.verify("Bearer oat_down")
    assert not down.ok and "could not be validated" in down.description

    plain = AccessTokenVerifier(issuer=ISSUER, audience="https://api.test", jwks_url=JWKS_URL)
    refused = plain.verify("Bearer oat_live")
    assert not refused.ok and "introspection" in refused.description

    live = AccessTokenVerifier(
        issuer=ISSUER,
        audience="https://api.test",
        jwks_url=JWKS_URL,
        introspection=IntrospectionOptions(
            client_id="oc_api",
            client_secret="s3cret",
            endpoint="https://iss.test/introspect",
            introspect_jwts=True,
        ),
        http_client=http,
    )
    token = mint_token(extra={"aud": "https://api.test", "token_use": "access_token"})
    state["active"] = False
    assert not live.verify(f"Bearer {token}").ok
    with pytest.raises(ValueError):
        Introspector(ISSUER, IntrospectionOptions(client_id="", client_secret=""))


def test_introspector_cache_bounds_and_expiry() -> None:
    clock = {"t": 1_800_000_000.0}
    hits = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        hits["n"] += 1
        return httpx.Response(200, json={"active": True, "exp": 1_800_000_005})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    i = Introspector(
        ISSUER,
        IntrospectionOptions(client_id="a", client_secret="b", cache_max=2),
        http_client=http,
        now=lambda: clock["t"],
    )
    for t in ("t1", "t2", "t3"):
        assert i.introspect(t) is not None
    assert len(i._cache) == 2
    i.introspect("t3")
    n = hits["n"]
    clock["t"] += 6
    i.introspect("t3")
    assert hits["n"] == n + 1  # never reused past exp


async def test_async_device_authorizations() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json={"object": "device_authorization", "id": "da_1", "user_code": "WDJB-MJHT"}
        )

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    d = AsyncDeviceAuthorizations("https://fapi.test", "sess_jwt", http_client=http)
    auth = await d.lookup("wdjbmjht")
    assert json.loads(seen[-1].content) == {"user_code": "WDJB-MJHT"}
    await d.approve(auth)
    assert seen[-1].url.path == "/v1/client/me/device_authorizations/da_1/approve"
    await d.deny(auth)
    assert seen[-1].url.path == "/v1/client/me/device_authorizations/da_1/deny"


@respx.mock
async def test_risk_events_and_fraud_lookup() -> None:
    lst = respx.get(f"{API_URL}/v1/risk_events").mock(return_value=httpx.Response(200, json=OK))
    met = respx.get(f"{API_URL}/v1/risk_events/metrics").mock(
        return_value=httpx.Response(200, json={"object": "risk_event_metrics", "days": 14})
    )
    fb = respx.post(f"{API_URL}/v1/risk_events/re_1/feedback").mock(
        return_value=httpx.Response(200, json={"object": "risk_event", "feedback": "fraud"})
    )
    fl = respx.post(f"{API_URL}/v1/fraud/lookup").mock(
        return_value=httpx.Response(200, json={"object": "fraud_lookup", "verdict": "allow"})
    )
    c = client()
    c.risk_based_mfa.list_events(
        user_id="u_1", level="high", limit=10, before="2026-02-01T00:00:00Z"
    )
    assert parse_qs(lst.calls.last.request.url.query.decode()) == {
        "user_id": ["u_1"],
        "level": ["high"],
        "limit": ["10"],
        "before": ["2026-02-01T00:00:00Z"],
    }
    assert c.risk_based_mfa.event_metrics(days=14)["days"] == 14
    assert met.calls.last.request.url.params["days"] == "14"
    assert c.risk_based_mfa.event_feedback("re_1", {"verdict": "fraud"})["feedback"] == "fraud"
    assert body_of(fb) == {"verdict": "fraud"}
    assert c.risk_based_mfa.fraud_lookup({"ip": "1.2.3.4"})["verdict"] == "allow"
    assert body_of(fl) == {"ip": "1.2.3.4"}
    async with AsyncAtlasClient(SECRET, base_url=API_URL) as ac:
        await ac.risk_based_mfa.list_events()
        await ac.risk_based_mfa.event_feedback("re_1", {"verdict": "legit"})
    assert body_of(fb) == {"verdict": "legit"}
