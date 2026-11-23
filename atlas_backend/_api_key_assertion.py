"""Sign the short-lived assertion a key-pair API key presents instead of a secret."""

from __future__ import annotations

import secrets
import time
from typing import Any

import jwt

__all__ = ["sign_api_key_assertion"]


def sign_api_key_assertion(
    private_key_pem: str,
    key_id: str,
    audience: str,
    ttl_seconds: int = 300,
    scope: str | None = None,
    jti: str | None = None,
) -> str:
    """Return a signed JWT for a key-pair API key (ES256 for P-256, EdDSA for Ed25519).

    ``private_key_pem`` is the PKCS#8 PEM Atlas returned once at create. Present the
    result as ``token`` to ``client.api_keys.verify`` or as ``assertion`` to
    ``client.api_keys.create_token``. PyJWT emits ES256 as raw ``r || s``.
    """
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    key = load_pem_private_key(private_key_pem.encode(), password=None)
    alg = "EdDSA" if isinstance(key, ed25519.Ed25519PrivateKey) else "ES256"
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": key_id,
        "aud": audience,
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": jti or secrets.token_urlsafe(16),
    }
    if scope:
        claims["scope"] = scope
    return jwt.encode(claims, key, algorithm=alg, headers={"kid": key_id, "typ": "JWT"})


def parse_assertion(token: Any) -> tuple[dict[str, Any], dict[str, Any], str, bytes] | None:
    """Split a compact JWS into (header, claims, signing_input, signature); ``None`` when malformed."""
    import base64
    import json

    if not isinstance(token, str):
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        dec = [base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)) for p in parts]
        header, claims = json.loads(dec[0]), json.loads(dec[1])
    except ValueError:
        return None
    if not isinstance(header, dict) or not isinstance(claims, dict):
        return None
    return header, claims, f"{parts[0]}.{parts[1]}", dec[2]


def verify_assertion_signature(header: dict[str, Any], signing_input: str, signature: bytes, public_key_pem: str) -> bool:
    """Check the signature with an SPKI PEM public key; the header ``alg`` must match the key's type."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    alg = header.get("alg")
    try:
        key = load_pem_public_key(public_key_pem.encode())
        data = signing_input.encode()
        if alg == "ES256" and isinstance(key, ec.EllipticCurvePublicKey) and key.curve.name == "secp256r1":
            if len(signature) != 64:
                return False
            der = encode_dss_signature(int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big"))
            key.verify(der, data, ec.ECDSA(hashes.SHA256()))
            return True
        if alg == "EdDSA" and isinstance(key, ed25519.Ed25519PublicKey):
            key.verify(signature, data)
            return True
    except (InvalidSignature, ValueError, TypeError):
        pass
    return False
