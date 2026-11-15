"""Mirrors, revocation, webhook dedupe, Web Bot Auth, machine client, resilience, telemetry, doctor."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

import httpx
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from atlas_backend import (
    AtlasClient,
    KeyMirror,
    MachineClient,
    MemoryMachineStore,
    MemoryWebhookStore,
    ResourceRoleMirror,
    RetryPolicy,
    SidRevocationList,
    WebBotAuthVerifier,
    create_dpop_proof,
    doctor,
    hash_api_key_secret,
    ip_in_allowlist,
    sign_machine_challenge,
    sign_web_bot_auth_request,
    verify_and_dedupe,
)

API = "https://api.example.test"
# RFC 8032 section 7.1, TEST 1: a published Ed25519 key and the signature over the empty message.
PRIVATE_PEM = "-----BEGIN PRIVATE KEY-----\nMC4CAQAwBQYDK2VwBCIEIJ1hsZ3v/VpguoRK9JLsLMREScVpezJpGXA7rAMcrn9g\n-----END PRIVATE KEY-----\n"
RFC8032_SIG = "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


# -- key mirror -------------------------------------------------------------------------------


class FakeKeys:
    def __init__(self) -> None:
        self.revoked: list[str] = []
        self.feed: list[dict[str, Any]] = []

    def create(self, body: dict, idempotency_key: str | None = None) -> dict:
        return {"id": "eak_1", "prefix": "ak_live", "subject_type": "user", "subject_id": "u1",
                "scopes": ["reports:read"], "secret": "ak_live_secret", "allowed_ips": ["10.0.0.0/8"]}

    def revoke(self, key_id: str) -> None:
        self.revoked.append(key_id)

    def list_revoked(self, **_: Any) -> dict:
        return {"data": self.feed, "has_more": False, "next_cursor": "c1"}


def test_key_mirror_verify_scopes_ip_and_revoke() -> None:
    keys = FakeKeys()
    mirror = KeyMirror(api_keys=keys)
    mirror.mint({})
    assert mirror.verify("ak_live_secret", client_ip="10.1.2.3").valid
    assert mirror.verify("ak_live_secret").code == "client_ip_required"
    assert mirror.verify("ak_live_secret", client_ip="8.8.8.8").code == "ip_not_allowed"
    r = mirror.verify("ak_live_secret", client_ip="10.1.2.3", required_scopes=["x"])
    assert r.code == "insufficient_scope" and r.missing_scopes == ["x"]
    assert not mirror.verify("nope").valid
    mirror.revoke("eak_1")
    assert keys.revoked == ["eak_1"] and not mirror.verify("ak_live_secret", client_ip="10.1.2.3").valid


def test_key_mirror_sync_and_staleness() -> None:
    keys = FakeKeys()
    clock = [1_000_000]
    mirror = KeyMirror(api_keys=keys, max_staleness_ms=1000, now=lambda: clock[0])
    mirror.mint({})
    assert mirror.verify("ak_live_secret", client_ip="10.0.0.1").code == "stale"
    keys.feed = [{"id": "eak_1", "revoked_at": 5, "revoked_reason": "rotated"}]
    assert mirror.sync() == 1
    assert not mirror.verify("ak_live_secret", client_ip="10.0.0.1").valid
    assert hash_api_key_secret("a") == hashlib.sha256(b"a").hexdigest()
    assert ip_in_allowlist("2001:db8::1", ["2001:db8::/32"]) and not ip_in_allowlist("bad", ["10.0.0.0/8"])


# -- resource-role mirror ---------------------------------------------------------------------


class FakeClient:
    class resources:  # noqa: N801
        class types:  # noqa: N801
            @staticmethod
            def list() -> dict:
                return {"data": [
                    {"key": "doc", "inherit": True, "roles": [{"key": "viewer", "permissions": ["read"]}]},
                    {"key": "folder", "inherit": True, "roles": [{"key": "owner", "permissions": ["*"]}]},
                ]}

        @staticmethod
        def list(**_: Any) -> dict:
            return {"data": [
                {"id": "r_f", "type": "folder", "external_id": "f1", "parent_id": None},
                {"id": "r_d", "type": "doc", "external_id": "d1", "parent_id": "r_f"},
            ], "has_more": False}

    class resource_role_assignments:  # noqa: N801
        @staticmethod
        def list_changes(**_: Any) -> dict:
            return {"data": [{"change": "created", "assignment_id": "a1", "resource_id": "r_f",
                              "subject": {"type": "user", "id": "u1"}, "role": "owner", "inherit": True}],
                    "has_more": False, "next_cursor": "n1"}


def test_resource_role_mirror_inherits_from_the_parent() -> None:
    mirror = ResourceRoleMirror(client=FakeClient())
    assert mirror.sync() == 1
    me = {"type": "user", "id": "u1"}
    res = mirror.check(me, "read", {"type": "doc", "external_id": "d1"})
    assert res["allowed"] and res["grants"][0]["inherited"]
    assert not mirror.can({"type": "user", "id": "u2"}, "read", {"id": "r_d"})
    assert mirror.check(me, "read", {"id": "missing"})["code"] == "unknown_resource"
    assert mirror.apply_webhook({"type": "resource_role_assignment.deleted", "data": {
        "id": "a1", "resource_id": "r_f", "subject": {"type": "user", "id": "u1"}, "role": "owner"}})
    assert not mirror.can(me, "read", {"id": "r_d"})


# -- webhook dedupe ---------------------------------------------------------------------------


def _signed(body: bytes, secret: str, delivery: str = "evt_1") -> dict[str, str]:
    ts = int(time.time() * 1000)
    sig = base64.b64encode(hmac.new(secret.encode(), f"{delivery}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
    return {"atlas-id": delivery, "atlas-timestamp": str(ts), "atlas-signature": f"v1,{sig}"}


def test_verify_and_dedupe() -> None:
    body = json.dumps({"id": "evt_1", "type": "user.created", "data": {}}).encode()
    store = MemoryWebhookStore()
    first = verify_and_dedupe(body, _signed(body, "whsec"), "whsec", store)
    again = verify_and_dedupe(body, _signed(body, "whsec"), "whsec", store)
    assert not first.duplicate and again.duplicate
    first.release()
    assert not verify_and_dedupe(body, _signed(body, "whsec"), "whsec", store).duplicate
    import pytest

    from atlas_backend import WebhookVerificationError

    with pytest.raises(WebhookVerificationError):
        verify_and_dedupe(body, _signed(body, "other"), "whsec", store)


# -- sid revocation ---------------------------------------------------------------------------


def test_sid_revocation_list_polls_the_feed() -> None:
    now = [10_000_000]
    with respx.mock(base_url=API) as mock:
        mock.get("/v1/sessions/revoked").mock(return_value=httpx.Response(200, json={
            "data": [{"sid": "sid_x", "revoked_at": now[0]}], "has_more": False, "next_cursor": None, "server_time": now[0]}))
        lst = SidRevocationList(secret_key="sk_t", base_url=API, now=lambda: now[0])
        assert lst.is_revoked("sid_x") and not lst.is_revoked("sid_y")


# -- web bot auth -----------------------------------------------------------------------------


def test_web_bot_auth_verifies_and_decides() -> None:
    seed = bytes(range(32))
    pub = Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    jwk = {"kty": "OKP", "crv": "Ed25519", "x": _b64u(pub)}
    now = int(time.time())
    headers = sign_web_bot_auth_request(method="GET", url="https://site.example/a?b=1", signature_agent="https://bot.example",
                                        private_key=seed, created=now, expires=now + 60)
    verifier = WebBotAuthVerifier(allow=[{"directory": "bot.example", "name": "Bot"}], fetch_json=lambda url: {"keys": [jwk]})
    ok = verifier.verify(method="GET", url="https://site.example/a?b=1", headers=headers)
    assert ok.verified and ok.decision == "allow" and ok.agent and ok.agent["name"] == "Bot"
    moved = verifier.verify(method="GET", url="https://other.example/a", headers=headers)
    assert not moved.verified and moved.reason == "bad_signature" and moved.agent is None
    assert verifier.verify(method="GET", url="https://site.example/", headers={}).reason == "no_signature"


# -- machine client ---------------------------------------------------------------------------


def test_challenge_signature_is_the_rfc8032_vector() -> None:
    assert sign_machine_challenge(PRIVATE_PEM, "") == _b64u(bytes.fromhex(RFC8032_SIG))


def test_machine_client_enrols_mints_and_caches() -> None:
    issuer = "https://id.example.test"
    state: dict[str, Any] = {"mints": 0}
    with respx.mock() as mock:
        def enroll(request: httpx.Request) -> httpx.Response:
            state["public"] = json.loads(request.content)["public_key_pem"]
            return httpx.Response(201, json={"id": "mch_1", "status": "active", "approval_required": False, "enrolled_at": 1})

        def token(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            key = serialization.load_pem_public_key(state["public"].encode())
            key.verify(base64.urlsafe_b64decode(body["signature"] + "=="), body["nonce"].encode())  # type: ignore[call-arg,union-attr]
            state["mints"] += 1
            return httpx.Response(200, json={"token": f"tok-{state['mints']}", "token_type": "Bearer", "expires_in": 600})

        mock.post(f"{issuer}/v1/machines/enroll").mock(side_effect=enroll)
        mock.post(f"{issuer}/v1/machines/challenge").mock(return_value=httpx.Response(200, json={"nonce": "n-1"}))
        mock.post(f"{issuer}/v1/machines/token").mock(side_effect=token)
        machine = MachineClient(issuer=issuer, store=MemoryMachineStore())
        assert not machine.is_enrolled()
        assert machine.enroll(credential="XXXX-XXXX", name="m").machine_id == "mch_1"
        assert machine.get_token(audience="a").token == "tok-1" and machine.get_token(audience="a").token == "tok-1"
        assert state["mints"] == 1
        assert machine.get_token(audience="b").token == "tok-2"


def test_dpop_proof_names_the_request_and_token() -> None:
    proof = create_dpop_proof(PRIVATE_PEM, "post", "https://api.example.test/x?q=1", access_token="tok", now=lambda: 5000)
    head, payload = (json.loads(base64.urlsafe_b64decode(p + "==")) for p in proof.split(".")[:2])
    assert head["typ"] == "dpop+jwt" and head["alg"] == "EdDSA"
    assert payload["htm"] == "POST" and payload["htu"] == "https://api.example.test/x" and payload["iat"] == 5
    assert payload["ath"] == _b64u(hashlib.sha256(b"tok").digest())


# -- resilience -------------------------------------------------------------------------------


def test_retry_honours_retry_after_and_skips_unkeyed_writes() -> None:
    sleeps: list[float] = []
    policy = RetryPolicy(max_retries=2, sleep=sleeps.append)
    with respx.mock(base_url=API) as mock:
        route = mock.get("/v1/users/u1").mock(side_effect=[
            httpx.Response(429, headers={"retry-after": "7"}, json={"errors": [{"code": "RATE_LIMITED", "message": "slow"}]}),
            httpx.Response(200, json={"id": "u1"}),
        ])
        post = mock.post("/v1/users").mock(return_value=httpx.Response(503, json={"errors": [{"code": "X", "message": "x"}]}))
        client = AtlasClient("sk_t", base_url=API, retry=policy)
        assert client.users.get("u1")["id"] == "u1" and sleeps == [7.0] and route.call_count == 2
        try:
            client.users.create({"email_address": "a@example.com"})
        except Exception:
            pass
        assert post.call_count == 1  # no idempotency key: never replayed


def test_status_aware_backoff_reads_the_status_endpoint() -> None:
    sleeps: list[float] = []
    policy = RetryPolicy(max_retries=1, status_aware=True, max_delay=40.0, sleep=sleeps.append)
    with respx.mock(base_url=API) as mock:
        mock.get("/v1/status").mock(return_value=httpx.Response(200, json={"object": "status", "status": "major_outage", "components": []}))
        mock.get("/v1/users/u1").mock(return_value=httpx.Response(503, json={"errors": [{"code": "X", "message": "x"}]}))
        client = AtlasClient("sk_t", base_url=API, retry=policy)
        try:
            client.users.get("u1")
        except Exception as e:
            assert getattr(e, "status_indicator", None) == "major_outage"
    assert sleeps == [40.0]


# -- doctor -----------------------------------------------------------------------------------


def test_doctor_reports_each_check() -> None:
    with respx.mock(base_url=API) as mock:
        mock.get("/v1/status").mock(return_value=httpx.Response(200, json={"status": "operational"}, headers={"date": "Wed, 01 Jan 2020 00:00:00 GMT"}))
        mock.get("/v1/instance").mock(return_value=httpx.Response(401, json={}))
        report = doctor(secret_key="sk_live_abc", base_url=API)
    by = {c.name: c for c in report.checks}
    assert by["clock"].status == "fail" and by["auth"].status == "fail" and not report.ok
    assert "sk_live_abc" not in report.format()
