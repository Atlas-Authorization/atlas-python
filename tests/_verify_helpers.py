"""Shared crypto fixtures for the verification + framework tests.

Mints a REAL RS256 token against a locally-generated RSA key and exposes the
matching JWKS, so the verifier exercises the genuine signature path rather than
a stub — the Python peer of ``verify_test.go``'s ``signToken`` / ``jwksServer``.
"""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

ISSUER = "https://id.atlas.test"
JWKS_URL = "https://id.atlas.test/.well-known/jwks.json"
KID = "kid-test-1"

# One 2048-bit key for the whole suite; a second, unrelated key for the
# tampered-signature case.
_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwks_document(kid: str = KID, key: rsa.RSAPrivateKey | None = None) -> dict[str, Any]:
    """The JWKS the verifier should fetch — a single RSA public key."""
    pub = (key or _PRIVATE_KEY).public_key()
    jwk = json.loads(RSAAlgorithm.to_jwk(pub))
    jwk.update({"kid": kid, "alg": "RS256", "use": "sig"})
    return {"keys": [jwk]}


def mint_token(
    *,
    kid: str = KID,
    key: rsa.RSAPrivateKey | None = None,
    issuer: str = ISSUER,
    sub: str = "user_test_1",
    sid: str = "sess_test_1",
    expires_in: int = 300,
    extra: dict[str, Any] | None = None,
) -> str:
    """Mint a signed RS256 session JWT. ``extra`` overrides/adds claims."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": issuer,
        "sub": sub,
        "sid": sid,
        "iat": now,
        "nbf": now - 5,
        "exp": now + expires_in,
        "org_role": "admin",
        "org_permissions": ["billing:read"],
    }
    if extra:
        claims.update(extra)
    return jwt.encode(
        claims, key or _PRIVATE_KEY, algorithm="RS256", headers={"kid": kid}
    )


def other_key() -> rsa.RSAPrivateKey:
    """An unrelated signing key, for the tampered-signature case."""
    return _OTHER_KEY
