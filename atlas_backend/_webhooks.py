"""Verify an inbound Atlas webhook, for the customer consuming events.

Atlas signs every delivery: ``atlas-signature: v1,<base64>`` is HMAC-SHA256 over
``<id>.<timestamp>.<raw body>`` keyed with the endpoint secret (``whsec_...``),
with ``atlas-id`` and ``atlas-timestamp`` (epoch ms) headers. A delivery more
than five minutes from now, in either direction, is refused so a captured
request cannot be replayed. The header may carry several space-separated
``v1,<base64>`` entries (one per secret while a secret rotates with an overlap);
the delivery verifies when any one matches. Matches ``verifyWebhook`` in
``@atlasauth/backend``.

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


def _signatures(header: str, wanted: str = "v1") -> list[str]:
    """The ``wanted`` (``v1`` or ``v2``) signatures in an ``atlas-signature`` header.

    The header carries one ``v1,<base64>`` entry, or several separated by spaces (while an
    endpoint secret rotates, Atlas signs with the old and the new secret; an endpoint with
    ``signature_versions`` including ``v2`` adds ``v2,<base64>`` entries that also cover the
    URL). Entries of another version are skipped.
    """
    out = []
    for entry in header.split():
        version, _, value = entry.partition(",")
        if version == wanted and value:
            out.append(value)
    return out


def verify_webhook(
    body: Union[bytes, str],
    headers: Mapping[str, Any],
    secret: str,
    *,
    now_ms: Optional[int] = None,
    tolerance_ms: int = REPLAY_TOLERANCE_MS,
    url: Optional[str] = None,
    require_v2: bool = False,
) -> WebhookVerification:
    """Verify and parse an Atlas webhook delivery.

    ``url`` is the URL Atlas posted to (your endpoint's registered URL). With it, ``v2``
    signatures (HMAC over ``<id>.<timestamp>.<url>.<body>``) are checked too, so a delivery
    replayed to another URL fails. ``require_v2=True`` accepts only ``v2`` (an endpoint with
    ``signature_versions: ["v2"]``); it needs ``url``. Unknown versions are ignored.
    """
    raw = body.encode("utf-8") if isinstance(body, str) else bytes(body)
    delivery_id = _header(headers, HEADER_ID)
    ts_raw = _header(headers, HEADER_TIMESTAMP)
    signature = _header(headers, HEADER_SIGNATURE)
    if not delivery_id or not ts_raw or not signature:
        return WebhookVerification(False, "missing_headers")

    provided = [] if require_v2 else _signatures(signature)
    provided_v2 = _signatures(signature, "v2") if url else []
    if not provided and not provided_v2:
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
    # Compare every entry (no early exit), each in constant time.
    matched = False
    for candidate in provided:
        if hmac.compare_digest(expected, candidate.encode("utf-8")):
            matched = True
    if provided_v2:
        signed_v2 = f"{delivery_id}.{timestamp}.{url}.".encode("utf-8") + raw
        expected_v2 = base64.b64encode(
            hmac.new(secret.encode("utf-8"), signed_v2, hashlib.sha256).digest()
        )
        for candidate in provided_v2:
            if hmac.compare_digest(expected_v2, candidate.encode("utf-8")):
                matched = True
    if not matched:
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
