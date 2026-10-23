"""DPoP (RFC 9449) on the access-token verifier: the same vectors as the TypeScript
@atlasauth/backend suite, plus every other refusal path. Keys are generated per run;
the access tokens are genuine ES256 JWTs and the proofs genuine ES/RS/PS/EdDSA JWSs.
"""

from __future__ import annotations

import base64
import json
import secrets
import time
from typing import Any

import httpx
import jwt
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from jwt.algorithms import ECAlgorithm, OKPAlgorithm, RSAAlgorithm

from atlas_backend import (
    DPOP_ALGS,
    AccessTokenVerifier,
    HmacDpopNonceSource,
    MemoryDpopReplayStore,
    build_www_authenticate,
    dpop_access_token_hash,
    jwk_thumbprint,
    normalize_htu,
    protected_resource_metadata,
)

API = "https://api.example.com/mcp"
META = "https://api.example.com/.well-known/oauth-protected-resource/mcp"
NOW = int(time.time())
_AS_KEY = ec.generate_private_key(ec.SECP256R1())


def _jwks() -> dict[str, Any]:
    jwk = json.loads(ECAlgorithm.to_jwk(_AS_KEY.public_key()))
    jwk.update({"kid": "k1", "alg": "ES256", "use": "sig"})
    return {"keys": [jwk]}


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class Key:
    def __init__(self, alg: str = "ES256") -> None:
        self.alg = alg
        if alg == "ES256":
            self.private: Any = ec.generate_private_key(ec.SECP256R1())
            self.jwk = json.loads(ECAlgorithm.to_jwk(self.private.public_key()))
        elif alg in ("RS256", "PS256"):
            self.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            self.jwk = json.loads(RSAAlgorithm.to_jwk(self.private.public_key()))
        else:
            self.private = ed25519.Ed25519PrivateKey.generate()
            self.jwk = json.loads(OKPAlgorithm.to_jwk(self.private.public_key()))
        self.jwk.pop("key_ops", None)
        self.jkt = jwk_thumbprint(self.jwk)

    def proof(
        self,
        token: str,
        *,
        header: dict[str, Any] | None = None,
        sign_alg: str | None = None,
        iat: int = NOW,
        **claims: Any,
    ) -> str:
        body: dict[str, Any] = {
            "htm": "POST",
            "htu": API,
            "jti": secrets.token_urlsafe(12),
            "iat": iat,
            "ath": dpop_access_token_hash(token),
        }
        for k, v in claims.items():
            if v is None:
                body.pop(k, None)
            else:
                body[k] = v
        h = header if header is not None else {"typ": "dpop+jwt", "jwk": self.jwk}
        return jwt.encode(body, self.private, algorithm=sign_alg or self.alg, headers=h)


def _token(jkt: str | None = None, **extra: Any) -> str:
    claims: dict[str, Any] = {
        "iss": ISSUER,
        "sub": "user_1",
        "aud": API,
        "exp": NOW + 300,
        "token_use": "access_token",
        "scope": "tools:read",
        "client_id": "cli_1",
        "jti": secrets.token_urlsafe(8),
        **extra,
    }
    if jkt:
        claims["cnf"] = {"jkt": jkt}
    return jwt.encode(claims, _AS_KEY, algorithm="ES256", headers={"kid": "k1"})


def _verifier(**opts: Any) -> AccessTokenVerifier:
    return AccessTokenVerifier(
        issuer=ISSUER, audience=API, jwks_url=JWKS_URL, resource_metadata_url=META, **opts
    )


def _verify(v: AccessTokenVerifier, scheme: str, token: str, proof: str | None, **kw: Any):
    kw.setdefault("method", "POST")
    kw.setdefault("url", API + "?x=1")
    return v.verify(f"{scheme} {token}", dpop=proof, **kw)


def _refused(result: Any, error: str) -> None:
    assert not result.ok, result
    assert result.status == 401 and result.error == error, result
    assert result.www_authenticate.startswith("DPoP "), result.www_authenticate
    assert f'error="{error}"' in result.www_authenticate
    assert 'algs="ES256' in result.www_authenticate


@pytest.fixture(autouse=True)
def _jwks_mock():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_jwks()))
        mock.route(host="testserver").pass_through()
        mock.route(host="localhost").pass_through()
        yield


@pytest.mark.parametrize("alg", ["ES256", "RS256", "PS256", "EdDSA"])
def test_accepts_bound_token_with_matching_proof(alg: str) -> None:
    k = Key(alg)
    tok = _token(k.jkt)
    r = _verify(_verifier(), "DPoP", tok, k.proof(tok))
    assert r.ok and r.dpop_bound and r.subject == "user_1", r


def test_unbound_bearer_still_accepted() -> None:
    r = _verify(_verifier(), "Bearer", _token(), None)
    assert r.ok and not r.dpop_bound


def test_never_accepts_bound_token_as_bearer() -> None:
    k = Key()
    tok = _token(k.jkt)
    _refused(_verify(_verifier(), "Bearer", tok, k.proof(tok)), "invalid_token")
    _refused(_verifier().verify(f"DPoP {tok}"), "invalid_dpop_proof")
    unbound = _token()
    _refused(_verify(_verifier(), "DPoP", unbound, k.proof(unbound)), "invalid_token")


def test_rejects_every_bad_proof() -> None:
    v = _verifier(dpop_replay_store=MemoryDpopReplayStore())
    k = Key()
    other = Key()
    tok = _token(k.jkt)
    private_jwk = {**k.jwk, "d": "AAAA"}
    cases = {
        "missing proof": None,
        "malformed": "not-a-jwt",
        "garbage header": "e30.e30.e30",
        "another key": other.proof(tok),
        "wrong htm": k.proof(tok, htm="GET"),
        "wrong htu": k.proof(tok, htu="https://api.example.com/other"),
        "wrong host": k.proof(tok, htu="https://evil.example.com/mcp"),
        "relative htu": k.proof(tok, htu="/mcp"),
        "wrong ath": k.proof(tok, ath="nope"),
        "no ath": k.proof(tok, ath=None),
        "proof for another token": k.proof(_token(k.jkt)),
        "stale": k.proof(tok, iat=NOW - 3600),
        "future": k.proof(tok, iat=NOW + 60),
        "no iat": k.proof(tok, iat=None),  # type: ignore[arg-type]
        "expired exp": k.proof(tok, exp=NOW - 60),
        "no jti": k.proof(tok, jti=None),
        "typ JWT": k.proof(tok, header={"typ": "JWT", "jwk": k.jwk}),
        "alg HS256": jwt.encode(
            {"htm": "POST", "htu": API, "jti": "j", "iat": NOW, "ath": dpop_access_token_hash(tok)},
            "s" * 32,
            algorithm="HS256",
            headers={"typ": "dpop+jwt", "jwk": k.jwk},
        ),
        "alg none": jwt.encode(
            {"htm": "POST", "htu": API, "jti": "j", "iat": NOW},
            None,
            algorithm="none",
            headers={"typ": "dpop+jwt", "jwk": k.jwk},
        ),
        "no jwk": k.proof(tok, header={"typ": "dpop+jwt"}),
        "private jwk": k.proof(tok, header={"typ": "dpop+jwt", "jwk": private_jwk}),
        "alg/key mismatch": Key("RS256").proof(tok, header={"typ": "dpop+jwt", "jwk": k.jwk}),
    }
    good = k.proof(tok)
    h, p, s = good.split(".")
    tampered_payload = _b64(json.dumps({"htm": "POST", "htu": API, "jti": "x"}).encode())
    cases["bad signature"] = f"{h}.{tampered_payload}.{s}"
    for name, proof in cases.items():
        r = _verify(v, "DPoP", tok, proof)
        assert not r.ok, name
        _refused(r, "invalid_dpop_proof")

    once = k.proof(tok, jti="fixed")
    assert _verify(v, "DPoP", tok, once).ok
    _refused(_verify(v, "DPoP", tok, once), "invalid_dpop_proof")
    # The same jti from a different key is a different proof.
    tok_other = _token(other.jkt)
    assert _verify(v, "DPoP", tok_other, other.proof(tok_other, jti="fixed")).ok


def test_require_dpop_refuses_unbound_token() -> None:
    v = _verifier(require_dpop=True)
    _refused(_verify(v, "Bearer", _token(), None), "invalid_token")
    none = v.verify(None)
    assert none.status == 401 and none.error is None
    assert none.www_authenticate.startswith("DPoP ") and 'algs="' in none.www_authenticate


def test_htu_normalisation_and_public_origin() -> None:
    k = Key()
    tok = _token(k.jkt)
    v = _verifier()
    for htu in ("HTTPS://API.Example.COM:443/mcp", "https://api.example.com/mcp?other=2#frag"):
        assert _verify(v, "DPoP", tok, k.proof(tok, htu=htu)).ok, htu
    _refused(_verify(v, "DPoP", tok, k.proof(tok), url="/mcp?x=1"), "invalid_dpop_proof")
    vo = _verifier(public_origin="https://api.example.com")
    assert _verify(vo, "DPoP", tok, k.proof(tok), url="/mcp?x=1", method="post").ok
    assert vo.request_url("https://internal:8080/mcp", "/mcp") == "/mcp"
    assert v.request_url("https://internal:8080/mcp", "/mcp") == "https://internal:8080/mcp"
    for given, want in {
        "https://A.example.com:443": "https://a.example.com/",
        "http://a.example.com:80/x?y#z": "http://a.example.com/x",
        "https://a.example.com:8443/p/": "https://a.example.com:8443/p/",
        "https://[::1]:443/p": "https://[::1]/p",
    }.items():
        assert normalize_htu(given) == want, given
    assert normalize_htu("ftp://x/y") is None


def test_server_nonce() -> None:
    clock = {"t": float(NOW)}
    nonces = HmacDpopNonceSource(b"s" * 32, 60, now=lambda: clock["t"])
    v = _verifier(dpop_nonces=nonces)
    k = Key()
    tok = _token(k.jkt)
    r = _verify(v, "DPoP", tok, k.proof(tok))
    _refused(r, "use_dpop_nonce")
    assert r.dpop_nonce and r.dpop_nonce == nonces.current()
    _refused(_verify(v, "DPoP", tok, k.proof(tok, nonce="made-up")), "use_dpop_nonce")
    ok = _verify(v, "DPoP", tok, k.proof(tok, nonce=r.dpop_nonce))
    assert ok.ok and ok.dpop_nonce
    issued = nonces.current()
    clock["t"] += 60
    assert nonces.valid(issued)
    clock["t"] += 60
    assert not nonces.valid(issued)
    _refused(_verify(v, "DPoP", tok, k.proof(tok, nonce=issued)), "use_dpop_nonce")
    with pytest.raises(ValueError):
        HmacDpopNonceSource(b"short")


def test_helpers() -> None:
    # RFC 7638 §3.1 example key and thumbprint.
    assert (
        jwk_thumbprint(
            {
                "kty": "RSA",
                "e": "AQAB",
                "alg": "RS256",
                "kid": "2011-04-29",
                "n": (
                    "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7"
                    "aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXA"
                    "rwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7"
                    "d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lF"
                    "d2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw"
                ),
            }
        )
        == "NzbLsXh8uDCcd-6MNwXF4W_7noWXFZAfHkxZsRGC9Xs"
    )
    with pytest.raises(ValueError):
        jwk_thumbprint({"kty": "oct", "k": "x"})
    clock = {"t": 1000.0}
    store = MemoryDpopReplayStore(2, now=lambda: clock["t"])
    assert store.claim("a", 1060) and not store.claim("a", 1060)
    clock["t"] = 1120
    assert store.claim("a", 1180)
    store.claim("b", 1180)
    store.claim("c", 1180)
    assert len(store) <= 2
    doc = protected_resource_metadata(
        resource=API, issuer=ISSUER, dpop_bound_access_tokens_required=True
    )
    assert doc["dpop_bound_access_tokens_required"] is True
    assert doc["dpop_signing_alg_values_supported"] == list(DPOP_ALGS)
    assert (
        build_www_authenticate(scheme="DPoP", error="use_dpop_nonce", description="n")
        == f'DPoP error="use_dpop_nonce", error_description="n", algs="{" ".join(DPOP_ALGS)}"'
    )


def test_fastapi_and_flask_dpop_with_nonce() -> None:
    fastapi = pytest.importorskip("fastapi")
    flask = pytest.importorskip("flask")
    from fastapi.testclient import TestClient

    from atlas_backend.fastapi import AtlasAccessToken
    from atlas_backend.flask import access_token_required

    nonces = HmacDpopNonceSource(b"k" * 32)
    v = _verifier(dpop_nonces=nonces, public_origin="https://api.example.com")
    k = Key("EdDSA")
    tok = _token(k.jkt)

    app = fastapi.FastAPI()

    @app.put("/docs/1")
    def put_doc(token=fastapi.Depends(AtlasAccessToken(v))):  # noqa: B008
        return {"bound": token.dpop_bound}

    fapp = flask.Flask(__name__)

    @fapp.put("/docs/1")
    @access_token_required(v)
    def fput_doc():
        return {"bound": flask.g.atlas_access_token.dpop_bound}

    def run(send: Any, prefix: str) -> None:
        def proof(nonce: str | None) -> str:
            return k.proof(
                tok,
                htm="PUT",
                htu="https://api.example.com/docs/1",
                jti=prefix + str(nonce),
                nonce=nonce,
            )

        first = send(proof(None))
        nonce = first.headers.get("DPoP-Nonce")
        assert first.status_code == 401 and nonce, (first.status_code, dict(first.headers))
        assert first.headers["WWW-Authenticate"].startswith('DPoP error="use_dpop_nonce"')
        ok = send(proof(nonce))
        assert ok.status_code == 200 and ok.headers.get("DPoP-Nonce"), ok.text
        replay = send(proof(nonce))
        assert replay.status_code == 401
        assert 'error="invalid_dpop_proof"' in replay.headers["WWW-Authenticate"]

    tc = TestClient(app)
    run(
        lambda p: tc.put("/docs/1?draft=1", headers={"Authorization": f"DPoP {tok}", "DPoP": p}),
        "fastapi-",
    )
    fc = fapp.test_client()
    run(
        lambda p: fc.put("/docs/1?draft=1", headers={"Authorization": f"DPoP {tok}", "DPoP": p}),
        "flask-",
    )
