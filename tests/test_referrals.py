"""Referral attribution: the instance settings, connection test and call log, the
user referral fields and fraud flag, and the referral protocol verifier for
referral platforms.

All HTTP is mocked with respx; each test asserts the method, path, query and body
the SDK sends, and that the response decodes.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json

import httpx
import respx

from atlas_backend import (
    REFERRAL_CONNECTION_TEST_REF,
    AsyncAtlasClient,
    AtlasClient,
    AtlasError,
    ErrorCode,
    ReferralOp,
    ReferralVerification,
    referral_op_for_path,
    verify_referral_request,
)

API_URL = "https://api.example.test"
REFERRALS = f"{API_URL}/v1/instance/referrals"

SETTINGS = {
    "object": "referral_settings",
    "enabled": True,
    "provider": "webhook",
    "endpoint_url": "https://referrals.example.com/atlas",
    "program_id": None,
    "connection_id": None,
    "signing_secret_set": True,
    "api_key_set": False,
    "url_params": ["ref", "via", "aff"],
    "context_cookie": None,
    "consent_category": "referrals",
    "consent_fallback_category": "marketing",
    "auto_enroll_users": True,
    "link_template": "https://app.example.com/join?ref={code}",
    "timeout_ms": 3000,
    "security": {
        "challenge_referred_signups": "always",
        "on_high_risk": "flag",
        "hold_until_email_verified": False,
        "max_referred_signups_per_ip_hour": 5,
    },
    "missing": [],
    "connection": {
        "last_test": {"ok": True, "at": 1, "http_status": 404, "error": None},
        "failed_calls_7d": 0,
        "retrying_calls": 0,
        "last_success_at": 1,
    },
    "providers": [
        {
            "id": "webhook",
            "name": "Atlas referral protocol (any platform)",
            "capabilities": {
                "signup": True,
                "erase": True,
                "export": True,
                "partner": True,
                "auto_enroll": True,
                "signal": True,
            },
            "needs": ["endpoint_url", "signing_secret"],
            "default_context_cookie": None,
            "docs_url": None,
        }
    ],
    "updated_at": 1,
}

CALL = {
    "object": "referral_call",
    "id": "rfc_1",
    "kind": "signup",
    "status": "succeeded",
    "outcome": "referred",
    "customer_ref": "user_1",
    "user_id": "user_1",
    "http_status": 200,
    "last_error": None,
    "attempts": 2,
    "next_attempt_at": None,
    "risk": {"level": "low", "score": 5, "signals": [], "captcha": "passed", "emailVerified": True},
    "payload": {"customerRef": "user_1"},
    "created_at": 1,
    "updated_at": 2,
}


def client() -> AtlasClient:
    return AtlasClient("sk_test_x", base_url=API_URL)


def body_of(route: respx.Route) -> object:
    return json.loads(route.calls.last.request.content)


@respx.mock
def test_settings_get_update_test() -> None:
    get = respx.get(REFERRALS).mock(return_value=httpx.Response(200, json=SETTINGS))
    patch = respx.patch(REFERRALS).mock(return_value=httpx.Response(200, json=SETTINGS))
    test = respx.post(f"{REFERRALS}/test").mock(
        return_value=httpx.Response(200, json={"ok": True, "http_status": 404, "latency_ms": 12})
    )
    referrals = client().instance.referrals

    view = referrals.get()
    assert get.called
    assert view["security"]["on_high_risk"] == "flag"
    assert view["providers"][0]["capabilities"]["signal"] is True

    referrals.update(
        {
            "enabled": True,
            "signing_secret": "x" * 32,
            "link_template": None,
            "security": {"on_high_risk": "hold"},
        },
        idempotency_key="idem-1",
    )
    assert body_of(patch) == {
        "enabled": True,
        "signing_secret": "x" * 32,
        "link_template": None,
        "security": {"on_high_risk": "hold"},
    }
    assert patch.calls.last.request.headers["idempotency-key"] == "idem-1"

    assert referrals.test()["ok"] is True
    assert test.calls.last.request.content in (b"", None)


@respx.mock
def test_call_log_and_retry() -> None:
    calls = respx.get(f"{REFERRALS}/calls").mock(
        return_value=httpx.Response(200, json={"object": "list", "data": [CALL], "has_more": False})
    )
    retry = respx.post(f"{REFERRALS}/calls/rfc_1/retry").mock(
        return_value=httpx.Response(200, json=CALL)
    )
    referrals = client().instance.referrals

    page = referrals.list_calls(limit=10, status="failed", kind="signup", user_id="user_1")
    assert dict(calls.calls.last.request.url.params) == {
        "limit": "10",
        "status": "failed",
        "kind": "signup",
        "user_id": "user_1",
    }
    assert page["data"][0]["risk"]["emailVerified"] is True
    referrals.list_calls()
    assert str(calls.calls.last.request.url) == f"{REFERRALS}/calls"

    assert referrals.retry_call("rfc_1", idempotency_key="idem-2")["outcome"] == "referred"
    assert retry.calls.last.request.headers["idempotency-key"] == "idem-2"


@respx.mock
def test_user_referral_fields_create_update_and_flag() -> None:
    user = {
        "object": "user",
        "id": "user_1",
        "referral": {
            "partner_id": "pn_1",
            "referrer_external_id": "cust_9",
            "referrer_user_id": "user_9",
            "matched_via": "code",
            "status": "lead",
            "risk_level": "low",
            "flagged": False,
        },
        "referral_code": "ada-1",
        "referral_link": "https://app.example.com/join?ref=ada-1",
    }
    create = respx.post(f"{API_URL}/v1/users").mock(return_value=httpx.Response(200, json=user))
    update = respx.patch(f"{API_URL}/v1/users/user_1").mock(
        return_value=httpx.Response(200, json=user)
    )
    flag = respx.post(f"{API_URL}/v1/users/user_1/referral/flag").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "user_referral",
                "user_id": "user_1",
                "status": "flagged",
                "flagged": True,
                "flag_reason": "ring",
                "flagged_at": 5,
                "risk_level": "high",
            },
        )
    )
    users = client().users

    created = users.create(
        {
            "email_address": "a@example.com",
            "referral": {"code": "ACME10", "click_id": "clk_123"},
            "referral_code": "ada-1",
        }
    )
    assert body_of(create) == {
        "email_address": "a@example.com",
        "referral": {"code": "ACME10", "click_id": "clk_123"},
        "referral_code": "ada-1",
    }
    referral = created["referral"]
    assert referral is not None and referral["referrer_user_id"] == "user_9"

    users.update("user_1", {"referral_code": None})
    assert body_of(update) == {"referral_code": None}

    flagged = users.flag_referral("user_1", reason="ring", idempotency_key="idem-3")
    assert body_of(flag) == {"reason": "ring"}
    assert flag.calls.last.request.headers["idempotency-key"] == "idem-3"
    assert flagged["flagged"] is True
    users.flag_referral("user_1")
    assert body_of(flag) == {}


@respx.mock
def test_referral_error_codes() -> None:
    respx.patch(f"{API_URL}/v1/users/user_1").mock(
        return_value=httpx.Response(
            409,
            json={
                "errors": [
                    {"code": "REFERRAL_CODE_TAKEN", "message": "taken", "param": "referral_code"}
                ]
            },
        )
    )
    try:
        client().users.update("user_1", {"referral_code": "ada-1"})
    except AtlasError as err:
        assert err.status == 409
        assert err.has_code(ErrorCode.REFERRAL_CODE_TAKEN)
    else:  # pragma: no cover
        raise AssertionError("expected AtlasError")
    assert ErrorCode.REFERRALS_NOT_CONFIGURED == "REFERRALS_NOT_CONFIGURED"


@respx.mock
def test_async_referrals() -> None:
    respx.get(REFERRALS).mock(return_value=httpx.Response(200, json=SETTINGS))
    flag = respx.post(f"{API_URL}/v1/users/user_1/referral/flag").mock(
        return_value=httpx.Response(200, json={"object": "user_referral", "user_id": "user_1"})
    )

    async def run() -> None:
        async with AsyncAtlasClient("sk_test_x", base_url=API_URL) as atlas:
            view = await atlas.instance.referrals.get()
            assert view["enabled"] is True
            await atlas.users.flag_referral("user_1", reason="ring")

    asyncio.run(run())
    assert body_of(flag) == {"reason": "ring"}


# --------------------------------------------------------------------------- #
# The referral protocol, for referral platforms                                #
# --------------------------------------------------------------------------- #

SECRET = "referral_signing_secret_0123456789"
NOW = 1_792_584_000_000


def signed(call_id: str, body: str, secret: str = SECRET, ts: int = NOW) -> dict[str, str]:
    mac = hmac.new(secret.encode(), f"{call_id}.{ts}.{body}".encode(), hashlib.sha256).digest()
    return {
        "atlas-id": call_id,
        "atlas-timestamp": str(ts),
        "atlas-signature": "v1," + base64.b64encode(mac).decode(),
        "Idempotency-Key": "signup:user_1",
    }


SIGNUP = json.dumps(
    {
        "op": "signup",
        "customerRef": "user_1",
        "emailHash": None,
        "ip": "203.0.113.7",
        "ua": "Mozilla/5.0",
        "signedUpAt": "2026-10-21T11:59:00.000Z",
        "programId": None,
        "autoEnroll": True,
        "referral": {
            "code": "ACME10",
            "clickId": None,
            "anonId": None,
            "capturedAt": "2026-10-21T11:58:00.000Z",
            "consent": "not_required",
        },
        "risk": {
            "level": "low",
            "score": 0,
            "signals": [],
            "captcha": "passed",
            "emailVerified": False,
        },
        "rejected": None,
    }
)
ERASE = json.dumps({"op": "erase", "customerRef": "user_1"})
EXPORT_TEST = json.dumps(
    {"op": "export", "customerRef": REFERRAL_CONNECTION_TEST_REF, "test": True}
)
EXPORT_USER = json.dumps({"op": "export", "customerRef": "user_1", "test": False})
PARTNER = json.dumps({"op": "partner", "customerRef": "user_1", "code": "ada-1", "emailHash": None})
SIGNAL = json.dumps(
    {
        "op": "signal",
        "customerRef": "user_1",
        "type": "fraud_confirmed",
        "occurredAt": "x",
        "data": {},
    }
)


def verify(
    body: str, path: str | None = None, expected_op: ReferralOp | None = None
) -> ReferralVerification:
    return verify_referral_request(
        body, signed("rfc_1", body), SECRET, path=path, expected_op=expected_op, now_ms=NOW
    )


def test_verify_signup_on_its_endpoint() -> None:
    res = verify(SIGNUP, "/atlas/signups")
    assert res.verified and res.op == "signup"
    assert res.customer_ref == "user_1"
    assert res.delivery_id == "rfc_1"
    assert res.idempotency_key == "signup:user_1"
    assert res.payload is not None and res.payload["referral"]["code"] == "ACME10"


def test_verify_export_exposes_test() -> None:
    test = verify(EXPORT_TEST, "https://referrals.example.com/atlas/export")
    assert test.verified and test.op == "export" and test.test
    assert test.customer_ref == REFERRAL_CONNECTION_TEST_REF
    user = verify(EXPORT_USER, "/export")
    assert user.verified and not user.test and user.customer_ref == "user_1"


def test_verify_erase_partner_signal() -> None:
    assert (verify(ERASE, "/erase").op, verify(ERASE, "/erase").customer_ref) == ("erase", "user_1")
    partner = verify(PARTNER, "/atlas/partners/")
    assert partner.op == "partner" and partner.payload == json.loads(PARTNER)
    signal = verify(SIGNAL, expected_op="signal")
    assert signal.op == "signal"
    assert signal.payload is not None and signal.payload["type"] == "fraud_confirmed"
    # Neither path nor expected operation: the signed op decides.
    assert verify(PARTNER).op == "partner"


def test_verify_refuses_replay_against_another_endpoint() -> None:
    assert verify(EXPORT_USER, "/atlas/erase").reason == "op_mismatch"
    assert verify(SIGNUP, "/atlas/partners").reason == "op_mismatch"
    assert verify(ERASE, expected_op="export").reason == "op_mismatch"
    assert verify(ERASE, "/erase", expected_op="signal").reason == "op_mismatch"
    assert verify(ERASE, "/atlas/partners/user_1").reason == "unknown_endpoint"
    assert verify(ERASE, "/atlas/webhooks").reason == "unknown_endpoint"


def test_verify_refuses_missing_or_unknown_op_and_bad_bodies() -> None:
    assert verify(json.dumps({"customerRef": "user_1"}), "/erase").reason == "missing_op"
    assert verify(json.dumps({"op": "delete"}), "/erase").reason == "unknown_op"
    assert verify(json.dumps({"op": 7}), "/erase").reason == "unknown_op"
    assert verify("", "/export").reason == "malformed_body"
    assert verify("[1]", "/export").reason == "malformed_body"


def test_verify_signature_refusals() -> None:
    wrong = verify_referral_request(
        SIGNUP, signed("rfc_7", SIGNUP, secret="another_secret_0123456789"), SECRET, now_ms=NOW
    )
    assert (wrong.verified, wrong.reason) == (False, "signature_mismatch")
    tampered = verify_referral_request(SIGNUP + " ", signed("rfc_7", SIGNUP), SECRET, now_ms=NOW)
    assert tampered.reason == "signature_mismatch"
    stale = verify_referral_request(
        SIGNUP, signed("rfc_7", SIGNUP, ts=NOW - 600_000), SECRET, now_ms=NOW
    )
    assert stale.reason == "stale_timestamp"
    assert verify_referral_request("", {}, SECRET, now_ms=NOW).reason == "missing_headers"
    raw = verify_referral_request(
        SIGNUP.encode(), signed("rfc_8", SIGNUP), SECRET, path="/signups", now_ms=NOW
    )
    assert raw.verified


def test_referral_op_for_path() -> None:
    assert referral_op_for_path("/a/signups") == "signup"
    assert referral_op_for_path("https://x.example.com/b/partners?x=1") == "partner"
    assert referral_op_for_path("/signals/") == "signal"
    assert referral_op_for_path("/nope") is None
