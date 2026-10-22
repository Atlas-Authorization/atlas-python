"""The Atlas referral protocol, for a REFERRAL PLATFORM receiving calls from Atlas.

An Atlas instance with referral attribution on (provider ``webhook``) calls the
platform's base URL. Every call is a signed POST whose JSON body says which
operation it is (``op``) and which customer it is about::

    POST {base}/signups   {op: signup, customerRef, ...}               -> 200 ReferralSignupResponse
    POST {base}/erase     {op: erase, customerRef}                      -> 2xx (404 = already gone)
    POST {base}/export    {op: export, customerRef, test}               -> 200 any JSON | 404
    POST {base}/partners  {op: partner, customerRef, code, emailHash}   -> 2xx | 409 | 404/405/501
    POST {base}/signals   {op: signal, customerRef, type, ...}         -> 2xx | 404/405/501
    POST {base}/aliases   {op: alias, customerRef, fromCustomerRef, toCustomerRef}
                                                                    -> 2xx | 409 (permanent)
    POST {base}/users     {op: user, customerRef, email?, name?, status?} -> 2xx
    POST {base}/ping      {op: ping, customerRef: atlas_connection_test} -> 200 ReferralPingResponse

The connection test is ``POST {base}/export`` with ``{op: export, customerRef:
atlas_connection_test, test: true}`` (answer 2xx or 404). Calls are signed exactly
like Atlas webhooks (``atlas-id``, ``atlas-timestamp``, ``atlas-signature`` over
``<id>.<timestamp>.<raw body>``), with ``Idempotency-Key``,
``User-Agent: Atlas-Referrals/1`` and ``Atlas-Referrals-Version: 2026-10-21``.
``atlas-id`` is the call id, the same on every retry of one call.

The signature covers the body, not the URL. Pass the path the call arrived on (or
the operation you expect): a signed body whose ``op`` does not match it is refused,
so a captured call cannot be replayed against another endpoint. Matches
``verifyReferralRequest`` in ``@atlasauth/backend``.

    from atlas_backend import verify_referral_request

    result = verify_referral_request(request.body, request.headers, secret, path=request.path)
    if not result.verified:
        return 401
    if result.op == "signup":
        return attribute(result.payload)       # a ReferralSignupResponse
    if result.op == "export" and result.test:
        return 404
    if result.op == "ping":
        return {"ok": True, "serverTime": now_iso()}   # a ReferralPingResponse
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict
from urllib.parse import urlsplit

from ._webhooks import REPLAY_TOLERANCE_MS, _header, verify_webhook

#: ``customerRef`` of the connection test (``POST {base}/export`` with ``test: true``).
REFERRAL_CONNECTION_TEST_REF = "atlas_connection_test"
#: The ``User-Agent`` Atlas sends on every referral call.
REFERRAL_PROTOCOL_USER_AGENT = "Atlas-Referrals/1"
#: The ``Atlas-Referrals-Version`` Atlas sends on every call; shapes only grow, additively,
#: under it.
REFERRAL_PROTOCOL_VERSION = "2026-10-21"
#: The name of the version header (lower-case).
REFERRAL_PROTOCOL_VERSION_HEADER = "atlas-referrals-version"

#: The lifecycle signal types.
REFERRAL_SIGNAL_TYPES = (
    "email_verified",
    "user_banned",
    "user_unbanned",
    "user_locked",
    "risk_elevated",
    "fraud_confirmed",
)

ReferralOp = Literal["signup", "erase", "export", "partner", "signal", "alias", "user", "ping"]

#: The endpoint (last path segment) each operation is sent to.
REFERRAL_OP_ENDPOINTS: dict[str, str] = {
    "signup": "signups",
    "erase": "erase",
    "export": "export",
    "partner": "partners",
    "signal": "signals",
    "alias": "aliases",
    "user": "users",
    "ping": "ping",
}


class ReferralContext(TypedDict):
    """The referral captured at sign-up. Never trusted."""

    code: str | None
    clickId: str | None
    anonId: str | None
    #: ISO 8601.
    capturedAt: str
    consent: Literal["granted", "not_required"]


class ReferralRiskVerdict(TypedDict):
    level: Literal["low", "medium", "high"]
    score: int
    signals: list[str]
    captcha: Literal["passed", "not_required", "not_configured"]
    emailVerified: bool


class _ReferralSignupPayloadRequired(TypedDict):
    op: Literal["signup"]
    customerRef: str
    #: sha256 hex of the lower-cased, trimmed primary email; ``None`` without one.
    emailHash: str | None
    ip: str | None
    ua: str | None
    #: ISO 8601: the original sign-up time, the same on every retry.
    signedUpAt: str
    programId: str | None
    autoEnroll: bool
    referral: ReferralContext | None


class ReferralSignupPayload(_ReferralSignupPayloadRequired, total=False):
    """``POST {base}/signups``. Idempotent on ``customerRef``."""

    risk: ReferralRiskVerdict | None
    #: Set when Atlas stripped the referral because of its risk policy.
    rejected: dict[str, str] | None


class ReferralSignupMatch(TypedDict):
    partnerId: str | None
    referrerExternalRef: str | None
    matchedVia: str | None
    status: str | None


class ReferralPartner(TypedDict, total=False):
    id: str | None
    code: str | None
    link: str | None


class _ReferralSignupResponseRequired(TypedDict):
    referral: ReferralSignupMatch | None


class ReferralSignupResponse(_ReferralSignupResponseRequired, total=False):
    """The answer to ``POST {base}/signups``."""

    #: The user's own partner record when ``autoEnroll`` was true.
    partner: ReferralPartner | None
    #: Why you matched or did not (shown in the Atlas delivery log and on the user).
    notes: list[str]


class ReferralErasePayload(TypedDict):
    op: Literal["erase"]
    customerRef: str


class ReferralExportPayload(TypedDict):
    """``POST {base}/export``: what you hold about a customer (answer any JSON, or 404)."""

    op: Literal["export"]
    customerRef: str
    #: True for the connection test (``customerRef`` ``atlas_connection_test``).
    test: bool


class ReferralPartnerPayload(TypedDict):
    """``POST {base}/partners``: the user's own referral code was set in Atlas."""

    op: Literal["partner"]
    customerRef: str
    code: str
    emailHash: str | None


class ReferralSignalPayload(TypedDict):
    op: Literal["signal"]
    customerRef: str
    #: One of :data:`REFERRAL_SIGNAL_TYPES` (new types may appear).
    type: str
    #: ISO 8601.
    occurredAt: str
    data: dict[str, Any]


class ReferralAliasPayload(TypedDict):
    """``POST {base}/aliases``: the user's ``external_id`` was set or changed after the
    sign-up call. Re-key the customer from ``fromCustomerRef`` (the old value, or the
    Atlas user id) to ``toCustomerRef``. ``customerRef`` equals ``toCustomerRef``. A 409
    is treated as permanent.
    """

    op: Literal["alias"]
    customerRef: str
    fromCustomerRef: str
    toCustomerRef: str


class _ReferralUserPayloadRequired(TypedDict):
    op: Literal["user"]
    customerRef: str


class ReferralUserPayload(_ReferralUserPayloadRequired, total=False):
    """``POST {base}/users``: a lifecycle change. ``email`` / ``name`` when they changed;
    ``status`` ``suspended`` on a ban, ``active`` on an unban, ``deleted`` on deletion
    (deletion is also sent to ``/erase``).
    """

    email: str | None
    name: str | None
    status: Literal["active", "suspended", "deleted"]


class ReferralPingPayload(TypedDict):
    """``POST {base}/ping``: the connection test where the platform supports it."""

    op: Literal["ping"]
    customerRef: str


class _ReferralPingResponseRequired(TypedDict):
    ok: bool


class ReferralPingResponse(_ReferralPingResponseRequired, total=False):
    """The answer to a ping. Every field but ``ok`` is optional and shown on the Atlas
    dashboard.
    """

    programName: str
    orgName: str
    autoEnrollUsers: bool
    #: ISO 8601. Atlas warns when it is more than 60 seconds off.
    serverTime: str


@dataclass(frozen=True)
class ReferralVerification:
    """The outcome of :func:`verify_referral_request`. Never raised: check ``verified``."""

    verified: bool
    #: A webhook signature failure (``missing_headers``, ``malformed_signature``,
    #: ``stale_timestamp``, ``signature_mismatch``), or ``malformed_body`` (not a JSON
    #: object), ``missing_op``, ``unknown_op``, ``unknown_endpoint`` (the path's last
    #: segment is not a protocol endpoint) or ``op_mismatch`` (the signed ``op`` is not
    #: the endpoint's or the expected one).
    reason: str | None = None
    #: ``signup``, ``erase``, ``export``, ``partner``, ``signal``, ``alias``, ``user`` or
    #: ``ping`` (verified only).
    op: ReferralOp | None = None
    #: The signed JSON body, including ``op`` and ``customerRef`` (verified only).
    payload: dict[str, Any] | None = None
    #: The signed ``customerRef``.
    customer_ref: str | None = None
    #: The connection test (an ``export`` with ``test: true``): answer 2xx or 404.
    test: bool = False
    #: The signed ``atlas-id`` (the call id), the same on every retry.
    delivery_id: str | None = None
    timestamp: int | None = None
    #: The ``Idempotency-Key`` header (not signed).
    idempotency_key: str | None = None
    #: The ``Atlas-Referrals-Version`` header, when sent (not signed).
    protocol_version: str | None = None


def referral_op_for_path(path: str) -> ReferralOp | None:
    """The operation of a path's (or URL's) last segment, or ``None``."""
    segments = [s for s in urlsplit(path).path.split("/") if s]
    last = segments[-1] if segments else ""
    for op, endpoint in REFERRAL_OP_ENDPOINTS.items():
        if endpoint == last:
            return op  # type: ignore[return-value]
    return None


def verify_referral_request(
    body: bytes | str,
    headers: Mapping[str, Any],
    secret: str,
    *,
    path: str | None = None,
    expected_op: ReferralOp | None = None,
    now_ms: int | None = None,
    tolerance_ms: int = REPLAY_TOLERANCE_MS,
) -> ReferralVerification:
    """Verify a call from Atlas to a referral platform and tell which operation it is.

    Pass the RAW body, the headers, the signing secret configured on the Atlas
    instance, and the ``path`` the call arrived on (or ``expected_op``): the signed
    ``op`` must match it.
    """
    result = verify_webhook(body, headers, secret, now_ms=now_ms, tolerance_ms=tolerance_ms)
    if not result.verified:
        return ReferralVerification(False, result.reason)
    payload = result.event
    if not isinstance(payload, dict):
        return ReferralVerification(False, "malformed_body")
    op = payload.get("op")
    if op is None or op == "":
        return ReferralVerification(False, "missing_op")
    if not isinstance(op, str) or op not in REFERRAL_OP_ENDPOINTS:
        return ReferralVerification(False, "unknown_op")
    if path is not None:
        endpoint_op = referral_op_for_path(path)
        if endpoint_op is None:
            return ReferralVerification(False, "unknown_endpoint")
        if endpoint_op != op:
            return ReferralVerification(False, "op_mismatch")
    if expected_op is not None and expected_op != op:
        return ReferralVerification(False, "op_mismatch")
    customer_ref = payload.get("customerRef")
    return ReferralVerification(
        True,
        op=op,  # type: ignore[arg-type]
        payload=payload,
        customer_ref=customer_ref if isinstance(customer_ref, str) else None,
        test=op == "export" and payload.get("test") is True,
        delivery_id=result.delivery_id,
        timestamp=result.timestamp,
        idempotency_key=_header(headers, "idempotency-key"),
        protocol_version=_header(headers, REFERRAL_PROTOCOL_VERSION_HEADER),
    )
