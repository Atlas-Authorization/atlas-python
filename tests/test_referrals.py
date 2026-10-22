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
    REFERRAL_OP_ENDPOINTS,
    REFERRAL_PROTOCOL_VERSION,
    REFERRAL_PROTOCOL_VERSION_HEADER,
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


# --------------------------------------------------------------------------- #
# Referral attribution v2                                                      #
# --------------------------------------------------------------------------- #

PING = {
    "ok": True,
    "at": 7,
    "http_status": 200,
    "error_code": None,
    "error": None,
    "latency_ms": 31,
    "connection_id": "conn_1",
    "program_id": "prg_1",
    "program_name": "Acme partners",
    "org_name": "Acme",
    "auto_enroll_users": True,
    "server_time": "2026-10-21T12:00:00.000Z",
    "clock_skew_ms": 90_000,
    "clock_skew_warning": True,
}

BACKFILL = {
    "object": "referral_backfill",
    "id": "rbf_1",
    "status": "running",
    "since": 1_790_000_000_000,
    "code_metadata_path": "public_metadata.referral_code",
    "codes_given": 1,
    "users_scanned": 12,
    "users_skipped": 2,
    "calls_queued": 10,
    "truncated": False,
    "next_since": None,
    "calls": {"pending": 10, "succeeded": 0, "failed": 0, "skipped": 0, "held": 0},
    "created_at": 1,
    "finished_at": None,
}

HOOK = {
    "object": "before_user_create_hook",
    "enabled": True,
    "url": "https://app.example.com/hooks/before-create",
    "signing_secret_set": True,
    "timeout_ms": 3000,
    "last_call": {"at": 3, "status": "ok", "error": None},
    "updated_at": 3,
}


@respx.mock
def test_v2_settings_fields_and_ping_test() -> None:
    settings = {
        **SETTINGS,
        "provider": "referally",
        "tracking_token": "tt_public_1",
        "code_lookup_url": "https://referrals.example.com/lookup/{code}",
        "signup_code_field": True,
        "forward_lifecycle": True,
        "mirror_to_public_metadata": False,
        "include_referral_claims": True,
        "connection": {
            **SETTINGS["connection"],
            "last_ping": PING,
            "alert": {"code": "signature_rejected", "message": "401", "at": 9, "call_id": "rfc_9"},
        },
    }
    respx.get(REFERRALS).mock(return_value=httpx.Response(200, json=settings))
    patch = respx.patch(REFERRALS).mock(return_value=httpx.Response(200, json=settings))
    respx.post(f"{REFERRALS}/test").mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "http_status": 200,
                "latency_ms": 31,
                "method": "ping",
                "ping": PING,
                "warnings": ["clock skew"],
            },
        )
    )
    referrals = client().instance.referrals

    view = referrals.get()
    assert view["tracking_token"] == "tt_public_1"
    connection = view["connection"]
    assert connection is not None
    assert connection["alert"] is not None and connection["alert"]["code"] == "signature_rejected"
    assert connection["last_ping"] is not None and connection["last_ping"]["clock_skew_warning"]

    referrals.update(
        {
            "provider": "referally",
            "tracking_token": "tt_public_1",
            "code_lookup_url": None,
            "signup_code_field": True,
            "forward_lifecycle": False,
            "mirror_to_public_metadata": True,
            "include_referral_claims": True,
        }
    )
    assert body_of(patch) == {
        "provider": "referally",
        "tracking_token": "tt_public_1",
        "code_lookup_url": None,
        "signup_code_field": True,
        "forward_lifecycle": False,
        "mirror_to_public_metadata": True,
        "include_referral_claims": True,
    }
    tested = referrals.test()
    assert tested["method"] == "ping" and tested["warnings"] == ["clock skew"]
    ping = tested["ping"]
    assert ping is not None and ping["org_name"] == "Acme"


@respx.mock
def test_v2_call_log_paging_and_fields() -> None:
    call = {
        **CALL,
        "kind": "alias",
        "error_code": "signature_rejected",
        "latency_ms": 44,
        "request_id": "req_1",
        "response": {"ok": False},
        "highlights": {"matched_via": "code", "partner_external_ref": "cust_9", "notes": ["n"]},
        "batch_id": "rbf_1",
    }
    calls = respx.get(f"{REFERRALS}/calls").mock(
        return_value=httpx.Response(200, json={"object": "list", "data": [call], "has_more": True})
    )
    page = client().instance.referrals.list_calls(
        limit=1000, error_code="signature_rejected", starting_after="rfc_0"
    )
    assert dict(calls.calls.last.request.url.params) == {
        "limit": "1000",
        "error_code": "signature_rejected",
        "starting_after": "rfc_0",
    }
    assert page["has_more"] is True
    got = page["data"][0]
    assert got["error_code"] == "signature_rejected" and got["batch_id"] == "rbf_1"
    assert got["highlights"]["notes"] == ["n"]


@respx.mock
def test_v2_retry_failed_simulate_backfill() -> None:
    retry = respx.post(f"{REFERRALS}/calls/retry_failed").mock(
        return_value=httpx.Response(200, json={"object": "referral_retry", "requeued": 4})
    )
    simulate = respx.post(f"{REFERRALS}/simulate").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "referral_simulation",
                "ok": True,
                "call_id": "rfc_5",
                "customer_ref": "atlas_test_abc",
                "http_status": 200,
                "latency_ms": 20,
                "result": {
                    "referral": {
                        "partner_id": "pn_1",
                        "partner_external_ref": "cust_9",
                        "matched_via": "code",
                        "status": "active",
                    },
                    "partner": None,
                    "notes": ["matched code"],
                },
                "response": {"referral": {}},
                "error": None,
            },
        )
    )
    backfill = respx.post(f"{REFERRALS}/backfill").mock(
        return_value=httpx.Response(200, json=BACKFILL)
    )
    get_backfill = respx.get(f"{REFERRALS}/backfill/rbf_1").mock(
        return_value=httpx.Response(200, json={**BACKFILL, "status": "completed"})
    )
    referrals = client().instance.referrals

    assert (
        referrals.retry_failed(error_code="signature_rejected", idempotency_key="k1")["requeued"]
        == 4
    )
    assert body_of(retry) == {"error_code": "signature_rejected"}
    assert retry.calls.last.request.headers["idempotency-key"] == "k1"
    referrals.retry_failed()
    assert body_of(retry) == {}

    sim = referrals.simulate(code="ACME10")
    assert body_of(simulate) == {"code": "ACME10"}
    result = sim["result"]
    assert result is not None and result["notes"] == ["matched code"]
    referrals.simulate()
    assert body_of(simulate) == {}

    job = referrals.backfill(
        {"since": "2026-01-01", "codes": {"cust_1": "ACME10"}}, idempotency_key="k2"
    )
    assert body_of(backfill) == {"since": "2026-01-01", "codes": {"cust_1": "ACME10"}}
    assert backfill.calls.last.request.headers["idempotency-key"] == "k2"
    assert job["calls"]["pending"] == 10
    assert referrals.get_backfill("rbf_1")["status"] == "completed"
    assert get_backfill.called


@respx.mock
def test_v2_user_referral_result_set_external_id_and_fields() -> None:
    result = {
        "object": "user_referral",
        "user_id": "user_1",
        "status": "attributed",
        "customer_ref": "cust_1",
        "partner_id": "pn_1",
        "partner_external_ref": "cust_9",
        "referrer_user_id": "user_9",
        "matched_via": "code",
        "referral_status": "active",
        "notes": ["matched code"],
        "referral_code": "ada-1",
        "referral_link": None,
        "context": {"code": "ACME10"},
        "risk_level": "low",
        "flagged": False,
        "hold_reason": None,
        "signed_up_at": 1,
        "updated_at": 2,
    }
    respx.get(f"{API_URL}/v1/users/user_1/referral").mock(
        return_value=httpx.Response(200, json=result)
    )
    user = {
        "object": "user",
        "id": "user_1",
        "external_id": "cust_1",
        "referral": {
            "status": "pending",
            "partner_id": None,
            "partner_external_ref": None,
            "referrer_external_id": None,
            "referrer_user_id": None,
            "matched_via": None,
            "referral_status": None,
            "notes": [],
            "risk_level": None,
            "flagged": False,
        },
    }
    update = respx.patch(f"{API_URL}/v1/users/user_1").mock(
        return_value=httpx.Response(200, json=user)
    )
    atlas = client()

    got = atlas.instance.referrals.get_for_user("user_1")
    assert got["status"] == "attributed" and got["referral_status"] == "active"
    assert got["customer_ref"] == "cust_1"

    updated = atlas.users.set_external_id("user_1", "cust_1")
    assert body_of(update) == {"external_id": "cust_1"}
    referral = updated["referral"]
    assert referral is not None and referral["status"] == "pending"
    atlas.users.set_external_id("user_1", None)
    assert body_of(update) == {"external_id": None}


@respx.mock
def test_v2_before_user_create_hook() -> None:
    url = f"{API_URL}/v1/instance/hooks/before_user_create"
    get = respx.get(url).mock(return_value=httpx.Response(200, json=HOOK))
    patch = respx.patch(url).mock(return_value=httpx.Response(200, json=HOOK))
    test = respx.post(f"{url}/test").mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "latency_ms": 12,
                "answer": {
                    "external_id": "cust_1",
                    "public_metadata": None,
                    "private_metadata_set": True,
                    "unsafe_metadata": None,
                },
            },
        )
    )
    hooks = client().instance.hooks

    hook = hooks.get_before_user_create()
    assert get.called and hook["last_call"] is not None
    hooks.update_before_user_create(
        {"enabled": True, "url": HOOK["url"], "signing_secret": "s" * 32, "timeout_ms": 2000},
        idempotency_key="k3",
    )
    assert body_of(patch) == {
        "enabled": True,
        "url": HOOK["url"],
        "signing_secret": "s" * 32,
        "timeout_ms": 2000,
    }
    assert patch.calls.last.request.headers["idempotency-key"] == "k3"
    tested = hooks.test_before_user_create()
    assert tested["answer"]["external_id"] == "cust_1"
    assert test.calls.last.request.content in (b"", None)


@respx.mock
def test_v2_async() -> None:
    respx.post(f"{REFERRALS}/simulate").mock(
        return_value=httpx.Response(
            200, json={"object": "referral_simulation", "ok": False, "customer_ref": "atlas_test_x"}
        )
    )
    respx.get(f"{API_URL}/v1/instance/hooks/before_user_create").mock(
        return_value=httpx.Response(200, json=HOOK)
    )
    update = respx.patch(f"{API_URL}/v1/users/user_1").mock(
        return_value=httpx.Response(200, json={"object": "user", "id": "user_1"})
    )

    async def run() -> None:
        async with AsyncAtlasClient("sk_test_x", base_url=API_URL) as atlas:
            sim = await atlas.instance.referrals.simulate(code="ACME10")
            assert sim["ok"] is False
            hook = await atlas.instance.hooks.get_before_user_create()
            assert hook["enabled"] is True
            await atlas.users.set_external_id("user_1", "cust_1")

    asyncio.run(run())
    assert body_of(update) == {"external_id": "cust_1"}


ALIAS = json.dumps(
    {"op": "alias", "customerRef": "cust_1", "fromCustomerRef": "user_1", "toCustomerRef": "cust_1"}
)
USER = json.dumps(
    {"op": "user", "customerRef": "cust_1", "email": "a@example.com", "status": "suspended"}
)
PING_CALL = json.dumps({"op": "ping", "customerRef": REFERRAL_CONNECTION_TEST_REF})


def test_verify_alias_user_ping_and_version_header() -> None:
    alias = verify(ALIAS, "/atlas/aliases")
    assert alias.verified and alias.op == "alias" and alias.customer_ref == "cust_1"
    assert alias.payload is not None and alias.payload["fromCustomerRef"] == "user_1"
    user = verify(USER, "/atlas/users")
    assert user.verified and user.op == "user"
    assert user.payload is not None and user.payload["status"] == "suspended"
    ping = verify(PING_CALL, "/atlas/ping")
    assert ping.verified and ping.op == "ping" and not ping.test
    assert ping.customer_ref == REFERRAL_CONNECTION_TEST_REF
    assert verify(PING_CALL, expected_op="ping").verified
    # Replays against another endpoint are refused.
    assert verify(ALIAS, "/atlas/users").reason == "op_mismatch"
    assert verify(PING_CALL, "/atlas/export").reason == "op_mismatch"
    assert verify(USER, expected_op="alias").reason == "op_mismatch"
    # The version header is read when sent, and is not required.
    assert ping.protocol_version is None
    headers = {**signed("rfc_2", PING_CALL), "Atlas-Referrals-Version": REFERRAL_PROTOCOL_VERSION}
    versioned = verify_referral_request(PING_CALL, headers, SECRET, path="/ping", now_ms=NOW)
    assert versioned.protocol_version == "2026-10-21"
    assert REFERRAL_PROTOCOL_VERSION_HEADER == "atlas-referrals-version"
    assert referral_op_for_path("/a/aliases") == "alias"
    assert referral_op_for_path("/a/users/") == "user"
    assert referral_op_for_path("/a/ping?x=1") == "ping"
    assert set(REFERRAL_OP_ENDPOINTS) == {
        "signup",
        "erase",
        "export",
        "partner",
        "signal",
        "alias",
        "user",
        "ping",
    }
