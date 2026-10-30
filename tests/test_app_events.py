"""2026-10-30 round: application webhooks, browser tickets, the test sign-in URL, Sign in
with Atlas, hosted pages, the privacy integration and the Standard Webhooks verifier."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
from typing import Any

import httpx
import respx

from atlas_backend import AsyncAtlasClient, AtlasClient, verify_standard_webhook

API_URL = "https://api.example.test"
ORG = "/v1/organizations/org_1/app_webhook_endpoints"

EXPECTED = [
    ("POST", "/v1/app_events"),
    ("GET", "/v1/app_events?organization_id=org_1&type=call.completed"),
    ("GET", "/v1/app_events/evt_1"),
    ("GET", "/v1/app_event_types"),
    ("POST", "/v1/app_event_types"),
    ("GET", "/v1/app_event_types/call.completed"),
    ("PATCH", "/v1/app_event_types/aet_1"),
    ("DELETE", "/v1/app_event_types/aet_1"),
    ("GET", ORG),
    ("POST", ORG),
    ("GET", f"{ORG}/we_1"),
    ("PATCH", f"{ORG}/we_1"),
    ("DELETE", f"{ORG}/we_1"),
    ("POST", f"{ORG}/we_1/rotate_secret"),
    ("POST", f"{ORG}/we_1/reveal_secret"),
    ("POST", f"{ORG}/we_1/test?wait=10s"),
    ("GET", f"{ORG}/we_1/deliveries?limit=5"),
    ("POST", f"{ORG}/we_1/deliveries/msg_1/redeliver"),
    ("POST", f"{ORG}/we_1/replay"),
    ("GET", "/v1/organizations/org_1/app_event_types"),
    ("POST", "/v1/sessions"),
    ("POST", "/v1/testing/sign_in_url"),
    ("GET", "/v1/instance/sign_in_with_atlas"),
    ("PATCH", "/v1/instance/sign_in_with_atlas"),
    ("GET", "/v1/instance/hosted_pages"),
    ("PATCH", "/v1/instance/hosted_pages"),
    ("GET", "/v1/instance/privacy_integrations"),
    ("POST", "/v1/instance/privacy_integrations/connect"),
]


def _calls(c: Any) -> list[Any]:
    """Every call in EXPECTED order; each returns the response (or an awaitable of it)."""
    ev, ep = c.app_events, c.app_events.endpoints
    return [
        lambda: ev.publish(
            {"organization_id": "org_1", "type": "call.completed", "data": {"call_id": "c1"}},
            idempotency_key="c1",
        ),
        lambda: ev.list("org_1", type="call.completed"),
        lambda: ev.get("evt_1"),
        lambda: ev.types.list(),
        lambda: ev.types.create({"type": "call.completed"}),
        lambda: ev.types.get("call.completed"),
        lambda: ev.types.update("aet_1", {"deprecated": True}),
        lambda: ev.types.delete("aet_1"),
        lambda: ep.list("org_1"),
        lambda: ep.create("org_1", {"url": "https://hooks.example.com/a"}),
        lambda: ep.get("org_1", "we_1"),
        lambda: ep.update("org_1", "we_1", {"active": False}),
        lambda: ep.delete("org_1", "we_1"),
        lambda: ep.rotate_secret("org_1", "we_1"),
        lambda: ep.reveal_secret("org_1", "we_1"),
        lambda: ep.test("org_1", "we_1", wait="10s"),
        lambda: ep.deliveries("org_1", "we_1", limit=5),
        lambda: ep.redeliver("org_1", "we_1", "msg_1"),
        lambda: ep.replay("org_1", "we_1", {"since": "failing_since"}),
        lambda: ep.app_event_types("org_1"),
        lambda: c.sessions.create_browser_ticket(
            "user_1", redirect_url="https://app.example.com/home", expires_in_seconds=120
        ),
        lambda: c.testing.create_sign_in_url("user_1", redirect_url="http://localhost:3000"),
        lambda: c.instance.sign_in_with_atlas.get(),
        lambda: c.instance.sign_in_with_atlas.update({"enabled": True}),
        lambda: c.instance.hosted_pages.get(),
        lambda: c.instance.hosted_pages.update({"sign_in_url": None}),
        lambda: c.privacy.integration.get(),
        lambda: c.privacy.integration.connect({"preset": "custom"}),
    ]


def _got(mock: respx.MockRouter) -> list[tuple[str, str]]:
    return [(r.request.method, r.request.url.raw_path.decode()) for r in mock.calls]


def _body(mock: respx.MockRouter, i: int) -> Any:
    return json.loads(mock.calls[i].request.content)


def _check_bodies(mock: respx.MockRouter) -> None:
    assert mock.calls[0].request.headers["Idempotency-Key"] == "c1"
    assert _body(mock, 20) == {
        "user_id": "user_1",
        "mode": "browser_ticket",
        "redirect_url": "https://app.example.com/home",
        "expires_in_seconds": 120,
    }
    assert _body(mock, 21) == {"user_id": "user_1", "redirect_url": "http://localhost:3000"}
    assert _body(mock, 25) == {"sign_in_url": None}


def test_sync_routes_and_bodies() -> None:
    with respx.mock(base_url=API_URL) as mock:
        mock.route().mock(return_value=httpx.Response(200, json={}))
        for call in _calls(AtlasClient("sk_test", base_url=API_URL)):
            call()
        assert _got(mock) == EXPECTED
        _check_bodies(mock)


def test_async_routes_and_bodies() -> None:
    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            mock.route().mock(return_value=httpx.Response(200, json={}))
            for call in _calls(AsyncAtlasClient("sk_test", base_url=API_URL)):
                await call()
            assert _got(mock) == EXPECTED
            _check_bodies(mock)

    asyncio.run(run())


# --------------------------------------------------------------------------- #
# Standard Webhooks                                                           #
# --------------------------------------------------------------------------- #

KEY = b"0123456789abcdef0123456789abcdef"
SECRET = "whsec_" + base64.b64encode(KEY).decode()
NOW = 1_790_000_000
BODY = json.dumps({"type": "call.completed", "data": {"call_id": "c1"}})


def _sig(key: bytes, msg_id: str, ts: int, body: str) -> str:
    mac = hmac.new(key, f"{msg_id}.{ts}.{body}".encode(), hashlib.sha256).digest()
    return "v1," + base64.b64encode(mac).decode()


def _headers(signature: str, ts: int = NOW) -> dict[str, str]:
    return {"webhook-id": "evt_1", "webhook-timestamp": str(ts), "webhook-signature": signature}


def test_standard_webhook_verifies() -> None:
    result = verify_standard_webhook(
        BODY, _headers(_sig(KEY, "evt_1", NOW, BODY)), SECRET, now_s=NOW + 5
    )
    assert result.verified
    assert result.delivery_id == "evt_1"
    assert result.timestamp == NOW
    assert result.event == {"type": "call.completed", "data": {"call_id": "c1"}}


def test_standard_webhook_accepts_any_signature_while_rotating() -> None:
    old = _sig(b"previous-key-previous-key-000000", "evt_1", NOW, BODY)
    sig = f"{old} {_sig(KEY, 'evt_1', NOW, BODY)}"
    assert verify_standard_webhook(BODY.encode(), _headers(sig), SECRET, now_s=NOW).verified


def test_standard_webhook_rejects_a_bad_signature() -> None:
    sig = _sig(KEY, "evt_1", NOW, BODY)
    tampered = BODY.replace("c1", "c2")
    result = verify_standard_webhook(tampered, _headers(sig), SECRET, now_s=NOW)
    assert (result.verified, result.reason) == (False, "signature_mismatch")
    result = verify_standard_webhook(BODY, _headers("v1,AAAA"), SECRET, now_s=NOW)
    assert result.reason == "signature_mismatch"
    result = verify_standard_webhook(BODY, _headers("v2,AAAA"), SECRET, now_s=NOW)
    assert result.reason == "malformed_signature"


def test_standard_webhook_rejects_a_stale_timestamp() -> None:
    sig = _sig(KEY, "evt_1", NOW, BODY)
    result = verify_standard_webhook(BODY, _headers(sig), SECRET, now_s=NOW + 301)
    assert (result.verified, result.reason) == (False, "stale_timestamp")
    # Milliseconds are not seconds: a ms timestamp is far in the future.
    ms = _sig(KEY, "evt_1", NOW * 1000, BODY)
    assert verify_standard_webhook(BODY, _headers(ms, NOW * 1000), SECRET, now_s=NOW).reason == (
        "stale_timestamp"
    )


def test_standard_webhook_rejects_missing_headers() -> None:
    headers = _headers(_sig(KEY, "evt_1", NOW, BODY))
    for name in list(headers):
        partial = {k: v for k, v in headers.items() if k != name}
        result = verify_standard_webhook(BODY, partial, SECRET, now_s=NOW)
        assert (result.verified, result.reason) == (False, "missing_headers")
