"""Tests for the base session-JWT verifier, JWKS cache, and API-key verifier.

All HTTP is mocked with respx — no network. The token is a genuine RS256 JWT
signed by a locally-minted key (see ``_verify_helpers``), so the signature path
is real, not stubbed.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token, other_key

from atlas_backend import (
    ApiKeyVerification,
    ApiKeyVerifier,
    AtlasBackend,
    AtlasError,
    JwksCache,
    SessionClaims,
    VerificationError,
)


def _backend(**kwargs: object) -> AtlasBackend:
    return AtlasBackend(jwks_url=JWKS_URL, issuer=ISSUER, **kwargs)  # type: ignore[arg-type]


@respx.mock
def test_verifies_valid_token_and_exposes_claims() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    claims = _backend().verify(mint_token())

    assert isinstance(claims, SessionClaims)
    assert claims.user_id == "user_test_1"
    assert claims.sub == "user_test_1"
    assert claims.sid == "sess_test_1"
    assert claims.has_role("admin")
    assert claims.has_permission("billing:read")
    assert not claims.has_permission("billing:write")
    assert claims.raw["iss"] == ISSUER


@respx.mock
def test_rejects_wrong_issuer() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    token = mint_token(issuer="https://evil.example.com")
    with pytest.raises(VerificationError) as exc:
        _backend().verify(token)
    assert exc.value.reason == VerificationError.INVALID


@respx.mock
def test_rejects_expired_token() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    token = mint_token(expires_in=-3600)
    with pytest.raises(VerificationError) as exc:
        _backend().verify(token)
    assert exc.value.reason == VerificationError.INVALID


@respx.mock
def test_rejects_tampered_signature() -> None:
    # JWKS serves the real key, but the token is signed with an unrelated key.
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    token = mint_token(key=other_key())
    with pytest.raises(VerificationError) as exc:
        _backend().verify(token)
    assert exc.value.reason == VerificationError.INVALID


def test_rejects_malformed_without_network() -> None:
    # No respx route registered: a malformed token must fail before any fetch.
    with pytest.raises(VerificationError) as exc:
        _backend().verify("not-a-jwt")
    assert exc.value.reason == VerificationError.MALFORMED


@respx.mock
def test_rejects_op_token_use_and_aud() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    b = _backend()

    with pytest.raises(VerificationError):
        b.verify(mint_token(extra={"token_use": "access_token"}))
    with pytest.raises(VerificationError):
        b.verify(mint_token(extra={"aud": "some-client"}))

    # token_use == "session" is explicitly fine.
    assert b.verify(mint_token(extra={"token_use": "session"})).user_id == "user_test_1"


@respx.mock
def test_authorized_parties_allowlist() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    b = _backend(authorized_parties=["https://app.example.com"])

    with pytest.raises(VerificationError) as exc:
        b.verify(mint_token(extra={"azp": "https://evil.example.com"}))
    assert exc.value.reason == VerificationError.UNAUTHORIZED_PARTY

    good = b.verify(mint_token(extra={"azp": "https://app.example.com"}))
    assert good.azp == "https://app.example.com"


@respx.mock
def test_authenticate_prefers_header_over_cookie() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    b = _backend()
    token = mint_token()

    assert b.authenticate(authorization=f"Bearer {token}").user_id == "user_test_1"
    assert b.authenticate(session_cookie=token).user_id == "user_test_1"
    with pytest.raises(VerificationError) as exc:
        b.authenticate()
    assert exc.value.reason == VerificationError.MALFORMED


def test_requires_issuer_and_jwks_url() -> None:
    with pytest.raises(ValueError):
        AtlasBackend(jwks_url=JWKS_URL, issuer="")
    with pytest.raises(ValueError):
        AtlasBackend(jwks_url="", issuer=ISSUER)


# --------------------------------------------------------------------------- #
# JWKS cache: kid-miss refetch throttle (§7.3)                                #
# --------------------------------------------------------------------------- #


@respx.mock
def test_jwks_cache_throttles_kid_miss() -> None:
    route = respx.get(JWKS_URL).mock(
        return_value=httpx.Response(200, json=jwks_document())
    )
    clock = {"ms": 1_700_000_000_000}
    b = AtlasBackend(
        jwks_url=JWKS_URL,
        issuer=ISSUER,
        now=lambda: clock["ms"],
    )

    # First verify populates the cache: one fetch.
    b.verify(mint_token())
    assert route.call_count == 1

    # Past the refetch interval, an unknown kid triggers exactly one refetch.
    clock["ms"] += 120_000
    with pytest.raises(VerificationError):
        b.verify(mint_token(kid="kid-unknown"))
    assert route.call_count == 2
    assert b.jwks.last_outcome == "refetched"

    # A second kid-miss at the same instant is throttled: no new fetch.
    with pytest.raises(VerificationError):
        b.verify(mint_token(kid="kid-unknown"))
    assert route.call_count == 2
    assert b.jwks.last_outcome == "throttled"


def test_jwks_read_kid() -> None:
    assert JwksCache.read_kid(mint_token(kid="abc")) == "abc"
    assert JwksCache.read_kid("garbage") is None


# --------------------------------------------------------------------------- #
# API-key verifier (online, with positive/negative caching)                   #
# --------------------------------------------------------------------------- #

API = "https://api.example.test"


@respx.mock
def test_api_key_verify_valid_and_caches() -> None:
    route = respx.post(f"{API}/v1/api_keys/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "valid": True,
                "id": "ak_1",
                "subject_type": "user",
                "subject_id": "user_9",
            },
        )
    )
    v = ApiKeyVerifier("sk_test_x", base_url=API)

    out = v.verify("ak_secret")
    assert isinstance(out, ApiKeyVerification)
    assert out.valid and out.subject_id == "user_9"

    # A second call is served from the positive cache: no second request.
    v.verify("ak_secret")
    assert route.call_count == 1


@respx.mock
def test_api_key_verify_invalid_is_not_an_error() -> None:
    respx.post(f"{API}/v1/api_keys/verify").mock(
        return_value=httpx.Response(200, json={"valid": False})
    )
    out = ApiKeyVerifier("sk_test_x", base_url=API).verify("ak_bad")
    assert out.valid is False


@respx.mock
def test_api_key_verify_non_2xx_raises() -> None:
    respx.post(f"{API}/v1/api_keys/verify").mock(
        return_value=httpx.Response(401, json={"errors": [{"message": "bad sk"}]})
    )
    with pytest.raises(AtlasError) as exc:
        ApiKeyVerifier("sk_bad", base_url=API).verify("ak_secret")
    assert exc.value.status == 401
