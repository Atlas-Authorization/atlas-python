from __future__ import annotations

import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from atlas_backend import sign_api_key_assertion


def _pem(key: object) -> str:
    return key.private_bytes(  # type: ignore[attr-defined]
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def test_es256_assertion_is_raw_rs_and_verifies() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    token = sign_api_key_assertion(_pem(key), "key_1", "ins_1", scope="read", jti="j1")
    header = jwt.get_unverified_header(token)
    assert header == {"alg": "ES256", "kid": "key_1", "typ": "JWT"}
    claims = jwt.decode(token, key.public_key(), algorithms=["ES256"], audience="ins_1")
    assert claims["iss"] == "key_1" and claims["jti"] == "j1" and claims["scope"] == "read"
    assert claims["exp"] - claims["iat"] == 300
    signing_input, sig = token.rsplit(".", 1)
    raw = jwt.utils.base64url_decode(sig)
    assert len(raw) == 64
    key.public_key().verify(
        encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")),
        signing_input.encode(),
        ec.ECDSA(hashes.SHA256()),
    )


def test_eddsa_assertion_verifies() -> None:
    key = ed25519.Ed25519PrivateKey.generate()
    token = sign_api_key_assertion(_pem(key), "key_2", "ins_1", ttl_seconds=60)
    assert jwt.get_unverified_header(token)["alg"] == "EdDSA"
    claims = jwt.decode(token, key.public_key(), algorithms=["EdDSA"], audience="ins_1")
    assert claims["exp"] - claims["iat"] == 60 and claims["jti"]


# -- the key mirror verifies assertions locally -------------------------------------------------


class _Keys:
    def __init__(self, row: dict) -> None:
        self.row = row

    def create(self, body: dict, idempotency_key: str | None = None) -> dict:
        return self.row


def _mirror(now: int = 1_800_000_000_000, **row: object):
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    from atlas_backend import KeyMirror

    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    base = {"id": "key_1", "subject_type": "user", "subject_id": "u1", "scopes": ["read", "write"], "secret": None,
            "credential": "key_pair", "audience": "ins_1", "public_key": pub}
    mirror = KeyMirror(api_keys=_Keys({**base, **row}), now=lambda: now)
    mirror.mint({})
    return mirror, _pem(key), now // 1000


def _sign(pem: str, now_s: int, **kw: object) -> str:
    import atlas_backend._api_key_assertion as mod

    real = mod.time.time
    mod.time.time = lambda: now_s  # type: ignore[assignment]
    try:
        return sign_api_key_assertion(pem, "key_1", kw.pop("audience", "ins_1"), **kw)  # type: ignore[arg-type]
    finally:
        mod.time.time = real  # type: ignore[assignment]


def test_mirror_verifies_assertion_and_narrows_scope() -> None:
    m, pem, now = _mirror()
    r = m.verify_assertion(_sign(pem, now, scope="read", jti="a"), required_scopes=["read"])
    assert r.valid and r.credential == "key_pair" and r.jti == "a" and r.effective_scopes == ["read"]
    assert m.verify_assertion(_sign(pem, now, scope="admin")).code == "scope_not_granted"
    assert m.verify_assertion(_sign(pem, now, scope="read"), required_scopes=["write"]).code == "insufficient_scope"


def test_mirror_refuses_with_server_codes_and_claims_jti_last() -> None:
    m, pem, now = _mirror()
    assert m.verify_assertion(_sign(pem, now, audience="other")).code == "wrong_audience"
    assert m.verify_assertion(_sign(pem, now - 1000, ttl_seconds=300)).code == "assertion_expired"
    assert m.verify_assertion(_sign(pem, now + 500)).code == "assertion_not_yet_valid"
    assert m.verify_assertion(_sign(pem, now, ttl_seconds=7200)).code == "assertion_lifetime_too_long"
    assert m.verify_assertion("a.b.c").code == "invalid_assertion"
    assert m.verify_assertion(_sign(pem, now)[:-4] + "AAAA").code == "invalid_assertion"
    # a refused assertion never burns its jti
    t = _sign(pem, now, jti="j1")
    assert m.verify_assertion(t, required_scopes=["nope"]).code == "insufficient_scope"
    assert m.verify_assertion(t).valid
    assert m.verify_assertion(t).code == "assertion_replayed"


def test_mirror_assertion_revoked_and_ip() -> None:
    m, pem, now = _mirror(allowed_ips=["10.0.0.0/8"])
    assert m.verify_assertion(_sign(pem, now)).code == "client_ip_required"
    assert m.verify_assertion(_sign(pem, now), client_ip="8.8.8.8").code == "ip_not_allowed"
    assert m.verify_assertion(_sign(pem, now), client_ip="10.1.1.1").valid
    m.store.mark_revoked("key_1", now)
    assert not m.verify_assertion(_sign(pem, now), client_ip="10.1.1.1").valid


def test_mirror_disabled_key_is_refused_and_webhook_copies_enabled() -> None:
    m, pem, now = _mirror()
    m.store.put({**m.store.get("key_1"), "enabled": False})
    assert m.verify_assertion(_sign(pem, now)).code == "invalid_assertion"
    assert m.apply_webhook({"type": "api_key.updated", "data": {"id": "key_1", "enabled": True}})
    assert m.verify_assertion(_sign(pem, now)).valid
    # the secret path refuses a disabled row too
    from atlas_backend import KeyMirror

    class Keys(_Keys):
        pass

    sm = KeyMirror(api_keys=Keys({"id": "k2", "secret": "ak_s", "enabled": False}))
    sm.mint({})
    assert not sm.verify("ak_s").valid
    sm.apply_webhook({"type": "api_key.updated", "data": {"id": "k2", "enabled": True}})
    assert sm.verify("ak_s").valid
