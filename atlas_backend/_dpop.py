"""DPoP proof verification (RFC 9449) for :class:`~atlas_backend.AccessTokenVerifier`.

A DPoP-bound access token carries ``cnf.jkt``, the RFC 7638 thumbprint of the
client's key. Each request must then arrive with the ``DPoP`` scheme and a ``DPoP``
header: a short-lived JWT (``typ`` ``dpop+jwt``) signed by that key, carrying the
public key itself, the request method (``htm``) and URL (``htu``), the hash of the
access token (``ath``), a unique ``jti``, and the server's nonce when the API asks
for one.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
from collections.abc import Mapping
from typing import Any, Callable, Protocol
from urllib.parse import urljoin, urlsplit

__all__ = [
    "DPOP_ALGS",
    "DPOP_PROOF_MAX_AGE_SECONDS",
    "DpopReplayStore",
    "MemoryDpopReplayStore",
    "DpopNonceSource",
    "HmacDpopNonceSource",
    "jwk_thumbprint",
    "dpop_access_token_hash",
    "normalize_htu",
]

#: How old a DPoP proof may be.
DPOP_PROOF_MAX_AGE_SECONDS = 300
#: Clock skew tolerated on a DPoP proof ``iat``.
DPOP_CLOCK_SKEW_SECONDS = 5
#: The JWS algorithms accepted on a DPoP proof (and advertised in challenges / metadata).
DPOP_ALGS: tuple[str, ...] = (
    "ES256",
    "ES384",
    "ES512",
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
    "EdDSA",
)
_EC_CURVES = {"ES256": "P-256", "ES384": "P-384", "ES512": "P-521"}
_PRIVATE_MEMBERS = ("d", "k", "p", "q", "dp", "dq", "qi")


class DpopReplayStore(Protocol):
    """Guards against a DPoP proof being used twice. ``claim`` records ``key`` until
    ``expires_at`` (epoch seconds) and returns ``False`` when it was already recorded.
    Share one store (Redis ``SET NX EX``, a unique database key, ...) when the API runs
    in more than one process."""

    def claim(self, key: str, expires_at: float) -> bool: ...


class MemoryDpopReplayStore:
    """The in-process replay store: entries live until they expire, at most ``max_entries``."""

    def __init__(self, max_entries: int = 10_000, *, now: Callable[[], float] | None = None):
        self._max = max_entries if max_entries > 0 else 10_000
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()
        self._now = now or time.time

    def claim(self, key: str, expires_at: float) -> bool:
        with self._lock:
            now = self._now()
            if self._seen.get(key, 0) > now:
                return False
            self._seen[key] = expires_at
            if len(self._seen) > self._max:
                for k in [k for k, exp in self._seen.items() if exp <= now]:
                    del self._seen[k]
                while len(self._seen) > self._max:
                    oldest = min((k for k in self._seen if k != key), key=self._seen.__getitem__)
                    del self._seen[oldest]
            return True

    def __len__(self) -> int:
        return len(self._seen)


class DpopNonceSource(Protocol):
    """Hands out the server nonce a DPoP proof must carry (RFC 9449 §8) and checks one.
    ``current()`` goes to the client in the ``DPoP-Nonce`` header; ``valid()`` accepts
    the nonces still in force."""

    def current(self) -> str: ...

    def valid(self, nonce: str) -> bool: ...


class HmacDpopNonceSource:
    """Nonces derived from a secret and the clock: a nonce is good for the window it was
    issued in and the next one, so every process sharing the secret agrees without
    shared state. ``secret`` must be at least 32 bytes."""

    def __init__(
        self,
        secret: bytes,
        window_seconds: int = 300,
        *,
        now: Callable[[], float] | None = None,
    ) -> None:
        if len(secret) < 32:
            raise ValueError("The DPoP nonce secret must be at least 32 bytes.")
        self._secret = bytes(secret)
        self._window = window_seconds if window_seconds > 0 else 300
        self._now = now or time.time

    def _at(self, epoch: int) -> str:
        mac = hmac.new(
            self._secret, b"atlas-dpop-nonce:" + epoch.to_bytes(8, "big", signed=True), "sha256"
        )
        return _b64u(mac.digest())

    def _epoch(self) -> int:
        return int(self._now() // self._window)

    def current(self) -> str:
        return self._at(self._epoch())

    def valid(self, nonce: str) -> bool:
        e = self._epoch()
        return any(hmac.compare_digest(self._at(x), nonce) for x in (e, e - 1))


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(value: str) -> bytes:
    if not isinstance(value, str) or "=" in value:
        raise ValueError("bad base64url")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def dpop_access_token_hash(token: str) -> str:
    """The ``ath`` a DPoP proof carries for ``token``: base64url(SHA-256(token))."""
    return _b64u(hashlib.sha256(token.encode("ascii")).digest())


def jwk_thumbprint(jwk: Mapping[str, Any]) -> str:
    """The RFC 7638 SHA-256 thumbprint (base64url) of a public EC, RSA or OKP JWK: the
    ``cnf.jkt`` a DPoP-bound token carries."""
    members = {
        "EC": ("crv", "kty", "x", "y"),
        "RSA": ("e", "kty", "n"),
        "OKP": ("crv", "kty", "x"),
    }.get(jwk.get("kty"))  # type: ignore[arg-type]
    if members is None:
        raise ValueError(f"Unsupported JWK kty {jwk.get('kty')!r}.")
    picked = {}
    for m in members:
        v = jwk.get(m)
        if not isinstance(v, str) or not v:
            raise ValueError(f"JWK member {m} is missing.")
        picked[m] = v
    canonical = json.dumps(picked, separators=(",", ":"), sort_keys=True)
    return _b64u(hashlib.sha256(canonical.encode("utf-8")).digest())


def normalize_htu(url: str) -> str | None:
    """Reduce a URL to the form RFC 9449 §4.3 compares ``htu`` in: scheme and host
    lower-cased, the default port dropped, an empty path as ``/``, no query or fragment.
    ``None`` for anything but an absolute http(s) URL."""
    if not isinstance(url, str):
        return None
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https") or not parts.hostname:
        return None
    host = parts.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    if port is not None and not (
        (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    ):
        host = f"{host}:{port}"
    return f"{scheme}://{host}{parts.path or '/'}"


def _verify_signature(jwk: Mapping[str, Any], alg: str, signing_input: bytes, sig: bytes) -> bool:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from jwt.algorithms import get_default_algorithms

    if isinstance(jwk.get("alg"), str) and jwk["alg"] and jwk["alg"] != alg:
        return False
    kty = jwk.get("kty")
    if alg.startswith("ES"):
        if kty != "EC" or jwk.get("crv") != _EC_CURVES[alg]:
            return False
    elif alg[:2] in ("RS", "PS"):
        if kty != "RSA":
            return False
    elif alg == "EdDSA":
        if kty != "OKP" or jwk.get("crv") not in ("Ed25519", "Ed448"):
            return False
    else:
        return False
    try:
        algo = get_default_algorithms()[alg]
        key = algo.from_jwk(json.dumps(dict(jwk)))
        if hasattr(key, "private_bytes"):
            return False
        if isinstance(key, rsa.RSAPublicKey) and key.key_size < 2048:
            return False
        return bool(algo.verify(signing_input, key, sig))
    except Exception:
        return False


def check_dpop_proof(
    proof: str,
    *,
    token: str,
    jkt: str,
    method: str,
    url: str,
    public_origin: str | None,
    now: float,
    replay: DpopReplayStore,
    nonces: DpopNonceSource | None,
) -> tuple[str, str] | None:
    """Check one proof. ``None`` when it is good, else ``(error, description)`` with
    error ``invalid_dpop_proof`` or ``use_dpop_nonce``."""

    def bad(desc: str) -> tuple[str, str]:
        return ("invalid_dpop_proof", desc)

    parts = proof.split(".")
    if len(parts) != 3:
        return bad("The DPoP proof is malformed.")
    try:
        header = json.loads(_b64u_decode(parts[0]))
    except Exception:
        return bad("The DPoP proof is malformed.")
    if not isinstance(header, dict):
        return bad("The DPoP proof is malformed.")
    if header.get("typ") != "dpop+jwt":
        return bad("The DPoP proof must have typ dpop+jwt.")
    alg = header.get("alg")
    if alg not in DPOP_ALGS:
        return bad("The DPoP proof uses an unsupported algorithm.")
    jwk = header.get("jwk")
    if not isinstance(jwk, dict):
        return bad("The DPoP proof must carry its public key.")
    if any(m in jwk for m in _PRIVATE_MEMBERS):
        return bad("The DPoP proof key must be a public key.")
    try:
        sig = _b64u_decode(parts[2])
    except Exception:
        return bad("The DPoP proof signature is invalid.")
    if not _verify_signature(jwk, alg, f"{parts[0]}.{parts[1]}".encode("ascii"), sig):
        return bad("The DPoP proof signature is invalid.")
    try:
        payload = json.loads(_b64u_decode(parts[1]))
    except Exception:
        return bad("The DPoP proof is malformed.")
    if not isinstance(payload, dict):
        return bad("The DPoP proof is malformed.")
    try:
        thumb = jwk_thumbprint(jwk)
    except ValueError:
        thumb = ""
    if not thumb or not hmac.compare_digest(thumb, jkt):
        return bad("The DPoP proof key does not match the token binding.")
    if payload.get("htm") != method:
        return bad("The DPoP proof htm does not match the request method.")
    target: str | None = url
    if not url.lower().startswith(("http://", "https://")):
        target = urljoin(public_origin, url) if public_origin else None
    expected = normalize_htu(target) if target else None
    htu = payload.get("htu")
    if expected is None or not isinstance(htu, str) or normalize_htu(htu) != expected:
        return bad("The DPoP proof htu does not match the request URL.")
    iat = payload.get("iat")
    if (
        isinstance(iat, bool)
        or not isinstance(iat, (int, float))
        or iat > now + DPOP_CLOCK_SKEW_SECONDS
        or now - iat > DPOP_PROOF_MAX_AGE_SECONDS
    ):
        return bad("The DPoP proof is too old or from the future.")
    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and not isinstance(exp, bool):
        if now >= exp + DPOP_CLOCK_SKEW_SECONDS:
            return bad("The DPoP proof is too old or from the future.")
    if payload.get("ath") != dpop_access_token_hash(token):
        return bad("The DPoP proof ath does not match the access token.")
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        return bad("The DPoP proof needs a jti.")
    if nonces is not None:
        nonce = payload.get("nonce")
        if not isinstance(nonce, str) or not nonce or not nonces.valid(nonce):
            return (
                "use_dpop_nonce",
                "The DPoP proof must carry the nonce from the DPoP-Nonce header.",
            )
    if not replay.claim(f"{jkt}:{jti}", float(iat) + DPOP_PROOF_MAX_AGE_SECONDS):
        return bad("The DPoP proof has already been used.")
    return None
