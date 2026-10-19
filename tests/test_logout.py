"""Back-channel logout token verification (OIDC Back-Channel Logout 1.0 §2.6).

Tokens are signed with a real RSA key generated for the test run; the JWKS is
served by respx.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
import pytest
import respx
from _verify_helpers import _PRIVATE_KEY, KID, jwks_document, other_key

from atlas_backend import (
    BACKCHANNEL_LOGOUT_EVENT,
    LogoutTokenVerifier,
    VerificationError,
    logout_token_from_form,
)

ISSUER = "https://atlasauth.net"
CLIENT_ID = "cid_demo"
JWKS = f"{ISSUER}/.well-known/jwks.json"


def mint(
    *,
    claims: dict[str, Any] | None = None,
    drop: tuple[str, ...] = (),
    headers: dict[str, Any] | None = None,
    key: Any = None,
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "iss": ISSUER,
        "sub": "user_1",
        "aud": CLIENT_ID,
        "iat": now,
        "exp": now + 120,
        "jti": "jti_1",
        "sid": "sess_1",
        "events": {BACKCHANNEL_LOGOUT_EVENT: {}},
    }
    payload.update(claims or {})
    for k in drop:
        payload.pop(k, None)
    hdr = {"kid": KID, "typ": "logout+jwt"}
    hdr.update(headers or {})
    return jwt.encode(payload, key or _PRIVATE_KEY, algorithm="RS256", headers=hdr)


@pytest.fixture
def verifier() -> Any:
    with respx.mock(assert_all_called=False) as mock:
        mock.get(JWKS).mock(return_value=httpx.Response(200, json=jwks_document()))
        yield LogoutTokenVerifier(issuer=ISSUER, client_id=CLIENT_ID)


def reject(v: LogoutTokenVerifier, token: str, reason: str = "invalid") -> None:
    with pytest.raises(VerificationError) as info:
        v.verify(token)
    assert info.value.reason == reason


def test_valid_token_returns_claims(verifier: LogoutTokenVerifier) -> None:
    claims = verifier.verify(mint())
    assert claims.sub == "user_1"
    assert claims.sid == "sess_1"
    assert claims.jti == "jti_1"
    assert isinstance(claims.iat, int)


def test_audience_may_be_a_list_and_sid_alone_is_enough(verifier: LogoutTokenVerifier) -> None:
    claims = verifier.verify(mint(claims={"aud": ["other", CLIENT_ID]}, drop=("sub",)))
    assert claims.sub is None
    assert claims.sid == "sess_1"


def test_sub_alone_is_enough(verifier: LogoutTokenVerifier) -> None:
    assert verifier.verify(mint(drop=("sid",))).sid is None


def test_typ_may_be_absent(verifier: LogoutTokenVerifier) -> None:
    token = jwt.encode(
        jwt.decode(mint(), options={"verify_signature": False}),
        _PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": KID, "typ": None},
    )
    assert verifier.verify(token).jti == "jti_1"


def test_wrong_typ_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(headers={"typ": "JWT"}))


def test_nonce_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(claims={"nonce": "n"}))


def test_missing_events_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(drop=("events",)))


def test_events_without_the_logout_event_object_is_rejected(
    verifier: LogoutTokenVerifier,
) -> None:
    reject(verifier, mint(claims={"events": {"http://example.test/other": {}}}))
    reject(verifier, mint(claims={"events": {BACKCHANNEL_LOGOUT_EVENT: "yes"}}))


def test_wrong_audience_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(claims={"aud": "someone_else"}))


def test_wrong_issuer_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(claims={"iss": "https://evil.test"}))


def test_expired_is_rejected(verifier: LogoutTokenVerifier) -> None:
    now = int(time.time())
    reject(verifier, mint(claims={"iat": now - 600, "exp": now - 300}))


def test_iat_in_the_future_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(claims={"iat": int(time.time()) + 3600}))


def test_missing_iat_or_jti_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(drop=("iat",)))
    reject(verifier, mint(drop=("jti",)))


def test_missing_both_sub_and_sid_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(drop=("sub", "sid")))


def test_bad_signature_is_rejected(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, mint(key=other_key()))


def test_non_rs256_is_rejected(verifier: LogoutTokenVerifier) -> None:
    now = int(time.time())
    token = jwt.encode(
        {
            "iss": ISSUER,
            "aud": CLIENT_ID,
            "sub": "u",
            "iat": now,
            "jti": "j",
            "events": {BACKCHANNEL_LOGOUT_EVENT: {}},
        },
        "a-shared-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
        headers={"kid": KID, "typ": "logout+jwt"},
    )
    reject(verifier, token)


def test_malformed_token(verifier: LogoutTokenVerifier) -> None:
    reject(verifier, "", "malformed")
    reject(verifier, "not-a-jwt", "malformed")


def test_replay_guard() -> None:
    seen: set[str] = set()

    def jti_seen(jti: str) -> bool:
        if jti in seen:
            return True
        seen.add(jti)
        return False

    with respx.mock(assert_all_called=False) as mock:
        mock.get(JWKS).mock(return_value=httpx.Response(200, json=jwks_document()))
        v = LogoutTokenVerifier(issuer=ISSUER, client_id=CLIENT_ID, jti_seen=jti_seen)
        token = mint()
        v.verify(token)
        reject(v, token, "replayed")


def test_explicit_jwks_url_is_used() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://keys.example.test/jwks").mock(
            return_value=httpx.Response(200, json=jwks_document())
        )
        v = LogoutTokenVerifier(
            issuer=ISSUER, client_id=CLIENT_ID, jwks_url="https://keys.example.test/jwks"
        )
        assert v.verify(mint()).sid == "sess_1"


def test_constructor_requires_issuer_and_client_id() -> None:
    with pytest.raises(ValueError):
        LogoutTokenVerifier(issuer="", client_id=CLIENT_ID)
    with pytest.raises(ValueError):
        LogoutTokenVerifier(issuer=ISSUER, client_id="")


def test_logout_token_from_form() -> None:
    assert logout_token_from_form(b"logout_token=a.b.c&x=1") == "a.b.c"
    assert logout_token_from_form("logout_token=a%2Eb.c") == "a.b.c"
    assert logout_token_from_form({"logout_token": "t"}) == "t"
    assert logout_token_from_form({"logout_token": ["t2"]}) == "t2"
    assert logout_token_from_form(b"other=1") == ""


def test_unreachable_jwks_is_no_keys_and_retryable() -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get(JWKS).mock(side_effect=httpx.ConnectError("unreachable"))
        v = LogoutTokenVerifier(issuer=ISSUER, client_id=CLIENT_ID)
        with pytest.raises(VerificationError) as info:
            v.verify(mint())
    assert info.value.reason == "no_keys"
    assert info.value.retryable is True


def test_jwks_5xx_is_retryable() -> None:
    with respx.mock(assert_all_called=False) as mock:
        mock.get(JWKS).mock(return_value=httpx.Response(503))
        v = LogoutTokenVerifier(issuer=ISSUER, client_id=CLIENT_ID)
        with pytest.raises(VerificationError) as info:
            v.verify(mint())
    assert info.value.retryable is True


def test_a_bad_token_is_not_retryable(verifier: LogoutTokenVerifier) -> None:
    with pytest.raises(VerificationError) as info:
        verifier.verify(mint(claims={"aud": "someone-else"}))
    assert info.value.reason == "invalid"
    assert info.value.retryable is False
    with pytest.raises(VerificationError) as malformed:
        verifier.verify("not-a-jwt")
    assert malformed.value.retryable is False
