"""Session tokens, ID tokens, logout tokens, status lists and transaction tokens verify under each of the five
signing algorithms, with the key type checked against ``alg`` (no algorithm confusion; ``none`` / HS* refused)."""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa

from atlas_backend import SIGNING_ALGS, LogoutTokenVerifier, VerificationError, verify_transaction_token
from atlas_backend._verify import jwk_public_key

ISS = "https://id.example.test"
CASES: list[tuple[str, Any]] = [
    ("RS256", rsa.generate_private_key(public_exponent=65537, key_size=2048)),
    ("PS256", rsa.generate_private_key(public_exponent=65537, key_size=2048)),
    ("ES256", ec.generate_private_key(ec.SECP256R1())),
    ("ES384", ec.generate_private_key(ec.SECP384R1())),
    ("EdDSA", ed25519.Ed25519PrivateKey.generate()),
]


def _jwk(alg: str, key: Any, declare_alg: bool = True) -> dict[str, Any]:
    cls = {"RS256": jwt.algorithms.RSAAlgorithm, "PS256": jwt.algorithms.RSAAlgorithm, "ES256": jwt.algorithms.ECAlgorithm,
           "ES384": jwt.algorithms.ECAlgorithm, "EdDSA": jwt.algorithms.OKPAlgorithm}[alg]
    jwk = json.loads(cls.to_jwk(key.public_key()))
    jwk["kid"] = f"k-{alg}"
    if declare_alg:
        jwk["alg"] = alg
    return jwk


def test_all_five_algorithms_are_accepted() -> None:
    assert set(SIGNING_ALGS) == {a for a, _ in CASES}


@pytest.mark.parametrize(("alg", "key"), CASES)
@pytest.mark.parametrize("declare_alg", [True, False])
def test_logout_token_verifies_per_algorithm(alg: str, key: Any, declare_alg: bool) -> None:
    now = int(time.time())
    token = jwt.encode(
        {"iss": ISS, "aud": "c1", "iat": now, "jti": "j", "sid": "s", "events": {"http://schemas.openid.net/event/backchannel-logout": {}}},
        key, algorithm=alg, headers={"kid": f"k-{alg}", "typ": "logout+jwt"},
    )
    verifier = LogoutTokenVerifier(issuer=ISS, client_id="c1")
    verifier.jwks = type("J", (), {"last_outcome": "fresh", "get": lambda self, kid=None: {"keys": [_jwk(alg, key, declare_alg)]}})()  # type: ignore[assignment]
    assert verifier.verify(token).sid == "s"


@pytest.mark.parametrize(("alg", "key"), CASES)
def test_transaction_token_verifies_per_algorithm(alg: str, key: Any) -> None:
    now = int(time.time())
    claims = {"iss": ISS, "aud": "td", "sub": "u", "txn": "t", "scope": "a b", "req_wl": "w", "iat": now, "exp": now + 60}
    token = jwt.encode(claims, key, algorithm=alg, headers={"kid": f"k-{alg}", "typ": "txntoken+jwt"})
    out = verify_transaction_token(token, issuer=ISS, trust_domain="td", jwks={"keys": [_jwk(alg, key, False)]})
    assert out.ok and out.scopes == ["a", "b"]


@pytest.mark.parametrize(("alg", "key"), CASES)
def test_key_type_must_match_alg(alg: str, key: Any) -> None:
    jwk = _jwk(alg, key, False)
    _, chosen = jwk_public_key(jwk, alg)
    assert chosen == alg
    # An RSA key never verifies an EC/EdDSA alg and vice versa: the key decides, the token's alg is only a hint.
    for other, _ in CASES:
        if jwk["kty"] != "RSA" and other != alg:
            assert jwk_public_key(jwk, other)[1] == alg


def test_none_and_hmac_never_verify() -> None:
    now = int(time.time())
    key = CASES[0][1]
    jwk = _jwk("RS256", key, False)
    claims = {"iss": ISS, "aud": "td", "sub": "u", "txn": "t", "scope": "a", "req_wl": "w", "iat": now, "exp": now + 60}
    forged_none = jwt.encode(claims, None, algorithm="none", headers={"typ": "txntoken+jwt"})
    pem = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key())
    forged_hs = jwt.encode(claims, "x" * 40, algorithm="HS256", headers={"typ": "txntoken+jwt"})
    for forged in (forged_none, forged_hs):
        assert not verify_transaction_token(forged, issuer=ISS, trust_domain="td", jwks={"keys": [jwk]}).ok
    assert pem
    now_s = int(time.time())
    logout = jwt.encode({"iss": ISS, "aud": "c1", "iat": now_s, "jti": "j", "sid": "s", "events": {"http://schemas.openid.net/event/backchannel-logout": {}}},
                        "x" * 40, algorithm="HS256", headers={"kid": "k-RS256", "typ": "logout+jwt"})
    v = LogoutTokenVerifier(issuer=ISS, client_id="c1")
    v.jwks = type("J", (), {"last_outcome": "fresh", "get": lambda self, kid=None: {"keys": [jwk]}})()  # type: ignore[assignment]
    with pytest.raises(VerificationError):
        v.verify(logout)


def test_rsa_key_declaring_rs256_refuses_a_ps256_token() -> None:
    key = CASES[0][1]
    jwk = _jwk("RS256", key, True)
    now = int(time.time())
    token = jwt.encode({"iss": ISS, "aud": "td", "sub": "u", "txn": "t", "scope": "a", "req_wl": "w", "iat": now, "exp": now + 60},
                       key, algorithm="PS256", headers={"typ": "txntoken+jwt"})
    assert not verify_transaction_token(token, issuer=ISS, trust_domain="td", jwks={"keys": [jwk]}).ok
