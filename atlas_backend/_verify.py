"""§7.3 session-token verification for customer backends — the Python peer of
``verify.ts`` / ``verify.go`` / ``SessionVerifier.php``.

The design constraint that matters is what this does NOT do: it never calls
Atlas on the hot path. A customer's API handling thousands of requests a second
cannot make an outbound call to verify each one, and a verifier that did would
make Atlas's availability the customer's availability. So the default path is
local RS256 verification against cached JWKS, and the revocation window is
bounded instead by the short token lifetime.

The actual RSA/RS256 cryptography is delegated to :mod:`jwt` (PyJWT, with its
``cryptography`` backend) — this module never implements a signature primitive
itself. What it owns is the Atlas policy on top: the kid-miss-throttled JWKS
cache (§7.3), the issuer check, the §13.1 OP token-confusion guard, and the
optional ``azp`` allowlist.

    from atlas_backend import AtlasBackend

    atlas = AtlasBackend(
        jwks_url="https://id.atlasauth.net/.well-known/jwks.json",
        issuer="https://id.atlasauth.net",
    )
    claims = atlas.verify(session_jwt)   # raises VerificationError on failure
    print(claims.user_id, claims.has_permission("billing:read"))
"""

from __future__ import annotations

import base64
import json
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

#: §7.3's five seconds either side, matching the server's minting tolerance.
CLOCK_SKEW_SECONDS = 5

#: §7.3's at-most-one JWKS refetch per minute, however many kid-misses arrive.
#: The rate limit is a security property, not politeness: it stops an attacker
#: sending random kids from turning this process into a traffic amplifier aimed
#: at the JWKS endpoint.
REFETCH_INTERVAL_MS = 60_000

#: The JWKS cache TTL (§7.3 serves ``Cache-Control: max-age=3600``).
DEFAULT_TTL_MS = 3_600_000


# --------------------------------------------------------------------------- #
# Result + error shapes                                                       #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SessionClaims:
    """The decoded payload of a verified Atlas session JWT.

    Known claims are typed; everything else is available in :attr:`raw`. The
    subject id is exposed both as :attr:`sub` and the friendlier
    :attr:`user_id`.
    """

    iss: str = ""
    sub: str = ""
    sid: str = ""
    exp: int = 0
    nbf: int = 0
    iat: int = 0
    azp: str = ""
    sv: int = 0
    mfa: bool = False
    org_id: str = ""
    org_slug: str = ""
    org_role: str = ""
    org_permissions: list[str] = field(default_factory=list)

    #: The full claim set, including any not modelled above.
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def user_id(self) -> str:
        """The authenticated user id (the ``sub`` claim)."""
        return self.sub

    def has_role(self, role: str) -> bool:
        """Whether the session's ``org_role`` equals ``role``."""
        return self.org_role == role

    def has_permission(self, permission: str) -> bool:
        """Whether ``org_permissions`` contains ``permission``.

        Reading the claim rather than calling Atlas is the whole point of
        putting permissions in the token: a permission change takes effect
        within one token lifetime, the same bound as revocation.
        """
        return permission in self.org_permissions

    @classmethod
    def from_raw(cls, claims: Mapping[str, Any]) -> SessionClaims:
        """Build a :class:`SessionClaims` from a decoded claim mapping."""
        perms = claims.get("org_permissions")
        return cls(
            iss=str(claims.get("iss", "")),
            sub=str(claims.get("sub", "")),
            sid=str(claims.get("sid", "")),
            exp=int(claims.get("exp", 0) or 0),
            nbf=int(claims.get("nbf", 0) or 0),
            iat=int(claims.get("iat", 0) or 0),
            azp=str(claims.get("azp", "")),
            sv=int(claims.get("sv", 0) or 0),
            mfa=bool(claims.get("mfa", False)),
            org_id=str(claims.get("org_id", "")),
            org_slug=str(claims.get("org_slug", "")),
            org_role=str(claims.get("org_role", "")),
            org_permissions=list(perms) if isinstance(perms, (list, tuple)) else [],
            raw=dict(claims),
        )


@dataclass(frozen=True)
class AtlasUser:
    """A minimal, framework-agnostic principal built from a verified session.

    Carries the user :attr:`id` and the full :attr:`claims`. The
    ``is_authenticated`` / ``is_anonymous`` flags mirror Django's / DRF's
    ``request.user`` contract so this can stand in as the request user.
    """

    id: str
    claims: SessionClaims
    is_authenticated: bool = True
    is_anonymous: bool = False

    @classmethod
    def from_claims(cls, claims: SessionClaims) -> AtlasUser:
        return cls(id=claims.user_id, claims=claims)


class VerificationError(Exception):
    """Raised when a token fails verification.

    :attr:`reason` is coarse by design — telling a caller whether the
    signature, issuer, or expiry was wrong helps someone refining a forged
    token more than a developer debugging a real one. Its values are
    ``"malformed"``, ``"invalid"``, ``"no_keys"``, and ``"unauthorized_party"``.
    """

    MALFORMED = "malformed"
    INVALID = "invalid"
    NO_KEYS = "no_keys"
    UNAUTHORIZED_PARTY = "unauthorized_party"

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"atlas: token verification failed: {reason}")


# --------------------------------------------------------------------------- #
# JWKS cache                                                                  #
# --------------------------------------------------------------------------- #


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


class JwksCache:
    """Caches an instance's JWKS in-process, refetching on a kid-miss at most
    once a minute.

    A stale JWKS still verifies every token signed by a key it contains, so it
    degrades to "new keys do not work yet", never "nobody can authenticate".
    The outcome of the last :meth:`get` is exposed on :attr:`last_outcome`
    (one of ``fresh``, ``cached``, ``refetched``, ``throttled``, ``failed``) so
    a caller or a test can assert the rate limit actually bit.
    """

    def __init__(
        self,
        url: str,
        *,
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
        ttl_ms: int = DEFAULT_TTL_MS,
        refetch_interval_ms: int = REFETCH_INTERVAL_MS,
    ) -> None:
        self._url = url
        self._http = http_client
        self._now = now or (lambda: int(time.time() * 1000))
        self._ttl_ms = ttl_ms
        self._refetch_interval_ms = refetch_interval_ms
        self._lock = threading.Lock()
        self._cached: dict[str, Any] | None = None
        self._fetched_at = 0
        self._last_attempt_at = 0
        self.last_outcome = "fresh"

    @staticmethod
    def read_kid(token: str) -> str | None:
        """Read the ``kid`` from a JWT header without verifying anything."""
        parts = token.split(".")
        if not parts or not parts[0]:
            return None
        try:
            header = json.loads(_b64url_decode(parts[0]))
        except (ValueError, json.JSONDecodeError):
            return None
        kid = header.get("kid") if isinstance(header, dict) else None
        return kid if isinstance(kid, str) else None

    def _has(self, kid: str | None) -> bool:
        if self._cached is None:
            return False
        keys = self._cached.get("keys", [])
        if not kid:
            return len(keys) > 0
        return any(k.get("kid") == kid for k in keys)

    def get(self, kid: str | None = None) -> dict[str, Any] | None:
        """The JWKS to verify against, refetching if this ``kid`` is unknown.

        Returns whatever is cached when a refetch is throttled or fails.
        """
        with self._lock:
            now = self._now()
            expired = self._cached is None or now - self._fetched_at >= self._ttl_ms
            kid_miss = self._cached is not None and not self._has(kid)

            if not expired and not kid_miss:
                self.last_outcome = "cached"
                return self._cached

            # The throttle: a kid-miss inside the window is answered from cache,
            # and the token simply fails to verify.
            if (
                kid_miss
                and not expired
                and now - self._last_attempt_at < self._refetch_interval_ms
            ):
                self.last_outcome = "throttled"
                return self._cached

            self._last_attempt_at = now
            try:
                fetched = self._fetch()
            except Exception:
                # Keep serving what we have. A JWKS outage should degrade to
                # "new keys do not work yet", not "nobody can authenticate".
                self.last_outcome = "failed"
                return self._cached

            self._cached = fetched
            self._fetched_at = now
            self.last_outcome = "refetched" if kid_miss else "fresh"
            return self._cached

    def _fetch(self) -> dict[str, Any]:
        owns = self._http is None
        client = self._http or httpx.Client(timeout=10.0)
        try:
            resp = client.get(self._url, headers={"accept": "application/json"})
        finally:
            if owns:
                client.close()
        resp.raise_for_status()
        body = resp.json()
        if not isinstance(body, dict) or not isinstance(body.get("keys"), list):
            raise ValueError("atlas: JWKS is malformed")
        return {"keys": list(body["keys"])}

    def snapshot(self) -> dict[str, int]:
        """Test and diagnostic surface — never used for a security decision."""
        with self._lock:
            keys = 0 if self._cached is None else len(self._cached.get("keys", []))
            return {"keys": keys, "fetched_at": self._fetched_at}


# --------------------------------------------------------------------------- #
# Session verifier                                                            #
# --------------------------------------------------------------------------- #


class AtlasBackend:
    """Verifies Atlas session JWTs locally against the instance JWKS, with
    caching.

    Args:
        jwks_url: The instance's JWKS URL. Required.
        issuer: The expected ``iss``. Required — an unchecked issuer accepts any
            Atlas instance's tokens.
        authorized_parties: When set, a token minted for a different origin
            (§7.3 ``azp`` allowlist) is refused.
        http_client: An optional pre-configured :class:`httpx.Client` shared by
            the JWKS cache.
        leeway: Clock-skew tolerance in seconds for ``exp``/``nbf``.
        now / ttl_ms / refetch_interval_ms: JWKS-cache tuning (mostly for tests).
    """

    def __init__(
        self,
        *,
        jwks_url: str,
        issuer: str,
        authorized_parties: list[str] | None = None,
        http_client: httpx.Client | None = None,
        leeway: int = CLOCK_SKEW_SECONDS,
        now: Callable[[], int] | None = None,
        ttl_ms: int = DEFAULT_TTL_MS,
        refetch_interval_ms: int = REFETCH_INTERVAL_MS,
    ) -> None:
        if not jwks_url:
            raise ValueError("AtlasBackend requires jwks_url.")
        if not issuer:
            raise ValueError(
                "AtlasBackend requires a non-empty issuer; an unchecked issuer "
                "accepts any Atlas instance's tokens."
            )
        self._issuer = issuer
        self._authorized_parties = list(authorized_parties or [])
        self._leeway = leeway
        self.jwks = JwksCache(
            jwks_url,
            http_client=http_client,
            now=now,
            ttl_ms=ttl_ms,
            refetch_interval_ms=refetch_interval_ms,
        )

    def verify(self, token: str) -> SessionClaims:
        """Verify a token locally.

        No network call unless the ``kid`` is unknown, and at most one of those
        a minute. Returns :class:`SessionClaims` on success; raises
        :class:`VerificationError` on any failure.
        """
        # Import lazily so `import atlas_backend` does not require the crypto
        # backend to be importable until a token is actually verified.
        import jwt  # PyJWT
        from jwt.algorithms import RSAAlgorithm

        if not token or token.count(".") != 2:
            raise VerificationError(VerificationError.MALFORMED)

        kid = JwksCache.read_kid(token)
        keyset = self.jwks.get(kid)
        if not keyset or not keyset.get("keys"):
            raise VerificationError(VerificationError.NO_KEYS)

        jwk = self._select_jwk(keyset["keys"], kid)
        if jwk is None:
            raise VerificationError(VerificationError.INVALID)

        try:
            # from_jwk returns a public/private union; a public JWK always
            # yields a public key, which jwt.decode accepts.
            key: Any = RSAAlgorithm.from_jwk(json.dumps(jwk))
            # ``from_jwk`` + algorithms=["RS256"] pins RS256, so a token whose
            # header says alg:none — or any algorithm coerced onto the key
            # material — fails to decode. Signature + exp/nbf (with leeway) + iss
            # are all enforced here by PyJWT.
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                issuer=self._issuer,
                leeway=self._leeway,
                options={"verify_aud": False, "require": ["exp"]},
            )
        except jwt.InvalidTokenError:
            # One reason for every failure. Telling a caller whether the
            # signature, the issuer or the expiry was wrong helps someone
            # refining a forged token far more than it helps a developer.
            raise VerificationError(VerificationError.INVALID) from None

        # §13.1 token-confusion guard. An OP access token
        # (``token_use: "access_token"``) and an id_token (carries ``aud``) are
        # signed with the SAME per-instance RS256 key, issuer and ``typ: "JWT"``
        # header as a first-party session JWT. Reject any token carrying an OP
        # marker so a "Sign in with Atlas" RP cannot replay one as a customer
        # session. An ABSENT token_use/aud is a valid session (backward-compat),
        # so this never mass-invalidates a live fleet.
        token_use = claims.get("token_use")
        if (token_use is not None and token_use != "session") or "aud" in claims:
            raise VerificationError(VerificationError.INVALID)

        if self._authorized_parties:
            azp = claims.get("azp")
            if not isinstance(azp, str) or azp not in self._authorized_parties:
                raise VerificationError(VerificationError.UNAUTHORIZED_PARTY)

        return SessionClaims.from_raw(claims)

    def authenticate(
        self,
        *,
        authorization: str | None = None,
        session_cookie: str | None = None,
    ) -> SessionClaims:
        """Verify whatever a request carries.

        An ``Authorization: Bearer <jwt>`` header wins over a ``__session``
        cookie value — a deliberately-set header should not be overridden by a
        stale cookie. Raises :class:`VerificationError` when neither carries a
        token or the token is invalid.
        """
        token = ""
        if authorization and authorization.startswith("Bearer "):
            token = authorization[len("Bearer ") :].strip()
        elif session_cookie:
            token = session_cookie
        if not token:
            raise VerificationError(VerificationError.MALFORMED)
        return self.verify(token)

    @staticmethod
    def _select_jwk(
        keys: list[dict[str, Any]], kid: str | None
    ) -> dict[str, Any] | None:
        for k in keys:
            if k.get("kty") != "RSA":
                continue
            if kid and k.get("kid") != kid:
                continue
            return k
        return None


# --------------------------------------------------------------------------- #
# End-user API-key verification (online, POST /v1/api_keys/verify)            #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ApiKeyVerification:
    """The verdict of :meth:`ApiKeyVerifier.verify`.

    A failed verification is ``valid = False``, NOT an exception — every
    negative (unknown, malformed, revoked, expired, since-deleted subject)
    resolves to the same ``valid = False`` so a caller learns nothing about
    which keys exist.
    """

    valid: bool = False
    id: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    claims: dict[str, Any] | None = None
    last_used_at: int | None = None


class ApiKeyVerifier:
    """Verifies end-user ``ak_`` API keys against Atlas with separate
    positive/negative caches.

    Unlike session-token verification this is an ONLINE check — the key's
    validity lives server-side. Results are cached with a longer positive TTL
    (a key that just verified stays valid) and a short negative TTL (a caller
    hammering a bad key is answered locally, yet a fixed key starts working
    again within seconds).
    """

    DEFAULT_POSITIVE_TTL_MS = 300_000
    DEFAULT_NEGATIVE_TTL_MS = 30_000

    def __init__(
        self,
        secret_key: str,
        *,
        base_url: str = "https://api.atlasauth.net",
        http_client: httpx.Client | None = None,
        now: Callable[[], int] | None = None,
        positive_ttl_ms: int = DEFAULT_POSITIVE_TTL_MS,
        negative_ttl_ms: int = DEFAULT_NEGATIVE_TTL_MS,
    ) -> None:
        if not secret_key:
            raise ValueError("ApiKeyVerifier requires a secret_key.")
        self._secret_key = secret_key
        self._base_url = base_url.rstrip("/")
        self._http = http_client
        self._now = now or (lambda: int(time.time() * 1000))
        self._positive_ttl_ms = positive_ttl_ms
        self._negative_ttl_ms = negative_ttl_ms
        self._lock = threading.Lock()
        self._positive: dict[str, tuple[int, ApiKeyVerification]] = {}
        self._negative: dict[str, tuple[int, ApiKeyVerification]] = {}

    def verify(self, secret: str) -> ApiKeyVerification:
        """Verify a presented ``ak_`` secret.

        A cache hit makes no network call. A transport/auth failure (e.g. a bad
        ``sk_`` key → 401) raises :class:`.AtlasError`, never a silent
        ``valid = False``, and is never cached as a negative.
        """
        now = self._now()
        cached = self._cached(secret, now)
        if cached is not None:
            return cached

        from ._errors import AtlasError

        url = f"{self._base_url}/v1/api_keys/verify"
        headers = {
            "authorization": f"Bearer {self._secret_key}",
            "content-type": "application/json",
            "accept": "application/json",
        }
        owns = self._http is None
        client = self._http or httpx.Client(timeout=30.0)
        try:
            resp = client.post(url, headers=headers, json={"secret": secret})
        finally:
            if owns:
                client.close()

        if not resp.is_success:
            # A non-2xx is a transport/config problem, not a verdict about the
            # presented key — surface it, and never cache it as a negative.
            raise AtlasError(
                resp.status_code,
                [{"message": f"api-key verify returned HTTP {resp.status_code}"}],
            )

        body = resp.json()
        verdict = ApiKeyVerification(
            valid=bool(body.get("valid", False)),
            id=body.get("id"),
            subject_type=body.get("subject_type"),
            subject_id=body.get("subject_id"),
            claims=body.get("claims"),
            last_used_at=body.get("last_used_at"),
        )

        ttl = self._positive_ttl_ms if verdict.valid else self._negative_ttl_ms
        store = self._positive if verdict.valid else self._negative
        with self._lock:
            store[secret] = (now + ttl, verdict)
        return verdict

    def _cached(self, secret: str, now: int) -> ApiKeyVerification | None:
        with self._lock:
            for store in (self._positive, self._negative):
                hit = store.get(secret)
                if hit is not None:
                    expires_at, verdict = hit
                    if now < expires_at:
                        return verdict
                    del store[secret]
        return None
