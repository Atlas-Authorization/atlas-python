"""API key spend caps and usage metering, session keep-alive, and ``notify`` on
user create and import.

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

STATE = {
    "unit": "usd_cents",
    "period": "month",
    "amount": 5000,
    "used": 12,
    "remaining": 4988,
    "window_start": 1790000000000,
    "resets_at": 1792000000000,
}
COUNTER = {
    "unit": "usd_cents",
    "period": "month",
    "used": 12,
    "window_start": 1790000000000,
    "resets_at": 1792000000000,
}
LIMIT = {"unit": "usd_cents", "amount": 5000, "period": "month"}


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


def body_of(route: respx.Route) -> object:
    return json.loads(route.calls.last.request.content)


@respx.mock
def test_create_sends_limits_and_decodes_usage() -> None:
    route = respx.post(f"{API_URL}/v1/api_keys").mock(
        return_value=httpx.Response(
            201,
            json={
                "object": "api_key",
                "id": "eak_1",
                "secret": "ak_x",
                "limits": [LIMIT],
                "usage": [STATE],
            },
        )
    )
    key = client().api_keys.create(
        {"subject_type": "user", "subject_id": "user_1", "limits": [LIMIT]}
    )
    assert body_of(route) == {"subject_type": "user", "subject_id": "user_1", "limits": [LIMIT]}
    assert key["limits"] == [LIMIT]
    assert key["usage"][0]["remaining"] == 4988


@respx.mock
def test_update_clears_limits_with_none() -> None:
    route = respx.patch(f"{API_URL}/v1/api_keys/eak_1").mock(
        return_value=httpx.Response(
            200, json={"object": "api_key", "id": "eak_1", "limits": None, "usage": []}
        )
    )
    key = client().api_keys.update("eak_1", {"limits": None})
    assert body_of(route) == {"limits": None}
    assert key["limits"] is None


@respx.mock
def test_record_usage_allowed() -> None:
    debit = {
        "object": "api_key_usage_debit",
        "key_id": "eak_1",
        "unit": "usd_cents",
        "amount": 12,
        "allowed": True,
        "exceeded": [],
        "usage": [STATE],
        "counters": [COUNTER],
        "idempotent_replay": False,
    }
    route = respx.post(f"{API_URL}/v1/api_keys/eak_1/usage").mock(
        return_value=httpx.Response(200, json=debit)
    )
    out = client().api_keys.record_usage(
        "eak_1", {"amount": 12, "unit": "usd_cents", "idempotency_key": "req_1"}
    )
    assert body_of(route) == {"amount": 12, "unit": "usd_cents", "idempotency_key": "req_1"}
    assert out == debit


@respx.mock
def test_record_usage_refusal_is_returned_not_raised() -> None:
    respx.post(f"{API_URL}/v1/api_keys/eak_1/usage").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "api_key_usage_debit",
                "key_id": "eak_1",
                "unit": "usd_cents",
                "amount": 9999,
                "allowed": False,
                "code": "LIMIT_EXCEEDED",
                "exceeded": [STATE],
                "usage": [STATE],
                "counters": [COUNTER],
                "idempotent_replay": False,
            },
        )
    )
    out = client().api_keys.record_usage("eak_1", {"amount": 9999, "unit": "usd_cents"})
    assert out["allowed"] is False
    assert out["code"] == ErrorCode.LIMIT_EXCEEDED
    assert out["exceeded"] == [STATE]


@respx.mock
def test_record_usage_idempotency_conflict_raises() -> None:
    respx.post(f"{API_URL}/v1/api_keys/eak_1/usage").mock(
        return_value=httpx.Response(
            409,
            json={
                "errors": [
                    {
                        "code": "IDEMPOTENCY_CONFLICT",
                        "message": "reused",
                        "param": "idempotency_key",
                    }
                ]
            },
        )
    )
    with pytest.raises(AtlasError) as exc:
        client().api_keys.record_usage(
            "eak_1", {"amount": 1, "unit": "requests", "idempotency_key": "k"}
        )
    assert exc.value.status == 409
    assert exc.value.has_code(ErrorCode.IDEMPOTENCY_CONFLICT)


@respx.mock
def test_get_usage() -> None:
    usage = {
        "object": "api_key_usage",
        "key_id": "eak_1",
        "limits": [LIMIT],
        "usage": [STATE],
        "counters": [COUNTER],
    }
    route = respx.get(f"{API_URL}/v1/api_keys/eak_1/usage").mock(
        return_value=httpx.Response(200, json=usage)
    )
    assert client().api_keys.get_usage("eak_1") == usage
    assert route.calls.last.request.content == b""


@respx.mock
def test_verify_decodes_policy_and_usage() -> None:
    respx.post(f"{API_URL}/v1/api_keys/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "api_key_verification",
                "valid": True,
                "id": "eak_1",
                "subject_type": "user",
                "subject_id": "user_1",
                "name": "CI",
                "claims": {},
                "scopes": ["read"],
                "constraints": {"ip": ["10.0.0.0/8"]},
                "limits": [LIMIT],
                "usage": [STATE],
                "last_used_at": None,
                "expires_at": None,
            },
        )
    )
    v = client().api_keys.verify({"secret": "ak_x"})
    assert v["valid"] is True
    assert v["name"] == "CI"  # type: ignore[typeddict-item]
    assert v["limits"] == [LIMIT]  # type: ignore[typeddict-item]
    assert v["usage"] == [STATE]  # type: ignore[typeddict-item]


SESSION = {
    "object": "session",
    "id": "sess_1",
    "user_id": "user_1",
    "status": "active",
    "last_active_organization_id": None,
    "impersonated_by": None,
    "last_active_at": 1,
    "expire_at": 3,
    "abandon_at": 2,
    "idle_expires_at": 2,
    "created_at": 0,
    "extended": True,
}


@respx.mock
def test_session_touch() -> None:
    route = respx.post(f"{API_URL}/v1/sessions/sess_1/touch").mock(
        return_value=httpx.Response(200, json=SESSION)
    )
    s = client().sessions.touch("sess_1")
    assert route.calls.last.request.content == b""
    assert s["extended"] is True
    assert s["idle_expires_at"] == 2


@respx.mock
def test_session_touch_ended_session_raises() -> None:
    respx.post(f"{API_URL}/v1/sessions/sess_1/touch").mock(
        return_value=httpx.Response(
            409, json={"errors": [{"code": "SESSION_IDLE_EXPIRED", "message": "timed out"}]}
        )
    )
    with pytest.raises(AtlasError) as exc:
        client().sessions.touch("sess_1")
    assert exc.value.has_code(ErrorCode.SESSION_IDLE_EXPIRED)


@respx.mock
def test_notify_on_user_create_and_import() -> None:
    users = respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(201, json={"id": "user_1"})
    )
    imports = respx.post(f"{API_URL}/v1/user_imports").mock(
        return_value=httpx.Response(201, json={"id": "job_1"})
    )
    atlas = client()
    atlas.users.create({"email_address": "a@b.test", "notify": False})
    assert body_of(users) == {"email_address": "a@b.test", "notify": False}
    atlas.user_imports.create({"users": [{"email_address": "a@b.test"}], "notify": True})
    assert body_of(imports) == {"users": [{"email_address": "a@b.test"}], "notify": True}


@respx.mock
async def test_async_record_usage_get_usage_and_touch() -> None:
    debit = respx.post(f"{API_URL}/v1/api_keys/eak_1/usage").mock(
        return_value=httpx.Response(200, json={"object": "api_key_usage_debit", "allowed": True})
    )
    respx.get(f"{API_URL}/v1/api_keys/eak_1/usage").mock(
        return_value=httpx.Response(200, json={"object": "api_key_usage", "key_id": "eak_1"})
    )
    respx.post(f"{API_URL}/v1/sessions/sess_1/touch").mock(
        return_value=httpx.Response(200, json=SESSION)
    )
    async with AsyncAtlasClient(SECRET, base_url=API_URL) as atlas:
        out = await atlas.api_keys.record_usage("eak_1", {"amount": 1, "unit": "requests"})
        assert out["allowed"] is True
        assert body_of(debit) == {"amount": 1, "unit": "requests"}
        assert (await atlas.api_keys.get_usage("eak_1"))["key_id"] == "eak_1"
        assert (await atlas.sessions.touch("sess_1"))["extended"] is True
