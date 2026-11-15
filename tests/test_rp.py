"""The hosted-redirect relying party against an offline issuer (respx + a throwaway RSA key)."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
import respx
from cryptography.hazmat.primitives.asymmetric import rsa

from atlas_backend import (
    MemorySidStore,
    OidcError,
    RelyingParty,
    RpRequest,
    authenticated_within,
    mfa_org_satisfied,
    mfa_satisfied,
    used_multi_factor,
)

ISSUER = "https://id.example.test"
REDIRECT = "https://app.example.test/auth/callback"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
JWK = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key()))
JWK.update(kid="k1", alg="RS256", use="sig")


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _make_rp(**kw: object) -> RelyingParty:
    return RelyingParty(
        issuer=ISSUER,
        client_id="client_1",
        client_secret="shh",
        redirect_uri=REDIRECT,
        secret="s" * 40,
        on_signed_in=lambda *a: None,
        **kw,  # type: ignore[arg-type]
    )


def _mock(mock: respx.MockRouter, claims_extra: dict | None = None, state: dict | None = None) -> None:
    state = state if state is not None else {}
    mock.get(f"{ISSUER}/.well-known/openid-configuration").mock(
        return_value=httpx.Response(
            200,
            json={
                "issuer": ISSUER,
                "authorization_endpoint": f"{ISSUER}/oauth2/authorize",
                "token_endpoint": f"{ISSUER}/oauth2/token",
                "jwks_uri": f"{ISSUER}/jwks",
                "end_session_endpoint": f"{ISSUER}/oauth2/logout",
            },
        )
    )
    mock.get(f"{ISSUER}/jwks").mock(return_value=httpx.Response(200, json={"keys": [JWK]}))

    def token(request: httpx.Request) -> httpx.Response:
        form = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
        assert _b64u(hashlib.sha256(form["code_verifier"].encode()).digest()) == state["challenge"]
        access = "access-token"
        now = int(time.time())
        claims = {
            "iss": ISSUER, "aud": "client_1", "sub": "user_1", "sid": "sid_1", "iat": now, "exp": now + 300,
            "nonce": state["nonce"], "email": "a@example.com", "email_verified": True, "auth_time": now,
            "at_hash": _b64u(hashlib.sha256(access.encode()).digest()[:16]), **(claims_extra or {}),
        }
        id_token = jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "k1"})
        return httpx.Response(200, json={"id_token": id_token, "access_token": access, "expires_in": 300})

    mock.post(f"{ISSUER}/oauth2/token").mock(side_effect=token)


def _sign_in(rp: RelyingParty, state: dict) -> tuple[RpRequest, str]:
    started = rp.start(RpRequest("GET", "https://app.example.test/auth/sign-in?return_to=/billing"))
    assert started.status == 302
    q = {k: v[0] for k, v in parse_qs(urlsplit(started.location or "").query).items()}
    assert q["code_challenge_method"] == "S256" and q["scope"] == "openid profile email"
    state.update(challenge=q["code_challenge"], nonce=q["nonce"])
    cookie = started.header("set-cookie").split(";")[0]  # type: ignore[union-attr]
    return RpRequest("GET", f"{REDIRECT}?code=c1&state={q['state']}", {"cookie": cookie}), cookie


def test_sign_in_round_trip() -> None:
    state: dict = {}
    with respx.mock() as mock:
        _mock(mock, state=state)
        rp = _make_rp()
        request, _ = _sign_in(rp, state)
        result = rp.callback(request)
    assert result.user.sub == "user_1" and result.user.sid == "sid_1" and result.user.email_verified
    assert result.return_to == "/billing" and result.response.location == "/billing"
    assert "Max-Age=0" in (result.response.header("set-cookie") or "")


def test_state_mismatch_clears_the_cookie() -> None:
    state: dict = {}
    with respx.mock(assert_all_called=False) as mock:  # fails on state before token/jwks
        _mock(mock, state=state)
        rp = _make_rp()
        request, cookie = _sign_in(rp, state)
        bad = RpRequest("GET", f"{REDIRECT}?code=c1&state=wrong", {"cookie": cookie})
        with pytest.raises(OidcError) as e:
            rp.callback(bad)
    assert e.value.code == "state_mismatch" and "Max-Age=0" in (e.value.clear_cookie or "")


def test_wrong_nonce_is_refused() -> None:
    state: dict = {}
    with respx.mock() as mock:
        _mock(mock, claims_extra={"nonce": "other"}, state=state)
        rp = _make_rp()
        request, _ = _sign_in(rp, state)
        with pytest.raises(OidcError) as e:
            rp.callback(request)
    assert e.value.code == "invalid_token"


def test_require_recent_auth_and_handle_routes() -> None:
    rp = _make_rp()
    now = int(time.time())
    here = RpRequest("GET", "https://app.example.test/settings?tab=security")
    assert rp.require_recent_auth(here, 300, sub="u", auth_time=now) is None
    with respx.mock(assert_all_called=False) as mock:  # only discovery is needed
        _mock(mock)
        out = rp.require_recent_auth(here, 300, sub="u", auth_time=now - 3600)
        assert out is not None and "max_age=300" in (out.location or "")
        assert rp.handle(RpRequest("GET", "https://app.example.test/elsewhere")) is None


def test_backchannel_logout_returns_bound_sessions() -> None:
    store = MemorySidStore()
    ended: list[list[str]] = []
    rp = _make_rp(sid_store=store, on_backchannel_logout=lambda ids, claims: ended.append(ids))
    rp.bind_session("sid_1", "app_1", int(time.time() * 1000) + 60_000)
    now = int(time.time())
    token = jwt.encode(
        {"iss": ISSUER, "aud": "client_1", "iat": now, "jti": "j1", "sid": "sid_1",
         "events": {"http://schemas.openid.net/event/backchannel-logout": {}}},
        KEY, algorithm="RS256", headers={"kid": "k1", "typ": "logout+jwt"},
    )
    with respx.mock() as mock:
        mock.get(f"{ISSUER}/.well-known/jwks.json").mock(return_value=httpx.Response(200, json={"keys": [JWK]}))
        out = rp.backchannel_logout(RpRequest("POST", "https://app.example.test/x", form={"logout_token": token}))
    assert out.status == 200 and ended == [["app_1"]]


def test_mfa_and_recent_auth_helpers() -> None:
    assert authenticated_within({"auth_time": time.time() - 10}, 60)
    assert not authenticated_within({}, 60)
    assert used_multi_factor({"amr": ["pwd", "mfa"]}) and used_multi_factor({"acr": "urn:atlas:acr:mfa"})
    assert mfa_satisfied({"mfa_satisfied": False, "mfa": True}) is False
    assert mfa_satisfied({"sso_connection_id": "x"})
    assert mfa_org_satisfied({"org_id": "o", "org_mfa_required": True, "org_mfa_ok": True}, "o")
    assert not mfa_org_satisfied({"org_id": "p"}, "o")
