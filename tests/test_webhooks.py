from __future__ import annotations

import base64
import hashlib
import hmac
import json

from atlas_backend import verify_webhook

SECRET = "whsec_test_secret"
NOW = 1_757_937_600_000
BODY = json.dumps({"id": "evt_1", "type": "user.updated", "data": {"object": "user", "id": "user_1"}})


def sign(delivery_id: str, ts: int, body: str, secret: str = SECRET) -> dict[str, str]:
    mac = hmac.new(secret.encode(), f"{delivery_id}.{ts}.{body}".encode(), hashlib.sha256).digest()
    return {
        "Atlas-Id": delivery_id,
        "Atlas-Timestamp": str(ts),
        "Atlas-Signature": "v1," + base64.b64encode(mac).decode(),
    }


def test_verifies_and_returns_the_delivery_id_and_timestamp() -> None:
    headers = sign("evt_1", NOW - 1_000, BODY)
    result = verify_webhook(BODY, headers, SECRET, now_ms=NOW)
    assert result.verified
    assert result.delivery_id == "evt_1"
    assert result.timestamp == NOW - 1_000
    assert result.event is not None and result.event["type"] == "user.updated"


def test_accepts_bytes_bodies() -> None:
    headers = sign("evt_1", NOW, BODY)
    assert verify_webhook(BODY.encode(), headers, SECRET, now_ms=NOW).verified


def test_rejects_a_tampered_body() -> None:
    headers = sign("evt_1", NOW, BODY)
    result = verify_webhook(BODY.replace("user_1", "user_2"), headers, SECRET, now_ms=NOW)
    assert not result.verified
    assert result.reason == "signature_mismatch"
    assert result.delivery_id is None


def test_rejects_stale_and_future_timestamps() -> None:
    for ts in (NOW - 6 * 60_000, NOW + 6 * 60_000):
        assert verify_webhook(BODY, sign("evt_1", ts, BODY), SECRET, now_ms=NOW).reason == "stale_timestamp"


def test_rejects_a_wrong_secret_and_bad_headers() -> None:
    assert verify_webhook(BODY, sign("evt_1", NOW, BODY, "whsec_other"), SECRET, now_ms=NOW).reason == "signature_mismatch"
    assert verify_webhook(BODY, {}, SECRET, now_ms=NOW).reason == "missing_headers"
    bad = {**sign("evt_1", NOW, BODY), "Atlas-Signature": "v2,abc"}
    assert verify_webhook(BODY, bad, SECRET, now_ms=NOW).reason == "malformed_signature"
