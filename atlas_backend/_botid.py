"""Vercel BotID for Atlas: the signing half that runs next to your BotID check.

BotID's verdict (``checkBotId()``) only exists inside a Vercel-hosted request, so that
route turns it into a short signed attestation; the browser sends it to Atlas as
``captcha_token``, and Atlas checks the signature, freshness and ``is_bot == False``,
and spends it (each attestation passes once). The same secret is stored in Atlas for
the ``vercel_botid`` captcha provider.

Format (version 1): ``atlas_botid.v1.<payload>.<sig>`` — ``payload`` is base64url JSON
``{v: 1, is_bot, verified_bot, iat, exp, jti}``; ``sig`` is base64url HMAC-SHA256 over
``atlas_botid.v1.<payload>`` keyed by the shared secret.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

__all__ = [
    "BOTID_ATTESTATION_PREFIX",
    "BOTID_ATTESTATION_MAX_TTL_SECONDS",
    "BOTID_SECRET_MIN_LENGTH",
    "create_botid_attestation",
]

BOTID_ATTESTATION_PREFIX = "atlas_botid.v1."
BOTID_ATTESTATION_MAX_TTL_SECONDS = 300
BOTID_SECRET_MIN_LENGTH = 32


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def create_botid_attestation(
    secret: str,
    *,
    is_bot: bool,
    is_verified_bot: bool = False,
    ttl_seconds: int = 60,
    now: float | None = None,
) -> str:
    """Sign a BotID verdict for Atlas. Raises ``ValueError`` when the secret is shorter
    than 32 characters (Atlas would refuse every attestation it signs). A bot verdict is
    still signed — Atlas refuses it. ``ttl_seconds`` is clamped to 1–300."""
    if not isinstance(secret, str) or len(secret) < BOTID_SECRET_MIN_LENGTH:
        raise ValueError(
            f"The BotID attestation secret must be at least {BOTID_SECRET_MIN_LENGTH} characters."
        )
    ttl = min(max(int(ttl_seconds), 1), BOTID_ATTESTATION_MAX_TTL_SECONDS)
    iat = int(now if now is not None else time.time())
    payload = _b64u(
        json.dumps(
            {
                "v": 1,
                "is_bot": bool(is_bot),
                "verified_bot": bool(is_verified_bot),
                "iat": iat,
                "exp": iat + ttl,
                "jti": _b64u(secrets.token_bytes(18)),
            },
            separators=(",", ":"),
        ).encode()
    )
    sig = hmac.new(
        secret.encode(), (BOTID_ATTESTATION_PREFIX + payload).encode(), hashlib.sha256
    ).digest()
    return f"{BOTID_ATTESTATION_PREFIX}{payload}.{_b64u(sig)}"
