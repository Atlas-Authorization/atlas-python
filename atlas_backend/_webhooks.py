"""Verify an inbound Atlas webhook, for the customer consuming events.

Atlas signs every delivery: ``atlas-signature: v1,<base64>`` is HMAC-SHA256 over
``<id>.<timestamp>.<raw body>`` keyed with the endpoint secret (``whsec_...``),
with ``atlas-id`` and ``atlas-timestamp`` (epoch ms) headers. A delivery more
than five minutes from now, in either direction, is refused so a captured
request cannot be replayed. Matches ``verifyWebhook`` in ``@atlasauth/backend``.

Verify over the RAW request body, before any JSON parse: re-serializing
reorders keys and breaks the MAC.

    from atlas_backend import verify_webhook

    result = verify_webhook(request.body, request.headers, secret)
    if not result.verified:
        return 400
    if already_handled(result.delivery_id):   # retries carry the same id
        return 200
    handle(result.event)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional, Union

REPLAY_TOLERANCE_MS = 5 * 60_000
HEADER_ID = "atlas-id"
HEADER_TIMESTAMP = "atlas-timestamp"
HEADER_SIGNATURE = "atlas-signature"


@dataclass(frozen=True)
class WebhookVerification:
    """The outcome of :func:`verify_webhook`. Never raised: check ``verified``."""

    verified: bool
    #: Why verification failed: ``missing_headers``, ``malformed_signature``,
    #: ``stale_timestamp`` or ``signature_mismatch``.
    reason: Optional[str] = None
    #: The parsed envelope ``{id, type, timestamp, instance_id, data}`` (verified only).
    event: Optional[dict[str, Any]] = None
    #: The signed ``atlas-id`` header (verified only). The same on every retry of
    #: one event, so it is the key to deduplicate deliveries on.
    delivery_id: Optional[str] = None
    #: The signed ``atlas-timestamp`` header, epoch ms (verified only).
    timestamp: Optional[int] = None


def _header(headers: Mapping[str, Any], name: str) -> Optional[str]:
    for key, value in headers.items():
        if str(key).lower() == name:
            if isinstance(value, (list, tuple)):
                value = value[0] if value else None
            return None if value is None else str(value)
    return None


def verify_webhook(
    body: Union[bytes, str],
    headers: Mapping[str, Any],
    secret: str,
    *,
    now_ms: Optional[int] = None,
    tolerance_ms: int = REPLAY_TOLERANCE_MS,
) -> WebhookVerification:
    """Verify and parse an Atlas webhook delivery."""
    raw = body.encode("utf-8") if isinstance(body, str) else bytes(body)
    delivery_id = _header(headers, HEADER_ID)
    ts_raw = _header(headers, HEADER_TIMESTAMP)
    signature = _header(headers, HEADER_SIGNATURE)
    if not delivery_id or not ts_raw or not signature:
        return WebhookVerification(False, "missing_headers")

    version, _, provided = signature.partition(",")
    if version != "v1" or not provided:
        return WebhookVerification(False, "malformed_signature")

    try:
        timestamp = int(ts_raw.strip())
    except ValueError:
        return WebhookVerification(False, "stale_timestamp")
    now = int(time.time() * 1000) if now_ms is None else now_ms
    if abs(now - timestamp) > tolerance_ms:
        return WebhookVerification(False, "stale_timestamp")

    signed = f"{delivery_id}.{timestamp}.".encode("utf-8") + raw
    expected = base64.b64encode(hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).digest())
    if not hmac.compare_digest(expected, provided.encode("utf-8")):
        return WebhookVerification(False, "signature_mismatch")

    try:
        event = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        event = None
    return WebhookVerification(
        True,
        event=event if isinstance(event, dict) else None,
        delivery_id=delivery_id,
        timestamp=timestamp,
    )
