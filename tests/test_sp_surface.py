"""Integrator-platform surface (0.17): every route's method, path, query and body on both the
sync and async clients, plus the helpers (v2 webhook signatures, trace context, key formats,
privacy executor, partner link requests, OIDC claims, back-channel logout app, operator flow,
sealed secrets) and the new error fields."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import io
import json
from typing import Any, Callable
from urllib.parse import parse_qsl

import httpx
import pytest
import respx

from atlas_backend import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasClient,
    AtlasError,
    AtlasPlatformClient,
    BackchannelLogoutApp,
    ErrorCode,
    KeyFormat,
    OAuthFlowError,
    OperatorLogin,
    SealedBox,
    Traceparent,
    VerificationError,
    atlas_id_integration_token,
    canonical_webhook_event,
    get_partner_link_request,
    handle_backchannel_logout,
    oidc_authorize_url_with_organization,
    oidc_organization_of,
    oidc_organizations_of,
    oidc_sso_of,
    request_partner_link,
    valid_privacy_idempotency_key,
    verify_partner_link_delivery,
    verify_privacy_case_request,
    verify_privacy_completion,
    verify_webhook,
    webhook_event_spellings,
)
from atlas_backend import models  # noqa: F401

API = "https://api.example.test"

Row = tuple[str, str, Any, Callable[[Any], Any]]

BAPI: list[Row] = [
    ("GET", "/v1/whoami", None, lambda c: c.whoami.get()),
    (
        "POST",
        "/v1/secret_keys",
        {"name": "ci", "scopes": ["users:read"]},
        lambda c: c.secret_keys.create({"name": "ci", "scopes": ["users:read"]}),
    ),
    (
        "POST",
        "/v1/secret_keys?dry_run=true",
        {"name": "ci"},
        lambda c: c.secret_keys.create({"name": "ci"}, dry_run=True),
    ),
    (
        "POST",
        "/v1/secret_keys",
        {
            "name": "ci",
            "allowed_origins": ["https://app.example.com"],
            "owner": "user:u1",
            "expires_at": 1,
        },
        lambda c: c.secret_keys.create(
            {
                "name": "ci",
                "allowed_origins": ["https://app.example.com"],
                "owner": "user:u1",
                "expires_at": 1,
            }
        ),
    ),
    (
        "GET",
        "/v1/secret_keys?metadata%5Bteam%5D=a",
        None,
        lambda c: c.secret_keys.list(metadata={"team": "a"}),
    ),
    ("GET", "/v1/secret_keys/sk_1", None, lambda c: c.secret_keys.get("sk_1")),
    (
        "PATCH",
        "/v1/secret_keys/sk_1",
        {"name": "x"},
        lambda c: c.secret_keys.update("sk_1", {"name": "x"}),
    ),
    (
        "POST",
        "/v1/secret_keys/sk_1/rotate",
        {"overlap_seconds": 0},
        lambda c: c.secret_keys.rotate("sk_1", {"overlap_seconds": 0}),
    ),
    ("POST", "/v1/secret_keys/sk_1/revoke", None, lambda c: c.secret_keys.revoke("sk_1")),
    ("GET", "/v1/keys", None, lambda c: c.keys.list()),
    (
        "POST",
        "/v1/keys/revoke_leaked",
        {"keys": ["atlas_live_sk_x"]},
        lambda c: c.keys.revoke_leaked({"keys": ["atlas_live_sk_x"]}),
    ),
    ("GET", "/v1/operator", None, lambda c: c.keys.operator()),
    (
        "POST",
        "/v1/partner_links",
        {"partner": "cookiemunch", "scopes": ["privacy:execute"]},
        lambda c: c.partner_links.create({"partner": "cookiemunch", "scopes": ["privacy:execute"]}),
    ),
    ("GET", "/v1/partner_links", None, lambda c: c.partner_links.list()),
    ("GET", "/v1/partner_links/pl_1", None, lambda c: c.partner_links.get("pl_1")),
    (
        "PATCH",
        "/v1/partner_links/pl_1",
        {"cert_fingerprints": ["abc"]},
        lambda c: c.partner_links.set_certificates("pl_1", ["abc"]),
    ),
    (
        "POST",
        "/v1/partner_links/pl_1/rotate_secret",
        None,
        lambda c: c.partner_links.rotate_secret("pl_1"),
    ),
    ("DELETE", "/v1/partner_links/pl_1", None, lambda c: c.partner_links.revoke("pl_1")),
    (
        "GET",
        "/v1/partner_links/requests?direction=inbound&status=pending%2Cdelivery_failed",
        None,
        lambda c: c.partner_links.requests.list(
            direction="inbound", status=["pending", "delivery_failed"]
        ),
    ),
    (
        "GET",
        "/v1/partner_links/requests/plr_1",
        None,
        lambda c: c.partner_links.requests.get("plr_1"),
    ),
    (
        "POST",
        "/v1/partner_links/requests/plr_1/approve",
        {"scopes": ["privacy:execute"]},
        lambda c: c.partner_links.requests.approve("plr_1", {"scopes": ["privacy:execute"]}),
    ),
    (
        "POST",
        "/v1/partner_links/requests/plr_1/approve",
        {},
        lambda c: c.partner_links.requests.approve("plr_1"),
    ),
    (
        "POST",
        "/v1/partner_links/requests/plr_1/deny",
        None,
        lambda c: c.partner_links.requests.deny("plr_1"),
    ),
    ("GET", "/v1/partner_links/outbound", None, lambda c: c.partner_links.outbound.list()),
    (
        "PUT",
        "/v1/partner_links/outbound/cm",
        {"token": "t"},
        lambda c: c.partner_links.outbound.save("cm", {"token": "t"}),
    ),
    (
        "POST",
        "/v1/partner_links/outbound/cm/test",
        None,
        lambda c: c.partner_links.outbound.test("cm"),
    ),
    (
        "POST",
        "/v1/partner_links/outbound/cm/request",
        {"scopes": ["privacy:execute"]},
        lambda c: c.partner_links.outbound.request("cm", {"scopes": ["privacy:execute"]}),
    ),
    (
        "DELETE",
        "/v1/partner_links/outbound/cm",
        None,
        lambda c: c.partner_links.outbound.remove("cm"),
    ),
    ("GET", "/v1/atlas_id_apps", None, lambda c: c.atlas_id_grants.list_apps()),
    (
        "GET",
        "/v1/atlas_id_apps/a_1/users?email=a%40b.c",
        None,
        lambda c: c.atlas_id_grants.lookup("a_1", "a@b.c"),
    ),
    (
        "DELETE",
        "/v1/atlas_id_apps/a_1/grants/g_1",
        None,
        lambda c: c.atlas_id_grants.revoke_grant("a_1", "g_1"),
    ),
    ("GET", "/v1/privacy", None, lambda c: c.privacy.discover()),
    ("GET", "/v1/privacy/presets/cookiemunch", None, lambda c: c.privacy.preset("cookiemunch")),
    (
        "POST",
        "/v1/privacy/lookup",
        {"emails": ["a@b.c"]},
        lambda c: c.privacy.lookup({"emails": ["a@b.c"]}),
    ),
    (
        "POST",
        "/v1/privacy/requests",
        {"subjectId": "u"},
        lambda c: c.privacy.create_request({"subjectId": "u"}),
    ),
    ("GET", "/v1/privacy/requests/pr_1", None, lambda c: c.privacy.get_request("pr_1")),
    ("POST", "/v1/privacy/requests/pr_1/cancel", None, lambda c: c.privacy.cancel_request("pr_1")),
    ("GET", "/v1/instance/privacy_orchestrator", None, lambda c: c.privacy.orchestrator.get()),
    (
        "PUT",
        "/v1/instance/privacy_orchestrator",
        {"provider": "cookiemunch"},
        lambda c: c.privacy.orchestrator.set({"provider": "cookiemunch"}),
    ),
    (
        "DELETE",
        "/v1/instance/privacy_orchestrator",
        None,
        lambda c: c.privacy.orchestrator.delete(),
    ),
    ("GET", "/v1/instance/integrations", None, lambda c: c.integrations.list()),
    ("GET", "/v1/instance/integrations/ref", None, lambda c: c.integrations.get("ref")),
    (
        "PUT",
        "/v1/instance/integrations/ref?dry_run=true",
        {"enabled": True},
        lambda c: c.integrations.set("ref", {"enabled": True}, dry_run=True),
    ),
    ("DELETE", "/v1/instance/integrations/ref", None, lambda c: c.integrations.delete("ref")),
    (
        "GET",
        "/v1/instance/integrations/ref/deliveries?trace=t1",
        None,
        lambda c: c.integrations.deliveries("ref", trace="t1"),
    ),
    (
        "POST",
        "/v1/instance/integrations/ref/events_secret",
        None,
        lambda c: c.integrations.events_secret("ref"),
    ),
    (
        "POST",
        "/v1/instance/integrations/ref/atlas_id_tokens",
        None,
        lambda c: c.integrations.atlas_id_tokens("ref"),
    ),
    (
        "POST",
        "/v1/sessions/s_1/integration_tokens/referalli",
        {"audience_hint": "x"},
        lambda c: c.integrations.get_token("s_1", "referalli", audience_hint="x"),
    ),
    (
        "POST",
        "/v1/sessions/s_1/integration_tokens/referalli",
        None,
        lambda c: c.sessions.get_token("s_1", for_="referalli"),
    ),
    (
        "POST",
        "/v1/integrations/verify_errors",
        {"code": "x"},
        lambda c: c.integrations.report_verify_error({"code": "x"}),
    ),
    ("GET", "/v1/integrations/ref/card", None, lambda c: c.integrations.card("ref")),
    (
        "POST",
        "/v1/integrations/ref/card/actions/revoke_sessions",
        None,
        lambda c: c.integrations.card_revoke_sessions("ref"),
    ),
    ("GET", "/v1/public/instances/ins_1", None, lambda c: c.integrations.public_instance("ins_1")),
    ("GET", "/v1/status", None, lambda c: c.status.get()),
    ("GET", "/v1/instance/status_subscription", None, lambda c: c.status.subscription.get()),
    (
        "PUT",
        "/v1/instance/status_subscription",
        {"enabled": True},
        lambda c: c.status.subscription.set({"enabled": True}),
    ),
    ("DELETE", "/v1/instance/status_subscription", None, lambda c: c.status.subscription.delete()),
    (
        "POST",
        "/v1/instance/status_subscription/rotate_feed",
        None,
        lambda c: c.status.subscription.rotate_feed(),
    ),
    (
        "GET",
        "/v1/instance/status_incidents?open=true&limit=5",
        None,
        lambda c: c.status.incidents(open=True, limit=5),
    ),
    ("GET", "/v1/instance/status_dependencies", None, lambda c: c.status.dependencies.list()),
    (
        "POST",
        "/v1/instance/status_dependencies",
        {"url": "u"},
        lambda c: c.status.dependencies.create({"url": "u"}),
    ),
    ("GET", "/v1/instance/status_dependencies/d1", None, lambda c: c.status.dependencies.get("d1")),
    (
        "PATCH",
        "/v1/instance/status_dependencies/d1",
        {"name": "n"},
        lambda c: c.status.dependencies.update("d1", {"name": "n"}),
    ),
    (
        "DELETE",
        "/v1/instance/status_dependencies/d1",
        None,
        lambda c: c.status.dependencies.delete("d1"),
    ),
    (
        "POST",
        "/v1/instance/status_dependencies/d1/refresh",
        None,
        lambda c: c.status.dependencies.refresh("d1"),
    ),
    ("GET", "/v1/instance/notices?all=true", None, lambda c: c.notices.list(all=True)),
    ("POST", "/v1/instance/notices/n1/acknowledge", None, lambda c: c.notices.acknowledge("n1")),
    ("GET", "/v1/security_advisories", None, lambda c: c.security_advisories.list()),
    (
        "POST",
        "/v1/security_advisories/a1/acknowledge",
        None,
        lambda c: c.security_advisories.acknowledge("a1"),
    ),
    ("GET", "/v1/public/security_advisories", None, lambda c: c.security_advisories.list_public()),
    ("GET", "/v1/audit_exports", None, lambda c: c.audit_exports.list()),
    ("GET", "/v1/audit_exports/ae1", None, lambda c: c.audit_exports.get("ae1")),
    ("POST", "/v1/audit_exports", {"url": "u"}, lambda c: c.audit_exports.create({"url": "u"})),
    (
        "PATCH",
        "/v1/audit_exports/ae1",
        {"active": False},
        lambda c: c.audit_exports.update("ae1", {"active": False}),
    ),
    ("DELETE", "/v1/audit_exports/ae1", None, lambda c: c.audit_exports.delete("ae1")),
    ("POST", "/v1/audit_exports/ae1/test", None, lambda c: c.audit_exports.test("ae1")),
    (
        "POST",
        "/v1/audit_exports/ae1/rotate_secret",
        None,
        lambda c: c.audit_exports.rotate_secret("ae1"),
    ),
    ("GET", "/v1/instance/sub_processors", None, lambda c: c.sub_processors.list()),
    ("GET", "/v1/entitlements", None, lambda c: c.entitlements.get()),
    ("GET", "/v1/integration-health", None, lambda c: c.integration_health.get()),
    ("GET", "/v1/integration-health/providers", None, lambda c: c.integration_health.providers()),
    ("GET", "/v1/embed?instance=ins_1", None, lambda c: c.embed.get(instance="ins_1")),
    ("GET", "/v1/instance/csp", None, lambda c: c.embed.csp()),
    (
        "GET",
        "/v1/openapi/diff?since=2026-10-15&surface=bapi",
        None,
        lambda c: c.openapi.diff(since="2026-10-15", surface="bapi"),
    ),
    ("GET", "/.well-known/api-catalog", None, lambda c: c.openapi.api_catalog()),
    (
        "GET",
        "/v1/instance/unknown_fields_report?days=7",
        None,
        lambda c: c.instance.unknown_fields_report(days=7),
    ),
    (
        "GET",
        "/v1/instance/preflight?min_severity=warning&include_suppressed=true",
        None,
        lambda c: c.instance.preflight(min_severity="warning", include_suppressed=True),
    ),
    (
        "GET",
        "/v1/messaging_providers/email",
        None,
        lambda c: c.messaging_providers.get_channel("email"),
    ),
    (
        "GET",
        "/v1/delivery_health?kind=webhook",
        None,
        lambda c: c.delivery_health.get(kind="webhook"),
    ),
    (
        "PUT",
        "/v1/delivery_health/webhook/we1/alert_contacts",
        {"alert_contacts": ["a@b.c"]},
        lambda c: c.delivery_health.set_alert_contacts("webhook", "we1", ["a@b.c"]),
    ),
    ("GET", "/v1/meta/egress_ips", None, lambda c: c.meta.egress_ips()),
    ("GET", "/v1/meta/egress_ips", None, lambda c: c.webhooks.egress_ips()),
    ("GET", "/v1/webhook_endpoints/we1", None, lambda c: c.webhooks.endpoints.get("we1")),
    (
        "GET",
        "/v1/webhook_endpoints?metadata%5Bk%5D=v&starting_after=we0&include_deprecated=true",
        None,
        lambda c: c.webhooks.endpoints.list(
            metadata={"k": "v"}, starting_after="we0", include_deprecated=True
        ),
    ),
    (
        "POST",
        "/v1/webhook_endpoints?dry_run=true",
        {"url": "u"},
        lambda c: c.webhooks.endpoints.create({"url": "u"}, dry_run=True),
    ),
    (
        "PUT",
        "/v1/webhook_endpoints/by_url",
        {"url": "u"},
        lambda c: c.webhooks.endpoints.put_by_url({"url": "u"}),
    ),
    (
        "POST",
        "/v1/webhook_endpoints/we1/test?wait=10",
        None,
        lambda c: c.webhooks.endpoints.test("we1", wait=10),
    ),
    (
        "POST",
        "/v1/webhook_endpoints/we1/redeliver",
        {"since": "failing_since"},
        lambda c: c.webhooks.endpoints.redeliver_window("we1", {"since": "failing_since"}),
    ),
    (
        "POST",
        "/v1/webhook_endpoints/we1/replay",
        {"since": "failing_since"},
        lambda c: c.webhooks.endpoints.replay("we1", {"since": "failing_since"}),
    ),
    (
        "GET",
        "/v1/webhook_endpoints/we1/deliveries?status=failed&until=9&starting_after=d1",
        None,
        lambda c: c.webhooks.deliveries("we1", status="failed", until=9, starting_after="d1"),
    ),
    (
        "GET",
        "/v1/webhook_endpoints/we1/deliveries?event_type=user.created&since=1",
        None,
        lambda c: c.webhooks.endpoints.list_deliveries("we1", event_type="user.created", since=1),
    ),
    (
        "GET",
        "/v1/users?updated_after=5&order_by=-updated_at",
        None,
        lambda c: c.users.list(updated_after=5, order_by="-updated_at"),
    ),
    ("GET", "/v1/events?since=5&order=asc", None, lambda c: c.events.list(since=5, order="asc")),
    (
        "POST",
        "/v1/instance/referrals/referalli/install",
        {"return_to": "https://x"},
        lambda c: c.instance.referrals.install("referalli", {"return_to": "https://x"}),
    ),
]

PLATFORM: list[Row] = [
    ("GET", "/v1/platform/whoami", None, lambda c: c.whoami.get()),
    ("GET", "/v1/platform/keys?kind=platform", None, lambda c: c.keys.list(kind="platform")),
    (
        "POST",
        "/v1/platform/keys",
        {"scopes": ["apps:read"], "allowed_origins": ["https://a.example.com"]},
        lambda c: c.keys.create(
            {"scopes": ["apps:read"], "allowed_origins": ["https://a.example.com"]}
        ),
    ),
    ("PATCH", "/v1/platform/keys/k1", {"name": "n"}, lambda c: c.keys.update("k1", {"name": "n"})),
    ("POST", "/v1/platform/keys/k1/revoke", None, lambda c: c.keys.revoke("k1")),
    (
        "GET",
        "/v1/platform/audit_logs?action=key.revoked",
        None,
        lambda c: c.audit.list(action="key.revoked"),
    ),
    ("GET", "/v1/platform/audit_streams", None, lambda c: c.audit.streams.list()),
    (
        "POST",
        "/v1/platform/audit_streams",
        {"url": "u"},
        lambda c: c.audit.streams.create({"url": "u"}),
    ),
    (
        "PATCH",
        "/v1/platform/audit_streams/s1",
        {"active": False},
        lambda c: c.audit.streams.update("s1", {"active": False}),
    ),
    ("DELETE", "/v1/platform/audit_streams/s1", None, lambda c: c.audit.streams.delete("s1")),
    ("POST", "/v1/platform/audit_streams/s1/test", None, lambda c: c.audit.streams.test("s1")),
    (
        "POST",
        "/v1/platform/apps/app_1/secret_keys",
        {},
        lambda c: c.apps.create_secret_key("app_1"),
    ),
    (
        "POST",
        "/v1/platform/apps/app_1/clone_config?dry_run=true",
        {"from_app_id": "app_0"},
        lambda c: c.apps.clone_config("app_1", {"from_app_id": "app_0"}, dry_run=True),
    ),
    (
        "POST",
        "/v1/platform/apps?dry_run=true",
        {"external_ref": "e1", "metadata": {"a": "b"}},
        lambda c: c.apps.create({"external_ref": "e1", "metadata": {"a": "b"}}, dry_run=True),
    ),
    (
        "GET",
        "/v1/platform/apps?metadata%5Bteam%5D=a",
        None,
        lambda c: c.apps.list(metadata={"team": "a"}),
    ),
    (
        "POST",
        "/v1/platform/apps/bulk_delete",
        {"metadata": {"t": "1"}, "dry_run": True},
        lambda c: c.apps.bulk_delete({"metadata": {"t": "1"}, "dry_run": True}),
    ),
]


def _split(path_q: str) -> tuple[str, list[tuple[str, str]]]:
    path, _, query = path_q.partition("?")
    return path, sorted(parse_qsl(query, keep_blank_values=True))


def _check(route: respx.Route, verb: str, path_q: str, body: Any) -> None:
    req = route.calls.last.request
    path, query = _split(path_q)
    assert req.method == verb, path_q
    assert req.url.path == path, path_q
    assert sorted(parse_qsl(req.url.query.decode())) == query, path_q
    if body is None:
        assert req.content == b"", f"{verb} {path_q} should send no body"
    else:
        assert json.loads(req.content) == body, path_q


@pytest.mark.parametrize(
    "rows,factory",
    [
        (BAPI, lambda: AtlasClient("sk_test", base_url=API)),
        (PLATFORM, lambda: AtlasPlatformClient("psk_test", base_url=API)),
    ],
)
def test_sync_routes(rows: list[Row], factory: Callable[[], Any]) -> None:
    with respx.mock(base_url=API, assert_all_called=False) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={"ok": True}))
        client = factory()
        for verb, path_q, body, call in rows:
            call(client)
            _check(route, verb, path_q, body)


@pytest.mark.parametrize(
    "rows,factory",
    [
        (BAPI, lambda: AsyncAtlasClient("sk_test", base_url=API)),
        (PLATFORM, lambda: AsyncAtlasPlatformClient("psk_test", base_url=API)),
    ],
)
def test_async_routes(rows: list[Row], factory: Callable[[], Any]) -> None:
    async def run() -> None:
        with respx.mock(base_url=API, assert_all_called=False) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={"ok": True}))
            client = factory()
            for verb, path_q, body, call in rows:
                await call(client)
                _check(route, verb, path_q, body)

    asyncio.run(run())


def test_route_counts() -> None:
    assert len(BAPI) == 104
    assert len(PLATFORM) == 16


def test_oauth_token_forms_are_urlencoded() -> None:
    with respx.mock(base_url=API) as mock:
        route = mock.post("/v1/oauth/token").mock(
            return_value=httpx.Response(200, json={"access_token": "t"})
        )
        c = AtlasClient("sk_test", base_url=API)
        c.keys.client_credentials(client_id="a", client_secret="b", scope="privacy:execute")
        req = route.calls.last.request
        assert req.headers["content-type"] == "application/x-www-form-urlencoded"
        assert dict(parse_qsl(req.content.decode()))["grant_type"] == "client_credentials"
        c.keys.token_exchange(subject_token="tok", resource="ins_1")
        form = dict(parse_qsl(route.calls.last.request.content.decode()))
        assert form["grant_type"] == "urn:ietf:params:oauth:grant-type:token-exchange"
        assert form["resource"] == "ins_1"


def test_idempotency_key_and_traceparent_headers() -> None:
    tp = Traceparent.generate()
    with respx.mock(base_url=API) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={}))
        c = AtlasClient("sk_test", base_url=API, traceparent=tp)
        c.privacy.create_request({"subjectId": "u"}, idempotency_key="k" * 20)
        assert route.calls.last.request.headers["idempotency-key"] == "k" * 20
        assert route.calls.last.request.headers["traceparent"] == tp
        other = Traceparent.child(tp)
        c.with_options(traceparent=other).whoami.get()
        assert route.calls.last.request.headers["traceparent"] == other
        AtlasClient("sk_test", base_url=API).whoami.get()
        assert "traceparent" not in route.calls.last.request.headers
        AtlasPlatformClient("psk_test", base_url=API, traceparent=tp).whoami.get()
        assert route.calls.last.request.headers["traceparent"] == tp


def test_trace_helpers() -> None:
    p = Traceparent.parse("00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01")
    assert p is not None and p.trace_id == "0af7651916cd43dd8448eb211c80319c" and p.sampled
    assert not Traceparent.is_valid("00-00000000000000000000000000000000-b7ad6b7169203331-01")
    assert not Traceparent.is_valid("nope")
    child = Traceparent.child("00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01")
    cp = Traceparent.parse(child)
    assert cp is not None and cp.trace_id == p.trace_id and cp.span_id != p.span_id
    assert Traceparent.is_valid(Traceparent.child(None))
    assert Traceparent.trace_id(child) == p.trace_id


def test_key_formats_accept_both() -> None:
    assert KeyFormat.is_secret_key("sk_live_abc") and KeyFormat.is_secret_key("atlas_live_sk_abc")
    assert KeyFormat.is_platform_key("psk_live_abc") and KeyFormat.is_platform_key(
        "atlas_test_psk_abc"
    )
    assert KeyFormat.is_publishable_key("atlas_live_pk_abc") and KeyFormat.is_publishable_key(
        "pk_test_abc"
    )
    assert KeyFormat.is_webhook_secret("whsec_abc") and KeyFormat.is_webhook_secret(
        "atlas_live_whsec_abc"
    )
    assert KeyFormat.kind("atlas_live_zz_abc") is None
    assert KeyFormat.kind("hello") is None
    assert KeyFormat.environment("atlas_live_sk_abc") == "live"
    assert KeyFormat.environment("sk_live_abc") == "live"
    assert KeyFormat.parse("atlas_test_sk_abc").format == "atlas"  # type: ignore[union-attr]
    # clients accept either format
    AtlasClient("atlas_live_sk_abc")
    AtlasPlatformClient("atlas_live_psk_abc")


def test_error_fields() -> None:
    def err(status: int, errors: list[dict[str, Any]]) -> AtlasError:
        with respx.mock(base_url=API) as mock:
            mock.route().mock(return_value=httpx.Response(status, json={"errors": errors}))
            with pytest.raises(AtlasError) as info:
                AtlasClient("sk_test", base_url=API).users.get("x")
            return info.value

    e = err(
        404,
        [
            {
                "code": "ROUTE_NOT_FOUND",
                "message": "no",
                "did_you_mean": ["/v1/organizations"],
                "allowed_methods": ["GET"],
                "docs_url": "https://atlasauth.net/errors/route_not_found",
            }
        ],
    )
    assert e.has_code(ErrorCode.ROUTE_NOT_FOUND)
    assert e.did_you_mean == ["/v1/organizations"] and e.allowed_methods == ["GET"]
    assert e.docs_url == "https://atlasauth.net/errors/route_not_found"

    e = err(
        403,
        [
            {
                "code": "INSUFFICIENT_SCOPE",
                "message": "no",
                "meta": {"required_scope": "users:write"},
            }
        ],
    )
    assert e.is_insufficient_scope and e.required_scope == "users:write"
    assert err(403, [{"code": "SCOPE_MISSING", "message": "no"}]).is_insufficient_scope
    e = err(403, [{"code": "STEP_UP_REQUIRED", "message": "no"}])
    assert e.is_step_up_required and not e.is_insufficient_scope
    assert e.did_you_mean == [] and e.docs_url is None
    e = err(403, [{"code": "ORIGIN_NOT_ALLOWED", "message": "no"}])
    assert (
        e.is_origin_not_allowed and e.code == ErrorCode.ORIGIN_NOT_ALLOWED == "ORIGIN_NOT_ALLOWED"
    )
    assert ErrorCode.PARTNER_LINK_UNAVAILABLE == "PARTNER_LINK_UNAVAILABLE"


# --- webhook v2 ---------------------------------------------------------------

SECRET = "whsec_test_secret"
NOW = 1_757_937_600_000
URL = "https://example.com/hooks/atlas"
BODY = json.dumps({"id": "evt_1", "type": "webhook.test", "data": {}})


def _mac(payload: str) -> str:
    return base64.b64encode(
        hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    ).decode()


def _headers(sig: str) -> dict[str, str]:
    return {"Atlas-Id": "evt_1", "Atlas-Timestamp": str(NOW), "Atlas-Signature": sig}


def test_webhook_v2_signature_covers_the_url() -> None:
    v1 = f"v1,{_mac(f'evt_1.{NOW}.{BODY}')}"
    v2 = f"v2,{_mac(f'evt_1.{NOW}.{URL}.{BODY}')}"
    assert verify_webhook(BODY, _headers(f"{v1} {v2}"), SECRET, now_ms=NOW, url=URL).verified
    assert verify_webhook(BODY, _headers(v2), SECRET, now_ms=NOW, url=URL).verified
    assert verify_webhook(BODY, _headers(v2), SECRET, now_ms=NOW, url=URL, require_v2=True).verified
    r = verify_webhook(BODY, _headers(v2), SECRET, now_ms=NOW, url="https://evil.example/x")
    assert r.reason == "signature_mismatch"
    assert not verify_webhook(
        BODY, _headers(v1), SECRET, now_ms=NOW, url=URL, require_v2=True
    ).verified
    assert verify_webhook(BODY, _headers(v2), SECRET, now_ms=NOW).reason == "malformed_signature"
    assert verify_webhook(BODY, _headers(f"v3,zzz {v1}"), SECRET, now_ms=NOW).verified


def test_privacy_helpers() -> None:
    sig = f"v1,{_mac(f'evt_1.{NOW}.{BODY}')}"
    assert verify_privacy_case_request(BODY, _headers(sig), SECRET, now_ms=NOW).verified
    assert valid_privacy_idempotency_key("k" * 16) and not valid_privacy_idempotency_key("short")
    completed = json.dumps({"id": "evt_1", "type": "privacy_request.completed", "data": {}})
    sig2 = f"v1,{_mac(f'evt_1.{NOW}.{completed}')}"
    assert verify_privacy_completion(completed, _headers(sig2), SECRET, now_ms=NOW).verified
    r = verify_privacy_completion(BODY, _headers(sig), SECRET, now_ms=NOW)
    assert not r.verified and r.reason == "unexpected_event"


def test_event_aliases() -> None:
    assert canonical_webhook_event("session.ended") == "session.revoked"
    assert canonical_webhook_event("user.created") == "user.created"
    assert "session.removed" in webhook_event_spellings("session.revoked")


# --- partner link requests (the partner's side) --------------------------------


def test_partner_link_request_protocol() -> None:
    with respx.mock(base_url=API) as mock:
        post = mock.post("/v1/partner_link_requests").mock(
            return_value=httpx.Response(
                201, json={"id": "plr_1", "request_secret": "rs_1", "status": "pending"}
            )
        )
        out = request_partner_link(
            {
                "partner": "acme",
                "resource": "ins_1",
                "scopes": ["privacy:execute"],
                "callback_url": "https://acme.test/cb",
            },
            api_url=API,
        )
        assert out["request_secret"] == "rs_1"
        assert json.loads(post.calls.last.request.content)["callback_url"] == "https://acme.test/cb"
        assert "authorization" not in post.calls.last.request.headers
        get = mock.get("/v1/partner_link_requests/plr_1").mock(
            return_value=httpx.Response(200, json={"status": "approved"})
        )
        assert get_partner_link_request("plr_1", "rs_1", api_url=API)["status"] == "approved"
        assert get.calls.last.request.headers["authorization"] == "Bearer rs_1"
        mock.post("/v1/partner_link_requests").mock(
            return_value=httpx.Response(
                403, json={"errors": [{"code": "PARTNER_LINK_UNAVAILABLE", "message": "no"}]}
            )
        )
        with pytest.raises(AtlasError) as info:
            request_partner_link({"partner": "x"}, api_url=API)
        assert info.value.has_code("PARTNER_LINK_UNAVAILABLE")

    delivery = json.dumps(
        {
            "object": "partner_link.credentials",
            "request_id": "plr_1",
            "client_id": "c",
            "client_secret": "s",
        }
    )
    ts = NOW
    sig = base64.b64encode(
        hmac.new(b"rs_1", f"evt_9.{ts}.{delivery}".encode(), hashlib.sha256).digest()
    ).decode()
    headers = {"atlas-id": "evt_9", "atlas-timestamp": str(ts), "atlas-signature": f"v1,{sig}"}
    ok = verify_partner_link_delivery(delivery, headers, "rs_1", now_ms=ts)
    assert ok.verified and ok.event["client_secret"] == "s"  # type: ignore[index]
    assert not verify_partner_link_delivery(delivery, headers, "other", now_ms=ts).verified
    url = "https://acme.test/cb"
    sig2 = base64.b64encode(
        hmac.new(b"rs_1", f"evt_9.{ts}.{url}.{delivery}".encode(), hashlib.sha256).digest()
    ).decode()
    h2 = {**headers, "atlas-signature": f"v2,{sig2}"}
    assert verify_partner_link_delivery(delivery, h2, "rs_1", url=url, now_ms=ts).verified


# --- OIDC claims ----------------------------------------------------------------


def test_oidc_org_and_sso_claims() -> None:
    claims = {
        "sub": "u1",
        "org_id": "org_1",
        "org_slug": "acme",
        "org_role": "admin",
        "org_permissions": ["org:read", 3],
        "orgs": [{"id": "org_1", "slug": "acme", "role": "admin"}, {"slug": "x"}],
        "sso_connection_id": "sso_1",
        "sso_organization_id": "org_1",
        "sso_connection_type": "saml",
        "sso_tenant_id": "tid",
        "sso_issuer": "https://idp",
        "sso_domain": "acme.com",
    }
    assert oidc_organization_of(claims) == {
        "id": "org_1",
        "slug": "acme",
        "role": "admin",
        "permissions": ["org:read"],
    }
    assert oidc_organizations_of(claims) == [{"id": "org_1", "slug": "acme", "role": "admin"}]
    assert oidc_sso_of(claims) == {
        "connection_id": "sso_1",
        "organization_id": "org_1",
        "type": "saml",
        "tenant_id": "tid",
        "issuer": "https://idp",
        "domain": "acme.com",
    }
    assert oidc_organization_of({"sub": "u"}) is None
    assert oidc_organizations_of({"sub": "u"}) is None
    assert oidc_sso_of({"sub": "u"}) is None
    url = oidc_authorize_url_with_organization(
        "https://atlasauth.net/oauth2/authorize?client_id=c&scope=openid", "acme"
    )
    assert dict(parse_qsl(url.split("?", 1)[1]))["organization"] == "acme"
    again = oidc_authorize_url_with_organization(url, "other")
    assert dict(parse_qsl(again.split("?", 1)[1]))["organization"] == "other"


# --- browser atlas_id_tokens route ------------------------------------------------


def test_atlas_id_integration_token_route() -> None:
    fapi = "https://clerk.example.test"
    with respx.mock(base_url=fapi) as mock:
        route = mock.post("/v1/client/integrations/referalli/atlas_id_tokens").mock(
            return_value=httpx.Response(
                200,
                json={
                    "jwt": "j",
                    "expires_in": 60,
                    "integration": "referalli",
                    "audience": "a",
                    "issuer": "i",
                    "jwks_uri": "u",
                },
            )
        )
        out = atlas_id_integration_token(
            fapi, "pk_test_1", "referalli", "at_1", origin="https://app.example.com"
        )
        assert out is not None and out["jwt"] == "j"
        req = route.calls.last.request
        assert req.headers["authorization"] == "Bearer at_1"
        assert req.headers["origin"] == "https://app.example.com"
        assert dict(parse_qsl(req.url.query.decode()))["publishable_key"] == "pk_test_1"
        atlas_id_integration_token(fapi, "pk_test_1", "referalli", "at_1", dpop_proof="proof")
        req = route.calls.last.request
        assert req.headers["authorization"] == "DPoP at_1" and req.headers["dpop"] == "proof"
        mock.post("/v1/client/integrations/nope/atlas_id_tokens").mock(
            return_value=httpx.Response(403, json={})
        )
        assert atlas_id_integration_token(fapi, "pk_test_1", "nope", "at_1") is None
        assert atlas_id_integration_token(fapi, "pk_test_1", "referalli", "") is None


# --- back-channel logout handler ---------------------------------------------------


class _Claims:
    sid = "sess_1"
    sub = "u1"


class _FakeVerifier:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def verify(self, token: str) -> _Claims:
        if self.error:
            raise self.error
        return _Claims()


def _wsgi(app: Any, method: str, form: str) -> tuple[str, dict[str, str]]:
    captured: dict[str, Any] = {}

    def start(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = form.encode()
    app(
        {
            "REQUEST_METHOD": method,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        },
        start,
    )
    return captured["status"], captured["headers"]


def test_backchannel_logout_handler_and_app() -> None:
    seen: list[Any] = []
    assert handle_backchannel_logout(_FakeVerifier(), "t", seen.append)[0] == 200
    assert seen and seen[0].sid == "sess_1"
    assert (
        handle_backchannel_logout(
            _FakeVerifier(VerificationError(VerificationError.INVALID)), "t", seen.append
        )[0]
        == 400
    )
    status, headers = handle_backchannel_logout(
        _FakeVerifier(VerificationError(VerificationError.NO_KEYS)), "t", seen.append
    )
    assert status == 503 and headers["Retry-After"] == "30"

    def boom(_: Any) -> None:
        raise RuntimeError("db down")

    assert handle_backchannel_logout(_FakeVerifier(), "t", boom)[0] == 503

    app = BackchannelLogoutApp(_FakeVerifier(), seen.append)
    assert _wsgi(app, "POST", "logout_token=tok")[0].startswith("200")
    assert _wsgi(app, "GET", "")[0].startswith("405")
    bad = BackchannelLogoutApp(
        _FakeVerifier(VerificationError(VerificationError.MALFORMED)), seen.append
    )
    assert _wsgi(bad, "POST", "logout_token=x")[0].startswith("400")


# --- operator flow -----------------------------------------------------------------


def test_operator_device_flow() -> None:
    sleeps: list[float] = []
    with respx.mock(base_url=API) as mock:
        mock.get("/v1/operator").mock(
            return_value=httpx.Response(
                200,
                json={
                    "client_id": "cli",
                    "scope": "openid",
                    "device_authorization_endpoint": f"{API}/v1/operator/device",
                    "token_endpoint": f"{API}/v1/operator/token",
                },
            )
        )
        mock.post("/v1/operator/device").mock(
            return_value=httpx.Response(
                200,
                json={
                    "device_code": "dc",
                    "user_code": "ABCD-EFGH",
                    "expires_in": 600,
                    "interval": 1,
                },
            )
        )
        token = mock.post("/v1/operator/token").mock(
            side_effect=[
                httpx.Response(400, json={"error": "authorization_pending"}),
                httpx.Response(400, json={"error": "slow_down"}),
                httpx.Response(200, json={"access_token": "op_tok"}),
            ]
        )
        login = OperatorLogin(API, sleep=sleeps.append)
        start = login.start()
        assert start["user_code"] == "ABCD-EFGH"
        assert login.poll(start)["access_token"] == "op_tok"
        assert token.call_count == 3 and sleeps == [1, 1, 6]
        ex = mock.post("/v1/oauth/token").mock(
            return_value=httpx.Response(200, json={"access_token": "scoped"})
        )
        assert (
            login.exchange("op_tok", "ins_1", ["users:read", "users:write"])["access_token"]
            == "scoped"
        )
        form = dict(parse_qsl(ex.calls.last.request.content.decode()))
        assert form["scope"] == "users:read users:write" and form["resource"] == "ins_1"
        mock.post("/v1/oauth/token").mock(
            return_value=httpx.Response(
                403, json={"errors": [{"code": "INSUFFICIENT_SCOPE", "message": "no"}]}
            )
        )
        with pytest.raises(OAuthFlowError) as info:
            login.exchange("op_tok", "ins_1", "x")
        assert info.value.code == "INSUFFICIENT_SCOPE"


# --- sealed secrets ----------------------------------------------------------------


def test_sealed_box_round_trip() -> None:
    pytest.importorskip("nacl")
    pair = SealedBox.generate_key_pair()
    assert pair.secret_recipient.startswith("x25519:")
    sealed = SealedBox.seal("atlas_live_sk_secret", pair.secret_recipient)
    assert SealedBox.open(sealed, pair.public_key, pair.secret_key) == b"atlas_live_sk_secret"
    other = SealedBox.generate_key_pair()
    with pytest.raises(ValueError):
        SealedBox.open(sealed, other.public_key, other.secret_key)
    with pytest.raises(ValueError):
        SealedBox.seal("x", "x25519:AAAA")
