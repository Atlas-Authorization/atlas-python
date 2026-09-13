"""Tests for the cross-property SSO handshake, including the PKCE binding.

All HTTP is mocked with respx — no network. Covers the PKCE pair helper
(S256 correctness, unpadded base64url, freshness) and that the redeem calls
carry ``code_verifier`` in the JSON body alongside ``user_id``/``nonce``.
"""

from __future__ import annotations

import base64
import hashlib
import json

import httpx
import pytest
import respx

from atlas_backend import (
    HandshakeParams,
    PKCEPair,
    aredeem_handshake,
    create_pkce_pair,
    read_handshake_params,
    redeem_handshake,
)

FAPI = "https://id.atlasauth.test"
REDEEM_URL = f"{FAPI}/v1/client/handshake/redeem"
PK = "pk_test_deadbeefdeadbeef"

_SESSION_BODY = {
    "jwt": "jwt-value",
    "refresh_token": "rt-value",
    "session_id": "sess_1",
    "expires_in": 60,
}


def _b64url_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


# --------------------------------------------------------------------------- #
# create_pkce_pair — RFC 7636 S256 correctness                                #
# --------------------------------------------------------------------------- #


def test_pkce_challenge_is_s256_of_verifier_unpadded() -> None:
    pair = create_pkce_pair()
    assert isinstance(pair, PKCEPair)

    # The challenge must be base64url(sha256(verifier)) with NO padding.
    expected = _b64url_no_pad(hashlib.sha256(pair.verifier.encode("ascii")).digest())
    assert pair.challenge == expected

    # Neither member carries base64 padding, and both are URL/header-safe
    # (unpadded base64url has no '=', '+' or '/').
    for token in (pair.verifier, pair.challenge):
        assert "=" not in token
        assert "+" not in token
        assert "/" not in token

    # The SHA-256 challenge is always 32 bytes → 43 unpadded base64url chars.
    assert len(pair.challenge) == 43


def test_pkce_verifier_has_256_bits_of_entropy_in_rfc_window() -> None:
    pair = create_pkce_pair()
    # 32 random bytes → 43 unpadded base64url chars, inside RFC 7636's 43..128.
    assert len(pair.verifier) == 43
    assert 43 <= len(pair.verifier) <= 128
    # Round-trips as base64url (add padding back) to exactly 32 bytes.
    padded = pair.verifier + "=" * (-len(pair.verifier) % 4)
    assert len(base64.urlsafe_b64decode(padded)) == 32


def test_pkce_pairs_are_fresh_each_call() -> None:
    a = create_pkce_pair()
    b = create_pkce_pair()
    assert a.verifier != b.verifier
    assert a.challenge != b.challenge


def test_pkce_pair_unpacks_like_a_tuple() -> None:
    verifier, challenge = create_pkce_pair()
    assert _b64url_no_pad(hashlib.sha256(verifier.encode("ascii")).digest()) == challenge


# --------------------------------------------------------------------------- #
# redeem_handshake — code_verifier is sent in the body                        #
# --------------------------------------------------------------------------- #


@respx.mock
def test_redeem_sends_code_verifier_in_body() -> None:
    route = respx.post(REDEEM_URL).mock(return_value=httpx.Response(200, json=_SESSION_BODY))

    session = redeem_handshake(
        fapi_origin=FAPI,
        publishable_key=PK,
        user_id="user_1",
        nonce="nonce_1",
        code_verifier="verifier_1",
    )

    assert session is not None
    assert session.jwt == "jwt-value"
    assert session.refresh_token == "rt-value"

    req = route.calls.last.request
    assert req.headers["x-publishable-key"] == PK
    assert json.loads(req.content) == {
        "user_id": "user_1",
        "nonce": "nonce_1",
        "code_verifier": "verifier_1",
    }
    # The verifier is a credential — it must never surface in the URL.
    assert "verifier_1" not in str(req.url)


@respx.mock
def test_redeem_round_trips_a_real_pkce_verifier() -> None:
    route = respx.post(REDEEM_URL).mock(return_value=httpx.Response(200, json=_SESSION_BODY))
    pair = create_pkce_pair()

    redeem_handshake(
        fapi_origin=FAPI,
        publishable_key=PK,
        user_id="user_1",
        nonce="nonce_1",
        code_verifier=pair.verifier,
    )

    body = json.loads(route.calls.last.request.content)
    assert body["code_verifier"] == pair.verifier
    # Server-side check the SDK is feeding: challenge == S256(verifier).
    assert _b64url_no_pad(hashlib.sha256(body["code_verifier"].encode("ascii")).digest()) == (
        pair.challenge
    )


@respx.mock
def test_redeem_returns_none_on_rejected_verifier() -> None:
    respx.post(REDEEM_URL).mock(
        return_value=httpx.Response(
            400, json={"errors": [{"code": "HANDSHAKE_INVALID", "message": "bad pkce"}]}
        )
    )
    out = redeem_handshake(
        fapi_origin=FAPI,
        publishable_key=PK,
        user_id="user_1",
        nonce="nonce_1",
        code_verifier="wrong",
    )
    assert out is None


@respx.mock
async def test_async_redeem_sends_code_verifier() -> None:
    route = respx.post(REDEEM_URL).mock(return_value=httpx.Response(200, json=_SESSION_BODY))

    session = await aredeem_handshake(
        fapi_origin=FAPI,
        publishable_key=PK,
        user_id="user_2",
        nonce="nonce_2",
        code_verifier="verifier_2",
    )

    assert session is not None
    assert json.loads(route.calls.last.request.content) == {
        "user_id": "user_2",
        "nonce": "nonce_2",
        "code_verifier": "verifier_2",
    }


# --------------------------------------------------------------------------- #
# read_handshake_params (return-leg parsing)                                  #
# --------------------------------------------------------------------------- #


def test_read_params_parses_ok_return_url() -> None:
    params = read_handshake_params(
        "https://sat.example.com/cb?__atlas_hs=ok&__atlas_hu=user_9&__atlas_hn=nonce_9"
    )
    assert params == HandshakeParams(user_id="user_9", nonce="nonce_9")


def test_read_params_none_when_not_ok() -> None:
    assert read_handshake_params("?__atlas_hs=fail&__atlas_hu=u&__atlas_hn=n") is None
    assert read_handshake_params("?__atlas_hs=ok&__atlas_hu=u") is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
