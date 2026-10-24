"""Helpers for the integrator platform: key formats, W3C trace context, webhook event
names, the privacy-executor verifiers, the partner-link request protocol, OIDC org/SSO
claims, the browser Atlas ID integration-token route, the back-channel logout handler,
the operator device flow and sealed secrets.

Everything here is a plain function or small class over ``httpx`` / ``hmac`` — none of it
needs a secret key.
"""

from __future__ import annotations

import asyncio
import base64
import re
import secrets
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import quote, urlencode, urlparse, urlunparse, parse_qsl

import httpx

from ._transport import DEFAULT_BASE_URL, _to_error
from ._webhooks import REPLAY_TOLERANCE_MS, WebhookVerification, verify_webhook

__all__ = [
    "AsyncOperatorLogin",
    "BackchannelLogoutApp",
    "KeyFormat",
    "OAuthFlowError",
    "OIDC_ORGANIZATION_PARAM",
    "OIDC_SCOPE_ORGANIZATIONS",
    "OperatorLogin",
    "PRIVACY_USER_AGENT",
    "SCOPE_PRIVACY_EXECUTE",
    "SCOPE_PRIVACY_GRANTS_REVOKE",
    "SCOPE_WEBHOOKS_REVEAL",
    "SealedBox",
    "Traceparent",
    "WEBHOOK_EVENT_ALIASES",
    "atlas_id_integration_token",
    "aatlas_id_integration_token",
    "canonical_webhook_event",
    "get_partner_link_request",
    "handle_backchannel_logout",
    "is_privacy_event",
    "oidc_authorize_url_with_organization",
    "oidc_organization_of",
    "oidc_organizations_of",
    "oidc_sso_of",
    "parse_key",
    "request_partner_link",
    "traceparent_from_headers",
    "valid_privacy_idempotency_key",
    "verify_partner_link_delivery",
    "verify_privacy_case_request",
    "verify_privacy_completion",
    "webhook_event_matches",
    "webhook_event_spellings",
]

# --------------------------------------------------------------------------- #
# Scopes                                                                       #
# --------------------------------------------------------------------------- #

SCOPE_PRIVACY_EXECUTE = "privacy:execute"
SCOPE_PRIVACY_GRANTS_REVOKE = "privacy:grants:revoke"
SCOPE_WEBHOOKS_REVEAL = "webhooks:reveal"

#: The OIDC scope that adds the ``orgs`` membership list to the ID token and userinfo.
OIDC_SCOPE_ORGANIZATIONS = "organizations"
#: The authorize parameter that pins the organization a sign-in is made in (id or slug).
OIDC_ORGANIZATION_PARAM = "organization"

# --------------------------------------------------------------------------- #
# Key formats                                                                  #
# --------------------------------------------------------------------------- #

_ATLAS_KEY = re.compile(
    r"^atlas_(live|test|dev|sandbox|[a-z0-9]{2,12})_(sk|pk|psk|whsec)_[A-Za-z0-9_\-]+$"
)
_LEGACY_ENV = re.compile(r"^(sk|pk|psk)_(live|test)_[A-Za-z0-9_\-]+$")
_LEGACY_BARE = re.compile(r"^(sk|pk|psk)_[A-Za-z0-9][A-Za-z0-9_\-]*$")
_LEGACY_WHSEC = re.compile(r"^whsec_[A-Za-z0-9_\-+/=]+$")


@dataclass(frozen=True)
class ParsedKey:
    """An Atlas key, taken apart. ``kind`` is ``sk``, ``pk``, ``psk`` or ``whsec``; ``env``
    is ``live`` / ``test`` / ... when the key names one; ``format`` is ``atlas`` for
    ``atlas_<env>_<kind>_...`` and ``legacy`` for ``sk_live_...``."""

    kind: str
    env: Optional[str]
    format: str


def parse_key(key: str) -> Optional[ParsedKey]:
    """Recognise an Atlas key in either format. ``None`` when ``key`` is not one."""
    if not isinstance(key, str):
        return None
    m = _ATLAS_KEY.match(key)
    if m:
        return ParsedKey(m.group(2), m.group(1), "atlas")
    m = _LEGACY_ENV.match(key)
    if m:
        return ParsedKey(m.group(1), m.group(2), "legacy")
    m = _LEGACY_BARE.match(key)
    if m:
        return ParsedKey(m.group(1), None, "legacy")
    if _LEGACY_WHSEC.match(key):
        return ParsedKey("whsec", None, "legacy")
    return None


class KeyFormat:
    """Recognise Atlas keys in either format: the suite format ``atlas_<env>_<kind>_<random>``
    (env ``live`` / ``test``; kind ``sk``, ``pk``, ``psk``, ``whsec``) and the legacy
    ``sk_live_...`` / ``pk_test_...`` / ``psk_...`` / ``whsec_...``. Use these instead of
    ``key.startswith("sk_")``, which refuses the new format."""

    SECRET = "sk"
    PUBLISHABLE = "pk"
    PLATFORM = "psk"
    WEBHOOK_SECRET = "whsec"

    @staticmethod
    def parse(key: str) -> Optional[ParsedKey]:
        return parse_key(key)

    @staticmethod
    def kind(key: str) -> Optional[str]:
        parsed = parse_key(key)
        return parsed.kind if parsed else None

    @staticmethod
    def environment(key: str) -> Optional[str]:
        parsed = parse_key(key)
        return parsed.env if parsed else None

    @staticmethod
    def is_secret_key(key: str) -> bool:
        return KeyFormat.kind(key) == "sk"

    @staticmethod
    def is_publishable_key(key: str) -> bool:
        return KeyFormat.kind(key) == "pk"

    @staticmethod
    def is_platform_key(key: str) -> bool:
        return KeyFormat.kind(key) == "psk"

    @staticmethod
    def is_webhook_secret(key: str) -> bool:
        return KeyFormat.kind(key) == "whsec"


# --------------------------------------------------------------------------- #
# W3C Trace Context                                                            #
# --------------------------------------------------------------------------- #

_TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


@dataclass(frozen=True)
class ParsedTraceparent:
    traceparent: str
    trace_id: str
    span_id: str
    flags: str

    @property
    def sampled(self) -> bool:
        return bool(int(self.flags, 16) & 1)


class Traceparent:
    """W3C Trace Context (``traceparent``) helpers. Atlas accepts a ``traceparent`` on any
    call and carries its trace id onto the webhooks, back-channel logouts, integration
    events and privacy cases the call causes, so one operation can be followed across
    systems::

        atlas = AtlasClient("sk_live_...", traceparent=Traceparent.generate())
        incoming = Traceparent.parse(request.headers.get("traceparent", ""))
        child = Traceparent.child(incoming.traceparent if incoming else None)
    """

    HEADER = "traceparent"

    @staticmethod
    def generate() -> str:
        """A new sampled traceparent: ``00-<32 hex trace id>-<16 hex span id>-01``."""
        return f"00-{secrets.token_hex(16)}-{secrets.token_hex(8)}-01"

    @staticmethod
    def parse(value: str) -> Optional[ParsedTraceparent]:
        """Parse a version-00 traceparent; ``None`` when invalid (all-zero ids are invalid)."""
        if not isinstance(value, str):
            return None
        v = value.strip().lower()
        m = _TRACEPARENT.match(v)
        if not m or m.group(1) == "0" * 32 or m.group(2) == "0" * 16:
            return None
        return ParsedTraceparent(v, m.group(1), m.group(2), m.group(3))

    @staticmethod
    def is_valid(value: str) -> bool:
        return Traceparent.parse(value) is not None

    @staticmethod
    def child(parent: Optional[str]) -> str:
        """A traceparent in ``parent``'s trace with a fresh span id (a new trace when
        ``parent`` is ``None`` or invalid)."""
        parsed = Traceparent.parse(parent) if parent else None
        if parsed is None:
            return Traceparent.generate()
        return f"00-{parsed.trace_id}-{secrets.token_hex(8)}-{parsed.flags}"

    @staticmethod
    def trace_id(value: str) -> Optional[str]:
        """The trace id, to match against ``trace_id`` / ``trace`` on deliveries and
        privacy requests."""
        parsed = Traceparent.parse(value)
        return parsed.trace_id if parsed else None


def traceparent_from_headers(headers: Mapping[str, Any]) -> Optional[str]:
    """The valid ``traceparent`` in a header mapping (any casing, ``HTTP_TRACEPARENT``
    too), or ``None``."""
    for name, value in headers.items():
        if str(name).lower() in ("traceparent", "http_traceparent"):
            if isinstance(value, (list, tuple)):
                value = value[0] if value else ""
            parsed = Traceparent.parse(str(value))
            return parsed.traceparent if parsed else None
    return None


# --------------------------------------------------------------------------- #
# Webhook event names                                                          #
# --------------------------------------------------------------------------- #

#: Deprecated spelling -> canonical name. ``session.ended``, ``session.removed`` and
#: ``user.deletion_cancelled`` are companions (sent alongside the canonical event to a
#: ``legacy`` endpoint); the rest are plain renames.
WEBHOOK_EVENT_ALIASES: dict[str, str] = {
    "session.ended": "session.revoked",
    "session.removed": "session.revoked",
    "organizationMembership.created": "organization_membership.created",
    "organizationMembership.updated": "organization_membership.updated",
    "organizationMembership.deleted": "organization_membership.deleted",
    "organization.membership.deleted": "organization_membership.deleted",
    "organizationInvitation.created": "organization_invitation.created",
    "organizationInvitation.accepted": "organization_invitation.accepted",
    "organizationInvitation.revoked": "organization_invitation.revoked",
    "organizationInvitation.declined": "organization_invitation.declined",
    "organizationInvitation.resent": "organization_invitation.resent",
    "teamMembership.created": "team_membership.created",
    "teamMembership.deleted": "team_membership.deleted",
    "appRole.created": "app_role.created",
    "appRole.updated": "app_role.updated",
    "appRole.deleted": "app_role.deleted",
    "organizationDomain.created": "organization_domain.created",
    "organizationDomain.updated": "organization_domain.updated",
    "organizationDomain.deleted": "organization_domain.deleted",
    "organization.settings.updated": "organization_settings.updated",
    "waitlistEntry.created": "waitlist_entry.created",
    "waitlistEntry.updated": "waitlist_entry.updated",
    "billing.subscription.created": "billing_subscription.created",
    "billing.subscription.updated": "billing_subscription.updated",
    "billing.subscription.canceled": "billing_subscription.canceled",
    "billing.invoice.payment_failed": "billing_invoice.payment_failed",
    "billing.trial.started": "billing_trial.started",
    "billing.trial.will_end": "billing_trial.will_end",
    "billing.trial.ended": "billing_trial.ended",
    "entitlement.override.created": "entitlement_override.created",
    "entitlement.override.deleted": "entitlement_override.deleted",
    "entitlement.override.expired": "entitlement_override.expired",
    "scimToken.created": "scim_token.created",
    "scimToken.revoked": "scim_token.revoked",
    "ssoConnection.created": "sso_connection.created",
    "ssoConnection.updated": "sso_connection.updated",
    "ssoConnection.deleted": "sso_connection.deleted",
    "user.data_export.requested": "user.data_export_requested",
    "user.deletion_cancelled": "user.deletion_canceled",
}


def canonical_webhook_event(name: str) -> str:
    """The canonical name for any spelling (an unknown name is returned unchanged)."""
    return WEBHOOK_EVENT_ALIASES.get(name, name)


def webhook_event_spellings(name: str) -> list[str]:
    """Every name an event is known by: the canonical one, then its aliases."""
    canonical = canonical_webhook_event(name)
    return [canonical] + [a for a, c in WEBHOOK_EVENT_ALIASES.items() if c == canonical]


def webhook_event_matches(event_type: str, wanted: str) -> bool:
    """True when ``event_type`` (any spelling) is ``wanted`` (any spelling)."""
    return canonical_webhook_event(event_type) == canonical_webhook_event(wanted)


# --------------------------------------------------------------------------- #
# Privacy executor                                                             #
# --------------------------------------------------------------------------- #

#: The ``User-Agent`` Atlas sends privacy calls with.
PRIVACY_USER_AGENT = "Atlas-Privacy/1"

_PRIVACY_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9_\-:.]{16,255}$")


def valid_privacy_idempotency_key(key: str) -> bool:
    """Whether ``key`` is acceptable as an ``Idempotency-Key`` on privacy writes (16-255
    URL-safe characters)."""
    return isinstance(key, str) and bool(_PRIVACY_IDEMPOTENCY_KEY.match(key))


def verify_privacy_case_request(
    body: bytes | str,
    headers: Mapping[str, Any],
    secret: str,
    *,
    now_ms: Optional[int] = None,
    tolerance_ms: int = REPLAY_TOLERANCE_MS,
) -> WebhookVerification:
    """Verify the case Atlas opens at your orchestrator's ``case_url`` (and the cancel call
    at ``cancel_url``) when the orchestrator has a signing secret. Signed like a webhook
    (``atlas-id``, ``atlas-timestamp``, ``atlas-signature``). The ``Idempotency-Key`` is the
    same on every retry: open one case per key."""
    return verify_webhook(body, headers, secret, now_ms=now_ms, tolerance_ms=tolerance_ms)


def verify_privacy_completion(
    body: bytes | str,
    headers: Mapping[str, Any],
    secret: str,
    *,
    url: Optional[str] = None,
    now_ms: Optional[int] = None,
) -> WebhookVerification:
    """Verify a ``privacy_request.updated`` / ``privacy_request.completed`` event Atlas posts
    to the managed completion webhook (pass its ``url`` to also accept ``v2`` signatures).
    Any other event type is refused with reason ``unexpected_event``."""
    result = verify_webhook(body, headers, secret, now_ms=now_ms, url=url)
    if not result.verified:
        return result
    if not is_privacy_event(result.event or {}):
        return WebhookVerification(False, "unexpected_event")
    return result


def is_privacy_event(event: Mapping[str, Any]) -> bool:
    """True for a ``privacy_request.*`` event envelope."""
    t = event.get("type") if isinstance(event, Mapping) else None
    return isinstance(t, str) and t.startswith("privacy_request.")


# --------------------------------------------------------------------------- #
# Partner link requests (the partner product's side)                           #
# --------------------------------------------------------------------------- #


def request_partner_link(
    request: Mapping[str, Any],
    *,
    api_url: str = DEFAULT_BASE_URL,
    http_client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """For a PARTNER product: ask an Atlas instance for a link (no Atlas credential needed).
    The owner approves it in the dashboard (or through ``partner_links.requests.approve``);
    the credentials then arrive at ``callback_url``, signed with the returned
    ``request_secret`` (verify with :func:`verify_partner_link_delivery`).

    ``request`` takes ``partner``, ``resource`` (``ins_...`` or publishable key), ``scopes``,
    ``callback_url`` and optionally ``name``, ``state`` and ``cert_fingerprints``."""
    client = http_client or httpx.Client(timeout=30.0)
    try:
        response = client.post(
            f"{api_url.rstrip('/')}/v1/partner_link_requests",
            json=dict(request),
            headers={"accept": "application/json"},
        )
    finally:
        if http_client is None:
            client.close()
    if not response.is_success:
        raise _to_error(response.status_code, response.text)
    return response.json()


def get_partner_link_request(
    request_id: str,
    request_secret: str,
    *,
    api_url: str = DEFAULT_BASE_URL,
    http_client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """For a PARTNER product: read the status of a request it made, authenticating with the
    ``request_secret`` returned at creation."""
    client = http_client or httpx.Client(timeout=30.0)
    try:
        response = client.get(
            f"{api_url.rstrip('/')}/v1/partner_link_requests/{quote(request_id, safe='')}",
            headers={"authorization": f"Bearer {request_secret}", "accept": "application/json"},
        )
    finally:
        if http_client is None:
            client.close()
    if not response.is_success:
        raise _to_error(response.status_code, response.text)
    return response.json()


def verify_partner_link_delivery(
    body: bytes | str,
    headers: Mapping[str, Any],
    request_secret: str,
    *,
    url: Optional[str] = None,
    now_ms: Optional[int] = None,
) -> WebhookVerification:
    """For a PARTNER product: verify and parse the credentials (``partner_link.credentials``)
    or denial (``partner_link.denied``) Atlas delivered to your callback. ``request_secret``
    is the request's secret; pass ``url`` (your callback URL) to also check the URL-bound
    signature. The verified ``event`` is the delivery."""
    return verify_webhook(body, headers, request_secret, now_ms=now_ms, url=url)


# --------------------------------------------------------------------------- #
# OIDC relying parties: organization and enterprise SSO claims                 #
# --------------------------------------------------------------------------- #


def oidc_organization_of(claims: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """The organization a sign-in was made in, from verified ID-token or userinfo claims
    (``org_id``, ``org_slug``, ``org_role``, ``org_permissions``). ``None`` when no
    organization was involved. Returns ``{"id", "slug", "role", "permissions"}``."""
    org_id = claims.get("org_id")
    if not isinstance(org_id, str):
        return None
    perms = claims.get("org_permissions")
    return {
        "id": org_id,
        "slug": claims["org_slug"] if isinstance(claims.get("org_slug"), str) else "",
        "role": claims["org_role"] if isinstance(claims.get("org_role"), str) else "",
        "permissions": [p for p in perms if isinstance(p, str)] if isinstance(perms, list) else [],
    }


def oidc_organizations_of(claims: Mapping[str, Any]) -> Optional[list[dict[str, str]]]:
    """Every membership (the ``orgs`` claim of the ``organizations`` scope), or ``None``
    when the scope was not requested. Each entry is ``{"id", "slug", "role"}``."""
    orgs = claims.get("orgs")
    if not isinstance(orgs, list):
        return None
    return [
        {
            "id": o["id"],
            "slug": o["slug"] if isinstance(o.get("slug"), str) else "",
            "role": o["role"] if isinstance(o.get("role"), str) else "",
        }
        for o in orgs
        if isinstance(o, Mapping) and isinstance(o.get("id"), str)
    ]


def oidc_sso_of(claims: Mapping[str, Any]) -> Optional[dict[str, Optional[str]]]:
    """The enterprise SSO connection the user signed in through (``sso_connection_id``,
    ``sso_tenant_id``, ``sso_issuer``, ``sso_domain``), or ``None``. Returns
    ``{"connection_id", "tenant_id", "issuer", "domain"}``."""
    cid = claims.get("sso_connection_id")
    if not isinstance(cid, str):
        return None

    def s(key: str) -> Optional[str]:
        v = claims.get(key)
        return v if isinstance(v, str) else None

    return {
        "connection_id": cid,
        "tenant_id": s("sso_tenant_id"),
        "issuer": s("sso_issuer"),
        "domain": s("sso_domain"),
    }


def oidc_authorize_url_with_organization(authorize_url: str, organization: str) -> str:
    """Add the ``organization`` authorize parameter (org id or slug) to an authorize URL:
    the sign-in must be made in that organization (a user who is not a member gets
    ``access_denied``) and the ID token's ``org_*`` claims are that organization's."""
    parts = urlparse(authorize_url)
    query = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "organization"
    ]
    query.append((OIDC_ORGANIZATION_PARAM, organization))
    return urlunparse(parts._replace(query=urlencode(query)))


# --------------------------------------------------------------------------- #
# Browser Atlas ID integration token                                           #
# --------------------------------------------------------------------------- #


def _atlas_id_token_request(
    frontend_api: str,
    publishable_key: str,
    integration: str,
    access_token: str,
    dpop_proof: Optional[str],
    origin: Optional[str],
) -> tuple[str, dict[str, str]]:
    path = f"/v1/client/integrations/{quote(integration, safe='')}/atlas_id_tokens"
    # The publishable key rides in the query, so a CORS preflight (no custom headers) can
    # name the instance.
    url = f"{frontend_api.rstrip('/')}{path}?publishable_key={quote(publishable_key, safe='')}"
    headers = {
        "authorization": f"{'DPoP' if dpop_proof else 'Bearer'} {access_token}",
        "accept": "application/json",
    }
    if dpop_proof:
        headers["dpop"] = dpop_proof
    if origin:
        headers["origin"] = origin
    return url, headers


def _atlas_id_token_result(response: httpx.Response) -> Optional[dict[str, Any]]:
    if not response.is_success:
        return None
    data = response.json()
    if not isinstance(data, dict) or not data.get("jwt"):
        return None
    return data


def atlas_id_integration_token(
    frontend_api: str,
    publishable_key: str,
    integration: str,
    access_token: str,
    *,
    dpop_proof: Optional[str] = None,
    origin: Optional[str] = None,
    http_client: Optional[httpx.Client] = None,
) -> Optional[dict[str, Any]]:
    """``POST /v1/client/integrations/<integration>/atlas_id_tokens``: an integration token
    for a user who signed in with Sign in with Atlas (not a session of this instance), for
    an app with no server of its own. Normally called from browser code; this is the same
    call for a backend-for-frontend.

    The user's Sign in with Atlas access token is sent as ``Authorization: Bearer`` or, with
    ``dpop_proof`` (a DPoP proof for this exact request: ``htm`` POST, ``htu`` the URL
    without the query, ``ath`` the access token's hash), as ``DPoP`` (required when the token
    is DPoP-bound). Atlas checks the ``Origin`` against the Sign in with Atlas app's web
    origins, so pass ``origin`` when calling server-side. No cookies are sent.

    Returns ``{"jwt", "expires_in", "integration", "audience", "issuer", "jwks_uri"}``, or
    ``None`` when the integration is not enabled for Sign in with Atlas users, the token is
    not accepted or the origin is not the app's."""
    if not access_token:
        return None
    url, headers = _atlas_id_token_request(
        frontend_api, publishable_key, integration, access_token, dpop_proof, origin
    )
    client = http_client or httpx.Client(timeout=30.0)
    try:
        return _atlas_id_token_result(client.post(url, headers=headers))
    finally:
        if http_client is None:
            client.close()


async def aatlas_id_integration_token(
    frontend_api: str,
    publishable_key: str,
    integration: str,
    access_token: str,
    *,
    dpop_proof: Optional[str] = None,
    origin: Optional[str] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> Optional[dict[str, Any]]:
    """Async peer of :func:`atlas_id_integration_token`."""
    if not access_token:
        return None
    url, headers = _atlas_id_token_request(
        frontend_api, publishable_key, integration, access_token, dpop_proof, origin
    )
    client = http_client or httpx.AsyncClient(timeout=30.0)
    try:
        return _atlas_id_token_result(await client.post(url, headers=headers))
    finally:
        if http_client is None:
            await client.aclose()


# --------------------------------------------------------------------------- #
# Back-channel logout handler                                                  #
# --------------------------------------------------------------------------- #


def handle_backchannel_logout(
    verifier: Any,
    logout_token: str,
    on_logout: Callable[[Any], Any],
) -> tuple[int, dict[str, str]]:
    """Verify a posted ``logout_token`` and run ``on_logout(claims)``. Returns the status and
    headers to answer with: 200 after the callback ran, 400 for a token that must be refused,
    and 503 + ``Retry-After`` when Atlas should retry (keys unreachable, or your callback
    raised)."""
    from ._verify import VerificationError

    no_store = {"Cache-Control": "no-store"}
    try:
        claims = verifier.verify(logout_token)
    except VerificationError as err:
        if getattr(err, "retryable", False):
            return 503, {"Retry-After": "30", **no_store}
        return 400, dict(no_store)
    try:
        on_logout(claims)
    except Exception:
        return 503, {"Retry-After": "30", **no_store}
    return 200, dict(no_store)


class BackchannelLogoutApp:
    """A WSGI app for the ``backchannel_logout_uri`` route (mount it at that path)::

        from atlas_backend import BackchannelLogoutApp, LogoutTokenVerifier

        app.mount("/atlas/logout", BackchannelLogoutApp(
            LogoutTokenVerifier(issuer=..., client_id=...),
            lambda claims: sessions.end(claims.sid, claims.sub),
        ))

    Answers 405 to anything but POST, then as :func:`handle_backchannel_logout`.
    """

    def __init__(self, verifier: Any, on_logout: Callable[[Any], Any]) -> None:
        self._verifier = verifier
        self._on_logout = on_logout

    def __call__(
        self, environ: Mapping[str, Any], start_response: Callable[..., Any]
    ) -> list[bytes]:
        from ._logout import logout_token_from_form

        if environ.get("REQUEST_METHOD", "").upper() != "POST":
            start_response(
                "405 Method Not Allowed", [("Allow", "POST"), ("Cache-Control", "no-store")]
            )
            return [b""]
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(min(length, 64 * 1024)) if length else b""
        status, headers = handle_backchannel_logout(
            self._verifier, logout_token_from_form(body), self._on_logout
        )
        reason = {200: "OK", 400: "Bad Request", 503: "Service Unavailable"}[status]
        start_response(f"{status} {reason}", list(headers.items()))
        return [b""]


# --------------------------------------------------------------------------- #
# Operator device flow, token exchange, leaked-key revocation                  #
# --------------------------------------------------------------------------- #


class OAuthFlowError(Exception):
    """A refused device-flow or token request. ``code`` is the OAuth ``error`` (or Atlas
    error code), e.g. ``access_denied``, ``expired_token``, ``not_configured``."""

    def __init__(self, code: str, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


_DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"
_ACCESS_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"


def _exchange_form(subject_token: str, resource: str, scope: str | Sequence[str]) -> dict[str, str]:
    return {
        "grant_type": _EXCHANGE_GRANT,
        "subject_token": subject_token,
        "subject_token_type": _ACCESS_TOKEN_TYPE,
        "audience": "atlas",
        "resource": resource,
        "scope": scope if isinstance(scope, str) else " ".join(scope),
    }


def _flow_error(status: int, out: Mapping[str, Any], fallback: str) -> OAuthFlowError:
    first: Mapping[str, Any] = {}
    errors = out.get("errors")
    if isinstance(errors, list) and errors and isinstance(errors[0], Mapping):
        first = errors[0]
    return OAuthFlowError(
        str(out.get("error") or first.get("code") or "error"),
        str(out.get("error_description") or first.get("message") or fallback),
        status,
    )


def _json_or_empty(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


class OperatorLogin:
    """Sign-in and token helpers for a CLI or a CI job, with no secret key: the operator
    device flow (RFC 8628), token exchange for a short-lived resource-bound token
    (RFC 8693), ``client_credentials`` with a partner link, and leaked-key revocation::

        login = OperatorLogin()
        start = login.start()          # show start["verification_uri_complete"], start["user_code"]
        tokens = login.poll(start)     # blocks until approved (raises OAuthFlowError otherwise)
        scoped = login.exchange(tokens["access_token"], "ins_123", ["users:read"])
    """

    def __init__(
        self,
        api_url: str = DEFAULT_BASE_URL,
        *,
        http_client: Optional[httpx.Client] = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api = api_url.rstrip("/")
        self._http = http_client or httpx.Client(timeout=30.0)
        self._owns = http_client is None
        self._sleep = sleep

    def close(self) -> None:
        if self._owns:
            self._http.close()

    def configuration(self) -> dict[str, Any]:
        """``GET /v1/operator``: where the device flow and token exchange live."""
        r = self._http.get(f"{self._api}/v1/operator", headers={"accept": "application/json"})
        out = _json_or_empty(r)
        if r.status_code != 200 or not out:
            raise OAuthFlowError(
                "not_configured",
                "The operator issuer is not configured on this deployment.",
                r.status_code,
            )
        return out

    def _form(self, url: str, fields: Mapping[str, str]) -> tuple[int, dict[str, Any]]:
        r = self._http.post(url, data=dict(fields), headers={"accept": "application/json"})
        return r.status_code, _json_or_empty(r)

    def start(self, config: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        """Start the device flow. Returns the device authorization (``device_code``,
        ``user_code``, ``verification_uri``, ``verification_uri_complete``, ``expires_in``,
        ``interval``) plus ``config``."""
        cfg = dict(config or self.configuration())
        status, out = self._form(
            str(cfg["device_authorization_endpoint"]),
            {"client_id": str(cfg["client_id"]), "scope": str(cfg.get("scope") or "")},
        )
        if status != 200:
            raise _flow_error(status, out, "Device authorization failed.")
        return {**out, "config": cfg}

    def poll(self, start: Mapping[str, Any]) -> dict[str, Any]:
        """Poll until the person approves (returns the tokens), denies or the code expires
        (raises). Honours ``interval`` and ``slow_down``."""
        cfg = start["config"]
        interval = max(1, int(start.get("interval") or 5))
        deadline = time.monotonic() + int(start["expires_in"])
        while time.monotonic() < deadline:
            self._sleep(interval)
            status, out = self._form(
                str(cfg["token_endpoint"]),
                {
                    "grant_type": _DEVICE_GRANT,
                    "device_code": str(start["device_code"]),
                    "client_id": str(cfg["client_id"]),
                },
            )
            if status == 200:
                return out
            error = out.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            raise _flow_error(status, out, "Sign-in failed.")
        raise OAuthFlowError("expired_token", "The sign-in code expired. Run the login again.", 400)

    def exchange(
        self, subject_token: str, resource: str, scope: str | Sequence[str]
    ) -> dict[str, Any]:
        """RFC 8693: swap an operator token for a one-hour, resource-bound Atlas token."""
        status, out = self._form(
            f"{self._api}/v1/oauth/token", _exchange_form(subject_token, resource, scope)
        )
        if status != 200:
            raise _flow_error(status, out, "Token exchange failed.")
        return out

    def partner_link_token(
        self, client_id: str, client_secret: str, scope: Optional[str] = None
    ) -> dict[str, Any]:
        """``client_credentials`` with a partner link's credentials (a partner product
        calling an instance)."""
        fields = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if scope:
            fields["scope"] = scope
        status, out = self._form(f"{self._api}/v1/oauth/token", fields)
        if status != 200:
            raise _flow_error(status, out, "Token request failed.")
        return out

    def revoke_leaked_keys(
        self, secrets_: Sequence[str], url: Optional[str] = None
    ) -> dict[str, Any]:
        """``POST /v1/keys/revoke_leaked``: revoke leaked Atlas credentials (needs no key)."""
        body: dict[str, Any] = {"secrets": list(secrets_)}
        if url:
            body["url"] = url
        r = self._http.post(
            f"{self._api}/v1/keys/revoke_leaked", json=body, headers={"accept": "application/json"}
        )
        if not r.is_success:
            raise OAuthFlowError(
                "request_failed", f"revoke_leaked failed ({r.status_code}).", r.status_code
            )
        return _json_or_empty(r)

    def __enter__(self) -> "OperatorLogin":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncOperatorLogin:
    """Async peer of :class:`OperatorLogin` over an :class:`httpx.AsyncClient`."""

    def __init__(
        self,
        api_url: str = DEFAULT_BASE_URL,
        *,
        http_client: Optional[httpx.AsyncClient] = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
    ) -> None:
        self._api = api_url.rstrip("/")
        self._http = http_client or httpx.AsyncClient(timeout=30.0)
        self._owns = http_client is None
        self._sleep = sleep

    async def aclose(self) -> None:
        if self._owns:
            await self._http.aclose()

    async def configuration(self) -> dict[str, Any]:
        r = await self._http.get(f"{self._api}/v1/operator", headers={"accept": "application/json"})
        out = _json_or_empty(r)
        if r.status_code != 200 or not out:
            raise OAuthFlowError(
                "not_configured",
                "The operator issuer is not configured on this deployment.",
                r.status_code,
            )
        return out

    async def _form(self, url: str, fields: Mapping[str, str]) -> tuple[int, dict[str, Any]]:
        r = await self._http.post(url, data=dict(fields), headers={"accept": "application/json"})
        return r.status_code, _json_or_empty(r)

    async def start(self, config: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        cfg = dict(config or await self.configuration())
        status, out = await self._form(
            str(cfg["device_authorization_endpoint"]),
            {"client_id": str(cfg["client_id"]), "scope": str(cfg.get("scope") or "")},
        )
        if status != 200:
            raise _flow_error(status, out, "Device authorization failed.")
        return {**out, "config": cfg}

    async def poll(self, start: Mapping[str, Any]) -> dict[str, Any]:
        cfg = start["config"]
        interval = max(1, int(start.get("interval") or 5))
        deadline = time.monotonic() + int(start["expires_in"])
        while time.monotonic() < deadline:
            await self._sleep(interval)
            status, out = await self._form(
                str(cfg["token_endpoint"]),
                {
                    "grant_type": _DEVICE_GRANT,
                    "device_code": str(start["device_code"]),
                    "client_id": str(cfg["client_id"]),
                },
            )
            if status == 200:
                return out
            error = out.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            raise _flow_error(status, out, "Sign-in failed.")
        raise OAuthFlowError("expired_token", "The sign-in code expired. Run the login again.", 400)

    async def exchange(
        self, subject_token: str, resource: str, scope: str | Sequence[str]
    ) -> dict[str, Any]:
        status, out = await self._form(
            f"{self._api}/v1/oauth/token", _exchange_form(subject_token, resource, scope)
        )
        if status != 200:
            raise _flow_error(status, out, "Token exchange failed.")
        return out

    async def partner_link_token(
        self, client_id: str, client_secret: str, scope: Optional[str] = None
    ) -> dict[str, Any]:
        fields = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if scope:
            fields["scope"] = scope
        status, out = await self._form(f"{self._api}/v1/oauth/token", fields)
        if status != 200:
            raise _flow_error(status, out, "Token request failed.")
        return out

    async def revoke_leaked_keys(
        self, secrets_: Sequence[str], url: Optional[str] = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"secrets": list(secrets_)}
        if url:
            body["url"] = url
        r = await self._http.post(
            f"{self._api}/v1/keys/revoke_leaked", json=body, headers={"accept": "application/json"}
        )
        if not r.is_success:
            raise OAuthFlowError(
                "request_failed", f"revoke_leaked failed ({r.status_code}).", r.status_code
            )
        return _json_or_empty(r)

    async def __aenter__(self) -> "AsyncOperatorLogin":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()


# --------------------------------------------------------------------------- #
# Sealed secrets                                                               #
# --------------------------------------------------------------------------- #


class SealedBox:
    """Sealed delivery of secrets (libsodium ``crypto_box_seal``, through PyNaCl: install
    ``atlas-backend[sealed]``). Generate a key pair, send ``secret_recipient``
    (``x25519:<base64 public key>``) with a key-creating call, and Atlas answers with
    ``sealed_*`` fields only you can open: the secret never crosses the wire in the clear::

        pair = SealedBox.generate_key_pair()
        created = atlas.secret_keys.create({"name": "ci", "secret_recipient": pair.secret_recipient})
        secret = SealedBox.open(created["sealed_secret"], pair.public_key, pair.secret_key)
    """

    @dataclass(frozen=True)
    class KeyPair:
        public_key: bytes
        secret_key: bytes
        #: ``x25519:<base64 public key>``: send as ``secret_recipient``.
        secret_recipient: str

    @staticmethod
    def _nacl() -> Any:
        try:
            import nacl.public
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise ImportError(
                "Sealed secrets need PyNaCl: pip install 'atlas-backend[sealed]'."
            ) from exc
        return nacl.public

    @classmethod
    def generate_key_pair(cls) -> "SealedBox.KeyPair":
        public = cls._nacl()
        sk = public.PrivateKey.generate()
        pk = bytes(sk.public_key)
        return cls.KeyPair(pk, bytes(sk), "x25519:" + base64.b64encode(pk).decode("ascii"))

    @classmethod
    def open(cls, sealed_base64: str, public_key: bytes, secret_key: bytes) -> bytes:
        """Open a ``sealed_*`` field (base64). Raises ``ValueError`` when it was not sealed to
        this key pair."""
        public = cls._nacl()
        try:
            sealed = base64.b64decode(sealed_base64, validate=True)
            box = public.SealedBox(public.PrivateKey(secret_key))
            return bytes(box.decrypt(sealed))
        except Exception as exc:
            raise ValueError("Could not open the sealed value with this key pair.") from exc

    @classmethod
    def seal(cls, plain: bytes | str, recipient: str | bytes) -> str:
        """Seal ``plain`` to a recipient (``x25519:<base64>`` or a raw 32-byte public key);
        for tests and mirrors. Returns base64."""
        public = cls._nacl()
        if isinstance(recipient, str):
            if not recipient.startswith("x25519:"):
                raise ValueError("The recipient is not an x25519:<base64> public key.")
            raw = base64.b64decode(recipient[7:], validate=True)
        else:
            raw = recipient
        if len(raw) != 32:
            raise ValueError("The recipient is not a 32-byte x25519 public key.")
        data = plain.encode("utf-8") if isinstance(plain, str) else plain
        return base64.b64encode(
            bytes(public.SealedBox(public.PublicKey(raw)).encrypt(data))
        ).decode("ascii")
