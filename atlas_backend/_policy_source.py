"""Atlas policy source protocol v1 - helpers for the system that SERVES an Atlas
instance's policy documents (a CMS, a docs platform, your own service).

* Atlas to you: ``GET {endpoint_url}/policies`` (the full feed) and
  ``GET {endpoint_url}/policies?key=<key>`` (one policy, after your event). The request
  is signed with the source's signing secret: ``atlas-id``, ``atlas-timestamp`` (epoch
  ms) and ``atlas-signature: v1,<base64 HMAC-SHA256>`` over
  ``{atlas-id}.{atlas-timestamp}.GET\\n{path+query}``. Check it with
  :func:`verify_policy_feed_request`, then answer a ``PolicyFeed``.
* You to Atlas: ``POST {webhook_url}`` (from ``policy_source.get()``), a
  ``policy.published`` / ``policy.retired`` event signed with the same secret by
  :func:`sign_policy_source_event`. Atlas then re-fetches that policy; it never stores
  content from the event.

Matches ``verifyPolicyFeedRequest`` / ``signPolicySourceEvent`` in ``@atlasauth/backend``.

    result = verify_policy_feed_request(request.method, request.full_path_and_query,
                                        request.headers, secret)
    if not result.verified:
        return 401
    return jsonify(build_feed(result.key))   # one policy when result.key is set
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import secrets
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict
from urllib.parse import parse_qsl

from ._webhooks import REPLAY_TOLERANCE_MS, _header

__all__ = [
    "POLICY_SOURCE_PROTOCOL_VERSION",
    "POLICY_SOURCE_VERSION_HEADER",
    "PolicyFeed",
    "PolicyFeedPolicy",
    "PolicyFeedVerification",
    "PolicyFeedVersion",
    "PolicySourceEvent",
    "SignedPolicySourceEvent",
    "sign_policy_source_event",
    "verify_policy_feed_request",
]

POLICY_SOURCE_PROTOCOL_VERSION = "2026-10-24"
#: The header Atlas sends with the protocol version on every feed request.
POLICY_SOURCE_VERSION_HEADER = "atlas-policies-version"


class _PolicyFeedVersionRequired(TypedDict):
    version: str


class PolicyFeedVersion(_PolicyFeedVersionRequired, total=False):
    """One version in the feed. Send one of ``content_html`` / ``content_markdown``, or
    ``content_url`` for Atlas to snapshot (at most 512 KB)."""

    #: Epoch ms or ISO 8601.
    published_at: int | str
    #: When Atlas starts asking users for it (defaults to ``published_at``).
    effective_at: int | str
    content_html: str
    content_markdown: str
    content_url: str
    summary_of_changes: str
    locale: str


class _PolicyFeedPolicyRequired(TypedDict):
    #: Slug: lowercase letters, digits, ``_`` and ``-``.
    key: str
    title: str
    versions: list[PolicyFeedVersion]


class PolicyFeedPolicy(_PolicyFeedPolicyRequired, total=False):
    display: Literal["checkbox", "scroll", "link"]
    required: bool
    applies_to: Literal["sign_up", "sign_in_and_sign_up"]


class PolicyFeed(TypedDict):
    """The answer to ``GET {endpoint_url}/policies``."""

    object: Literal["policy_list"]
    policies: list[PolicyFeedPolicy]


class _PolicySourceEventRequired(TypedDict):
    #: ``policy.published`` or ``policy.retired``.
    type: Literal["policy.published", "policy.retired"]
    key: str


class PolicySourceEvent(_PolicySourceEventRequired, total=False):
    #: Required for ``policy.published``: the version label to re-fetch.
    version: str
    occurred_at: str | int


@dataclass(frozen=True)
class PolicyFeedVerification:
    """The outcome of :func:`verify_policy_feed_request`. Never raised: check ``verified``."""

    verified: bool
    #: ``missing_headers``, ``malformed_signature``, ``stale_timestamp``,
    #: ``signature_mismatch`` or ``wrong_method`` (failures only).
    reason: str | None = None
    #: The signed ``atlas-id`` (verified only).
    delivery_id: str | None = None
    #: The signed ``atlas-timestamp``, epoch ms (verified only).
    timestamp: int | None = None
    #: The ``key`` query parameter when Atlas asks for one policy, else ``None``.
    key: str | None = None
    #: The ``atlas-policies-version`` header, when sent (not signed).
    protocol_version: str | None = None


def _mac(secret: str, delivery_id: str, timestamp: str, payload: str) -> bytes:
    signed = f"{delivery_id}.{timestamp}.{payload}".encode()
    return hmac.new(secret.encode(), signed, hashlib.sha256).digest()


def verify_policy_feed_request(
    method: str | None,
    path_and_query: str,
    headers: Mapping[str, Any],
    secret: str,
    *,
    now_ms: int | None = None,
    tolerance_ms: int = REPLAY_TOLERANCE_MS,
) -> PolicyFeedVerification:
    """Verify Atlas's signed GET of your feed.

    Pass the request method, the path AND query exactly as received (for example
    ``/atlas/policies?key=tos``), the headers and the source's signing secret. The
    ``atlas-signature`` header may carry several ``v1,<base64>`` entries; one match is
    enough. A timestamp more than five minutes from now is refused.
    """
    if method and method.upper() != "GET":
        return PolicyFeedVerification(False, "wrong_method")
    delivery_id = _header(headers, "atlas-id")
    ts_raw = _header(headers, "atlas-timestamp")
    signature = _header(headers, "atlas-signature")
    if not delivery_id or not ts_raw or not signature:
        return PolicyFeedVerification(False, "missing_headers")
    provided: list[bytes] = []
    for entry in signature.split():
        if entry.startswith("v1,"):
            try:
                provided.append(base64.b64decode(entry[3:] + "=" * (-len(entry[3:]) % 4)))
            except (binascii.Error, ValueError):
                provided.append(b"")
    if not provided:
        return PolicyFeedVerification(False, "malformed_signature")
    try:
        timestamp = float(ts_raw)
    except ValueError:
        return PolicyFeedVerification(False, "stale_timestamp")
    now = int(time.time() * 1000) if now_ms is None else now_ms
    if not math.isfinite(timestamp) or abs(now - timestamp) > tolerance_ms:
        return PolicyFeedVerification(False, "stale_timestamp")
    expected = _mac(secret, delivery_id, ts_raw, f"GET\n{path_and_query}")
    matched = False
    for candidate in provided:  # no early exit
        if hmac.compare_digest(expected, candidate):
            matched = True
    if not matched:
        return PolicyFeedVerification(False, "signature_mismatch")
    key: str | None = None
    q = path_and_query.find("?")
    if q != -1:
        for name, value in parse_qsl(path_and_query[q + 1 :], keep_blank_values=True):
            if name == "key":
                key = value
                break
    return PolicyFeedVerification(
        True,
        delivery_id=delivery_id,
        timestamp=int(timestamp),
        key=key,
        protocol_version=_header(headers, POLICY_SOURCE_VERSION_HEADER),
    )


@dataclass(frozen=True)
class SignedPolicySourceEvent:
    """A signed event: send ``body`` byte-for-byte with ``headers`` (add
    ``content-type: application/json``)."""

    body: str
    headers: dict[str, str]


def sign_policy_source_event(
    event: PolicySourceEvent,
    secret: str,
    *,
    event_id: str | None = None,
    timestamp_ms: int | None = None,
) -> SignedPolicySourceEvent:
    """Sign a ``policy.published`` / ``policy.retired`` event for ``POST {webhook_url}``
    (``atlas-id``, ``atlas-timestamp`` in ms, ``atlas-signature: v1,<base64 HMAC-SHA256
    of "{id}.{ts}.{body}">``). ``occurred_at`` defaults to now (ISO 8601). Atlas also
    accepts Standard Webhooks signatures if you prefer a library for that."""
    ts = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    payload: dict[str, Any] = {
        "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    }
    payload.update(event)
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    eid = event_id or f"evt_{secrets.token_hex(16)}"
    mac = _mac(secret, eid, str(ts), body)
    return SignedPolicySourceEvent(
        body=body,
        headers={
            "atlas-id": eid,
            "atlas-timestamp": str(ts),
            "atlas-signature": "v1," + base64.b64encode(mac).decode(),
        },
    )
