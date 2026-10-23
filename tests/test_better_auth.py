"""Migrate from Better Auth: the bundle-import resource (and its upload / wait
helpers), bridge settings, the secret-key session exchange, the framework bridge,
and legacy-issuer JWT acceptance in :class:`AtlasBackend`.

HTTP is mocked with respx; legacy tokens are REAL signatures (Ed25519, P-256,
P-521, RSA, RSA-PSS) minted here.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
import jwt
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from jwt.algorithms import ECAlgorithm, OKPAlgorithm, RSAAlgorithm

from atlas_backend import (
    BETTER_AUTH_IMPORT_PART_BYTES,
    AsyncAtlasClient,
    AsyncBetterAuthBridge,
    AtlasBackend,
    AtlasClient,
    BetterAuthBridge,
    BridgeCookie,
    LegacyIssuer,
    VerificationError,
    better_auth_cookie_names,
    exchange_better_auth_session,
    read_better_auth_session_cookie,
    serialize_bridge_cookie,
    split_bundle_parts,
)

SECRET = "sk_test_placeholder"
API_URL = "https://api.example.test"
BASE = f"{API_URL}/v1/better_auth_imports"
EXCHANGE = f"{API_URL}/v1/migrations/better_auth/exchange"
BA_ISSUER = "https://old.example.test"
BA_JWKS_URL = "https://old.example.test/api/auth/jwks"


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


def body_of(route: respx.Route, index: int = -1) -> Any:
    content = route.calls[index].request.content
    return json.loads(content) if content else None


# --------------------------------------------------------------------------- #
# Bundle splitting                                                            #
# --------------------------------------------------------------------------- #


def test_split_bundle_parts_keeps_whole_lines_under_the_limit() -> None:
    lines = [f'{{"n":{i},"pad":"{"x" * (i % 7)}"}}' for i in range(200)]
    bundle = "\n".join(lines) + "\n"
    parts = split_bundle_parts(bundle, 256)
    assert len(parts) > 1
    assert all(len(p.encode()) <= 256 for p in parts)
    assert all(p.endswith("\n") for p in parts)
    assert "".join(parts) == bundle


def test_split_bundle_parts_drops_blank_lines_and_crlf_and_counts_utf8() -> None:
    parts = split_bundle_parts("a\r\n\n\nb\n", 1024)
    assert parts == ["a\nb\n"]
    # "é" is two bytes: two 3-byte lines don't fit in 5 bytes.
    assert split_bundle_parts("é\né\n", 5) == ["é\n", "é\n"]
    assert split_bundle_parts(b"x\n") == ["x\n"]
    assert split_bundle_parts("") == []
    assert BETTER_AUTH_IMPORT_PART_BYTES == 8 * 1024 * 1024
    with pytest.raises(ValueError):
        split_bundle_parts("x", 0)


def test_oversized_line_is_its_own_part() -> None:
    parts = split_bundle_parts("aa\n" + "b" * 50 + "\ncc\n", 10)
    assert parts == ["aa\n", "b" * 50 + "\n", "cc\n"]


# --------------------------------------------------------------------------- #
# The imports resource                                                        #
# --------------------------------------------------------------------------- #

IMP = {"object": "better_auth_import", "id": "bai_1", "status": "uploading"}


@respx.mock
def test_every_import_operation_hits_its_path() -> None:
    c = client()
    calls: list[tuple[str, str, Any]] = [
        ("GET", "/public_key", lambda: c.better_auth_imports.get_public_key()),
        ("POST", "/public_key/rotate", lambda: c.better_auth_imports.rotate_public_key()),
        ("POST", "", lambda: c.better_auth_imports.create({"options": {"import_sessions": True}})),
        ("GET", "", lambda: c.better_auth_imports.list(limit=5, starting_after="bai_0")),
        ("GET", "/bai_1", lambda: c.better_auth_imports.get("bai_1")),
        ("PUT", "/bai_1/parts/2", lambda: c.better_auth_imports.upload_part("bai_1", 2, "l\n")),
        ("POST", "/bai_1/finalize", lambda: c.better_auth_imports.finalize("bai_1")),
        ("POST", "/bai_1/dry_run", lambda: c.better_auth_imports.dry_run("bai_1")),
        (
            "POST",
            "/bai_1/apply",
            lambda: c.better_auth_imports.apply("bai_1", {"confirm_conflicts": True}),
        ),
        ("DELETE", "/bai_1", lambda: c.better_auth_imports.delete("bai_1")),
        ("GET", "/jwks", lambda: c.better_auth_imports.list_jwks()),
        ("DELETE", "/jwks/kid_1", lambda: c.better_auth_imports.delete_jwk("kid_1")),
    ]
    for method, path, call in calls:
        route = respx.request(method, f"{BASE}{path}").mock(
            return_value=httpx.Response(200, json=IMP)
        )
        call()
        assert route.called, (method, path)
    create = respx.routes[2]
    assert body_of(create) == {"options": {"import_sessions": True}}
    assert respx.routes[3].calls.last.request.url.params["starting_after"] == "bai_0"
    assert body_of(respx.routes[5]) == {"data": "l\n"}
    raw = respx.put(f"{BASE}/bai_1/parts/3").mock(return_value=httpx.Response(200, json={}))
    c.better_auth_imports.upload_part("bai_1", 3, b"x\n")
    assert raw.calls.last.request.content == b"x\n"
    assert raw.calls.last.request.headers["content-type"].startswith("text/plain")
    assert body_of(respx.routes[7]) == {}
    assert body_of(respx.routes[8]) == {"confirm_conflicts": True}


@respx.mock
def test_upload_creates_uploads_line_split_parts_and_finalizes() -> None:
    create = respx.post(BASE).mock(return_value=httpx.Response(201, json=IMP))
    part = respx.put(url__regex=rf"{BASE}/bai_1/parts/\d+").mock(
        return_value=httpx.Response(200, json={"object": "better_auth_import_part"})
    )
    finalize = respx.post(f"{BASE}/bai_1/finalize").mock(
        return_value=httpx.Response(200, json={**IMP, "status": "ready"})
    )
    bundle = "".join(f'{{"line":{i}}}\n' for i in range(40))
    seen: list[tuple[int, int]] = []
    out = client().better_auth_imports.upload(
        bundle,
        options={"models": ["user"]},
        part_bytes=64,
        on_part=lambda n, of: seen.append((n, of)),
    )
    assert out["status"] == "ready"
    assert body_of(create) == {"options": {"models": ["user"]}}
    urls = [str(call.request.url) for call in part.calls]
    assert urls == [f"{BASE}/bai_1/parts/{i}" for i in range(1, len(urls) + 1)]
    uploaded = [json.loads(call.request.content)["data"] for call in part.calls]
    assert "".join(uploaded) == bundle
    assert all(len(u.encode()) <= 64 for u in uploaded)
    assert seen == [(i, len(urls)) for i in range(1, len(urls) + 1)]
    assert finalize.call_count == 1


def test_upload_refuses_an_empty_bundle() -> None:
    with pytest.raises(ValueError, match="empty"):
        client().better_auth_imports.upload("\n\n")


@respx.mock
def test_wait_for_polls_through_in_flight_statuses(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))
    statuses = ["analyzing", "queued", "applying", "completed"]
    route = respx.get(f"{BASE}/bai_1").mock(
        side_effect=[httpx.Response(200, json={**IMP, "status": s}) for s in statuses]
    )
    progress: list[str] = []
    out = client().better_auth_imports.wait_for(
        "bai_1", interval=0.25, on_progress=lambda imp: progress.append(imp["status"])
    )
    assert out["status"] == "completed"
    assert route.call_count == 4
    assert progress == statuses
    assert sleeps == [0.25, 0.25, 0.25]


@respx.mock
def test_wait_for_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda s: None)
    respx.get(f"{BASE}/bai_1").mock(
        return_value=httpx.Response(200, json={**IMP, "status": "applying"})
    )
    with pytest.raises(TimeoutError, match="applying"):
        client().better_auth_imports.wait_for("bai_1", timeout=-1)


@respx.mock
async def test_async_upload_and_wait_for() -> None:
    respx.post(BASE).mock(return_value=httpx.Response(201, json=IMP))
    part = respx.put(url__regex=rf"{BASE}/bai_1/parts/\d+").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post(f"{BASE}/bai_1/finalize").mock(
        return_value=httpx.Response(202, json={**IMP, "status": "analyzing"})
    )
    respx.get(f"{BASE}/bai_1").mock(
        side_effect=[
            httpx.Response(200, json={**IMP, "status": "analyzing"}),
            httpx.Response(200, json={**IMP, "status": "ready"}),
        ]
    )
    c = AsyncAtlasClient(SECRET, base_url=API_URL)
    imp = await c.better_auth_imports.upload("a\nb\nc\n", part_bytes=4)
    assert imp["status"] == "analyzing"
    assert part.call_count == 2  # "a\nb\n" fills 4 bytes, "c\n" starts a new part
    done = await c.better_auth_imports.wait_for("bai_1", interval=0)
    assert done["status"] == "ready"


# --------------------------------------------------------------------------- #
# Bridge settings + exchange                                                  #
# --------------------------------------------------------------------------- #


@respx.mock
def test_bridge_settings_operations() -> None:
    url = f"{API_URL}/v1/migrations/better_auth/bridge"
    get = respx.get(url).mock(return_value=httpx.Response(200, json={"enabled": True}))
    put = respx.put(url).mock(return_value=httpx.Response(200, json={"enabled": True}))
    delete = respx.delete(url).mock(return_value=httpx.Response(200, json={"deleted": True}))
    c = client()
    assert c.better_auth_bridge.get()["enabled"] is True
    c.better_auth_bridge.update(
        {"enabled": True, "ends_at": "2027-01-01T00:00:00Z", "live_fallback": {"secret": None}}
    )
    assert body_of(put) == {
        "enabled": True,
        "ends_at": "2027-01-01T00:00:00Z",
        "live_fallback": {"secret": None},
    }
    c.better_auth_bridge.delete()
    assert get.called and delete.called


@respx.mock
def test_exchange_forwards_the_end_users_ip_and_user_agent() -> None:
    route = respx.post(EXCHANGE).mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "session_tokens",
                "jwt": "j.w.t",
                "refresh_token": "rt_1",
                "session_id": "sess_1",
                "user_id": "user_1",
                "expires_in": 60,
            },
        )
    )
    result = exchange_better_auth_session(
        client(), "tok.sig", client_ip="203.0.113.9", user_agent="Mozilla/5.0", remember=False
    )
    assert result.kind == "session"
    assert (result.jwt, result.refresh_token, result.session_id, result.user_id) == (
        "j.w.t",
        "rt_1",
        "sess_1",
        "user_1",
    )
    assert result.expires_in == 60
    req = route.calls.last.request
    assert req.headers["authorization"] == f"Bearer {SECRET}"
    assert req.headers["x-atlas-client-ip"] == "203.0.113.9"
    assert req.headers["x-atlas-client-user-agent"] == "Mozilla/5.0"
    assert body_of(route) == {"token": "tok.sig", "remember": False}


@respx.mock
def test_exchange_omits_absent_forwarding_headers() -> None:
    route = respx.post(EXCHANGE).mock(return_value=httpx.Response(200, json={}))
    client().better_auth_bridge.exchange("t")
    req = route.calls.last.request
    assert "x-atlas-client-ip" not in req.headers
    assert "x-atlas-client-user-agent" not in req.headers
    assert body_of(route) == {"token": "t"}


def _refusal(status: int, outcome: str | None, code: str = "VERIFICATION_FAILED") -> httpx.Response:
    meta = {"bridge_outcome": outcome} if outcome else {}
    return httpx.Response(status, json={"errors": [{"code": code, "message": "x", "meta": meta}]})


@pytest.mark.parametrize(
    ("response", "outcome", "status"),
    [
        (_refusal(400, "invalid"), "invalid", 400),
        (_refusal(400, "reused"), "reused", 400),
        (_refusal(400, "expired", "VERIFICATION_EXPIRED"), "expired", 400),
        (_refusal(403, "closed"), "closed", 403),
        (_refusal(429, None, "RATE_LIMITED"), "rate_limited", 429),
        (_refusal(503, None, "INTERNAL"), "unavailable", 503),
        (_refusal(403, "something_new"), "unavailable", 403),
    ],
)
@respx.mock
def test_exchange_classifies_refusals(response: httpx.Response, outcome: str, status: int) -> None:
    respx.post(EXCHANGE).mock(return_value=response)
    result = exchange_better_auth_session(client(), "t")
    assert (result.kind, result.outcome, result.http_status) == ("refused", outcome, status)


@respx.mock
def test_exchange_transport_failure_never_raises() -> None:
    respx.post(EXCHANGE).mock(side_effect=httpx.ConnectError("down"))
    result = exchange_better_auth_session(client(), "t")
    assert (result.kind, result.outcome, result.http_status) == ("refused", "unavailable", 0)


@respx.mock
def test_exchange_needs_mfa() -> None:
    respx.post(EXCHANGE).mock(
        return_value=httpx.Response(
            200, json={"object": "sign_in_attempt", "id": "sia_1", "status": "needs_second_factor"}
        )
    )
    result = exchange_better_auth_session(client(), "t")
    assert (result.kind, result.attempt_id, result.status) == (
        "needs_mfa",
        "sia_1",
        "needs_second_factor",
    )


# --------------------------------------------------------------------------- #
# Cookies + the framework-neutral bridge                                      #
# --------------------------------------------------------------------------- #


def test_cookie_names_and_reading() -> None:
    names = better_auth_cookie_names()
    assert names["session_token"] == [
        "__Secure-better-auth.session_token",
        "better-auth.session_token",
    ]
    assert "__Secure-better-auth.session_data" in names["all"]
    assert "better-auth.dont_remember" in names["all"]
    header = "a=1; better-auth.session_token=plain; __Secure-better-auth.session_token=secure"
    assert read_better_auth_session_cookie(header) == "secure"
    assert read_better_auth_session_cookie("my.sess=v", cookie_name="my.sess") == "v"
    assert read_better_auth_session_cookie({"app.session_token": "x"}, cookie_prefix="app") == "x"
    assert read_better_auth_session_cookie(None) is None


def test_serialize_cookie() -> None:
    assert (
        serialize_bridge_cookie(
            BridgeCookie("__atlas_rt", "v", http_only=True, same_site="lax", secure=True)
        )
        == "__atlas_rt=v; Path=/; HttpOnly; Secure; SameSite=Lax"
    )
    assert (
        serialize_bridge_cookie(BridgeCookie("x", "", max_age=0, domain=".example.com"))
        == "x=; Path=/; Domain=.example.com; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT"
    )


SESSION_JSON = {
    "object": "session_tokens",
    "jwt": "j.w.t",
    "refresh_token": "rt_1",
    "session_id": "s",
    "user_id": "u",
    "expires_in": 60,
}


@respx.mock
def test_bridge_signed_in_sets_atlas_cookies_and_clears_better_auth() -> None:
    route = respx.post(EXCHANGE).mock(return_value=httpx.Response(200, json=SESSION_JSON))
    bridge = BetterAuthBridge(client(), better_auth_cookie_domain=".example.com")
    decision = bridge(
        "better-auth.session_token=tok.sig",
        user_agent="UA",
        headers={"X-Forwarded-For": "198.51.100.7, 10.0.0.1"},
    )
    assert decision.action == "signed_in"
    by_name = {c.name: c for c in decision.cookies}
    assert by_name["__session"].value == "j.w.t" and by_name["__session"].secure
    assert by_name["__atlas_rt"].http_only and by_name["__atlas_rt"].value == "rt_1"
    cleared = [c for c in decision.cookies if c.max_age == 0]
    assert {c.name for c in cleared} == set(better_auth_cookie_names()["all"])
    assert all(c.domain == ".example.com" for c in cleared)
    assert all(c.secure for c in cleared if c.name.startswith("__Secure-"))
    req = route.calls.last.request
    assert req.headers["x-atlas-client-ip"] == "198.51.100.7"
    assert req.headers["x-atlas-client-user-agent"] == "UA"


@respx.mock(assert_all_called=False)
def test_bridge_does_nothing_without_a_cookie_or_with_an_atlas_session() -> None:
    route = respx.post(EXCHANGE).mock(return_value=httpx.Response(200, json=SESSION_JSON))
    bridge = BetterAuthBridge(client())
    assert bridge("other=1").action == "none"
    assert bridge("better-auth.session_token=t; __session=x").action == "none"
    assert bridge({"better-auth.session_token": "t", "__atlas_rt": "r"}).action == "none"
    assert not route.called


@respx.mock
def test_bridge_needs_mfa_continuation_url() -> None:
    respx.post(EXCHANGE).mock(
        return_value=httpx.Response(
            200, json={"object": "sign_in_attempt", "id": "sia_1", "status": "needs_mfa_enrollment"}
        )
    )
    decision = BetterAuthBridge(client())("better-auth.session_token=t", client_ip="192.0.2.1")
    assert decision.action == "needs_mfa"
    assert all(c.max_age == 0 for c in decision.cookies)
    url = decision.continuation_url("https://app.example.com/sign-in?redirect=%2Fx")
    assert url == (
        "https://app.example.com/sign-in?redirect=%2Fx"
        "&__atlas_attempt=sia_1&__atlas_status=needs_mfa_enrollment"
    )


@respx.mock
def test_bridge_clears_only_on_final_refusals() -> None:
    route = respx.post(EXCHANGE)
    bridge = BetterAuthBridge(client(), cookie_name="custom.sess")
    route.mock(return_value=_refusal(400, "reused"))
    final = bridge("custom.sess=t")
    assert final.action == "refused" and final.outcome == "reused"
    assert {"custom.sess", "__Secure-custom.sess"} <= {c.name for c in final.cookies}
    for response in (_refusal(403, "closed"), _refusal(429, None), _refusal(500, None)):
        route.mock(return_value=response)
        kept = bridge("custom.sess=t")
        assert kept.action == "refused" and kept.cookies == []


@respx.mock
async def test_async_bridge() -> None:
    respx.post(EXCHANGE).mock(return_value=httpx.Response(200, json=SESSION_JSON))
    bridge = AsyncBetterAuthBridge(AsyncAtlasClient(SECRET, base_url=API_URL), secure=False)
    decision = await bridge("better-auth.session_token=t")
    assert decision.action == "signed_in"
    assert not {c.name: c for c in decision.cookies}["__session"].secure


# --------------------------------------------------------------------------- #
# Framework integrations                                                      #
# --------------------------------------------------------------------------- #


@respx.mock
def test_flask_bridge_redirects_signed_in_and_clears_on_final_refusal() -> None:
    from flask import Flask

    from atlas_backend.flask import Atlas

    app = Flask(__name__)
    app.config.update(
        ATLAS_JWKS_URL=JWKS_URL,
        ATLAS_ISSUER=ISSUER,
        ATLAS_SECRET_KEY=SECRET,
        ATLAS_API_URL=API_URL,
        ATLAS_BETTER_AUTH_BRIDGE={"sign_in_url": "https://app.example.com/sign-in"},
    )
    Atlas(app)
    app.add_url_rule("/page", "page", lambda: "ok")
    app.add_url_rule("/form", "form", lambda: "posted", methods=["POST"])
    route = respx.post(EXCHANGE).mock(return_value=httpx.Response(200, json=SESSION_JSON))
    tc = app.test_client()
    tc.set_cookie("better-auth.session_token", "tok")
    res = tc.get("/page?x=1", headers={"User-Agent": "UA", "X-Forwarded-For": "203.0.113.5"})
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/page?x=1")
    set_cookies = res.headers.getlist("Set-Cookie")
    assert any(c.startswith("__session=j.w.t") for c in set_cookies)
    assert any(c.startswith("__atlas_rt=rt_1") and "HttpOnly" in c for c in set_cookies)
    assert route.calls.last.request.headers["x-atlas-client-ip"] == "203.0.113.5"

    route.mock(
        return_value=httpx.Response(
            200, json={"object": "sign_in_attempt", "id": "sia_9", "status": "needs_second_factor"}
        )
    )
    tc2 = app.test_client()
    tc2.set_cookie("better-auth.session_token", "tok")
    res = tc2.get("/page")
    assert res.status_code == 302
    assert res.headers["Location"].startswith(
        "https://app.example.com/sign-in?__atlas_attempt=sia_9"
    )

    route.mock(return_value=_refusal(400, "expired", "VERIFICATION_EXPIRED"))
    tc3 = app.test_client()
    tc3.set_cookie("better-auth.session_token", "tok")
    res = tc3.get("/page")
    assert res.status_code == 200 and res.text == "ok"
    assert any(
        c.startswith("better-auth.session_token=;") for c in res.headers.getlist("Set-Cookie")
    )

    # POSTs pass through untouched.
    calls = route.call_count
    tc3.set_cookie("better-auth.session_token", "tok")
    assert tc3.post("/form").text == "posted"
    assert route.call_count == calls


def test_flask_bridge_needs_the_secret_key() -> None:
    from flask import Flask

    from atlas_backend.flask import Atlas

    app = Flask(__name__)
    app.config.update(ATLAS_JWKS_URL=JWKS_URL, ATLAS_ISSUER=ISSUER, ATLAS_BETTER_AUTH_BRIDGE=True)
    with pytest.raises(RuntimeError, match="ATLAS_SECRET_KEY"):
        Atlas(app)


@respx.mock
def test_django_middleware_bridge() -> None:
    import test_django  # noqa: F401  (configures Django settings once)
    from django.http import HttpRequest, HttpResponse
    from django.test import RequestFactory, override_settings

    import atlas_backend.django as atlas_django
    from atlas_backend.django import AtlasMiddleware

    route = respx.post(EXCHANGE).mock(return_value=httpx.Response(200, json=SESSION_JSON))

    def view(request: HttpRequest) -> HttpResponse:
        return HttpResponse("ok")

    with override_settings(
        ATLAS_SECRET_KEY=SECRET,
        ATLAS_API_URL=API_URL,
        ATLAS_BETTER_AUTH_BRIDGE={"secure": False},
    ):
        atlas_django._reset_backend()
        try:
            request = RequestFactory().get(
                "/page?x=1", HTTP_USER_AGENT="UA", REMOTE_ADDR="198.51.100.2"
            )
            request.COOKIES["better-auth.session_token"] = "tok"
            response = AtlasMiddleware(view)(request)
            assert response.status_code == 302
            assert response["Location"] == "/page?x=1"
            assert response.cookies["__session"].value == "j.w.t"
            assert response.cookies["__atlas_rt"]["httponly"]
            assert response.cookies["better-auth.session_token"]["max-age"] == 0
            headers = route.calls.last.request.headers
            assert headers["x-atlas-client-ip"] == "198.51.100.2"
            assert headers["x-atlas-client-user-agent"] == "UA"

            route.mock(return_value=_refusal(400, "invalid"))
            request = RequestFactory().get("/page")
            request.COOKIES["better-auth.session_token"] = "tok"
            response = AtlasMiddleware(view)(request)
            assert response.status_code == 200
            assert response.cookies["better-auth.session_token"]["max-age"] == 0
        finally:
            atlas_django._reset_backend()


# --------------------------------------------------------------------------- #
# Legacy issuers                                                              #
# --------------------------------------------------------------------------- #

_ED = ed25519.Ed25519PrivateKey.generate()
_P256 = ec.generate_private_key(ec.SECP256R1())
_P521 = ec.generate_private_key(ec.SECP521R1())
_RSA = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwk(alg: str, kid: str) -> dict[str, Any]:
    if alg == "EdDSA":
        jwk = json.loads(OKPAlgorithm.to_jwk(_ED.public_key()))
    elif alg == "ES256":
        jwk = json.loads(ECAlgorithm.to_jwk(_P256.public_key()))
    elif alg == "ES512":
        jwk = json.loads(ECAlgorithm.to_jwk(_P521.public_key()))
    else:
        jwk = json.loads(RSAAlgorithm.to_jwk(_RSA.public_key()))
    jwk["kid"] = kid
    return jwk


def _private(alg: str) -> Any:
    return {"EdDSA": _ED, "ES256": _P256, "ES512": _P521}.get(alg, _RSA)


def ba_token(alg: str = "EdDSA", kid: str = "ba1", **overrides: Any) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": BA_ISSUER,
        "aud": BA_ISSUER,
        "sub": "ba_user_1",
        "iat": now,
        "exp": now + 900,
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, _private(alg), algorithm=alg, headers={"kid": kid})


def ba_jwks() -> dict[str, Any]:
    return {"keys": [_jwk(a, f"k-{a}") for a in ("EdDSA", "ES256", "ES512", "RS256")]}


def backend(**legacy: Any) -> AtlasBackend:
    entry: dict[str, Any] = {
        "issuer": BA_ISSUER,
        "until": int(time.time() * 1000) + 86_400_000,
        "jwks": ba_jwks(),
        "audience": BA_ISSUER,
        "resolve_subject": lambda sub, claims: {"ba_user_1": "user_atlas_1"}.get(sub),
    }
    entry.update(legacy)
    return AtlasBackend(jwks_url=JWKS_URL, issuer=ISSUER, legacy_issuers=[LegacyIssuer(**entry)])


@pytest.mark.parametrize("alg", ["EdDSA", "ES256", "ES512", "RS256", "PS256"])
def test_legacy_token_verifies_and_maps_sub(alg: str) -> None:
    kid = "k-RS256" if alg == "PS256" else f"k-{alg}"
    claims = backend().verify(ba_token(alg, kid, sid="ba_sess"))
    assert claims.sub == "user_atlas_1"
    assert claims.sid == "ba_sess"
    assert claims.raw["external_id"] == "ba_user_1"
    assert claims.raw["legacy"] == {"kind": "better_auth", "issuer": BA_ISSUER, "sub": "ba_user_1"}


def test_legacy_refusals() -> None:
    b = backend()
    for token in (
        ba_token("EdDSA", "k-EdDSA", exp=None),  # no expiry
        ba_token("EdDSA", "k-EdDSA", exp=int(time.time()) - 60),  # expired
        ba_token("EdDSA", "k-EdDSA", aud="https://someone-else"),  # wrong audience
        ba_token("EdDSA", "k-EdDSA", sub="unknown"),  # resolver says no
        ba_token("ES256", "k-EdDSA"),  # key type / alg mismatch
    ):
        with pytest.raises(VerificationError) as err:
            b.verify(token)
        assert err.value.reason == VerificationError.INVALID


def test_legacy_algorithm_allowlist() -> None:
    b = backend(algorithms=["EdDSA"])
    assert b.verify(ba_token("EdDSA", "k-EdDSA")).sub == "user_atlas_1"
    with pytest.raises(VerificationError):
        b.verify(ba_token("RS256", "k-RS256"))


@respx.mock
def test_legacy_window_closed_falls_through_to_atlas_keys() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    b = backend(until=int(time.time() * 1000) - 1)
    with pytest.raises(VerificationError) as err:
        b.verify(ba_token("EdDSA", "k-EdDSA"))
    assert err.value.reason == VerificationError.INVALID
    # Atlas's own tokens still verify alongside a legacy issuer.
    assert backend().verify(mint_token()).iss == ISSUER


@respx.mock
def test_legacy_default_resolver_uses_external_id_and_caches() -> None:
    route = respx.get(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "user_atlas_9"}]})
    )
    b = AtlasBackend(
        jwks_url=JWKS_URL,
        issuer=ISSUER,
        secret_key=SECRET,
        api_url=API_URL,
        legacy_issuers=[
            LegacyIssuer(
                issuer=BA_ISSUER,
                until="2999-01-01T00:00:00Z",
                jwks_url=BA_JWKS_URL,
            )
        ],
    )
    respx.get(BA_JWKS_URL).mock(return_value=httpx.Response(200, json=ba_jwks()))
    assert b.verify(ba_token("EdDSA", "k-EdDSA")).sub == "user_atlas_9"
    assert b.verify(ba_token("EdDSA", "k-EdDSA")).sub == "user_atlas_9"
    assert route.call_count == 1
    req = route.calls.last.request
    assert req.url.params["external_id"] == "ba_user_1"
    assert req.headers["authorization"] == f"Bearer {SECRET}"


@respx.mock
def test_legacy_resolver_failure_is_not_cached() -> None:
    route = respx.get(f"{API_URL}/v1/users").mock(
        side_effect=[
            httpx.Response(503, json={}),
            httpx.Response(200, json={"data": [{"id": "user_atlas_2"}]}),
        ]
    )
    b = AtlasBackend(
        jwks_url=JWKS_URL,
        issuer=ISSUER,
        secret_key=SECRET,
        api_url=API_URL,
        legacy_issuers=[LegacyIssuer(issuer=BA_ISSUER, until=4_000_000_000_000, jwks=ba_jwks())],
    )
    with pytest.raises(VerificationError):
        b.verify(ba_token("EdDSA", "k-EdDSA"))
    assert b.verify(ba_token("EdDSA", "k-EdDSA")).sub == "user_atlas_2"
    assert route.call_count == 2


def test_legacy_configuration_errors() -> None:
    until = 4_000_000_000_000
    with pytest.raises(ValueError, match="exactly one"):
        AtlasBackend(
            jwks_url=JWKS_URL,
            issuer=ISSUER,
            secret_key=SECRET,
            legacy_issuers=[LegacyIssuer(issuer=BA_ISSUER, until=until)],
        )
    with pytest.raises(ValueError, match="until"):
        AtlasBackend(
            jwks_url=JWKS_URL,
            issuer=ISSUER,
            secret_key=SECRET,
            legacy_issuers=[LegacyIssuer(issuer=BA_ISSUER, until="not a date", jwks=ba_jwks())],
        )
    with pytest.raises(ValueError, match="secret_key"):
        AtlasBackend(
            jwks_url=JWKS_URL,
            issuer=ISSUER,
            legacy_issuers=[LegacyIssuer(issuer=BA_ISSUER, until=until, jwks=ba_jwks())],
        )
    with pytest.raises(ValueError, match="Atlas issuer"):
        AtlasBackend(
            jwks_url=JWKS_URL,
            issuer=ISSUER,
            secret_key=SECRET,
            legacy_issuers=[LegacyIssuer(issuer=ISSUER, until=until, jwks=ba_jwks())],
        )
