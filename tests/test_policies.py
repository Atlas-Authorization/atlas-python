"""Policy acceptance: the Backend API surface, the policy source helpers (checked against
vectors computed with the TypeScript reference) and the ``pol`` claim."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx

from atlas_backend import (
    POLICY_SOURCE_PROTOCOL_VERSION,
    WEBHOOK_EVENT_POLICY_VERSION_PUBLISHED,
    WEBHOOK_EVENT_USER_POLICY_ACCEPTED,
    AsyncAtlasClient,
    AtlasClient,
    SessionClaims,
    sign_policy_source_event,
    verify_policy_feed_request,
)

API_URL = "https://api.example.test"
OK: dict[str, Any] = {"object": "x", "id": "x_1", "data": [], "has_more": False}
SECRET = "whsec_policy_source_test_secret"
NOW = 1_800_000_000_000
SIG_KEY = "veZ8K1cchaPsRfu/JPTU6fBWAsbUn/e/iaGPyP9nFoU="
SIG_ALL = "yJ3sPsHcT6fbi40UVNPScqsB9/5UomhRMTD/VcpNlWA="
SIG_EVENT = "m2QmhSM8RGmN8j3QS0wyVr1kqaHmykmswSug5wyHaVU="


def body_of(route: respx.Route) -> Any:
    content = route.calls.last.request.content
    return json.loads(content) if content else None


def _calls(c: AtlasClient) -> list[tuple[str, str, Any]]:
    return [
        ("GET", "/v1/policies", lambda: c.policies.list(include_retired=True)),
        ("POST", "/v1/policies", lambda: c.policies.create({"key": "tos", "title": "Terms"})),
        ("GET", "/v1/policies/tos", lambda: c.policies.get("tos")),
        ("PATCH", "/v1/policies/tos", lambda: c.policies.update("tos", {"status": "retired"})),
        ("DELETE", "/v1/policies/tos", lambda: c.policies.delete("tos")),
        ("GET", "/v1/policies/tos/versions", lambda: c.policies.versions.list("tos")),
        (
            "POST",
            "/v1/policies/tos/versions",
            lambda: c.policies.versions.create("tos", {"version": "v2", "publish": True}),
        ),
        ("GET", "/v1/policies/tos/versions/v2", lambda: c.policies.versions.get("tos", "v2")),
        (
            "PATCH",
            "/v1/policies/tos/versions/v2",
            lambda: c.policies.versions.update("tos", "v2", {"summary_of_changes": "x"}),
        ),
        ("DELETE", "/v1/policies/tos/versions/v2", lambda: c.policies.versions.delete("tos", "v2")),
        (
            "POST",
            "/v1/policies/tos/versions/v2/publish",
            lambda: c.policies.versions.publish("tos", "v2", {"effective_at": NOW}),
        ),
        (
            "POST",
            "/v1/policies/tos/versions/v2/retire",
            lambda: c.policies.versions.retire("tos", "v2"),
        ),
        (
            "GET",
            "/v1/policies/tos/acceptances",
            lambda: c.policies.list_acceptances("tos", version="v2", status="all", limit=5),
        ),
        ("GET", "/v1/users/u_1/policies", lambda: c.policies.for_user("u_1")),
        ("GET", "/v1/instance/policy_settings", lambda: c.policies.settings.get()),
        (
            "PATCH",
            "/v1/instance/policy_settings",
            lambda: c.policies.settings.update({"session_claim": True}),
        ),
        ("GET", "/v1/instance/policy_source", lambda: c.policy_source.get()),
        (
            "PUT",
            "/v1/instance/policy_source",
            lambda: c.policy_source.update({"enabled": True, "signing_secret": "s" * 20}),
        ),
        ("DELETE", "/v1/instance/policy_source", lambda: c.policy_source.delete()),
        ("POST", "/v1/instance/policy_source/test", lambda: c.policy_source.test()),
        ("POST", "/v1/instance/policy_source/sync", lambda: c.policy_source.sync()),
        (
            "GET",
            "/v1/instance/policy_source/deliveries",
            lambda: c.policy_source.list_deliveries(kind="fetch", status="failed", limit=2),
        ),
    ]


@respx.mock
def test_policy_surface_paths_methods_and_bodies() -> None:
    c = AtlasClient("sk_test", base_url=API_URL)
    routes = {}
    for method, path, call in _calls(c):
        route = respx.request(method, f"{API_URL}{path}").mock(
            return_value=httpx.Response(200, json=OK)
        )
        call()
        assert route.called, (method, path)
        routes[(method, path)] = route
    assert (
        routes[("GET", "/v1/policies")].calls.last.request.url.params["include_retired"] == "true"
    )
    assert body_of(routes[("POST", "/v1/policies")]) == {"key": "tos", "title": "Terms"}
    assert body_of(routes[("POST", "/v1/policies/tos/versions")]) == {
        "version": "v2",
        "publish": True,
    }
    assert body_of(routes[("POST", "/v1/policies/tos/versions/v2/publish")]) == {
        "effective_at": NOW
    }
    q = routes[("GET", "/v1/policies/tos/acceptances")].calls.last.request.url.params
    assert (q["version"], q["status"], q["limit"]) == ("v2", "all", "5")
    assert body_of(routes[("PUT", "/v1/instance/policy_source")])["enabled"] is True
    d = routes[("GET", "/v1/instance/policy_source/deliveries")].calls.last.request.url.params
    assert (d["kind"], d["status"], d["limit"]) == ("fetch", "failed", "2")


@respx.mock
def test_publish_without_body_sends_an_empty_object() -> None:
    route = respx.post(f"{API_URL}/v1/policies/tos/versions/v2/publish").mock(
        return_value=httpx.Response(200, json=OK)
    )
    AtlasClient("sk_test", base_url=API_URL).policies.versions.publish("tos", "v2")
    assert body_of(route) == {}


@respx.mock
def test_export_acceptances_csv_returns_text() -> None:
    route = respx.get(f"{API_URL}/v1/policies/tos/acceptances").mock(
        return_value=httpx.Response(200, text="user_id,policy\nu_1,tos\n")
    )
    out = AtlasClient("sk_test", base_url=API_URL).policies.export_acceptances_csv(
        "tos", status="accepted"
    )
    assert out == "user_id,policy\nu_1,tos\n"
    params = route.calls.last.request.url.params
    assert params["format"] == "csv" and params["status"] == "accepted"


@respx.mock
@pytest.mark.asyncio
async def test_async_policy_surface() -> None:
    respx.get(f"{API_URL}/v1/users/u_1/policies").mock(return_value=httpx.Response(200, json=OK))
    respx.put(f"{API_URL}/v1/instance/policy_source").mock(
        return_value=httpx.Response(200, json=OK)
    )
    async with AsyncAtlasClient("sk_test", base_url=API_URL) as c:
        assert (await c.policies.for_user("u_1"))["id"] == "x_1"
        await c.policy_source.update({"enabled": False})


@respx.mock
def test_consent_evidence_fields_pass_through() -> None:
    route = respx.post(f"{API_URL}/v1/users/u_1/consents").mock(
        return_value=httpx.Response(200, json=OK)
    )
    body = {
        "policy": "tos",
        "version": "v2",
        "policy_version_id": "polv_1",
        "content_sha256": "ab" * 32,
        "display": "scroll",
        "scrolled_to_end": True,
        "view_ms": 1200,
        "locale": "en",
    }
    AtlasClient("sk_test", base_url=API_URL).users.consents.record("u_1", body)  # type: ignore[arg-type]
    assert body_of(route) == body


def test_event_constants() -> None:
    assert WEBHOOK_EVENT_USER_POLICY_ACCEPTED == "user.policy_accepted"
    assert WEBHOOK_EVENT_POLICY_VERSION_PUBLISHED == "policy.version_published"
    assert POLICY_SOURCE_PROTOCOL_VERSION == "2026-10-24"


def _headers(sig: str, delivery_id: str = "evt_feed_1", ts: str = str(NOW)) -> dict[str, str]:
    return {
        "Atlas-Id": delivery_id,
        "Atlas-Timestamp": ts,
        "Atlas-Signature": sig,
        "Atlas-Policies-Version": POLICY_SOURCE_PROTOCOL_VERSION,
    }


def test_verify_feed_request_matches_the_typescript_vectors() -> None:
    r = verify_policy_feed_request(
        "GET", "/atlas/policies?key=tos", _headers("v1," + SIG_KEY), SECRET, now_ms=NOW + 1000
    )
    assert r.verified and r.key == "tos" and r.delivery_id == "evt_feed_1" and r.timestamp == NOW
    assert r.protocol_version == POLICY_SOURCE_PROTOCOL_VERSION
    full = verify_policy_feed_request(
        None,
        "/atlas/policies",
        _headers("v1," + SIG_ALL, "evt_feed_2"),
        SECRET,
        now_ms=NOW,
    )
    assert full.verified and full.key is None


def test_verify_feed_request_accepts_any_of_several_v1_values() -> None:
    sig = "v1,AAAA v2,zzzz v1," + SIG_KEY
    r = verify_policy_feed_request(
        "get", "/atlas/policies?key=tos", _headers(sig), SECRET, now_ms=NOW
    )
    assert r.verified


@pytest.mark.parametrize(
    ("headers", "path", "method", "now", "reason"),
    [
        ({}, "/atlas/policies?key=tos", "GET", NOW, "missing_headers"),
        (_headers("v2,abc"), "/atlas/policies?key=tos", "GET", NOW, "malformed_signature"),
        (
            _headers("v1," + SIG_KEY),
            "/atlas/policies?key=tos",
            "GET",
            NOW + 300_001,
            "stale_timestamp",
        ),
        (
            _headers("v1," + SIG_KEY),
            "/atlas/policies?key=tos",
            "GET",
            NOW - 300_001,
            "stale_timestamp",
        ),
        (
            _headers("v1," + SIG_KEY, ts="nope"),
            "/atlas/policies?key=tos",
            "GET",
            NOW,
            "stale_timestamp",
        ),
        (
            _headers("v1," + SIG_KEY),
            "/atlas/policies?key=privacy",
            "GET",
            NOW,
            "signature_mismatch",
        ),
        (_headers("v1," + SIG_KEY), "/atlas/policies?key=tos", "POST", NOW, "wrong_method"),
        (_headers("v1,!!!!"), "/atlas/policies?key=tos", "GET", NOW, "signature_mismatch"),
    ],
)
def test_verify_feed_request_refusals(
    headers: dict[str, str], path: str, method: str, now: int, reason: str
) -> None:
    r = verify_policy_feed_request(method, path, headers, SECRET, now_ms=now)
    assert not r.verified and r.reason == reason


def test_verify_feed_request_wrong_secret_and_tolerance_edge() -> None:
    h = _headers("v1," + SIG_KEY)
    assert not verify_policy_feed_request("GET", "/atlas/policies?key=tos", h, "other").verified
    assert verify_policy_feed_request(
        "GET", "/atlas/policies?key=tos", h, SECRET, now_ms=NOW + 300_000
    ).verified


def test_sign_event_matches_the_typescript_vector() -> None:
    signed = sign_policy_source_event(
        {
            "type": "policy.published",
            "key": "tos",
            "version": "2026-10-24",
            "occurred_at": "2026-10-24T00:00:00.000Z",
        },
        SECRET,
        event_id="evt_out_1",
        timestamp_ms=NOW + 123,
    )
    assert signed.body == (
        '{"occurred_at":"2026-10-24T00:00:00.000Z","type":"policy.published",'
        '"key":"tos","version":"2026-10-24"}'
    )
    assert signed.headers == {
        "atlas-id": "evt_out_1",
        "atlas-timestamp": str(NOW + 123),
        "atlas-signature": "v1," + SIG_EVENT,
    }


def test_sign_event_defaults() -> None:
    signed = sign_policy_source_event({"type": "policy.retired", "key": "tos"}, SECRET)
    body = json.loads(signed.body)
    assert body["type"] == "policy.retired" and body["occurred_at"].endswith("Z")
    assert signed.headers["atlas-id"].startswith("evt_")
    assert signed.headers["atlas-signature"].startswith("v1,")


def test_pol_session_claim_helpers() -> None:
    claims = SessionClaims.from_raw({"sub": "u_1", "pol": {"tos": "2026-10-24", "privacy": "3"}})
    assert claims.policies == {"tos": "2026-10-24", "privacy": "3"}
    assert claims.accepted_policy_version("tos") == "2026-10-24"
    assert claims.accepted_policy_version("other") is None
    assert SessionClaims.from_raw({"sub": "u_1"}).policies == {}
    assert SessionClaims.from_raw({"sub": "u_1", "pol": "x"}).policies == {}
