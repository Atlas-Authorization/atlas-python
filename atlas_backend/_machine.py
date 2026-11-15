"""The device side of machine enrolment, for a service or device of your own: generate an Ed25519 key,
enrol with a token or a short code, then trade a signed challenge for short-lived machine tokens,
cached until shortly before they expire.

    from atlas_backend import MachineClient, FileMachineStore

    machine = MachineClient(issuer="https://id.example.com", store=FileMachineStore("~/.config/app/machine.json"))
    machine.enroll(credential="XXXX-XXXX", name="build-agent-7")
    token = machine.get_token(audience="https://api.example.com", scopes=["reports:read"])
    headers = {"authorization": f"{token.token_type} {token.token}"}

The challenge signature is pure Ed25519 over the nonce's UTF-8 bytes (base64url). With ``dpop_key``
every token is bound to a DPoP key (RFC 9449; Ed25519 or P-256): send :meth:`MachineClient.dpop_proof`
with each call to your API. :func:`create_dpop_proof` signs a proof on its own.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class MachineStore(Protocol):
    """Where a machine keeps its identity (``issuer``, ``machine_id``, ``private_key_pem``,
    ``public_key_pem``, ``enrolled_at``). The private key never leaves it; implement this for a keychain."""

    def load(self) -> dict[str, Any] | None: ...
    def save(self, identity: dict[str, Any]) -> None: ...
    def clear(self) -> None: ...


class FileMachineStore:
    """A store backed by one file, written 0600 in a 0700 directory."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path).expanduser()

    def load(self) -> dict[str, Any] | None:
        try:
            value = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError):
            return None
        return value if isinstance(value, dict) else None

    def save(self, identity: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=self.path.name + ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json.dumps(identity))
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class MemoryMachineStore:
    """A store that forgets on exit (tests, short-lived jobs that enrol every run)."""

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._value = initial

    def load(self) -> dict[str, Any] | None:
        return self._value

    def save(self, identity: dict[str, Any]) -> None:
        self._value = identity

    def clear(self) -> None:
        self._value = None


class MachineClientError(Exception):
    """Atlas refused a request. ``code`` is the machine-readable error code when the response had one."""

    def __init__(self, status: int, code: str | None, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def sign_machine_challenge(private_key_pem: str, nonce: str) -> str:
    """``base64url(sign(private_key, nonce))``: pure Ed25519 over the nonce's UTF-8 bytes."""
    from cryptography.hazmat.primitives import serialization

    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    return _b64u(key.sign(nonce.encode("utf-8")))  # type: ignore[call-arg,union-attr]


def public_key_pem_of(private_key_pem: str) -> str:
    """The SPKI PEM of the key's public half (what enrolment registered)."""
    from cryptography.hazmat.primitives import serialization

    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    return key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()


def generate_dpop_key() -> str:
    """A new Ed25519 key for DPoP, as a PKCS#8 PEM. Keep it as safely as the machine's own key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    return (
        Ed25519PrivateKey.generate()
        .private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        .decode()
    )


def _public_jwk(private_key_pem: str) -> tuple[dict[str, str], str, Any]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519

    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    if isinstance(key, ed25519.Ed25519PrivateKey):
        raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return {"kty": "OKP", "crv": "Ed25519", "x": _b64u(raw)}, "EdDSA", key
    if isinstance(key, ec.EllipticCurvePrivateKey) and key.curve.name == "secp256r1":
        nums = key.public_key().public_numbers()
        coord = lambda n: _b64u(n.to_bytes(32, "big"))  # noqa: E731
        return {"kty": "EC", "crv": "P-256", "x": coord(nums.x), "y": coord(nums.y)}, "ES256", key
    raise ValueError("A DPoP key must be Ed25519 or P-256.")


def dpop_thumbprint(private_key_pem: str) -> str:
    """The RFC 7638 thumbprint of the key: the ``cnf.jkt`` a token minted with its proofs carries."""
    jwk, _, _ = _public_jwk(private_key_pem)
    canonical = json.dumps({k: jwk[k] for k in sorted(jwk)}, separators=(",", ":"))
    return _b64u(hashlib.sha256(canonical.encode()).digest())


def create_dpop_proof(
    private_key_pem: str,
    method: str,
    url: str,
    *,
    access_token: str | None = None,
    nonce: str | None = None,
    now: Callable[[], int] | None = None,
) -> str:
    """Sign one DPoP proof (RFC 9449) for one request. ``url`` is the full request URL (query and fragment are
    dropped); pass ``access_token`` when calling a resource server so the proof names the token, and ``nonce``
    when the server answered ``use_dpop_nonce``."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

    jwk, alg, key = _public_jwk(private_key_pem)
    u = urlsplit(url)
    payload: dict[str, Any] = {
        "jti": secrets.token_urlsafe(16),
        "htm": method.upper(),
        "htu": f"{u.scheme}://{u.netloc}{u.path}",
        "iat": (now or (lambda: int(time.time() * 1000)))() // 1000,
    }
    if access_token:
        payload["ath"] = _b64u(hashlib.sha256(access_token.encode()).digest())
    if nonce:
        payload["nonce"] = nonce
    header = {"typ": "dpop+jwt", "alg": alg, "jwk": jwk}
    signing_input = f"{_b64u(json.dumps(header).encode())}.{_b64u(json.dumps(payload).encode())}"
    if alg == "EdDSA":
        sig = key.sign(signing_input.encode())
    else:
        r, s = decode_dss_signature(key.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256())))
        sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{signing_input}.{_b64u(sig)}"


@dataclass(frozen=True)
class MachineToken:
    token: str
    #: ``DPoP`` when bound to this client's key (send ``Authorization: DPoP <token>`` plus a proof), else ``Bearer``.
    token_type: str
    #: Epoch ms when the token stops being valid.
    expires_at: int
    audience: str | None = None
    scope: str | None = None
    #: The grant's ``constraints`` as the token carries them. Your API enforces them.
    constraints: dict[str, Any] | None = None
    organization_id: str | None = None


@dataclass(frozen=True)
class MachineEnrolResult:
    machine_id: str
    status: str
    #: True when an administrator must approve the machine before it can get tokens.
    approval_required: bool


class MachineClient:
    """Enrol a machine and mint its tokens. Thread-safe; concurrent callers asking for the same thing share one mint.

    Args:
        issuer: your instance's issuer URL (the ``iss`` of its tokens).
        store: a :class:`MachineStore` (:class:`FileMachineStore` or :class:`MemoryMachineStore`).
        refresh_skew_seconds: fetch a new token this long before the cached one expires (default 60).
        dpop_key: a PKCS#8 PEM (Ed25519 or P-256), or ``True`` for a key made in memory for this client.
    """

    def __init__(
        self,
        *,
        issuer: str,
        store: MachineStore,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
        refresh_skew_seconds: int = 60,
        dpop_key: str | bool | None = None,
    ) -> None:
        self.issuer = issuer.rstrip("/")
        self.store = store
        self._http = http_client or httpx.Client(timeout=30.0)
        self._now = now or (lambda: int(time.time() * 1000))
        self._skew = refresh_skew_seconds * 1000
        self._dpop_key = generate_dpop_key() if dpop_key is True else (dpop_key or None)
        self._cache: dict[str, MachineToken] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def _post(self, path: str, body: Mapping[str, Any], proof: bool = False) -> dict[str, Any]:
        url = f"{self.issuer}{path}"
        headers = {"content-type": "application/json"}
        if proof and self._dpop_key:
            headers["dpop"] = create_dpop_proof(self._dpop_key, "POST", url, now=self._now)  # type: ignore[arg-type]
        res = self._http.post(url, headers=headers, content=json.dumps(body))
        try:
            out = res.json() if res.text else {}
        except ValueError:
            out = {}  # a non-JSON error page: fall through to the status
        out = out if isinstance(out, dict) else {}
        if not res.is_success:
            errs = out.get("errors")
            first = errs[0] if isinstance(errs, list) and errs and isinstance(errs[0], dict) else {}
            raise MachineClientError(
                res.status_code,
                first.get("code") or (out["code"] if isinstance(out.get("code"), str) else None),
                first.get("message") or (out["message"] if isinstance(out.get("message"), str) else f"Request failed with status {res.status_code}."),
            )
        return out

    def _identity(self) -> dict[str, Any] | None:
        i = self.store.load()
        return i if i and i.get("issuer") == self.issuer else None

    def enroll(self, *, credential: str, name: str, metadata: Mapping[str, Any] | None = None, device_key: str | None = None) -> MachineEnrolResult:
        """Generate a key, enrol with a ``met_`` token or a short code, and store the identity.
        The private key is created here and only its public half is sent."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        key = Ed25519PrivateKey.generate()
        private_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        public_pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        body: dict[str, Any] = {"enrolment_token": credential.strip(), "name": name, "public_key_pem": public_pem}
        if metadata:
            body["metadata"] = dict(metadata)
        if device_key:
            body["device_key"] = device_key
        res = self._post("/v1/machines/enroll", body)
        self.store.save(
            {
                "issuer": self.issuer,
                "machine_id": res["id"],
                "private_key_pem": private_pem,
                "public_key_pem": public_pem,
                "enrolled_at": res.get("enrolled_at") or self._now(),
            }
        )
        with self._guard:
            self._cache.clear()
        return MachineEnrolResult(res["id"], res["status"], bool(res.get("approval_required")))

    def is_enrolled(self) -> bool:
        return self._identity() is not None

    def machine_id(self) -> str | None:
        i = self._identity()
        return i["machine_id"] if i else None

    def _mint(self, audience: str | None, scopes: Sequence[str] | None, scope_presets: Sequence[str] | None, organization_id: str | None) -> MachineToken:
        ident = self._identity()
        if not ident:
            raise MachineClientError(0, "not_enrolled", "This machine is not enrolled. Call enroll() first.")
        challenge = self._post("/v1/machines/challenge", {"machine_id": ident["machine_id"]})
        body: dict[str, Any] = {
            "machine_id": ident["machine_id"],
            "nonce": challenge["nonce"],
            "signature": sign_machine_challenge(ident["private_key_pem"], challenge["nonce"]),
        }
        if audience:
            body["audience"] = audience
        if scopes is not None:
            body["scopes"] = list(scopes)
        if scope_presets is not None:
            body["scope_presets"] = list(scope_presets)
        if organization_id:
            body["organization_id"] = organization_id
        res = self._post("/v1/machines/token", body, proof=True)
        return MachineToken(
            token=res["token"],
            token_type="DPoP" if res.get("token_type") == "DPoP" else "Bearer",
            expires_at=self._now() + int(res["expires_in"]) * 1000,
            audience=res.get("audience"),
            scope=res.get("scope"),
            constraints=res.get("constraints"),
            organization_id=res.get("organization_id"),
        )

    def get_token(
        self,
        *,
        audience: str | None = None,
        scopes: Sequence[str] | None = None,
        scope_presets: Sequence[str] | None = None,
        organization_id: str | None = None,
    ) -> MachineToken:
        """A machine token for this request, from the cache while it has more than the refresh skew left.
        ``audience`` (a resource server identifier) becomes the token's ``aud``; ``scopes`` /
        ``scope_presets`` need it."""
        key = json.dumps([audience or "", sorted(scopes or []), sorted(scope_presets or []), organization_id or ""])
        with self._guard:
            hit = self._cache.get(key)
            if hit and hit.expires_at - self._skew > self._now():
                return hit
            lock = self._locks.setdefault(key, threading.Lock())
        with lock:  # concurrent callers asking for the same thing share one mint
            with self._guard:
                hit = self._cache.get(key)
            if hit and hit.expires_at - self._skew > self._now():
                return hit
            token = self._mint(audience, scopes, scope_presets, organization_id)
            with self._guard:
                self._cache[key] = token
            return token

    def dpop_proof(self, *, token: str, method: str, url: str, nonce: str | None = None) -> str:
        """A DPoP proof for one call to your API with a token this client minted. Needs ``dpop_key``."""
        if not self._dpop_key:
            raise MachineClientError(0, "dpop_not_configured", "Create the client with the `dpop_key` option to sign DPoP proofs.")
        return create_dpop_proof(self._dpop_key, method, url, access_token=token, nonce=nonce, now=self._now)  # type: ignore[arg-type]

    def dpop_thumbprint(self) -> str | None:
        """The thumbprint (``cnf.jkt``) tokens minted by this client carry, or ``None`` without a ``dpop_key``."""
        return dpop_thumbprint(self._dpop_key) if self._dpop_key else None  # type: ignore[arg-type]

    def clear_tokens(self) -> None:
        """Forget cached tokens (the stored identity stays)."""
        with self._guard:
            self._cache.clear()

    def reset(self) -> None:
        """Forget the identity too: the machine must enrol again."""
        self.clear_tokens()
        self.store.clear()
