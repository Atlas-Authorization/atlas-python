"""Typed wire shapes for every namespace: returned objects and request bodies.

These mirror the Backend API JSON one-to-one (snake_case, no translation) and
are shared by both the sync and async clients. Bodies with required fields use
the ``Base(TypedDict)`` + ``Body(Base, total=False)`` split so the required keys
stay required and the rest optional — a pattern that works on Python 3.9, which
lacks ``Required``/``NotRequired``.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, Union

from ._types import Metadata


class SecretsSealed(TypedDict):
    """Says a response was sealed to your ``X-Secret-Recipient`` key: each listed field
    arrives as ``sealed_<field>`` (open it with ``SealedBox.open``) instead of in plaintext."""

    algorithm: str
    recipient: str
    fields: list[str]


class SealedSecrets(TypedDict, total=False):
    """The ``sealed_*`` fields any shown-once secret response can carry when the request
    named a recipient (``X-Secret-Recipient``, or ``secret_recipient`` on the client). The
    plaintext field is then absent."""

    sealed_secret: str
    sealed_client_secret: str
    sealed_webhook_secret: str
    secrets_sealed: SecretsSealed


class AtlasIdOriginSeen(TypedDict):
    """A page origin the Sign in with Atlas button script ran on (last 7 days)."""

    origin: str
    last_seen_at: int
    requests: int


class DryRunChange(TypedDict):
    section: str
    before: Any
    after: Any


class DryRunWarning(TypedDict, total=False):
    code: str
    message: str


class DryRunValidationSkipped(TypedDict):
    reason: Literal["external_call", "database", "unsupported_response"]
    detail: str


class _DryRunResultRequired(TypedDict):
    object: Literal["dry_run"]
    dry_run: Literal[True]
    #: ``native``: the endpoint's own dry run, validated in full. ``rollback``: the real
    #: write ran in a transaction that was rolled back, every side effect held back,
    #: validated in full. ``plan``: validation could not run to the end (see
    #: ``validation_skipped``).
    mode: Literal["native", "rollback", "plan"]
    validated: bool
    method: str
    path: str
    changes: list[DryRunChange]
    note: str


class DryRunResult(_DryRunResultRequired, total=False):
    """What a write answers with ``dry_run=True``."""

    #: The same non-fatal warnings the real write returns (e.g. ``origin_still_referenced``).
    warnings: list[DryRunWarning]
    #: What the real write would return (secrets redacted).
    would_return: Any
    #: The status the real write would answer with (``rollback`` mode).
    would_return_status: int
    #: Side effects held back: ``email``, ``sms``, ``voice``, ``push``, ``outbound_network``,
    #: ``redis``, ``cache``, ``file``.
    suppressed: list[str]
    #: ``plan`` mode: why validation did not run to the end.
    validation_skipped: DryRunValidationSkipped


# --------------------------------------------------------------------------- #
# Users                                                                        #
# --------------------------------------------------------------------------- #


class _UserRequired(TypedDict):
    object: Literal["user"]
    id: str
    username: str | None
    first_name: str | None
    last_name: str | None
    image_url: str | None
    public_metadata: Metadata
    mfa_enabled: bool
    banned: bool
    locked: bool
    last_sign_in_at: int | None
    created_at: int
    updated_at: int


class UserReferral(TypedDict, total=False):
    """Where a user's inbound referral stands and, once attributed, who referred them.
    Present for every user reported to the referral platform.
    """

    #: The platform's id for the referring partner.
    partner_id: str | None
    #: The referrer as the platform knows them (your ``external_id`` for that user, or
    #: their Atlas id).
    referrer_external_id: str | None
    #: The referrer's Atlas user id, when they are a user of this instance.
    referrer_user_id: str | None
    #: How the platform matched the referral, e.g. ``code``, ``click``, ``coupon``.
    matched_via: str | None
    #: Where attribution stands: ``pending`` (the platform has not answered yet),
    #: ``attributed``, ``none``, ``failed``, ``held`` or ``flagged``. Servers before
    #: referral attribution v2 sent the platform's own status here; that is now
    #: ``referral_status``.
    status: str | None
    #: The referrer as the platform knows them. Same value as ``referrer_external_id``.
    partner_external_ref: str | None
    #: The platform's own status for the referral, e.g. ``active``.
    referral_status: str | None
    #: The platform's reasoning notes (why it matched, or why not).
    notes: list[str]
    #: The risk level Atlas assessed at sign-up, when one was.
    risk_level: Literal["low", "medium", "high"] | None
    #: An admin marked the referral fraudulent (``users.flag_referral``).
    flagged: bool


class User(_UserRequired, total=False):
    #: Strictly increases with every change to the user; webhook payloads carry the same
    #: value. Apply an update only if its version is higher than the one you hold.
    version: int
    #: Where the user's referral stands (referral attribution on), or ``None`` when the
    #: user was never reported to the referral platform.
    referral: UserReferral | None
    #: The user's own referral code, when they are a referrer.
    referral_code: str | None
    #: The user's own referral link, when they are a referrer.
    referral_link: str | None
    #: When a timed ban lifts (epoch ms); ``None`` for a permanent ban or no ban.
    ban_expires_at: int | None
    ban_reason: str | None
    ban_note: str | None


class UserReferralFlag(TypedDict):
    """A user's referral after ``users.flag_referral``."""

    object: Literal["user_referral"]
    user_id: str
    #: ``flagged`` after the call.
    status: str
    flagged: bool
    flag_reason: str | None
    #: Epoch ms.
    flagged_at: int | None
    risk_level: Literal["low", "medium", "high"] | None


class UserReferralAttributedEvent(TypedDict):
    """The ``data`` of a ``user.referral_attributed`` webhook: the referral platform
    answered after ``user.created`` was sent.
    """

    object: Literal["user_referral"]
    user_id: str
    #: ``attributed``, ``not_referred`` (the platform found no referrer), ``failed``, ...
    attribution_status: str
    referral: UserReferral | None
    referral_code: str | None
    referral_link: str | None
    #: Epoch ms.
    signed_up_at: int
    updated_at: int


#: The ``data`` of a ``user.referral_resolved`` webhook: the full user, sent when a
#: referral that was still ``pending`` at ``user.created`` reaches its final state.
#: ``referral.status`` is then ``attributed``, ``none`` or ``failed``.
UserReferralResolvedEvent = User


class _UserReferralResultRequired(TypedDict):
    object: Literal["user_referral"]
    user_id: str
    #: ``pending``, ``attributed``, ``none``, ``failed``, ``held`` or ``flagged``.
    status: Literal["pending", "attributed", "none", "failed", "held", "flagged"]
    #: The id the referral platform knows the user by: their ``external_id``, else the
    #: Atlas user id.
    customer_ref: str
    #: The platform's reasoning notes.
    notes: list[str]
    #: Epoch ms.
    signed_up_at: int
    updated_at: int


class UserReferralResult(_UserReferralResultRequired, total=False):
    """``GET /v1/users/{id}/referral``: the stored result of the user's referral calls,
    with no call to the platform. 404 when the user was never reported.
    """

    partner_id: str | None
    #: The referrer as the platform knows them.
    partner_external_ref: str | None
    referrer_user_id: str | None
    matched_via: str | None
    #: The platform's own status for the referral.
    referral_status: str | None
    referral_code: str | None
    referral_link: str | None
    #: The referral captured at sign-up, as sent (camelCase).
    context: dict[str, Any] | None
    risk_level: Literal["low", "medium", "high"] | None
    flagged: bool
    #: Why the sign-up report is held, while ``held``.
    hold_reason: str | None


class _EmailAddressVerificationRequired(TypedDict):
    status: Literal["verified", "unverified"]


class EmailAddressVerification(_EmailAddressVerificationRequired, total=False):
    """How (and whether) an address was proven."""

    #: ``email_code``, ``email_link``, ``oauth``, ``admin``, ``import``, ``scim``, ``lti``;
    #: ``skipped`` for an address held for sign-in but never proven; ``None`` when not verified.
    strategy: str | None


class _EmailAddressRequired(TypedDict):
    object: Literal["email_address"]
    id: str
    email_address: str
    #: True only when the address was proven. An address that signed up while
    #: ``requireEmailVerification`` was false reads ``False``.
    verified: bool
    primary: bool
    created_at: int


class EmailAddress(_EmailAddressRequired, total=False):
    #: ``status`` mirrors ``verified``; ``strategy`` says how it was verified.
    verification: EmailAddressVerification


class OAuthAccessToken(TypedDict):
    object: Literal["oauth_access_token"]
    provider: str
    token: str
    expires_at: int | None
    scopes: list[str]
    refreshed: bool


class _CreateUserRequired(TypedDict):
    email_address: str


class ImportedIdentity(TypedDict, total=False):
    """A social identity to attach to a user created (or imported) server-side."""

    provider: str
    provider_user_id: str
    email_address: str
    verified: bool


class ImportedTotp(TypedDict, total=False):
    secret_base32: str
    algorithm: str
    digits: float
    period: float
    verified_at: Any


class ImportedMfa(TypedDict, total=False):
    """MFA material carried over from another system on create."""

    totp: ImportedTotp
    backup_codes: list[str]


class CreateUserReferral(TypedDict, total=False):
    """An imported referral on ``users.create``. Each id is 3-64 characters of
    ``A-Z a-z 0-9 _ -``.
    """

    code: str
    click_id: str
    anon_id: str


class CreateUserBody(_CreateUserRequired, total=False):
    password: str
    #: A password hash migrated from another system (bcrypt, argon2, ...).
    password_hash: str | None
    password_digest: str | None
    first_name: str
    last_name: str
    email_verified: bool
    #: Your own id for this user; ``None`` or ``""`` clears it.
    external_id: str | None
    identities: list[ImportedIdentity]
    mfa: ImportedMfa
    public_metadata: Metadata
    private_metadata: Metadata
    unsafe_metadata: Metadata
    #: Whether the create may notify the user. ``False`` (the default) guarantees no
    #: email, SMS or push is sent as a consequence of the create.
    notify: bool
    #: Import a referral (how the user arrived). With referral attribution on, the user
    #: is reported to the referral platform.
    referral: CreateUserReferral
    #: The user's own referral code; unique per instance (409 ``REFERRAL_CODE_TAKEN``).
    referral_code: str


class UpdateUserBody(TypedDict, total=False):
    #: The user's own referral code; ``None`` clears it. Unique per instance
    #: (409 ``REFERRAL_CODE_TAKEN``).
    referral_code: str | None
    first_name: str
    last_name: str
    #: Your own id for this user; ``None`` or ``""`` clears it.
    external_id: str | None
    #: Admin password reset. Prefer ``users.set_password``.
    password: str
    skip_password_checks: bool
    public_metadata: Metadata
    private_metadata: Metadata
    unsafe_metadata: Metadata


class ReplaceUserMetadataBody(TypedDict, total=False):
    public_metadata: Metadata
    private_metadata: Metadata
    unsafe_metadata: Metadata


# --------------------------------------------------------------------------- #
# Organizations                                                                #
# --------------------------------------------------------------------------- #


class Organization(TypedDict):
    object: Literal["organization"]
    id: str
    name: str
    slug: str
    image_url: str | None
    public_metadata: Metadata
    max_allowed_memberships: int
    created_by: str
    created_at: int
    updated_at: int


class OrganizationMembership(TypedDict):
    object: Literal["organization_membership"]
    id: str
    organization_id: str
    user_id: str
    role: str
    created_at: int


class OrgDomain(TypedDict):
    object: Literal["org_domain"]
    id: str
    organization_id: str
    domain: str
    status: str
    auto_join: bool
    default_role_id: str | None
    verification: dict[str, Any]
    verified_at: int | None
    last_checked_at: int | None
    created_at: int


class _CreateOrganizationRequired(TypedDict):
    name: str
    slug: str
    created_by: str


class CreateOrganizationBody(_CreateOrganizationRequired, total=False):
    max_allowed_memberships: int


class UpdateOrganizationBody(TypedDict, total=False):
    name: str
    slug: str
    image_url: str
    max_allowed_memberships: int
    public_metadata: Metadata
    private_metadata: Metadata


class ReplaceOrganizationMetadataBody(TypedDict, total=False):
    public_metadata: Metadata
    private_metadata: Metadata


class OrgEndUserPoolPolicy(TypedDict, total=False):
    """Whether this organization keeps its own end-user pool, and how people join it."""

    enabled: bool
    requireApproval: bool
    allowHostedSignup: bool


class OrganizationPolicyPatch(TypedDict, total=False):
    """Org policy PATCH body. Keys are camelCase; an explicit ``None`` clears an override.

    Every field the server knows is typed here. To send a field this SDK release
    does not know yet, pass a plain ``dict`` instead — the method accepts both.
    """

    requireMfa: bool | None
    ssoRequired: bool | None
    sessionIdleOverrideMs: int | None
    #: Restrict which sign-in methods a member may use (e.g. ``"password"``,
    #: ``"oauth:google"``, ``"saml"``, ``"magic_link"``). ``None`` clears it.
    allowedSignInMethods: list[str] | None
    #: CIDR allow-list gating member sign-in. ``None`` clears it.
    ipAllowlist: list[str] | None
    #: Cap the absolute session lifetime for members, in seconds (300 to 7776000).
    maxSessionAgeSeconds: int | None
    endUserPool: OrgEndUserPoolPolicy | None
    #: Retired; only ``None`` (clear a stored value) is accepted.
    entitlementPlan: None
    #: Retired; only ``None`` (clear a stored value) is accepted.
    entitlementOverrides: None


class _AddMembershipRequired(TypedDict):
    user_id: str


class AddMembershipBody(_AddMembershipRequired, total=False):
    role: str


class _CreateOrgInvitationRequired(TypedDict):
    email: str
    role: str
    inviter_user_id: str


class CreateOrgInvitationBody(_CreateOrgInvitationRequired, total=False):
    pass


class _CreateOrgDomainRequired(TypedDict):
    domain: str


class CreateOrgDomainBody(_CreateOrgDomainRequired, total=False):
    auto_join: bool
    default_role_id: str | None


# --------------------------------------------------------------------------- #
# Sessions                                                                     #
# --------------------------------------------------------------------------- #


class _SessionRequired(TypedDict):
    object: Literal["session"]
    id: str
    user_id: str
    status: str
    last_active_organization_id: str | None
    impersonated_by: str | None
    last_active_at: int
    expire_at: int
    abandon_at: int
    created_at: int


class Session(_SessionRequired, total=False):
    #: Epoch ms the session ends from inactivity unless there is activity first
    #: (same value as ``abandon_at``).
    idle_expires_at: int
    #: Custom per-session data your backend (or a post_login Action) attached.
    custom_data: dict[str, Any] | None


class TouchedSession(_SessionRequired):
    """The session after a keep-alive ``sessions.touch``."""

    idle_expires_at: int
    #: ``True`` when this touch moved the inactivity window; ``False`` when a touch
    #: within the last 60 seconds already had.
    extended: bool


# --------------------------------------------------------------------------- #
# Invitations                                                                  #
# --------------------------------------------------------------------------- #


class Invitation(TypedDict):
    object: Literal["invitation"]
    id: str
    email_address: str
    status: str
    public_metadata: Metadata
    expires_at: int
    accepted_at: int | None
    created_at: int


class _CreateInvitationRequired(TypedDict):
    email_address: str


class CreateInvitationBody(_CreateInvitationRequired, total=False):
    public_metadata: Metadata


# --------------------------------------------------------------------------- #
# Roles & permissions                                                          #
# --------------------------------------------------------------------------- #


class Role(TypedDict):
    object: Literal["role"]
    id: str
    key: str
    name: str
    description: str | None
    is_system: bool
    permissions: list[str]
    member_count: int
    created_at: int


class Permission(TypedDict):
    object: Literal["permission"]
    id: str
    key: str
    name: str
    description: str | None
    is_system: bool


class _CreateRoleRequired(TypedDict):
    key: str
    name: str


class CreateRoleBody(_CreateRoleRequired, total=False):
    description: str
    permissions: list[str]


class UpdateRoleBody(TypedDict, total=False):
    name: str
    description: str
    key: str


class _CreatePermissionRequired(TypedDict):
    key: str


class CreatePermissionBody(_CreatePermissionRequired, total=False):
    name: str
    description: str


# --------------------------------------------------------------------------- #
# Webhooks                                                                     #
# --------------------------------------------------------------------------- #


class _WebhookEndpointRequired(TypedDict):
    object: Literal["webhook_endpoint"]
    id: str
    url: str
    enabled_events: list[str]
    active: bool
    disabled_at: int | None
    created_at: int


class WebhookEndpoint(_WebhookEndpointRequired, total=False):
    #: Start of the current failure streak (epoch ms), or ``None`` when the last delivery
    #: succeeded.
    failing_since: int | None
    #: When the most recent failure streak began (epoch ms). Kept after the endpoint
    #: recovers or is re-enabled, so ``since="failing_since"`` still resolves on replay.
    last_failing_since: int | None
    #: While a secret rotation overlap is open: when the previous secret stops signing
    #: deliveries (epoch ms). Until then every delivery carries two signatures. ``None``
    #: otherwise.
    previous_secret_expires_at: int | None
    #: ``canonical`` (default), ``legacy`` or ``both``: which event spellings are sent.
    event_naming: Literal["canonical", "legacy", "both"]
    #: ``["v1"]`` (default) or ``["v1", "v2"]``: ``v2`` signatures also cover the URL.
    signature_versions: list[str]
    #: Where deliveries go instead of an HTTPS URL (``type``, ..., ``credentials_set``).
    destination: dict[str, Any] | None
    description: str | None
    #: ``healthy``, ``degraded`` or ``failing``.
    health: str
    last_success_at: int | None
    consecutive_failures: int
    success_rate_24h: float | None
    attempts_24h: int
    alert_contacts: list[str]
    metadata: dict[str, Any]
    external_ref: str | None


class RotateWebhookSecretBody(TypedDict, total=False):
    #: How long the previous secret keeps signing deliveries (as a second
    #: ``atlas-signature`` entry), in seconds. Default 0: it stops at once. At most 604800
    #: (7 days). Set it only once every receiver verifies with a verifier that accepts
    #: several signatures (this package 0.7.0+).
    overlap_seconds: int


class WebhookEventCatalogEntry(TypedDict, total=False):
    """One subscribable event, described (``event_catalog`` on the endpoint list)."""

    name: str
    description: str
    #: Who should act on it, e.g. ``rp_sessions``, ``rp_accounts``, ``dsar``.
    relevant_for: list[str]
    #: Set on a superseded spelling: subscribe to this event instead.
    deprecated_alias_of: str


class WebhookDelivery(TypedDict, total=False):
    """One webhook delivery attempt (``webhooks.endpoints.list_deliveries``)."""

    object: Literal["webhook_delivery"]
    id: str
    event_id: str
    event_type: str | None
    attempt_number: int
    max_attempts: int
    payload: Any
    status: Literal["pending", "success", "failed"]
    http_status: int | None
    #: ``webhook_redirect_not_followed`` (see ``location``), ``webhook_http_error``,
    #: ``webhook_timeout``, ``webhook_network_error`` or ``webhook_url_blocked``.
    error: str | None
    #: The absolute ``Location`` of a 3xx answer. Not followed.
    location: str | None
    response_snippet: str | None
    next_retry_at: int | None
    delivered_at: int | None
    created_at: int


class _CreateWebhookEndpointRequired(TypedDict):
    url: str


class CreateWebhookEndpointBody(_CreateWebhookEndpointRequired, total=False):
    enabled_events: list[str]
    event_naming: Literal["canonical", "legacy", "both"]
    signature_versions: list[str]
    #: A non-HTTPS destination (``url`` is then optional); its secrets go in
    #: ``destination_credentials`` (write-only).
    destination: dict[str, Any]
    destination_credentials: dict[str, Any]
    description: str
    alert_contacts: list[str]
    external_ref: str
    metadata: dict[str, Any]


# --------------------------------------------------------------------------- #
# OAuth clients                                                                #
# --------------------------------------------------------------------------- #

TokenAuthMethod = Literal["client_secret_basic", "client_secret_post", "none"]


class _OAuthClientRequired(TypedDict):
    object: Literal["oauth_client"]
    id: str
    client_id: str
    name: str
    logo_url: str | None
    redirect_uris: list[str]
    allowed_scopes: list[str]
    grant_types: list[str]
    token_endpoint_auth_method: TokenAuthMethod
    secret_prefix: str | None
    is_public: bool
    first_party: bool
    created_at: int
    updated_at: int


class OAuthClient(_OAuthClientRequired, SealedSecrets, total=False):
    #: After a rotation with overlap: when the previous secret stops working (epoch ms).
    #: ``None`` when only the current secret is accepted.
    previous_secret_expires_at: int | None
    #: First-party only. When ``True``, ``/oauth2/logout`` with this client's
    #: ``client_id`` and an exactly registered ``post_logout_redirect_uri`` ends the
    #: session and redirects straight back (with ``state``), skipping the
    #: confirmation page. ``False`` by default.
    skip_logout_confirmation: bool
    #: Every OAuth flow for the client is refused while ``True``.
    disabled: bool
    #: PKCE is required for this confidential client too.
    require_pkce: bool
    #: ``public`` (``sub`` = the user id) or ``pairwise`` (a per-sector ``sub``).
    subject_type: Literal["public", "pairwise"]
    #: The pairwise sector document, if registered.
    sector_identifier_uri: str | None
    #: When the current secret stops authenticating (epoch ms); ``None`` = never.
    client_secret_expires_at: int | None
    #: ``cimd`` when the client came from its Client ID Metadata Document.
    discovery_source: str | None
    #: ``jwt`` or ``opaque`` access tokens for this client; ``None`` inherits.
    access_token_format: Literal["jwt", "opaque"] | None
    #: Token lifetime overrides (seconds); a ``None`` field is inherited. On write it
    #: replaces the overrides; ``None`` clears them all.
    token_lifetimes: OAuthTokenLifetimes | None


class OAuthTokenLifetimes(TypedDict, total=False):
    """Token lifetimes in seconds; a missing or ``None`` field inherits the API's, then
    the instance's, then Atlas's default. Bounds: access / id token 60–86400; refresh
    token 300–31536000 (idle ≤ absolute); authorization code 10–600; device code
    60–1800."""

    access_token_ttl_seconds: int | None
    id_token_ttl_seconds: int | None
    refresh_token_absolute_ttl_seconds: int | None
    refresh_token_idle_ttl_seconds: int | None
    authorization_code_ttl_seconds: int | None
    device_code_ttl_seconds: int | None


class RotateOAuthClientSecretBody(TypedDict, total=False):
    #: How long the previous secret keeps working, in seconds. Default 86400 (24 hours);
    #: 0 revokes it now; at most 604800 (7 days).
    overlap_seconds: int
    #: Lifetime of the new secret (reported as ``client_secret_expires_at``); omit for
    #: one that does not expire.
    secret_expires_in_seconds: int


class _OAuthClientSecretRotationRequired(_OAuthClientRequired):
    #: The new client secret. Returned exactly once.
    client_secret: str
    #: The overlap applied, in seconds.
    overlap_seconds: int
    #: When the previous secret stops working (epoch ms), or ``None`` when it already has.
    previous_secret_expires_at: int | None


class OAuthClientSecretRotation(_OAuthClientSecretRotationRequired, SealedSecrets, total=False):
    """The rotate response: the client, its new secret (shown once) and the overlap."""

    note: str
    skip_logout_confirmation: bool


class ClientGrant(TypedDict):
    object: Literal["client_grant"]
    id: str
    client_id: str
    resource_server_id: str
    scopes: list[str]
    created_at: int
    updated_at: int


class _CreateOAuthClientRequired(TypedDict):
    name: str
    redirect_uris: list[str]


class CreateOAuthClientBody(_CreateOAuthClientRequired, total=False):
    allowed_scopes: list[str]
    grant_types: list[str]
    token_endpoint_auth_method: TokenAuthMethod
    logo_url: str
    first_party: bool
    #: Where ``/oauth2/logout`` may send the user after sign-out (exact match).
    post_logout_redirect_uris: list[str]
    #: OIDC Back-Channel Logout: a signed ``logout_token`` is POSTed here on sign-out.
    backchannel_logout_uri: str | None
    backchannel_logout_session_required: bool
    #: OIDC Front-Channel Logout: loaded in a hidden iframe on the sign-out page.
    frontchannel_logout_uri: str | None
    frontchannel_logout_session_required: bool
    #: First-party clients only (a third-party client is refused with 422
    #: ``VALIDATION_FAILED``, param ``skip_logout_confirmation``). When ``True``,
    #: RP-initiated logout (``/oauth2/logout``) with this ``client_id`` and an exactly
    #: registered ``post_logout_redirect_uri`` ends the session and redirects straight
    #: back with ``state``, without the confirmation page.
    skip_logout_confirmation: bool
    #: How long the issued secret authenticates (reported as ``client_secret_expires_at``).
    secret_expires_in_seconds: int
    #: ``pairwise`` gives the client a per-sector ``sub`` (OIDC Core §8).
    subject_type: Literal["public", "pairwise"]
    #: An https URL listing every redirect_uri; required for a pairwise client whose
    #: redirect_uris span more than one host. ``None`` clears it.
    sector_identifier_uri: str | None
    #: ``jwt`` or ``opaque`` access tokens for this client; ``None`` inherits.
    access_token_format: Literal["jwt", "opaque"] | None
    #: Token lifetime overrides (seconds); a ``None`` field is inherited. On write it
    #: replaces the overrides; ``None`` clears them all.
    token_lifetimes: OAuthTokenLifetimes | None


class UpdateOAuthClientBody(TypedDict, total=False):
    name: str
    redirect_uris: list[str]
    allowed_scopes: list[str]
    grant_types: list[str]
    token_endpoint_auth_method: TokenAuthMethod
    logo_url: str | None
    first_party: bool
    #: Where ``/oauth2/logout`` may send the user after sign-out (exact match).
    post_logout_redirect_uris: list[str]
    #: OIDC Back-Channel Logout: a signed ``logout_token`` is POSTed here on sign-out.
    backchannel_logout_uri: str | None
    backchannel_logout_session_required: bool
    #: OIDC Front-Channel Logout: loaded in a hidden iframe on the sign-out page.
    frontchannel_logout_uri: str | None
    frontchannel_logout_session_required: bool
    #: First-party clients only (a third-party client is refused with 422
    #: ``VALIDATION_FAILED``, param ``skip_logout_confirmation``). When ``True``,
    #: RP-initiated logout (``/oauth2/logout``) with this ``client_id`` and an exactly
    #: registered ``post_logout_redirect_uri`` ends the session and redirects straight
    #: back with ``state``, without the confirmation page.
    skip_logout_confirmation: bool
    #: How long the issued secret authenticates (reported as ``client_secret_expires_at``).
    secret_expires_in_seconds: int
    #: ``pairwise`` gives the client a per-sector ``sub`` (OIDC Core §8).
    subject_type: Literal["public", "pairwise"]
    #: An https URL listing every redirect_uri; required for a pairwise client whose
    #: redirect_uris span more than one host. ``None`` clears it.
    sector_identifier_uri: str | None
    #: Refuse (``True``) or re-allow (``False``) every OAuth flow for the client.
    disabled: bool
    #: Require PKCE for this confidential client too.
    require_pkce: bool
    #: ``jwt`` or ``opaque`` access tokens for this client; ``None`` inherits.
    access_token_format: Literal["jwt", "opaque"] | None
    #: Token lifetime overrides (seconds); a ``None`` field is inherited. On write it
    #: replaces the overrides; ``None`` clears them all.
    token_lifetimes: OAuthTokenLifetimes | None


class _CreateGrantRequired(TypedDict):
    resource_server_id: str


class CreateGrantBody(_CreateGrantRequired, total=False):
    scopes: list[str]


# --------------------------------------------------------------------------- #
# Resource servers                                                             #
# --------------------------------------------------------------------------- #


class _ResourceServerRequired(TypedDict):
    object: Literal["resource_server"]
    id: str
    identifier: str
    name: str
    scopes: list[dict[str, Any]]
    token_ttl_seconds: int
    signing_alg: str
    created_at: int
    updated_at: int


class ResourceServer(_ResourceServerRequired, total=False):
    #: Atlas serves the API's RFC 9728 protected-resource metadata document.
    publish_resource_metadata: bool
    #: ``jwt`` or ``opaque`` access tokens for this API; ``None`` inherits.
    access_token_format: Literal["jwt", "opaque"] | None
    #: Refresh-token lifetimes for grants issued for this API (seconds); ``None`` inherits.
    refresh_token_absolute_ttl_seconds: int | None
    refresh_token_idle_ttl_seconds: int | None
    #: client_ids of confidential clients allowed to introspect this API's tokens.
    introspection_client_ids: list[str]


class _CreateResourceServerRequired(TypedDict):
    identifier: str
    name: str


class CreateResourceServerBody(_CreateResourceServerRequired, total=False):
    scopes: list[Any]
    token_ttl_seconds: int
    #: ``RS256`` or ``ES256``: the algorithm of this API's access tokens.
    signing_alg: Literal["RS256", "ES256"]
    #: Serve the RFC 9728 protected-resource metadata document for this API.
    publish_resource_metadata: bool
    #: ``jwt`` or ``opaque`` access tokens for this API; ``None`` inherits.
    access_token_format: Literal["jwt", "opaque"] | None
    #: Refresh-token lifetimes for grants issued for this API (seconds); ``None`` inherits.
    refresh_token_absolute_ttl_seconds: int | None
    refresh_token_idle_ttl_seconds: int | None
    #: client_ids of confidential clients allowed to introspect this API's tokens.
    introspection_client_ids: list[str]


class UpdateResourceServerBody(TypedDict, total=False):
    name: str
    scopes: list[Any]
    token_ttl_seconds: int
    identifier: str
    signing_alg: Literal["RS256", "ES256"]
    publish_resource_metadata: bool
    #: ``jwt`` or ``opaque`` access tokens for this API; ``None`` inherits.
    access_token_format: Literal["jwt", "opaque"] | None
    #: Refresh-token lifetimes for grants issued for this API (seconds); ``None`` inherits.
    refresh_token_absolute_ttl_seconds: int | None
    refresh_token_idle_ttl_seconds: int | None
    #: client_ids of confidential clients allowed to introspect this API's tokens.
    introspection_client_ids: list[str]


# --------------------------------------------------------------------------- #
# SSO connections                                                              #
# --------------------------------------------------------------------------- #


class ClaimRoleMapping(TypedDict):
    claim: str
    value: str
    roleKey: str


class _SsoConnectionRequired(TypedDict):
    object: Literal["sso_connection"]
    id: str
    organization_id: str | None
    type: str
    status: str
    oidc_issuer: str | None
    oidc_client_id: str | None
    has_secret: bool
    saml_idp_entity_id: str | None
    saml_idp_sso_url: str | None
    saml_sp_entity_id: str | None
    has_saml_certificate: bool
    saml_allow_idp_initiated: bool
    saml_sign_authn_requests: bool
    saml_want_response_signed: bool
    has_discourse_secret: bool
    discourse_provider_url: str | None
    allowed_domains: list[str]
    claim_role_mappings: list[ClaimRoleMapping]
    default_role_id: str | None
    created_at: int
    updated_at: int


class SsoConnection(_SsoConnectionRequired, total=False):
    #: SAML Single Logout is on for the connection.
    saml_single_logout: bool
    #: The IdP SingleLogoutService Location / ResponseLocation and delivery binding.
    saml_idp_slo_url: str | None
    saml_idp_slo_response_url: str | None
    saml_idp_slo_binding: Literal["redirect", "post"]
    #: The IdP SOAP SingleLogoutService — the back channel for sessions ended server-side.
    saml_idp_slo_soap_url: str | None
    #: Assertions not encrypted to the connection's key are refused.
    saml_require_encrypted_assertions: bool
    #: An SP encryption key pair is set up (the private key is never returned).
    has_saml_encryption_key: bool
    #: A key rotation is in progress (the previous key is still accepted).
    has_previous_saml_encryption_key: bool
    saml_encryption_rotated_at: int | None
    #: OIDC relying-party settings (see custom OAuth providers).
    profile_mapping: ProfileMapping | None
    token_endpoint_auth_method: TokenEndpointAuthMethod | None
    client_assertion_audience: str | None
    logout: UpstreamLogoutSettings
    idp_initiated_login: IdpInitiatedLoginSettings
    #: OIDC connections: the URLs to register at the IdP.
    upstream_urls: UpstreamUrls | None


class _SamlMetadataRequired(TypedDict):
    object: Literal["sso_saml_metadata"]
    sp_entity_id: str
    acs_url: str
    metadata_xml: str


class SamlMetadata(_SamlMetadataRequired, total=False):
    #: Our SingleLogoutService URL (both bindings), when Single Logout is on.
    slo_url: str | None


class SamlEncryptionKey(TypedDict):
    """A SAML connection's SP encryption key pair — certificates only."""

    object: Literal["sso_saml_encryption_key"]
    connection_id: str
    #: The current certificate (PEM), published in SP metadata; ``None`` when off.
    certificate: str | None
    #: The previous certificate during a rotation.
    previous_certificate: str | None
    #: When the current key was installed (epoch ms).
    rotated_at: int | None
    require_encrypted_assertions: bool


class CreateSsoConnectionBody(TypedDict, total=False):
    organization_id: str | None
    type: Literal["oidc", "saml", "discourse"]
    status: Literal["draft", "active", "disabled"]
    oidc_issuer: str
    oidc_client_id: str
    oidc_client_secret: str
    saml_idp_entity_id: str
    saml_idp_sso_url: str
    saml_idp_certificate: str
    saml_sp_entity_id: str
    saml_allow_idp_initiated: bool
    saml_sign_authn_requests: bool
    saml_want_response_signed: bool
    discourse_secret: str
    discourse_provider_url: str
    allowed_domains: list[str]
    claim_role_mappings: list[ClaimRoleMapping]
    default_role_id: str | None
    #: For an org-bound connection: ``member`` (default) seats the user as an org
    #: member; ``end_user`` seats them into the org's end-user pool instead.
    provisioning_mode: Literal["member", "end_user"]
    #: Optional manual OIDC endpoint overrides.
    manual_endpoints: dict[str, Any]
    #: SAML Single Logout on/off; the IdP SLO URLs are https (``None`` clears them).
    saml_single_logout: bool
    saml_idp_slo_url: str | None
    saml_idp_slo_response_url: str | None
    saml_idp_slo_binding: Literal["redirect", "post"] | None
    #: The back channel for sessions ended server-side (https; ``None`` clears it).
    saml_idp_slo_soap_url: str | None
    #: Requires an encryption key (see ``sso_connections.create_saml_encryption_key``).
    saml_require_encrypted_assertions: bool
    #: OIDC: declarative profile mapping; ``None`` clears it.
    profile_mapping: ProfileMapping | None
    #: OIDC: token-endpoint client authentication (private_key_jwt needs no secret).
    token_endpoint_auth_method: TokenEndpointAuthMethod | None
    client_assertion_audience: str | None
    #: OIDC: RP-initiated and back-channel logout.
    logout: UpstreamLogoutSettings | None
    #: OIDC: third-party initiated login.
    idp_initiated_login: IdpInitiatedLoginSettings | None


#: PATCH accepts everything create does except ``type``, which is immutable.
UpdateSsoConnectionBody = CreateSsoConnectionBody


# --------------------------------------------------------------------------- #
# SCIM tokens                                                                  #
# --------------------------------------------------------------------------- #


class _ScimTokenRequired(TypedDict):
    object: Literal["scim_token"]
    id: str
    name: str | None
    organization_id: str
    connection_id: str | None
    prefix: str
    last_used_at: int | None
    expires_at: int | None
    revoked_at: int | None
    created_at: int


class ScimRoleMapping(TypedDict):
    #: A SCIM ``roles`` value.
    value: str
    #: The organization role key it maps to.
    role: str


class ScimToken(_ScimTokenRequired, SealedSecrets, total=False):
    #: ``None`` = read and write; ``["read"]`` = read-only.
    scopes: list[str] | None
    role_mappings: list[ScimRoleMapping]


class _CreateScimTokenRequired(TypedDict):
    organization_id: str


class CreateScimTokenBody(_CreateScimTokenRequired, total=False):
    name: str
    connection_id: str
    #: ``["read"]`` makes the token read-only.
    scopes: list[str]
    role_mappings: list[ScimRoleMapping]


class UpdateScimTokenBody(TypedDict, total=False):
    name: str | None
    scopes: list[str] | None
    role_mappings: list[ScimRoleMapping] | None


# --------------------------------------------------------------------------- #
# Custom domains                                                               #
# --------------------------------------------------------------------------- #


class CustomDomain(TypedDict):
    object: Literal["custom_domain"]
    id: str
    role: Literal["fapi", "accounts"]
    host: str
    status: str
    action: str
    live: bool
    cname_target: str
    last_checked_at: int | None
    last_observed_target: str | None
    failure_reason: str | None
    certificate_expires_at: int | None
    cookie_domain: str | None
    #: DNS automation: ``{"provider": "cloudflare", "token_set": True}`` or ``None``.
    dns: dict[str, Any] | None


class _CustomDomainDnsInputRequired(TypedDict):
    provider: Literal["cloudflare"]
    #: Write-only; never returned.
    api_token: str


class CustomDomainDnsInput(_CustomDomainDnsInputRequired, total=False):
    """Let Atlas write the domain's DNS record."""

    #: Replace a conflicting existing record.
    overwrite: bool


class _CreateDomainRequired(TypedDict):
    host: str


class CreateDomainBody(_CreateDomainRequired, total=False):
    role: Literal["fapi", "accounts"]
    dns: CustomDomainDnsInput


# --------------------------------------------------------------------------- #
# Waitlist                                                                     #
# --------------------------------------------------------------------------- #


class WaitlistEntry(TypedDict):
    object: Literal["waitlist_entry"]
    id: str
    email_address: str
    status: str
    note: str | None
    decided_by: str | None
    decided_at: int | None
    created_at: int


class _DecideWaitlistRequired(TypedDict):
    status: Literal["approved", "denied"]


class DecideWaitlistBody(_DecideWaitlistRequired, total=False):
    note: str


# --------------------------------------------------------------------------- #
# Restrictions                                                                 #
# --------------------------------------------------------------------------- #


class AllowlistIdentifier(TypedDict):
    object: Literal["allowlist_identifier"]
    id: str
    identifier: str
    created_at: int


class BlocklistIdentifier(TypedDict):
    object: Literal["blocklist_identifier"]
    id: str
    identifier: str
    created_at: int


# --------------------------------------------------------------------------- #
# Attack protection                                                            #
# --------------------------------------------------------------------------- #


class DormantAccountsSettings(TypedDict, total=False):
    """When an account idle for ``threshold_days`` (1–3650, default 90) signs in again:
    an audit entry, the ``user.reactivated`` webhook, an optional notice to the user
    and, with ``require_mfa``, a second-factor step-up (``on_no_factor`` decides for an
    account without one)."""

    enabled: bool
    threshold_days: int
    require_mfa: bool
    on_no_factor: Literal["allow", "require_enroll", "block"]
    notify_user: bool


class _AttackProtectionRequired(TypedDict):
    object: Literal["attack_protection"]
    brute_force: dict[str, Any]
    breached_password: dict[str, Any]
    suspicious_ip: dict[str, Any]
    captcha: dict[str, Any]


class AttackProtection(_AttackProtectionRequired, total=False):
    country_restrictions: dict[str, Any]
    device_accounts: dict[str, Any]
    #: Dormant-account reactivation alerts (writable).
    dormant_accounts: DormantAccountsSettings


class UpdateAttackProtectionBody(TypedDict, total=False):
    brute_force: dict[str, Any]
    breached_password: dict[str, Any]
    dormant_accounts: DormantAccountsSettings


# --------------------------------------------------------------------------- #
# Actor & sign-in tokens                                                       #
# --------------------------------------------------------------------------- #


class ActorToken(TypedDict):
    object: Literal["actor_token"]
    id: str
    user_id: str
    actor: dict[str, Any]
    token: str
    expires_in: int


class _CreateActorTokenRequired(TypedDict):
    user_id: str
    actor: dict[str, Any]


class CreateActorTokenBody(_CreateActorTokenRequired, total=False):
    expires_in_seconds: int


class SignInToken(TypedDict):
    object: Literal["sign_in_token"]
    user_id: str
    token: str
    expires_in: int


class _CreateSignInTokenRequired(TypedDict):
    user_id: str


class CreateSignInTokenBody(_CreateSignInTokenRequired, total=False):
    expires_in_seconds: int


# --------------------------------------------------------------------------- #
# Audit logs                                                                   #
# --------------------------------------------------------------------------- #


class AuditLog(TypedDict):
    object: Literal["audit_log"]
    id: str
    actor_type: str
    actor_id: str | None
    action: str
    target_type: str | None
    target_id: str | None
    metadata: dict[str, Any] | None
    created_at: int


# --------------------------------------------------------------------------- #
# JWT templates                                                                #
# --------------------------------------------------------------------------- #


class JwtTemplate(TypedDict):
    object: Literal["jwt_template"]
    name: str
    claims: dict[str, str]


class _CreateJwtTemplateRequired(TypedDict):
    name: str
    claims: dict[str, str]


class CreateJwtTemplateBody(_CreateJwtTemplateRequired, total=False):
    pass


# --------------------------------------------------------------------------- #
# Sign in with Atlas apps (platform key)                                       #
# --------------------------------------------------------------------------- #


class AtlasIdAppBrandingCopy(TypedDict, total=False):
    """Text overrides on the Sign in with Atlas page and consent screen."""

    sign_in_title: str | None
    sign_in_subtitle: str | None
    sign_up_title: str | None
    sign_up_subtitle: str | None
    consent_message: str | None
    support_url: str | None
    support_label: str | None


class _AtlasIdAppBrandingRequired(TypedDict):
    theme: Literal["auto", "light", "dark"]
    accent_color: str | None
    background_color: str | None
    privacy_policy_url: str | None
    terms_of_service_url: str | None
    copy: AtlasIdAppBrandingCopy


class AtlasIdAppBranding(_AtlasIdAppBrandingRequired, total=False):
    """How the Sign in with Atlas page looks for an app, as stored."""

    #: The stored design overrides (``None`` = none).
    design: AtlasDesign | None
    #: What the Sign in with Atlas page renders with.
    resolved_design: ResolvedDesign


class _AtlasIdAppRequired(TypedDict):
    object: Literal["atlas_id_app"]
    id: str
    client_id: str
    name: str
    redirect_uris: list[str]
    post_logout_redirect_uris: list[str]
    backchannel_logout_uri: str | None
    backchannel_logout_session_required: bool
    frontchannel_logout_uri: str | None
    frontchannel_logout_session_required: bool
    allowed_scopes: list[str]
    type: Literal["confidential", "public"]
    created_at: int
    updated_at: int


class AtlasIdApp(_AtlasIdAppRequired, SealedSecrets, total=False):
    """A Sign in with Atlas app (an OpenID Connect client on https://atlasauth.net)."""

    logo_url: str | None
    homepage_url: str | None
    branding: AtlasIdAppBranding
    secret_prefix: str | None
    managed_by_instance_id: str | None
    #: ``instance_toggle``: an instance's Sign in with Atlas toggle app; ``adopted``: handed
    #: to an instance with ``atlas_id_apps.set_managed_by``.
    managed_via: Literal["instance_toggle", "adopted"] | None
    #: The page origins the Sign in with Atlas button script ran on in the last 7 days.
    button_rendered_origins: list[AtlasIdOriginSeen]
    #: How many people have signed in to this app (on reads).
    user_count: int
    #: Confidential apps only; returned exactly once (on create and rotate_secret).
    client_secret: str
    note: str
    #: The per-app webhook URL, or ``None``.
    webhook_url: str | None
    webhook_events: list[str]
    #: ``False`` once auto-disabled after repeated failures; ``None`` without a webhook.
    webhook_active: bool | None
    #: The per-app webhook signing secret, returned exactly once (first set or rotated).
    webhook_secret: str
    #: While a webhook secret rotation overlap is open: when the previous secret stops
    #: signing deliveries (epoch ms); else ``None``.
    webhook_previous_secret_expires_at: int | None
    #: After a client secret rotation with an overlap: when the previous secret stops
    #: working (epoch ms); else ``None``.
    previous_secret_expires_at: int | None
    #: When the current client secret was issued (epoch ms); ``None`` for a public app.
    secret_issued_at: int | None
    #: On a rotation: the overlap applied, in seconds.
    overlap_seconds: int
    #: Test sign-in mode: ``+atlas_test`` addresses on a verified domain sign in to this app
    #: with the fixed code 424242.
    test_mode: bool
    #: Test and review accounts must use an address on a domain you verified.
    provisioned_verified_domains_only: bool


class _AtlasIdProvisionedAccountApp(TypedDict):
    id: str
    client_id: str
    name: str


class _AtlasIdProvisionedAccountRequired(TypedDict):
    object: Literal["atlas_id_provisioned_account"]
    id: str
    #: The Atlas ID subject the app sees.
    sub: str
    email: str | None
    email_verified: bool
    label: str
    kind: Literal["provisioned", "test_mode", "developer"]
    provisioned_by: Literal["app", "staff"]
    app_ids: list[str]
    apps: list[_AtlasIdProvisionedAccountApp]
    any_app: bool
    two_factor_exempt: bool
    #: Epoch ms; ``None`` = never expires.
    expires_at: int | None
    expired: bool
    developer_account_id: str | None
    created_by: dict[str, str]
    last_sign_in_at: int | None
    password_rotated_at: int | None
    created_at: int
    updated_at: int


class AtlasIdProvisionedAccount(_AtlasIdProvisionedAccountRequired, total=False):
    """A Sign in with Atlas test or review account, confined to the app(s) it was made for.

    ``password`` is a shown-once secret (create and rotation only): never log it. With a
    ``secret_recipient`` it is absent and ``sealed_password`` carries it, sealed to your key
    (open it with ``SealedBox``).
    """

    password: str
    sealed_password: str
    secrets_sealed: SecretsSealed
    note: str


class AtlasIdProvisionedAccountList(TypedDict):
    object: Literal["list"]
    data: list[AtlasIdProvisionedAccount]
    #: The account-wide cap (default 25).
    limit: int
    #: Test accounts the account holds across all its apps.
    total: int


class AtlasIdProvisionedAccountDeleted(TypedDict):
    object: Literal["atlas_id_provisioned_account"]
    id: str
    deleted: Literal[True]
    sessions_ended: int


class _CreateAtlasIdProvisionedAccountRequired(TypedDict):
    email: str
    #: What the account is for, e.g. "app-store reviewer".
    label: str


class CreateAtlasIdProvisionedAccountBody(_CreateAtlasIdProvisionedAccountRequired, total=False):
    #: At least 12 characters. Omit it and Atlas generates one. Returned once either way.
    password: str
    #: Default ``True``.
    email_verified: bool
    #: Never asked for a second factor when signing in to this app. A risk you opt into.
    two_factor_exempt: bool
    #: Epoch ms or ISO 8601; omit or ``None`` for a non-expiring account.
    expires_at: int | str | None


class RotateAtlasIdProvisionedPasswordBody(TypedDict, total=False):
    #: At least 12 characters; omit it and Atlas generates one.
    password: str


class AccountDomainVerification(TypedDict):
    type: Literal["TXT"]
    #: The TXT record to publish.
    name: str
    value: str


class _AccountDomainRequired(TypedDict):
    object: Literal["account_domain"]
    id: str
    domain: str
    verified: bool
    verified_at: int | None
    last_checked_at: int | None
    verification: AccountDomainVerification
    created_at: int


class AccountDomain(_AccountDomainRequired, total=False):
    """A domain the account claimed; verified ones gate test sign-in mode."""

    record_found: bool


class AccountDomainList(TypedDict):
    object: Literal["list"]
    data: list[AccountDomain]
    verified_domains: list[str]


class SetAtlasIdAppManagedByBody(TypedDict):
    """Body of ``atlas_id_apps.set_managed_by``: the instance to hand grant management to,
    or ``None`` to take it back."""

    instance_id: str | None


class AtlasIdAppManagedBy(AtlasIdApp):
    """``PUT /v1/platform/atlas_id_apps/{id}/managed_by``: the app, plus whether anything changed."""

    changed: bool


class RotateAtlasIdAppSecretBody(TypedDict, total=False):
    #: How long the previous secret keeps working, in seconds; at most 604800 (7 days).
    #: Default for the client secret: 86400 (24 hours). Default for the webhook secret: 0
    #: (it stops signing at once). ``0`` stops it now.
    overlap_seconds: int


class AtlasIdAppList(TypedDict):
    """``GET /v1/platform/atlas_id_apps``: the apps plus the issuer to configure."""

    object: Literal["list"]
    data: list[AtlasIdApp]
    issuer: str
    discovery_url: str
    #: The most apps one account may register.
    limit: int


# --------------------------------------------------------------------------- #
# OAuth providers                                                              #
# --------------------------------------------------------------------------- #


class OAuthProviderSettings(TypedDict, total=False):
    """Non-secret provider settings for ``oauth_providers.upsert``.

    A redirect provider takes ``redirect_uri``. The wallet providers take their
    verifier settings: ``siwe`` — ``domain``, ``chain_ids``, ``rpc_url``; ``siws`` —
    ``domain``, ``networks``; ``siwf`` — ``domain``, ``chain_ids``,
    ``optimism_rpc_url``, ``id_registry_address``. ``None`` or ``""`` clears one
    setting; an unknown key is refused.
    """

    redirect_uri: str | None
    #: Hostname with an optional port, no scheme or path (e.g. ``app.example.com``).
    domain: str | None
    #: EIP-155 chain ids, as a list or a comma-separated string.
    chain_ids: list[int] | str | None
    #: An ``https://`` RPC URL; enables contract-wallet (EIP-1271) signatures.
    rpc_url: str | None
    #: Solana networks: ``mainnet``, ``devnet`` or ``testnet``.
    networks: list[str] | str | None
    #: An ``https://`` Optimism RPC URL, required to verify Farcaster id ownership.
    optimism_rpc_url: str | None
    #: The Farcaster id registry contract (a ``0x`` address).
    id_registry_address: str | None


class UpsertOAuthProviderBody(TypedDict, total=False):
    """Set a provider's credentials and/or re-brand its button.

    ``display_name`` / ``icon_url`` / ``mode`` work without credentials; ``None``
    or ``""`` clears each of them.
    """

    client_id: str
    client_secret: str
    scopes: list[str]
    values: dict[str, str]
    settings: OAuthProviderSettings
    custom_redirect_uri: str
    native: bool
    #: Force the sign-in mode; ``None`` or ``""`` clears the override.
    mode: Literal["native", "redirect", ""] | None
    #: The brand shown on the button (e.g. ``"Discord"``); empty clears.
    display_name: str | None
    #: An http(s) or ``data:image`` icon URL for the button; empty clears.
    icon_url: str | None


# --------------------------------------------------------------------------- #
# Generated from the public OpenAPI document (BAPI + PLATFORM).                #
# --------------------------------------------------------------------------- #


class _OrgPolicyEndUserPoolRequired(TypedDict):
    enabled: bool


class OrgPolicyEndUserPool(_OrgPolicyEndUserPoolRequired, total=False):
    requireApproval: bool
    allowHostedSignup: bool


class OrgPolicy(TypedDict, total=False):
    """Org policy override object."""

    requireMfa: bool
    ssoRequired: bool
    sessionIdleOverrideMs: int
    #: Restrict which sign-in methods a member may use (e.g. "password", "passkey", "oauth",
    #: "oauth:google", "saml", "magic_link").
    allowedSignInMethods: list[str]
    #: CIDR allow-list gating sign-in for members (e.g. "203.0.113.0/24").
    ipAllowlist: list[str]
    #: Cap the absolute session lifetime for members, in seconds (300 … 7776000).
    maxSessionAgeSeconds: int
    endUserPool: OrgPolicyEndUserPool


class AtlasDesignPalette(TypedDict, total=False):
    primary: str
    primaryInk: str
    accent: str
    background: str
    surface: str
    text: str
    muted: str
    border: str
    danger: str
    success: str
    inputBackground: str
    inputText: str


class AtlasDesignTypography(TypedDict, total=False):
    font: Literal[
        "system",
        "system-serif",
        "system-mono",
        "inter",
        "roboto",
        "open-sans",
        "lato",
        "montserrat",
        "poppins",
        "nunito",
        "work-sans",
        "dm-sans",
        "manrope",
        "source-serif",
        "merriweather",
        "playfair-display",
        "jetbrains-mono",
        "ibm-plex-mono",
    ]
    headingFont: Literal[
        "system",
        "system-serif",
        "system-mono",
        "inter",
        "roboto",
        "open-sans",
        "lato",
        "montserrat",
        "poppins",
        "nunito",
        "work-sans",
        "dm-sans",
        "manrope",
        "source-serif",
        "merriweather",
        "playfair-display",
        "jetbrains-mono",
        "ibm-plex-mono",
    ]
    baseSize: int
    headingWeight: int
    bodyWeight: int
    letterCase: Literal["none", "uppercase"]
    scale: Literal[
        "minor-second",
        "major-second",
        "minor-third",
        "major-third",
        "perfect-fourth",
        "augmented-fourth",
        "perfect-fifth",
        "golden",
        "minor-seventh",
        "octave",
    ]


class AtlasDesignShape(TypedDict, total=False):
    radius: int
    controlRadius: int
    borderWidth: int


class AtlasDesignElevation(TypedDict, total=False):
    cardShadow: Literal["none", "sm", "md", "lg", "xl"]


class AtlasDesignSpacing(TypedDict, total=False):
    density: Literal["compact", "comfortable", "spacious"]


class AtlasDesignCard(TypedDict, total=False):
    style: Literal["solid", "glass", "outline", "none"]
    blur: int
    width: Literal["narrow", "normal", "wide"]


class AtlasDesignLayout(TypedDict, total=False):
    position: Literal["center", "left", "right", "split"]
    splitImageSide: Literal["left", "right"]
    logoPlacement: Literal["card", "page", "hidden"]
    logoSize: Literal["sm", "md", "lg"]


class AtlasDesignButtons(TypedDict, total=False):
    style: Literal["solid", "outline", "soft", "gradient"]
    socialLayout: Literal["list", "grid", "icons"]


class AtlasDesignInputs(TypedDict, total=False):
    style: Literal["outline", "filled", "underline"]


class AtlasDesignBackgroundGradientStopsItem(TypedDict):
    color: str
    at: float


class _AtlasDesignBackgroundGradientRequired(TypedDict):
    type: Literal["linear", "radial"]
    stops: list[AtlasDesignBackgroundGradientStopsItem]


class AtlasDesignBackgroundGradient(_AtlasDesignBackgroundGradientRequired, total=False):
    angle: int


class AtlasDesignBackgroundImageOverlay(TypedDict):
    color: str
    opacity: float


class _AtlasDesignBackgroundImageRequired(TypedDict):
    assetId: str


class AtlasDesignBackgroundImage(_AtlasDesignBackgroundImageRequired, total=False):
    fit: Literal["cover", "contain"]
    position: Literal[
        "top-left",
        "top",
        "top-right",
        "left",
        "center",
        "right",
        "bottom-left",
        "bottom",
        "bottom-right",
    ]
    overlay: AtlasDesignBackgroundImageOverlay
    blur: int


class AtlasDesignBackground(TypedDict, total=False):
    color: str
    gradient: AtlasDesignBackgroundGradient
    image: AtlasDesignBackgroundImage
    pattern: Literal["none", "dots", "grid", "noise"]


class AtlasDesignLogo(TypedDict, total=False):
    assetId: str
    darkAssetId: str


class AtlasDesign(TypedDict, total=False):
    """A structured sign-in page design: OVERRIDES on top of a preset (every field optional;
    unset fields come from the preset, then the defaults).
    """

    version: Literal[1]
    preset: Literal[
        "minimal",
        "atlas",
        "glass",
        "midnight",
        "editorial",
        "terminal",
        "sunrise",
        "forest",
        "grape",
        "slate",
        "split-photo",
        "bold",
    ]
    colorScheme: Literal["auto", "light", "dark"]
    palette: AtlasDesignPalette
    paletteDark: AtlasDesignPalette
    typography: AtlasDesignTypography
    shape: AtlasDesignShape
    elevation: AtlasDesignElevation
    spacing: AtlasDesignSpacing
    card: AtlasDesignCard
    layout: AtlasDesignLayout
    buttons: AtlasDesignButtons
    inputs: AtlasDesignInputs
    background: AtlasDesignBackground
    backgroundDark: AtlasDesignBackground
    logo: AtlasDesignLogo


class ResolvedDesign(TypedDict):
    """The fully-resolved design every surface renders (defaults ← preset ← overrides): the
    same shape as AtlasDesign with every field present.
    """

    version: Literal[1]
    preset: str
    colorScheme: Literal["auto", "light", "dark"]
    #: Every palette slot, as #rrggbb.
    palette: dict[str, str]
    #: Every palette slot, as #rrggbb.
    paletteDark: dict[str, str]
    typography: dict[str, Any]
    shape: dict[str, Any]
    elevation: dict[str, Any]
    spacing: dict[str, Any]
    card: dict[str, Any]
    layout: dict[str, Any]
    buttons: dict[str, Any]
    inputs: dict[str, Any]
    background: dict[str, Any]
    backgroundDark: dict[str, Any]
    logo: dict[str, Any]


class CreateActionBody(TypedDict, total=False):
    name: str
    trigger: str
    code: str
    enabled: bool
    secrets: Any


class _ActionRequired(TypedDict):
    object: Literal["action"]
    id: str
    name: str
    trigger: str
    code: str
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class Action(_ActionRequired, total=False):
    runtime: str
    secret_names: list[str]


class ActionBindingList(TypedDict):
    object: Literal["action_binding_list"]
    trigger: str
    action_ids: list[str]


class SetActionBindingBody(TypedDict, total=False):
    action_ids: Any


class UpdateActionBody(TypedDict, total=False):
    name: str
    code: str
    enabled: bool
    secrets: Any


class TestActionBodyEventConnection(TypedDict, total=False):
    strategy: str


class TestActionBodyEventRequest(TypedDict, total=False):
    ip: str
    user_agent: str
    #: The ISO code ``event.request.country`` should carry.
    country: str


class TestActionBodyEvent(TypedDict, total=False):
    user: dict[str, Any]
    connection: TestActionBodyEventConnection
    request: TestActionBodyEventRequest


class TestActionBody(TypedDict, total=False):
    event: TestActionBodyEvent


class _ActionTestResultRequired(TypedDict):
    object: Literal["action_test_result"]
    id: str
    denied: bool


class ActionTestResult(_ActionTestResultRequired, total=False):
    deny_reason: str | None
    access_token_claims: dict[str, Any]
    id_token_claims: dict[str, Any]
    app_metadata: dict[str, Any]
    logs: list[str]
    error: str | None
    #: What the code queued with ``api.http`` (sent only on a real post_login /
    #: post_user_registration run).
    http_requests: list[ActionTestHttpRequest]


class ActionTestHttpRequest(TypedDict):
    method: Literal["GET", "POST"]
    #: Query values are masked.
    url: str
    #: Header names only; values are never echoed.
    header_names: list[str]
    has_body: bool
    save_response_as: str | None


#: The window a spend cap counts over: ``request`` caps a single debit; ``day`` and
#: ``month`` are UTC calendar windows; ``total`` never resets.
ApiKeyLimitPeriod = Literal["request", "day", "month", "total"]


class ApiKeyLimit(TypedDict):
    """A per-key spend cap, metered with ``api_keys.record_usage``."""

    #: App-defined unit, e.g. ``"requests"`` or ``"usd_cents"``.
    unit: str
    #: The cap, in ``unit``.
    amount: int
    period: ApiKeyLimitPeriod


class ApiKeyLimitState(TypedDict):
    """A spend cap with its current-window usage."""

    unit: str
    period: ApiKeyLimitPeriod
    amount: int
    #: Used in the current window (always 0 for a per-request cap).
    used: int
    #: ``amount - used``, never below 0.
    remaining: int
    #: Epoch ms the window started; ``None`` for a per-request cap.
    window_start: int | None
    #: Epoch ms the window ends; ``None`` for per-request and total caps.
    resets_at: int | None


class ApiKeyUsageCounter(TypedDict):
    """A raw usage counter for one unit in its current window."""

    unit: str
    period: Literal["day", "month", "total"]
    used: int
    window_start: int
    #: Epoch ms the window ends; ``None`` for ``total``.
    resets_at: int | None


class _RecordApiKeyUsageBodyRequired(TypedDict):
    #: How much to debit, in ``unit`` (a positive integer).
    amount: int
    #: The unit to debit, matching the unit of the caps it should count against.
    unit: str


class RecordApiKeyUsageBody(_RecordApiKeyUsageBodyRequired, total=False):
    #: Retry-safe key: the same value returns the first outcome without counting
    #: again (kept 24 hours).
    idempotency_key: str


class _ApiKeyUsageDebitRequired(TypedDict):
    object: Literal["api_key_usage_debit"]
    key_id: str
    unit: str
    amount: int
    #: ``True`` when the debit was recorded; ``False`` when it would exceed a cap
    #: (nothing was recorded).
    allowed: bool
    #: The caps that refused the debit (empty when allowed).
    exceeded: list[ApiKeyLimitState]
    #: Every cap on the key after this call.
    usage: list[ApiKeyLimitState]
    #: The debited unit's day, month and total counters after this call.
    counters: list[ApiKeyUsageCounter]
    #: ``True`` when this is the stored outcome of an earlier call with the same
    #: idempotency key.
    idempotent_replay: bool


class ApiKeyUsageDebit(_ApiKeyUsageDebitRequired, total=False):
    #: ``"LIMIT_EXCEEDED"``, present only when ``allowed`` is ``False``.
    code: Literal["LIMIT_EXCEEDED"]


class ApiKeyUsage(TypedDict):
    """A key's current-window usage."""

    object: Literal["api_key_usage"]
    key_id: str
    limits: list[ApiKeyLimit] | None
    usage: list[ApiKeyLimitState]
    #: Counters for every unit the key has been debited in, capped or not.
    counters: list[ApiKeyUsageCounter]


class CreateApiKeyBodyImport(TypedDict, total=False):
    secret_hash: str
    hash_algorithm: Literal["sha256", "sha256_hex"]
    prefix: str
    created_at: float | None
    last_used_at: float | None
    revoked_at: float | None
    expires_at: float | None


CreateApiKeyBody = TypedDict(
    "CreateApiKeyBody",
    {
        "subject_type": 'Literal["user", "organization", "machine"]',
        "subject_id": "str",
        "name": "str",
        "claims": "dict[str, Any]",
        "expires_at": "float | None",
        "scopes": "list[str]",
        "constraints": "dict[str, Any]",
        "max_token_lifetime_seconds": "float | None",
        "public_key": "str | None",
        "limits": "list[ApiKeyLimit] | None",
        "import": "CreateApiKeyBodyImport",
        # Alternative to expires_at; without either the instance default lifetime applies.
        "expires_in_seconds": "int",
        # A custom secret prefix, e.g. "acme" gives acme_<id>_<secret>.
        "prefix": "str",
        # False mints the key disabled.
        "enabled": "bool",
        "rate_limit": "ApiKeyRateLimit",
        # A use budget each successful verify spends; None = unlimited.
        "remaining": "int | None",
    },
    total=False,
)


class _ApiKeyCreateRequired(TypedDict):
    object: Literal["api_key"]
    id: str
    subject_type: Literal["user", "organization", "machine"]
    subject_id: str
    name: str | None
    prefix: str
    claims: dict[str, Any]
    last_used_at: int | None
    expires_at: int | None
    revoked_at: int | None
    #: Created (epoch ms).
    created_at: int
    #: Reveal-once plaintext ak_ key (create-only).
    secret: str


class ApiKeyCreate(_ApiKeyCreateRequired, SealedSecrets, total=False):
    #: Tenant-defined scopes embedded into tokens minted from this key.
    scopes: list[str] | None
    #: Arbitrary constraint claims (e.g. desk_ids, cwd, run_as) embedded into minted tokens.
    constraints: dict[str, Any]
    #: Org-policy ceiling (seconds) on the lifetime of a token minted from this key.
    max_token_lifetime_seconds: int | None
    #: Registered SPKI PEM public key for proof-of-possession, or null for a bearer key.
    public_key: str | None
    #: RFC 7638 JWK thumbprint of public_key — the cnf.jkt minted tokens carry.
    public_key_jkt: str | None
    #: Per-key spend caps; ``None`` when the key has none.
    limits: list[ApiKeyLimit] | None
    #: Each cap with its current-window usage.
    usage: list[ApiKeyLimitState]
    note: str


class CreateApiKeyTokenBody(TypedDict, total=False):
    secret: str
    ttl_seconds: float
    audience: Any


class ApiKeyTokenCnf(TypedDict, total=False):
    """Proof-of-possession confirmation — present only for a PoP key."""

    jkt: str


class _ApiKeyTokenRequired(TypedDict):
    object: Literal["api_key_token"]
    #: The short-lived JWKS-signed access JWT (token_use:api_key).
    token: str
    token_type: Literal["Bearer"]
    #: Unique token id — deny-list this to revoke one token.
    jti: str
    #: The long-lived key this token was minted from (the JWT sub).
    key_id: str
    scopes: list[str]
    constraints: dict[str, Any]
    #: Lifetime in seconds (clamped to key expiry + org ceiling + global cap).
    expires_in: int
    #: Expiry (epoch ms).
    expires_at: int
    #: The issuer/JWKS a verifier checks this token against.
    issuer: str


class ApiKeyToken(_ApiKeyTokenRequired, total=False):
    subject_type: Literal["user", "organization", "machine"]
    subject_id: str
    #: Proof-of-possession confirmation — present only for a PoP key.
    cnf: ApiKeyTokenCnf


class VerifyApiKeyBody(TypedDict, total=False):
    secret: str
    #: Scopes the key must carry; a key missing one answers ``valid: False`` with
    #: ``code: "insufficient_scope"`` and ``missing_scopes``.
    required_scopes: list[str]


class _ApiKeyVerificationVariant1Required(TypedDict):
    object: Literal["api_key_verification"]
    valid: Literal[False]


class ApiKeyVerificationVariant1(_ApiKeyVerificationVariant1Required, total=False):
    """A refusal. Without ``code`` the key is unknown, revoked, expired, disabled or its
    subject deleted (never says which). With ``code`` a LIVE key was refused by its own
    policy: ``insufficient_scope`` (``missing_scopes``), ``rate_limited``
    (``retry_after_ms``) or ``usage_exhausted``.
    """

    code: Literal["insufficient_scope", "rate_limited", "usage_exhausted"]
    id: str
    missing_scopes: list[str]
    retry_after_ms: int
    remaining: int


class _ApiKeyVerificationVariant2Required(TypedDict):
    object: Literal["api_key_verification"]
    valid: Literal[True]
    id: str
    subject_type: str
    subject_id: str
    claims: dict[str, Any]


class ApiKeyVerificationVariant2(_ApiKeyVerificationVariant2Required, total=False):
    name: str | None
    scopes: list[str] | None
    constraints: dict[str, Any]
    #: The key's spend caps (``None`` when none).
    limits: list[ApiKeyLimit] | None
    #: Each cap with its current-window usage.
    usage: list[ApiKeyLimitState]
    last_used_at: int | None
    expires_at: int | None
    #: Uses left after this verify (``None`` = unlimited).
    remaining: int | None


ApiKeyVerification = Union[ApiKeyVerificationVariant1, ApiKeyVerificationVariant2]


class _ApiKeyRequired(TypedDict):
    object: Literal["api_key"]
    id: str
    subject_type: Literal["user", "organization", "machine"]
    subject_id: str
    name: str | None
    prefix: str
    claims: dict[str, Any]
    last_used_at: int | None
    expires_at: int | None
    revoked_at: int | None
    #: Created (epoch ms).
    created_at: int


class ApiKey(_ApiKeyRequired, total=False):
    #: Tenant-defined scopes embedded into tokens minted from this key.
    scopes: list[str] | None
    #: Arbitrary constraint claims (e.g. desk_ids, cwd, run_as) embedded into minted tokens.
    constraints: dict[str, Any]
    #: Org-policy ceiling (seconds) on the lifetime of a token minted from this key.
    max_token_lifetime_seconds: int | None
    #: Registered SPKI PEM public key for proof-of-possession, or null for a bearer key.
    public_key: str | None
    #: RFC 7638 JWK thumbprint of public_key — the cnf.jkt minted tokens carry.
    public_key_jkt: str | None
    #: Per-key spend caps; ``None`` when the key has none.
    limits: list[ApiKeyLimit] | None
    #: Each cap with its current-window usage (empty when the key has no caps).
    usage: list[ApiKeyLimitState]
    #: ``False`` for a disabled key (it verifies as invalid until re-enabled).
    enabled: bool
    #: The per-key verify throttle, or ``None``.
    rate_limit: ApiKeyRateLimit | None
    #: Uses left (each successful verify spends one); ``None`` = unlimited.
    remaining: int | None


class ApiKeyRateLimit(TypedDict):
    #: At most ``max`` verifies per ``window_seconds``.
    max: int
    window_seconds: int


class UpdateApiKeyBody(TypedDict, total=False):
    name: str | None
    claims: dict[str, Any]
    expires_at: float | None
    scopes: list[str]
    constraints: dict[str, Any]
    max_token_lifetime_seconds: float | None
    #: Replace the spend caps; ``None`` clears them (counters are kept).
    limits: list[ApiKeyLimit] | None
    #: ``False`` disables the key without revoking it; ``True`` re-enables it.
    enabled: bool
    #: Set the verify throttle; ``None`` removes it.
    rate_limit: ApiKeyRateLimit | None
    #: Set the use budget; ``None`` makes it unlimited.
    remaining: int | None


class ApiKeyRevokeResult(TypedDict):
    object: Literal["api_key"]
    id: str
    revoked: Literal[True]


class CreateAuditEventBodyActor(TypedDict, total=False):
    type: str
    id: str


class CreateAuditEventBodyTarget(TypedDict, total=False):
    type: str
    id: str
    name: str


class CreateAuditEventBody(TypedDict, total=False):
    actor: CreateAuditEventBodyActor
    action: str
    target: CreateAuditEventBodyTarget
    organization_id: str
    occurred_at: float
    metadata: dict[str, Any]


class AuditEventActor(TypedDict, total=False):
    #: The tenant's own actor vocabulary, e.g. `user`, `service`.
    type: str
    id: str | None


class AuditEventTarget(TypedDict, total=False):
    type: str | None
    id: str | None
    #: A human label for the target.
    name: str | None


class _AuditEventRequired(TypedDict):
    object: Literal["audit_event"]
    id: str
    actor: AuditEventActor
    #: The tenant's own action string, e.g. `invoice.sent`.
    action: str
    target: AuditEventTarget
    #: When the event happened in the tenant's system (epoch ms).
    occurred_at: int
    #: Arbitrary non-secret structured context the tenant attached.
    metadata: Any
    #: When Atlas received the event (epoch ms).
    created_at: int


class AuditEvent(_AuditEventRequired, total=False):
    #: The org this event is scoped to, if any.
    organization_id: str | None


class AuditEventDeleteResult(TypedDict):
    object: Literal["audit_events.bulk_delete"]
    #: How many events were removed.
    deleted: int


class CreateBatchAuditEventBody(TypedDict, total=False):
    events: list[CreateAuditEventBody]


#: The billing providers a plan or subscription can live on.
BillingProviderName = Literal["stripe", "polar", "dodo", "creem", "chargebee", "autumn", "commet"]


class _CreateBillingPlanBodyRequired(TypedDict):
    name: str
    #: Unique per instance; becomes the `pla` session claim.
    slug: str


class CreateBillingPlanBody(_CreateBillingPlanBodyRequired, total=False):
    #: The recurring Stripe price.
    stripe_price_id: str | None
    audience: Literal["user", "org"]
    interval: Literal["month", "year"]
    amount: str | None
    currency: str
    features: list[str]
    #: Numeric limits, e.g. {"max_devices":5}.
    limits: dict[str, Any]
    active: bool
    pricing_model: Literal["flat", "per_seat", "metered"]
    trial_days: int | None
    #: The billing provider the plan sells through (default ``stripe``).
    provider: BillingProviderName
    #: The plan's price at the provider (the neutral alias of ``stripe_price_id``).
    provider_price_id: str
    #: The yearly price at the provider, to offer the plan annually too.
    annual_price_id: str | None
    annual_amount: str | None
    #: ``base`` (default): the subject's main plan. ``addon``: bought alongside it.
    kind: Literal["base", "addon"]
    #: Autumn plans: one of the plan's features; its usage follows the org's member count.
    seat_feature_id: str | None


class BillingPlanCreateResult(TypedDict, total=False):
    object: Literal["billing_plan"]
    id: str
    name: str
    slug: str
    stripe_price_id: str | None
    #: true when the plan has no Stripe price.
    free: bool
    audience: str
    features: list[str]
    limits: dict[str, Any]
    active: bool


class _BillingPlanRequired(TypedDict):
    object: Literal["billing_plan"]
    id: str
    name: str
    slug: str
    stripe_price_id: str | None
    #: true when the plan has no Stripe price.
    free: bool
    currency: str
    features: list[str]
    audience: Literal["user", "org"]
    active: bool
    pricing_model: Literal["flat", "per_seat", "metered"]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class BillingPlan(_BillingPlanRequired, total=False):
    interval: Literal["month", "year"]
    amount: str | None
    #: Numeric limits this plan grants, e.g. {"max_devices":5}.
    limits: dict[str, Any]
    trial_days: int | None
    stripe_meter_id: str | None
    usage_unit: str | None
    provider: BillingProviderName
    provider_price_id: str | None
    annual_price_id: str | None
    annual_amount: str | None
    #: ``base``: the subject's main plan. ``addon``: bought alongside it; several may be live.
    kind: Literal["base", "addon"]
    #: Autumn plans: the feature whose usage tracks the org's member count.
    seat_feature_id: str | None


class UpdateBillingPlanBody(TypedDict, total=False):
    name: str
    slug: str
    stripe_price_id: str
    interval: str
    amount: str
    currency: str
    features: Any
    limits: Any
    audience: str
    active: bool
    pricing_model: str
    trial_days: float | None
    stripe_meter_id: str | None
    usage_unit: str | None
    #: The billing provider the plan sells through (default ``stripe``).
    provider: BillingProviderName
    #: The plan's price at the provider (the neutral alias of ``stripe_price_id``).
    provider_price_id: str
    #: The yearly price at the provider, to offer the plan annually too.
    annual_price_id: str | None
    annual_amount: str | None
    #: ``base`` or ``addon`` (refused once the plan has subscriptions).
    kind: Literal["base", "addon"]
    #: Autumn seat feature; ``None`` clears it.
    seat_feature_id: str | None


class BillingSeats(TypedDict):
    object: Literal["billing_seats"]
    subject_type: str
    subject_id: str
    quantity: int


class ImportSubscriptionBody(TypedDict, total=False):
    subject_type: Any
    subject_id: Any
    stripe_subscription_id: Any
    stripe_customer_id: Any
    plan_id: Any


class _SubscriptionRequired(TypedDict):
    object: Literal["billing_subscription"]
    id: str
    subject_type: Literal["user", "org"]
    subject_id: str
    plan_id: str
    status: str
    stripe_subscription_id: str | None
    stripe_customer_id: str | None
    current_period_end: int | None
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class Subscription(_SubscriptionRequired, total=False):
    provider: BillingProviderName
    provider_subscription_id: str | None
    provider_customer_id: str | None
    #: ``instance`` (your own provider account) or ``platform`` (a legacy subscription on
    #: the shared account: mirrored, not manageable).
    account: Literal["instance", "platform"]
    interval: Literal["month", "year"] | None
    quantity: int | None
    #: ``True`` while a cancellation is scheduled for the period end.
    cancel_at_period_end: bool
    scheduled_plan_id: str | None
    scheduled_interval: str | None
    scheduled_change_at: int | None
    trial_end: int | None
    canceled_at: int | None
    #: On a change: ``True`` when the switch waits for the period end.
    scheduled: bool
    #: What an entitlement provider (Autumn, Commet) reports this subscription grants.
    entitlements: BillingEntitlements | None


class BillingEntitlements(TypedDict):
    features: list[str]
    limits: dict[str, float]


class BillingSettings(TypedDict):
    """How numeric limits merge when a subject holds several entitling subscriptions."""

    object: Literal["billing_settings"]
    default_limit_merge: Literal["max", "sum"]
    limit_merge: dict[str, Literal["max", "sum"]]


class UpdateBillingSettingsBody(TypedDict, total=False):
    default_limit_merge: Literal["max", "sum"]
    #: Limit key → ``max`` | ``sum``; replaces the stored map.
    limit_merge: dict[str, Literal["max", "sum"]]


class _CheckBillingFeatureBodyRequired(TypedDict):
    subject_type: Literal["user", "org"]
    subject_id: str
    feature: str


class CheckBillingFeatureBody(_CheckBillingFeatureBodyRequired, total=False):
    #: Units about to be used (default 1).
    required: float


class BillingFeatureCheck(TypedDict):
    """``source`` is ``provider`` (asked live of Autumn/Commet) or ``atlas`` (from the
    resolved entitlement and this period's usage)."""

    object: Literal["billing_feature_check"]
    feature: str
    allowed: bool
    source: Literal["provider", "atlas"]
    provider: str | None
    remaining: float | None
    granted: float | None
    usage: float | None
    unlimited: bool


class ChangeSubscriptionBody(TypedDict, total=False):
    plan_id: str
    interval: Literal["month", "year"]
    #: Switch at the end of the current period instead of now (prorated).
    schedule_at_period_end: bool


class BillingProvider(TypedDict, total=False):
    """One billing provider's settings. Secrets are never returned: ``secrets_set``
    reports which are stored; ``webhook_url`` is the endpoint to register with the
    provider."""

    object: Literal["billing_provider"]
    provider: BillingProviderName
    environment: Literal["live", "test"]
    status: str
    config: dict[str, str]
    secrets_set: dict[str, bool]
    webhook_url: str
    capabilities: dict[str, Any] | None
    last_verified_at: int | None
    last_webhook_at: int | None
    updated_at: int


class SetBillingProviderBody(TypedDict, total=False):
    """Merged onto what is stored. ``config`` keys: Stripe ``secret_key``,
    ``webhook_secret``, ``publishable_key``; Polar ``access_token``, ``webhook_secret``;
    Dodo and Creem ``api_key``, ``webhook_secret``; Chargebee ``api_key``, ``site``,
    ``webhook_username`` + ``webhook_password``; Autumn ``secret_key``, ``webhook_secret``;
    Commet ``api_key``, ``webhook_secret``, optional ``seat_feature_code``."""

    environment: Literal["live", "test"]
    config: dict[str, str]


class BillingProviderTest(TypedDict, total=False):
    object: Literal["billing_provider_test"]
    provider: str
    ok: bool
    error: str | None
    account: str | None


class RecordUsageBody(TypedDict, total=False):
    subject_type: str
    subject_id: str
    quantity: float
    idempotency_key: str
    #: Count against this provider feature (an Autumn feature id / Commet feature code).
    feature: str
    #: Attribute to this subscription when the subject holds several.
    subscription_id: str


class BillingUsage(TypedDict):
    object: Literal["billing_usage"]
    recorded: bool
    metered: bool
    total: float


class CreateBotLabelBody(TypedDict, total=False):
    subject_type: str
    subject_id: str
    label: str
    confidence: float
    note: str


class _BotLabelRequired(TypedDict):
    object: Literal["bot_label"]
    id: str
    subject_type: str
    subject_id: str
    label: str
    source: str
    #: Created (epoch ms).
    created_at: int


class BotLabel(_BotLabelRequired, total=False):
    confidence: float
    note: str | None
    labeled_by: str | None


class Branding(TypedDict):
    """Branding config; flat fields plus a `resolved` bag are spread in."""

    object: Literal["branding"]
    resolved: dict[str, Any]


class BrandingAudience(TypedDict, total=False):
    """The hosted-page branding for one audience hint (``branding.audiences[hint]``).

    Write it with ``branding.update({"audiences": {"partners": {...}}})``; ``None`` for a hint
    deletes it, ``"audiences": None`` removes them all. Start a hosted sign-in with
    ``audience_hint=<hint>`` to use it. ``resolved["audiences"]`` echoes what the page reads.
    """

    #: Replaces the card heading (up to 120 characters).
    heading: str
    #: Replaces the line under the heading (up to 240 characters).
    subheading: str
    #: Replaces the logo (https).
    logoUrl: str
    #: Replaces the primary colour (hex, rgb() or a CSS colour name).
    primaryColor: str


class HostedPagePreview(TypedDict):
    object: Literal["hosted_page_preview"]
    html: str


class VerifyCaptchaBody(TypedDict, total=False):
    token: str
    action: str
    remote_ip: str


class _CaptchaVerificationRequired(TypedDict):
    object: Literal["captcha_verification"]
    success: bool
    action: str | None
    provider: str


class CaptchaVerification(_CaptchaVerificationRequired, total=False):
    score: float
    verdict: Literal["pass", "fail", "low_score", "edge"]
    challenge_ts: str
    meta: dict[str, Any]


class _CreateConnectorBodyRequired(TypedDict):
    slug: str
    display_name: str


class CreateConnectorBody(_CreateConnectorBodyRequired, total=False):
    logo_url: str
    tagline: str
    description: str
    category: str
    tags: list[str]
    website_url: str
    docs_url: str
    support_url: str
    screenshots: list[Any]
    setup_guide: str
    protocol: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    issuer: str
    default_scopes: list[str]
    api_scopes: list[Any]
    credential_fields: list[Any]
    authorization_params: dict[str, Any]
    quirks: dict[str, Any]
    share_modes: list[Literal["prefill", "full_shared", "full_idp"]]
    idp_instance_id: str
    idp_issuer: str
    idp_auto_register: bool


class _ConnectorRequired(TypedDict):
    object: Literal["connector"]
    id: str
    slug: str
    display_name: str
    category: str
    tags: list[Any]
    protocol: str
    default_scopes: list[str]
    share_modes: list[Literal["prefill", "full_shared", "full_idp"]]
    shared_revoked: bool
    idp_auto_register: bool
    status: Literal["draft", "published", "unlisted", "banned"]
    verified: bool
    featured: bool
    install_count: int
    view_count: int
    rating_avg: float
    rating_count: int
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class Connector(_ConnectorRequired, total=False):
    logo_url: str | None
    tagline: str | None
    description: str | None
    website_url: str | None
    docs_url: str | None
    support_url: str | None
    setup_guide: str | None
    authorization_endpoint: str | None
    token_endpoint: str | None
    userinfo_endpoint: str | None
    issuer: str | None
    api_scopes: list[Any]
    credential_fields: list[Any]
    shared_client_id: str | None
    idp_issuer: str | None


class UpdateConnectorBody(TypedDict, total=False):
    slug: str
    display_name: str
    logo_url: str
    tagline: str
    description: str
    category: str
    tags: list[str]
    website_url: str
    docs_url: str
    support_url: str
    screenshots: list[Any]
    setup_guide: str
    protocol: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    issuer: str
    default_scopes: list[str]
    api_scopes: list[Any]
    credential_fields: list[Any]
    authorization_params: dict[str, Any]
    quirks: dict[str, Any]
    share_modes: list[Literal["prefill", "full_shared", "full_idp"]]
    idp_instance_id: str
    idp_issuer: str
    idp_auto_register: bool


class SetConnectorSharedCredentialsBody(TypedDict, total=False):
    client_id: str
    client_secret: str
    revoke: bool


class InstallConnectorBody(TypedDict, total=False):
    share_mode: str
    client_id: str
    client_secret: str
    scopes: list[str]


class _ConnectorInstallRequired(TypedDict):
    object: Literal["connector_install"]
    connector: str
    share_mode: str


class ConnectorInstall(_ConnectorInstallRequired, total=False):
    provider_key: str
    needs_credentials: bool


class ReviewConnectorBody(TypedDict, total=False):
    rating: float
    body: str


class ConnectorReview(TypedDict):
    object: Literal["connector_review"]
    connector: str
    rating: int


class _CreateDataSubjectRequestBodyRequired(TypedDict):
    type: Literal["export", "erasure"]


class CreateDataSubjectRequestBody(_CreateDataSubjectRequestBodyRequired, total=False):
    """Identify the subject by user_id OR subject_email (user_id wins if both are given)."""

    #: The subject's Atlas id.
    user_id: str
    #: The subject's email address (verified, else unverified).
    subject_email: str
    reason: str


class _DataSubjectRequestRequired(TypedDict):
    object: Literal["data_subject_request"]
    id: str
    type: Literal["export", "erasure"]
    #: A deferred erasure is `scheduled` (held in its grace window with a `scheduled_for`/`eta`),
    #: distinguishing it from a `pending` request that runs on the next worker pass.
    status: Literal["pending", "scheduled", "processing", "completed", "rejected", "cancelled"]
    user_id: str
    requested_by_type: str
    #: Requested (epoch ms).
    requested_at: int
    #: Last updated (epoch ms).
    updated_at: int


class DataSubjectRequest(_DataSubjectRequestRequired, total=False):
    requested_by_id: str | None
    reason: str | None
    #: Erasure only: epoch ms when the grace/cancellation window lapses and the worker fulfils
    #: it.
    scheduled_for: int | None
    #: Estimated completion (epoch ms).
    eta: int | None
    completed_at: int | None
    result: Any


class RejectDataSubjectRequestBody(TypedDict, total=False):
    reason: str


class DesignAsset(TypedDict):
    """An uploaded design image."""

    object: Literal["design_asset"]
    #: dasset_...
    asset_id: str
    kind: Literal["background", "logo"]
    #: Where Atlas serves the stored image.
    url: str
    width: int
    height: int
    #: #rrggbb for an opaque image, else null.
    dominant_color: str | None
    #: Size of the stored image.
    bytes: int
    created_at: str


class DesignAssetDeleteResult(TypedDict):
    object: Literal["design_asset"]
    asset_id: str
    deleted: Literal[True]


class DesignWarning(TypedDict):
    """A contrast warning (advice, never a refusal): a text/background pair below WCAG AA
    4.5:1.
    """

    code: Literal["low_contrast"]
    mode: Literal["light", "dark"]
    pair: list[str]
    ratio: float
    required: float
    #: The setting to change, e.g. palette.primaryInk.
    path: str
    message: str


class _DesignSettingsRequired(TypedDict):
    object: Literal["design", "organization_design"]
    #: The stored overrides ({} when nothing is stored).
    design: AtlasDesign
    resolved: ResolvedDesign
    warnings: list[DesignWarning]
    #: True when nothing is stored and the page is drawn from the older branding settings.
    legacy: bool


class DesignSettings(_DesignSettingsRequired, total=False):
    #: Organization designs only.
    organization_id: str
    #: When legacy is true: the design derived from the older branding settings (a good starting
    #: point for an editor).
    legacy_design: AtlasDesign | None


class ReplaceDesignBody(TypedDict):
    design: AtlasDesign


class AtlasDesignPatchPalette(TypedDict, total=False):
    primary: str | None
    primaryInk: str | None
    accent: str | None
    background: str | None
    surface: str | None
    text: str | None
    muted: str | None
    border: str | None
    danger: str | None
    success: str | None
    inputBackground: str | None
    inputText: str | None


class AtlasDesignPatchTypography(TypedDict, total=False):
    font: (
        Literal[
            "system",
            "system-serif",
            "system-mono",
            "inter",
            "roboto",
            "open-sans",
            "lato",
            "montserrat",
            "poppins",
            "nunito",
            "work-sans",
            "dm-sans",
            "manrope",
            "source-serif",
            "merriweather",
            "playfair-display",
            "jetbrains-mono",
            "ibm-plex-mono",
        ]
        | None
    )
    headingFont: (
        Literal[
            "system",
            "system-serif",
            "system-mono",
            "inter",
            "roboto",
            "open-sans",
            "lato",
            "montserrat",
            "poppins",
            "nunito",
            "work-sans",
            "dm-sans",
            "manrope",
            "source-serif",
            "merriweather",
            "playfair-display",
            "jetbrains-mono",
            "ibm-plex-mono",
        ]
        | None
    )
    baseSize: int | None
    headingWeight: int | None
    bodyWeight: int | None
    letterCase: Literal["none", "uppercase"] | None
    scale: (
        Literal[
            "minor-second",
            "major-second",
            "minor-third",
            "major-third",
            "perfect-fourth",
            "augmented-fourth",
            "perfect-fifth",
            "golden",
            "minor-seventh",
            "octave",
        ]
        | None
    )


class AtlasDesignPatchShape(TypedDict, total=False):
    radius: int | None
    controlRadius: int | None
    borderWidth: int | None


class AtlasDesignPatchElevation(TypedDict, total=False):
    cardShadow: Literal["none", "sm", "md", "lg", "xl"] | None


class AtlasDesignPatchSpacing(TypedDict, total=False):
    density: Literal["compact", "comfortable", "spacious"] | None


class AtlasDesignPatchCard(TypedDict, total=False):
    style: Literal["solid", "glass", "outline", "none"] | None
    blur: int | None
    width: Literal["narrow", "normal", "wide"] | None


class AtlasDesignPatchLayout(TypedDict, total=False):
    position: Literal["center", "left", "right", "split"] | None
    splitImageSide: Literal["left", "right"] | None
    logoPlacement: Literal["card", "page", "hidden"] | None
    logoSize: Literal["sm", "md", "lg"] | None


class AtlasDesignPatchButtons(TypedDict, total=False):
    style: Literal["solid", "outline", "soft", "gradient"] | None
    socialLayout: Literal["list", "grid", "icons"] | None


class AtlasDesignPatchInputs(TypedDict, total=False):
    style: Literal["outline", "filled", "underline"] | None


class AtlasDesignPatchBackgroundGradient(TypedDict, total=False):
    type: Literal["linear", "radial"] | None
    angle: int | None
    stops: list[AtlasDesignBackgroundGradientStopsItem] | None


class AtlasDesignPatchBackgroundImageOverlay(TypedDict, total=False):
    color: str | None
    opacity: float | None


class AtlasDesignPatchBackgroundImage(TypedDict, total=False):
    assetId: str | None
    fit: Literal["cover", "contain"] | None
    position: (
        Literal[
            "top-left",
            "top",
            "top-right",
            "left",
            "center",
            "right",
            "bottom-left",
            "bottom",
            "bottom-right",
        ]
        | None
    )
    overlay: AtlasDesignPatchBackgroundImageOverlay | None
    blur: int | None


class AtlasDesignPatchBackground(TypedDict, total=False):
    color: str | None
    gradient: AtlasDesignPatchBackgroundGradient | None
    image: AtlasDesignPatchBackgroundImage | None
    pattern: Literal["none", "dots", "grid", "noise"] | None


class AtlasDesignPatchLogo(TypedDict, total=False):
    assetId: str | None
    darkAssetId: str | None


class AtlasDesignPatch(TypedDict, total=False):
    """A partial design update: nested objects merge, arrays (gradient stops) and values
    replace, and null removes a setting (falling back to the preset).
    """

    version: Literal[1] | None
    preset: (
        Literal[
            "minimal",
            "atlas",
            "glass",
            "midnight",
            "editorial",
            "terminal",
            "sunrise",
            "forest",
            "grape",
            "slate",
            "split-photo",
            "bold",
        ]
        | None
    )
    colorScheme: Literal["auto", "light", "dark"] | None
    palette: AtlasDesignPatchPalette | None
    paletteDark: AtlasDesignPatchPalette | None
    typography: AtlasDesignPatchTypography | None
    shape: AtlasDesignPatchShape | None
    elevation: AtlasDesignPatchElevation | None
    spacing: AtlasDesignPatchSpacing | None
    card: AtlasDesignPatchCard | None
    layout: AtlasDesignPatchLayout | None
    buttons: AtlasDesignPatchButtons | None
    inputs: AtlasDesignPatchInputs | None
    background: AtlasDesignPatchBackground | None
    backgroundDark: AtlasDesignPatchBackground | None
    logo: AtlasDesignPatchLogo | None


class UpdateDesignBody(TypedDict):
    design: AtlasDesignPatch


class PreviewDesignBody(TypedDict):
    design: AtlasDesign


class DesignPreview(TypedDict):
    object: Literal["design_preview"]
    #: The selector the CSS is scoped to: ".atlas-root".
    scope: str
    #: CSS custom properties (--atlas-*) for the scope, including light/dark blocks.
    css: str
    #: Attributes to set on the scoped element (data-atlas-layout, data-atlas-card, …).
    data_attributes: dict[str, str]
    #: Absolute URLs of the self-hosted font stylesheets to link.
    font_stylesheets: list[str]
    resolved: ResolvedDesign
    warnings: list[DesignWarning]
    #: The sign-in page rendered with the draft design (inert: for a sandboxed preview frame).
    html: str


LoginReadinessChecksItem = TypedDict(
    "LoginReadinessChecksItem",
    {"name": "str", "pass": "bool", "applies": "bool", "observed": "Any", "detail": "str"},
    total=False,
)
"""One check. ``applies`` is ``False`` when it does not matter for the assumed integration
(it then never makes ``ready`` false)."""


class LoginReadinessIntegration(TypedDict):
    """The integration the checks assumed for the origin, and why."""

    #: ``redirect``: hosted-redirect OIDC, so the ``cors`` and ``session_cookie`` checks do
    #: not apply.
    assumed: Literal["redirect", "embedded"]
    source: Literal["declared", "embedded_traffic", "redirect_clients", "default"]
    #: A plain sentence saying why.
    reason: str


class _LoginReadinessRequired(TypedDict):
    object: Literal["login_readiness"]
    origin: str
    live: bool
    ready: bool
    checks: list[LoginReadinessChecksItem]


class LoginReadiness(_LoginReadinessRequired, total=False):
    data_region: str | None
    integration: LoginReadinessIntegration


class RequestInspectionFindingsItem(TypedDict, total=False):
    check: str
    blocks: bool
    observed: Any
    detail: str


class RequestInspection(TypedDict):
    object: Literal["request_inspection"]
    origin: str
    method: str
    path: str
    would_be_rejected: bool
    findings: list[RequestInspectionFindingsItem]


class SetEmailTemplateBody(TypedDict, total=False):
    subject: str
    text: str


class EmailTemplateSetResultOverride(TypedDict, total=False):
    subject: str | None
    text: str | None


class EmailTemplateSetResult(TypedDict):
    object: Literal["email_template"]
    name: str
    override: EmailTemplateSetResultOverride
    customised: Literal[True]


class EmailTemplateResetResult(TypedDict):
    object: Literal["email_template"]
    name: str
    override: None
    customised: Literal[False]


class PreviewEmailTemplateBody(TypedDict, total=False):
    subject: str
    text: str


class EmailPreview(TypedDict):
    object: Literal["email_preview"]
    template: str
    valid: bool
    problem: str | None
    html: str | None
    variables: dict[str, str]


class _CreateEntitlementOverrideBodyRequired(TypedDict):
    subject_type: Literal["user", "org"]
    subject_id: str


class CreateEntitlementOverrideBody(_CreateEntitlementOverrideBodyRequired, total=False):
    #: Plan slug to pin, or null to override features/limits only.
    plan: str | None
    #: Replaces (not adds to) the resolved feature set.
    features: list[str] | None
    #: Numeric limits, e.g. {"max_devices":50}.
    limits: dict[str, Any] | None
    #: Epoch ms when the override lapses; omit/null for open-ended.
    expires_at: int | None


class EntitlementOverride(TypedDict):
    """A sales-led entitlement override (P1-6): a non-Stripe grant pinning a plan / features /
    limits onto a user or org.
    """

    object: Literal["entitlement_override"]
    id: str
    subject_type: Literal["user", "org"]
    subject_id: str
    #: Plan slug to pin, or null to override features/limits only.
    plan: str | None
    features: list[str] | None
    limits: dict[str, Any] | None
    #: Epoch ms when the override lapses, or null for open-ended.
    expires_at: int | None
    created_by: str | None
    #: Created (epoch ms).
    created_at: int


class CreateFgaStoreBody(TypedDict, total=False):
    name: Any


class FgaStore(TypedDict):
    object: Literal["fga.store"]
    id: str
    name: str
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class CreateFgaAuthorizationModelBody(TypedDict, total=False):
    type_definitions: Any
    schema_version: Any
    dsl: Any


class _FgaAuthorizationModelRequired(TypedDict):
    object: Literal["fga.authorization_model"]
    id: str
    store_id: str
    schema_version: str
    #: Created (epoch ms).
    created_at: int


class FgaAuthorizationModel(_FgaAuthorizationModelRequired, total=False):
    """`model` is present on create + single-get, omitted from list responses."""

    model: dict[str, Any]


class BatchCheckFgaBody(TypedDict, total=False):
    checks: Any
    authorization_model_id: Any


class FgaBatchCheckResultItem(TypedDict):
    correlation_id: str
    allowed: bool


class FgaBatchCheck(TypedDict):
    object: Literal["fga.batch_check"]
    authorization_model_id: str
    result: list[FgaBatchCheckResultItem]


class CheckFgaBody(TypedDict, total=False):
    user: Any
    relation: Any
    object: Any
    authorization_model_id: Any
    contextual_tuples: Any


class FgaCheck(TypedDict):
    object: Literal["fga.check"]
    allowed: bool
    authorization_model_id: str


class ExpandFgaBody(TypedDict, total=False):
    object: Any
    relation: Any
    authorization_model_id: Any


class FgaExpand(TypedDict):
    object: Literal["fga.expand"]
    tree: dict[str, Any]
    authorization_model_id: str


class ListObjectsFgaBody(TypedDict, total=False):
    user: Any
    relation: Any
    type: Any
    authorization_model_id: Any
    contextual_tuples: Any


class FgaListObjects(TypedDict):
    object: Literal["fga.list_objects"]
    objects: list[str]
    authorization_model_id: str


class ReadFgaBody(TypedDict, total=False):
    user: Any
    relation: Any
    object: Any


class WriteFgaBody(TypedDict, total=False):
    writes: Any
    deletes: Any


class FgaWriteResult(TypedDict):
    object: Literal["fga.write_result"]
    writes: int
    deletes: int


class OpenFgaStoreListStoresItem(TypedDict):
    id: str
    name: str
    created_at: str
    updated_at: str


class OpenFgaStoreList(TypedDict):
    stores: list[OpenFgaStoreListStoresItem]


class CreateOpenFgaStoreBody(TypedDict):
    name: str


class OpenFgaStore(TypedDict, total=False):
    id: str
    name: str
    created_at: str
    updated_at: str


class OpenFgaAuthorizationModelListAuthorizationModelsItem(TypedDict):
    id: str
    schema_version: str


class OpenFgaAuthorizationModelList(TypedDict):
    authorization_models: list[OpenFgaAuthorizationModelListAuthorizationModelsItem]


class CreateOpenFgaAuthorizationModelBody(TypedDict, total=False):
    type_definitions: list[dict[str, Any]]
    schema_version: str
    dsl: str


class OpenFgaWriteModelResult(TypedDict):
    authorization_model_id: str


class OpenFgaAuthorizationModelResultAuthorizationModel(TypedDict, total=False):
    id: str
    schema_version: str
    type_definitions: list[dict[str, Any]]


class OpenFgaAuthorizationModelResult(TypedDict, total=False):
    authorization_model: OpenFgaAuthorizationModelResultAuthorizationModel


class BatchCheckOpenFgaBodyChecksItemTupleKey(TypedDict, total=False):
    user: str
    relation: str
    object: str


class BatchCheckOpenFgaBodyChecksItem(TypedDict, total=False):
    tuple_key: BatchCheckOpenFgaBodyChecksItemTupleKey
    correlation_id: str
    contextual_tuples: dict[str, Any]


class _BatchCheckOpenFgaBodyRequired(TypedDict):
    checks: list[BatchCheckOpenFgaBodyChecksItem]


class BatchCheckOpenFgaBody(_BatchCheckOpenFgaBodyRequired, total=False):
    authorization_model_id: str


class OpenFgaBatchCheckResultResultValue(TypedDict, total=False):
    allowed: bool


class OpenFgaBatchCheckResult(TypedDict, total=False):
    result: dict[str, OpenFgaBatchCheckResultResultValue]


class CheckOpenFgaBodyTupleKey(TypedDict):
    #: e.g. user:alice
    user: str
    #: e.g. viewer
    relation: str
    #: e.g. document:roadmap
    object: str


class _CheckOpenFgaBodyRequired(TypedDict):
    tuple_key: CheckOpenFgaBodyTupleKey


class CheckOpenFgaBody(_CheckOpenFgaBodyRequired, total=False):
    authorization_model_id: str
    #: OpenFGA contextual tuples.
    contextual_tuples: dict[str, Any]


class ExpandOpenFgaBodyTupleKey(TypedDict):
    object: str
    relation: str


class _ExpandOpenFgaBodyRequired(TypedDict):
    tuple_key: ExpandOpenFgaBodyTupleKey


class ExpandOpenFgaBody(_ExpandOpenFgaBodyRequired, total=False):
    authorization_model_id: str


class OpenFgaExpandResultTree(TypedDict, total=False):
    root: dict[str, Any]


class OpenFgaExpandResult(TypedDict, total=False):
    tree: OpenFgaExpandResultTree


class _ListObjectsOpenFgaBodyRequired(TypedDict):
    #: e.g. document
    type: str
    #: e.g. viewer
    relation: str
    #: e.g. user:alice
    user: str


class ListObjectsOpenFgaBody(_ListObjectsOpenFgaBodyRequired, total=False):
    authorization_model_id: str
    #: OpenFGA contextual tuples.
    contextual_tuples: dict[str, Any]


class OpenFgaListObjectsResult(TypedDict, total=False):
    objects: list[str]


class ReadOpenFgaBodyTupleKey(TypedDict, total=False):
    user: str
    relation: str
    #: A full `type:id` or a bare `type:` prefix.
    object: str


class ReadOpenFgaBody(TypedDict, total=False):
    tuple_key: ReadOpenFgaBodyTupleKey
    page_size: int
    continuation_token: str


class OpenFgaReadResultTuplesItem(TypedDict, total=False):
    key: BatchCheckOpenFgaBodyChecksItemTupleKey
    timestamp: str


class OpenFgaReadResult(TypedDict, total=False):
    tuples: list[OpenFgaReadResultTuplesItem]
    continuation_token: str


class WriteOpenFgaBodyWrites(TypedDict, total=False):
    tuple_keys: list[BatchCheckOpenFgaBodyChecksItemTupleKey]


class WriteOpenFgaBody(TypedDict, total=False):
    """OpenFGA write — `writes` adds tuples, `deletes` removes them."""

    writes: WriteOpenFgaBodyWrites
    deletes: WriteOpenFgaBodyWrites


class GrantRevokeResult(TypedDict):
    object: Literal["grant"]
    id: str
    deleted: Literal[True]
    tokens_revoked: int


class InstanceAuthConfigResolvedStrategies(TypedDict, total=False):
    """Which first-factor sign-in methods are enabled."""

    password: bool
    #: Email one-time code (passwordless).
    emailCode: bool
    #: Magic link.
    emailLink: bool
    #: WebAuthn passkeys.
    passkey: bool
    #: SMS OTP (off by default).
    phoneCode: bool
    #: Username as a login identifier.
    username: bool
    siwe: bool
    siws: bool
    siwf: bool


class InstanceAuthConfigResolvedPasswordPolicy(TypedDict, total=False):
    minLength: int
    requireUppercase: bool
    requireNumber: bool
    requireSymbol: bool
    #: Reject known-breached passwords (HIBP).
    checkBreaches: bool


class InstanceAuthConfigResolvedVerification(TypedDict, total=False):
    """Per-method code/link TTLs, lengths and resend limits."""

    emailCode: dict[str, Any]
    smsCode: dict[str, Any]
    magicLink: dict[str, Any]


class InstanceAuthConfigResolvedSession(TypedDict, total=False):
    """Session lifetime + token behaviour."""

    idleMs: int
    absoluteMs: int
    jwtTtlSeconds: int
    crossSubdomainCookies: bool
    #: Add email/name to the session JWT.
    includeEmailClaim: bool
    #: Add the eu_orgs reader claim.
    includeEndUserPoolClaim: bool


class _InstanceAuthConfigResolvedSamlIdpServiceProvidersItemRequired(TypedDict):
    #: Stable key used in the SSO URL + audit.
    id: str
    #: The SP's SAML entityId (assertion audience).
    entityId: str
    #: The SP's Assertion Consumer Service URL (https) the Response is POSTed to.
    acsUrl: str


class InstanceAuthConfigResolvedSamlIdpServiceProvidersItem(
    _InstanceAuthConfigResolvedSamlIdpServiceProvidersItemRequired, total=False
):
    #: User field for the NameID.
    nameIdField: Literal["email", "user_id"]
    #: Extra attribute statements: SAML attribute name → user field / metadata key.
    attributes: dict[str, str]


class InstanceAuthConfigResolvedSamlIdp(TypedDict, total=False):
    """Atlas AS a SAML IdP — "Sign in with Atlas" over SAML for a downstream Service Provider
    (direct SAML; no OIDC/atlas_byo needed).
    """

    #: The SPs Atlas issues signed assertions to.
    serviceProviders: list[InstanceAuthConfigResolvedSamlIdpServiceProvidersItem]


class _InstanceAuthConfigResolvedExternalJwtIssuersItemRequired(TypedDict):
    #: Stable key; the linked identity is stored under provider ext_jwt:<id>.
    id: str
    #: The expected iss claim.
    issuer: str
    #: The issuer's JWKS URL, used to verify the token signature.
    jwksUri: str
    #: The expected aud claim.
    audience: str


class InstanceAuthConfigResolvedExternalJwtIssuersItem(
    _InstanceAuthConfigResolvedExternalJwtIssuersItemRequired, total=False
):
    #: Claim to read the email from.
    emailClaim: str


class InstanceAuthConfigResolvedExternalJwt(TypedDict, total=False):
    """Trust JWTs minted by an EXTERNAL issuer as a sign-in credential (e.g. a legacy IdP or
    your own token service).
    """

    issuers: list[InstanceAuthConfigResolvedExternalJwtIssuersItem]


class InstanceAuthConfigResolved(TypedDict, total=False):
    """Instance auth configuration."""

    #: Which first-factor sign-in methods are enabled.
    strategies: InstanceAuthConfigResolvedStrategies
    passwordPolicy: InstanceAuthConfigResolvedPasswordPolicy
    #: Per-method code/link TTLs, lengths and resend limits.
    verification: InstanceAuthConfigResolvedVerification
    #: Session lifetime + token behaviour.
    session: InstanceAuthConfigResolvedSession
    mfaPolicy: Literal["off", "optional", "required"]
    #: public: anyone may sign up.
    signUpMode: Literal["public", "waitlist", "restricted"]
    #: Whether a password sign-up must prove the address before it completes. When false the
    #: address stays unverified until the user proves it later.
    requireEmailVerification: bool
    #: DANGEROUS. Report addresses that skipped proof as verified again (the old behaviour).
    dangerouslyReportSkippedEmailsAsVerified: bool
    #: Refuse unknown body fields on every Backend API write (422 ``UNKNOWN_FIELD``). True for
    #: instances created from 2026-10 on.
    strictRequestBodies: bool
    #: The declared integration per allowed origin (``redirect`` | ``embedded``). Set it with
    #: ``allowed_origins`` entries ``{"origin", "integration"}``.
    originIntegrations: dict[str, Literal["redirect", "embedded"]]
    #: Per-audience hosted-page branding (``{"audiences": {hint: BrandingAudience | None}}``).
    #: Only ``branding.audiences`` is applied on ``PATCH /v1/instance``.
    branding: dict[str, Any]
    #: Atlas AS a SAML IdP — "Sign in with Atlas" over SAML for a downstream Service Provider
    #: (direct SAML; no OIDC/atlas_byo needed).
    samlIdp: InstanceAuthConfigResolvedSamlIdp
    #: Trust JWTs minted by an EXTERNAL issuer as a sign-in credential (e.g. a legacy IdP or your
    #: own token service).
    externalJwt: InstanceAuthConfigResolvedExternalJwt


class Instance(TypedDict, total=False):
    object: Literal["instance"]
    id: str
    environment: Literal["development", "production"]
    publishable_key: str
    frontend_api_host: str | None
    #: The ``iss`` the session tokens carry. Changes when a custom domain goes active, so
    #: read it rather than hard-coding it.
    issuer: str
    #: The OpenID discovery document whose ``issuer`` equals ``issuer``.
    discovery_url: str
    #: The JWKS holding the instance's signing keys.
    jwks_uri: str
    allowed_origins: list[str]
    #: The declared integration per allowed origin (``redirect`` | ``embedded``).
    allowed_origin_integrations: dict[str, Literal["redirect", "embedded"]]
    #: The raw stored patch (often {} = defaults).
    auth_config: dict[str, Any]
    #: Instance auth configuration.
    auth_config_resolved: InstanceAuthConfigResolved
    #: Created (epoch ms).
    created_at: int


class _AllowedOriginEntryRequired(TypedDict):
    origin: str


class AllowedOriginEntry(_AllowedOriginEntryRequired, total=False):
    """An ``allowed_origins`` entry that also says how the origin signs in."""

    #: ``redirect`` (hosted-redirect OIDC), ``embedded`` (the sign-in components run on the
    #: origin), or ``auto`` / ``None`` (clear the hint; Atlas infers it).
    integration: Literal["redirect", "embedded", "auto"] | None


#: An origin string (keeps the origin's current hint), or an :class:`AllowedOriginEntry`.
AllowedOriginInput = Union[str, AllowedOriginEntry]


class UpdateInstanceBody(TypedDict, total=False):
    #: Bare origins, no wildcards. Strings or ``{"origin", "integration"}`` entries.
    allowed_origins: list[AllowedOriginInput]
    #: Instance auth configuration.
    auth_config: InstanceAuthConfigResolved


class SetCaptchaSecretBody(TypedDict, total=False):
    secret: str
    #: The captcha provider the secret belongs to (defaults to the configured one).
    #: Captcha is bring-your-own-keys: store the secret before turning captcha on.
    provider: str


class CaptchaSecret(TypedDict):
    object: Literal["captcha_secret"]
    provider: str
    set: Literal[True]


class _InstanceDeleteCaptchaSecretResultBase(TypedDict):
    object: Literal["captcha_secret"]
    provider: str
    deleted: Literal[True]


class InstanceDeleteCaptchaSecretResult(_InstanceDeleteCaptchaSecretResultBase, total=False):
    #: The flows a ``force=True`` delete turned off (absent when none were using it).
    flows_turned_off: list[str]


#: A built-in settings-link preset: it adds the attribute the named CMP listens on to
#: reopen its preferences (``"custom"`` adds none). Responses carry the preset as a
#: plain ``str`` so a preset added later still decodes.
CookieConsentSettingsLinkPreset = Literal["cookiemunch", "cookiebot", "onetrust", "custom"]


class _CookieConsentSettingsLinkInputRequired(TypedDict):
    #: The link text, 1-60 characters.
    label: str


class CookieConsentSettingsLinkInput(_CookieConsentSettingsLinkInputRequired, total=False):
    """A "cookie settings" link on the hosted pages that reopens the CMP preferences.

    Needs a ``preset`` or at least one attribute (400 otherwise).
    """

    preset: CookieConsentSettingsLinkPreset | None
    #: Extra attributes for the link: ``data-*``, ``aria-*``, ``id``, ``class`` and
    #: ``href`` (https or a ``#fragment``). At most 10; values up to 200 characters.
    attributes: dict[str, str]


class CookieConsentSettingsLink(TypedDict):
    """The configured "cookie settings" link."""

    label: str
    #: One of :data:`CookieConsentSettingsLinkPreset`, or ``None``; kept a ``str`` so
    #: unknown presets still decode.
    preset: str | None
    #: The attributes you set.
    attributes: dict[str, str]
    #: The attributes the rendered link carries: yours plus the preset's trigger.
    rendered_attributes: dict[str, str]


class DeclaredCookie(TypedDict):
    """A cookie or browser-storage key Atlas writes (all strictly necessary)."""

    #: The exact name, or ``None`` when ``pattern`` describes a family of keys.
    name: str | None
    #: A ``*`` wildcard for keys with an id suffix, e.g. ``atlasid:*``.
    pattern: str | None
    store: Literal["cookie", "localStorage", "sessionStorage", "indexedDB"]
    domain: str
    #: Seconds; ``None`` = browser session (cookie) or until cleared (storage).
    lifetime_seconds: int | None
    lifetime: str
    http_only: bool
    category: Literal["necessary"]
    purpose: str
    written_when: str
    set_by: Literal["atlas_frontend_api", "atlas_sdk"]


class _CookieConsentRequired(TypedDict):
    object: Literal["cookie_consent"]
    enabled: bool


class CookieConsent(_CookieConsentRequired, total=False):
    """The consent-management platform (CMP) injected into the hosted pages."""

    #: The CMP script URL (https).
    script_url: str
    script_id: str | None
    site_id: str | None
    blocking_mode: str | None
    extra_origins: list[str]
    #: The "cookie settings" link, or ``None`` when there is none.
    settings_link: CookieConsentSettingsLink | None
    #: ``page`` (default): the CMP tag carries the page language; ``browser``: no attribute.
    culture: Literal["page", "browser"]
    #: Every cookie and browser-storage key Atlas writes for this instance.
    declared_cookies: list[DeclaredCookie]


class _SetCookieConsentBodyRequired(TypedDict):
    #: Your CMP script URL.
    script_url: str


class SetCookieConsentBody(_SetCookieConsentBodyRequired, total=False):
    #: The <script id> some CMPs need.
    script_id: str | None
    #: Your CMP site id (sent as data-cbid).
    site_id: str | None
    #: The CMP prior-blocking mode, e.g. "auto" (sent as data-blockingmode).
    blocking_mode: str | None
    #: Other https URLs the CMP loads from or calls; each origin is added to the page CSP.
    extra_origins: list[str]
    #: A "cookie settings" link that reopens the CMP preferences; ``None`` or omitted
    #: means no link.
    settings_link: CookieConsentSettingsLinkInput | None
    #: ``page`` (default) or ``browser``.
    culture: Literal["page", "browser"] | None


class SetKerberosSecretBody(TypedDict, total=False):
    secret: str


class KerberosSecret(TypedDict):
    object: Literal["kerberos_secret"]
    set: Literal[True]


class InstanceDeleteKerberosSecretResult(TypedDict):
    object: Literal["kerberos_secret"]
    deleted: Literal[True]


class ProxySecret(TypedDict):
    """The trusted reverse proxy secret: whether one is set (never the secret itself).

    A proxy that serves the Frontend API from your own origin sends the secret in
    ``X-Atlas-Proxy-Secret`` and the browser's IP in ``X-Atlas-Client-IP``; Atlas then uses
    that IP for rate limits, lockout, risk signals, geo, audit logs and session metadata.
    """

    object: Literal["proxy_secret"]
    set: bool
    #: When the current secret was created (epoch ms), or ``None``.
    created_at: int | None
    #: After a rotation: when the replaced secret stops working (epoch ms), or ``None``.
    previous_expires_at: int | None
    secret_header: Literal["X-Atlas-Proxy-Secret"]
    client_ip_header: Literal["X-Atlas-Client-IP"]


class ProxySecretCreated(ProxySecret, SealedSecrets):
    """Create / rotate result: the secret, shown only here."""

    #: ``aps_...``. Store it in your proxy's environment; Atlas keeps only a hash.
    secret: str
    #: ``True`` when an existing secret was replaced.
    rotated: bool


class CreateProxySecretBody(TypedDict, total=False):
    #: On rotation: seconds the replaced secret keeps working. Default 86400, ``0`` stops it
    #: now, at most 604800.
    overlap_seconds: int | None


class InstanceDeleteProxySecretResult(TypedDict):
    object: Literal["proxy_secret"]
    deleted: Literal[True]


# --------------------------------------------------------------------------- #
# Referral attribution                                                         #
# --------------------------------------------------------------------------- #


class _ReferralProviderCapabilitiesRequired(TypedDict):
    signup: bool
    erase: bool
    export: bool
    partner: bool
    auto_enroll: bool
    signal: bool


class ReferralProviderCapabilities(_ReferralProviderCapabilitiesRequired, total=False):
    #: Re-keys a customer whose ``external_id`` changed after sign-up.
    alias: bool
    #: Takes user lifecycle updates (email, name, suspension).
    user: bool
    #: Answers a ping for the connection test (org, program, clock).
    ping: bool
    #: Sends referral changes made after sign-up to Atlas (two-way sync).
    inbound: bool


class ReferralProvider(TypedDict):
    """A referral provider Atlas supports."""

    #: ``webhook`` (the Atlas referral protocol), ``referalli`` (the former ``referally`` is
    #: accepted too) or another vendor
    #: adapter id.
    id: str
    name: str
    capabilities: ReferralProviderCapabilities
    #: What must be set before ``enabled`` can be true: ``endpoint_url``,
    #: ``signing_secret``, ``api_key``, ``connection_id``, ``tracking_token``.
    needs: list[str]
    default_context_cookie: str | None
    docs_url: str | None


class ReferralSecuritySettings(TypedDict, total=False):
    """Fraud and bot protection for referred sign-ups (``security`` on the settings).
    On a PATCH only the fields sent change.
    """

    #: ``always`` (default): a sign-up carrying a referral code must pass the bot
    #: challenge. ``inherit``: the instance captcha policy decides.
    challenge_referred_signups: Literal["always", "inherit"]
    #: ``flag`` (default): report with the risk. ``strip``: report as not referred.
    #: ``hold``: report nothing until the email is proven, then re-assess.
    on_high_risk: Literal["flag", "strip", "hold"]
    #: Hold every referred sign-up until the email is proven. Default ``False``.
    hold_until_email_verified: bool
    #: Referred sign-ups per code from one IP network or device per hour before a
    #: velocity signal (1-1000, default 5).
    max_referred_signups_per_ip_hour: int


class ReferralLastTest(TypedDict):
    ok: bool
    #: Epoch ms.
    at: int
    http_status: int | None
    error: str | None


class ReferralPing(TypedDict, total=False):
    """What a platform answered to a ping (the connection test, where supported)."""

    ok: bool
    #: Epoch ms.
    at: int | None
    http_status: int | None
    #: e.g. ``signature_rejected``, ``connection_paused``, ``timeout``,
    #: ``network_error``, ``ping_not_ok``.
    error_code: str | None
    error: str | None
    latency_ms: int | None
    connection_id: str | None
    program_id: str | None
    program_name: str | None
    org_name: str | None
    #: The platform connection's own auto-enrol setting.
    auto_enroll_users: bool | None
    #: The platform's clock, as it reported it.
    server_time: str | None
    #: The platform's clock minus Atlas's, in ms. Signed calls fail past 5 minutes.
    clock_skew_ms: int | None
    #: True when the skew is over 60 seconds.
    clock_skew_warning: bool


class _ReferralAlertRequired(TypedDict):
    #: ``signature_rejected`` (the platform answered 401: a rotated secret or clock
    #: skew) or ``connection_paused``.
    code: str
    message: str
    #: Epoch ms.
    at: int


class ReferralAlert(_ReferralAlertRequired, total=False):
    """Delivery is blocked on something only a person can fix. Show it as a banner."""

    call_id: str | None


class _ReferralConnectionStatusRequired(TypedDict):
    last_test: ReferralLastTest | None
    #: Calls that failed permanently in the last 7 days.
    failed_calls_7d: int
    #: Calls waiting for a retry.
    retrying_calls: int
    last_success_at: int | None


class ReferralConnectionStatus(_ReferralConnectionStatusRequired, total=False):
    #: The last ping, when the provider answers one.
    last_ping: ReferralPing | None
    #: Set while delivery is blocked on something only a person can fix.
    alert: ReferralAlert | None


ReferralInboundOutcome = Literal[
    "applied", "unchanged", "stale", "unknown_customer", "other_program", "ignored"
]


class ReferralInboundEvent(TypedDict):
    """The latest event a platform sent to the inbound URL."""

    #: When Atlas received it (epoch ms).
    at: int
    type: str
    outcome: ReferralInboundOutcome


class ReferralInboundStatus(TypedDict):
    """Two-way sync: where the platform sends referral changes made after sign-up."""

    #: Give this URL to the platform; ``None`` when the provider sends no events.
    url: str | None
    #: Whether an inbound secret is stored (the value is never returned).
    secret_set: bool
    #: The platform's id for Atlas's event subscription, kept for reference.
    endpoint_id: str | None
    #: The latest event received, or ``None``.
    last_event: ReferralInboundEvent | None


#: A referral program whose script or cookie the browser reads.
ReferralBrowserSource = Literal[
    "referalli",
    "referally",
    "rewardful",
    "tolt",
    "promotekit",
    "firstpromoter",
    "partnerstack",
    "dub",
]

#: Which consent manager decides on the tracking cookie's ids: ``auto`` (any common
#: one), one manager, or ``app`` (only the app's own decision).
ReferralConsentProvider = Literal[
    "auto",
    "cookiemunch",
    "onetrust",
    "cookiebot",
    "didomi",
    "usercentrics",
    "osano",
    "cookieyes",
    "complianz",
    "klaro",
    "tcf",
    "consent_mode",
    "app",
]


class _ReferralSettingsRequired(TypedDict):
    object: Literal["referral_settings"]
    enabled: bool
    provider: str
    signing_secret_set: bool
    api_key_set: bool
    url_params: list[str]
    providers: list[ReferralProvider]


class ReferralSettings(_ReferralSettingsRequired, total=False):
    """``GET /v1/instance/referrals``. Secrets are never returned, only ``*_set``."""

    endpoint_url: str | None
    program_id: str | None
    connection_id: str | None
    context_cookie: str | None
    consent_category: str
    consent_fallback_category: str | None
    auto_enroll_users: bool
    link_template: str | None
    timeout_ms: int
    security: ReferralSecuritySettings
    #: Public tracking token (the ``referalli`` provider derives the code lookup from
    #: it). Not a secret.
    tracking_token: str | None
    #: Public, CORS-enabled URL template with ``{code}`` for "X invited you" on hosted
    #: sign-up.
    code_lookup_url: str | None
    #: Show an optional "Referral code" field on hosted sign-up (default ``False``).
    signup_code_field: bool
    #: The referral programs whose script or cookie the browser reads, in order (the
    #: provider's default unless set).
    browser_sources: list[ReferralBrowserSource]
    #: Whether ``browser_sources`` is the provider's default.
    browser_sources_default: bool
    #: Which consent manager decides on the tracking cookie's ids (default ``auto``).
    consent_provider: ReferralConsentProvider
    #: Forward email, name and suspension changes to the platform (default ``True``).
    forward_lifecycle: bool
    #: Mirror the result into ``public_metadata.referral`` (default ``False``).
    mirror_to_public_metadata: bool
    #: Add the user's own code as a ``referral_code`` claim to session and ID tokens
    #: (default ``False``).
    include_referral_claims: bool
    #: What the chosen provider still needs before referrals can be enabled.
    missing: list[str]
    connection: ReferralConnectionStatus | None
    #: Two-way sync: the URL the platform sends referral changes to, and the latest
    #: one received.
    inbound: ReferralInboundStatus
    updated_at: int | None


class UpdateReferralSettingsBody(TypedDict, total=False):
    """``PATCH /v1/instance/referrals``: only the fields sent change, ``None`` clears.
    Enabling without what the provider needs is 422 ``REFERRALS_NOT_CONFIGURED``.
    """

    enabled: bool
    provider: str
    #: https only (http only for localhost on a development instance).
    endpoint_url: str | None
    program_id: str | None
    connection_id: str | None
    #: Write-only, 16-512 characters.
    signing_secret: str | None
    #: Write-only vendor API key.
    api_key: str | None
    #: Write-only, 16-512 characters: verifies the platform's events to
    #: ``inbound.url``. Optional for the Atlas referral protocol (the signing
    #: secret is used when unset).
    inbound_secret: str | None
    #: The platform's id for Atlas's event subscription, kept for reference.
    inbound_endpoint_id: str | None
    url_params: list[str]
    context_cookie: str | None
    consent_category: str
    consent_fallback_category: str | None
    auto_enroll_users: bool
    #: An https URL containing ``{code}``.
    link_template: str | None
    #: 100-5000.
    timeout_ms: int
    security: ReferralSecuritySettings
    #: 1-128 of ``A-Z a-z 0-9 _ -``.
    tracking_token: str | None
    #: An https URL template containing ``{code}``.
    code_lookup_url: str | None
    signup_code_field: bool
    #: The programs to read, in order; ``None`` goes back to the provider's default.
    browser_sources: list[ReferralBrowserSource] | None
    consent_provider: ReferralConsentProvider
    forward_lifecycle: bool
    mirror_to_public_metadata: bool
    include_referral_claims: bool


class ReferralTestError(TypedDict):
    #: e.g. ``signature_rejected`` (401/403), ``timeout``, ``network_error``,
    #: ``url_blocked``, ``http_500``.
    code: str
    message: str


class _ReferralConnectionTestRequired(TypedDict):
    ok: bool


class ReferralConnectionTest(_ReferralConnectionTestRequired, total=False):
    http_status: int | None
    latency_ms: int | None
    error: ReferralTestError
    #: ``ping`` when the platform answered a ping; ``probe`` for the signed export probe.
    method: Literal["ping", "probe"]
    #: The ping answer, when the provider supports ping.
    ping: ReferralPing | None
    #: e.g. a clock more than 60 seconds off.
    warnings: list[str]


class ReferralSimulationMatch(TypedDict, total=False):
    partner_id: str | None
    partner_external_ref: str | None
    matched_via: str | None
    status: str | None


class ReferralSimulationPartner(TypedDict, total=False):
    id: str | None
    code: str | None
    link: str | None


class ReferralSimulationResult(TypedDict, total=False):
    referral: ReferralSimulationMatch | None
    partner: ReferralSimulationPartner | None
    notes: list[str]


class _ReferralSimulateResultRequired(TypedDict):
    object: Literal["referral_simulation"]
    ok: bool
    #: ``atlas_test_<random>``. No user is created.
    customer_ref: str


class ReferralSimulateResult(_ReferralSimulateResultRequired, total=False):
    """``POST /v1/instance/referrals/simulate``: a sign-up call for a made-up user."""

    #: The logged call, in the delivery log.
    call_id: str | None
    http_status: int | None
    latency_ms: int | None
    #: The platform's answer, normalised (``None`` when the call failed).
    result: ReferralSimulationResult | None
    #: The platform's raw answer, personal fields removed.
    response: dict[str, Any] | None
    error: ReferralTestError | None


class ReferralRetryFailedResult(TypedDict):
    """``POST /v1/instance/referrals/calls/retry_failed``."""

    object: Literal["referral_retry"]
    #: How many failed calls were queued to send now.
    requeued: int


class _ReferralBackfillBodyRequired(TypedDict):
    #: ISO 8601 date or date-time (or epoch ms): users created at or after it.
    since: str | int


class ReferralBackfillBody(_ReferralBackfillBodyRequired, total=False):
    """``POST /v1/instance/referrals/backfill``."""

    #: customerRef (``external_id`` or user id) to referral code, up to 10,000. Wins
    #: over ``code_metadata_path``.
    codes: dict[str, str]
    #: Where each user keeps the code they arrived with, e.g.
    #: ``public_metadata.referral_code``.
    code_metadata_path: str


class ReferralBackfillCalls(TypedDict):
    pending: int
    succeeded: int
    failed: int
    skipped: int
    held: int


class _ReferralBackfillJobRequired(TypedDict):
    object: Literal["referral_backfill"]
    id: str
    #: ``running`` while any queued call is still to be sent, then ``completed``.
    status: Literal["running", "completed"]
    #: Epoch ms.
    since: int
    users_scanned: int
    #: Already reported, or no code while auto-enrol is off.
    users_skipped: int
    calls_queued: int
    #: True when more users matched than one backfill takes: run again from
    #: ``next_since``.
    truncated: bool
    #: Where the queued calls stand.
    calls: ReferralBackfillCalls
    #: Epoch ms.
    created_at: int


class ReferralBackfillJob(_ReferralBackfillJobRequired, total=False):
    """A backfill job. Users already reported are skipped."""

    code_metadata_path: str | None
    #: How many codes were given in ``codes``.
    codes_given: int
    #: Epoch ms, when ``truncated``.
    next_since: int | None
    finished_at: int | None


class ReferralRisk(TypedDict):
    """The risk verdict sent with a sign-up (camelCase, as on the referral protocol)."""

    level: Literal["low", "medium", "high"]
    #: 0-100.
    score: int
    signals: list[str]
    captcha: Literal["passed", "not_required", "not_configured"]
    emailVerified: bool


class _ReferralCallRequired(TypedDict):
    object: Literal["referral_call"]
    #: Also the signed ``atlas-id`` header of every attempt.
    id: str
    kind: Literal["signup", "erase", "export", "partner", "signal", "alias", "user", "ping", "test"]
    status: Literal["pending", "succeeded", "retrying", "failed", "held", "skipped"]
    customer_ref: str
    attempts: int
    created_at: int


class ReferralCall(_ReferralCallRequired, total=False):
    """One call in the referral call log."""

    #: Sign-up calls: ``referred``, ``not_referred`` or ``stripped``.
    outcome: str | None
    user_id: str | None
    http_status: int | None
    last_error: str | None
    #: Epoch ms of the next retry, while pending or retrying.
    next_attempt_at: int | None
    risk: ReferralRisk | None
    #: What was sent (never secrets).
    payload: dict[str, Any]
    #: Round trip of the last attempt, in ms.
    latency_ms: int | None
    #: Why the last attempt failed, e.g. ``signature_rejected`` (401, not retried),
    #: ``connection_paused`` (not retried), ``rate_limited``, ``timeout``,
    #: ``network_error``, ``alias_conflict``, ``http_<status>``.
    error_code: str | None
    #: The platform's last answer, personal fields removed.
    response: dict[str, Any] | None
    #: Sign-up calls: how the platform matched the referral and why.
    highlights: ReferralCallHighlights | None
    #: The platform's request id for its last answer, for its support team.
    request_id: str | None
    #: The backfill job that queued the call.
    batch_id: str | None
    updated_at: int


class ReferralCallHighlights(TypedDict, total=False):
    matched_via: str | None
    partner_external_ref: str | None
    notes: list[str]


# --------------------------------------------------------------------------- #
# before_user_create hook                                                      #
# --------------------------------------------------------------------------- #


class BeforeUserCreateHookLastCall(TypedDict, total=False):
    #: Epoch ms.
    at: int
    #: ``ok``, ``timeout``, ``error`` or ``invalid_response``.
    status: str | None
    error: str | None


class _BeforeUserCreateHookRequired(TypedDict):
    object: Literal["before_user_create_hook"]
    enabled: bool
    url: str | None
    #: The secret is write-only.
    signing_secret_set: bool
    #: 500-5000, default 3000.
    timeout_ms: int


class BeforeUserCreateHook(_BeforeUserCreateHookRequired, total=False):
    """``GET /v1/instance/hooks/before_user_create``."""

    #: The last call Atlas made to the hook.
    last_call: BeforeUserCreateHookLastCall | None
    updated_at: int | None


class UpdateBeforeUserCreateHookBody(TypedDict, total=False):
    """``PATCH /v1/instance/hooks/before_user_create``: only the fields sent change.
    Turning it on needs ``url`` and ``signing_secret``.
    """

    enabled: bool
    #: https (http only for localhost on a development instance); ``None`` clears.
    url: str | None
    #: Write-only, 16-512 characters; ``None`` clears.
    signing_secret: str | None
    #: 500-5000.
    timeout_ms: int


class BeforeUserCreateHookAnswer(TypedDict, total=False):
    external_id: str | None
    public_metadata: dict[str, Any] | None
    private_metadata_set: bool
    unsafe_metadata: dict[str, Any] | None


class _BeforeUserCreateHookTestRequired(TypedDict):
    ok: bool
    latency_ms: int


class BeforeUserCreateHookTest(_BeforeUserCreateHookTestRequired, total=False):
    """``POST /v1/instance/hooks/before_user_create/test``: a sample draft sent to the
    hook; nothing is stored.
    """

    answer: BeforeUserCreateHookAnswer
    #: ``code``: ``timeout``, ``error``, ``invalid_response`` or ``not_configured``.
    error: ReferralTestError


class SetLdapBindPasswordBody(TypedDict, total=False):
    bind_password: str


class LdapBindPassword(TypedDict):
    object: Literal["ldap_bind_password"]
    connection_id: str
    set: Literal[True]


class InstanceDeleteLdapBindPasswordResult(TypedDict):
    object: Literal["ldap_bind_password"]
    connection_id: str
    deleted: Literal[True]


class _PreflightFindingsItemRequired(TypedDict):
    severity: Literal["error", "warning", "info"]
    #: Stable snake_case identifier, e.g. oauth_provider_missing_credentials.
    code: str
    #: What is wrong, in a plain sentence.
    message: str
    #: What to do about it, in a plain sentence.
    fix: str


class PreflightFindingsItem(_PreflightFindingsItemRequired, total=False):
    #: Ids of what the finding is about (provider, id/client_id, domain_id/host, …).
    subject: dict[str, str]


class SdkAdvisory(TypedDict):
    object: Literal["sdk_advisory"]
    #: e.g. ``@atlasauth/react``.
    package: str
    #: The affected range, e.g. ``<0.8.1``.
    affected: str
    fixed_in: str
    #: Stable code, e.g. ``email_code_sign_in``.
    reason: str
    severity: Literal["critical", "high", "medium", "low"]
    summary: str
    #: ISO date.
    published_at: str


class SdkVersionSeen(TypedDict):
    package: str
    version: str
    #: Epoch ms.
    last_seen_at: int
    advisories: list[SdkAdvisory]


class _PreflightRequired(TypedDict):
    object: Literal["preflight"]
    #: True when there are no error-severity findings.
    ok: bool
    #: When the check ran (epoch ms).
    checked_at: int
    #: Ordered error, then warning, then info.
    findings: list[PreflightFindingsItem]


class Preflight(_PreflightRequired, total=False):
    #: Atlas browser SDK versions seen in the last 7 days, with their advisories.
    sdk_versions_seen: list[SdkVersionSeen]


class _InstanceSecurityRequired(TypedDict):
    object: Literal["instance_security"]
    kill_switches: dict[str, bool]
    ip_allowlist: list[str]


class InstanceSecurity(_InstanceSecurityRequired, total=False):
    warning: str


class UpdateInstanceSecurityBody(TypedDict, total=False):
    kill_switches: Any
    ip_allowlist: Any
    confirm_lockout: bool


class BulkCreateInvitationsBodyInvitationsItem(TypedDict, total=False):
    email_address: str
    public_metadata: Any


class BulkCreateInvitationsBody(TypedDict, total=False):
    invitations: list[BulkCreateInvitationsBodyInvitationsItem]


class _JobRequired(TypedDict):
    object: Literal["job"]
    id: str
    type: str
    status: str
    total: int
    processed: int
    succeeded: int
    failed: int
    error_count: int
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int
    completed_at: int | None


class Job(_JobRequired, total=False):
    """An import/export job."""

    result: Any
    results: Any


class LegacyAuthConnection(TypedDict, total=False):
    object: Literal["legacy_auth_connection"]
    id: str
    enabled: bool
    verify_url: str
    #: Whether a secret is set — never the secret.
    has_signing_secret: bool
    import_on_login: bool
    timeout_ms: int
    strategy: str
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int
    #: Present and false when no connection exists yet.
    configured: bool


class _SetLegacyAuthConnectionBodyRequired(TypedDict):
    #: The tenant's HTTPS verify endpoint.
    verify_url: str


class SetLegacyAuthConnectionBody(_SetLegacyAuthConnectionBodyRequired, total=False):
    #: Whether sign-in consults the legacy store.
    enabled: bool
    #: HMAC signing secret for the verify webhook.
    signing_secret: str
    #: Create the user locally (hashing the verified password) on a successful verify — the
    #: drain.
    import_on_login: bool
    #: Fail-closed call budget, 1–30000.
    timeout_ms: int
    #: Only "password" today.
    strategy: Literal["password"]


class LegacyAuthConnectionDeleteResult(TypedDict, total=False):
    object: Literal["legacy_auth_connection"]
    deleted: bool


class CreateLocalizationBody(TypedDict, total=False):
    resource_type: str
    resource_name: str
    locale: str
    content: dict[str, Any]
    enabled: bool


class Localization(TypedDict):
    """A per-locale content override."""

    object: Literal["localization"]
    id: str
    resource_type: Literal["email_template", "sms_template", "prompt_copy"]
    resource_name: str
    #: Canonical BCP-47.
    locale: str
    content: dict[str, str]
    enabled: bool
    created_at: str
    updated_at: str


class UpdateLocalizationBody(TypedDict, total=False):
    content: dict[str, Any]
    enabled: bool


class CreateLogStreamBody(TypedDict, total=False):
    name: str
    type: str
    destination: Any
    event_filter: Any
    enabled: bool


class LogStream(TypedDict):
    object: Literal["log_stream"]
    id: str
    name: str
    type: Literal["http", "datadog", "splunk"]
    enabled: bool
    status: str
    event_filter: list[str] | None
    destination: dict[str, Any]
    cursor: str | None
    consecutive_failures: int
    last_error: str | None
    last_delivered_at: int | None
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class UpdateLogStreamBody(TypedDict, total=False):
    name: str
    destination: Any
    event_filter: Any
    enabled: bool
    status: str


class LogStreamTest(TypedDict):
    object: Literal["log_stream_test_result"]
    id: str
    ok: bool
    status: int | None
    error: str | None


class CreateLtiPlatformBody(TypedDict, total=False):
    issuer: str
    client_id: str
    auth_login_url: str
    jwks_uri: str
    deployment_ids: Any
    organization_id: str


class LtiPlatform(TypedDict):
    object: Literal["lti_platform"]
    id: str
    organization_id: str | None
    issuer: str
    client_id: str
    auth_login_url: str
    jwks_uri: str
    deployment_ids: list[str]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class UpdateLtiPlatformBody(TypedDict, total=False):
    auth_login_url: str
    jwks_uri: str
    deployment_ids: Any
    organization_id: str | None


class VerifyM2mTokenBody(TypedDict, total=False):
    token: str


class _M2mTokenVerificationRequired(TypedDict):
    object: str
    valid: bool


class M2mTokenVerification(_M2mTokenVerificationRequired, total=False):
    machine_id: str
    name: str


class CreateMachineEnrolmentTokenBody(TypedDict, total=False):
    organization_id: str
    max_uses: float
    expires_in_seconds: float
    requires_approval: bool
    data: dict[str, Any]
    owner_user_id: str
    single_session: bool
    max_machines: float


class _MachineEnrolmentTokenWithSecretRequired(TypedDict):
    object: Literal["machine_enrolment_token"]
    id: str
    max_uses: int
    uses: int
    #: Expiry (epoch ms).
    expires_at: int
    requires_approval: bool
    #: Created (epoch ms).
    created_at: int
    #: Reveal-once met_ enrolment token (create-only).
    token: str


class MachineEnrolmentTokenWithSecret(_MachineEnrolmentTokenWithSecretRequired, total=False):
    organization_id: str | None


class CreateMachineBody(TypedDict, total=False):
    name: str
    owner_user_id: str
    data: dict[str, Any]


class _MachineWithSecretRequired(TypedDict):
    object: Literal["machine"]
    id: str
    name: str
    #: Stored device lifecycle state (unchanged by the owner's state).
    status: Literal["active", "pending", "revoked"]
    #: Created (epoch ms).
    created_at: int
    #: Reveal-once mk_ secret (create/rotate-only).
    secret: str


class MachineWithSecret(_MachineWithSecretRequired, SealedSecrets, total=False):
    #: Owning org, when org-scoped.
    organization_id: str | None
    #: Owning user, when a user-owned device.
    owner_user_id: str | None
    #: Whether the owning user is usable (not banned, locked, or deleted).
    owner_usable: bool
    #: Derived status: 'active' only when the machine is active AND its owner is usable;
    #: 'owner_suspended' when active but the owner is not; otherwise the raw status.
    effective_status: Literal["active", "owner_suspended", "pending", "revoked"]
    #: The stable device self-identifier supplied at enrolment (null when none).
    device_key: str | None
    #: RFC 7638 thumbprint of the device public key.
    public_key_jkt: str | None
    #: Device metadata (hostname, os, app_version, last_seen_at).
    metadata: dict[str, Any]
    #: When the device completed enrolment (epoch ms).
    enrolled_at: int | None
    #: Updated (epoch ms).
    updated_at: int


class _MachineRequired(TypedDict):
    object: Literal["machine"]
    id: str
    name: str
    #: Stored device lifecycle state (unchanged by the owner's state).
    status: Literal["active", "pending", "revoked"]
    #: Created (epoch ms).
    created_at: int


class Machine(_MachineRequired, total=False):
    #: Owning org, when org-scoped.
    organization_id: str | None
    #: Owning user, when a user-owned device.
    owner_user_id: str | None
    #: Whether the owning user is usable (not banned, locked, or deleted).
    owner_usable: bool
    #: Derived status: 'active' only when the machine is active AND its owner is usable;
    #: 'owner_suspended' when active but the owner is not; otherwise the raw status.
    effective_status: Literal["active", "owner_suspended", "pending", "revoked"]
    #: The stable device self-identifier supplied at enrolment (null when none).
    device_key: str | None
    #: RFC 7638 thumbprint of the device public key.
    public_key_jkt: str | None
    #: Device metadata (hostname, os, app_version, last_seen_at).
    metadata: dict[str, Any]
    #: When the device completed enrolment (epoch ms).
    enrolled_at: int | None
    #: Updated (epoch ms).
    updated_at: int


class UpdateMachineBody(TypedDict, total=False):
    name: str


class UpdateMachineMetadataBody(TypedDict, total=False):
    metadata: dict[str, Any]


class RotateMachineKeyBody(TypedDict):
    #: New device public key, SPKI PEM.
    public_key_pem: str


class ManagedWafCredential(TypedDict, total=False):
    mode: str
    access_key_id: str | None
    has_secret_access_key: bool
    role_arn: str | None
    has_external_id: bool


class _ManagedWafRequired(TypedDict):
    object: Literal["managed_waf"]
    configured: bool
    enabled: bool
    status: str


class ManagedWaf(_ManagedWafRequired, total=False):
    """Unconfigured form omits all but the first four keys."""

    scope: str
    region: str
    web_acl_name: str
    edge_resource_arn: str | None
    cloudfront_distribution_id: str | None
    token_domains: list[str]
    gated_paths: list[str]
    immunity_seconds: int
    credential: ManagedWafCredential
    web_acl_id: str | None
    web_acl_arn: str | None
    last_error: str | None
    last_provisioned_at: int | None
    #: Last updated (epoch ms).
    updated_at: int


class SetManagedWafBodyCredential(TypedDict, total=False):
    mode: Literal["keys", "role"]
    access_key_id: str | None
    secret_access_key: str | None
    role_arn: str | None
    external_id: str | None


class SetManagedWafBody(TypedDict, total=False):
    enabled: bool
    scope: Literal["REGIONAL", "CLOUDFRONT"]
    region: str
    web_acl_name: str
    edge_resource_arn: str | None
    cloudfront_distribution_id: str | None
    token_domains: list[str]
    gated_paths: list[str]
    immunity_seconds: int
    credential: SetManagedWafBodyCredential


class ManagedWafStatus(TypedDict):
    object: Literal["managed_waf_status"]
    enabled: bool
    status: str
    web_acl_id: str | None
    web_acl_arn: str | None
    last_error: str | None
    last_provisioned_at: int | None


class McpServerServer(TypedDict, total=False):
    name: str
    version: str


class _McpServerRequired(TypedDict):
    object: Literal["mcp_server"]
    protocol_version: str
    server: McpServerServer
    capabilities: dict[str, Any]
    tools: list[dict[str, Any]]


class McpServer(_McpServerRequired, total=False):
    rate_limit: Any
    recommended_agent_scopes: list[str]


class McpRequestBody(TypedDict, total=False):
    jsonrpc: str
    id: Any
    method: str
    params: Any


class McpResponseError(TypedDict, total=False):
    code: int
    message: str


class McpResponse(TypedDict, total=False):
    """JSON-RPC 2.0 envelope."""

    jsonrpc: Literal["2.0"]
    id: str | int | None
    result: dict[str, Any]
    error: McpResponseError


class McpConnector(TypedDict, total=False):
    object: Literal["mcp_connector"]
    enabled: bool
    name: str | None
    exposed_scopes: list[str]
    dynamic_registration: bool
    allowed_redirect_hosts: list[str]
    #: The RFC 9728 protected-resource metadata URL.
    discovery_url: str | None
    #: The RFC 8707 resource identifier (token audience).
    resource: str | None
    #: Whether the MCP resource server has been provisioned.
    resource_server_exists: bool


class SetMcpConnectorBody(TypedDict, total=False):
    #: Master switch for the connector and its OAuth discovery.
    enabled: bool
    #: Display name shown on the consent screen (max 80 chars).
    name: str
    #: Which user-scoped tool groups the connector exposes.
    exposed_scopes: list[Literal["profile", "email", "mfa", "sessions", "organizations"]]
    #: Let MCP clients self-register an OAuth client (RFC 7591) for the MCP resource.
    dynamic_registration: bool
    #: Extra redirect-URI hostnames allowed for dynamic registration beyond the built-in MCP
    #: clients.
    allowed_redirect_hosts: list[str]


class _MessagingProviderRequired(TypedDict):
    object: Literal["messaging_provider"]
    channel: str
    transport: str
    from_address: str | None
    status: str
    config: dict[str, str]
    secrets_set: dict[str, bool]
    #: Last updated (epoch ms).
    updated_at: int


class MessagingProvider(_MessagingProviderRequired, total=False):
    #: The provider id: pass it as ``provider_id`` to managed email or the development sender.
    id: str
    #: How the provider sends.
    mode: Literal["standard", "development", "managed_domain"]


class _MessagingProvidersRequired(TypedDict):
    object: Literal["messaging_providers"]
    email: MessagingProvider | None
    sms: MessagingProvider | None


class MessagingProviders(_MessagingProvidersRequired, total=False):
    #: The Atlas-managed sending domain summary (``object``, ``from_address``, ``domain``,
    #: ``status``, ``verified``), or ``None``.
    managed_email: dict[str, Any] | None
    #: The email provider in development mode (``object``, ``enabled``, ``from_address``), or
    #: ``None``.
    development_email: dict[str, Any] | None


class EmailProviderResendConfig(TypedDict, total=False):
    """Provider settings."""

    #: Resend API key (re_…).
    api_key: str


class _EmailProviderResendRequired(TypedDict):
    transport: Literal["resend"]


class EmailProviderResend(_EmailProviderResendRequired, total=False):
    #: The From address, e.g. "Acme <no-reply@acme.com>".
    from_address: str
    #: ``development``: a development instance sends without a verified domain (Atlas sign-in
    #: templates only, capped); 409 on a production instance. Omitted: the stored mode is kept.
    mode: Literal["standard", "development"]
    #: Provider settings.
    config: EmailProviderResendConfig


class EmailProviderSesConfig(TypedDict, total=False):
    """Provider settings."""

    #: AWS region, e.g. us-east-1.
    region: str
    #: IAM access key ID.
    access_key_id: str
    #: IAM secret access key.
    secret_access_key: str
    #: STS session token, only for temporary credentials.
    session_token: str


class _EmailProviderSesRequired(TypedDict):
    transport: Literal["ses"]


class EmailProviderSes(_EmailProviderSesRequired, total=False):
    #: The From address, e.g. "Acme <no-reply@acme.com>".
    from_address: str
    #: ``development``: a development instance sends without a verified domain (Atlas sign-in
    #: templates only, capped); 409 on a production instance. Omitted: the stored mode is kept.
    mode: Literal["standard", "development"]
    #: Provider settings.
    config: EmailProviderSesConfig


class EmailProviderSmtpConfig(TypedDict, total=False):
    """Provider settings."""

    #: SMTP server hostname, e.g. smtp.example.com.
    host: str
    #: SMTP port (1-65535).
    port: int
    #: Use implicit TLS.
    secure: bool
    #: SMTP username, if the server requires authentication.
    username: str
    #: SMTP password or app password.
    password: str


class _EmailProviderSmtpRequired(TypedDict):
    transport: Literal["smtp"]


class EmailProviderSmtp(_EmailProviderSmtpRequired, total=False):
    #: The From address, e.g. "Acme <no-reply@acme.com>".
    from_address: str
    #: ``development``: a development instance sends without a verified domain (Atlas sign-in
    #: templates only, capped); 409 on a production instance. Omitted: the stored mode is kept.
    mode: Literal["standard", "development"]
    #: Provider settings.
    config: EmailProviderSmtpConfig


class EmailProviderBrevoConfig(TypedDict, total=False):
    """Provider settings."""

    #: Brevo API key (xkeysib-…).
    api_key: str


class _EmailProviderBrevoRequired(TypedDict):
    transport: Literal["brevo"]


class EmailProviderBrevo(_EmailProviderBrevoRequired, total=False):
    #: The From address, e.g. "Acme <no-reply@acme.com>".
    from_address: str
    #: ``development``: a development instance sends without a verified domain (Atlas sign-in
    #: templates only, capped); 409 on a production instance. Omitted: the stored mode is kept.
    mode: Literal["standard", "development"]
    #: Provider settings.
    config: EmailProviderBrevoConfig


class EmailProviderMailgunConfig(TypedDict, total=False):
    """Provider settings."""

    #: Mailgun private API key.
    api_key: str
    #: Your Mailgun sending domain, e.g. mg.example.com.
    domain: str
    #: Mailgun region.
    region: Literal["us", "eu"]


class _EmailProviderMailgunRequired(TypedDict):
    transport: Literal["mailgun"]


class EmailProviderMailgun(_EmailProviderMailgunRequired, total=False):
    #: The From address, e.g. "Acme <no-reply@acme.com>".
    from_address: str
    #: ``development``: a development instance sends without a verified domain (Atlas sign-in
    #: templates only, capped); 409 on a production instance. Omitted: the stored mode is kept.
    mode: Literal["standard", "development"]
    #: Provider settings.
    config: EmailProviderMailgunConfig


EmailProviderConfig = Union[
    EmailProviderResend,
    EmailProviderSes,
    EmailProviderSmtp,
    EmailProviderBrevo,
    EmailProviderMailgun,
]


#: Provider settings.
SmsProviderTwilioConfig = TypedDict(
    "SmsProviderTwilioConfig",
    {
        "account_sid": "str",
        "auth_token": "str",
        "from": "str",
        "whatsapp_from": "str",
        "voice_from": "str",
    },
    total=False,
)


class _SmsProviderTwilioRequired(TypedDict):
    transport: Literal["twilio"]


class SmsProviderTwilio(_SmsProviderTwilioRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderTwilioConfig


#: Provider settings.
SmsProviderVonageConfig = TypedDict(
    "SmsProviderVonageConfig", {"api_key": "str", "api_secret": "str", "from": "str"}, total=False
)


class _SmsProviderVonageRequired(TypedDict):
    transport: Literal["vonage"]


class SmsProviderVonage(_SmsProviderVonageRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderVonageConfig


#: Provider settings.
SmsProviderMessagebirdConfig = TypedDict(
    "SmsProviderMessagebirdConfig", {"access_key": "str", "from": "str"}, total=False
)


class _SmsProviderMessagebirdRequired(TypedDict):
    transport: Literal["messagebird"]


class SmsProviderMessagebird(_SmsProviderMessagebirdRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderMessagebirdConfig


#: Provider settings.
SmsProviderPlivoConfig = TypedDict(
    "SmsProviderPlivoConfig", {"auth_id": "str", "auth_token": "str", "from": "str"}, total=False
)


class _SmsProviderPlivoRequired(TypedDict):
    transport: Literal["plivo"]


class SmsProviderPlivo(_SmsProviderPlivoRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderPlivoConfig


#: Provider settings.
SmsProviderTelnyxConfig = TypedDict(
    "SmsProviderTelnyxConfig", {"api_key": "str", "from": "str"}, total=False
)


class _SmsProviderTelnyxRequired(TypedDict):
    transport: Literal["telnyx"]


class SmsProviderTelnyx(_SmsProviderTelnyxRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderTelnyxConfig


#: Provider settings.
SmsProviderSinchConfig = TypedDict(
    "SmsProviderSinchConfig",
    {"service_plan_id": "str", "api_token": "str", "region": "str", "from": "str"},
    total=False,
)


class _SmsProviderSinchRequired(TypedDict):
    transport: Literal["sinch"]


class SmsProviderSinch(_SmsProviderSinchRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderSinchConfig


#: Provider settings.
SmsProviderInfobipConfig = TypedDict(
    "SmsProviderInfobipConfig", {"base_url": "str", "api_key": "str", "from": "str"}, total=False
)


class _SmsProviderInfobipRequired(TypedDict):
    transport: Literal["infobip"]


class SmsProviderInfobip(_SmsProviderInfobipRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderInfobipConfig


#: Provider settings.
SmsProviderClicksendConfig = TypedDict(
    "SmsProviderClicksendConfig", {"username": "str", "api_key": "str", "from": "str"}, total=False
)


class _SmsProviderClicksendRequired(TypedDict):
    transport: Literal["clicksend"]


class SmsProviderClicksend(_SmsProviderClicksendRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderClicksendConfig


#: Provider settings.
SmsProviderBandwidthConfig = TypedDict(
    "SmsProviderBandwidthConfig",
    {
        "account_id": "str",
        "application_id": "str",
        "username": "str",
        "password": "str",
        "from": "str",
    },
    total=False,
)


class _SmsProviderBandwidthRequired(TypedDict):
    transport: Literal["bandwidth"]


class SmsProviderBandwidth(_SmsProviderBandwidthRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderBandwidthConfig


#: Provider settings.
SmsProviderAwsSnsConfig = TypedDict(
    "SmsProviderAwsSnsConfig",
    {
        "region": "str",
        "access_key_id": "str",
        "secret_access_key": "str",
        "session_token": "str",
        "from": "str",
    },
    total=False,
)


class _SmsProviderAwsSnsRequired(TypedDict):
    transport: Literal["aws_sns"]


class SmsProviderAwsSns(_SmsProviderAwsSnsRequired, total=False):
    #: The sender number in E.164 format, e.g. +15551234567.
    from_address: str
    #: Provider settings.
    config: SmsProviderAwsSnsConfig


SmsProviderConfig = Union[
    SmsProviderTwilio,
    SmsProviderVonage,
    SmsProviderMessagebird,
    SmsProviderPlivo,
    SmsProviderTelnyx,
    SmsProviderSinch,
    SmsProviderInfobip,
    SmsProviderClicksend,
    SmsProviderBandwidth,
    SmsProviderAwsSns,
]


class MessagingProviderDeleteResult(TypedDict):
    object: Literal["messaging_provider"]
    channel: str
    deleted: Literal[True]


class TestMessagingProviderBody(TypedDict, total=False):
    to: str


class MessagingTest(TypedDict):
    object: Literal["messaging_test"]
    channel: str
    sent_to: str
    ok: Literal[True]


class CreateNetworkAclBody(TypedDict, total=False):
    action: Any
    cidr: Any
    description: Any
    priority: Any
    enabled: Any


class NetworkAcl(TypedDict):
    object: Literal["network_acl"]
    id: str
    action: Literal["allow", "deny"]
    cidr: str
    description: str | None
    priority: int
    enabled: bool
    expires_at: int | None
    source: str
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class UpdateNetworkAclBody(TypedDict, total=False):
    action: Any
    cidr: Any
    description: Any
    priority: Any
    enabled: Any


class CreateNotificationCategoryBody(TypedDict):
    key: str
    label: str


class NotificationCategory(TypedDict):
    object: Literal["notification_category"]
    id: str
    #: The category key templates and preferences reference.
    key: str
    #: The user-facing label on the preference toggle.
    label: str
    #: Always true for a tenant-defined category.
    optional: bool
    created_at: int


class SetNotificationCategoryBody(TypedDict):
    label: str


class NotificationCategoryDeleteResult(TypedDict, total=False):
    object: Literal["notification_category"]
    key: str
    deleted: bool


class CreateNotificationTemplateBody(TypedDict):
    #: The template name a send passes; unique per instance.
    name: str
    subject: str
    #: Email body with `{{variables}}`.
    body: str
    #: A built-in or tenant-defined notification category key.
    category: str


class NotificationTemplate(TypedDict):
    object: Literal["notification_template"]
    id: str
    #: The template name — the `template` a send passes.
    name: str
    subject: str
    #: The body with `{{variables}}` interpolated at send.
    body: str
    #: The end-user notification category whose preference gates this template.
    category: str
    created_at: int
    updated_at: int


class SetNotificationTemplateBody(TypedDict):
    subject: str
    #: Email body with `{{variables}}`.
    body: str
    #: A built-in category (new_device, unattended_access, credential_change) or a tenant-defined
    #: one (POST /v1/notification_categories), so the send honours the opt-out.
    category: str


class NotificationTemplateDeleteResult(TypedDict, total=False):
    object: Literal["notification_template"]
    name: str
    deleted: bool


class _SendNotificationBodyRequired(TypedDict):
    #: The end-user to notify.
    user_id: str
    #: A tenant-defined template name, or a built-in (new_device, unattended_access,
    #: password_changed, mfa_changed).
    template: str


class SendNotificationBody(_SendNotificationBodyRequired, total=False):
    #: Variables interpolated into the template (e.g. device, location, when, url).
    data: dict[str, str]


class NotificationSend(TypedDict):
    object: Literal["notification"]
    id: str
    status: Literal["sent", "suppressed"]


class _ImportOAuthClientsBodyClientsItemRequired(TypedDict):
    #: Preserve the existing client_id for a migration.
    client_id: str
    name: str
    redirect_uris: list[str]


class ImportOAuthClientsBodyClientsItem(_ImportOAuthClientsBodyClientsItemRequired, total=False):
    #: Plaintext secret; hashed on import.
    client_secret: str
    #: A pre-computed secret hash to import verbatim (in place of client_secret).
    client_secret_hash: str
    allowed_scopes: list[str]
    grant_types: list[str]
    token_endpoint_auth_method: str


class ImportOAuthClientsBody(TypedDict):
    #: The clients to import; each entry is an OAuth client registration.
    clients: list[ImportOAuthClientsBodyClientsItem]


class _OAuthProviderRequired(TypedDict):
    object: Literal["oauth_provider"]
    provider: str
    display_name: str
    configured: bool
    #: Whether the provider is turned on.
    enabled: bool
    allow_sign_in: bool
    allow_sign_up: bool


class OAuthProvider(_OAuthProviderRequired, total=False):
    """A social/OAuth provider config."""

    category: str
    tier: str
    setup_docs_url: str | None
    default_scopes: list[str]
    api_scopes: list[str]
    credential_fields: list[dict[str, Any]]
    settings: list[dict[str, Any]]
    #: Credential-less providers only (siwe, siws, siwf): the stored verifier settings, e.g. {
    #: domain, chain_ids, rpc_url }.
    setting_values: dict[str, str]
    #: True when this provider signs in through an in-page native library (e.g. Google One Tap /
    #: GSI) that verifies an id_token, rather than a redirect.
    native: bool
    #: The effective sign-in mode.
    mode: Literal["native", "redirect"]
    #: Native providers only: the Authorized JavaScript origins to register on the provider
    #: console (the in-page library refuses to start on an unregistered origin, failing
    #: silently).
    javascript_origins: list[str]
    #: The exact callback URL to register at the provider console.
    redirect_uri: str
    #: Atlas's own callback URL; a custom_redirect_uri forwards ?code&state here.
    atlas_callback: str
    #: A tenant's own already-registered callback (migration): Atlas uses it in the authorize +
    #: token exchange and it forwards to atlas_callback.
    custom_redirect_uri: str | None
    client_id: str | None
    has_secret: bool
    scopes: list[str]
    #: The instance's per-provider icon override, or null.
    icon_url: str | None
    updated_at: int | None


class _OauthProviderRequired(TypedDict):
    object: Literal["oauth_provider"]
    provider: str
    configured: bool
    enabled: bool
    updated_fields: list[str]


class OauthProvider(_OauthProviderRequired, total=False):
    #: Credential-less providers (siwe, siws, siwf) only: the stored verifier settings after this
    #: write.
    setting_values: dict[str, str]
    warning: str


class OAuthProviderDeleteResult(TypedDict):
    object: Literal["oauth_provider"]
    provider: str
    deleted: Literal[True]
    note: str


class SetOAuthProviderEnabledBody(TypedDict, total=False):
    enabled: bool


class OAuthProviderSetEnabledResult(TypedDict):
    object: Literal["oauth_provider"]
    provider: str
    enabled: bool


class SetOAuthProviderScopeBody(TypedDict, total=False):
    allow_sign_in: bool
    allow_sign_up: bool


class OAuthProviderSetScopeResult(TypedDict):
    object: Literal["oauth_provider"]
    provider: str
    allow_sign_in: bool
    allow_sign_up: bool


class OauthConnectionTest(TypedDict):
    object: Literal["oauth_connection_test"]
    provider: str
    ok: bool
    reason: str
    message: str
    checked: list[str]
    not_checked: list[str]


class CreateOrgLdapConnectionBodyAttributes(TypedDict, total=False):
    """Directory attribute → Atlas field mapping."""

    email: str
    firstName: str
    lastName: str
    username: str


class CreateOrgLdapConnectionBody(TypedDict, total=False):
    #: The owning organization (required on create).
    organization_id: str
    status: Literal["draft", "active", "disabled"]
    #: ldap:// or ldaps:// directory URL.
    url: str
    #: Service-account DN Atlas binds as to search.
    bind_dn: str
    #: Subtree searched under.
    base_dn: str
    #: Search filter with a {{username}} placeholder.
    user_filter: str
    start_tls: bool
    #: Directory attribute → Atlas field mapping.
    attributes: CreateOrgLdapConnectionBodyAttributes
    #: Service-account password.
    bind_password: str
    default_role_id: str | None


class OrgLdapConnection(TypedDict, total=False):
    object: Literal["org_ldap_connection"]
    id: str
    organization_id: str
    status: Literal["draft", "active", "disabled"]
    url: str
    bind_dn: str
    base_dn: str
    user_filter: str
    start_tls: bool
    #: Directory attribute → Atlas field mapping.
    attributes: CreateOrgLdapConnectionBodyAttributes
    #: Whether a bind password is set — never the password.
    has_bind_password: bool
    default_role_id: str | None
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class UpdateOrgLdapConnectionBody(TypedDict, total=False):
    #: The owning organization (required on create).
    organization_id: str
    status: Literal["draft", "active", "disabled"]
    #: ldap:// or ldaps:// directory URL.
    url: str
    #: Service-account DN Atlas binds as to search.
    bind_dn: str
    #: Subtree searched under.
    base_dn: str
    #: Search filter with a {{username}} placeholder.
    user_filter: str
    start_tls: bool
    #: Directory attribute → Atlas field mapping.
    attributes: CreateOrgLdapConnectionBodyAttributes
    #: Service-account password.
    bind_password: str
    default_role_id: str | None


class TestOrgLdapConnectionBody(TypedDict, total=False):
    bind_password: str


class OrgLdapConnectionTest(TypedDict, total=False):
    object: Literal["org_ldap_connection_test"]
    id: str
    #: Whether the service-account bind succeeded.
    ok: bool
    #: Present only when the bind failed.
    error: str


class OrganizationSettingsSchema(TypedDict, total=False):
    object: Literal["organization_settings_schema"]
    #: A JSON Schema (OpenAPI 3.1 dialect).
    schema: dict[str, Any]
    #: Bumped each time the schema is re-registered.
    version: int
    #: Last registered (epoch ms).
    updated_at: int


class CreateOrganizationSettingsSchemaBody(TypedDict):
    #: A JSON Schema (OpenAPI 3.1 dialect).
    schema: dict[str, Any]


class ReplaceOrganizationSettingsSchemaBody(TypedDict):
    #: A JSON Schema (OpenAPI 3.1 dialect).
    schema: dict[str, Any]


class CreateAuditStreamBody(TypedDict, total=False):
    #: Public HTTPS endpoint.
    url: str
    #: Shared HMAC-SHA256 signing secret (min 16 chars).
    secret: str
    #: Optional shape hint for the collector.
    format: str


class OrgAuditStream(TypedDict, total=False):
    object: Literal["org_audit_stream"]
    id: str
    organization_id: str
    #: The organization's HTTPS SIEM/collector endpoint.
    url: str
    #: Shape hint for the collector, e.g. `json`.
    format: str
    active: bool
    #: Whether a signing secret is set — never the secret itself.
    has_secret: bool
    #: Created (epoch ms).
    created_at: int


class OrganizationBranding(TypedDict):
    object: Literal["organization_branding"]
    organization_id: str
    display_name: str | None
    logo_url: str | None
    primary_color: str | None
    support_url: str | None
    custom_domain: str | None
    updated_at: int | None


class SetOrgBrandingBody(TypedDict, total=False):
    display_name: str | None
    logo_url: str | None
    primary_color: str | None
    support_url: str | None
    custom_domain: str | None


class OrganizationEntitlements(TypedDict):
    object: Literal["organization_entitlements"]
    organization_id: str
    plan: str | None
    features: list[str]
    limits: dict[str, Any]


class OrganizationHierarchyChildrenItem(TypedDict):
    id: str
    name: str
    slug: str


class OrganizationHierarchy(TypedDict):
    object: Literal["organization_hierarchy"]
    organization_id: str
    ancestors: list[str]
    children: list[OrganizationHierarchyChildrenItem]


class SetOrganizationParentBody(TypedDict, total=False):
    parent_organization_id: str | None


class OrganizationSettings(TypedDict, total=False):
    object: Literal["organization_settings"]
    organization_id: str
    values: dict[str, Any]
    #: Monotonic per-org version; 0 when nothing is set yet.
    version: int
    updated_by: str | None
    #: Last write (epoch ms), or null if never set.
    updated_at: int | None


class OrgSettingsBody(TypedDict):
    #: The org settings document.
    values: dict[str, Any]


class _AddOrgEndUserBodyRequired(TypedDict):
    #: An instance user id to attach as a reader.
    user_id: str


class AddOrgEndUserBody(_AddOrgEndUserBodyRequired, total=False):
    #: Defaults to active.
    status: Literal["active", "pending", "blocked"]
    #: How the reader entered the pool.
    source: Literal["hosted", "federated", "token_exchange", "import"]


class OrganizationEndUser(TypedDict, total=False):
    object: Literal["organization_end_user"]
    id: str
    organization_id: str
    user_id: str
    status: Literal["active", "pending", "blocked"]
    source: str
    public_metadata: dict[str, Any]
    approved_at: int | None
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class UpdateOrgEndUserBody(TypedDict):
    status: Literal["active", "pending", "blocked"]


class SetReaderDomainBody(TypedDict):
    #: The organization's own hostname, e.g. readers.acme.com.
    host: str


class PcaAttestors(TypedDict, total=False):
    object: Literal["pca_attestors"]
    #: b64u Ed25519 public keys.
    trusted_attestor_keys: list[str]


class SetPcaAttestorsBody(TypedDict):
    trusted_attestor_keys: list[str]


class PcaFreeze(TypedDict, total=False):
    object: Literal["pca_freeze"]
    frozen: bool


class FreezePcaBody(TypedDict, total=False):
    reason: str


class CreatePcaRevocationBody(TypedDict):
    grant_ref: str
    cap_id: str


class PcaRevokeResult(TypedDict, total=False):
    object: Literal["pca_revocation"]
    grant_ref: str
    cap_id: str
    revoked: bool


class DenyPcaStepUpBody(TypedDict, total=False):
    reason: str


class PcaStepup(TypedDict, total=False):
    object: Literal["pca_stepup"]
    stepup_id: str
    grant_ref: str
    action_digest: str
    required_t: int
    status: Literal["pending", "approved", "denied", "expired"]
    #: Roles that have contributed a share.
    shares: list[str]
    created_at: str
    expires_at: str
    #: Ledger anchoring receipt (present once approved).
    receipt: dict[str, Any]
    #: Present on a cosign that has not yet met the threshold.
    step_up_required: bool


class UpdatePermissionBody(TypedDict, total=False):
    name: str
    description: str | None
    key: str


class CreateAccountlessAppBody(TypedDict, total=False):
    name: str
    environment: str
    #: Origin strings or ``{"origin", "integration"}`` entries.
    allowed_origins: Any


class AccountlessApp(TypedDict):
    object: Literal["accountless_app"]
    id: str
    name: str
    environment: str
    publishable_key: str
    claim_token: str
    expires_at: int
    note: str


class CreatePlatformAppBody(TypedDict, total=False):
    name: str
    environment: str
    allowed_origins: Any
    create_development_sibling: bool
    tags: Any


class _PlatformAppWithSecretRequired(TypedDict):
    object: Literal["app"]
    id: str
    name: str
    environment: Literal["production", "development"]
    publishable_key: str
    #: The Frontend API host: the default per-app host, or the custom domain once it is active.
    frontend_api_host: str | None
    #: The ``iss`` the app's session tokens carry. Changes when a custom domain goes active.
    issuer: str
    #: The OpenID discovery document whose ``issuer`` equals ``issuer``.
    discovery_url: str
    #: The JWKS holding the app's signing keys.
    jwks_uri: str
    allowed_origins: list[str]
    #: X8 housekeeping labels (≤20, each ≤40 chars).
    tags: list[str]
    #: X8 housekeeping: hidden from the default listing.
    archived: bool
    #: Epoch ms the app was archived, or null if not archived.
    archived_at: int | None
    disabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int
    #: Reveal-once per-instance secret key.
    secret: str


class PlatformAppWithSecret(_PlatformAppWithSecretRequired, SealedSecrets, total=False):
    note: str
    #: The declared integration per allowed origin (``redirect`` | ``embedded``).
    allowed_origin_integrations: dict[str, Literal["redirect", "embedded"]]


class PlatformAppProvisioned(TypedDict, total=False):
    #: The auto-created test-mode sibling in the environment opposite the primary (development
    #: for a production app — the default and common case).
    sibling_instance: PlatformAppWithSecret


class AcceptPlatformAppTransferBody(TypedDict, total=False):
    transfer_token: Any


class BulkDeletePlatformAppsBody(TypedDict, total=False):
    ids: Any


class _BulkDeleteResultResultsItemRequired(TypedDict):
    id: str
    deleted: bool


class BulkDeleteResultResultsItem(_BulkDeleteResultResultsItemRequired, total=False):
    reason: str


class BulkDeleteResult(TypedDict):
    object: Literal["bulk_delete_result"]
    results: list[BulkDeleteResultResultsItem]


class ClaimPlatformAppBody(TypedDict, total=False):
    claim_token: Any


class App(TypedDict):
    object: Literal["app"]
    id: str
    disabled: Literal[True]
    note: str


class _PlatformAppRequired(TypedDict):
    object: Literal["app"]
    id: str
    name: str
    environment: Literal["production", "development"]
    publishable_key: str
    #: The Frontend API host: the default per-app host, or the custom domain once it is active.
    frontend_api_host: str | None
    #: The ``iss`` the app's session tokens carry. Changes when a custom domain goes active.
    issuer: str
    #: The OpenID discovery document whose ``issuer`` equals ``issuer``.
    discovery_url: str
    #: The JWKS holding the app's signing keys.
    jwks_uri: str
    allowed_origins: list[str]
    #: X8 housekeeping labels (≤20, each ≤40 chars).
    tags: list[str]
    #: X8 housekeeping: hidden from the default listing.
    archived: bool
    #: Epoch ms the app was archived, or null if not archived.
    archived_at: int | None
    disabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class PlatformApp(_PlatformAppRequired, total=False):
    """An app (instance) a platform owns."""

    #: The declared integration per allowed origin (``redirect`` | ``embedded``). Write
    #: ``allowed_origins`` entries as ``{"origin", "integration"}`` to set one.
    allowed_origin_integrations: dict[str, Literal["redirect", "embedded"]]


class UpdatePlatformAppBody(TypedDict, total=False):
    name: Any
    allowed_origins: Any
    tags: Any


class CreatePlatformAppInstanceBody(TypedDict, total=False):
    environment: str
    allowed_origins: Any


class AppSecret(SealedSecrets):
    object: Literal["app_secret"]
    id: str
    secret: str
    note: str


class RotatePlatformAppSecretBody(TypedDict, total=False):
    #: How long the prior keys keep working, in seconds. Default 259200 (72 hours); ``0``
    #: revokes them now; at most 604800 (7 days).
    overlap_seconds: float


#: Body of ``apps.rotate_instance_secret`` (the same shape as the app-level rotate).
RotatePlatformSecretBody = RotatePlatformAppSecretBody


class _PlatformInstanceSecretRotationRequired(TypedDict):
    object: Literal["app_secret"]
    app_id: str
    instance_id: str
    #: The new secret key, revealed exactly once.
    secret: str
    #: The overlap applied, in seconds.
    overlap_seconds: int
    #: When the prior keys stop working (epoch ms); ``None`` on a hard cut.
    previous_keys_expire_at: int | None
    note: str


class PlatformInstanceSecretRotation(_PlatformInstanceSecretRotationRequired, SealedSecrets, total=False):
    """``apps.rotate_instance_secret`` response."""


class _PlatformAppRotateSecretResultRequired(TypedDict):
    object: Literal["app_secret"]
    app_id: str
    secret: str
    overlap_seconds: int
    note: str


class PlatformAppRotateSecretResult(_PlatformAppRotateSecretResultRequired, SealedSecrets, total=False):
    previous_keys_expire_at: int | None


class AppTransfer(TypedDict):
    object: Literal["app_transfer"]
    id: str
    transfer_token: str
    expires_at: int
    note: str


class CreateAtlasIdAppBodyBrandingCopy(TypedDict, total=False):
    """Page text."""

    #: Default "Sign in" (the app is named on the "to continue to {app}" line under it).
    sign_in_title: str | None
    sign_in_subtitle: str | None
    #: Default "Create your Atlas Account".
    sign_up_title: str | None
    sign_up_subtitle: str | None
    #: Shown on the consent screen above the list of permissions.
    consent_message: str | None
    #: https URL, linked in the page footer.
    support_url: str | None
    #: Text of the support link.
    support_label: str | None


class CreateAtlasIdAppBodyBranding(TypedDict, total=False):
    """How the Sign in with Atlas page and consent screen look for this app."""

    #: Default auto (follows the visitor’s system setting).
    theme: Literal["auto", "light", "dark"] | None
    #: Button colour, #RRGGBB.
    accent_color: str | None
    #: Page background behind the card, #RRGGBB.
    background_color: str | None
    #: https URL, linked in the page footer.
    privacy_policy_url: str | None
    #: https URL, linked in the page footer.
    terms_of_service_url: str | None
    #: The sign-in page design (AtlasDesign settings).
    design: AtlasDesignPatch | None
    #: Page text.
    copy: CreateAtlasIdAppBodyBrandingCopy | None


class CreateAtlasIdAppBody(TypedDict, total=False):
    name: str
    redirect_uris: list[str]
    #: Where /oauth2/logout may send the user after sign-out.
    post_logout_redirect_uris: list[str]
    #: OIDC Back-Channel Logout: when the user signs out of Atlas, a signed logout_token is
    #: POSTed here (form field `logout_token`).
    backchannel_logout_uri: str | None
    #: Whether the app needs `sid` in the logout_token.
    backchannel_logout_session_required: bool
    #: OIDC Front-Channel Logout: loaded in a hidden iframe on the Atlas sign-out page, with
    #: `iss` (and `sid` if session-required).
    frontchannel_logout_uri: str | None
    #: Add `sid` to the front-channel logout URL.
    frontchannel_logout_session_required: bool
    logo_url: str | None
    homepage_url: str | None
    allowed_scopes: list[str]
    #: How the Sign in with Atlas page and consent screen look for this app.
    branding: CreateAtlasIdAppBodyBranding | None
    type: Literal["confidential", "public"]


class UpdateAtlasIdAppBody(TypedDict, total=False):
    name: str
    redirect_uris: list[str]
    #: Where /oauth2/logout may send the user after sign-out.
    post_logout_redirect_uris: list[str]
    #: OIDC Back-Channel Logout: when the user signs out of Atlas, a signed logout_token is
    #: POSTed here (form field `logout_token`).
    backchannel_logout_uri: str | None
    #: Whether the app needs `sid` in the logout_token.
    backchannel_logout_session_required: bool
    #: OIDC Front-Channel Logout: loaded in a hidden iframe on the Atlas sign-out page, with
    #: `iss` (and `sid` if session-required).
    frontchannel_logout_uri: str | None
    #: Add `sid` to the front-channel logout URL.
    frontchannel_logout_session_required: bool
    logo_url: str | None
    homepage_url: str | None
    allowed_scopes: list[str]
    #: How the Sign in with Atlas page and consent screen look for this app.
    branding: CreateAtlasIdAppBodyBranding | None
    #: Per-app webhook (public https): user.updated, user.deleted and grant.revoked for this
    #: app's users. The first set returns ``webhook_secret`` once; ``None`` removes it.
    webhook_url: str | None
    #: Test sign-in mode for this app (needs a verified domain; 422 ``DOMAIN_NOT_VERIFIED``).
    test_mode: bool
    #: Test and review accounts must use an address on a domain you verified.
    provisioned_verified_domains_only: bool


class CreateRadiusClientBody(TypedDict, total=False):
    name: Any
    nas_identifier: Any
    ip_address: Any
    ip_cidr: Any
    reply_attributes: Any
    shared_secret: Any
    require_message_authenticator: Any
    enabled: Any


class RadiusClientReplyAttributes(TypedDict, total=False):
    filterId: str
    vlan: int


class RadiusClient(TypedDict):
    """reply_attributes inner keys are camelCase (stored value returned unchanged)."""

    object: Literal["radius_client"]
    id: str
    name: str
    nas_identifier: str
    ip_address: str | None
    ip_cidr: str | None
    reply_attributes: RadiusClientReplyAttributes | None
    has_secret: bool
    require_message_authenticator: bool
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class UpdateRadiusClientBody(TypedDict, total=False):
    name: Any
    nas_identifier: Any
    ip_address: Any
    ip_cidr: Any
    reply_attributes: Any
    shared_secret: Any
    require_message_authenticator: Any
    enabled: Any


class RateLimitPolicyBoundsValue(TypedDict, total=False):
    min: int
    max: int


class _RateLimitPolicyRequired(TypedDict):
    object: Literal["rate_limit_policy"]
    fapi_create_per_min: int
    fapi_verify_per_min: int
    bapi_per_min: int
    bounds: dict[str, RateLimitPolicyBoundsValue]


class RateLimitRule(TypedDict):
    """At most ``max`` requests per ``window_seconds`` for one named ``group``, counted
    per ``key``. A rule on a group that owns a built-in budget replaces it; any other
    rule adds a budget on top."""

    group: str
    window_seconds: int
    max: int
    key: Literal["ip", "user", "instance"]


class RateLimitPolicy(_RateLimitPolicyRequired, total=False):
    ldap_per_ip_per_min: int
    ldap_per_user_per_min: int
    #: Per-endpoint rules (one per group) over the built-in limiter.
    rules: list[RateLimitRule]
    #: The groups a rule may name, with what each covers and its budget.
    groups: list[dict[str, Any]]


class UpdateRateLimitPolicyBody(TypedDict, total=False):
    fapi_create_per_min: Any
    fapi_verify_per_min: Any
    bapi_per_min: Any
    ldap_per_ip_per_min: Any
    ldap_per_user_per_min: Any
    #: The FULL rule list (replaces the stored one; ``[]`` clears).
    rules: list[RateLimitRule]


class CreateRedirectUrlBody(TypedDict, total=False):
    url: str


class RedirectUrl(TypedDict):
    object: Literal["redirect_url"]
    id: str
    url: str
    #: Created (epoch ms).
    created_at: int


class _RiskBasedMfaRequired(TypedDict):
    object: Literal["risk_based_mfa"]
    enabled: bool
    step_up_threshold: float
    on_high_risk_no_factor: str
    weights: dict[str, Any]
    signals: dict[str, Any]


class RiskBasedMfa(_RiskBasedMfaRequired, total=False):
    #: ``enforce`` or ``audit`` (score and record without acting).
    mode: str
    #: What each risk level does: ``{"medium": ..., "high": ...}``.
    level_actions: dict[str, Any]
    #: IP-reputation / email-risk feeds.
    reputation: dict[str, Any]
    #: Fraud rules and sanctioned countries used by ``fraud_lookup``.
    fraud: dict[str, Any]
    #: Per-user baseline: ``{"enabled": bool, "weight": number}``.
    baseline: dict[str, Any]
    #: Re-evaluate a session on refresh: ``{"enabled": bool, "action": "revoke"|"notify"|"audit"}``.
    mid_session: dict[str, Any]


class UpdateRiskBasedMfaBody(TypedDict, total=False):
    enabled: Any
    step_up_threshold: Any
    on_high_risk_no_factor: Any
    weights: Any
    signals: Any
    mode: Any
    level_actions: Any
    reputation: Any
    fraud: Any
    baseline: Any
    mid_session: Any


class _RiskEventRequired(TypedDict):
    object: Literal["risk_event"]
    id: str
    user_id: str
    #: ``low``, ``medium`` or ``high``.
    level: str
    score: float
    #: Names of the signals that fired.
    signals: list[str]
    #: The action decided; in audit mode, what would have happened.
    action: str
    #: ``enforce`` or ``audit``.
    mode: str
    ip: str | None
    #: ``legit``, ``fraud`` or ``None``.
    feedback: str | None
    feedback_at: str | None
    created_at: str


class RiskEvent(_RiskEventRequired):
    pass


class RiskEventFeedbackBody(TypedDict):
    #: ``legit`` or ``fraud``.
    verdict: str


class RiskEventMetrics(TypedDict):
    object: Literal["risk_event_metrics"]
    days: int
    total: int
    #: ``[{"level", "action", "mode", "count"}]``.
    buckets: list[dict[str, Any]]


class _FraudLookupBodyRequired(TypedDict):
    #: Client IP address.
    ip: str


class FraudLookupBody(_FraudLookupBodyRequired, total=False):
    user_agent: str
    #: The stable id from the JS SDK.
    device_id: str
    email: str
    #: A user of this instance, for user-based rules.
    user_id: str
    org_id: str
    #: Device features reported by the SDK.
    device: dict[str, Any]


class FraudLookup(TypedDict):
    object: Literal["fraud_lookup"]
    #: ``allow``, ``challenge`` or ``block``.
    verdict: str
    reasons: list[str]
    matched_rules: list[str]
    device_id: str | None
    signals: dict[str, Any]


class _CreateScimProvisioningTargetBodyRequired(TypedDict):
    #: A label for this target.
    name: str
    #: Downstream SCIM 2.0 base URL.
    base_url: str
    #: Write-only.
    bearer_token: str


class CreateScimProvisioningTargetBody(_CreateScimProvisioningTargetBodyRequired, total=False):
    #: Optional.
    attribute_mapping: dict[str, str]
    #: What to do downstream when an Atlas user is banned/soft-deleted.
    deprovision_action: Literal["deactivate", "delete"]
    #: Default true.
    enabled: bool


class ScimProvisioningTarget(TypedDict):
    object: Literal["scim_provisioning_target"]
    id: str
    name: str
    base_url: str
    #: The bearer token is write-only; only this marker is returned.
    has_bearer_token: bool
    enabled: bool
    attribute_mapping: dict[str, Any]
    deprovision_action: str
    status: str
    cursor: str | None
    consecutive_failures: int
    last_error: str | None
    last_synced_at: int | None
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class ScimProvisioningTargetGetResult(TypedDict, total=False):
    object: Literal["scim_provisioning_target"]
    id: str
    name: str
    #: The downstream SCIM 2.0 base URL (https).
    base_url: str
    #: Whether a downstream bearer is configured.
    has_bearer_token: bool
    enabled: bool
    #: SCIM attribute path → Atlas source field (e.g.
    #: {"userName":"email","name.givenName":"firstName"}).
    attribute_mapping: dict[str, str]
    deprovision_action: Literal["deactivate", "delete"]
    status: Literal["active", "paused"]
    #: Event cursor; only users after it forward automatically (backfill with sync_user).
    cursor: str | None
    consecutive_failures: int
    last_error: str | None
    #: Epoch ms of the last successful push, or null.
    last_synced_at: int | None
    created_at: int
    updated_at: int


class UpdateScimProvisioningTargetBody(TypedDict, total=False):
    name: str
    #: https, SSRF-guarded (same rule as create).
    base_url: str
    #: Write-only; omit to keep the current bearer.
    bearer_token: str
    attribute_mapping: dict[str, str]
    deprovision_action: Literal["deactivate", "delete"]
    enabled: bool
    #: Pause forwarding without deleting the target.
    status: Literal["active", "paused"]


class SyncScimGroupBody(TypedDict):
    #: The organization id whose members to sync (only users already provisioned to this target
    #: are pushed).
    group_id: str


class ScimSyncResult(TypedDict, total=False):
    #: The push performed: create, update, deprovision, or noop.
    action: str
    ok: bool
    #: Downstream HTTP status.
    status: int | None
    #: The id the downstream assigned; stored and reused on re-sync (POST→PUT).
    remote_id: str | None
    error: str | None


class SyncScimUserBody(TypedDict):
    user_id: str


class ScimProvisioningTargetTest(TypedDict, total=False):
    ok: bool
    #: Downstream HTTP status of the probe, or null on a transport failure.
    status: int | None
    error: str | None


class _CreateSessionExchangeAppBodyRequired(TypedDict):
    #: A human label for the downstream app.
    name: str
    #: Public https endpoint Atlas POSTs the signed logout_token to (application/x-www-form-
    #: urlencoded: logout_token=<jwt>) when a session ends.
    backchannel_logout_uri: str


class CreateSessionExchangeAppBody(_CreateSessionExchangeAppBodyRequired, total=False):
    #: Optional override for the logout_token `aud` claim.
    audience: str | None


class SessionExchangeApp(TypedDict, total=False):
    object: Literal["session_exchange_app"]
    id: str
    name: str
    backchannel_logout_uri: str
    #: The aud claim the logout_token carries.
    audience: str
    created_at: int
    updated_at: int


class UpdateSessionExchangeAppBody(TypedDict, total=False):
    name: str
    #: Public https endpoint.
    backchannel_logout_uri: str
    audience: str | None


class CreateSessionBodyActor(TypedDict, total=False):
    """Stamp an impersonation act claim."""

    sub: str


class _CreateSessionBodyRequired(TypedDict):
    user_id: str


class CreateSessionBody(_CreateSessionBodyRequired, total=False):
    #: Opt in to browser-cookie establishment.
    set_cookies: bool
    #: Domain= for the cookies (e.g. .acme.com) so the session spans subdomains.
    cookie_domain: str
    #: Stamp an impersonation act claim.
    actor: CreateSessionBodyActor
    #: Custom per-session data to attach (a JSON object, at most 2 KB).
    custom_data: dict[str, Any]


class SessionCreated(TypedDict, total=False):
    object: Literal["session"]
    id: str
    user_id: str
    #: The session JWT (short-lived; verify with JWKS).
    jwt: str
    #: Long-lived refresh token to mint the next jwt.
    refresh_token: str
    #: Seconds until the jwt expires.
    expires_in: int
    #: Present ONLY when the request passed set_cookies:true — the Set-Cookie header strings to
    #: relay verbatim onto your HTTP response to establish a real browser session.
    cookies: list[str]


class SessionToken(TypedDict):
    object: str
    jwt: str
    expires_in: int


class SignInTokenRevokeResult(TypedDict):
    object: Literal["sign_in_token"]
    id: str
    revoked: Literal[True]


class CreateSmsTemplateBody(TypedDict, total=False):
    name: str
    body: str
    enabled: bool


class SmsTemplate(TypedDict):
    object: Literal["sms_template"]
    name: str
    default: str
    body: str | None
    enabled: bool
    customised: bool
    variables: list[str]


class UpdateSmsTemplateBody(TypedDict, total=False):
    body: str
    enabled: bool


class PreviewSmsTemplateBody(TypedDict, total=False):
    body: str


class SmsTemplatePreview(TypedDict):
    object: Literal["sms_template_preview"]
    name: str
    body: str
    customised: bool


class CreateSsoOnboardingProfileBody(TypedDict, total=False):
    name: str
    allowed_connection_types: Any
    organization_id: str | None
    company_name: str | None
    allow_scim: Any


class SsoOnboardingProfile(TypedDict):
    object: Literal["sso_onboarding_profile"]
    id: str
    name: str
    allowed_connection_types: list[str]
    organization_id: str | None
    company_name: str | None
    allow_scim: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class CreateSsoOnboardingTicketBody(TypedDict, total=False):
    organization_id: str | None
    expires_in_seconds: float


class SsoOnboardingRevokeTicketResult(TypedDict):
    object: Literal["sso_onboarding_ticket"]
    id: str
    revoked: Literal[True]


class CreateTestInstanceBody(TypedDict, total=False):
    #: Mint a fresh sk_test for the sibling.
    rotate_secret: bool


class TestInstance(TypedDict, total=False):
    object: Literal["test_instance"]
    instance_id: str
    environment: Literal["development"]
    publishable_key: str
    created: bool
    #: The sk_test — returned ONLY on create/rotate.
    secret_key: str


class PurgeTestUsersBody(TypedDict, total=False):
    #: Max users to purge this call (1–1000, default 200).
    limit: int


class TestingPurgeTestUsersResult(TypedDict):
    object: str
    purged: int
    has_more: bool


class TestingToken(TypedDict):
    object: Literal["testing_token"]
    #: The signed testing token.
    jwt: str
    token_use: Literal["testing"]
    #: Lifetime in seconds.
    expires_in: int


class _CreateTicketBodyRequired(TypedDict):
    #: Ticket lifetime in seconds.
    ttl_seconds: int


class CreateTicketBody(_CreateTicketBodyRequired, total=False):
    #: Arbitrary JSON returned to whoever redeems the ticket.
    payload: Any
    #: When true (default), the first successful redeem consumes the ticket and all later redeems
    #: are refused.
    single_use: bool
    #: If set, only a redeemer acting as this user may redeem (FAPI: the session user; BAPI:
    #: for_user).
    bound_user: str
    #: If set, only a redeemer acting for this organization may redeem (FAPI: a proven member;
    #: BAPI: for_org).
    bound_org: str


class Ticket(TypedDict, total=False):
    object: Literal["ticket"]
    id: str
    #: The opaque `tkt_…` secret — returned only here, never again.
    ticket: str
    single_use: bool
    bound_user: str | None
    bound_org: str | None
    created_at: int
    expires_at: int


class _RedeemTicketBodyRequired(TypedDict):
    #: The opaque `tkt_…` secret to redeem.
    ticket: str


class RedeemTicketBody(_RedeemTicketBodyRequired, total=False):
    #: The user this redemption is on behalf of, matched against bound_user.
    for_user: str
    #: The organization this redemption is for, matched against bound_org.
    for_org: str


class RedeemedTicket(TypedDict, total=False):
    object: Literal["ticket_redemption"]
    #: The redeemed ticket id.
    id: str
    #: The arbitrary JSON the ticket carried, returned verbatim.
    payload: Any
    single_use: bool


class VerifyTokenBody(TypedDict, total=False):
    token: str
    authorized_parties: list[str]


class _TokenVerificationRequired(TypedDict):
    object: str
    verified: bool


class TokenVerification(_TokenVerificationRequired, total=False):
    reason: str
    user_id: str
    session_id: str
    organization_id: str | None
    organization_role: str | None
    organization_permissions: list[str]
    mfa: bool
    checked_authoritatively: bool


UsageWindow = TypedDict("UsageWindow", {"from": "str", "to": "str", "days": "int"}, total=False)


UsagePreviousWindow = TypedDict("UsagePreviousWindow", {"from": "str", "to": "str"}, total=False)


class UsageMetricsItem(TypedDict, total=False):
    metric: str
    label: str
    description: str
    additive: bool
    points: list[Any]
    peak: Any
    total: float | None
    trend: float | None


class UsageMonthlyActiveUsers(TypedDict, total=False):
    value: int | None
    window_days: int
    trend: float | None


class _UsageRequired(TypedDict):
    object: Literal["usage"]
    window: UsageWindow
    metrics: list[UsageMetricsItem]


class Usage(_UsageRequired, total=False):
    previous_window: UsagePreviousWindow
    monthly_active_users: UsageMonthlyActiveUsers


class ImportPhoneNumber(TypedDict, total=False):
    phone_number: str
    verified: bool


class ImportOrganizationMembership(TypedDict, total=False):
    """The organization by Atlas id, by its id in the old system or by slug; with the
    job option ``create_organizations`` a missing one is created (``organization_name``)."""

    organization_id: str
    organization_external_id: str
    organization_slug: str
    organization_name: str
    #: A role key (``org:admin``, ``admin``, ``member`` or a custom key).
    role: str


class ImportUserRow(TypedDict, total=False):
    """One row of ``user_imports.create``. Rows are plain dicts; these are the keys."""

    email_address: str
    password: str
    password_hash: str
    password_hasher: str
    #: The per-user salt for a hash whose parameters are given job-wide.
    password_salt: str
    email_verified: bool
    first_name: str
    last_name: str
    username: str
    public_metadata: dict[str, Any]
    private_metadata: dict[str, Any]
    unsafe_metadata: dict[str, Any]
    external_accounts: list[dict[str, Any]]
    #: The user's id in the system being migrated from.
    external_id: str
    #: When the account was originally created: ISO 8601, or epoch seconds/ms.
    created_at: str | int
    phone_number: str
    phone_numbers: list[ImportPhoneNumber]
    organization_memberships: list[ImportOrganizationMembership]


class FirebaseScryptConfig(TypedDict):
    signer_key: str
    salt_separator: str
    rounds: int
    mem_cost: int


class PasswordHashConfig(TypedDict, total=False):
    firebase: FirebaseScryptConfig


class CreateUserImportBody(TypedDict, total=False):
    users: list[ImportUserRow] | list[dict[str, Any]]
    upsert: bool
    #: Whether the import may notify the imported users. ``False`` (the default) sends nothing.
    notify: bool
    #: Create an organization a membership names that does not exist yet.
    create_organizations: bool
    #: Job-level hash parameters (Firebase scrypt).
    password_hash_config: PasswordHashConfig


class _UsersByEmailsBodyRequired(TypedDict):
    #: Up to 1000 addresses, deduped.
    email_addresses: list[str]


class UsersByEmailsBody(_UsersByEmailsBodyRequired, total=False):
    #: Default false (verified only).
    include_unverified: bool
    #: Default false (live users only).
    include_deleted: bool


class _CreateApprovalRequestBodyRequired(TypedDict):
    #: What is being approved, shown on the device (e.g. "Remote desktop connection from
    #: 203.0.113.9, Berlin").
    description: str


class CreateApprovalRequestBody(_CreateApprovalRequestBodyRequired, total=False):
    #: Optional key/value details to render beneath the description.
    context: dict[str, str]


class ApprovalRequestCreated(TypedDict, total=False):
    object: Literal["approval_request"]
    id: str
    status: Literal["pending"]
    #: The number to display to the user; the device must send back the one that matches.
    match_number: str
    expires_at: int


class ApprovalRequest(TypedDict, total=False):
    object: Literal["approval_request"]
    id: str
    status: Literal["pending", "approved", "denied", "expired"]
    description: str
    context: dict[str, str]
    #: The push device that approved (if the responder named it).
    approved_by_device_id: str | None
    created_at: int
    expires_at: int
    resolved_at: int | None


class RecordConsentBody(TypedDict, total=False):
    policy: str
    version: str
    status: str
    source: str
    metadata: Any
    #: Policy acceptance evidence: the exact version (must be that version of that policy).
    policy_version_id: str
    #: Must equal the version's ``content_sha256`` when given.
    content_sha256: str
    display: Literal["checkbox", "scroll", "link"]
    scrolled_to_end: bool
    view_ms: int
    locale: str


class _ConsentRequired(TypedDict):
    object: Literal["consent"]
    id: str
    policy: str
    version: str
    #: accepted | withdrawn
    status: str
    #: Recorded (epoch ms).
    created_at: int


class Consent(_ConsentRequired, total=False):
    source: str | None
    metadata: Any
    #: Policy acceptance evidence (``None`` on records made outside a policy flow).
    policy_version_id: str | None
    content_sha256: str | None
    display: Literal["checkbox", "scroll", "link"] | None
    scrolled_to_end: bool | None
    view_ms: int | None
    locale: str | None


class ScheduleUserDeletionBody(TypedDict, total=False):
    #: Cancellation window in seconds before the deletion is finalized.
    grace_seconds: float


class SetUserDirectiveBody(TypedDict, total=False):
    suspended_until: str
    read_only: bool
    forced_logout: bool
    reason: str


class _DirectiveRequired(TypedDict):
    object: Literal["directive"]
    user_id: str
    #: Live sessions revoked by imposing the directive.
    sessions_revoked: int


class Directive(_DirectiveRequired, total=False):
    #: ISO 8601; present only when a suspension was imposed.
    suspended_until: str
    #: Present only when set.
    read_only: Literal[True]
    #: Present only when set.
    forced_logout: Literal[True]
    #: Present only when provided.
    reason: str


class DirectiveLiftResult(TypedDict):
    object: Literal["directive"]
    user_id: str
    lifted: Literal[True]


class _CreateErasureAckBodyRequired(TypedDict):
    #: The acknowledging app/system (its app id or a label).
    source: str


class CreateErasureAckBody(_CreateErasureAckBodyRequired, total=False):
    #: Alias of source.
    app_id: str
    #: The app's contributed data for the DSAR export; omit to only confirm a purge.
    payload: dict[str, Any]


class UserErasureAck(TypedDict):
    object: Literal["user_erasure_ack"]
    id: str
    user_id: str
    #: The acknowledging app/system.
    source: str
    #: Acknowledged (epoch ms).
    created_at: int


class UserErasureExportAppContributionsItem(TypedDict):
    source: str
    #: Contributed (epoch ms).
    contributed_at: int
    payload: Any


class UserErasureExport(TypedDict):
    object: Literal["erasure_export"]
    format_version: Literal[1]
    #: Generated (epoch ms).
    generated_at: int
    user_id: str
    #: Atlas's own data about the subject — the no-secret self-service export bundle.
    atlas: dict[str, Any]
    #: One entry per app that acknowledged, with the blob it contributed.
    app_contributions: list[UserErasureExportAppContributionsItem]


class ConnectExternalAccountBody(TypedDict, total=False):
    provider: str
    redirect_url: str
    additional_scopes: Any


class UserConnectExternalAccountResult(TypedDict):
    object: str
    provider: str
    user_id: str
    attempt_id: str
    authorization_url: str
    scopes: list[str]


class UserGrantRevokeAllResult(TypedDict):
    object: str
    id: str
    grants_revoked: int
    tokens_revoked: int


class LinkIdentityBody(TypedDict, total=False):
    secondary_user_id: str
    user_id: str
    link_with: str


class IdentityUnlinkProviderResult(TypedDict):
    object: str
    id: str
    provider: str
    removed: bool


class ImportIdentityBody(TypedDict, total=False):
    provider: str
    provider_user_id: str
    email_address: str
    verified: bool


class _IdentityRequired(TypedDict):
    object: str
    id: str
    type: str
    provider: str
    is_primary: bool


class Identity(_IdentityRequired, total=False):
    provider_user_id: str
    email: str | None
    email_verified: bool
    has_password: bool


class _IdentityUnlinkResultRequired(TypedDict):
    object: str
    id: str
    provider: str
    unlinked: bool


class IdentityUnlinkResult(_IdentityUnlinkResultRequired, total=False):
    new_user_id: str


class NotificationPreferencesPreferencesItem(TypedDict):
    category: str
    #: User-facing label for the toggle.
    label: str
    enabled: bool
    optional: bool


class NotificationPreferences(TypedDict):
    object: Literal["notification_preferences"]
    preferences: list[NotificationPreferencesPreferencesItem]


class UpdateNotificationPreferencesBody(TypedDict):
    #: Map of category → enabled.
    preferences: dict[str, bool]


class _SetUserPasswordBodyRequired(TypedDict):
    #: The new plaintext password; Argon2id-hashed server-side.
    password: str


class SetUserPasswordBody(_SetUserPasswordBodyRequired, total=False):
    #: A no-op here since an admin set runs no policy/breach check.
    skip_password_checks: bool
    #: Revoke the user's live sessions and bump sessions_version (JWTs die within 60s).
    sign_out_of_other_sessions: bool


class AddPhoneNumberBody(TypedDict, total=False):
    phone_number: str


class PhoneNumber(TypedDict):
    object: Literal["phone_number"]
    id: str
    phone_number: str
    verified: bool
    #: When the number was added (epoch ms).
    created_at: int


class ProgressionEventBody(TypedDict, total=False):
    track: str
    amount: float
    reason: str
    idempotency_key: str


class ProgressionEvent(TypedDict):
    object: Literal["progression_event"]
    track: str
    xp: int
    level: int
    level_changed: bool
    delta: int


class ResolvedUserIdentitiesItem(TypedDict):
    provider: str
    provider_user_id: str
    email: str | None


class ResolvedUser(TypedDict):
    object: str
    user_id: str
    email: str | None
    email_verified: bool
    name: str | None
    image_url: str | None
    identities: list[ResolvedUserIdentitiesItem]


class UserStateAttributesProgressionValue(TypedDict):
    xp: int
    level: int


class _UserStateAttributesRequired(TypedDict):
    #: Map keyed by track name.
    progression: dict[str, UserStateAttributesProgressionValue]


class UserStateAttributes(_UserStateAttributesRequired, total=False):
    #: From public_metadata.tier; present only when set.
    tier: Any
    #: From public_metadata.flair; present only when set.
    flair: Any


class UserState(TypedDict):
    """A user's portable state (progression / tier / flair / entitlements / directives /
    roles).
    """

    object: Literal["user_state"]
    attributes: UserStateAttributes
    entitlements: list[Any]
    directives: list[Any]
    roles: list[Any]


class CreateWaitlistEntryBody(TypedDict, total=False):
    email_address: str


class BulkCreateWaitlistEntriesBody(TypedDict, total=False):
    email_addresses: list[str]


class UpdateWebhookEndpointBody(TypedDict, total=False):
    url: str
    enabled_events: list[str]
    active: bool
    event_naming: Literal["canonical", "legacy", "both"]
    signature_versions: list[str]
    destination: dict[str, Any]
    destination_credentials: dict[str, Any]
    description: str
    alert_contacts: list[str]
    metadata: dict[str, Any]


class WebhookDeliveryAttempt(TypedDict):
    object: Literal["webhook_delivery"]
    id: str
    event_id: str
    status: str
    note: str


class WebhookSecret(SealedSecrets):
    object: Literal["webhook_secret"]
    #: The current whsec_ signing secret.
    secret: str


class _WebhookSecretRotationRequired(TypedDict):
    object: Literal["webhook_secret"]
    secret: str


class WebhookSecretRotation(_WebhookSecretRotationRequired, SealedSecrets, total=False):
    warning: str
    #: The overlap applied, in seconds.
    overlap_seconds: int
    #: When the previous secret stops signing deliveries (epoch ms), or ``None`` when it
    #: already has.
    previous_secret_expires_at: int | None


# --------------------------------------------------------------------------- #
# Origin moves, connections, integrations, logout fan-out, managed email,      #
# back-channel deliveries, Sign in with Atlas publisher                        #
# --------------------------------------------------------------------------- #

#: ``instance.move_origin`` / ``atlas_id_apps.move_origin`` body. ``from`` is a Python
#: keyword, so this TypedDict uses the functional form: ``{"from": ..., "to": ...}``.
#: ``from`` / ``to`` are ``scheme://host[:port]`` origins; ``dry_run: True`` writes nothing.
_OriginMoveBodyRequired = TypedDict("_OriginMoveBodyRequired", {"from": str, "to": str})


class OriginMoveBody(_OriginMoveBodyRequired, total=False):
    dry_run: bool


class OriginMoveChange(TypedDict):
    object: Literal["instance", "oauth_client", "atlas_id_app", "webhook_endpoint", "redirect_url"]
    id: str
    #: e.g. ``allowed_origins``, ``redirect_uris``, ``homepage_url``.
    field: str
    before: str | list[str] | None
    after: str | list[str] | None


class OriginMoveProblem(TypedDict, total=False):
    object: str
    id: str
    field: str
    url: str
    message: str


_OriginMoveRequired = TypedDict(
    "_OriginMoveRequired",
    {
        "object": Literal["origin_move"],
        "from": str,
        "to": str,
        "dry_run": bool,
        "applied": bool,
        "changes": "list[OriginMoveChange]",
        "problems": "list[OriginMoveProblem]",
    },
)


class OriginMove(_OriginMoveRequired, total=False):
    """The before → after diff of an origin move. A repeated run returns no changes."""

    #: Platform app twin only: the app after the move.
    app: dict[str, Any]


class InstanceConnection(TypedDict):
    """One link from this instance to another platform, and its health."""

    object: Literal["connection"]
    kind: Literal["privacy_webhook", "cmp", "atlas_id_app", "jwt_template"]
    #: What was checked, e.g. ``privacy_webhook_delivery`` or ``cmp_site``.
    check: str
    ok: bool
    severity: Literal["error", "warning", "info"]
    subject: dict[str, str]
    #: What to do when ``ok`` is false.
    fix_hint: str | None
    last_checked_at: int
    #: Kind-specific facts.
    details: dict[str, Any]


class InstanceConnections(TypedDict):
    object: Literal["instance_connections"]
    #: False when any warning- or error-severity row is not ok.
    ok: bool
    checked_at: int
    data: list[InstanceConnection]


class _ChatlyIntegrationRequired(TypedDict):
    object: Literal["chatly_integration"]
    enabled: bool


class ChatlyIntegration(_ChatlyIntegrationRequired, total=False):
    """The Chatly connection (``enabled: False`` and nothing else when none is set)."""

    channel: str
    #: The template name to pass to ``getToken({ template: 'chatly' })``.
    template: Literal["chatly"]
    #: ``chatly:<channel>``.
    audience: str
    issuer: str
    jwks_url: str
    token_ttl_seconds: int
    identity_verification: dict[str, str]


class SetChatlyIntegrationBody(TypedDict):
    #: The chat channel public id (letters, digits, ``_`` and ``-``).
    channel: str


class ForumulateSpace(TypedDict):
    id: str
    #: Where the reader's browser redeems the token.
    redeem_url: str


class _ForumulateIntegrationRequired(TypedDict):
    object: Literal["forumulate_integration"]
    enabled: bool


class ForumulateIntegration(_ForumulateIntegrationRequired, total=False):
    """The Forumulate connection (``enabled: False`` and nothing else when none is set)."""

    org_id: str
    spaces: list[ForumulateSpace]
    audience: str
    issuer: str
    jwks_url: str
    token_ttl_seconds: int
    #: The external_jwt provider to store on each space.
    reader_auth_provider: dict[str, Any]


class _SetForumulateIntegrationBodyRequired(TypedDict):
    org_id: str
    #: 1-50 space ids, or ``{"id": ..., "redeem_url": ...}``.
    spaces: list[str | dict[str, Any]]


class SetForumulateIntegrationBody(_SetForumulateIntegrationBodyRequired, total=False):
    #: The token ``aud``. Default ``forumulate:<org_id>``.
    audience: str | None


class LogoutNotifyEndpoint(TypedDict, total=False):
    """A logout fan-out endpoint: gets the same ``logout_token`` as your OIDC apps."""

    object: Literal["logout_notify_endpoint"]
    id: str
    url: str
    #: The client_id this endpoint follows; ``None`` = instance-wide.
    oauth_client_id: str | None
    #: The ``aud`` its logout_tokens carry.
    audience: str
    description: str | None
    created_at: int
    updated_at: int


class _CreateLogoutNotifyEndpointBodyRequired(TypedDict):
    #: Public https endpoint.
    url: str


class CreateLogoutNotifyEndpointBody(_CreateLogoutNotifyEndpointBodyRequired, total=False):
    #: A client_id of this instance to follow; omit for instance-wide.
    oauth_client_id: str | None
    #: Default: the client_id when following a client, else the instance id.
    audience: str | None
    description: str | None


class UpdateLogoutNotifyEndpointBody(TypedDict, total=False):
    url: str
    audience: str | None
    description: str | None


class LogoutNotifyDelivery(TypedDict, total=False):
    object: Literal["logout_notify_delivery"]
    id: str
    sub: str
    #: ``None`` = a subject-wide logout (ban / deletion).
    sid: str | None
    status: Literal["pending", "success", "failed"]
    attempt_number: int
    http_status: int | None
    response_snippet: str | None
    next_retry_at: int | None
    delivered_at: int | None
    created_at: int


class ManagedEmailRecord(TypedDict, total=False):
    purpose: Literal["dkim", "spf", "return_path", "ownership", "dmarc", "other"]
    type: Literal["TXT", "MX", "CNAME"]
    #: Fully-qualified record name.
    name: str
    value: str
    priority: int
    status: str


class _ManagedEmailRequired(TypedDict):
    object: Literal["managed_email"]
    id: str
    from_address: str
    domain: str
    provider: str
    region: str | None
    #: ``not_started`` | ``pending`` | ``verified`` | ``failed`` | ``temporary_failure``.
    status: str
    verified: bool
    records: list[ManagedEmailRecord]
    #: Always ``None``: no Atlas sending limits apply; your provider account's own do.
    #: (Servers before 2026-10 sent ``{"hourly": int, "daily": int}``.)
    limits: dict[str, int] | None
    #: ``sent``, ``bounces``, ``complaints``, ``last_bounce_at``, ``last_complaint_at``.
    usage: dict[str, Any]
    #: ``your_provider_account`` (``shared_platform_account`` from servers before 2026-10).
    reputation: str
    #: ``{"provider": str, "token_set": bool}`` or ``None``; the token is never returned.
    dns: dict[str, Any] | None
    failure_reason: str | None
    last_checked_at: int | None
    verified_at: int | None
    created_at: int
    updated_at: int


class ManagedEmail(_ManagedEmailRequired, total=False):
    """Managed email: Atlas sets your sending domain up on your own Resend or Brevo account."""

    #: The email service the domain lives on (your own account there).
    backend: Literal["resend", "brevo"]
    #: Your email provider (mode ``managed_domain``) that holds the API key.
    provider_id: str | None
    #: Brevo, on create: whether the bounce / complaint webhook was registered on your account.
    feedback_webhook: Literal["registered", "not_registered"]

    #: Create only, with ``dns``: the zone and the records Atlas wrote.
    dns_result: dict[str, Any]
    next_step: str


class _ManagedEmailDnsInputRequired(TypedDict):
    provider: Literal["cloudflare"]
    #: A DNS API token with Zone Read and DNS Edit. Write-only.
    api_token: str


class ManagedEmailDnsInput(_ManagedEmailDnsInputRequired, total=False):
    #: Replace a conflicting existing record.
    overwrite: bool


class _CreateManagedEmailBodyRequired(TypedDict):
    #: Bare or ``"Name <address>"``; its domain becomes the sending domain.
    from_address: str


class ManagedEmailProviderKey(TypedDict):
    #: Your Resend (re_…) or Brevo (xkeysib-…) API key, with domain permissions. Write-only.
    api_key: str


class CreateManagedEmailBody(_CreateManagedEmailBodyRequired, total=False):
    #: Your own provider account Atlas sets the domain up on. With ``config``, unless
    #: ``provider_id`` is given.
    transport: Literal["resend", "brevo"]
    config: ManagedEmailProviderKey
    #: Instead of ``transport`` + ``config``: your configured Resend or Brevo email provider.
    provider_id: str
    #: Resend only.
    region: Literal["us-east-1", "eu-west-1", "sa-east-1", "ap-northeast-1"]
    dns: ManagedEmailDnsInput


class _ManagedEmailDeleteResultRequired(TypedDict):
    object: Literal["managed_email"]
    domain: str
    deleted: Literal[True]


class ManagedEmailDeleteResult(_ManagedEmailDeleteResultRequired, total=False):
    #: Whether the email provider that held the key (mode ``managed_domain``) was removed too.
    provider_removed: bool


class DevelopmentEmailLimits(TypedDict):
    daily: int
    per_recipient_hourly: int


class _DevelopmentEmailRequired(TypedDict):
    object: Literal["development_email"]
    #: Your email provider, in development mode.
    provider_id: str
    enabled: Literal[True]
    #: Whether mail goes out through it now. Always ``False`` on a production instance.
    active: bool
    #: ``resend``, ``ses``, ``smtp``, ``brevo`` or ``mailgun``.
    transport: str
    from_address: str | None
    #: Added to every subject: ``"[Atlas test] "``.
    subject_prefix: str
    #: The line added to the end of every message.
    footer: str
    #: The only emails it sends: Atlas's own sign-in templates.
    templates: list[str]
    limits: DevelopmentEmailLimits
    updated_at: int


class DevelopmentEmail(_DevelopmentEmailRequired, total=False):
    """Your own email provider in development mode (a development instance, no verified domain)."""

    #: Present for ``onboarding@resend.dev``: Resend delivers it only to your account address.
    note: str
    next_step: str


class EnableDevelopmentEmailBody(TypedDict, total=False):
    """``{"provider_id"}``, or ``transport`` + ``config`` exactly as ``set_email`` takes them."""

    #: The id of your configured email provider.
    provider_id: str
    transport: Literal["resend", "ses", "smtp", "brevo", "mailgun"]
    #: A sender your provider accepts without a verified domain. Default for Resend:
    #: ``onboarding@resend.dev``.
    from_address: str
    config: dict[str, Any]


class DevelopmentEmailDeleteResult(TypedDict):
    object: Literal["development_email"]
    deleted: Literal[True]
    provider_id: str
    mode: Literal["standard"]


class BackchannelLogoutDelivery(TypedDict, total=False):
    """One back-channel logout attempt. Atlas never follows redirects."""

    object: Literal["backchannel_logout_delivery"]
    id: str
    oauth_client_id: str | None
    #: The ended session (``sid_test_…`` for a test); ``None`` for "sign out everywhere".
    sid: str | None
    #: Sent by the test call; never retried.
    test: bool
    status: Literal["pending", "success", "failed"]
    attempt_number: int
    max_attempts: int
    http_status: int | None
    latency_ms: int | None
    #: ``backchannel_redirect_not_followed``, ``backchannel_http_error``,
    #: ``backchannel_timeout``, ``backchannel_network_error`` or ``backchannel_url_blocked``.
    error: str | None
    #: The absolute ``Location`` of a 3xx answer. Not followed.
    location: str | None
    response_snippet: str | None
    next_retry_at: int | None
    attempted_at: int | None
    delivered_at: int | None
    created_at: int


class BackchannelLogoutDeliveryList(TypedDict):
    object: Literal["list"]
    #: Newest first.
    data: list[BackchannelLogoutDelivery]
    has_more: bool
    #: Pass as ``starting_after`` for the next page.
    next_cursor: str | None


class BackchannelLogoutTest(TypedDict):
    """A test back-channel logout, sent now and recorded with ``test: True``."""

    object: Literal["backchannel_logout_test"]
    delivery_id: str
    #: True when the receiver answered 2xx.
    ok: bool
    sid: str
    status: int | None
    latency_ms: int | None
    error: str | None
    location: str | None
    #: Set when nothing was sent (private, loopback or non-https address).
    blocked_reason: str | None
    body_excerpt: str | None


class AtlasIdAppPreflight(TypedDict):
    object: Literal["preflight"]
    app_id: str
    #: True when there are no error-severity findings.
    ok: bool
    checked_at: int
    #: People who have approved the app.
    user_count: int
    findings: list[PreflightFindingsItem]


class AtlasIdAppAuthorizeRequests7d(TypedDict):
    """How the last 7 days' sign-ins started."""

    button: int
    js: int
    fedcm: int
    fallback: int
    unmarked: int


class AtlasIdAppPreflightDetail(AtlasIdAppPreflight, total=False):
    """The D08 fields of an app's setup check."""

    #: The page origins the Sign in with Atlas button script ran on in the last 7 days.
    button_rendered_origins: list[AtlasIdOriginSeen]
    #: How the last 7 days' sign-ins started.
    authorize_requests_7d: AtlasIdAppAuthorizeRequests7d
    #: Origins of sign-ins that came through the no-script fallback link.
    fallback_origins: list[AtlasIdOriginSeen]
    #: Whether the app's homepage references the button script (``None`` = could not check).
    homepage_includes_script: bool | None


class AtlasIdAppUser(TypedDict):
    """A person who has approved a Sign in with Atlas app."""

    object: Literal["atlas_id_user"]
    atlas_id_user: Literal[True]
    #: The user id as this app sees it (the id_token ``sub``).
    sub: str
    grant_id: str
    scopes: list[str]
    granted_at: int


class AtlasIdAppUserList(TypedDict):
    object: Literal["list"]
    data: list[AtlasIdAppUser]


class _AtlasIdGrantRevocationRequired(TypedDict):
    object: Literal["atlas_id_grant"]
    id: str
    sub: str
    revoked: Literal[True]


class AtlasIdGrantRevocation(_AtlasIdGrantRevocationRequired, total=False):
    tokens_revoked: int
    backchannel_logouts: int


class AtlasIdPublisherVerification(TypedDict):
    record_name: str
    record_type: Literal["TXT"]
    record_value: str


class _AtlasIdPublisherRequired(TypedDict):
    object: Literal["atlas_id_publisher"]
    name: str
    domain: str
    verified: bool
    skip_consent: bool
    verification: AtlasIdPublisherVerification


class AtlasIdPublisher(_AtlasIdPublisherRequired, total=False):
    """The account's Sign in with Atlas publisher (name + DNS-verified domain)."""

    verified_at: int | None
    last_checked_at: int | None
    created_at: int
    updated_at: int
    #: On ``verify`` only: whether the TXT record matched.
    record_found: bool


class _SetAtlasIdPublisherBodyRequired(TypedDict):
    #: Shown on consent screens once verified (up to 100 characters).
    name: str
    #: The host your apps' homepage_url lives on, e.g. ``example.com``.
    domain: str


class SetAtlasIdPublisherBody(_SetAtlasIdPublisherBodyRequired, total=False):
    skip_consent: bool


class UpdateAtlasIdPublisherBody(TypedDict):
    skip_consent: bool


class AtlasIdPublisherDeleteResult(TypedDict):
    object: Literal["atlas_id_publisher"]
    deleted: Literal[True]


# --------------------------------------------------------------------------- #
# App roles                                                                    #
# --------------------------------------------------------------------------- #


class _AppRoleRequired(TypedDict):
    object: Literal["app_role"]
    id: str
    key: str
    name: str
    description: str | None
    permissions: list[str]
    created_at: int
    updated_at: int


class AppRole(_AppRoleRequired, total=False):
    #: How many users hold the role (list and create only).
    users_count: int


class _CreateAppRoleRequired(TypedDict):
    #: 2-64 lowercase letters, digits, ``_`` or ``-``, starting with a letter.
    key: str
    name: str


class CreateAppRoleBody(_CreateAppRoleRequired, total=False):
    description: str | None
    #: ``resource:action`` keys (the ``org:`` namespace is reserved).
    permissions: list[str]


class UpdateAppRoleBody(TypedDict, total=False):
    name: str
    description: str | None
    permissions: list[str]


class UserAppRoles(TypedDict):
    object: Literal["user_app_roles"]
    user_id: str
    roles: list[AppRole]
    #: The ``app_roles`` session claim.
    role_keys: list[str]
    #: The union of the roles' permissions: the ``app_permissions`` session claim.
    permissions: list[str]


class SetUserAppRolesBody(TypedDict, total=False):
    """``roles`` replaces the whole set; ``add`` / ``remove`` change it. Send one form."""

    roles: list[str]
    add: list[str]
    remove: list[str]


# --------------------------------------------------------------------------- #
# Organization teams, org-scoped roles, slugs                                  #
# --------------------------------------------------------------------------- #


class Team(TypedDict):
    object: Literal["team"]
    id: str
    organization_id: str
    name: str
    description: str | None
    members_count: int
    created_at: int
    updated_at: int


class TeamBody(TypedDict, total=False):
    name: str
    description: str | None


class TeamMemberUser(TypedDict):
    id: str
    first_name: str | None
    last_name: str | None
    image_url: str | None


class TeamMember(TypedDict, total=False):
    object: Literal["team_membership"]
    team_id: str
    user_id: str
    user: TeamMemberUser
    deleted: bool


class OrgRole(TypedDict):
    object: Literal["role"]
    id: str
    key: str
    name: str
    description: str | None
    is_system: bool
    #: Set for the organization's own custom roles; ``None`` for instance roles.
    organization_id: str | None
    permissions: list[str]
    member_count: int
    created_at: int
    updated_at: int


class _CreateOrgRoleRequired(TypedDict):
    key: str
    name: str


class CreateOrgRoleBody(_CreateOrgRoleRequired, total=False):
    description: str | None
    permissions: list[str]


class UpdateOrgRoleBody(TypedDict, total=False):
    name: str
    description: str | None
    permissions: list[str]


class SlugCheck(TypedDict):
    object: Literal["organization_slug_check"]
    slug: str
    valid: bool
    available: bool


# --------------------------------------------------------------------------- #
# OAuth server: signing keys and initial access tokens                         #
# --------------------------------------------------------------------------- #


class SigningKey(TypedDict, total=False):
    object: Literal["signing_key"]
    kid: str
    alg: Literal["RS256", "ES256"]
    #: ``current`` signs new tokens; ``previous`` stays published until ``retires_at``.
    status: Literal["current", "previous"]
    #: ``main``, or ``secondary`` (the key of the other algorithm, for APIs set to it).
    role: Literal["main", "secondary"]
    #: Epoch ms.
    retires_at: int | None
    #: On the current main key: ``local``, or the KMS that holds its private half.
    provider: Literal["local", "aws_kms", "gcp_kms", "azure_key_vault"]


class SigningKeyProviderSettings(TypedDict, total=False):
    """Where the signing key lives; never carries credentials. ``config`` holds the
    non-secret settings (``None`` for ``local``); ``active`` is ``True`` when the current
    main key is in this KMS; ``key_version`` is the KMS key version tokens are signed
    with."""

    object: Literal["signing_key_provider"]
    id: str
    provider: Literal["local", "aws_kms", "gcp_kms", "azure_key_vault"]
    config: dict[str, Any] | None
    active: bool
    key_version: str | None
    last_verified_at: int | None
    created_at: int
    updated_at: int
    #: On a PUT / DELETE: the rotation onto (or off) the KMS key.
    rotation: SigningKeyRotation | None
    deleted: bool


class _SetSigningKeyProviderRequired(TypedDict):
    provider: Literal["aws_kms", "gcp_kms", "azure_key_vault"]
    config: dict[str, Any]
    credentials: dict[str, Any]


class SetSigningKeyProviderBody(_SetSigningKeyProviderRequired, total=False):
    """``aws_kms``: config ``{region, key_id?, alg?}``, credentials ``{access_key_id,
    secret_access_key, session_token?}``. ``gcp_kms``: config ``{crypto_key,
    key_version?}``, credentials ``{service_account_json}``. ``azure_key_vault``: config
    ``{vault_url, key_name, key_version?, alg?}``, credentials ``{tenant_id, client_id,
    client_secret}``. Without a key id / version Atlas creates a new key version."""

    #: How long the previous key stays published (default 86400, at most 2592000).
    grace_period_seconds: int
    #: Publish only the new key now.
    emergency: bool


class WalletRpcSecret(TypedDict):
    object: Literal["wallet_rpc_secret"]
    chain_id: int
    set: bool


class SigningKeyList(TypedDict):
    object: Literal["list"]
    data: list[SigningKey]


class RotateSigningKeyBody(TypedDict, total=False):
    alg: Literal["RS256", "ES256"]
    #: Default 86400, at most 2592000.
    grace_period_seconds: int
    #: Publish ONLY the new key: every token signed by the old one stops verifying.
    emergency: bool


class SigningKeyRotation(TypedDict):
    object: Literal["signing_key_rotation"]
    kid: str
    alg: Literal["RS256", "ES256"]
    previous_kid: str | None
    previous_retires_at: int | None
    emergency: bool


class _InitialAccessTokenRequired(TypedDict):
    object: Literal["oauth_initial_access_token"]
    id: str
    token_prefix: str
    description: str | None
    status: Literal["active", "expired", "used_up", "revoked"]
    max_uses: int | None
    use_count: int
    expires_at: int | None
    revoked_at: int | None
    last_used_at: int | None
    created_at: int


class InitialAccessToken(_InitialAccessTokenRequired, total=False):
    #: Returned once, on create.
    token: str


class CreateInitialAccessTokenBody(TypedDict, total=False):
    description: str
    expires_in_seconds: int
    max_uses: int


# --------------------------------------------------------------------------- #
# Custom OAuth / OIDC providers (Atlas as the relying party)                   #
# --------------------------------------------------------------------------- #

#: Token-endpoint client authentication to the upstream provider.
TokenEndpointAuthMethod = Literal[
    "client_secret_basic", "client_secret_post", "client_secret_jwt", "private_key_jwt", "none"
]

#: A claim path (``"emails[0].value"``, ``"$id_token.sub"``), a ``"{{template}}"``, or a
#: rule ``{from, template, value, transforms}``.
ProfileMappingExpr = Any


class ProfileMapping(TypedDict, total=False):
    """``fields`` keys: id, email, email_verified, first_name, last_name, full_name,
    username, image_url, phone_number, external_id. ``update_on_sign_in`` re-applies
    names, image and metadata on every sign-in (default: at account creation)."""

    fields: dict[str, ProfileMappingExpr]
    public_metadata: dict[str, ProfileMappingExpr]
    private_metadata: dict[str, ProfileMappingExpr]
    update_on_sign_in: bool


class UpstreamLogoutSettings(TypedDict, total=False):
    #: On Atlas sign-out, hand back the provider end-session URL to send the browser to.
    rp_initiated: bool
    post_logout_redirect_url: str | None
    #: Accept OIDC Back-Channel Logout tokens and end the matching Atlas sessions.
    backchannel: bool
    #: Accept OIDC Front-Channel Logout (the provider frames ``frontchannel_logout_uri``).
    frontchannel: bool
    #: Front-channel: require ``iss`` + ``sid`` (default ``True``).
    frontchannel_session_required: bool
    end_session_endpoint: str | None


class IdpInitiatedLoginSettings(TypedDict, total=False):
    enabled: bool
    #: Exact URLs or bare origins a third-party initiated login may land on.
    allowed_targets: list[str]
    default_target: str | None


class UpstreamSigningKey(TypedDict):
    object: Literal["upstream_signing_key"]
    kid: str
    alg: Literal["RS256", "PS256", "ES256"]
    status: Literal["active", "retiring", "retired"]
    public_jwk: dict[str, Any]
    created_at: int
    retired_at: int | None


class UpstreamUrls(TypedDict):
    #: Register at the provider as the client JWKS URL (private_key_jwt).
    client_jwks_uri: str
    backchannel_logout_uri: str
    frontchannel_logout_uri: str
    post_logout_redirect_uri: str
    initiate_login_uri: str


class CustomOAuthProviderSettings(TypedDict, total=False):
    display_name: str
    icon_url: str | None
    protocol: Literal["oidc", "oauth2"]
    issuer: str | None
    discovery_url: str | None
    authorization_endpoint: str | None
    token_endpoint: str | None
    userinfo_endpoint: str | None
    jwks_uri: str | None
    end_session_endpoint: str | None
    scopes: list[str]
    scope_separator: Literal[" ", ",", "+"]
    pkce: bool
    authorization_params: dict[str, str] | None
    token_params: dict[str, str] | None
    userinfo_auth: Literal["header", "query"]
    token_endpoint_auth_method: TokenEndpointAuthMethod
    client_assertion_audience: str | None
    profile_source: Literal["merged", "userinfo", "id_token"]
    profile_mapping: ProfileMapping | None
    logout: UpstreamLogoutSettings | None
    idp_initiated_login: IdpInitiatedLoginSettings | None
    client_id: str
    #: Write-only; never returned.
    client_secret: str
    enabled: bool
    allow_sign_in: bool
    allow_sign_up: bool


class CreateCustomOAuthProviderBody(CustomOAuthProviderSettings, total=False):
    """``provider_key`` and ``display_name`` are required on create."""

    provider_key: str


class CustomOAuthProvider(UpstreamUrls):
    object: Literal["custom_oauth_provider"]
    id: str
    provider_key: str
    display_name: str
    icon_url: str | None
    protocol: Literal["oidc", "oauth2"]
    issuer: str | None
    discovery_url: str | None
    authorization_endpoint: str | None
    token_endpoint: str | None
    userinfo_endpoint: str | None
    jwks_uri: str | None
    end_session_endpoint: str | None
    scopes: list[str]
    scope_separator: str
    pkce: bool
    authorization_params: dict[str, str]
    token_params: dict[str, str]
    userinfo_auth: Literal["header", "query"]
    token_endpoint_auth_method: TokenEndpointAuthMethod
    client_assertion_audience: str | None
    profile_source: Literal["merged", "userinfo", "id_token"]
    profile_mapping: ProfileMapping | None
    logout: UpstreamLogoutSettings
    idp_initiated_login: IdpInitiatedLoginSettings
    client_id: str | None
    has_secret: bool
    enabled: bool
    allow_sign_in: bool
    allow_sign_up: bool
    #: Register at the provider as the redirect / callback URI.
    redirect_uri: str
    signing_keys: list[UpstreamSigningKey]
    created_at: int
    updated_at: int


class ProfileMappingPreviewBody(TypedDict, total=False):
    profile_mapping: ProfileMapping
    userinfo: dict[str, Any]
    id_token_claims: dict[str, Any]
    #: A sample id_token — decoded, not verified.
    id_token: str


class ProfileMappingPreview(TypedDict):
    object: Literal["profile_mapping_preview"]
    profile: dict[str, Any]
    #: Per target: ``{value, source}``.
    trace: dict[str, dict[str, Any]]
    warnings: list[str]


class OidcDiscoveryResult(TypedDict, total=False):
    object: Literal["oidc_discovery"]
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str | None
    jwks_uri: str
    end_session_endpoint: str | None
    scopes_supported: list[str]
    claims_supported: list[str]
    token_endpoint_auth_methods_supported: list[str]
    token_endpoint_auth_signing_alg_values_supported: list[str]
    code_challenge_methods_supported: list[str]
    backchannel_logout_supported: bool
    backchannel_logout_session_supported: bool


# --------------------------------------------------------------------------- #
# Actions gallery                                                              #
# --------------------------------------------------------------------------- #


class ActionTemplateSecret(TypedDict):
    """A secret a template reads, declared by NAME; values are never part of a template."""

    name: str
    description: str
    required: bool


class ActionGalleryEntry(TypedDict, total=False):
    object: Literal["action_template"]
    source: Literal["builtin", "community"]
    slug: str
    name: str
    summary: str
    trigger: str
    category: str
    tags: list[str]
    #: SPDX licence id.
    license: str
    author: dict[str, Any]
    verified: bool
    featured: bool
    install_count: int
    latest_version: str
    #: The code sends outbound requests with ``api.http``.
    uses_http: bool
    secrets: list[ActionTemplateSecret]
    updated_at: int | None
    #: On the detail view.
    description: str
    code: str
    changelog: str | None
    repository_url: str | None
    versions: list[dict[str, Any]]


class InstallTemplateBody(TypedDict, total=False):
    #: A specific approved version (default: the latest).
    version: str
    #: The action's name (default: the template's).
    name: str
    #: Values for the secrets the template declares. Write-only.
    secrets: dict[str, str]


class ActionGalleryInstallResult(TypedDict):
    object: Literal["action_gallery_install"]
    #: The new action: disabled and not bound to any flow yet.
    action: dict[str, Any]
    template: dict[str, Any]
    install_id: str
    #: Required secrets you have not supplied yet.
    missing_secrets: list[str]


class ActionGalleryUpdateResult(TypedDict, total=False):
    object: Literal["action_gallery_update"]
    #: ``False`` when the action already runs the latest version.
    updated: bool
    action: dict[str, Any]
    from_version: str
    version: str


class ActionTemplateVersion(TypedDict, total=False):
    object: Literal["action_template_version"]
    version: str
    status: Literal["draft", "pending_review", "approved", "rejected"]
    trigger: str
    secrets: list[ActionTemplateSecret]
    changelog: str | None
    #: Why staff rejected it, when they did.
    review_note: str | None
    code: str
    submitted_at: int | None
    reviewed_at: int | None
    created_at: int


class ActionTemplate(TypedDict, total=False):
    """A template this instance publishes."""

    object: Literal["action_template"]
    id: str
    slug: str
    name: str
    author_name: str
    summary: str
    description: str | None
    category: str
    tags: list[str]
    trigger: str
    license: str
    repository_url: str | None
    status: Literal["draft", "in_review", "published", "unlisted", "rejected", "banned"]
    latest_version: str | None
    verified: bool
    featured: bool
    install_count: int
    view_count: int
    published_at: int | None
    created_at: int
    updated_at: int
    versions: list[ActionTemplateVersion]


class ActionTemplateListing(TypedDict, total=False):
    slug: str
    name: str
    #: Shown as the author on the gallery.
    author_name: str
    summary: str
    #: Markdown.
    description: str
    category: str
    tags: list[str]
    trigger: str
    #: SPDX id (MIT, Apache-2.0, BSD-3-Clause, ISC, MPL-2.0, …).
    license: str
    repository_url: str | None


class CreateActionTemplateBody(ActionTemplateListing, total=False):
    """``slug``, ``name``, ``author_name`` and ``trigger`` are required; the first
    version may come in the same call."""

    version: str
    code: str
    secrets: list[ActionTemplateSecret]
    changelog: str
    #: Send to review right away.
    submit: bool


class _NewTemplateVersionRequired(TypedDict):
    #: MAJOR.MINOR.PATCH, higher than every existing version.
    version: str
    code: str


class NewTemplateVersionBody(_NewTemplateVersionRequired, total=False):
    secrets: list[ActionTemplateSecret]
    changelog: str
    submit: bool


# --------------------------------------------------------------------------- #
# Migrate from Better Auth: sealed-bundle imports and the session bridge      #
# --------------------------------------------------------------------------- #

BetterAuthImportStatus = Literal[
    "uploading", "analyzing", "ready", "invalid", "queued", "applying", "completed", "failed"
]


class BetterAuthImportKey(TypedDict, total=False):
    """The X25519 key the Better Auth exporter seals a bundle to."""

    object: Literal["better_auth_import_key"]
    kid: str
    #: base64url raw X25519 public key.
    public_key: str
    alg: Literal["X25519-HKDF-SHA256-A256GCM"]
    status: Literal["active", "retired"]
    #: SHA-256 of the raw key, first 16 bytes as hex pairs.
    fingerprint: str
    #: ``kid:public_key`` — the form the exporter's ``--public-key`` takes.
    compact: str
    created_at: int
    retired_at: int | None


class BetterAuthImportOptions(TypedDict, total=False):
    models: list[str]
    on_email_conflict: Literal["skip", "link"]
    default_role: str
    create_app_roles: bool
    import_oauth_tokens: bool
    passkeys_on_rp_mismatch: Literal["skip", "import"]
    import_subscriptions: bool
    plan_map: dict[str, str]
    import_jwks: bool
    #: 1–365, default 30.
    jwks_cutover_days: int
    import_sessions: bool
    retain_bundle: bool


class CreateBetterAuthImportBody(TypedDict, total=False):
    options: BetterAuthImportOptions


class ApplyBetterAuthImportBody(TypedDict, total=False):
    #: Required when the dry run reported conflicts.
    confirm_conflicts: bool


class BetterAuthImportActionItem(TypedDict, total=False):
    code: str
    #: Only ``required`` should block: those rows stay out until fixed and re-run.
    severity: Literal["required", "recommended", "info"]
    message: str
    count: int
    items: list[str]


class BetterAuthImportProgress(TypedDict, total=False):
    total: int
    processed: int
    succeeded: int
    failed: int
    percent: int


class BetterAuthImportError(TypedDict, total=False):
    #: bundle_malformed | bundle_unsupported | bundle_wrong_key | bundle_tampered |
    #: bundle_truncated | bundle_count_mismatch | import_key_retired | analysis_failed |
    #: apply_failed
    code: str
    message: str


class BetterAuthImport(TypedDict, total=False):
    """One Better Auth bundle import: ``uploading → analyzing → ready | invalid →
    queued → applying → completed | failed``."""

    object: Literal["better_auth_import"]
    id: str
    status: BetterAuthImportStatus
    key_id: str | None
    parts: int
    bytes: int
    bundle_sha256: str | None
    bundle_purged: bool
    options: BetterAuthImportOptions
    #: The exporter's manifest (Better Auth version, plugins, models, rp_id, ...).
    source: dict[str, Any] | None
    total: int
    progress: BetterAuthImportProgress | None
    #: The dry run: ``models``, ``skipped``, ``conflicts``, ``action_items``, ...
    report: dict[str, Any] | None
    #: The apply outcome: per-model created/updated/unchanged/skipped/failed.
    result: dict[str, Any] | None
    error: BetterAuthImportError | None
    created_at: int
    updated_at: int
    analyzed_at: int | None
    apply_started_at: int | None
    completed_at: int | None


class BetterAuthImportPart(TypedDict, total=False):
    object: Literal["better_auth_import_part"]
    import_id: str
    part: int
    bytes: int
    sha256: str


class BetterAuthImportDeleted(TypedDict, total=False):
    object: Literal["better_auth_import"]
    id: str
    deleted: bool


class ImportedJwk(TypedDict, total=False):
    """A Better Auth JWT key published in the instance JWKS for the cutover."""

    object: Literal["imported_jwk"]
    kid: str
    source: str
    jwk: dict[str, Any]
    import_id: str | None
    expires_at: int | None
    created_at: int


class ImportedJwkDeleted(TypedDict, total=False):
    object: Literal["imported_jwk"]
    kid: str
    deleted: bool


class BetterAuthLiveFallbackBody(TypedDict, total=False):
    enabled: bool
    #: The old app's Better Auth base URL including its base path
    #: (``https://app.example.com/api/auth``).
    base_url: str | None
    #: The old app's ``BETTER_AUTH_SECRET``. Write-only: omit to keep, ``None`` to clear.
    secret: str | None


class UpdateBetterAuthBridgeBody(TypedDict, total=False):
    enabled: bool
    #: End of the migration window (ISO-8601 or epoch ms); ``None`` = open until disabled.
    ends_at: str | int | None
    #: Better Auth's ``advanced.cookiePrefix`` (default ``better-auth``).
    cookie_prefix: str
    live_fallback: BetterAuthLiveFallbackBody


class BetterAuthBridgeSettings(TypedDict, total=False):
    object: Literal["better_auth_bridge"]
    enabled: bool
    ends_at: int | None
    cookie_prefix: str
    #: ``{enabled, base_url, has_secret}`` — never the secret.
    live_fallback: dict[str, Any]
    exchange_path: str
    #: ``{exchanged, from_import, from_live}``.
    stats: dict[str, int]
    created_at: int | None
    updated_at: int | None


class BetterAuthBridgeDeleted(TypedDict, total=False):
    object: Literal["better_auth_bridge"]
    deleted: bool


class BetterAuthExchangeResponse(TypedDict, total=False):
    #: ``session_tokens``, or ``sign_in_attempt`` when a second factor is still owed.
    object: Literal["session_tokens", "sign_in_attempt"]
    #: sign_in_attempt only: the attempt to continue.
    id: str
    session_id: str
    user_id: str
    jwt: str
    refresh_token: str
    expires_in: int
    status: Literal["needs_second_factor", "needs_mfa_enrollment"]


# --------------------------------------------------------------------------- #
# Policy acceptance                                                            #
# --------------------------------------------------------------------------- #

PolicyDisplay = Literal["checkbox", "scroll", "link"]
PolicyAppliesTo = Literal["sign_up", "sign_in_and_sign_up"]
PolicyReaccept = Literal["none", "next_sign_in", "grace"]


class PolicyVersionRef(TypedDict):
    """A policy's current, upcoming or latest version."""

    id: str
    version: str
    #: ``draft``, ``published`` or ``retired``.
    status: str
    content_sha256: str
    published_at: int | None
    effective_at: int | None


class Policy(TypedDict):
    """A policy (Terms of Service, privacy policy, any key) users accept."""

    object: Literal["policy"]
    id: str
    key: str
    title: str
    display: PolicyDisplay
    required: bool
    applies_to: PolicyAppliesTo
    reaccept: PolicyReaccept
    grace_days: int | None
    #: ``atlas`` or ``external`` (synced from a policy source).
    source: str
    position: int
    #: ``active`` or ``retired``.
    status: str
    #: External policies: the fields changed in Atlas that a sync keeps.
    overrides: list[str]
    #: The version in effect now.
    current_version: PolicyVersionRef | None
    #: A newer published version that is not in effect yet.
    upcoming_version: PolicyVersionRef | None
    #: The newest version of any status (drafts included).
    latest_version: PolicyVersionRef | None
    retired_at: int | None
    created_at: int
    updated_at: int


class _PolicyVersionRequired(TypedDict):
    object: Literal["policy_version"]
    id: str
    policy_id: str
    policy: str
    version: str
    #: ``draft``, ``published`` or ``retired``.
    status: str
    content_markdown: str | None
    #: The sanitised HTML clients render.
    content_html: str
    content_url: str | None
    #: Hex SHA-256 of ``content_html``.
    content_sha256: str
    summary_of_changes: str | None
    locale: str | None
    published_at: int | None
    effective_at: int | None
    retired_at: int | None
    created_at: int
    updated_at: int


class PolicyVersion(_PolicyVersionRequired, total=False):
    #: On a list: how many users accepted this version.
    acceptance_count: int


class PolicyAcceptance(TypedDict):
    """One acceptance (or withdrawal) with its evidence."""

    object: Literal["policy_acceptance"]
    id: str
    user_id: str
    policy: str
    version: str
    policy_version_id: str | None
    #: ``accepted`` or ``withdrawn``.
    status: str
    #: ``signup``, ``signin``, ``reaccept``, ``api``, ``import`` or another string.
    source: str | None
    content_sha256: str | None
    display: PolicyDisplay | None
    scrolled_to_end: bool | None
    view_ms: int | None
    locale: str | None
    ip: str | None
    user_agent: str | None
    accepted_at: int


class PolicyStanding(TypedDict):
    """A user's standing on one policy."""

    object: Literal["policy_standing"]
    policy: str
    policy_id: str
    title: str
    display: PolicyDisplay
    required: bool
    applies_to: PolicyAppliesTo
    reaccept: PolicyReaccept
    current_version_id: str | None
    current_version: str | None
    content_sha256: str | None
    summary_of_changes: str | None
    accepted_version_id: str | None
    accepted_version: str | None
    accepted_at: int | None
    needs_reaccept: bool
    #: Accepting is required before the user's next sign-in completes.
    blocking: bool
    grace_ends_at: int | None


class _UserPoliciesRequired(TypedDict):
    object: Literal["list"]
    user_id: str
    data: list[PolicyStanding]
    needs_acceptance: bool


class UserPolicies(_UserPoliciesRequired, total=False):
    """``GET /v1/users/{id}/policies``: the user's standing on every policy."""


class _CreatePolicyBodyRequired(TypedDict):
    #: Slug, unique per instance (``tos``, ``privacy``). Becomes the consent record's ``policy``.
    key: str
    title: str


class CreatePolicyBody(_CreatePolicyBodyRequired, total=False):
    display: PolicyDisplay
    required: bool
    applies_to: PolicyAppliesTo
    reaccept: PolicyReaccept
    #: Required with ``reaccept: "grace"`` (1-365).
    grace_days: int | None
    position: int


class UpdatePolicyBody(TypedDict, total=False):
    """``PATCH /v1/policies/{id}``. The key cannot change."""

    title: str
    display: PolicyDisplay
    required: bool
    applies_to: PolicyAppliesTo
    reaccept: PolicyReaccept
    grace_days: int | None
    position: int
    #: ``retired`` stops it gating (history is kept); ``active`` brings it back.
    status: Literal["active", "retired"]


class _CreatePolicyVersionBodyRequired(TypedDict):
    #: A label such as ``2026-10-24`` or ``1.2.0``, unique per policy.
    version: str


class CreatePolicyVersionBody(_CreatePolicyVersionBodyRequired, total=False):
    #: Markdown (rendered and sanitised by Atlas) - or ``content_html``.
    content_markdown: str
    content_html: str
    content_url: str | None
    summary_of_changes: str | None
    locale: str | None
    #: Publish immediately instead of saving a draft.
    publish: bool
    #: With ``publish``: when the gate starts asking for it (epoch ms or ISO; default now).
    effective_at: int | str


class UpdatePolicyVersionBody(TypedDict, total=False):
    """``PATCH /v1/policies/{id}/versions/{versionId}`` (drafts only)."""

    version: str
    content_markdown: str
    content_html: str
    content_url: str | None
    summary_of_changes: str | None
    locale: str | None


class PublishPolicyVersionBody(TypedDict, total=False):
    #: When the gate starts asking for it (epoch ms or ISO; default now).
    effective_at: int | str


class PolicySettings(TypedDict):
    object: Literal["policy_settings"]
    #: Put ``pol`` (the accepted versions of required policies) on session tokens.
    session_claim: bool


class UpdatePolicySettingsBody(TypedDict, total=False):
    session_claim: bool


class PolicySource(TypedDict):
    """The external policy source (Atlas policy source protocol v1). The signing
    secret is never returned, only ``signing_secret_set``."""

    object: Literal["policy_source"]
    enabled: bool
    endpoint_url: str | None
    signing_secret_set: bool
    #: ``webhook`` or ``poll``.
    sync: str
    poll_interval_minutes: int
    #: Where your source sends ``policy.published`` / ``policy.retired`` events.
    webhook_url: str | None
    protocol_version: str
    last_synced_at: int | None
    last_sync_ok: bool | None
    last_sync_error: str | None
    next_poll_at: int | None


class UpdatePolicySourceBody(TypedDict, total=False):
    """``PUT /v1/instance/policy_source``: only the fields sent change, ``None`` clears.
    Enabling needs ``endpoint_url`` and ``signing_secret``."""

    enabled: bool
    #: Base URL; Atlas calls ``GET {endpoint_url}/policies``.
    endpoint_url: str | None
    #: Write-only (a ``whsec_`` secret works).
    signing_secret: str | None
    #: ``webhook`` or ``poll``.
    sync: Literal["webhook", "poll"]
    #: Poll mode: 5-1440.
    poll_interval_minutes: int


class PolicySourceDelivery(TypedDict):
    object: Literal["policy_source_delivery"]
    id: str
    #: ``outbound`` or ``inbound``.
    direction: str
    #: ``fetch``, ``test``, ``poll`` or ``webhook``.
    kind: str
    #: ``ok``, ``failed`` or ``rejected``.
    status: str
    http_status: int | None
    error: str | None
    event_type: str | None
    policy: str | None
    version: str | None
    url: str | None
    changes: dict[str, Any] | None
    latency_ms: int | None
    created_at: int


class PolicySourceFeedSummary(TypedDict):
    key: str
    title: str
    versions: list[str]


class _PolicySourceTestRequired(TypedDict):
    object: Literal["policy_source_test"]
    ok: bool


class PolicySourceTest(_PolicySourceTestRequired, total=False):
    """``POST /v1/instance/policy_source/test``: a signed fetch, validated, not stored."""

    http_status: int | None
    latency_ms: int | None
    error: str | None
    warnings: list[str]
    policies: list[PolicySourceFeedSummary]
    delivery: PolicySourceDelivery


class PolicySourceChanges(TypedDict, total=False):
    created: list[str]
    updated: list[str]
    published: list[str]
    unchanged: list[str]
    rejected: list[str]
    retired: list[str]


class _PolicySourceSyncRequired(TypedDict):
    object: Literal["policy_source_sync"]
    ok: bool


class PolicySourceSync(_PolicySourceSyncRequired, total=False):
    """``POST /v1/instance/policy_source/sync``: fetch the feed now and store it."""

    error: str | None
    warnings: list[str]
    changes: PolicySourceChanges | None
    delivery: PolicySourceDelivery


# --------------------------------------------------------------------------- #
# Credentials: secret keys, platform keys, partner links                       #
# --------------------------------------------------------------------------- #


class SecretKey(TypedDict, SealedSecrets, total=False):
    """A secret key (``/v1/secret_keys``). The secret itself (``secret``, or
    ``sealed_secret`` when ``secret_recipient`` was sent) is returned once, on create and
    rotate."""

    object: Literal["secret_key"]
    id: str
    name: str
    prefix: str
    scopes: list[str]
    #: Who the key belongs to: ``user:<id>``, ``api_key:<id>`` or ``platform_key:<id>``.
    #: Defaults to the creator.
    owner: str | None
    #: When the key stops working (epoch ms). New keys default to one year; ``null`` is
    #: refused at create.
    expires_at: int | None
    #: Browser origins the key may be used from, enforced when a request carries an
    #: ``Origin`` header (a refusal is ``ORIGIN_NOT_ALLOWED``). Exact origins or a
    #: one-level wildcard such as ``https://*.example.com``.
    allowed_origins: list[str]
    allowed_ips: list[str]
    metadata: dict[str, Any]
    external_ref: str | None
    status: str
    created_at: int
    revoked_at: int | None
    last_used_at: int | None
    secret: str
    sealed_secret: str
    idempotent_replay: bool


class CreateSecretKeyBody(TypedDict, total=False):
    name: str
    scopes: list[str]
    #: Defaults to the creator (``user:<id>`` / ``api_key:<id>`` / ``platform_key:<id>``).
    owner: str
    #: Epoch ms or an ISO date; at most one year out. ``null`` and ``"never"`` are refused.
    expires_at: int | str
    #: Browser origins the key is locked to (``origin_allowlist`` is accepted as an alias).
    allowed_origins: list[str]
    allowed_ips: list[str]
    #: ``"atlas"`` (default, ``atlas_<env>_sk_...``) or ``"legacy"`` (``sk_...``).
    key_format: Literal["atlas", "legacy"]
    #: ``x25519:<base64 public key>``: the secret comes back sealed to it.
    secret_recipient: str
    external_ref: str
    metadata: dict[str, Any]


class UpdateSecretKeyBody(TypedDict, total=False):
    name: str
    owner: str
    expires_at: int | str
    allowed_origins: list[str]
    allowed_ips: list[str]
    metadata: dict[str, Any]


class PlatformKey(TypedDict, SealedSecrets, total=False):
    """A platform key (``psk``) as listed by ``platform.keys``."""

    object: str
    id: str
    name: str
    prefix: str
    scopes: list[str]
    owner: str | None
    expires_at: int | None
    allowed_origins: list[str]
    status: str
    created_at: int
    revoked_at: int | None
    last_used_at: int | None


class PartnerLink(TypedDict, total=False):
    object: Literal["partner_link"]
    id: str
    client_id: str
    #: Any lowercase id; ``cookiemunch``, ``chatly``, ``forumulate`` and ``referalli`` are presets.
    partner: str
    name: str
    preset: bool
    resource: str
    scopes: list[str]
    client_secret_prefix: str
    token_endpoint: str
    #: mTLS: client-certificate SHA-256 fingerprints (base64url) every use must present.
    cert_fingerprints: list[str]
    auth_methods: list[str]
    #: The partner link request this link was approved from; ``None`` when created by hand.
    request_id: str | None
    status: Literal["active", "expired", "revoked"]
    expires_at: int | None
    revoked_at: int | None
    last_used_at: int | None
    last_used_ip: str | None
    calls_30d: int
    created_at: int
    client_secret: str
    sealed_client_secret: str


class PartnerLinkRequest(TypedDict, total=False):
    """A partner link request: a partner asking this instance (``inbound``), or Atlas asking a
    partner (``outbound``)."""

    object: Literal["partner_link_request"]
    id: str
    direction: Literal["inbound", "outbound"]
    partner: str
    name: str
    preset: bool
    resource: str | None
    scopes: list[str]
    callback_url: str | None
    callback_host: str | None
    cert_fingerprints: list[str]
    status: Literal[
        "pending", "approved", "denied", "expired", "delivery_failed", "installed", "failed"
    ]
    link_id: str | None
    remote_request_id: str | None
    decided_by: str | None
    decided_at: int | None
    delivery_attempts: int
    delivered_at: int | None
    last_error: str | None
    expires_at: int
    created_at: int


class PartnerLinkRequestApproval(PartnerLinkRequest, total=False):
    #: Whether Atlas delivered the credentials to the partner's callback.
    delivered: bool
    link: PartnerLink | None
    note: str


class ApprovePartnerLinkRequestBody(TypedDict, total=False):
    #: Narrow the requested scopes (never wider than the request, nor than your own).
    scopes: list[str]
    expires_at: int | str


class PartnerLinkRequestInput(TypedDict, total=False):
    """What a partner product sends to ``request_partner_link``."""

    #: Your product id (lowercase, 2-40 characters).
    partner: str
    name: str
    #: The Atlas instance: its ``ins_...`` id or publishable key.
    resource: str
    scopes: list[str]
    #: Where Atlas delivers the credentials (https).
    callback_url: str
    state: str
    #: Ask for a certificate-locked (mTLS) link.
    cert_fingerprints: list[str]


class PartnerLinkRequestCreated(TypedDict, total=False):
    object: Literal["partner_link_request"]
    protocol: str
    id: str
    status: Literal["pending"]
    resource: str
    scopes: list[str]
    #: Keep it: it verifies the delivery and reads the request. Shown once.
    request_secret: str
    expires_at: int


class OidcOrganization(TypedDict):
    """The organization a sign-in was made in (the ID token's ``org_*`` claims)."""

    id: str
    slug: str
    role: str
    permissions: list[str]


class OidcOrganizationMembership(TypedDict):
    """One entry of the ``orgs`` claim (the ``organizations`` scope)."""

    id: str
    slug: str
    role: str


class OidcSsoContext(TypedDict):
    """The enterprise SSO context of a sign-in (the ID token's ``sso_*`` claims)."""

    connection_id: str
    #: The Atlas organization that owns the connection (``sso_organization_id``), or ``None``
    #: for an instance-wide connection. Independent of ``org_id``.
    organization_id: str | None
    #: The connection protocol (``sso_connection_type``).
    type: Literal["saml", "oidc"] | None
    tenant_id: str | None
    issuer: str | None
    domain: str | None


# --------------------------------------------------------------------------- #
# Partner platforms, per-call audiences, privacy orchestrator, operator        #
# --------------------------------------------------------------------------- #


class PartnerPlatformRegistrationState(TypedDict):
    status: Literal["unregistered", "registered"]
    registered_at: int | None


class PartnerPlatform(TypedDict, total=False):
    """A product that signs its partner deliveries with a published Ed25519 key set. The
    partner token is write-only: only ``token_set`` and ``token_prefix`` are ever returned."""

    object: Literal["partner_platform"]
    id: str
    partner: str
    name: str
    preset: bool
    platform_id: str
    enabled: bool
    jwks_url: str
    signature_header: str
    signature_scheme: Literal["t_kid_ed25519"]
    tolerance_seconds: int
    allowed_sources: list[str]
    record_consents: bool
    receiver_url: str
    receiver_url_template: str
    serves_deployment: bool
    registration: PartnerPlatformRegistrationState
    token_set: bool
    token_prefix: str | None
    last_delivery_at: int | None
    last_delivery_error: str | None
    created_at: int
    updated_at: int


class PartnerPlatformList(TypedDict, total=False):
    object: str
    data: list[PartnerPlatform]
    has_more: bool
    #: The ready-made partner defaults a ``partner`` id can pick.
    presets: list[dict[str, Any]]


class PartnerPlatformInput(TypedDict, total=False):
    """Body of ``partner_platforms.set``; every field is optional (a preset fills defaults)."""

    name: str | None
    platform_id: str
    enabled: bool
    jwks_url: str
    signature_header: str
    signature_scheme: Literal["t_kid_ed25519"]
    tolerance_seconds: int
    allowed_sources: list[str]
    record_consents: bool
    serves_deployment: bool


class PartnerPlatformDeleted(TypedDict):
    object: Literal["partner_platform"]
    partner: str
    deleted: Literal[True]


class PartnerPlatformSignature(TypedDict):
    header: str
    scheme: str
    format: str
    jwks_url: str
    tolerance_seconds: int


class PartnerPlatformSendTo(TypedDict):
    contact: str
    docs: str


class PartnerPlatformRegistration(TypedDict):
    """What to send the partner so it can register this instance as a receiver."""

    object: Literal["partner_platform_registration"]
    partner: str
    platform_id: str
    receiver_url: str
    receiver_url_is_template: bool
    external_id: str | None
    events: list[str]
    signature: PartnerPlatformSignature
    send_to: PartnerPlatformSendTo | None
    token_prefix: str | None
    next_step: str


class PartnerDelivery(TypedDict):
    object: Literal["partner_delivery"]
    event_id: str | None
    event_type: str | None
    outcome: Literal[
        "recorded", "unchanged", "no_subject", "no_user", "source_not_allowed", "ignored"
    ]
    user_id: str | None
    received_at: int


class PerCallAudience(TypedDict, total=False):
    """An integration's ``per_call_audience``: ``sessions.get_token(..., audience_params=
    {param: value})`` mints a token whose ``aud`` is ``template`` with ``{<param>}`` filled
    in, when the value is the configured one, listed in ``allowed``, or ``any_matching`` is on.
    Set it to ``None`` on ``integrations.set`` to mint for the configured audience only."""

    #: The per-call parameter, e.g. ``cbid``, ``channel``, ``org_id`` or your own.
    param: str
    #: The audience with ``{<param>}`` in it once (required for a custom integration).
    template: str
    #: Further permitted values of the parameter (not whole audiences).
    allowed: list[str]
    #: Any value of the format is permitted.
    any_matching: bool
    #: Read only: true when this is the preset default.
    default: bool


class PrivacyOrchestrator(TypedDict, total=False):
    object: Literal["privacy_orchestrator"]
    configured: bool
    enabled: bool
    provider: str | None
    name: str | None
    case_url: str | None
    cancel_url: str | None
    auth_header: str
    auth_scheme: str
    api_key_set: bool
    signing_secret_set: bool
    use_partner_link: bool
    #: The partner link the orchestrator's owner granted this instance (sent as ``X-Partner-Link``).
    partner_link_id: str | None
    #: The orchestrator-side site a case is for.
    site_id: str | None
    open_closure_cases: bool
    #: Cancel a self-scheduled deletion when the person signs back in during the grace period.
    cancel_deletion_on_sign_in: bool
    completion_webhook: dict[str, Any] | None
    last_case_at: int | None
    last_error: str | None
    last_error_at: int | None
    #: Ready-made orchestrator presets; each may carry a ``case_format``.
    presets: list[dict[str, Any]]
    #: Only on the write that minted it.
    signing_secret: str
    #: Only on the write that created the completion endpoint.
    completion_webhook_secret: str


class PrivacyOrchestratorInput(TypedDict, total=False):
    provider: str
    name: str
    enabled: bool
    case_url: str | None
    #: Must contain ``{id}``.
    cancel_url: str | None
    auth_header: str
    auth_scheme: Literal["bearer", "raw"]
    api_key: str | None
    use_partner_link: bool
    #: Implies ``use_partner_link``.
    partner_link_id: str | None
    site_id: str | None
    open_closure_cases: bool
    cancel_deletion_on_sign_in: bool
    sign_requests: bool
    completion_webhook_url: str | None


class OperatorConfiguration(TypedDict, total=False):
    """``GET /v1/operator``."""

    issuer: str
    device_authorization_endpoint: str
    token_endpoint: str
    client_id: str
    scope: str
    token_exchange_endpoint: str
    token_exchange_audience: Literal["atlas"]
    root_action_max_mfa_age_seconds: int
    #: Other products that accept Atlas operators (pass one as the device login ``audience``).
    audiences: list[str]
    #: The claims an operator access token carries.
    access_token_claims: list[str]


class OutboundPartnerLink(TypedDict, total=False):
    object: Literal["outbound_partner_link"]
    id: str
    partner: str
    name: str
    preset: bool
    resource: str | None
    scopes: list[str]
    base_url: str
    token_url: str
    client_id: str
    auth_method: Literal["client_credentials", "bearer_secret"]
    has_client_secret: Literal[True]
    #: ``manual``, ``oauth_install`` (delivered by the partner) or ``registration`` (a partner
    #: platform's stored partner token).
    source: Literal["manual", "oauth_install", "registration"]
    status: Literal["active", "revoked", "failing"]
    expires_at: int | None
    last_used_at: int | None
    last_error: str | None
    last_error_at: int | None
    calls_30d: int
    created_at: int
    updated_at: int


class AppCatalogPresetsResponse(TypedDict, total=False):
    object: Literal["list"]
    data: list[dict[str, Any]]


class AppCatalogInstalledResponse(TypedDict, total=False):
    object: Literal["list"]
    data: list[dict[str, Any]]


class AppCatalogInstallBody(TypedDict, total=False):
    #: The preset's parameters (GET /v1/app_catalog lists them).
    params: dict[str, Any]
    #: 1-64 letters, digits, - or _. Defaults to the preset id.
    installed_id: str
    name: str
    allowed_email_domains: list[str]
    #: Who may open the app. mode everyone (default) or assigned; with assigned, only the listed
    #: users, members of the listed instance groups (id or slug, inherited), members of the listed
    #: organizations or holders of the listed organization roles. allowed_email_domains applies on
    #: top.
    assignment: dict[str, Any]


class AppCatalogInstallResponse(TypedDict, total=False):
    object: Literal["installed_app"]
    id: str
    protocol: Literal["saml", "oidc"]
    name: str
    preset_id: str | None
    entity_id: str | None
    acs_url: str | None
    client_id: str | None
    launch_url: str | None
    allowed_email_domains: list[str]
    #: Who may open the app. mode everyone (default) or assigned; with assigned, only the listed
    #: users, members of the listed instance groups (id or slug, inherited), members of the listed
    #: organizations or holders of the listed organization roles. allowed_email_domains applies on
    #: top.
    assignment: dict[str, Any]


class AppCatalogUpdateBody(TypedDict, total=False):
    name: str
    allowed_email_domains: list[str]
    #: Who may open the app. mode everyone (default) or assigned; with assigned, only the listed
    #: users, members of the listed instance groups (id or slug, inherited), members of the listed
    #: organizations or holders of the listed organization roles. allowed_email_domains applies on
    #: top.
    assignment: dict[str, Any]


class AppCatalogUpdateResponse(TypedDict, total=False):
    object: Literal["installed_app"]
    id: str
    protocol: Literal["saml", "oidc"]
    name: str
    preset_id: str | None
    entity_id: str | None
    acs_url: str | None
    client_id: str | None
    launch_url: str | None
    allowed_email_domains: list[str]
    #: Who may open the app. mode everyone (default) or assigned; with assigned, only the listed
    #: users, members of the listed instance groups (id or slug, inherited), members of the listed
    #: organizations or holders of the listed organization roles. allowed_email_domains applies on
    #: top.
    assignment: dict[str, Any]


class _LdapServerClientsCreateBodyRequired(TypedDict):
    name: str
    #: e.g. dc=acme,dc=com
    base_dn: str
    #: The service account cn under base_dn.
    bind_cn: str


class LdapServerClientsCreateBody(_LdapServerClientsCreateBodyRequired, total=False):
    #: Source networks allowed to bind (empty = anywhere).
    allowed_cidrs: list[str]
    allow_user_bind: bool
    size_limit: int
    status: Literal["active", "disabled"]


class LdapServerClientsCreateResponse(TypedDict, total=False):
    object: Literal["ldap_server_client"]
    id: str
    name: str
    base_dn: str
    bind_dn: str
    user_dn_template: str
    allowed_cidrs: list[str]
    allow_user_bind: bool
    size_limit: int
    status: Literal["active", "disabled"]
    secret_prefix: str
    last_bind_at: int | None
    created_at: int
    #: On create and rotate only: the bind password, shown once.
    secret: str


class LdapServerClientsGetResponse(TypedDict, total=False):
    object: Literal["ldap_server_client"]
    id: str
    name: str
    base_dn: str
    bind_dn: str
    user_dn_template: str
    allowed_cidrs: list[str]
    allow_user_bind: bool
    size_limit: int
    status: Literal["active", "disabled"]
    secret_prefix: str
    last_bind_at: int | None
    created_at: int
    #: On create and rotate only: the bind password, shown once.
    secret: str


class LdapServerClientsUpdateBody(TypedDict, total=False):
    name: str
    #: e.g. dc=acme,dc=com
    base_dn: str
    #: The service account cn under base_dn.
    bind_cn: str
    #: Source networks allowed to bind (empty = anywhere).
    allowed_cidrs: list[str]
    allow_user_bind: bool
    size_limit: int
    status: Literal["active", "disabled"]


class LdapServerClientsUpdateResponse(TypedDict, total=False):
    object: Literal["ldap_server_client"]
    id: str
    name: str
    base_dn: str
    bind_dn: str
    user_dn_template: str
    allowed_cidrs: list[str]
    allow_user_bind: bool
    size_limit: int
    status: Literal["active", "disabled"]
    secret_prefix: str
    last_bind_at: int | None
    created_at: int
    #: On create and rotate only: the bind password, shown once.
    secret: str


class LdapServerClientsRotateSecretResponse(TypedDict, total=False):
    object: Literal["ldap_server_client"]
    id: str
    name: str
    base_dn: str
    bind_dn: str
    user_dn_template: str
    allowed_cidrs: list[str]
    allow_user_bind: bool
    size_limit: int
    status: Literal["active", "disabled"]
    secret_prefix: str
    last_bind_at: int | None
    created_at: int
    #: On create and rotate only: the bind password, shown once.
    secret: str


class UsersMinorStatusResponse(TypedDict, total=False):
    object: Literal["minor_status"]
    status: Literal["not_required", "consent_required", "consented", "declined"]
    birthdate: str
    age_at_assessment: int
    consent_age: int
    jurisdiction: str | None
    consented_at: int | None
    guardians: list[dict[str, Any]]


class UsersAssessMinorResponse(TypedDict, total=False):
    object: Literal["minor_status"]
    status: Literal["not_required", "consent_required", "consented", "declined"]
    birthdate: str
    age_at_assessment: int
    consent_age: int
    jurisdiction: str | None
    consented_at: int | None
    guardians: list[dict[str, Any]]


class _UsersCreateLinkBodyRequired(TypedDict):
    type: Literal["password_reset", "email_verification"]


class UsersCreateLinkBody(_UsersCreateLinkBodyRequired, total=False):
    #: One of the user's addresses. Default: the primary address.
    email_address_id: str
    #: Default 3600.
    expires_in_seconds: int


class _UsersCreateLinkResponseRequired(TypedDict):
    object: Literal["user_link"]
    type: Literal["password_reset", "email_verification"]
    user_id: str
    email_address_id: str
    email_address: str
    #: Expires (epoch ms).
    expires_at: int


class UsersCreateLinkResponse(_UsersCreateLinkResponseRequired, total=False):
    #: Present when the instance delivers this proof as a link.
    url: str
    #: Present when the instance delivers this proof as a code (always, for email_verification).
    code: str
    #: password_reset only: the reset attempt the link and code belong to.
    attempt_id: str


class _UsersRequiredActionsRequestBodyRequired(TypedDict):
    action: Literal[
        "update_password",
        "verify_email",
        "accept_policy",
        "configure_mfa",
        "update_profile",
        "identity_verification",
        "custom",
    ]


class UsersRequiredActionsRequestBody(_UsersRequiredActionsRequestBodyRequired, total=False):
    #: custom only: the https URL the user is sent to.
    url: str
    #: Free note shown on the audit entry and the held attempt (max 500 characters).
    reason: str


class _UsersRequiredActionsRequestResponseRequired(TypedDict):
    object: Literal["required_action"]
    id: str
    user_id: str
    action: Literal[
        "update_password",
        "verify_email",
        "accept_policy",
        "configure_mfa",
        "update_profile",
        "identity_verification",
        "custom",
    ]
    #: Requested (epoch ms).
    created_at: int


class UsersRequiredActionsRequestResponse(
    _UsersRequiredActionsRequestResponseRequired, total=False
):
    #: custom only: where the user is sent.
    url: str | None
    reason: str | None
    created_by: str | None


class _UsersRequiredActionsBulkBodyRequired(TypedDict):
    action: Literal[
        "update_password",
        "verify_email",
        "accept_policy",
        "configure_mfa",
        "update_profile",
        "identity_verification",
        "custom",
    ]


class UsersRequiredActionsBulkBody(_UsersRequiredActionsBulkBodyRequired, total=False):
    #: custom only: the https URL the user is sent to.
    url: str
    reason: str
    #: Exactly one of organization_id or user_ids.
    organization_id: str
    user_ids: list[str]


class _UsersNotesCreateBodyRequired(TypedDict):
    #: The note text.
    body: str


class UsersNotesCreateBody(_UsersNotesCreateBodyRequired, total=False):
    #: Pinned notes are listed first.
    pinned: bool


class UsersNotesCreateResponse(TypedDict):
    object: Literal["user_note"]
    id: str
    user_id: str
    body: str
    pinned: bool
    author: dict[str, Any]
    #: Added (epoch ms).
    created_at: int
    #: Last edited (epoch ms).
    updated_at: int


class UsersNotesUpdateBody(TypedDict, total=False):
    #: The note text.
    body: str
    #: Pinned notes are listed first.
    pinned: bool


class UsersNotesUpdateResponse(TypedDict):
    object: Literal["user_note"]
    id: str
    user_id: str
    body: str
    pinned: bool
    author: dict[str, Any]
    #: Added (epoch ms).
    created_at: int
    #: Last edited (epoch ms).
    updated_at: int


class UsersGuardiansRequestBody(TypedDict, total=False):
    #: The guardian's email address.
    email: str
    #: A user of this application who is the guardian.
    guardian_user_id: str
    #: Free label such as mother or legal guardian.
    relationship: str
    #: Email the consent link to the guardian (default false).
    send_email: bool


class _UsersGuardiansRequestResponseRequired(TypedDict):
    object: Literal["guardian_link"]
    id: str
    child_user_id: str
    status: Literal["pending", "active", "declined", "revoked", "expired"]
    created_at: int


class UsersGuardiansRequestResponse(_UsersGuardiansRequestResponseRequired, total=False):
    guardian_user_id: str | None
    guardian_email: str | None
    relationship: str | None
    #: When a pending consent link stops working (Unix ms).
    expires_at: int | None
    consent_method: str | None
    consented_at: int | None
    consent_url: str
    emailed: bool


class UsersGuardiansApproveBody(TypedDict, total=False):
    #: How consent was obtained (kept on the link).
    note: str


class _UsersGuardiansApproveResponseRequired(TypedDict):
    object: Literal["guardian_link"]
    id: str
    child_user_id: str
    status: Literal["pending", "active", "declined", "revoked", "expired"]
    created_at: int


class UsersGuardiansApproveResponse(_UsersGuardiansApproveResponseRequired, total=False):
    guardian_user_id: str | None
    guardian_email: str | None
    relationship: str | None
    #: When a pending consent link stops working (Unix ms).
    expires_at: int | None
    consent_method: str | None
    consented_at: int | None


class _UsersGuardiansRevokeResponseRequired(TypedDict):
    object: Literal["guardian_link"]
    id: str
    child_user_id: str
    status: Literal["pending", "active", "declined", "revoked", "expired"]
    created_at: int


class UsersGuardiansRevokeResponse(_UsersGuardiansRevokeResponseRequired, total=False):
    guardian_user_id: str | None
    guardian_email: str | None
    relationship: str | None
    #: When a pending consent link stops working (Unix ms).
    expires_at: int | None
    consent_method: str | None
    consented_at: int | None


class UsersSearchQueryBody(TypedDict, total=False):
    #: A filter tree. A group is exactly one of {"and":[…]}, {"or":[…]}, {"not":{…}} (nest up to 6
    #: levels, 50 conditions). A condition is {"field","op","value"}. Fields: id, username,
    #: first_name, last_name, external_id, locale, email, phone, created_at, updated_at,
    #: last_sign_in_at, password_updated_at, ban
    filter: dict[str, Any]
    #: Free text over id, names, username, emails and phones, ANDed with the filter.
    query: str
    #: created_at (default -created_at), updated_at, last_sign_in_at; prefix - for descending.
    order_by: str
    include_deleted: bool
    limit: int
    starting_after: str
    offset: int
    include_total_count: bool


class UsersSearchExportBody(TypedDict, total=False):
    #: A filter tree. A group is exactly one of {"and":[…]}, {"or":[…]}, {"not":{…}} (nest up to 6
    #: levels, 50 conditions). A condition is {"field","op","value"}. Fields: id, username,
    #: first_name, last_name, external_id, locale, email, phone, created_at, updated_at,
    #: last_sign_in_at, password_updated_at, ban
    filter: dict[str, Any]
    #: Free text over id, names, username, emails and phones, ANDed with the filter.
    query: str
    #: created_at (default -created_at), updated_at, last_sign_in_at; prefix - for descending.
    order_by: str
    include_deleted: bool
    format: Literal["csv", "ndjson"]
    fields: list[str]


class _UsersSearchViewsCreateBodyRequired(TypedDict):
    #: Unique per instance (max 100 characters).
    name: str


class UsersSearchViewsCreateBody(_UsersSearchViewsCreateBodyRequired, total=False):
    #: A filter tree. A group is exactly one of {"and":[…]}, {"or":[…]}, {"not":{…}} (nest up to 6
    #: levels, 50 conditions). A condition is {"field","op","value"}. Fields: id, username,
    #: first_name, last_name, external_id, locale, email, phone, created_at, updated_at,
    #: last_sign_in_at, password_updated_at, ban
    filter: dict[str, Any]
    #: One of created_at, updated_at, last_sign_in_at, optionally prefixed with - for descending.
    order_by: str | None


class _UsersSearchViewsCreateResponseRequired(TypedDict):
    object: Literal["user_search_view"]
    id: str
    name: str
    filter: dict[str, Any]
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class UsersSearchViewsCreateResponse(_UsersSearchViewsCreateResponseRequired, total=False):
    order_by: str | None
    created_by: str | None


class UsersSearchViewsUpdateBody(TypedDict, total=False):
    #: Unique per instance (max 100 characters).
    name: str
    #: A filter tree. A group is exactly one of {"and":[…]}, {"or":[…]}, {"not":{…}} (nest up to 6
    #: levels, 50 conditions). A condition is {"field","op","value"}. Fields: id, username,
    #: first_name, last_name, external_id, locale, email, phone, created_at, updated_at,
    #: last_sign_in_at, password_updated_at, ban
    filter: dict[str, Any]
    #: One of created_at, updated_at, last_sign_in_at, optionally prefixed with - for descending.
    order_by: str | None


class _UsersSearchViewsUpdateResponseRequired(TypedDict):
    object: Literal["user_search_view"]
    id: str
    name: str
    filter: dict[str, Any]
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class UsersSearchViewsUpdateResponse(_UsersSearchViewsUpdateResponseRequired, total=False):
    order_by: str | None
    created_by: str | None


class _JourneysCreateBodyRequired(TypedDict):
    name: str
    definition: dict[str, Any]


class JourneysCreateBody(_JourneysCreateBodyRequired, total=False):
    description: str | None
    #: The journey for every sign-in without an application-specific one (only one is default).
    is_default: bool
    #: OAuth client ids whose sign-ins use this journey instead of the default.
    applications: list[str]
    enabled: bool
    #: Make the new version active (default true).
    activate: bool


class JourneysCreateResponse(TypedDict, total=False):
    object: Literal["sign_in_journey"]
    id: str
    name: str
    description: str | None
    is_default: bool
    applications: list[str]
    enabled: bool
    active_version: int | None
    latest_version: int
    definition: dict[str, Any] | None
    created_at: int
    updated_at: int


class JourneysGetResponse(TypedDict, total=False):
    object: Literal["sign_in_journey"]
    id: str
    name: str
    description: str | None
    is_default: bool
    applications: list[str]
    enabled: bool
    active_version: int | None
    latest_version: int
    definition: dict[str, Any] | None
    created_at: int
    updated_at: int


class JourneysUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    #: The journey for every sign-in without an application-specific one (only one is default).
    is_default: bool
    #: OAuth client ids whose sign-ins use this journey instead of the default.
    applications: list[str]
    enabled: bool
    definition: dict[str, Any]
    #: Make the new version active (default true).
    activate: bool


class JourneysUpdateResponse(TypedDict, total=False):
    object: Literal["sign_in_journey"]
    id: str
    name: str
    description: str | None
    is_default: bool
    applications: list[str]
    enabled: bool
    active_version: int | None
    latest_version: int
    definition: dict[str, Any] | None
    created_at: int
    updated_at: int


class JourneysVersionsResponse(TypedDict, total=False):
    object: Literal["list"]
    data: list[dict[str, Any]]


class JourneysActivateBody(TypedDict):
    version: int


class JourneysActivateResponse(TypedDict, total=False):
    object: Literal["sign_in_journey"]
    id: str
    name: str
    description: str | None
    is_default: bool
    applications: list[str]
    enabled: bool
    active_version: int | None
    latest_version: int
    definition: dict[str, Any] | None
    created_at: int
    updated_at: int


class _JourneysSimulateBodyRequired(TypedDict):
    user_id: str


class JourneysSimulateBody(_JourneysSimulateBodyRequired, total=False):
    method: str
    mfa_verified: bool
    ip: str
    application_id: str
    version: int


class JourneysSimulateResponse(TypedDict, total=False):
    object: Literal["sign_in_journey_simulation"]
    journey_id: str
    version: int
    outcome: Literal["allowed", "held", "refused"]
    effects: list[dict[str, Any]]
    trace: list[dict[str, Any]]


class _GroupsCreateBodyRequired(TypedDict):
    #: Lowercase letters, digits, - and _ (max 63). Unique per instance; usable in place of the id
    #: in paths.
    slug: str
    name: str


class GroupsCreateBody(_GroupsCreateBodyRequired, total=False):
    description: str | None
    #: Nest under another group (up to 8 levels, no cycles). Members of a child are also members of
    #: its ancestors for the token claim and role mapping.
    parent_id: str | None
    #: Free attributes (max 8 KB).
    attributes: dict[str, Any]
    #: App roles every member (and member of a descendant) holds, merged into app_roles /
    #: app_permissions on the token.
    app_role_keys: list[str]
    #: Add the slug to the `groups` token claim (default true).
    include_in_token: bool
    #: A user-search filter tree. POST …/reapply (and each SSO sign-in) makes membership match it.
    dynamic_filter: dict[str, Any] | None
    #: { claim, equals | contains | matches }: join at SSO sign-in when the IdP claim (a string or
    #: list, e.g. "groups") matches; leave when it stops matching.
    sso_match: dict[str, Any] | None


class _GroupsCreateResponseRequired(TypedDict):
    object: Literal["group"]
    id: str
    slug: str
    name: str
    attributes: dict[str, Any]
    app_role_keys: list[str]
    include_in_token: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class GroupsCreateResponse(_GroupsCreateResponseRequired, total=False):
    description: str | None
    parent_id: str | None
    dynamic_filter: dict[str, Any] | None
    sso_match: dict[str, Any] | None
    member_count: int
    #: GET /v1/users/:id/groups only: how the user joined.
    source: str


class _GroupsGetResponseRequired(TypedDict):
    object: Literal["group"]
    id: str
    slug: str
    name: str
    attributes: dict[str, Any]
    app_role_keys: list[str]
    include_in_token: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class GroupsGetResponse(_GroupsGetResponseRequired, total=False):
    description: str | None
    parent_id: str | None
    dynamic_filter: dict[str, Any] | None
    sso_match: dict[str, Any] | None
    member_count: int
    #: GET /v1/users/:id/groups only: how the user joined.
    source: str


class GroupsUpdateBody(TypedDict, total=False):
    #: Lowercase letters, digits, - and _ (max 63). Unique per instance; usable in place of the id
    #: in paths.
    slug: str
    name: str
    description: str | None
    #: Nest under another group (up to 8 levels, no cycles). Members of a child are also members of
    #: its ancestors for the token claim and role mapping.
    parent_id: str | None
    #: Free attributes (max 8 KB).
    attributes: dict[str, Any]
    #: App roles every member (and member of a descendant) holds, merged into app_roles /
    #: app_permissions on the token.
    app_role_keys: list[str]
    #: Add the slug to the `groups` token claim (default true).
    include_in_token: bool
    #: A user-search filter tree. POST …/reapply (and each SSO sign-in) makes membership match it.
    dynamic_filter: dict[str, Any] | None
    #: { claim, equals | contains | matches }: join at SSO sign-in when the IdP claim (a string or
    #: list, e.g. "groups") matches; leave when it stops matching.
    sso_match: dict[str, Any] | None


class _GroupsUpdateResponseRequired(TypedDict):
    object: Literal["group"]
    id: str
    slug: str
    name: str
    attributes: dict[str, Any]
    app_role_keys: list[str]
    include_in_token: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class GroupsUpdateResponse(_GroupsUpdateResponseRequired, total=False):
    description: str | None
    parent_id: str | None
    dynamic_filter: dict[str, Any] | None
    sso_match: dict[str, Any] | None
    member_count: int
    #: GET /v1/users/:id/groups only: how the user joined.
    source: str


class GroupsAddMembersBody(TypedDict):
    user_ids: list[str]


class GroupsRemoveMembersBody(TypedDict):
    user_ids: list[str]


class GroupsReapplyResponse(TypedDict):
    object: Literal["group_reapply_result"]
    group_id: str
    #: Users the dynamic filter matches now.
    matched: int
    #: Members added by this run.
    added: int
    #: Members removed because they no longer match.
    removed: int


class _GroupsRulesCreateBodyRequired(TypedDict):
    name: str
    #: A user-search filter tree (see POST /v1/users/search).
    condition: dict[str, Any]
    actions: list[dict[str, Any]]


class GroupsRulesCreateBody(_GroupsRulesCreateBodyRequired, total=False):
    enabled: bool
    #: Lower runs first (default 100).
    priority: int


class _GroupsRulesCreateResponseRequired(TypedDict):
    object: Literal["group_rule"]
    id: str
    name: str
    enabled: bool
    priority: int
    condition: dict[str, Any]
    actions: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class GroupsRulesCreateResponse(_GroupsRulesCreateResponseRequired, total=False):
    created_by: str | None


class _GroupsRulesGetResponseRequired(TypedDict):
    object: Literal["group_rule"]
    id: str
    name: str
    enabled: bool
    priority: int
    condition: dict[str, Any]
    actions: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class GroupsRulesGetResponse(_GroupsRulesGetResponseRequired, total=False):
    created_by: str | None


class GroupsRulesUpdateBody(TypedDict, total=False):
    name: str
    enabled: bool
    #: Lower runs first (default 100).
    priority: int
    #: A user-search filter tree (see POST /v1/users/search).
    condition: dict[str, Any]
    actions: list[dict[str, Any]]


class _GroupsRulesUpdateResponseRequired(TypedDict):
    object: Literal["group_rule"]
    id: str
    name: str
    enabled: bool
    priority: int
    condition: dict[str, Any]
    actions: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class GroupsRulesUpdateResponse(_GroupsRulesUpdateResponseRequired, total=False):
    created_by: str | None


class GroupsRulesApplyResponse(TypedDict):
    object: Literal["group_rule_result"]
    rule_id: str
    #: Users the rule condition matches.
    matched: int
    groups_added: int
    groups_removed: int
    roles_granted: int
    traits_set: int


class _MigrationsExchangeBodyRequired(TypedDict):
    #: The old session token (JWT or opaque), as the middleware extracted it.
    token: str


class MigrationsExchangeBody(_MigrationsExchangeBodyRequired, total=False):
    #: false records a browser-session (non-persistent) session. Default true.
    remember: bool


class MigrationsExchangeResponse(TypedDict, total=False):
    object: Literal["session", "session_tokens", "sign_in_attempt"]
    id: str
    session_id: str
    user_id: str
    jwt: str
    #: Body delivery only.
    refresh_token: str
    expires_in: int
    status: Literal["needs_second_factor", "needs_mfa_enrollment", "needs_policy_acceptance"]
    identifier: str | None
    supported_first_factors: list[str]
    created_session_id: None
    expires_at: int


class MigrationsGetBridgeResponse(TypedDict, total=False):
    object: Literal["migration_bridge"]
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    enabled: bool
    #: End of the migration window, or null (Unix milliseconds).
    ends_at: int | None
    mode: Literal["jwt", "session_table", "remote"]
    preset: str | None
    preset_vars: dict[str, Any]
    issuer: str | None
    jwks_url: str | None
    audience: list[str] | None
    algorithms: list[str]
    claim_map: dict[str, Any]
    expired_grace_seconds: int
    cookie_names: list[str]
    create_users: bool
    #: Whether an HS256 secret is stored — never the secret.
    has_shared_secret: bool
    #: The Frontend API path the SDKs call.
    exchange_path: str
    stats: dict[str, Any]
    #: Created, or null when never configured (Unix milliseconds).
    created_at: int | None
    #: Updated, or null when never configured (Unix milliseconds).
    updated_at: int | None


class MigrationsSetBridgeBody(TypedDict, total=False):
    #: Whether the exchange accepts old sessions. Default false.
    enabled: bool
    #: End of the migration window (ISO-8601 or Unix ms); null = open until disabled.
    ends_at: str | int | None
    #: jwt: the old session is a vendor JWT. session_table: an opaque token matched against
    #: imported sessions. remote: the vendor is asked about the token with the preset's call
    #: (vendors whose sessions only they can check; needs a preset with a remote check). Default:
    #: the preset's.
    mode: Literal["jwt", "session_table", "remote"]
    #: A bridge preset (GET /v1/migrations/sources lists them): fills issuer, keys URL, audience,
    #: algorithms, claims and cookie names from preset_vars.
    preset: str | None
    #: The preset's variables, e.g. {"domain": "acme.us.auth0.com"} or {"region": "us-east-1",
    #: "user_pool_id": "…", "client_id": "…"}.
    preset_vars: dict[str, Any]
    #: Override: the `iss` the old tokens carry.
    issuer: str | None
    #: Override: where the old signing keys are (public https on production).
    jwks_url: str | None
    #: Override: accepted `aud` values; null = unchecked.
    audience: list[str] | None
    algorithms: list[str] | None
    claim_map: dict[str, Any]
    #: Accept a validly signed token this long past exp (still single use). For vendors whose
    #: cookie token is refreshed by their client SDK only.
    expired_grace_seconds: int
    #: Where the SDK middleware finds the token (* wildcards). Default: the preset's.
    cookie_names: list[str]
    #: Create an Atlas user for a valid token whose subject was never imported (needs a verified
    #: email claim). Default false.
    create_users: bool
    #: Write-only HS256 secret, for vendors that sign with one (Supabase legacy JWT secret). Omit
    #: to keep, null to clear.
    shared_secret: str | None


class MigrationsSetBridgeResponse(TypedDict, total=False):
    object: Literal["migration_bridge"]
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    enabled: bool
    #: End of the migration window, or null (Unix milliseconds).
    ends_at: int | None
    mode: Literal["jwt", "session_table", "remote"]
    preset: str | None
    preset_vars: dict[str, Any]
    issuer: str | None
    jwks_url: str | None
    audience: list[str] | None
    algorithms: list[str]
    claim_map: dict[str, Any]
    expired_grace_seconds: int
    cookie_names: list[str]
    create_users: bool
    #: Whether an HS256 secret is stored — never the secret.
    has_shared_secret: bool
    #: The Frontend API path the SDKs call.
    exchange_path: str
    stats: dict[str, Any]
    #: Created, or null when never configured (Unix milliseconds).
    created_at: int | None
    #: Updated, or null when never configured (Unix milliseconds).
    updated_at: int | None


class MigrationsDeleteBridgeResponse(TypedDict, total=False):
    object: Literal["migration_bridge"]
    source: str
    deleted: Literal[True]


class _MigrationsImportsGetPublicKeyResponseRequired(TypedDict):
    object: Literal["migration_import_key"]
    kid: str
    #: base64url raw X25519 public key. One key serves every source.
    public_key: str
    alg: Literal["X25519-HKDF-SHA256-A256GCM"]
    status: Literal["active", "retired"]
    #: SHA-256 of the raw key, first 16 bytes as hex pairs: compare it with what the exporter
    #: prints.
    fingerprint: str
    #: The `kid:public_key` form the exporters accept.
    compact: str
    created_at: int


class MigrationsImportsGetPublicKeyResponse(
    _MigrationsImportsGetPublicKeyResponseRequired, total=False
):
    retired_at: int | None


class _MigrationsImportsRotatePublicKeyResponseRequired(TypedDict):
    object: Literal["migration_import_key"]
    kid: str
    #: base64url raw X25519 public key. One key serves every source.
    public_key: str
    alg: Literal["X25519-HKDF-SHA256-A256GCM"]
    status: Literal["active", "retired"]
    #: SHA-256 of the raw key, first 16 bytes as hex pairs: compare it with what the exporter
    #: prints.
    fingerprint: str
    #: The `kid:public_key` form the exporters accept.
    compact: str
    created_at: int


class MigrationsImportsRotatePublicKeyResponse(
    _MigrationsImportsRotatePublicKeyResponseRequired, total=False
):
    retired_at: int | None


class MigrationsImportsCreateBody(TypedDict, total=False):
    #: What the import does. Every field is optional; an unknown field is refused. A `better_auth`
    #: import takes the Better Auth options (see /v1/better_auth_imports); every other source takes
    #: these.
    options: dict[str, Any]


class _MigrationsImportsCreateResponseRequired(TypedDict):
    object: Literal["migration_import"]
    id: str
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    status: Literal[
        "uploading", "analyzing", "ready", "invalid", "queued", "applying", "completed", "failed"
    ]
    created_at: int
    updated_at: int


class MigrationsImportsCreateResponse(_MigrationsImportsCreateResponseRequired, total=False):
    format: Literal["atlas-migration-bundle", "atlas-better-auth-bundle"]
    key_id: str | None
    parts: int
    bytes: int
    bundle_sha256: str | None
    bundle_purged: bool
    options: dict[str, Any]
    #: What the exporter reported about the source.
    manifest: dict[str, Any] | None
    total: int
    progress: dict[str, Any] | None
    #: The dry run: what an apply would do.
    report: dict[str, Any] | None
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    analyzed_at: int | None
    apply_started_at: int | None
    completed_at: int | None


class _MigrationsImportsGetResponseRequired(TypedDict):
    object: Literal["migration_import"]
    id: str
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    status: Literal[
        "uploading", "analyzing", "ready", "invalid", "queued", "applying", "completed", "failed"
    ]
    created_at: int
    updated_at: int


class MigrationsImportsGetResponse(_MigrationsImportsGetResponseRequired, total=False):
    format: Literal["atlas-migration-bundle", "atlas-better-auth-bundle"]
    key_id: str | None
    parts: int
    bytes: int
    bundle_sha256: str | None
    bundle_purged: bool
    options: dict[str, Any]
    #: What the exporter reported about the source.
    manifest: dict[str, Any] | None
    total: int
    progress: dict[str, Any] | None
    #: The dry run: what an apply would do.
    report: dict[str, Any] | None
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    analyzed_at: int | None
    apply_started_at: int | None
    completed_at: int | None


class MigrationsImportsPutPartBody(TypedDict):
    #: Lines of the sealed bundle file.
    data: str


class MigrationsImportsPutPartResponse(TypedDict, total=False):
    object: Literal["migration_import_part"]
    import_id: str
    part: int
    bytes: int
    sha256: str


class _MigrationsImportsFinalizeResponseRequired(TypedDict):
    object: Literal["migration_import"]
    id: str
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    status: Literal[
        "uploading", "analyzing", "ready", "invalid", "queued", "applying", "completed", "failed"
    ]
    created_at: int
    updated_at: int


class MigrationsImportsFinalizeResponse(_MigrationsImportsFinalizeResponseRequired, total=False):
    format: Literal["atlas-migration-bundle", "atlas-better-auth-bundle"]
    key_id: str | None
    parts: int
    bytes: int
    bundle_sha256: str | None
    bundle_purged: bool
    options: dict[str, Any]
    #: What the exporter reported about the source.
    manifest: dict[str, Any] | None
    total: int
    progress: dict[str, Any] | None
    #: The dry run: what an apply would do.
    report: dict[str, Any] | None
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    analyzed_at: int | None
    apply_started_at: int | None
    completed_at: int | None


class MigrationsImportsDryRunBody(TypedDict, total=False):
    #: What the import does. Every field is optional; an unknown field is refused. A `better_auth`
    #: import takes the Better Auth options (see /v1/better_auth_imports); every other source takes
    #: these.
    options: dict[str, Any]


class _MigrationsImportsDryRunResponseRequired(TypedDict):
    object: Literal["migration_import"]
    id: str
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    status: Literal[
        "uploading", "analyzing", "ready", "invalid", "queued", "applying", "completed", "failed"
    ]
    created_at: int
    updated_at: int


class MigrationsImportsDryRunResponse(_MigrationsImportsDryRunResponseRequired, total=False):
    format: Literal["atlas-migration-bundle", "atlas-better-auth-bundle"]
    key_id: str | None
    parts: int
    bytes: int
    bundle_sha256: str | None
    bundle_purged: bool
    options: dict[str, Any]
    #: What the exporter reported about the source.
    manifest: dict[str, Any] | None
    total: int
    progress: dict[str, Any] | None
    #: The dry run: what an apply would do.
    report: dict[str, Any] | None
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    analyzed_at: int | None
    apply_started_at: int | None
    completed_at: int | None


class MigrationsImportsApplyBody(TypedDict, total=False):
    confirm_conflicts: bool


class _MigrationsImportsApplyResponseRequired(TypedDict):
    object: Literal["migration_import"]
    id: str
    source: Literal[
        "better_auth",
        "auth0",
        "clerk",
        "cognito",
        "firebase",
        "supabase",
        "workos",
        "authjs",
        "okta",
        "stytch",
        "keycloak",
        "fusionauth",
        "kinde",
        "descope",
        "lucia",
        "passport",
        "iron_session",
        "devise",
        "django",
        "ory",
        "frontegg",
        "custom",
        "propelauth",
        "magic",
        "userfront",
        "corbado",
        "ping_identity",
        "onelogin",
        "saml",
        "oidc",
        "ldap",
    ]
    status: Literal[
        "uploading", "analyzing", "ready", "invalid", "queued", "applying", "completed", "failed"
    ]
    created_at: int
    updated_at: int


class MigrationsImportsApplyResponse(_MigrationsImportsApplyResponseRequired, total=False):
    format: Literal["atlas-migration-bundle", "atlas-better-auth-bundle"]
    key_id: str | None
    parts: int
    bytes: int
    bundle_sha256: str | None
    bundle_purged: bool
    options: dict[str, Any]
    #: What the exporter reported about the source.
    manifest: dict[str, Any] | None
    total: int
    progress: dict[str, Any] | None
    #: The dry run: what an apply would do.
    report: dict[str, Any] | None
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    analyzed_at: int | None
    apply_started_at: int | None
    completed_at: int | None


class ManagedGrantsListResponse(TypedDict):
    object: Literal["list"]
    data: list[dict[str, Any]]


class _ManagedGrantsGetResponseRequired(TypedDict):
    object: Literal["managed_grant"]
    #: The `grant_id` returned in token responses.
    id: str
    client_id: str | None
    user_id: str
    status: Literal["active", "revoked"]
    scopes: list[str]
    #: Bumped by every merge, replace and narrowing.
    revision: int
    created_at: int
    updated_at: int


class ManagedGrantsGetResponse(_ManagedGrantsGetResponseRequired, total=False):
    organization_id: str | None
    #: The API (resource server identifier) the grant covers, or null.
    resource: str | None
    authorization_details: list[dict[str, Any]] | None
    revoked_at: int | None
    revoked_by: str | None


class ManagedGrantsNarrowBody(TypedDict, total=False):
    scopes: list[str]
    authorization_details: list[dict[str, Any]]


class _ManagedGrantsNarrowResponseRequired(TypedDict):
    object: Literal["managed_grant"]
    #: The `grant_id` returned in token responses.
    id: str
    client_id: str | None
    user_id: str
    status: Literal["active", "revoked"]
    scopes: list[str]
    #: Bumped by every merge, replace and narrowing.
    revision: int
    created_at: int
    updated_at: int


class ManagedGrantsNarrowResponse(_ManagedGrantsNarrowResponseRequired, total=False):
    organization_id: str | None
    #: The API (resource server identifier) the grant covers, or null.
    resource: str | None
    authorization_details: list[dict[str, Any]] | None
    revoked_at: int | None
    revoked_by: str | None


class ManagedGrantsRevokeResponse(TypedDict):
    object: Literal["managed_grant"]
    id: str
    deleted: Literal[True]
    tokens_ended: int


class LeastPrivilegeReportResponse(TypedDict):
    object: Literal["least_privilege_report"]
    generated_at: int
    window_days: int
    summary: dict[str, Any]
    data: list[dict[str, Any]]


class _LeastPrivilegeGetResponseRequired(TypedDict):
    object: Literal["least_privilege_subject"]
    subject_type: Literal["api_key", "oauth_client", "mcp_gateway", "agent"]
    subject_id: str
    window_days: int
    #: How many of the window's days the usage data covers. Use is recorded from the day the
    #: feature reached the instance; gateway tool calls come from the audit trail.
    observed_days: int
    #: `low` when the data covers less than the window: a permission used once a month can look
    #: unused.
    confidence: Literal["high", "low"]
    granted: list[dict[str, Any]]
    used: list[dict[str, Any]]
    unused: list[dict[str, Any]]
    #: The narrower grant. It only ever removes permissions.
    suggestion: dict[str, Any] | None
    #: The suggestion can be applied with one call.
    applicable: bool


class LeastPrivilegeGetResponse(_LeastPrivilegeGetResponseRequired, total=False):
    name: str | None
    note: str


class LeastPrivilegeApplyBody(TypedDict, total=False):
    subject_type: Literal["api_key", "oauth_client", "mcp_gateway", "agent"]
    subject_id: str
    digest: str
    days: int
    acknowledge_short_window: bool


class _LeastPrivilegeApplyResponseRequired(TypedDict):
    object: Literal["least_privilege_change"]
    subject_type: str
    subject_id: str
    applied: Literal[True]
    changes: list[dict[str, Any]]


class LeastPrivilegeApplyResponse(_LeastPrivilegeApplyResponseRequired, total=False):
    summary: str


class DeliveryHealthGetResponse(TypedDict, total=False):
    object: Literal["delivery_health"]
    kind: Literal["webhook_endpoint", "referral_connection", "backchannel_receiver", "integration"]
    target_id: str
    url: str | None
    label: str | None
    state: Literal["healthy", "failing", "disabled"]
    failing_since: int | None
    disabled_at: int | None
    last_success_at: int | None
    last_failure: dict[str, Any] | None
    consecutive_failures: int
    success_rate_24h: float | None
    attempts_24h: dict[str, Any]
    alert_contacts: list[str] | None
    alerts: dict[str, Any]


class FlagsAssignOrganizationEntitlementsBody(TypedDict, total=False):
    plan: str | None
    features: list[str] | None
    limits: dict[str, Any] | None
    #: Unix ms or ISO 8601; null = no expiry.
    expires_at: int | str | None


class FlagsAssignOrganizationEntitlementsResponse(TypedDict):
    object: Literal["assigned_entitlements"]
    subject_type: Literal["user", "org"]
    subject_id: str
    plan: str | None
    features: list[str] | None
    limits: dict[str, Any] | None
    #: Epoch milliseconds.
    expires_at: int | None


class _FlagsCreateBodyRequired(TypedDict):
    #: Lowercase letters, digits, - and _.
    key: str
    type: Literal["boolean", "string", "int", "json"]
    #: A boolean, string, integer or JSON value matching the flag `type`.
    default_value: bool | str | int | float | dict[str, Any] | list[Any] | None


class FlagsCreateBody(_FlagsCreateBodyRequired, total=False):
    description: str | None
    enabled: bool
    #: A boolean, string, integer or JSON value matching the flag `type`.
    off_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: Ordered targeting rules; the first match wins.
    rules: list[dict[str, Any]]


class _FlagsCreateResponseRequired(TypedDict):
    object: Literal["feature_flag"]
    id: str
    #: Unique within the instance (an instance is one environment).
    key: str
    type: Literal["boolean", "string", "int", "json"]
    #: The kill switch: while false, every subject gets `off_value`.
    enabled: bool
    #: A boolean, string, integer or JSON value matching the flag `type`.
    default_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: A boolean, string, integer or JSON value matching the flag `type`.
    off_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: Evaluated in order; the first rule that matches (and whose percentage bucket includes the
    #: subject) supplies the value.
    rules: list[dict[str, Any]]
    #: When the flag was created (epoch ms).
    created_at: int
    #: When the flag last changed (epoch ms).
    updated_at: int


class FlagsCreateResponse(_FlagsCreateResponseRequired, total=False):
    description: str | None


class _FlagsRetrieveResponseRequired(TypedDict):
    object: Literal["feature_flag"]
    id: str
    #: Unique within the instance (an instance is one environment).
    key: str
    type: Literal["boolean", "string", "int", "json"]
    #: The kill switch: while false, every subject gets `off_value`.
    enabled: bool
    #: A boolean, string, integer or JSON value matching the flag `type`.
    default_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: A boolean, string, integer or JSON value matching the flag `type`.
    off_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: Evaluated in order; the first rule that matches (and whose percentage bucket includes the
    #: subject) supplies the value.
    rules: list[dict[str, Any]]
    #: When the flag was created (epoch ms).
    created_at: int
    #: When the flag last changed (epoch ms).
    updated_at: int


class FlagsRetrieveResponse(_FlagsRetrieveResponseRequired, total=False):
    description: str | None


class FlagsUpdateBody(TypedDict, total=False):
    description: str | None
    enabled: bool
    #: A boolean, string, integer or JSON value matching the flag `type`.
    default_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: A boolean, string, integer or JSON value matching the flag `type`.
    off_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: Ordered targeting rules; the first match wins.
    rules: list[dict[str, Any]]


class _FlagsUpdateResponseRequired(TypedDict):
    object: Literal["feature_flag"]
    id: str
    #: Unique within the instance (an instance is one environment).
    key: str
    type: Literal["boolean", "string", "int", "json"]
    #: The kill switch: while false, every subject gets `off_value`.
    enabled: bool
    #: A boolean, string, integer or JSON value matching the flag `type`.
    default_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: A boolean, string, integer or JSON value matching the flag `type`.
    off_value: bool | str | int | float | dict[str, Any] | list[Any] | None
    #: Evaluated in order; the first rule that matches (and whose percentage bucket includes the
    #: subject) supplies the value.
    rules: list[dict[str, Any]]
    #: When the flag was created (epoch ms).
    created_at: int
    #: When the flag last changed (epoch ms).
    updated_at: int


class FlagsUpdateResponse(_FlagsUpdateResponseRequired, total=False):
    description: str | None


class FlagsDeleteResponse(TypedDict):
    object: Literal["feature_flag"]
    id: str
    key: str
    deleted: bool


class FlagsEvaluateBody(TypedDict, total=False):
    user_id: str
    org_id: str
    plan: str
    keys: list[str]


class FlagsEvaluateResponse(TypedDict):
    object: Literal["feature_flag_evaluation"]
    subject: dict[str, Any]
    flags: dict[str, Any]


class FlagsAssignUserEntitlementsBody(TypedDict, total=False):
    plan: str | None
    features: list[str] | None
    limits: dict[str, Any] | None
    #: Unix ms or ISO 8601; null = no expiry.
    expires_at: int | str | None


class FlagsAssignUserEntitlementsResponse(TypedDict):
    object: Literal["assigned_entitlements"]
    subject_type: Literal["user", "org"]
    subject_id: str
    plan: str | None
    features: list[str] | None
    limits: dict[str, Any] | None
    #: Epoch milliseconds.
    expires_at: int | None


class MfaFactorsSetYubicoSecretBody(TypedDict):
    #: Base64 secret key.
    secret: str


class MfaFactorsSetYubicoSecretResponse(TypedDict):
    object: Literal["yubico_secret"]
    set: Literal[True]


class MfaFactorsRemoveYubicoSecretResponse(TypedDict):
    object: Literal["yubico_secret"]
    deleted: Literal[True]


class MfaFactorsSetDuoSecretBody(TypedDict):
    #: Duo client secret.
    secret: str


class MfaFactorsSetDuoSecretResponse(TypedDict):
    object: Literal["duo_secret"]
    set: Literal[True]


class MfaFactorsRemoveDuoSecretResponse(TypedDict):
    object: Literal["duo_secret"]
    deleted: Literal[True]


class MfaFactorsSetSmartCardSecretBody(TypedDict):
    #: Random shared secret, 24 characters or more.
    secret: str


class MfaFactorsSetSmartCardSecretResponse(TypedDict):
    object: Literal["smart_card_secret"]
    set: Literal[True]


class MfaFactorsRemoveSmartCardSecretResponse(TypedDict):
    object: Literal["smart_card_secret"]
    deleted: Literal[True]


class MfaFactorsDuoHealthCheckResponse(TypedDict):
    object: Literal["duo_health_check"]
    ok: bool
    message: str


class MfaFactorsResetSecurityQuestionsResponse(TypedDict):
    object: Literal["security_questions"]
    user_id: str
    deleted: bool


class MfaFactorsYubikeysListResponse(TypedDict):
    object: Literal["list"]
    data: list[dict[str, Any]]


class _MfaFactorsYubikeysRegisterBodyRequired(TypedDict):
    #: Modhex prefix printed on the key (2 to 16 characters).
    public_id: str
    #: 32 hex characters.
    aes_key: str


class MfaFactorsYubikeysRegisterBody(_MfaFactorsYubikeysRegisterBodyRequired, total=False):
    #: Optional 12 hex characters; when given the decrypted token must carry it.
    private_id: str
    label: str
    user_id: str


class _MfaFactorsYubikeysRegisterResponseRequired(TypedDict):
    object: Literal["yubikey"]
    id: str
    public_id: str


class MfaFactorsYubikeysRegisterResponse(_MfaFactorsYubikeysRegisterResponseRequired, total=False):
    label: str | None
    #: The user the key belongs to, once assigned or enrolled.
    user_id: str | None
    has_private_id: bool
    #: The highest use/session counter accepted so far (replay guard).
    last_counter: int | None
    created_at: int


class MfaFactorsSmartCardMappingsListResponse(TypedDict):
    object: Literal["list"]
    data: list[dict[str, Any]]


class _MfaFactorsSmartCardMappingsAddBodyRequired(TypedDict):
    kind: Literal["san_email", "san_upn", "subject_cn", "serial", "fingerprint"]
    value: str


class MfaFactorsSmartCardMappingsAddBody(_MfaFactorsSmartCardMappingsAddBodyRequired, total=False):
    #: Issuer DN. Required for kind "serial".
    issuer: str
    label: str


class _MfaFactorsSmartCardMappingsAddResponseRequired(TypedDict):
    object: Literal["smartcard_mapping"]
    id: str
    user_id: str
    kind: Literal["san_email", "san_upn", "subject_cn", "serial", "fingerprint"]
    #: The normalised value: lowercase; fingerprint 64 hex; serial as "<issuer DN>#<serial hex>".
    value: str


class MfaFactorsSmartCardMappingsAddResponse(
    _MfaFactorsSmartCardMappingsAddResponseRequired, total=False
):
    label: str | None
    last_used_at: int | None
    created_at: int


class AnalyticsFunnelResponse(TypedDict, total=False):
    object: Literal["analytics_funnel"]
    window: dict[str, Any]
    data: list[dict[str, Any]]


class AnalyticsJourneyFunnelResponse(TypedDict, total=False):
    object: Literal["analytics_journey_funnel"]
    window: dict[str, Any]
    journey_id: str
    journey_name: str
    data: list[dict[str, Any]]


class AnalyticsFailuresResponse(TypedDict, total=False):
    object: Literal["analytics_failures"]
    window: dict[str, Any]
    total: int
    data: list[dict[str, Any]]


class AnalyticsBreakdownResponse(TypedDict, total=False):
    object: Literal["analytics_breakdown"]
    window: dict[str, Any]
    dimension: str
    total: int
    data: list[dict[str, Any]]


class AnalyticsActiveUsersResponse(TypedDict, total=False):
    object: Literal["analytics_active_users"]
    window: dict[str, Any]
    dau: int
    wau: int
    mau: int
    data: list[dict[str, Any]]


class AnalyticsPasskeyAdoptionResponse(TypedDict, total=False):
    object: Literal["analytics_passkey_adoption"]
    window: dict[str, Any]
    users: int
    users_with_passkey: int
    adoption_rate: float
    data: list[dict[str, Any]]


class AnalyticsApiUsageResponse(TypedDict, total=False):
    object: Literal["api_usage"]
    window_minutes: int
    baseline_hours: int
    generated_at: int
    data: list[dict[str, Any]]


class AnalyticsReportsMfaCoverageResponse(TypedDict, total=False):
    object: Literal["analytics_report_mfa_coverage"]
    window: dict[str, Any]
    total_users: int
    data: list[dict[str, Any]]


class AnalyticsReportsAccessByAppResponse(TypedDict, total=False):
    object: Literal["analytics_report_access_by_app"]
    window: dict[str, Any]
    data: list[dict[str, Any]]


class _AnalyticsAlertRulesCreateBodyRequired(TypedDict):
    name: str
    #: Percent metrics are 0-100; failed_sign_ins is a count; sign_in_p95_seconds is seconds;
    #: api_usage_spike is the ratio of a key or organization's request rate in the window to its
    #: average hourly rate over the 7 days before (for example 10 = ten times its usual volume),
    #: and min_sample is the fewest requ
    metric: Literal[
        "sign_in_success_rate",
        "failed_passkey_ratio",
        "failed_sign_ins",
        "sign_in_p95_seconds",
        "api_usage_spike",
    ]
    comparator: Literal["lt", "gt"]
    threshold: float


class AnalyticsAlertRulesCreateBody(_AnalyticsAlertRulesCreateBodyRequired, total=False):
    #: Trailing window, 5 to 1440 (default 60).
    window_minutes: int
    #: Ratios and latency are not evaluated on fewer observations (default 20).
    min_sample: int
    #: Minimum minutes between notifications while the rule stays firing (default 60).
    cooldown_minutes: int
    email_contacts: list[str]
    #: A public HTTPS endpoint. The body is signed like any Atlas webhook; the signing secret is
    #: returned once, on create.
    webhook_url: str | None
    enabled: bool
    #: api_usage_spike only: watch secret keys, end-user API keys or organizations (null = all).
    subject_type: str | None
    #: api_usage_spike only: watch one key or organization (needs subject_type).
    subject_id: str | None
    #: Also raise a Shared Signals event (an opaque subject naming the key or organization) on
    #: every enabled stream that asks for it.
    ssf: bool


class AnalyticsAlertRulesCreateResponse(TypedDict, total=False):
    object: Literal["analytics_alert_rule"]
    id: str
    name: str
    metric: Literal[
        "sign_in_success_rate",
        "failed_passkey_ratio",
        "failed_sign_ins",
        "sign_in_p95_seconds",
        "api_usage_spike",
    ]
    comparator: Literal["lt", "gt"]
    threshold: float
    window_minutes: int
    min_sample: int
    cooldown_minutes: int
    email_contacts: list[str]
    webhook_url: str | None
    has_webhook_secret: bool
    enabled: bool
    subject_type: str | None
    subject_id: str | None
    ssf: bool
    state: Literal["ok", "firing"]
    last_value: float | None
    last_evaluated_at: int | None
    last_triggered_at: int | None
    last_error: str | None
    created_at: int


class AnalyticsAlertRulesGetResponse(TypedDict, total=False):
    object: Literal["analytics_alert_rule"]
    id: str
    name: str
    metric: Literal[
        "sign_in_success_rate",
        "failed_passkey_ratio",
        "failed_sign_ins",
        "sign_in_p95_seconds",
        "api_usage_spike",
    ]
    comparator: Literal["lt", "gt"]
    threshold: float
    window_minutes: int
    min_sample: int
    cooldown_minutes: int
    email_contacts: list[str]
    webhook_url: str | None
    has_webhook_secret: bool
    enabled: bool
    subject_type: str | None
    subject_id: str | None
    ssf: bool
    state: Literal["ok", "firing"]
    last_value: float | None
    last_evaluated_at: int | None
    last_triggered_at: int | None
    last_error: str | None
    created_at: int


class AnalyticsAlertRulesUpdateBody(TypedDict, total=False):
    name: str
    #: Percent metrics are 0-100; failed_sign_ins is a count; sign_in_p95_seconds is seconds;
    #: api_usage_spike is the ratio of a key or organization's request rate in the window to its
    #: average hourly rate over the 7 days before (for example 10 = ten times its usual volume),
    #: and min_sample is the fewest requ
    metric: Literal[
        "sign_in_success_rate",
        "failed_passkey_ratio",
        "failed_sign_ins",
        "sign_in_p95_seconds",
        "api_usage_spike",
    ]
    comparator: Literal["lt", "gt"]
    threshold: float
    #: Trailing window, 5 to 1440 (default 60).
    window_minutes: int
    #: Ratios and latency are not evaluated on fewer observations (default 20).
    min_sample: int
    #: Minimum minutes between notifications while the rule stays firing (default 60).
    cooldown_minutes: int
    email_contacts: list[str]
    #: A public HTTPS endpoint. The body is signed like any Atlas webhook; the signing secret is
    #: returned once, on create.
    webhook_url: str | None
    enabled: bool
    #: api_usage_spike only: watch secret keys, end-user API keys or organizations (null = all).
    subject_type: str | None
    #: api_usage_spike only: watch one key or organization (needs subject_type).
    subject_id: str | None
    #: Also raise a Shared Signals event (an opaque subject naming the key or organization) on
    #: every enabled stream that asks for it.
    ssf: bool


class AnalyticsAlertRulesUpdateResponse(TypedDict, total=False):
    object: Literal["analytics_alert_rule"]
    id: str
    name: str
    metric: Literal[
        "sign_in_success_rate",
        "failed_passkey_ratio",
        "failed_sign_ins",
        "sign_in_p95_seconds",
        "api_usage_spike",
    ]
    comparator: Literal["lt", "gt"]
    threshold: float
    window_minutes: int
    min_sample: int
    cooldown_minutes: int
    email_contacts: list[str]
    webhook_url: str | None
    has_webhook_secret: bool
    enabled: bool
    subject_type: str | None
    subject_id: str | None
    ssf: bool
    state: Literal["ok", "firing"]
    last_value: float | None
    last_evaluated_at: int | None
    last_triggered_at: int | None
    last_error: str | None
    created_at: int


class AnalyticsAlertRulesTestBody(TypedDict, total=False):
    notify: bool


class AnalyticsAlertRulesTestResponse(TypedDict, total=False):
    object: Literal["analytics_alert_test"]
    value: float | None
    sample: int
    subject: dict[str, Any] | None
    notified: bool
    error: str | None


class MarketingGetSettingsResponse(TypedDict, total=False):
    object: Literal["marketing_settings"]
    capture: dict[str, Any]
    scripts: dict[str, Any]


class MarketingUpdateSettingsBody(TypedDict, total=False):
    capture: dict[str, Any]
    scripts: dict[str, Any]


class MarketingUpdateSettingsResponse(TypedDict, total=False):
    object: Literal["marketing_settings"]
    capture: dict[str, Any]
    scripts: dict[str, Any]


class _AuditEventSchemasRegisterBodyRequired(TypedDict):
    #: e.g. invoice.sent
    action: str


class AuditEventSchemasRegisterBody(_AuditEventSchemasRegisterBodyRequired, total=False):
    version: int
    description: str
    target_types: list[str]
    actor_types: list[str]
    metadata_schema: dict[str, Any]


class AuditEventSchemasRegisterResponse(TypedDict, total=False):
    object: Literal["audit_event_schema"]
    id: str
    action: str
    version: int
    description: str | None
    #: Allowed target.type values; empty = any.
    target_types: list[str]
    #: Allowed actor.type values; empty = any.
    actor_types: list[str]
    #: A JSON Schema the event metadata must satisfy (type, required, properties,
    #: additionalProperties, enum, minimum/maximum, minLength/maxLength, pattern, format, items,
    #: minItems/maxItems).
    metadata_schema: dict[str, Any]
    status: Literal["active", "deprecated"]
    created_at: int


class AuditEventSchemasGetResponse(TypedDict, total=False):
    object: Literal["audit_event_schema"]
    id: str
    action: str
    version: int
    description: str | None
    #: Allowed target.type values; empty = any.
    target_types: list[str]
    #: Allowed actor.type values; empty = any.
    actor_types: list[str]
    #: A JSON Schema the event metadata must satisfy (type, required, properties,
    #: additionalProperties, enum, minimum/maximum, minLength/maxLength, pattern, format, items,
    #: minItems/maxItems).
    metadata_schema: dict[str, Any]
    status: Literal["active", "deprecated"]
    created_at: int


class AuditEventSchemasUpdateBody(TypedDict, total=False):
    description: str | None
    status: Literal["active", "deprecated"]


class AuditEventSchemasUpdateResponse(TypedDict, total=False):
    object: Literal["audit_event_schema"]
    id: str
    action: str
    version: int
    description: str | None
    #: Allowed target.type values; empty = any.
    target_types: list[str]
    #: Allowed actor.type values; empty = any.
    actor_types: list[str]
    #: A JSON Schema the event metadata must satisfy (type, required, properties,
    #: additionalProperties, enum, minimum/maximum, minLength/maxLength, pattern, format, items,
    #: minItems/maxItems).
    metadata_schema: dict[str, Any]
    status: Literal["active", "deprecated"]
    created_at: int


class AuditEventSchemasRedactBody(TypedDict):
    fields: list[str]
    reason: str


class AuditEventSchemasRedactResponse(TypedDict, total=False):
    object: Literal["audit_event_redaction"]
    event_id: str
    redacted: list[str]
    unchanged: list[str]
    reason: str


class _DirectoryPullSourcesCreateBodyRequired(TypedDict):
    organization_id: str
    name: str
    provider: Literal[
        "entra", "google_workspace", "bamboohr", "hibob", "personio", "csv", "rest_json"
    ]


class DirectoryPullSourcesCreateBody(_DirectoryPullSourcesCreateBodyRequired, total=False):
    status: Literal["active", "paused"]
    config: dict[str, Any]
    #: Write-only.
    credentials: dict[str, Any]
    default_role_id: str | None
    #: Schedule, role mappings and disable-on-removal.
    settings: dict[str, Any]


class DirectoryPullSourcesCreateResponse(TypedDict, total=False):
    object: Literal["directory_pull_source"]
    id: str
    organization_id: str
    name: str
    provider: Literal[
        "entra", "google_workspace", "bamboohr", "hibob", "personio", "csv", "rest_json"
    ]
    status: Literal["active", "paused"]
    config: dict[str, Any]
    settings: dict[str, Any]
    default_role_id: str | None
    has_credentials: bool
    has_uploaded_csv: bool
    next_sync_at: int | None
    created_at: int
    updated_at: int


class DirectoryPullSourcesGetResponse(TypedDict, total=False):
    object: Literal["directory_pull_source"]
    id: str
    organization_id: str
    name: str
    provider: Literal[
        "entra", "google_workspace", "bamboohr", "hibob", "personio", "csv", "rest_json"
    ]
    status: Literal["active", "paused"]
    config: dict[str, Any]
    settings: dict[str, Any]
    default_role_id: str | None
    has_credentials: bool
    has_uploaded_csv: bool
    next_sync_at: int | None
    created_at: int
    updated_at: int


class DirectoryPullSourcesUpdateBody(TypedDict, total=False):
    organization_id: str
    name: str
    provider: Literal[
        "entra", "google_workspace", "bamboohr", "hibob", "personio", "csv", "rest_json"
    ]
    status: Literal["active", "paused"]
    config: dict[str, Any]
    #: Write-only.
    credentials: dict[str, Any]
    default_role_id: str | None
    #: Schedule, role mappings and disable-on-removal.
    settings: dict[str, Any]


class DirectoryPullSourcesUpdateResponse(TypedDict, total=False):
    object: Literal["directory_pull_source"]
    id: str
    organization_id: str
    name: str
    provider: Literal[
        "entra", "google_workspace", "bamboohr", "hibob", "personio", "csv", "rest_json"
    ]
    status: Literal["active", "paused"]
    config: dict[str, Any]
    settings: dict[str, Any]
    default_role_id: str | None
    has_credentials: bool
    has_uploaded_csv: bool
    next_sync_at: int | None
    created_at: int
    updated_at: int


class DirectoryPullSourcesSetCsvBody(TypedDict, total=False):
    csv: str


class DirectoryPullSourcesSyncRunsCreateResponse(TypedDict, total=False):
    object: Literal["directory_pull_run"]
    id: str
    source_id: str
    organization_id: str
    trigger: str
    status: str
    stats: dict[str, Any]
    error: str | None
    created_at: int
    started_at: int | None
    finished_at: int | None


class DirectoryPullSourcesSyncRunsGetResponse(TypedDict, total=False):
    object: Literal["directory_pull_run"]
    id: str
    source_id: str
    organization_id: str
    trigger: str
    status: str
    stats: dict[str, Any]
    error: str | None
    created_at: int
    started_at: int | None
    finished_at: int | None


class OrgLdapConnectionsGetSyncResponse(TypedDict, total=False):
    object: Literal["ldap_sync_settings"]


class OrgLdapConnectionsSetSyncBody(TypedDict, total=False):
    enabled: bool
    intervalMinutes: float
    pageSize: float
    idAttribute: str
    userFilter: str | None
    groupBaseDN: str | None
    groupFilter: str
    groupMemberAttribute: str
    groupNameAttribute: str
    syncGroups: bool
    roleMappings: list[dict[str, Any]]
    disableOnRemoval: bool
    deltaAttribute: str


class OrgLdapConnectionsGetRelayResponse(TypedDict, total=False):
    object: Literal["ldap_relay"]
    agent_id: str | None


class OrgLdapConnectionsSetRelayBody(TypedDict, total=False):
    agent_id: str | None


class OrgLdapConnectionsSyncRunsCreateBody(TypedDict, total=False):
    kind: str


class OrgLdapConnectionsSyncRunsGetResponse(TypedDict, total=False):
    object: Literal["ldap_sync_run"]
    id: str
    connection_id: str
    organization_id: str
    kind: str
    trigger: str
    status: str
    stats: dict[str, Any]
    error: str | None
    created_at: int
    started_at: int | None
    finished_at: int | None


class _RelayAgentsCreateBodyRequired(TypedDict):
    name: str


class RelayAgentsCreateBody(_RelayAgentsCreateBodyRequired, total=False):
    organization_id: str | None
    status: Literal["active", "revoked"]
    #: host:port destinations the agent may reach.
    allowed_destinations: list[str]
    #: Client-certificate pins.
    cert_fingerprints: list[str]


class RelayAgentsCreateResponse(TypedDict, total=False):
    object: Literal["relay_agent"]
    id: str
    name: str
    organization_id: str | None
    status: Literal["active", "revoked"]
    allowed_destinations: list[str]
    cert_fingerprints: list[str]
    secret_prefix: str
    online: bool
    last_seen_at: int | None
    last_ip: str | None
    agent_version: str | None
    created_at: int
    #: On create and rotate only: the agent token, shown once.
    token: str


class RelayAgentsGetResponse(TypedDict, total=False):
    object: Literal["relay_agent"]
    id: str
    name: str
    organization_id: str | None
    status: Literal["active", "revoked"]
    allowed_destinations: list[str]
    cert_fingerprints: list[str]
    secret_prefix: str
    online: bool
    last_seen_at: int | None
    last_ip: str | None
    agent_version: str | None
    created_at: int
    #: On create and rotate only: the agent token, shown once.
    token: str


class RelayAgentsUpdateBody(TypedDict, total=False):
    name: str
    organization_id: str | None
    status: Literal["active", "revoked"]
    #: host:port destinations the agent may reach.
    allowed_destinations: list[str]
    #: Client-certificate pins.
    cert_fingerprints: list[str]


class RelayAgentsUpdateResponse(TypedDict, total=False):
    object: Literal["relay_agent"]
    id: str
    name: str
    organization_id: str | None
    status: Literal["active", "revoked"]
    allowed_destinations: list[str]
    cert_fingerprints: list[str]
    secret_prefix: str
    online: bool
    last_seen_at: int | None
    last_ip: str | None
    agent_version: str | None
    created_at: int
    #: On create and rotate only: the agent token, shown once.
    token: str


class RelayAgentsRotateSecretResponse(TypedDict, total=False):
    object: Literal["relay_agent"]
    id: str
    name: str
    organization_id: str | None
    status: Literal["active", "revoked"]
    allowed_destinations: list[str]
    cert_fingerprints: list[str]
    secret_prefix: str
    online: bool
    last_seen_at: int | None
    last_ip: str | None
    agent_version: str | None
    created_at: int
    #: On create and rotate only: the agent token, shown once.
    token: str


class OauthClientsGetExchangePolicyResponse(TypedDict, total=False):
    object: Literal["oauth_exchange_policy"]
    #: The OAuth client row id (oac_…).
    client_id: str
    #: Resource server identifiers the client may exchange for; null = any it holds a client grant
    #: on.
    allowed_audiences: list[str] | None
    #: Scope ceiling applied on top of the client grant; null = no extra limit.
    allowed_scopes: list[str] | None
    #: Resource authorization server issuers this client may request an ID-JAG (Cross App Access)
    #: for; null = none.
    id_jag_audiences: list[str] | None
    #: false = the client must present an actor_token (delegation only).
    allow_impersonation: bool
    #: true = delegation needs a subject token carrying may_act.
    require_may_act: bool
    #: Deepest act chain the client may produce (1 to 10).
    max_delegation_depth: int
    #: false = these are the defaults; no policy row exists.
    configured: bool


class OauthClientsSetExchangePolicyBody(TypedDict, total=False):
    allowed_audiences: list[str] | None
    allowed_scopes: list[str] | None
    id_jag_audiences: list[str] | None
    allow_impersonation: bool
    require_may_act: bool
    max_delegation_depth: int


class OauthClientsSetExchangePolicyResponse(TypedDict, total=False):
    object: Literal["oauth_exchange_policy"]
    #: The OAuth client row id (oac_…).
    client_id: str
    #: Resource server identifiers the client may exchange for; null = any it holds a client grant
    #: on.
    allowed_audiences: list[str] | None
    #: Scope ceiling applied on top of the client grant; null = no extra limit.
    allowed_scopes: list[str] | None
    #: Resource authorization server issuers this client may request an ID-JAG (Cross App Access)
    #: for; null = none.
    id_jag_audiences: list[str] | None
    #: false = the client must present an actor_token (delegation only).
    allow_impersonation: bool
    #: true = delegation needs a subject token carrying may_act.
    require_may_act: bool
    #: Deepest act chain the client may produce (1 to 10).
    max_delegation_depth: int
    #: false = these are the defaults; no policy row exists.
    configured: bool


class OauthClientsSetProfileBody(TypedDict):
    #: A built-in or custom profile name; null clears.
    profile: str | None


class OauthClientsSetProfileResponse(TypedDict, total=False):
    object: Literal["oauth_client_profile_assignment"]
    client_id: str
    profile: str | None


class OauthClientsSetDelegatedUiBody(TypedDict, total=False):
    #: https URL of your sign-in page; null clears it. Omit to leave unchanged.
    login_url: str | None
    #: https URL of your consent page; null clears it. Omit to leave unchanged.
    consent_url: str | None


class OauthClientsSetDelegatedUiResponse(TypedDict, total=False):
    object: Literal["oauth_client_delegated_ui"]
    client_id: str
    login_url: str | None
    consent_url: str | None


class OauthClientsAppSettingsGetResponse(TypedDict, total=False):
    object: Literal["app_settings"]
    client_id: str
    #: The sign-in methods a session must have used for this app: password, email_code, email_link,
    #: passkey, phone_code, siwe, siws, siwf, a provider such as oauth_google, or the families
    #: oauth (any social provider) and enterprise_sso (any enterprise connection). The hosted pages
    #: offer only these when the
    allowed_sign_in_methods: list[str] | None
    #: The heading, sub-heading, logo and primary colour of the hosted sign-in and sign-up pages
    #: when the sign-in is for this app.
    branding: dict[str, Any] | None
    #: The user claims this app receives in its ID token and from userinfo (for example email,
    #: name, org_id). Protocol claims (iss, sub, aud, exp, iat, nonce, auth_time, acr, amr, azp,
    #: sid) always pass. [] = protocol claims only.
    claims_allowlist: list[str] | None
    #: The identity traits a session that came from this app (a native app that exchanged its token
    #: for a session) may change through PATCH /v1/client/me. Others are refused with 403.
    writable_traits: list[str] | None
    #: Overrides of the instance's riskBasedMfa for sign-ins to this app (a sign-in started from
    #: this app's /oauth2/authorize request). A field left null keeps the instance value; weights,
    #: signals and reputation feeds stay instance-wide.
    risk: dict[str, Any] | None


class OauthClientsAppSettingsUpdateBody(TypedDict, total=False):
    #: The sign-in methods a session must have used for this app: password, email_code, email_link,
    #: passkey, phone_code, siwe, siws, siwf, a provider such as oauth_google, or the families
    #: oauth (any social provider) and enterprise_sso (any enterprise connection). The hosted pages
    #: offer only these when the
    allowed_sign_in_methods: list[str] | None
    #: The heading, sub-heading, logo and primary colour of the hosted sign-in and sign-up pages
    #: when the sign-in is for this app.
    branding: dict[str, Any] | None
    #: The user claims this app receives in its ID token and from userinfo (for example email,
    #: name, org_id). Protocol claims (iss, sub, aud, exp, iat, nonce, auth_time, acr, amr, azp,
    #: sid) always pass. [] = protocol claims only.
    claims_allowlist: list[str] | None
    #: The identity traits a session that came from this app (a native app that exchanged its token
    #: for a session) may change through PATCH /v1/client/me. Others are refused with 403.
    writable_traits: list[str] | None
    #: Overrides of the instance's riskBasedMfa for sign-ins to this app (a sign-in started from
    #: this app's /oauth2/authorize request). A field left null keeps the instance value; weights,
    #: signals and reputation feeds stay instance-wide.
    risk: dict[str, Any] | None


class OauthClientsAppSettingsUpdateResponse(TypedDict, total=False):
    object: Literal["app_settings"]
    client_id: str
    #: The sign-in methods a session must have used for this app: password, email_code, email_link,
    #: passkey, phone_code, siwe, siws, siwf, a provider such as oauth_google, or the families
    #: oauth (any social provider) and enterprise_sso (any enterprise connection). The hosted pages
    #: offer only these when the
    allowed_sign_in_methods: list[str] | None
    #: The heading, sub-heading, logo and primary colour of the hosted sign-in and sign-up pages
    #: when the sign-in is for this app.
    branding: dict[str, Any] | None
    #: The user claims this app receives in its ID token and from userinfo (for example email,
    #: name, org_id). Protocol claims (iss, sub, aud, exp, iat, nonce, auth_time, acr, amr, azp,
    #: sid) always pass. [] = protocol claims only.
    claims_allowlist: list[str] | None
    #: The identity traits a session that came from this app (a native app that exchanged its token
    #: for a session) may change through PATCH /v1/client/me. Others are refused with 403.
    writable_traits: list[str] | None
    #: Overrides of the instance's riskBasedMfa for sign-ins to this app (a sign-in started from
    #: this app's /oauth2/authorize request). A field left null keeps the instance value; weights,
    #: signals and reputation feeds stay instance-wide.
    risk: dict[str, Any] | None


class OauthClientsWorkloadIdentityCloudTrustResponse(TypedDict, total=False):
    object: Literal["workload_cloud_trust"]
    provider: Literal["aws", "gcp", "azure"]
    steps: list[str]
    #: AWS IAM role trust policy.
    trust_policy: dict[str, Any]
    #: GCP workload identity pool provider settings.
    provider_config: dict[str, Any]
    #: GCP principal to grant roles/iam.workloadIdentityUser.
    principal: str
    #: Azure federated identity credential.
    federated_credential: dict[str, Any]
    token_endpoint: str


class _OauthClientsTrustedIssuersCreateBodyRequired(TypedDict):
    issuer: str


class OauthClientsTrustedIssuersCreateBody(
    _OauthClientsTrustedIssuersCreateBodyRequired, total=False
):
    #: Inline JWK Set. Provide exactly one of jwks or jwks_uri.
    jwks: dict[str, Any]
    #: https URL of the issuer JWK Set. Provide exactly one of jwks or jwks_uri.
    jwks_uri: str
    subject_mapping: Literal["user_id", "external_id", "email"]
    #: Fills in issuer and jwks_uri for github_actions, gcp and azure when you omit them.
    workload_kind: Literal["generic", "spiffe", "kubernetes", "github_actions", "gcp", "azure"]
    #: Required for workload_kind azure (without an explicit issuer).
    tenant_id: str
    purpose: Literal["user_assertion", "client_auth", "both"]
    #: Required when purpose is client_auth or both. A glob with * wildcards; a bare * is refused.
    subject_pattern: str
    #: Extra claims that must match exactly.
    required_claims: dict[str, Any]
    #: Accepted aud values. Defaults to the token endpoint, the PAR endpoint and the issuer.
    audiences: list[str]


class OauthClientsTrustedIssuersCreateResponse(TypedDict, total=False):
    object: Literal["oauth_trusted_issuer"]
    id: str
    #: The OAuth client row id (oac_…) that trusts this issuer.
    client_id: str
    #: The `iss` its JWTs carry.
    issuer: str
    #: Inline JWK Set, or null when jwks_uri is used.
    jwks: dict[str, Any] | None
    jwks_uri: str | None
    #: How the JWT `sub` names an Atlas user.
    subject_mapping: Literal["user_id", "external_id", "email"]
    #: The kind of workload platform issuing the tokens; it only supplies defaults.
    workload_kind: Literal["generic", "spiffe", "kubernetes", "github_actions", "gcp", "azure"]
    #: Whether the issuer asserts users (jwt-bearer grant), authenticates the client itself
    #: (workload_jwt), or both.
    purpose: Literal["user_assertion", "client_auth", "both"]
    #: Glob (* wildcard) the workload token `sub` must match.
    subject_pattern: str | None
    #: Claims that must equal these string values.
    required_claims: dict[str, Any] | None
    #: Accepted `aud` values for a workload token; null means the token endpoint and the issuer.
    audiences: list[str] | None
    #: Created (epoch ms).
    created_at: int


class OauthClientsLoginRequestsGetResponse(TypedDict, total=False):
    object: Literal["oauth_login_request"]
    client: dict[str, Any]
    requested_scope: list[str]
    audience: str | None
    #: sign-up when the application asked for prompt=create.
    page: Literal["sign-in", "sign-up"]
    #: The Atlas user already signed in on this browser, if any.
    session_subject: str | None
    ui_locales: str | None
    login_hint: str | None
    #: The challenge expires (epoch ms).
    expires_at: int


class _OauthClientsLoginRequestsAcceptBodyRequired(TypedDict):
    #: The Atlas user id the visitor authenticated as.
    subject: str


class OauthClientsLoginRequestsAcceptBody(
    _OauthClientsLoginRequestsAcceptBodyRequired, total=False
):
    #: Keep the Atlas session across browser restarts.
    remember: bool
    #: Authentication methods used, recorded on the session and echoed in the id_token.
    amr: list[str]
    #: Authentication context class reached.
    acr: str


class OauthClientsLoginRequestsAcceptResponse(TypedDict, total=False):
    object: Literal["oauth_login_redirect"]
    #: Send the end user’s browser here next.
    redirect_to: str


class OauthClientsLoginRequestsRejectBody(TypedDict, total=False):
    #: The OAuth error returned to the application. Default access_denied.
    error: Literal[
        "access_denied",
        "login_required",
        "interaction_required",
        "consent_required",
        "account_selection_required",
        "unauthorized_client",
        "temporarily_unavailable",
        "server_error",
    ]
    error_description: str


class OauthClientsLoginRequestsRejectResponse(TypedDict, total=False):
    object: Literal["oauth_login_redirect"]
    #: Send the end user’s browser here next.
    redirect_to: str


class OauthClientsConsentRequestsGetResponse(TypedDict, total=False):
    object: Literal["oauth_consent_request"]
    #: The signed-in Atlas user id.
    subject: str
    client: dict[str, Any]
    requested_scope: list[str]
    audience: str | None
    authorization_details: list[dict[str, Any]]
    organization_id: str | None
    redirect_uri: str
    #: The challenge expires (epoch ms).
    expires_at: int


class OauthClientsConsentRequestsAcceptBody(TypedDict, total=False):
    #: The scopes to grant: a subset of requested_scope that includes openid. Default: all
    #: requested.
    grant_scope: list[str]
    #: Record the consent so the user is not asked again. Default true.
    remember: bool


class OauthClientsConsentRequestsAcceptResponse(TypedDict, total=False):
    object: Literal["oauth_consent_redirect"]
    #: Send the end user’s browser here next.
    redirect_to: str


class OauthClientsConsentRequestsRejectBody(TypedDict, total=False):
    #: The OAuth error returned to the application. Default access_denied.
    error: Literal[
        "access_denied",
        "login_required",
        "interaction_required",
        "consent_required",
        "account_selection_required",
        "unauthorized_client",
        "temporarily_unavailable",
        "server_error",
    ]
    error_description: str


class OauthClientsConsentRequestsRejectResponse(TypedDict, total=False):
    object: Literal["oauth_consent_redirect"]
    #: Send the end user’s browser here next.
    redirect_to: str


class OrganizationsGetConnectionSecretResponse(TypedDict):
    object: Literal["connection_secret"]
    connection_id: str
    kind: Literal["api_key", "bearer", "basic", "custom_header", "hmac_secret"]
    #: The vault version that was read.
    version: int
    #: The credential's fields. api_key: {api_key}. bearer: {token}. basic: {username, password}.
    #: custom_header: {value}. hmac_secret: {secret}.
    secret: dict[str, Any]
    #: The non-secret settings (placement, header name, algorithm...) needed to apply it.
    config: dict[str, Any]
    #: When the credential expires, epoch ms.
    expires_at: int | None


class OrganizationsWebhookEndpointsCreateBody(TypedDict, total=False):
    #: The HTTPS receiver (any public URL that answers 2xx).
    url: str
    #: Event types to receive, or ["*"]. Only events that belong to this organization are ever
    #: delivered.
    enabled_events: list[str]
    #: A label, up to 500 characters.
    description: str | None
    #: Set false to pause deliveries.
    active: bool


class _OrganizationsWebhookEndpointsGetResponseRequired(TypedDict):
    object: Literal["webhook_endpoint"]
    id: str
    #: The HTTPS receiver; for an event destination, a descriptor such as
    #: aws-eventbridge://us-east-1/default.
    url: str
    enabled_events: list[str]
    active: bool
    #: Start of the current failure streak (epoch ms), or null when the last delivery succeeded.
    failing_since: int | None
    #: When the endpoint was switched off after repeated failures (epoch ms), or null.
    disabled_at: int | None
    #: Created (epoch ms).
    created_at: int


class OrganizationsWebhookEndpointsGetResponse(
    _OrganizationsWebhookEndpointsGetResponseRequired, total=False
):
    description: str | None
    #: Which names `*` delivers under: canonical, or the pre-convention spellings (endpoints
    #: created before the canonical catalogue).
    event_naming: Literal["canonical", "legacy"]
    #: A third-party receiver: preflight does not flag its host as off-origin.
    external: bool
    signature_versions: list[Literal["v1", "v2"]]
    #: Where deliveries go: { type: "https" } or an event destination with its non-secret settings.
    #: Credentials are never returned (credentials_set says whether they are stored).
    destination: dict[str, Any]
    health: Literal["healthy", "failing", "disabled"]
    #: Start of the failure streak that preceded the last re-enable (epoch ms); what replay
    #: resolves since=failing_since to once the live streak is cleared.
    last_failing_since: int | None
    last_success_at: int | None
    last_failure: dict[str, Any] | None
    consecutive_failures: int
    #: Share of attempts in the last 24 hours that succeeded (0–1), null with no attempts.
    success_rate_24h: float | None
    attempts_24h: dict[str, Any]
    #: Who is emailed when it fails; null = the owners of the account.
    alert_contacts: list[str] | None
    #: Alerts sent for the current streak: first (1 hour), second (24 hours) and the disabled
    #: notice (epoch ms or null).
    alerts_sent: dict[str, Any]
    auto_disable: dict[str, Any]
    #: While a secret rotation overlap is open: when the previous secret stops signing deliveries
    #: (epoch ms). Until then every delivery carries two signatures. Null otherwise.
    previous_secret_expires_at: int | None
    #: On an update that re-enabled the endpoint: the call that replays what it missed.
    replay: dict[str, Any] | None
    #: On create and PUT by_url: whether this call created the endpoint.
    created: bool
    #: Last changed (epoch ms).
    updated_at: int


class OrganizationsWebhookEndpointsUpdateBody(TypedDict, total=False):
    #: The HTTPS receiver (any public URL that answers 2xx).
    url: str
    #: Event types to receive, or ["*"]. Only events that belong to this organization are ever
    #: delivered.
    enabled_events: list[str]
    #: A label, up to 500 characters.
    description: str | None
    #: Set false to pause deliveries.
    active: bool


class _OrganizationsWebhookEndpointsUpdateResponseRequired(TypedDict):
    object: Literal["webhook_endpoint"]
    id: str
    #: The HTTPS receiver; for an event destination, a descriptor such as
    #: aws-eventbridge://us-east-1/default.
    url: str
    enabled_events: list[str]
    active: bool
    #: Start of the current failure streak (epoch ms), or null when the last delivery succeeded.
    failing_since: int | None
    #: When the endpoint was switched off after repeated failures (epoch ms), or null.
    disabled_at: int | None
    #: Created (epoch ms).
    created_at: int


class OrganizationsWebhookEndpointsUpdateResponse(
    _OrganizationsWebhookEndpointsUpdateResponseRequired, total=False
):
    description: str | None
    #: Which names `*` delivers under: canonical, or the pre-convention spellings (endpoints
    #: created before the canonical catalogue).
    event_naming: Literal["canonical", "legacy"]
    #: A third-party receiver: preflight does not flag its host as off-origin.
    external: bool
    signature_versions: list[Literal["v1", "v2"]]
    #: Where deliveries go: { type: "https" } or an event destination with its non-secret settings.
    #: Credentials are never returned (credentials_set says whether they are stored).
    destination: dict[str, Any]
    health: Literal["healthy", "failing", "disabled"]
    #: Start of the failure streak that preceded the last re-enable (epoch ms); what replay
    #: resolves since=failing_since to once the live streak is cleared.
    last_failing_since: int | None
    last_success_at: int | None
    last_failure: dict[str, Any] | None
    consecutive_failures: int
    #: Share of attempts in the last 24 hours that succeeded (0–1), null with no attempts.
    success_rate_24h: float | None
    attempts_24h: dict[str, Any]
    #: Who is emailed when it fails; null = the owners of the account.
    alert_contacts: list[str] | None
    #: Alerts sent for the current streak: first (1 hour), second (24 hours) and the disabled
    #: notice (epoch ms or null).
    alerts_sent: dict[str, Any]
    auto_disable: dict[str, Any]
    #: While a secret rotation overlap is open: when the previous secret stops signing deliveries
    #: (epoch ms). Until then every delivery carries two signatures. Null otherwise.
    previous_secret_expires_at: int | None
    #: On an update that re-enabled the endpoint: the call that replays what it missed.
    replay: dict[str, Any] | None
    #: On create and PUT by_url: whether this call created the endpoint.
    created: bool
    #: Last changed (epoch ms).
    updated_at: int


class OrganizationsWebhookEndpointsRotateSecretResponse(TypedDict):
    object: Literal["webhook_secret"]
    #: The new signing secret. Returned exactly once.
    secret: str
    overlap_seconds: int
    previous_secret_expires_at: int | None


class OauthClientProfilesSetBody(TypedDict, total=False):
    description: str | None
    require_pkce: bool
    #: Authorization requests must be pushed (RFC 9126).
    require_par: bool
    #: The token request must prove DPoP, mutual TLS, or either (any).
    sender_constraint: Literal["none", "dpop", "mtls", "any"]
    #: Authorization requests must be a signed request object (RFC 9101), pushed or direct.
    require_signed_request: bool
    #: Allowed client authentication methods; null = any.
    token_endpoint_auth_methods: list[str] | None
    #: JWS algorithms accepted for request objects and client assertions; null = any asymmetric.
    signing_algs: list[str] | None
    https_redirects_only: bool
    #: Claim names a `claims` request may ask for; null = any.
    allowed_claims: list[str] | None


class OauthClientProfilesSetResponse(TypedDict, total=False):
    object: Literal["oauth_client_profile"]
    name: str
    builtin: bool
    description: str | None
    require_pkce: bool
    #: Authorization requests must be pushed (RFC 9126).
    require_par: bool
    #: The token request must prove DPoP, mutual TLS, or either (any).
    sender_constraint: Literal["none", "dpop", "mtls", "any"]
    #: Authorization requests must be a signed request object (RFC 9101), pushed or direct.
    require_signed_request: bool
    #: Allowed client authentication methods; null = any.
    token_endpoint_auth_methods: list[str] | None
    #: JWS algorithms accepted for request objects and client assertions; null = any asymmetric.
    signing_algs: list[str] | None
    https_redirects_only: bool
    #: Claim names a `claims` request may ask for; null = any.
    allowed_claims: list[str] | None


class _PasskeyApiRegistrationInitBodyRequired(TypedDict):
    #: Your own user id. Atlas stores it with the passkey and never needs a matching Atlas user.
    user_id: str


class PasskeyApiRegistrationInitBody(_PasskeyApiRegistrationInitBodyRequired, total=False):
    #: Shown by the authenticator. Defaults to user_id.
    username: str
    display_name: str


class PasskeyApiRegistrationInitResponse(TypedDict, total=False):
    object: Literal["passkey_registration_options"]
    #: Login only: send back to finalize with the browser response.
    handle: str
    #: Pass to navigator.credentials.create() / get() in the user’s browser (challenge is
    #: base64url).
    options: dict[str, Any]


class _PasskeyApiRegistrationFinalizeBodyRequired(TypedDict):
    #: Your own user id. Atlas stores it with the passkey and never needs a matching Atlas user.
    user_id: str
    challenge: str
    #: base64url.
    attestation_object: str
    #: base64url.
    client_data_json: str


class PasskeyApiRegistrationFinalizeBody(_PasskeyApiRegistrationFinalizeBodyRequired, total=False):
    name: str
    transports: list[str]


class PasskeyApiRegistrationFinalizeResponse(TypedDict, total=False):
    object: Literal["external_passkey"]
    id: str
    user_id: str
    credential_id: str
    name: str | None
    aaguid: str | None
    backed_up: bool
    transports: list[str]
    #: Last successful login (epoch ms).
    last_used_at: int | None
    #: Registered (epoch ms).
    created_at: int


class PasskeyApiLoginInitBody(TypedDict, total=False):
    #: Your own user id. Atlas stores it with the passkey and never needs a matching Atlas user.
    user_id: str


class PasskeyApiLoginInitResponse(TypedDict, total=False):
    object: Literal["passkey_login_options"]
    #: Login only: send back to finalize with the browser response.
    handle: str
    #: Pass to navigator.credentials.create() / get() in the user’s browser (challenge is
    #: base64url).
    options: dict[str, Any]


class _PasskeyApiLoginFinalizeBodyRequired(TypedDict):
    handle: str
    challenge: str
    credential_id: str
    authenticator_data: str
    client_data_json: str
    signature: str


class PasskeyApiLoginFinalizeBody(_PasskeyApiLoginFinalizeBodyRequired, total=False):
    #: Your own user id. Atlas stores it with the passkey and never needs a matching Atlas user.
    user_id: str


class PasskeyApiLoginFinalizeResponse(TypedDict, total=False):
    object: Literal["passkey_login_result"]
    verified: bool
    user_id: str
    credential_id: str
    passkey_id: str
    user_verified: bool
    #: The signature counter went backwards: possible cloned authenticator.
    cloned_warning: bool


class PasskeyApiUsageResponse(TypedDict, total=False):
    object: Literal["passkey_api_usage"]
    passkeys: int


class _VcCreateOfferBodyRequired(TypedDict):
    credential_type_id: str
    user_id: str


class VcCreateOfferBody(_VcCreateOfferBodyRequired, total=False):
    #: 4 to 8 digits the wallet must send, delivered to the user separately.
    tx_code: str
    #: Default 600.
    expires_in_seconds: int


class VcCreateOfferResponse(TypedDict, total=False):
    object: Literal["vc_offer"]
    id: str
    #: Expires (epoch ms).
    expires_at: int
    credential_offer: dict[str, Any]
    credential_offer_uri: str


class _VcCredentialTypesCreateBodyRequired(TypedDict):
    #: The credential type identifier (a URN or URL); for mso_mdoc the docType, for example
    #: org.iso.18013.5.1.mDL.
    vct: str
    name: str
    claims: list[dict[str, Any]]


class VcCredentialTypesCreateBody(_VcCredentialTypesCreateBodyRequired, total=False):
    #: Default dc+sd-jwt. mso_mdoc issues an ISO 18013-5 mdoc (ES256, holder key P-256).
    format: Literal["dc+sd-jwt", "mso_mdoc"]
    #: mso_mdoc only: the namespace the claims live in (default the docType).
    namespace: str
    #: mso_mdoc only: PEM IACA root certificates (ISO 18013-5 Annex B). With roots set, a
    #: presentation must carry an x5chain leading to one of them and the issuer signature must
    #: verify under its Document Signer key; bare trusted keys are then not accepted.
    iaca_roots: list[str]
    #: mso_mdoc only: PEM Document Signer certificate first, then intermediates, published as
    #: x5chain. The first certificate must be for this instance’s mdoc signing key (the ES256 key
    #: in its key set), otherwise 400.
    signer_chain: list[str]
    #: Default one year.
    lifetime_seconds: int
    require_wallet_attestation: bool
    #: JWK Set of accepted wallet providers; required with require_wallet_attestation.
    wallet_attestation_jwks: dict[str, Any]


class VcCredentialTypesCreateResponse(TypedDict, total=False):
    object: Literal["vc_credential_type"]
    id: str
    #: The credential type (SD-JWT VC) or the docType (mdoc).
    vct: str
    format: Literal["dc+sd-jwt", "mso_mdoc"]
    #: mdoc namespace of the claims.
    namespace: str | None
    #: mdoc: PEM IACA root certificates. When set, presentations of this type are accepted only
    #: with an x5chain that leads to one of them.
    iaca_roots: list[str]
    #: mdoc: PEM Document Signer certificate (then intermediates) published as x5chain in issued
    #: mdocs.
    signer_chain: list[str]
    name: str
    claims: list[dict[str, Any]]
    lifetime_seconds: int
    require_wallet_attestation: bool
    #: Created (epoch ms).
    created_at: int


class VcCredentialTypesGetResponse(TypedDict, total=False):
    object: Literal["vc_credential_type"]
    id: str
    #: The credential type (SD-JWT VC) or the docType (mdoc).
    vct: str
    format: Literal["dc+sd-jwt", "mso_mdoc"]
    #: mdoc namespace of the claims.
    namespace: str | None
    #: mdoc: PEM IACA root certificates. When set, presentations of this type are accepted only
    #: with an x5chain that leads to one of them.
    iaca_roots: list[str]
    #: mdoc: PEM Document Signer certificate (then intermediates) published as x5chain in issued
    #: mdocs.
    signer_chain: list[str]
    name: str
    claims: list[dict[str, Any]]
    lifetime_seconds: int
    require_wallet_attestation: bool
    #: Created (epoch ms).
    created_at: int


class VcCredentialsRevokeResponse(TypedDict, total=False):
    object: Literal["vc_credential"]
    id: str
    credential_type_id: str
    user_id: str
    #: Position in the published status list.
    status_idx: int
    #: Issued (epoch ms).
    issued_at: int
    #: Expires (epoch ms).
    expires_at: int
    revoked_at: int | None


class _VcPresentationRequestsCreateBodyRequired(TypedDict):
    #: The vct, or the docType for mso_mdoc.
    vct: str


class VcPresentationRequestsCreateBody(_VcPresentationRequestsCreateBodyRequired, total=False):
    #: Default dc+sd-jwt.
    format: Literal["dc+sd-jwt", "mso_mdoc"]
    #: mso_mdoc only: PEM IACA roots for this request; overrides the credential type’s. Certificate
    #: chain mode only: no bare key is accepted when roots apply.
    iaca_roots: list[str]
    #: Claims the wallet must disclose.
    claims: list[str]
    #: Other issuers accepted besides this instance.
    trusted_issuers: list[dict[str, Any]]
    #: Default 600.
    expires_in_seconds: int


class VcPresentationRequestsCreateResponse(TypedDict, total=False):
    object: Literal["vc_presentation_request"]
    id: str
    vct: str
    format: Literal["dc+sd-jwt", "mso_mdoc"]
    iaca_roots: list[str]
    claims: list[str]
    status: Literal["pending", "verified", "failed"]
    #: When verified: issuer, vct and the disclosed claims.
    result: dict[str, Any] | None
    error: str | None
    #: When the credential was issued by this instance: the user it was issued to.
    user_id: str | None
    #: Expires (epoch ms).
    expires_at: int
    request_uri: str
    #: The openid4vp:// link for a QR code or deep link.
    authorization_request_uri: str


class VcPresentationRequestsGetResponse(TypedDict, total=False):
    object: Literal["vc_presentation_request"]
    id: str
    vct: str
    format: Literal["dc+sd-jwt", "mso_mdoc"]
    iaca_roots: list[str]
    claims: list[str]
    status: Literal["pending", "verified", "failed"]
    #: When verified: issuer, vct and the disclosed claims.
    result: dict[str, Any] | None
    error: str | None
    #: When the credential was issued by this instance: the user it was issued to.
    user_id: str | None
    #: Expires (epoch ms).
    expires_at: int
    request_uri: str
    #: The openid4vp:// link for a QR code or deep link.
    authorization_request_uri: str


class ListenCreateSessionBody(TypedDict, total=False):
    #: Event types or patterns to forward, such as `user.created` or `user.*`. Omit for every
    #: event.
    events: list[str]
    #: How long the session lives. Default 3600.
    ttl_seconds: int


class ListenCreateSessionResponse(TypedDict, total=False):
    object: Literal["listen_session"]
    id: str
    #: Verify forwarded deliveries with this secret, exactly like a webhook signing secret.
    secret: str
    events: list[str]
    #: Epoch milliseconds.
    expires_at: int
    stream_url: str


class AgentRegistrationGetResponse(TypedDict, total=False):
    object: Literal["agent_registration"]
    enabled: bool
    allow_anonymous: bool
    allow_service_auth: bool
    allow_refresh: bool
    untrusted_scopes: list[str]
    trusted_scopes: list[str]
    claim_ttl_seconds: int
    auto_approve_rules: list[dict[str, Any]]


class AgentRegistrationReplaceBody(TypedDict, total=False):
    enabled: bool
    allow_anonymous: bool
    allow_service_auth: bool
    allow_refresh: bool
    untrusted_scopes: list[str]
    trusted_scopes: list[str]
    claim_ttl_seconds: int
    #: Access requests from a trusted agent matching a rule are approved automatically.
    auto_approve_rules: list[dict[str, Any]]


class AgentsClaimBody(TypedDict):
    user_id: str


class AgentsSetOwnerBody(TypedDict):
    user_id: str | None


class AgentsRevokeAccessBody(TypedDict, total=False):
    disable: bool


class AgentAccessRequestsApproveBody(TypedDict, total=False):
    expires_in_seconds: int
    decided_by: str


class AgentAccessRequestsDenyBody(TypedDict, total=False):
    decided_by: str


class WorkflowsCreateBody(TypedDict, total=False):
    name: str
    description: str | None
    enabled: bool
    trigger: dict[str, Any]
    steps: list[dict[str, Any]]


class _WorkflowsCreateResponseRequired(TypedDict):
    object: Literal["workflow"]
    id: str
    name: str
    enabled: bool
    #: What starts a run: `cron`, `user_created`, `inactive`, `membership_age`, `trial_end` or
    #: `webhook_event`, with that trigger's fields.
    trigger: dict[str, Any]
    #: The ordered steps (1 to 20): `notify`, `disable`, `delete`, `invite`, `add_to_org`,
    #: `remove_from_org`, `add_to_team`, `remove_from_team`, `add_to_group`, `remove_from_group`,
    #: `call_action`.
    steps: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class WorkflowsCreateResponse(_WorkflowsCreateResponseRequired, total=False):
    description: str | None
    #: A cron workflow's next slot, Unix ms; null for any other trigger.
    next_run_at: int | None


class _WorkflowsGetResponseRequired(TypedDict):
    object: Literal["workflow"]
    id: str
    name: str
    enabled: bool
    #: What starts a run: `cron`, `user_created`, `inactive`, `membership_age`, `trial_end` or
    #: `webhook_event`, with that trigger's fields.
    trigger: dict[str, Any]
    #: The ordered steps (1 to 20): `notify`, `disable`, `delete`, `invite`, `add_to_org`,
    #: `remove_from_org`, `add_to_team`, `remove_from_team`, `add_to_group`, `remove_from_group`,
    #: `call_action`.
    steps: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class WorkflowsGetResponse(_WorkflowsGetResponseRequired, total=False):
    description: str | None
    #: A cron workflow's next slot, Unix ms; null for any other trigger.
    next_run_at: int | None


class WorkflowsUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    enabled: bool
    trigger: dict[str, Any]
    steps: list[dict[str, Any]]


class _WorkflowsUpdateResponseRequired(TypedDict):
    object: Literal["workflow"]
    id: str
    name: str
    enabled: bool
    #: What starts a run: `cron`, `user_created`, `inactive`, `membership_age`, `trial_end` or
    #: `webhook_event`, with that trigger's fields.
    trigger: dict[str, Any]
    #: The ordered steps (1 to 20): `notify`, `disable`, `delete`, `invite`, `add_to_org`,
    #: `remove_from_org`, `add_to_team`, `remove_from_team`, `add_to_group`, `remove_from_group`,
    #: `call_action`.
    steps: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class WorkflowsUpdateResponse(_WorkflowsUpdateResponseRequired, total=False):
    description: str | None
    #: A cron workflow's next slot, Unix ms; null for any other trigger.
    next_run_at: int | None


class WorkflowsDryRunBody(TypedDict, total=False):
    user_id: str
    organization_id: str


class _WorkflowsDryRunResponseRequired(TypedDict):
    object: Literal["workflow_run"]
    id: str
    workflow_id: str
    #: What the run was for: `user:<id>`, `event:<id>`, `cron:<slot>`, `membership:<id>`,
    #: `trial:<id>:<end>`, `inactive:<id>:<last>` or `manual:<ms>:<user>`.
    subject: str
    dry_run: bool
    status: Literal["running", "succeeded", "failed"]
    steps: list[dict[str, Any]]
    #: Started (epoch ms).
    started_at: int


class WorkflowsDryRunResponse(_WorkflowsDryRunResponseRequired, total=False):
    user_id: str | None
    error: str | None
    #: Finished, Unix ms.
    finished_at: int | None


class WorkflowsRunBody(TypedDict, total=False):
    user_id: str
    organization_id: str


class _WorkflowsRunResponseRequired(TypedDict):
    object: Literal["workflow_run"]
    id: str
    workflow_id: str
    #: What the run was for: `user:<id>`, `event:<id>`, `cron:<slot>`, `membership:<id>`,
    #: `trial:<id>:<end>`, `inactive:<id>:<last>` or `manual:<ms>:<user>`.
    subject: str
    dry_run: bool
    status: Literal["running", "succeeded", "failed"]
    steps: list[dict[str, Any]]
    #: Started (epoch ms).
    started_at: int


class WorkflowsRunResponse(_WorkflowsRunResponseRequired, total=False):
    user_id: str | None
    error: str | None
    #: Finished, Unix ms.
    finished_at: int | None


class PageTemplatesGetResponse(TypedDict):
    object: Literal["page_template"]
    page: Literal["sign-in", "sign-up", "user-profile"]
    #: The template the hosted page renders: `{ version, updated_at, definition }`.
    live: dict[str, Any] | None
    #: The unpublished template, visible only behind a preview link.
    draft: dict[str, Any] | None


class PageTemplatesSaveDraftBody(TypedDict, total=False):
    definition: dict[str, Any]


class PageTemplatesSaveDraftResponse(TypedDict):
    object: Literal["page_template"]
    page: Literal["sign-in", "sign-up", "user-profile"]
    #: The template the hosted page renders: `{ version, updated_at, definition }`.
    live: dict[str, Any] | None
    #: The unpublished template, visible only behind a preview link.
    draft: dict[str, Any] | None


class PageTemplatesDiscardResponse(TypedDict):
    object: Literal["page_template"]
    page: Literal["sign-in", "sign-up", "user-profile"]
    #: The template the hosted page renders: `{ version, updated_at, definition }`.
    live: dict[str, Any] | None
    #: The unpublished template, visible only behind a preview link.
    draft: dict[str, Any] | None


class PageTemplatesPreviewResponse(TypedDict):
    object: Literal["page_template_preview"]
    page: str
    url: str
    #: Link expires (epoch ms).
    expires_at: int


class PageTemplatesPromoteResponse(TypedDict):
    object: Literal["page_template"]
    page: Literal["sign-in", "sign-up", "user-profile"]
    #: The template the hosted page renders: `{ version, updated_at, definition }`.
    live: dict[str, Any] | None
    #: The unpublished template, visible only behind a preview link.
    draft: dict[str, Any] | None


class ServiceConnectorsCreateBody(TypedDict, total=False):
    name: str
    kind: str
    config: dict[str, Any]
    credentials: dict[str, Any]


class ServiceConnectorsCreateResponse(TypedDict):
    object: Literal["service_connector"]
    id: str
    #: Unique within the instance; what Actions and flows call it by.
    name: str
    #: The catalog entry, e.g. `twilio`, `segment`, `persona`, `http`.
    kind: str
    category: str | None
    #: The non-secret settings. Credentials are never returned.
    config: dict[str, Any]
    enabled: bool
    #: When an operation last ran (epoch ms).
    last_used_at: int | None
    last_status: str | None
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class ServiceConnectorsGetResponse(TypedDict):
    object: Literal["service_connector"]
    id: str
    #: Unique within the instance; what Actions and flows call it by.
    name: str
    #: The catalog entry, e.g. `twilio`, `segment`, `persona`, `http`.
    kind: str
    category: str | None
    #: The non-secret settings. Credentials are never returned.
    config: dict[str, Any]
    enabled: bool
    #: When an operation last ran (epoch ms).
    last_used_at: int | None
    last_status: str | None
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class ServiceConnectorsUpdateBody(TypedDict, total=False):
    name: str
    enabled: bool
    config: dict[str, Any]
    credentials: dict[str, Any]


class ServiceConnectorsUpdateResponse(TypedDict):
    object: Literal["service_connector"]
    id: str
    #: Unique within the instance; what Actions and flows call it by.
    name: str
    #: The catalog entry, e.g. `twilio`, `segment`, `persona`, `http`.
    kind: str
    category: str | None
    #: The non-secret settings. Credentials are never returned.
    config: dict[str, Any]
    enabled: bool
    #: When an operation last ran (epoch ms).
    last_used_at: int | None
    last_status: str | None
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class ServiceConnectorsInvokeBody(TypedDict, total=False):
    operation: str
    input: dict[str, Any]


class ServiceConnectorsInvokeResponse(TypedDict):
    object: Literal["service_connector_result"]
    operation: str | None
    #: The operation's normalized result; see the catalog entry.
    result: dict[str, Any]


class DesktopMfaGetPolicyResponse(TypedDict):
    object: Literal["desktop_mfa_policy"]
    #: Workstation agents ask for a second factor at OS login.
    enabled: bool
    #: `selected` limits it to `user_ids` and members of `org_ids`.
    applies_to: Literal["all", "selected"]
    user_ids: list[str]
    org_ids: list[str]
    #: Factors an agent may start: push (with number matching), totp, passkey.
    allowed_factors: list[Literal["push", "totp", "passkey"]]
    #: Agents may cache a sealed offline verifier and unlock without reaching Atlas.
    offline_enabled: bool
    #: How long a cached verifier stays usable without a refresh.
    offline_grace_hours: int
    #: Offline unlock needs the user's PIN as well as the one-time code.
    offline_pin_required: bool


class DesktopMfaUpdatePolicyBody(TypedDict, total=False):
    enabled: bool
    applies_to: str
    user_ids: list[str]
    org_ids: list[str]
    allowed_factors: list[str]
    offline_enabled: bool
    offline_grace_hours: float
    offline_pin_required: bool


class DesktopMfaUpdatePolicyResponse(TypedDict):
    object: Literal["desktop_mfa_policy"]
    #: Workstation agents ask for a second factor at OS login.
    enabled: bool
    #: `selected` limits it to `user_ids` and members of `org_ids`.
    applies_to: Literal["all", "selected"]
    user_ids: list[str]
    org_ids: list[str]
    #: Factors an agent may start: push (with number matching), totp, passkey.
    allowed_factors: list[Literal["push", "totp", "passkey"]]
    #: Agents may cache a sealed offline verifier and unlock without reaching Atlas.
    offline_enabled: bool
    #: How long a cached verifier stays usable without a refresh.
    offline_grace_hours: int
    #: Offline unlock needs the user's PIN as well as the one-time code.
    offline_pin_required: bool


class DesktopMfaCreateEnrolmentCodeBody(TypedDict, total=False):
    user_id: str
    expires_in_minutes: float


class DesktopMfaCreateEnrolmentCodeResponse(TypedDict):
    object: Literal["desktop_enrolment_code"]
    #: Shown once. Single use.
    code: str
    #: Expires (epoch ms).
    expires_at: int
    user_id: str


class _DesktopMfaGetDeviceResponseRequired(TypedDict):
    object: Literal["desktop_device"]
    id: str
    user_id: str
    #: The device key the workstation signs with.
    device_key_id: str
    hostname: str | None
    platform: Literal["windows", "macos", "linux"]
    agent_version: str | None
    status: Literal["active", "revoked"]
    offline_pin_set: bool
    #: Raised to void every offline verifier issued so far.
    bundle_generation: int
    #: Last authenticated call (epoch ms).
    last_seen_at: int | None
    revoked_at: int | None
    #: Enrolled (epoch ms).
    created_at: int


class DesktopMfaGetDeviceResponse(_DesktopMfaGetDeviceResponseRequired, total=False):
    #: The most recent offline verifiers issued to the workstation.
    offline_bundles: list[dict[str, Any]]


class DesktopMfaRevokeDeviceResponse(TypedDict):
    object: Literal["desktop_device"]
    id: str
    user_id: str
    #: The device key the workstation signs with.
    device_key_id: str
    hostname: str | None
    platform: Literal["windows", "macos", "linux"]
    agent_version: str | None
    status: Literal["active", "revoked"]
    offline_pin_set: bool
    #: Raised to void every offline verifier issued so far.
    bundle_generation: int
    #: Last authenticated call (epoch ms).
    last_seen_at: int | None
    revoked_at: int | None
    #: Enrolled (epoch ms).
    created_at: int


class DesktopMfaRevokeOfflineCacheResponse(TypedDict):
    object: Literal["desktop_device"]
    id: str
    user_id: str
    #: The device key the workstation signs with.
    device_key_id: str
    hostname: str | None
    platform: Literal["windows", "macos", "linux"]
    agent_version: str | None
    status: Literal["active", "revoked"]
    offline_pin_set: bool
    #: Raised to void every offline verifier issued so far.
    bundle_generation: int
    #: Last authenticated call (epoch ms).
    last_seen_at: int | None
    revoked_at: int | None
    #: Enrolled (epoch ms).
    created_at: int


class IdentityVerificationSettingsResponse(TypedDict):
    object: Literal["identity_verification_settings"]
    enabled: bool
    #: The service connector (Persona, Onfido, Veriff or Stripe Identity) that does the checking.
    connector_id: str | None
    #: Offer a verified identity as the custom second step of sign-in.
    as_challenge: bool
    #: The URL to give the verification service for verdict webhooks (set the service's webhook
    #: secret on the connector as `webhook_secret`; Veriff uses its shared secret).
    webhook_url: str | None


class IdentityVerificationUpdateSettingsBody(TypedDict, total=False):
    enabled: bool
    connector_id: str | None
    as_challenge: bool


class IdentityVerificationUpdateSettingsResponse(TypedDict):
    object: Literal["identity_verification_settings"]
    enabled: bool
    #: The service connector (Persona, Onfido, Veriff or Stripe Identity) that does the checking.
    connector_id: str | None
    #: Offer a verified identity as the custom second step of sign-in.
    as_challenge: bool
    #: The URL to give the verification service for verdict webhooks (set the service's webhook
    #: secret on the connector as `webhook_secret`; Veriff uses its shared secret).
    webhook_url: str | None


class IdentityVerificationGetResponse(TypedDict):
    object: Literal["identity_verification"]
    id: str
    user_id: str
    provider: Literal["persona", "onfido", "veriff", "stripe_identity"]
    status: Literal["pending", "approved", "declined", "needs_review"]
    #: The service's short reason for a decline or review.
    reason: str | None
    #: The service's hosted verification page, while the check is pending.
    url: str | None
    #: Who decided a review by hand.
    decided_by: str | None
    #: Started (epoch ms).
    created_at: int
    #: When the check was approved or declined (epoch ms).
    completed_at: int | None


class IdentityVerificationDecideBody(TypedDict, total=False):
    decision: Literal["approved", "declined"]
    reason: str


class IdentityVerificationDecideResponse(TypedDict):
    object: Literal["identity_verification"]
    id: str
    user_id: str
    provider: Literal["persona", "onfido", "veriff", "stripe_identity"]
    status: Literal["pending", "approved", "declined", "needs_review"]
    #: The service's short reason for a decline or review.
    reason: str | None
    #: The service's hosted verification page, while the check is pending.
    url: str | None
    #: Who decided a review by hand.
    decided_by: str | None
    #: Started (epoch ms).
    created_at: int
    #: When the check was approved or declined (epoch ms).
    completed_at: int | None


class IdentityVerificationStartBody(TypedDict, total=False):
    redirect_url: str


class IdentityVerificationStartResponse(TypedDict):
    object: Literal["identity_verification"]
    id: str
    user_id: str
    provider: Literal["persona", "onfido", "veriff", "stripe_identity"]
    status: Literal["pending", "approved", "declined", "needs_review"]
    #: The service's short reason for a decline or review.
    reason: str | None
    #: The service's hosted verification page, while the check is pending.
    url: str | None
    #: Who decided a review by hand.
    decided_by: str | None
    #: Started (epoch ms).
    created_at: int
    #: When the check was approved or declined (epoch ms).
    completed_at: int | None


class _IgaEntitlementsCreateBodyRequired(TypedDict):
    key: str
    name: str
    kind: Literal["role", "org_membership", "group", "resource_role", "app_assignment", "custom"]
    target: dict[str, Any]


class IgaEntitlementsCreateBody(_IgaEntitlementsCreateBodyRequired, total=False):
    description: str | None
    owner_user_id: str | None
    risk_level: Literal["low", "medium", "high", "critical"]
    approval_rules: dict[str, Any]
    max_duration_seconds: int | None
    requestable: bool
    require_justification: bool


class IgaEntitlementsCreateResponse(TypedDict):
    object: Literal["iga_entitlement"]
    id: str
    key: str
    name: str
    description: str | None
    kind: Literal["role", "org_membership", "group", "resource_role", "app_assignment", "custom"]
    #: What the entitlement points at, by kind: role {role_key}, org_membership {organization_id,
    #: role}, group {group}, resource_role {resource_id, role}, app_assignment {app_id}, custom
    #: (free-form).
    target: dict[str, Any]
    owner_user_id: str | None
    risk_level: Literal["low", "medium", "high", "critical"]
    approval_rules: dict[str, Any]
    max_duration_seconds: int | None
    requestable: bool
    require_justification: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class IgaEntitlementsGetResponse(TypedDict):
    object: Literal["iga_entitlement"]
    id: str
    key: str
    name: str
    description: str | None
    kind: Literal["role", "org_membership", "group", "resource_role", "app_assignment", "custom"]
    #: What the entitlement points at, by kind: role {role_key}, org_membership {organization_id,
    #: role}, group {group}, resource_role {resource_id, role}, app_assignment {app_id}, custom
    #: (free-form).
    target: dict[str, Any]
    owner_user_id: str | None
    risk_level: Literal["low", "medium", "high", "critical"]
    approval_rules: dict[str, Any]
    max_duration_seconds: int | None
    requestable: bool
    require_justification: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class IgaEntitlementsUpdateBody(TypedDict, total=False):
    key: str
    name: str
    description: str | None
    kind: Literal["role", "org_membership", "group", "resource_role", "app_assignment", "custom"]
    target: dict[str, Any]
    owner_user_id: str | None
    risk_level: Literal["low", "medium", "high", "critical"]
    approval_rules: dict[str, Any]
    max_duration_seconds: int | None
    requestable: bool
    require_justification: bool


class IgaEntitlementsUpdateResponse(TypedDict):
    object: Literal["iga_entitlement"]
    id: str
    key: str
    name: str
    description: str | None
    kind: Literal["role", "org_membership", "group", "resource_role", "app_assignment", "custom"]
    #: What the entitlement points at, by kind: role {role_key}, org_membership {organization_id,
    #: role}, group {group}, resource_role {resource_id, role}, app_assignment {app_id}, custom
    #: (free-form).
    target: dict[str, Any]
    owner_user_id: str | None
    risk_level: Literal["low", "medium", "high", "critical"]
    approval_rules: dict[str, Any]
    max_duration_seconds: int | None
    requestable: bool
    require_justification: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class _IgaRequestsCreateBodyRequired(TypedDict):
    entitlement: str
    user_id: str


class IgaRequestsCreateBody(_IgaRequestsCreateBodyRequired, total=False):
    requester_user_id: str
    justification: str
    duration_seconds: int


class IgaRequestsCreateResponse(TypedDict):
    object: Literal["iga_request"]
    id: str
    entitlement_id: str
    requester_user_id: str | None
    beneficiary_user_id: str
    source: Literal["self", "admin"]
    justification: str | None
    duration_seconds: int | None
    status: Literal["pending", "approved", "denied", "cancelled", "fulfilled", "failed"]
    current_step: int | None
    steps: list[dict[str, Any]]
    sod: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    failure: str | None
    decided_at: int | None
    #: Filed (epoch ms).
    created_at: int


class IgaRequestsGetResponse(TypedDict):
    object: Literal["iga_request"]
    id: str
    entitlement_id: str
    requester_user_id: str | None
    beneficiary_user_id: str
    source: Literal["self", "admin"]
    justification: str | None
    duration_seconds: int | None
    status: Literal["pending", "approved", "denied", "cancelled", "fulfilled", "failed"]
    current_step: int | None
    steps: list[dict[str, Any]]
    sod: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    failure: str | None
    decided_at: int | None
    #: Filed (epoch ms).
    created_at: int


class _IgaRequestsDecideBodyRequired(TypedDict):
    decision: Literal["approve", "deny"]


class IgaRequestsDecideBody(_IgaRequestsDecideBodyRequired, total=False):
    comment: str
    approver_user_id: str


class IgaRequestsDecideResponse(TypedDict):
    object: Literal["iga_request"]
    id: str
    entitlement_id: str
    requester_user_id: str | None
    beneficiary_user_id: str
    source: Literal["self", "admin"]
    justification: str | None
    duration_seconds: int | None
    status: Literal["pending", "approved", "denied", "cancelled", "fulfilled", "failed"]
    current_step: int | None
    steps: list[dict[str, Any]]
    sod: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    failure: str | None
    decided_at: int | None
    #: Filed (epoch ms).
    created_at: int


class IgaRequestsCancelResponse(TypedDict):
    object: Literal["iga_request"]
    id: str
    entitlement_id: str
    requester_user_id: str | None
    beneficiary_user_id: str
    source: Literal["self", "admin"]
    justification: str | None
    duration_seconds: int | None
    status: Literal["pending", "approved", "denied", "cancelled", "fulfilled", "failed"]
    current_step: int | None
    steps: list[dict[str, Any]]
    sod: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    failure: str | None
    decided_at: int | None
    #: Filed (epoch ms).
    created_at: int


class _IgaGrantsCreateBodyRequired(TypedDict):
    entitlement: str
    user_id: str


class IgaGrantsCreateBody(_IgaGrantsCreateBodyRequired, total=False):
    expires_at: int
    override_reason: str


class IgaGrantsCreateResponse(TypedDict):
    object: Literal["iga_grant"]
    id: str
    user_id: str
    entitlement_id: str
    request_id: str | None
    source: Literal["request", "admin", "birthright", "existing"]
    status: Literal["active", "revoked", "expired"]
    #: Granted (epoch ms).
    granted_at: int
    expires_at: int | None
    revoked_at: int | None
    revoked_reason: str | None
    revoked_by: str | None
    #: The access existed before governance took it over. An expiry or a birthright change leaves
    #: adopted access in place; an administrator or reviewer revoke removes it.
    adopted: bool


class IgaGrantsRevokeBody(TypedDict, total=False):
    reason: str


class IgaGrantsRevokeResponse(TypedDict):
    object: Literal["iga_grant"]
    id: str
    user_id: str
    entitlement_id: str
    request_id: str | None
    source: Literal["request", "admin", "birthright", "existing"]
    status: Literal["active", "revoked", "expired"]
    #: Granted (epoch ms).
    granted_at: int
    expires_at: int | None
    revoked_at: int | None
    revoked_reason: str | None
    revoked_by: str | None
    #: The access existed before governance took it over. An expiry or a birthright change leaves
    #: adopted access in place; an administrator or reviewer revoke removes it.
    adopted: bool


class _IgaDelegationsCreateBodyRequired(TypedDict):
    delegator_user_id: str
    delegate_user_id: str
    ends_at: int


class IgaDelegationsCreateBody(_IgaDelegationsCreateBodyRequired, total=False):
    starts_at: int


class IgaDelegationsCreateResponse(TypedDict):
    object: Literal["iga_delegation"]
    id: str
    delegator_user_id: str
    delegate_user_id: str
    #: Starts (epoch ms).
    starts_at: int
    #: Ends (epoch ms).
    ends_at: int
    #: Created (epoch ms).
    created_at: int


class _IgaSodCreateRuleBodyRequired(TypedDict):
    name: str
    entitlement_a: str
    entitlement_b: str


class IgaSodCreateRuleBody(_IgaSodCreateRuleBodyRequired, total=False):
    description: str
    mode: Literal["block", "require_approval"]
    approver: dict[str, Any]
    enabled: bool


class IgaSodCreateRuleResponse(TypedDict):
    object: Literal["iga_sod_rule"]
    id: str
    name: str
    description: str | None
    entitlement_a: str
    entitlement_b: str
    mode: Literal["block", "require_approval"]
    approver: dict[str, Any] | None
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class IgaSodUpdateRuleBody(TypedDict, total=False):
    name: str
    description: str
    mode: Literal["block", "require_approval"]
    approver: dict[str, Any]
    enabled: bool


class IgaSodUpdateRuleResponse(TypedDict):
    object: Literal["iga_sod_rule"]
    id: str
    name: str
    description: str | None
    entitlement_a: str
    entitlement_b: str
    mode: Literal["block", "require_approval"]
    approver: dict[str, Any] | None
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Updated (epoch ms).
    updated_at: int


class IgaSodScanResponse(TypedDict):
    object: Literal["iga_sod_scan"]
    found: int
    resolved: int


class _IgaLifecycleCreateBirthrightRuleBodyRequired(TypedDict):
    name: str
    match: dict[str, Any]
    entitlement_ids: list[str]


class IgaLifecycleCreateBirthrightRuleBody(
    _IgaLifecycleCreateBirthrightRuleBodyRequired, total=False
):
    revoke_on_unmatch: bool
    enabled: bool


class IgaLifecycleCreateBirthrightRuleResponse(TypedDict):
    object: Literal["iga_birthright_rule"]
    id: str
    name: str
    match: dict[str, Any]
    entitlement_ids: list[str]
    revoke_on_unmatch: bool
    enabled: bool
    #: Created (epoch ms).
    created_at: int


class IgaLifecycleUpdateBirthrightRuleBody(TypedDict, total=False):
    name: str
    match: dict[str, Any]
    entitlement_ids: list[str]
    revoke_on_unmatch: bool
    enabled: bool


class IgaLifecycleUpdateBirthrightRuleResponse(TypedDict):
    object: Literal["iga_birthright_rule"]
    id: str
    name: str
    match: dict[str, Any]
    entitlement_ids: list[str]
    revoke_on_unmatch: bool
    enabled: bool
    #: Created (epoch ms).
    created_at: int


class IgaLifecycleReconcileResponse(TypedDict):
    object: Literal["iga_jml"]
    user_id: str
    granted: list[str]
    revoked: list[str]


class IgaLifecycleOffboardBody(TypedDict, total=False):
    close_account: bool
    grace_seconds: int
    reason: str


class IgaLifecycleOffboardResponse(TypedDict):
    object: Literal["iga_offboarding"]
    user_id: str
    revoked_grants: int
    cancelled_requests: int
    account_closure: dict[str, Any] | None


class IgaLifecycleSettingsResponse(TypedDict):
    object: Literal["iga_settings"]
    jml_enabled: bool
    leaver_action: Literal["revoke", "revoke_and_close"]
    leaver_close_grace_seconds: int | None


class IgaLifecycleUpdateSettingsBody(TypedDict, total=False):
    jml_enabled: bool
    leaver_action: Literal["revoke", "revoke_and_close"]
    leaver_close_grace_seconds: int | None


class IgaLifecycleUpdateSettingsResponse(TypedDict):
    object: Literal["iga_settings"]
    jml_enabled: bool
    leaver_action: Literal["revoke", "revoke_and_close"]
    leaver_close_grace_seconds: int | None


class _IgaCampaignsCreateBodyRequired(TypedDict):
    name: str


class IgaCampaignsCreateBody(_IgaCampaignsCreateBodyRequired, total=False):
    description: str
    scope_type: Literal["all", "entitlement", "app", "role", "group", "org"]
    scope_ids: list[str]
    reviewer_type: Literal["manager", "owner", "named"]
    reviewer_ids: list[str]
    due_at: int
    reminder_days: list[int]
    auto_revoke: bool


class IgaCampaignsCreateResponse(TypedDict):
    object: Literal["iga_campaign"]
    id: str
    name: str
    description: str | None
    scope_type: Literal["all", "entitlement", "app", "role", "group", "org"]
    scope_ids: list[str]
    reviewer_type: Literal["manager", "owner", "named"]
    reviewer_ids: list[str]
    status: Literal["draft", "active", "closed"]
    due_at: int | None
    reminder_days: list[int]
    auto_revoke: bool
    launched_at: int | None
    closed_at: int | None
    #: Created (epoch ms).
    created_at: int


class IgaCampaignsGetResponse(TypedDict):
    object: Literal["iga_campaign"]
    id: str
    name: str
    description: str | None
    scope_type: Literal["all", "entitlement", "app", "role", "group", "org"]
    scope_ids: list[str]
    reviewer_type: Literal["manager", "owner", "named"]
    reviewer_ids: list[str]
    status: Literal["draft", "active", "closed"]
    due_at: int | None
    reminder_days: list[int]
    auto_revoke: bool
    launched_at: int | None
    closed_at: int | None
    #: Created (epoch ms).
    created_at: int


class IgaCampaignsLaunchResponse(TypedDict):
    object: Literal["iga_campaign"]
    id: str
    name: str
    description: str | None
    scope_type: Literal["all", "entitlement", "app", "role", "group", "org"]
    scope_ids: list[str]
    reviewer_type: Literal["manager", "owner", "named"]
    reviewer_ids: list[str]
    status: Literal["draft", "active", "closed"]
    due_at: int | None
    reminder_days: list[int]
    auto_revoke: bool
    launched_at: int | None
    closed_at: int | None
    #: Created (epoch ms).
    created_at: int


class IgaCampaignsCloseResponse(TypedDict):
    object: Literal["iga_campaign"]
    id: str
    name: str
    description: str | None
    scope_type: Literal["all", "entitlement", "app", "role", "group", "org"]
    scope_ids: list[str]
    reviewer_type: Literal["manager", "owner", "named"]
    reviewer_ids: list[str]
    status: Literal["draft", "active", "closed"]
    due_at: int | None
    reminder_days: list[int]
    auto_revoke: bool
    launched_at: int | None
    closed_at: int | None
    #: Created (epoch ms).
    created_at: int


class IgaCampaignsProgressResponse(TypedDict):
    object: Literal["iga_campaign_progress"]
    campaign_id: str
    status: Literal["draft", "active", "closed"]
    total: int
    pending: int
    certified: int
    revoked: int
    percent_complete: int
    overdue: bool
    reviewers: list[dict[str, Any]]


class IgaCampaignsEvidenceResponse(TypedDict):
    object: Literal["iga_campaign_evidence"]
    campaign: dict[str, Any]
    progress: dict[str, Any]
    generated_at: str
    items: list[dict[str, Any]]


class _IgaCampaignsDecideBodyRequired(TypedDict):
    decision: Literal["certify", "revoke"]


class IgaCampaignsDecideBody(_IgaCampaignsDecideBodyRequired, total=False):
    comment: str
    reviewer_user_id: str


class IgaCampaignsDecideResponse(TypedDict):
    object: Literal["iga_campaign_item"]
    id: str
    campaign_id: str
    grant_id: str
    user_id: str
    entitlement_id: str
    reviewer_user_id: str | None
    decision: Literal["pending", "certified", "revoked"]
    decided_by: str | None
    decided_at: int | None
    comment: str | None
    revoked_applied: bool


class VaultCreateBody(TypedDict, total=False):
    name: str
    value: str
    key_context: dict[str, Any]
    metadata: dict[str, Any]


class VaultCreateResponse(TypedDict):
    object: Literal["vault_object"]
    id: str
    #: Unique within the instance.
    name: str
    #: The mandatory labels bound into the encryption.
    key_context: dict[str, Any]
    #: Non-secret labels returned by list and metadata reads.
    metadata: dict[str, Any]
    #: The current version number.
    version: int
    #: `atlas` (the instance key) or the customer KMS that wraps the current version's data key
    #: (`aws_kms`, `gcp_kms`, `azure_key_vault`).
    key_provider: str
    #: When the object was created (epoch ms).
    created_at: int
    #: When the current version was written (epoch ms).
    updated_at: int


class VaultMetadataResponse(TypedDict):
    object: Literal["vault_object"]
    id: str
    #: Unique within the instance.
    name: str
    #: The mandatory labels bound into the encryption.
    key_context: dict[str, Any]
    #: Non-secret labels returned by list and metadata reads.
    metadata: dict[str, Any]
    #: The current version number.
    version: int
    #: `atlas` (the instance key) or the customer KMS that wraps the current version's data key
    #: (`aws_kms`, `gcp_kms`, `azure_key_vault`).
    key_provider: str
    #: When the object was created (epoch ms).
    created_at: int
    #: When the current version was written (epoch ms).
    updated_at: int


class VaultReadResponse(TypedDict):
    object: Literal["vault_object"]
    id: str
    #: Unique within the instance.
    name: str
    #: The mandatory labels bound into the encryption.
    key_context: dict[str, Any]
    #: Non-secret labels returned by list and metadata reads.
    metadata: dict[str, Any]
    #: The current version number.
    version: int
    #: `atlas` (the instance key) or the customer KMS that wraps the current version's data key
    #: (`aws_kms`, `gcp_kms`, `azure_key_vault`).
    key_provider: str
    #: When the object was created (epoch ms).
    created_at: int
    #: When the current version was written (epoch ms).
    updated_at: int
    #: The decrypted value.
    value: str


class VaultUpdateBody(TypedDict, total=False):
    value: str
    version_check: float


class VaultUpdateResponse(TypedDict):
    object: Literal["vault_object"]
    id: str
    #: Unique within the instance.
    name: str
    #: The mandatory labels bound into the encryption.
    key_context: dict[str, Any]
    #: Non-secret labels returned by list and metadata reads.
    metadata: dict[str, Any]
    #: The current version number.
    version: int
    #: `atlas` (the instance key) or the customer KMS that wraps the current version's data key
    #: (`aws_kms`, `gcp_kms`, `azure_key_vault`).
    key_provider: str
    #: When the object was created (epoch ms).
    created_at: int
    #: When the current version was written (epoch ms).
    updated_at: int


class VaultKeyProviderGetResponse(TypedDict):
    object: Literal["vault_key_provider"]
    id: str
    provider: Literal["aws_kms", "gcp_kms", "azure_key_vault"]
    #: The non-secret settings. Credentials are never returned.
    config: dict[str, Any]
    #: When the settings last changed (epoch ms).
    updated_at: int


class VaultKeyProviderSetBody(TypedDict, total=False):
    provider: str
    config: dict[str, Any]
    credentials: dict[str, Any]


class VaultKeyProviderSetResponse(TypedDict):
    object: Literal["vault_key_provider"]
    id: str
    provider: Literal["aws_kms", "gcp_kms", "azure_key_vault"]
    #: The non-secret settings. Credentials are never returned.
    config: dict[str, Any]
    #: When the settings last changed (epoch ms).
    updated_at: int


class VaultKeyProviderRemoveResponse(TypedDict):
    object: Literal["vault_key_provider.deleted"]
    deleted: bool


class _ConnectionsCreateBodyRequired(TypedDict):
    owner: dict[str, Any]
    kind: Literal[
        "oauth",
        "api_key",
        "client_credentials",
        "bearer",
        "basic",
        "custom_header",
        "hmac_secret",
        "jwt_bearer",
        "oauth1",
        "github_app_installation",
        "admin_consent",
    ]
    #: A built-in or custom OAuth provider key for oauth; any short key otherwise.
    provider: str
    #: Hostnames, or *.example.com wildcards (1 to 20).
    allowed_hosts: list[str]


class ConnectionsCreateBody(_ConnectionsCreateBodyRequired, total=False):
    name: str
    #: api_key: placement (header or query), name, scheme. custom_header: name. hmac_secret:
    #: algorithm, encoding, signature_header, prefix, timestamp_header. client_credentials:
    #: token_url, client_id, scopes, auth_style, grant_type, account_id, audience, resource,
    #: extra_params, request_format, token_header.
    config: dict[str, Any]
    #: Relay verbs allowed for this connection (default GET, HEAD, POST).
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: Only data is accepted. A sign-in link is an external account.
    purpose: Literal["data"]


class _ConnectionsCreateResponseRequired(TypedDict):
    object: Literal["connection"]
    id: str
    owner: dict[str, Any]
    #: oauth, github_app_installation, admin_consent and a three-legged oauth1 are authorized by a
    #: browser step; client_credentials and jwt_bearer mint tokens from a credential Atlas holds;
    #: api_key, bearer, basic, custom_header and hmac_secret are typed secrets the owner enters.
    kind: Literal[
        "oauth",
        "api_key",
        "client_credentials",
        "bearer",
        "basic",
        "custom_header",
        "hmac_secret",
        "jwt_bearer",
        "oauth1",
        "github_app_installation",
        "admin_consent",
    ]
    provider: str
    #: Your label for this account, for example "Support inbox".
    name: str
    #: The only hosts the relay may call with this connection.
    allowed_hosts: list[str]
    #: Non-secret settings of the kind (api_key placement and name, token_url, client_id, scopes,
    #: issuer, audience, public_jwk, signature_method, realm, installation_id, tenant...). Never a
    #: secret.
    config: dict[str, Any]
    #: needs_reauth: the token expired or was refused and cannot be refreshed. revoked:
    #: disconnected on purpose.
    status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
    #: A connection is never a sign-in method: connecting one adds no way to sign in, counts toward
    #: no only-method rule and needs no step-up.
    purpose: Literal["data"]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: True when environment is sandbox.
    sandbox: bool
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: The scopes the provider granted.
    scopes: list[str]
    #: Non-secret provider handles captured with the token (instance_url, realmId, hub_id,
    #: tenant_id, team_id...).
    metadata: dict[str, Any]
    #: Whether a credential is stored. The credential itself is never returned by this object.
    has_secret: bool
    #: The relay verbs this connection may use. GET, HEAD and POST unless set.
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]
    #: When the connection was created (epoch ms).
    created_at: int
    #: When the connection last changed (epoch ms).
    updated_at: int


class ConnectionsCreateResponse(_ConnectionsCreateResponseRequired, total=False):
    #: The provider-side account this connection covers (a QuickBooks realm, a Slack workspace, a
    #: HubSpot hub, the authorizing user's id at the provider). Several connections of one provider
    #: coexist by it; null until connected.
    external_id: str | None
    #: The owner OAuth client that issued the stored token, or null when the instance client did.
    oauth_client_id: str | None
    #: When the access token expires, epoch milliseconds. Refreshed automatically on read.
    expires_at: int | None
    #: Who connected it. Informational only: the connection does not depend on that user, who may
    #: be deleted.
    authorized_by_user_id: str | None
    #: Epoch milliseconds.
    connected_at: int | None
    #: Epoch milliseconds.
    last_refreshed_at: int | None
    #: Epoch milliseconds.
    status_changed_at: int | None
    #: Why the connection left connected, or why the last refresh failed.
    last_error: None | dict[str, Any]
    #: Consecutive failed refreshes; 0 when healthy. A provider outage is retried with backoff and
    #: announced (connection.refresh_failed) after 3.
    refresh_failures: int
    #: When the keep-alive worker next refreshes this connection (epoch milliseconds), null when
    #: there is nothing to keep alive.
    next_refresh_at: int | None
    #: Deprecated, always null: a connection owns its tokens and no longer rides a user's linked
    #: account.
    external_account_id: None
    #: When the entered credential expires (epoch ms). connection.secret_expiring reminders go out
    #: 30, 7 and 1 days before.
    secret_expires_at: int | None
    #: While a rotation's overlap window is open: when the replaced version stops being accepted
    #: (epoch ms).
    previous_valid_until: int | None


class _ConnectionsGetResponseRequired(TypedDict):
    object: Literal["connection"]
    id: str
    owner: dict[str, Any]
    #: oauth, github_app_installation, admin_consent and a three-legged oauth1 are authorized by a
    #: browser step; client_credentials and jwt_bearer mint tokens from a credential Atlas holds;
    #: api_key, bearer, basic, custom_header and hmac_secret are typed secrets the owner enters.
    kind: Literal[
        "oauth",
        "api_key",
        "client_credentials",
        "bearer",
        "basic",
        "custom_header",
        "hmac_secret",
        "jwt_bearer",
        "oauth1",
        "github_app_installation",
        "admin_consent",
    ]
    provider: str
    #: Your label for this account, for example "Support inbox".
    name: str
    #: The only hosts the relay may call with this connection.
    allowed_hosts: list[str]
    #: Non-secret settings of the kind (api_key placement and name, token_url, client_id, scopes,
    #: issuer, audience, public_jwk, signature_method, realm, installation_id, tenant...). Never a
    #: secret.
    config: dict[str, Any]
    #: needs_reauth: the token expired or was refused and cannot be refreshed. revoked:
    #: disconnected on purpose.
    status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
    #: A connection is never a sign-in method: connecting one adds no way to sign in, counts toward
    #: no only-method rule and needs no step-up.
    purpose: Literal["data"]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: True when environment is sandbox.
    sandbox: bool
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: The scopes the provider granted.
    scopes: list[str]
    #: Non-secret provider handles captured with the token (instance_url, realmId, hub_id,
    #: tenant_id, team_id...).
    metadata: dict[str, Any]
    #: Whether a credential is stored. The credential itself is never returned by this object.
    has_secret: bool
    #: The relay verbs this connection may use. GET, HEAD and POST unless set.
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]
    #: When the connection was created (epoch ms).
    created_at: int
    #: When the connection last changed (epoch ms).
    updated_at: int


class ConnectionsGetResponse(_ConnectionsGetResponseRequired, total=False):
    #: The provider-side account this connection covers (a QuickBooks realm, a Slack workspace, a
    #: HubSpot hub, the authorizing user's id at the provider). Several connections of one provider
    #: coexist by it; null until connected.
    external_id: str | None
    #: The owner OAuth client that issued the stored token, or null when the instance client did.
    oauth_client_id: str | None
    #: When the access token expires, epoch milliseconds. Refreshed automatically on read.
    expires_at: int | None
    #: Who connected it. Informational only: the connection does not depend on that user, who may
    #: be deleted.
    authorized_by_user_id: str | None
    #: Epoch milliseconds.
    connected_at: int | None
    #: Epoch milliseconds.
    last_refreshed_at: int | None
    #: Epoch milliseconds.
    status_changed_at: int | None
    #: Why the connection left connected, or why the last refresh failed.
    last_error: None | dict[str, Any]
    #: Consecutive failed refreshes; 0 when healthy. A provider outage is retried with backoff and
    #: announced (connection.refresh_failed) after 3.
    refresh_failures: int
    #: When the keep-alive worker next refreshes this connection (epoch milliseconds), null when
    #: there is nothing to keep alive.
    next_refresh_at: int | None
    #: Deprecated, always null: a connection owns its tokens and no longer rides a user's linked
    #: account.
    external_account_id: None
    #: When the entered credential expires (epoch ms). connection.secret_expiring reminders go out
    #: 30, 7 and 1 days before.
    secret_expires_at: int | None
    #: While a rotation's overlap window is open: when the replaced version stops being accepted
    #: (epoch ms).
    previous_valid_until: int | None


class ConnectionsUpdateBody(TypedDict, total=False):
    name: str
    allowed_hosts: list[str]
    config: dict[str, Any]
    shared_by_user_id: str
    #: Transfer the connection to another organization or user of this instance. Its tokens move
    #: with it; nobody reconnects.
    owner: dict[str, Any]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]


class _ConnectionsUpdateResponseRequired(TypedDict):
    object: Literal["connection"]
    id: str
    owner: dict[str, Any]
    #: oauth, github_app_installation, admin_consent and a three-legged oauth1 are authorized by a
    #: browser step; client_credentials and jwt_bearer mint tokens from a credential Atlas holds;
    #: api_key, bearer, basic, custom_header and hmac_secret are typed secrets the owner enters.
    kind: Literal[
        "oauth",
        "api_key",
        "client_credentials",
        "bearer",
        "basic",
        "custom_header",
        "hmac_secret",
        "jwt_bearer",
        "oauth1",
        "github_app_installation",
        "admin_consent",
    ]
    provider: str
    #: Your label for this account, for example "Support inbox".
    name: str
    #: The only hosts the relay may call with this connection.
    allowed_hosts: list[str]
    #: Non-secret settings of the kind (api_key placement and name, token_url, client_id, scopes,
    #: issuer, audience, public_jwk, signature_method, realm, installation_id, tenant...). Never a
    #: secret.
    config: dict[str, Any]
    #: needs_reauth: the token expired or was refused and cannot be refreshed. revoked:
    #: disconnected on purpose.
    status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
    #: A connection is never a sign-in method: connecting one adds no way to sign in, counts toward
    #: no only-method rule and needs no step-up.
    purpose: Literal["data"]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: True when environment is sandbox.
    sandbox: bool
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: The scopes the provider granted.
    scopes: list[str]
    #: Non-secret provider handles captured with the token (instance_url, realmId, hub_id,
    #: tenant_id, team_id...).
    metadata: dict[str, Any]
    #: Whether a credential is stored. The credential itself is never returned by this object.
    has_secret: bool
    #: The relay verbs this connection may use. GET, HEAD and POST unless set.
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]
    #: When the connection was created (epoch ms).
    created_at: int
    #: When the connection last changed (epoch ms).
    updated_at: int


class ConnectionsUpdateResponse(_ConnectionsUpdateResponseRequired, total=False):
    #: The provider-side account this connection covers (a QuickBooks realm, a Slack workspace, a
    #: HubSpot hub, the authorizing user's id at the provider). Several connections of one provider
    #: coexist by it; null until connected.
    external_id: str | None
    #: The owner OAuth client that issued the stored token, or null when the instance client did.
    oauth_client_id: str | None
    #: When the access token expires, epoch milliseconds. Refreshed automatically on read.
    expires_at: int | None
    #: Who connected it. Informational only: the connection does not depend on that user, who may
    #: be deleted.
    authorized_by_user_id: str | None
    #: Epoch milliseconds.
    connected_at: int | None
    #: Epoch milliseconds.
    last_refreshed_at: int | None
    #: Epoch milliseconds.
    status_changed_at: int | None
    #: Why the connection left connected, or why the last refresh failed.
    last_error: None | dict[str, Any]
    #: Consecutive failed refreshes; 0 when healthy. A provider outage is retried with backoff and
    #: announced (connection.refresh_failed) after 3.
    refresh_failures: int
    #: When the keep-alive worker next refreshes this connection (epoch milliseconds), null when
    #: there is nothing to keep alive.
    next_refresh_at: int | None
    #: Deprecated, always null: a connection owns its tokens and no longer rides a user's linked
    #: account.
    external_account_id: None
    #: When the entered credential expires (epoch ms). connection.secret_expiring reminders go out
    #: 30, 7 and 1 days before.
    secret_expires_at: int | None
    #: While a rotation's overlap window is open: when the replaced version stops being accepted
    #: (epoch ms).
    previous_valid_until: int | None


class ConnectionsSetCredentialsBody(TypedDict, total=False):
    #: api_key.
    api_key: str
    #: bearer; or the token of a tba/three-legged oauth1 credential.
    token: str
    #: basic (no colon).
    username: str
    #: basic.
    password: str
    #: custom_header.
    value: str
    #: hmac_secret.
    secret: str
    #: client_credentials, or the app client id of a jwt_bearer with Basic client authentication.
    client_id: str
    #: client_credentials / jwt_bearer client authentication.
    client_secret: str
    #: https token endpoint (client_credentials, jwt_bearer); `{name}` placeholders are filled from
    #: host_params.
    token_url: str
    scopes: list[str]
    #: jwt_bearer / github_app_installation: a PEM private key (RSA or P-256). Held in the vault;
    #: never returned.
    private_key: str
    #: jwt_bearer: have Atlas generate the key pair; the public JWK is returned in
    #: config.public_jwk for you to register at the provider.
    generate_key: bool
    #: jwt_bearer: a Google service-account JSON key (a string or the parsed object).
    service_account_json: str | dict[str, Any]
    #: jwt_bearer with a provider-issued JWT credential (RingCentral).
    assertion: str
    #: oauth1.
    consumer_key: str
    #: oauth1.
    consumer_secret: str
    #: oauth1.
    token_secret: str
    #: Non-secret settings to merge (same keys as the connection config).
    config: dict[str, Any]
    #: When this credential expires: epoch milliseconds or an ISO date. Reminders are sent at 30, 7
    #: and 1 days before.
    expires_at: int | str


class _ConnectionsSetCredentialsResponseRequired(TypedDict):
    object: Literal["connection"]
    id: str
    owner: dict[str, Any]
    #: oauth, github_app_installation, admin_consent and a three-legged oauth1 are authorized by a
    #: browser step; client_credentials and jwt_bearer mint tokens from a credential Atlas holds;
    #: api_key, bearer, basic, custom_header and hmac_secret are typed secrets the owner enters.
    kind: Literal[
        "oauth",
        "api_key",
        "client_credentials",
        "bearer",
        "basic",
        "custom_header",
        "hmac_secret",
        "jwt_bearer",
        "oauth1",
        "github_app_installation",
        "admin_consent",
    ]
    provider: str
    #: Your label for this account, for example "Support inbox".
    name: str
    #: The only hosts the relay may call with this connection.
    allowed_hosts: list[str]
    #: Non-secret settings of the kind (api_key placement and name, token_url, client_id, scopes,
    #: issuer, audience, public_jwk, signature_method, realm, installation_id, tenant...). Never a
    #: secret.
    config: dict[str, Any]
    #: needs_reauth: the token expired or was refused and cannot be refreshed. revoked:
    #: disconnected on purpose.
    status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
    #: A connection is never a sign-in method: connecting one adds no way to sign in, counts toward
    #: no only-method rule and needs no step-up.
    purpose: Literal["data"]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: True when environment is sandbox.
    sandbox: bool
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: The scopes the provider granted.
    scopes: list[str]
    #: Non-secret provider handles captured with the token (instance_url, realmId, hub_id,
    #: tenant_id, team_id...).
    metadata: dict[str, Any]
    #: Whether a credential is stored. The credential itself is never returned by this object.
    has_secret: bool
    #: The relay verbs this connection may use. GET, HEAD and POST unless set.
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]
    #: When the connection was created (epoch ms).
    created_at: int
    #: When the connection last changed (epoch ms).
    updated_at: int


class ConnectionsSetCredentialsResponse(_ConnectionsSetCredentialsResponseRequired, total=False):
    #: The provider-side account this connection covers (a QuickBooks realm, a Slack workspace, a
    #: HubSpot hub, the authorizing user's id at the provider). Several connections of one provider
    #: coexist by it; null until connected.
    external_id: str | None
    #: The owner OAuth client that issued the stored token, or null when the instance client did.
    oauth_client_id: str | None
    #: When the access token expires, epoch milliseconds. Refreshed automatically on read.
    expires_at: int | None
    #: Who connected it. Informational only: the connection does not depend on that user, who may
    #: be deleted.
    authorized_by_user_id: str | None
    #: Epoch milliseconds.
    connected_at: int | None
    #: Epoch milliseconds.
    last_refreshed_at: int | None
    #: Epoch milliseconds.
    status_changed_at: int | None
    #: Why the connection left connected, or why the last refresh failed.
    last_error: None | dict[str, Any]
    #: Consecutive failed refreshes; 0 when healthy. A provider outage is retried with backoff and
    #: announced (connection.refresh_failed) after 3.
    refresh_failures: int
    #: When the keep-alive worker next refreshes this connection (epoch milliseconds), null when
    #: there is nothing to keep alive.
    next_refresh_at: int | None
    #: Deprecated, always null: a connection owns its tokens and no longer rides a user's linked
    #: account.
    external_account_id: None
    #: When the entered credential expires (epoch ms). connection.secret_expiring reminders go out
    #: 30, 7 and 1 days before.
    secret_expires_at: int | None
    #: While a rotation's overlap window is open: when the replaced version stops being accepted
    #: (epoch ms).
    previous_valid_until: int | None


class _ConnectionsConnectBodyRequired(TypedDict):
    #: Where the owner lands after the provider returns. Must be an allowed origin of the instance.
    redirect_url: str


class ConnectionsConnectBody(_ConnectionsConnectBodyRequired, total=False):
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: Scopes to ask for on top of the provider defaults, the owner client's scopes and
    #: config.scopes.
    additional_scopes: list[str]
    login_hint: str
    #: popup completes through postMessage like a popup sign-in.
    display: Literal["redirect", "popup"]
    #: When the provider returns a different account than the one this connection already holds,
    #: create a sibling connection for it instead of answering 409.
    create_if_new: bool
    #: Informational: the user who is connecting (stored as authorized_by_user_id).
    connect_user_id: str


class ConnectionsConnectResponse(TypedDict):
    object: Literal["connection_authorization"]
    connection_id: str
    #: Send the owner here. The provider returns to Atlas, the tokens are stored on the connection,
    #: and the owner lands on your redirect_url with `__atlas_status=connected` and
    #: `__atlas_connection=<id of the connection that was written>`.
    authorization_url: str
    attempt_id: str


class _ConnectionsOauth1SignBodyRequired(TypedDict):
    url: str


class ConnectionsOauth1SignBody(_ConnectionsOauth1SignBodyRequired, total=False):
    #: Default GET.
    method: str
    #: The request body, to sign when it is form-encoded.
    body: str
    content_type: str


class ConnectionsOauth1SignResponse(TypedDict):
    object: Literal["connection_signature"]
    connection_id: str
    #: The `Authorization: OAuth ...` header value to send. It is valid for this method, URL and
    #: body only.
    authorization: str
    method: str
    url: str


class _ConnectionsRelayBodyRequired(TypedDict):
    #: Absolute https URL on an allowed host.
    url: str


class ConnectionsRelayBody(_ConnectionsRelayBodyRequired, total=False):
    #: Must be in the connection's allowed_methods.
    method: Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]
    #: Extra request headers. Authorization, Cookie and Host cannot be set.
    headers: dict[str, Any]
    #: POST, PUT, PATCH or DELETE: a string, or an object sent as JSON (up to 256 KiB).
    body: Any
    #: Where the provider returns after authorizing, to receive meta.authorize_url on a 402.
    redirect_url: str
    #: The user the authorization link is for (organization-owned connections).
    connect_user_id: str


class ConnectionsRelayResponse(TypedDict):
    object: Literal["connection_relay_response"]
    connection_id: str
    #: The provider's HTTP status.
    status: int
    #: A small allow-list of response headers (content-type, etag, retry-after, link and a few
    #: more).
    headers: dict[str, Any]
    #: The provider's response body as text (up to 1 MiB).
    body: str
    truncated: bool


class _ConnectionsTokenResponseRequired(TypedDict):
    object: Literal["connection_token"]
    connection_id: str
    #: A live access token (refreshed first when it was expired or about to be).
    access_token: str
    #: Epoch milliseconds, null when the provider did not say.
    expires_at: int | None
    scopes: list[str]
    #: Non-secret provider handles (instance_url, realmId, hub_id, team_id, cloud_id,
    #: tenant_id...).
    metadata: dict[str, Any]
    #: The provider's token response without secret fields, plus fields looked up after the
    #: exchange (Xero `tenants`, Atlassian `accessible_resources`).
    token_response: dict[str, Any]
    #: Further credentials held by the same connection, by name. Slack: `user` is the installing
    #: user's token next to the bot token in `access_token`.
    credentials: dict[str, Any]
    external_id: str | None
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: True when this read refreshed (or minted) the token.
    refreshed: bool


class ConnectionsTokenResponse(_ConnectionsTokenResponseRequired, total=False):
    #: jwt_bearer: the user the token acts as (domain-wide delegation), when one was asked for.
    subject: str


class ConnectionsRefreshTokenBody(TypedDict, total=False):
    #: Why you are refreshing; recorded in the audit log.
    reason: Literal["provider_401", "expired", "manual"]
    #: SHA-256 (hex) of the access token the provider refused.
    stale_token_hash: str


class _ConnectionsRefreshTokenResponseRequired(TypedDict):
    object: Literal["connection_token"]
    connection_id: str
    #: A live access token (refreshed first when it was expired or about to be).
    access_token: str
    #: Epoch milliseconds, null when the provider did not say.
    expires_at: int | None
    scopes: list[str]
    #: Non-secret provider handles (instance_url, realmId, hub_id, team_id, cloud_id,
    #: tenant_id...).
    metadata: dict[str, Any]
    #: The provider's token response without secret fields, plus fields looked up after the
    #: exchange (Xero `tenants`, Atlassian `accessible_resources`).
    token_response: dict[str, Any]
    #: Further credentials held by the same connection, by name. Slack: `user` is the installing
    #: user's token next to the bot token in `access_token`.
    credentials: dict[str, Any]
    external_id: str | None
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: True when this read refreshed (or minted) the token.
    refreshed: bool


class ConnectionsRefreshTokenResponse(_ConnectionsRefreshTokenResponseRequired, total=False):
    #: jwt_bearer: the user the token acts as (domain-wide delegation), when one was asked for.
    subject: str


class _ConnectionsTokensBodyRequired(TypedDict):
    #: Connection ids (duplicates are read once).
    ids: list[str]


class ConnectionsTokensBody(_ConnectionsTokensBodyRequired, total=False):
    min_ttl_seconds: int


class _ConnectionsImportConnectionsBodyRequired(TypedDict):
    connections: list[dict[str, Any]]


class ConnectionsImportConnectionsBody(_ConnectionsImportConnectionsBodyRequired, total=False):
    #: Spend each refresh token against the provider and store what it issues.
    validate: bool
    dry_run: bool


class ConnectionsImportConnectionsResponse(TypedDict):
    object: Literal["connection_import"]
    total: int
    dry_run: bool
    #: Whether refresh tokens were checked against the provider.
    validated: bool
    created: int
    updated: int
    would_create: int
    would_update: int
    failed: int
    data: list[dict[str, Any]]


class ConnectionsExportConnectionsBody(TypedDict, total=False):
    owner_type: Literal["organization", "user"]
    owner_id: str
    provider: str
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
    limit: int
    starting_after: str
    include_secrets: bool
    #: Required with include_secrets: a PUBLIC JWK. A key with private parameters is refused.
    recipient_public_key: dict[str, Any]


class _ConnectionsExportConnectionsResponseRequired(TypedDict):
    object: Literal["connection_export"]
    #: True when the tokens are included, sealed in `bundle`.
    sealed: bool
    count: int
    has_more: bool
    next_cursor: str | None


class ConnectionsExportConnectionsResponse(
    _ConnectionsExportConnectionsResponseRequired, total=False
):
    #: Present when sealed is false.
    connections: list[dict[str, Any]]
    #: The thumbprint of the key the bundle is sealed to.
    recipient_key_id: str
    #: Present when sealed is true: a compact JWE (RSA-OAEP-256 or ECDH-ES+A256KW with A256GCM) of
    #: {version, exported_at, connections}.
    bundle: str


class ConnectionsSecretResponse(TypedDict):
    object: Literal["connection_secret"]
    connection_id: str
    kind: Literal["api_key", "bearer", "basic", "custom_header", "hmac_secret"]
    #: The vault version that was read.
    version: int
    #: The credential's fields. api_key: {api_key}. bearer: {token}. basic: {username, password}.
    #: custom_header: {value}. hmac_secret: {secret}.
    secret: dict[str, Any]
    #: The non-secret settings (placement, header name, algorithm...) needed to apply it.
    config: dict[str, Any]
    #: When the credential expires, epoch ms.
    expires_at: int | None


class ConnectionsRotateCredentialsBody(TypedDict, total=False):
    overlap_seconds: int
    #: Epoch milliseconds or an ISO date.
    expires_at: int | str


class _ConnectionsRotateCredentialsResponseRequired(TypedDict):
    object: Literal["connection"]
    id: str
    owner: dict[str, Any]
    #: oauth, github_app_installation, admin_consent and a three-legged oauth1 are authorized by a
    #: browser step; client_credentials and jwt_bearer mint tokens from a credential Atlas holds;
    #: api_key, bearer, basic, custom_header and hmac_secret are typed secrets the owner enters.
    kind: Literal[
        "oauth",
        "api_key",
        "client_credentials",
        "bearer",
        "basic",
        "custom_header",
        "hmac_secret",
        "jwt_bearer",
        "oauth1",
        "github_app_installation",
        "admin_consent",
    ]
    provider: str
    #: Your label for this account, for example "Support inbox".
    name: str
    #: The only hosts the relay may call with this connection.
    allowed_hosts: list[str]
    #: Non-secret settings of the kind (api_key placement and name, token_url, client_id, scopes,
    #: issuer, audience, public_jwk, signature_method, realm, installation_id, tenant...). Never a
    #: secret.
    config: dict[str, Any]
    #: needs_reauth: the token expired or was refused and cannot be refreshed. revoked:
    #: disconnected on purpose.
    status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
    #: A connection is never a sign-in method: connecting one adds no way to sign in, counts toward
    #: no only-method rule and needs no step-up.
    purpose: Literal["data"]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: True when environment is sandbox.
    sandbox: bool
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    #: The scopes the provider granted.
    scopes: list[str]
    #: Non-secret provider handles captured with the token (instance_url, realmId, hub_id,
    #: tenant_id, team_id...).
    metadata: dict[str, Any]
    #: Whether a credential is stored. The credential itself is never returned by this object.
    has_secret: bool
    #: The relay verbs this connection may use. GET, HEAD and POST unless set.
    allowed_methods: list[Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]]
    #: When the connection was created (epoch ms).
    created_at: int
    #: When the connection last changed (epoch ms).
    updated_at: int


class ConnectionsRotateCredentialsResponse(
    _ConnectionsRotateCredentialsResponseRequired, total=False
):
    #: The provider-side account this connection covers (a QuickBooks realm, a Slack workspace, a
    #: HubSpot hub, the authorizing user's id at the provider). Several connections of one provider
    #: coexist by it; null until connected.
    external_id: str | None
    #: The owner OAuth client that issued the stored token, or null when the instance client did.
    oauth_client_id: str | None
    #: When the access token expires, epoch milliseconds. Refreshed automatically on read.
    expires_at: int | None
    #: Who connected it. Informational only: the connection does not depend on that user, who may
    #: be deleted.
    authorized_by_user_id: str | None
    #: Epoch milliseconds.
    connected_at: int | None
    #: Epoch milliseconds.
    last_refreshed_at: int | None
    #: Epoch milliseconds.
    status_changed_at: int | None
    #: Why the connection left connected, or why the last refresh failed.
    last_error: None | dict[str, Any]
    #: Consecutive failed refreshes; 0 when healthy. A provider outage is retried with backoff and
    #: announced (connection.refresh_failed) after 3.
    refresh_failures: int
    #: When the keep-alive worker next refreshes this connection (epoch milliseconds), null when
    #: there is nothing to keep alive.
    next_refresh_at: int | None
    #: Deprecated, always null: a connection owns its tokens and no longer rides a user's linked
    #: account.
    external_account_id: None
    #: When the entered credential expires (epoch ms). connection.secret_expiring reminders go out
    #: 30, 7 and 1 days before.
    secret_expires_at: int | None
    #: While a rotation's overlap window is open: when the replaced version stops being accepted
    #: (epoch ms).
    previous_valid_until: int | None


class _ConnectionsOauthClientsSetBodyRequired(TypedDict):
    provider: str
    client_id: str


class ConnectionsOauthClientsSetBody(_ConnectionsOauthClientsSetBodyRequired, total=False):
    owner: dict[str, Any]
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    #: Write-only. Required when the client is first created; omit it to keep the stored secret.
    client_secret: str
    scopes: list[str]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    enabled: bool


class ConnectionsOauthClientsSetResponse(TypedDict):
    object: Literal["connection_oauth_client"]
    id: str
    owner: dict[str, Any]
    provider: str
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    client_id: str
    #: The client secret is write-only; it is sealed in the vault and never returned.
    has_secret: Literal[True]
    scopes: list[str]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    enabled: bool
    #: The redirect URI to register on this client at the provider.
    callback_url: str
    #: When the client was added (epoch ms).
    created_at: int
    #: When the client last changed (epoch ms).
    updated_at: int


class ConnectionsOauthClientsGetResponse(TypedDict):
    object: Literal["connection_oauth_client"]
    id: str
    owner: dict[str, Any]
    provider: str
    #: The provider environment the credential belongs to. sandbox selects the provider's test
    #: hosts (Salesforce test.salesforce.com, PayPal and QuickBooks sandboxes, DocuSign demo...).
    environment: Literal["production", "sandbox"]
    client_id: str
    #: The client secret is write-only; it is sealed in the vault and never returned.
    has_secret: Literal[True]
    scopes: list[str]
    #: Values that fill the provider's host templates for this one connection, for example
    #: {"subdomain":"acme"} (Zendesk), {"shop":"acme"} (Shopify),
    #: {"domain":"acme.my.salesforce.com"} (Salesforce My Domain), {"data_center":"eu"} (Zoho),
    #: {"tenant":"contoso.onmicrosoft.com"} (Microsoft), {"host":"git.examp
    host_params: dict[str, Any]
    enabled: bool
    #: The redirect URI to register on this client at the provider.
    callback_url: str
    #: When the client was added (epoch ms).
    created_at: int
    #: When the client last changed (epoch ms).
    updated_at: int


class _ConnectionsWebhooksVerifyBodyRequired(TypedDict):
    scheme: Literal[
        "hubspot_v3",
        "shopify_hmac",
        "intercom",
        "zoom",
        "slack_v0",
        "calendly",
        "stripe",
        "generic_hmac_sha256",
    ]
    #: The delivery's headers.
    headers: dict[str, Any]
    #: The body exactly as received (up to 1 MiB).
    raw_body: str


class ConnectionsWebhooksVerifyBody(_ConnectionsWebhooksVerifyBodyRequired, total=False):
    raw_body_encoding: Literal["utf8", "base64"]
    #: hubspot_v3: the HTTP method of the delivery (default POST).
    method: str
    #: hubspot_v3: the full URL the provider posted to.
    url: str
    #: Use this webhook endpoint's signing secret and options.
    endpoint_id: str
    tolerance_seconds: int
    #: generic_hmac_sha256: signature_header, encoding, prefix, algorithm.
    options: dict[str, Any]
    #: Set false to check without remembering the delivery (default true).
    record_replay: bool


class ConnectionsWebhooksVerifyResponse(TypedDict):
    object: Literal["connection_webhook_verification"]
    connection_id: str
    scheme: Literal[
        "hubspot_v3",
        "shopify_hmac",
        "intercom",
        "zoom",
        "slack_v0",
        "calendly",
        "stripe",
        "generic_hmac_sha256",
    ]
    #: True only for a genuine, fresh, first-time delivery.
    valid: bool
    reason: str | None
    #: The same delivery id (or signature) verified before on this connection.
    replayed: bool
    #: The signed timestamp, epoch seconds, for schemes that sign one.
    timestamp: int | None
    #: The provider's delivery id when the scheme carries one (Shopify).
    delivery_id: str | None
    #: Zoom endpoint.url_validation ({plainToken, encryptedToken}) or Slack url_verification
    #: ({challenge}): answer the provider with this body.
    handshake: dict[str, Any] | None


class _ConnectionsWebhooksCreateEndpointBodyRequired(TypedDict):
    scheme: Literal[
        "hubspot_v3",
        "shopify_hmac",
        "intercom",
        "zoom",
        "slack_v0",
        "calendly",
        "stripe",
        "generic_hmac_sha256",
    ]
    #: https URL that receives verified deliveries as Atlas-signed webhooks.
    forward_url: str


class ConnectionsWebhooksCreateEndpointBody(
    _ConnectionsWebhooksCreateEndpointBodyRequired, total=False
):
    #: Write-only. The provider's signing secret for this endpoint (Slack signing secret, Zoom
    #: secret token, Calendly signing key...). Without it, the connection's hmac_secret credential
    #: or its OAuth client secret is used.
    signing_secret: str
    #: generic_hmac_sha256 only: signature_header, encoding (hex or base64), prefix, algorithm.
    options: dict[str, Any]
    enabled: bool


class _ConnectionsWebhooksCreateEndpointResponseRequired(TypedDict):
    object: Literal["connection_webhook_endpoint"]
    id: str
    connection_id: str
    scheme: Literal[
        "hubspot_v3",
        "shopify_hmac",
        "intercom",
        "zoom",
        "slack_v0",
        "calendly",
        "stripe",
        "generic_hmac_sha256",
    ]
    forward_url: str
    #: Give this URL to the provider as the webhook target.
    ingress_url: str
    options: dict[str, Any]
    #: Whether the endpoint has its own provider signing secret (never returned).
    has_signing_secret: bool
    enabled: bool
    last_delivery_at: int | None
    #: When the endpoint was created (epoch ms).
    created_at: int
    #: When the endpoint last changed (epoch ms).
    updated_at: int


class ConnectionsWebhooksCreateEndpointResponse(
    _ConnectionsWebhooksCreateEndpointResponseRequired, total=False
):
    #: Only in the create response, once: verifies the Atlas-signed deliveries sent to forward_url
    #: (atlas-signature, as for any Atlas webhook).
    forward_secret: str


class ConnectionsWebhooksUpdateEndpointBody(TypedDict, total=False):
    scheme: Literal[
        "hubspot_v3",
        "shopify_hmac",
        "intercom",
        "zoom",
        "slack_v0",
        "calendly",
        "stripe",
        "generic_hmac_sha256",
    ]
    #: https URL that receives verified deliveries as Atlas-signed webhooks.
    forward_url: str
    #: Write-only. The provider's signing secret for this endpoint (Slack signing secret, Zoom
    #: secret token, Calendly signing key...). Without it, the connection's hmac_secret credential
    #: or its OAuth client secret is used.
    signing_secret: str
    #: generic_hmac_sha256 only: signature_header, encoding (hex or base64), prefix, algorithm.
    options: dict[str, Any]
    enabled: bool


class _ConnectionsWebhooksUpdateEndpointResponseRequired(TypedDict):
    object: Literal["connection_webhook_endpoint"]
    id: str
    connection_id: str
    scheme: Literal[
        "hubspot_v3",
        "shopify_hmac",
        "intercom",
        "zoom",
        "slack_v0",
        "calendly",
        "stripe",
        "generic_hmac_sha256",
    ]
    forward_url: str
    #: Give this URL to the provider as the webhook target.
    ingress_url: str
    options: dict[str, Any]
    #: Whether the endpoint has its own provider signing secret (never returned).
    has_signing_secret: bool
    enabled: bool
    last_delivery_at: int | None
    #: When the endpoint was created (epoch ms).
    created_at: int
    #: When the endpoint last changed (epoch ms).
    updated_at: int


class ConnectionsWebhooksUpdateEndpointResponse(
    _ConnectionsWebhooksUpdateEndpointResponseRequired, total=False
):
    #: Only in the create response, once: verifies the Atlas-signed deliveries sent to forward_url
    #: (atlas-signature, as for any Atlas webhook).
    forward_secret: str


class FgaListUsersBody(TypedDict, total=False):
    object: str | dict[str, Any]
    relation: str
    user_filters: list[dict[str, Any]]
    authorization_model_id: str
    contextual_tuples: list[dict[str, Any]] | dict[str, Any]
    context: dict[str, Any]
    page_size: int
    continuation_token: str
    consistency: Literal["UNSPECIFIED", "MINIMIZE_LATENCY", "HIGHER_CONSISTENCY"]
    consistency_token: str


class _FgaListUsersResponseRequired(TypedDict):
    object: Literal["fga.list_users"]
    #: Members as `type:id`, `type:id#relation` (relation filter), or `type:*` for a public
    #: wildcard.
    users: list[str]
    #: Users a wildcard in `users` does NOT cover.
    excluded_users: list[str]
    authorization_model_id: str


class FgaListUsersResponse(_FgaListUsersResponseRequired, total=False):
    #: Pass back to fetch the next page; null on the last page.
    continuation_token: str | None
    #: Opaque consistency token (zookie). Pass it back as `consistency_token` on a later read to
    #: require it be evaluated at least this fresh.
    consistency_token: str


class _OpenfgaListUsersBodyRequired(TypedDict):
    object: dict[str, Any]
    #: e.g. viewer
    relation: str
    user_filters: list[dict[str, Any]]


class OpenfgaListUsersBody(_OpenfgaListUsersBodyRequired, total=False):
    authorization_model_id: str
    #: The OpenFGA tuple-list wrapper.
    contextual_tuples: dict[str, Any]
    #: Request-time values for tuple-condition parameters. A tuple's own context wins on a clash.
    context: dict[str, Any]
    #: MINIMIZE_LATENCY (and UNSPECIFIED) may be answered from a short-lived result cache;
    #: HIGHER_CONSISTENCY bypasses it and reads the primary.
    consistency: Literal["UNSPECIFIED", "MINIMIZE_LATENCY", "HIGHER_CONSISTENCY"]
    #: A token returned by a write (or any read): evaluate at least that fresh, so a check can
    #: never be answered from before that write. Also accepted as the `Atlas-Consistency-Token`
    #: request header.
    consistency_token: str
    #: Defaults to 1000.
    page_size: int
    #: The `continuation_token` of the previous page.
    continuation_token: str


class _OpenfgaListUsersResponseRequired(TypedDict):
    users: list[dict[str, Any]]
    excluded_users: list[dict[str, Any]]


class OpenfgaListUsersResponse(_OpenfgaListUsersResponseRequired, total=False):
    #: Empty on the last page.
    continuation_token: str


class OpenfgaReadChangesResponse(TypedDict):
    changes: list[dict[str, Any]]
    continuation_token: str


class AttackProtectionSetAppAttestationSecretBody(TypedDict, total=False):
    secret: str
    kind: Literal["play_integrity", "devicecheck"]


class AttackProtectionSetAppAttestationSecretResponse(TypedDict):
    object: Literal["app_attestation_secret"]
    set: Literal[True]


class AttackProtectionRemoveAppAttestationSecretResponse(TypedDict):
    object: Literal["app_attestation_secret"]
    deleted: Literal[True]


class RiskBasedMfaSetReputationSecretBody(TypedDict, total=False):
    secret: str
    provider: str


class RiskBasedMfaSetReputationSecretResponse(TypedDict):
    object: Literal["risk_reputation_secret"]
    provider: str
    set: Literal[True]


class RiskBasedMfaRemoveReputationSecretResponse(TypedDict):
    object: Literal["risk_reputation_secret"]
    provider: str
    deleted: Literal[True]


class SsfStreamsCreateBody(TypedDict, total=False):
    delivery_method: Literal["push", "poll"]
    endpoint_url: str
    authorization_header: str
    audience: str
    description: str
    events_requested: list[str]


class SsfStreamsGetResponse(TypedDict):
    object: Literal["ssf_stream"]


class SsfStreamsUpdateBody(TypedDict, total=False):
    endpoint_url: str
    authorization_header: str
    description: str
    events_requested: list[str]
    status: Literal["enabled", "paused", "disabled"]


class SsfStreamsVerifyBody(TypedDict, total=False):
    state: str


class SsfStreamsGetStatusResponse(TypedDict):
    object: Literal["ssf_stream_status"]


class SsfStreamsUpdateStatusBody(TypedDict, total=False):
    status: Literal["enabled", "paused", "disabled"]


class SsfStreamsUpdateStatusResponse(TypedDict):
    object: Literal["ssf_stream_status"]


class SsfReceiversCreateBody(TypedDict, total=False):
    name: str
    issuer: str
    jwks_uri: str
    audience: str
    actions: dict[str, Any]


class SsfReceiversUpdateBody(TypedDict, total=False):
    name: str
    jwks_uri: str
    audience: str
    actions: dict[str, Any]
    enabled: bool


class NetworkZonesCreateBody(TypedDict, total=False):
    name: str
    description: str | None
    cidrs: list[str]
    countries: list[str]
    asns: list[int]
    anonymizers: list[Literal["tor", "datacenter", "vpn"]]
    enabled: bool


class NetworkZonesCreateResponse(TypedDict):
    object: Literal["network_zone"]
    id: str
    name: str
    description: str | None
    cidrs: list[str]
    #: ISO 3166-1 alpha-2, upper case.
    countries: list[str]
    asns: list[int]
    anonymizers: list[Literal["tor", "datacenter", "vpn"]]
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class NetworkZonesGetResponse(TypedDict):
    object: Literal["network_zone"]
    id: str
    name: str
    description: str | None
    cidrs: list[str]
    #: ISO 3166-1 alpha-2, upper case.
    countries: list[str]
    asns: list[int]
    anonymizers: list[Literal["tor", "datacenter", "vpn"]]
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class NetworkZonesUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    cidrs: list[str]
    countries: list[str]
    asns: list[int]
    anonymizers: list[Literal["tor", "datacenter", "vpn"]]
    enabled: bool


class NetworkZonesUpdateResponse(TypedDict):
    object: Literal["network_zone"]
    id: str
    name: str
    description: str | None
    cidrs: list[str]
    #: ISO 3166-1 alpha-2, upper case.
    countries: list[str]
    asns: list[int]
    anonymizers: list[Literal["tor", "datacenter", "vpn"]]
    enabled: bool
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class NetworkZonesCheckBody(TypedDict, total=False):
    ip: str


class NetworkZonesCheckResponse(TypedDict):
    object: Literal["network_zone_check"]
    zone_id: str
    #: The address checked, normalised.
    ip: str
    #: Whether the address falls inside the zone (always false while the zone is disabled).
    matches: bool
    #: What Atlas knows about the address; null where it has no data.
    facts: dict[str, Any]


class AccessPoliciesCreateBody(TypedDict, total=False):
    name: str
    description: str | None
    enabled: bool
    priority: int
    stages: list[Literal["sign_in", "authorize", "token"]]
    conditions: dict[str, Any]
    grants: list[dict[str, Any]]


class AccessPoliciesCreateResponse(TypedDict):
    object: Literal["access_policy"]
    id: str
    name: str
    description: str | None
    enabled: bool
    #: Lower evaluates first.
    priority: int
    #: Empty = every stage.
    stages: list[Literal["sign_in", "authorize", "token"]]
    #: All present conditions must match.
    conditions: dict[str, Any]
    grants: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AccessPoliciesSimulateBody(TypedDict, total=False):
    policy_id: str
    stage: str
    ip: str
    application_id: str
    user_id: str
    groups: list[str]
    orgs: list[str]
    roles: list[str]
    country: str
    risk_level: Literal["low", "medium", "high"]
    device_trust: Literal["trusted", "untrusted", "unknown"]
    auth_methods: list[str]
    mfa_verified: bool
    acr: list[str]
    now: int


class AccessPoliciesSimulateResponse(TypedDict):
    object: Literal["access_policy_simulation"]
    decision: Literal["allow", "block", "step_up"]
    matched: list[str]
    blocked_by: str | None
    requirements: dict[str, Any]
    unmet: list[str]


class AccessPoliciesGetResponse(TypedDict):
    object: Literal["access_policy"]
    id: str
    name: str
    description: str | None
    enabled: bool
    #: Lower evaluates first.
    priority: int
    #: Empty = every stage.
    stages: list[Literal["sign_in", "authorize", "token"]]
    #: All present conditions must match.
    conditions: dict[str, Any]
    grants: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AccessPoliciesUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    enabled: bool
    priority: int
    stages: list[Literal["sign_in", "authorize", "token"]]
    conditions: dict[str, Any]
    grants: list[dict[str, Any]]


class AccessPoliciesUpdateResponse(TypedDict):
    object: Literal["access_policy"]
    id: str
    name: str
    description: str | None
    enabled: bool
    #: Lower evaluates first.
    priority: int
    #: Empty = every stage.
    stages: list[Literal["sign_in", "authorize", "token"]]
    #: All present conditions must match.
    conditions: dict[str, Any]
    grants: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacCreateBody(TypedDict, total=False):
    name: str
    description: str | None
    enabled: bool
    fga_store_id: str | None
    source: str
    tests: list[dict[str, Any]]


class AbacCreateResponse(TypedDict):
    object: Literal["abac_policy"]
    id: str
    name: str
    description: str | None
    enabled: bool
    current_version: int
    #: The FGA store `fga.check(...)` consults.
    fga_store_id: str | None
    #: The current version’s policy source.
    source: str
    tests: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacGetResponse(TypedDict):
    object: Literal["abac_policy"]
    id: str
    name: str
    description: str | None
    enabled: bool
    current_version: int
    #: The FGA store `fga.check(...)` consults.
    fga_store_id: str | None
    #: The current version’s policy source.
    source: str
    tests: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    enabled: bool
    fga_store_id: str | None
    source: str
    tests: list[dict[str, Any]]
    current_version: int


class AbacUpdateResponse(TypedDict):
    object: Literal["abac_policy"]
    id: str
    name: str
    description: str | None
    enabled: bool
    current_version: int
    #: The FGA store `fga.check(...)` consults.
    fga_store_id: str | None
    #: The current version’s policy source.
    source: str
    tests: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacTestBody(TypedDict, total=False):
    version: int
    source: str
    tests: list[dict[str, Any]]


class AbacTestResponse(TypedDict):
    object: Literal["abac_policy_test_run"]
    passed: bool
    #: Which rules and `when`/`unless` clauses the test cases exercised.
    coverage: dict[str, Any]
    results: list[dict[str, Any]]


class AbacEvaluateBody(TypedDict, total=False):
    principal: dict[str, Any]
    action: str
    resource: dict[str, Any]
    context: dict[str, Any]
    entities: list[dict[str, Any]]
    policy_ids: list[str]


class AbacEvaluateResponse(TypedDict):
    object: Literal["abac_decision"]
    decision: Literal["allow", "deny"]
    #: Names of the policies that decided it.
    reasons: list[str]
    #: Policies skipped because they errored while evaluating.
    errors: list[str]


class _AbacPartialEvaluateBodyRequired(TypedDict):
    principal: dict[str, Any]
    action: str
    resource: dict[str, Any]


class AbacPartialEvaluateBody(_AbacPartialEvaluateBodyRequired, total=False):
    context: dict[str, Any]
    #: Other entities the policies reference (hierarchy and attributes).
    entities: list[dict[str, Any]]
    #: Only these policies (default: every enabled one).
    policy_ids: list[str]
    #: Which entity’s attributes are unknown. Default ["resource"].
    unknowns: list[Literal["principal", "resource"]]
    #: Replace relationship conditions with the ids the FGA store returns. Default true.
    resolve_relations: bool
    output: dict[str, Any]


class _AbacPartialEvaluateResponseRequired(TypedDict):
    object: Literal["abac_residual"]
    #: `allow`/`deny` when the filter is constant; `conditional` otherwise.
    decision: Literal["allow", "deny", "conditional"]
    #: A residual-policy condition over fields of the unknown entity (`resource.department`,
    #: `principal.level`; reserved `<var>.$id` and `<var>.$ancestors`). Leaves are total booleans
    #: (a missing field is false) and there is no `not`. `and`/`or` carry `args`;
    #: `eq|ne|lt|lte|gt|gte` carry `field` with a `valu
    filter: dict[str, Any]
    #: A residual-policy condition over fields of the unknown entity (`resource.department`,
    #: `principal.level`; reserved `<var>.$id` and `<var>.$ancestors`). Leaves are total booleans
    #: (a missing field is false) and there is no `not`. `and`/`or` carry `args`;
    #: `eq|ne|lt|lte|gt|gte` carry `field` with a `valu
    permit: dict[str, Any]
    #: A residual-policy condition over fields of the unknown entity (`resource.department`,
    #: `principal.level`; reserved `<var>.$id` and `<var>.$ancestors`). Leaves are total booleans
    #: (a missing field is false) and there is no `not`. `and`/`or` carry `args`;
    #: `eq|ne|lt|lte|gt|gte` carry `field` with a `valu
    forbid: dict[str, Any]
    unknowns: list[Literal["principal", "resource"]]
    #: true when relationship conditions were replaced by id lists from the FGA store.
    relations_resolved: bool


class AbacPartialEvaluateResponse(_AbacPartialEvaluateResponseRequired, total=False):
    sql: dict[str, Any]
    #: A Prisma `where` object.
    prisma: dict[str, Any]


class _AbacAccessibleResourcesBodyRequired(TypedDict):
    principal: dict[str, Any]
    action: str
    #: The Atlas resource type key (the policy type is its PascalCase form).
    resource_type: str


class AbacAccessibleResourcesBody(_AbacAccessibleResourcesBodyRequired, total=False):
    context: dict[str, Any]
    entities: list[dict[str, Any]]
    candidates: list[dict[str, Any]]
    policy_ids: list[str]
    #: Default 100.
    limit: int
    starting_after: str


AbacDiffResponse = TypedDict(
    "AbacDiffResponse",
    {
        "object": 'Literal["abac_policy_diff"]',
        "policy_id": "str",
        "from": "int",
        "to": "int",
        "text": "dict[str, Any]",
        "semantic": "dict[str, Any] | None",
    },
    total=False,
)


class _AbacDiffSourcesBodyRequired(TypedDict):
    before: str
    after: str


class AbacDiffSourcesBody(_AbacDiffSourcesBodyRequired, total=False):
    semantic: bool
    max_requests: int
    max_changes: int


AbacDiffSourcesResponse = TypedDict(
    "AbacDiffSourcesResponse",
    {
        "object": 'Literal["abac_policy_diff"]',
        "policy_id": "str",
        "from": "int",
        "to": "int",
        "text": "dict[str, Any]",
        "semantic": "dict[str, Any] | None",
    },
    total=False,
)


class AbacAuthzenEvaluationBody(TypedDict, total=False):
    subject: dict[str, Any]
    resource: dict[str, Any]
    action: dict[str, Any]
    context: dict[str, Any]
    evaluations: list[dict[str, Any]]
    options: dict[str, Any]


class _AbacAuthzenEvaluationResponseRequired(TypedDict):
    #: true = allowed.
    decision: bool


class AbacAuthzenEvaluationResponse(_AbacAuthzenEvaluationResponseRequired, total=False):
    context: dict[str, Any]


class AbacAuthzenEvaluationsBody(TypedDict, total=False):
    subject: dict[str, Any]
    resource: dict[str, Any]
    action: dict[str, Any]
    context: dict[str, Any]
    evaluations: list[dict[str, Any]]
    options: dict[str, Any]


class AbacAuthzenEvaluationsResponse(TypedDict, total=False):
    evaluations: list[dict[str, Any]]
    decision: bool


class _AbacAuthzenSearchSubjectBodyRequired(TypedDict):
    subject: dict[str, Any]
    action: dict[str, Any]
    resource: dict[str, Any]


class AbacAuthzenSearchSubjectBody(_AbacAuthzenSearchSubjectBodyRequired, total=False):
    context: dict[str, Any]
    page: dict[str, Any]


class AbacAuthzenSearchSubjectResponse(TypedDict):
    results: list[dict[str, Any]]
    page: dict[str, Any]


class _AbacAuthzenSearchResourceBodyRequired(TypedDict):
    subject: dict[str, Any]
    action: dict[str, Any]
    resource: dict[str, Any]


class AbacAuthzenSearchResourceBody(_AbacAuthzenSearchResourceBodyRequired, total=False):
    context: dict[str, Any]
    page: dict[str, Any]


class AbacAuthzenSearchResourceResponse(TypedDict):
    results: list[dict[str, Any]]
    page: dict[str, Any]


class _AbacAuthzenSearchActionBodyRequired(TypedDict):
    subject: dict[str, Any]
    resource: dict[str, Any]


class AbacAuthzenSearchActionBody(_AbacAuthzenSearchActionBodyRequired, total=False):
    context: dict[str, Any]
    page: dict[str, Any]


class AbacAuthzenSearchActionResponse(TypedDict):
    results: list[dict[str, Any]]
    page: dict[str, Any]


class _AbacTemplatesCreateBodyRequired(TypedDict):
    name: str
    #: Policy source with `?principal` and/or `?resource` slots in the scope, e.g. `permit
    #: (principal == ?principal, action == Action::"read", resource in ?resource);`.
    source: str


class AbacTemplatesCreateBody(_AbacTemplatesCreateBodyRequired, total=False):
    description: str | None
    #: The FGA store `fga.check(...)` in the source consults.
    fga_store_id: str | None


class _AbacTemplatesCreateResponseRequired(TypedDict):
    object: Literal["abac_policy_template"]
    id: str
    name: str
    description: str | None
    #: Policy source with `?principal` / `?resource` slots in the scope.
    source: str
    #: Increases each time `source` changes; every link follows it.
    version: int
    slots: list[Literal["?principal", "?resource"]]
    fga_store_id: str | None
    link_count: int
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacTemplatesCreateResponse(_AbacTemplatesCreateResponseRequired, total=False):
    #: On an update that changed `source`: the links that now evaluate the new source.
    links_updated: int


class _AbacTemplatesGetResponseRequired(TypedDict):
    object: Literal["abac_policy_template"]
    id: str
    name: str
    description: str | None
    #: Policy source with `?principal` / `?resource` slots in the scope.
    source: str
    #: Increases each time `source` changes; every link follows it.
    version: int
    slots: list[Literal["?principal", "?resource"]]
    fga_store_id: str | None
    link_count: int
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacTemplatesGetResponse(_AbacTemplatesGetResponseRequired, total=False):
    #: On an update that changed `source`: the links that now evaluate the new source.
    links_updated: int


class AbacTemplatesUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    #: Policy source with `?principal` and/or `?resource` slots in the scope, e.g. `permit
    #: (principal == ?principal, action == Action::"read", resource in ?resource);`.
    source: str
    #: The FGA store `fga.check(...)` in the source consults.
    fga_store_id: str | None


class _AbacTemplatesUpdateResponseRequired(TypedDict):
    object: Literal["abac_policy_template"]
    id: str
    name: str
    description: str | None
    #: Policy source with `?principal` / `?resource` slots in the scope.
    source: str
    #: Increases each time `source` changes; every link follows it.
    version: int
    slots: list[Literal["?principal", "?resource"]]
    fga_store_id: str | None
    link_count: int
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacTemplatesUpdateResponse(_AbacTemplatesUpdateResponseRequired, total=False):
    #: On an update that changed `source`: the links that now evaluate the new source.
    links_updated: int


class _AbacLinksCreateBodyRequired(TypedDict):
    template_id: str
    #: Shown as the deciding policy in decisions.
    name: str


class AbacLinksCreateBody(_AbacLinksCreateBodyRequired, total=False):
    #: An entity such as `{ "type": "User", "id": "alice" }`.
    principal: dict[str, Any] | None
    #: An entity such as `{ "type": "User", "id": "alice" }`.
    resource: dict[str, Any] | None
    enabled: bool


class AbacLinksCreateResponse(TypedDict):
    object: Literal["abac_policy_link"]
    id: str
    #: Shown as the deciding policy in decisions.
    name: str
    template_id: str
    template_name: str | None
    #: The template version the link currently follows (always the latest).
    template_version: int | None
    principal: dict[str, Any] | None
    resource: dict[str, Any] | None
    enabled: bool
    #: The policy source the link evaluates: the template with its slots filled.
    source: str
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacLinksGetResponse(TypedDict):
    object: Literal["abac_policy_link"]
    id: str
    #: Shown as the deciding policy in decisions.
    name: str
    template_id: str
    template_name: str | None
    #: The template version the link currently follows (always the latest).
    template_version: int | None
    principal: dict[str, Any] | None
    resource: dict[str, Any] | None
    enabled: bool
    #: The policy source the link evaluates: the template with its slots filled.
    source: str
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class AbacLinksUpdateBody(TypedDict, total=False):
    template_id: str
    #: Shown as the deciding policy in decisions.
    name: str
    #: An entity such as `{ "type": "User", "id": "alice" }`.
    principal: dict[str, Any] | None
    #: An entity such as `{ "type": "User", "id": "alice" }`.
    resource: dict[str, Any] | None
    enabled: bool


class AbacLinksUpdateResponse(TypedDict):
    object: Literal["abac_policy_link"]
    id: str
    #: Shown as the deciding policy in decisions.
    name: str
    template_id: str
    template_name: str | None
    #: The template version the link currently follows (always the latest).
    template_version: int | None
    principal: dict[str, Any] | None
    resource: dict[str, Any] | None
    enabled: bool
    #: The policy source the link evaluates: the template with its slots filled.
    source: str
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class _AbacSchemaGetResponseRequired(TypedDict):
    object: Literal["abac_schema"]
    #: The entity schema: `entity_types` and `actions`. Null when none is set.
    schema: dict[str, Any] | None
    #: 0 when none is set.
    version: int
    updated_at: int | None


class AbacSchemaGetResponse(_AbacSchemaGetResponseRequired, total=False):
    #: On a save: the errors this schema would give the policies and links already stored (the
    #: schema is saved anyway; they must be fixed before those are edited).
    policy_issues: list[dict[str, Any]]


class AbacSchemaSetBody(TypedDict):
    schema: dict[str, Any]


class _AbacSchemaSetResponseRequired(TypedDict):
    object: Literal["abac_schema"]
    #: The entity schema: `entity_types` and `actions`. Null when none is set.
    schema: dict[str, Any] | None
    #: 0 when none is set.
    version: int
    updated_at: int | None


class AbacSchemaSetResponse(_AbacSchemaSetResponseRequired, total=False):
    #: On a save: the errors this schema would give the policies and links already stored (the
    #: schema is saved anyway; they must be fixed before those are edited).
    policy_issues: list[dict[str, Any]]


class _AbacSchemaValidateBodyRequired(TypedDict):
    source: str


class AbacSchemaValidateBody(_AbacSchemaValidateBodyRequired, total=False):
    schema: dict[str, Any]
    template: bool


class AbacSchemaValidateResponse(TypedDict):
    object: Literal["abac_validation"]
    #: false when there is any error (warnings do not count).
    valid: bool
    #: false when no schema was set or the source did not parse.
    schema_checked: bool
    issues: list[dict[str, Any]]


class ResourcesUpsertBody(TypedDict, total=False):
    type: str
    external_id: str
    name: str | None
    parent: dict[str, Any] | None
    metadata: dict[str, Any]


class ResourcesUpsertResponse(TypedDict):
    object: Literal["resource"]
    id: str
    type: str
    #: Your own identifier for the resource.
    external_id: str
    name: str | None
    parent_id: str | None
    metadata: dict[str, Any]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class ResourcesSyncBody(TypedDict, total=False):
    resources: list[dict[str, Any]]


class ResourcesGetResponse(TypedDict):
    object: Literal["resource"]
    id: str
    type: str
    #: Your own identifier for the resource.
    external_id: str
    name: str | None
    parent_id: str | None
    metadata: dict[str, Any]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class ResourcesCheckBody(TypedDict, total=False):
    subject: dict[str, Any]
    permission: str
    resource: dict[str, Any]
    groups: list[str]


class _ResourcesCheckResponseRequired(TypedDict):
    object: Literal["resource_check"]
    allowed: bool
    resource_id: str


class ResourcesCheckResponse(_ResourcesCheckResponseRequired, total=False):
    #: The assignments that allow it (single checks only).
    grants: list[dict[str, Any]]


class ResourcesCheckBatchBody(TypedDict, total=False):
    checks: list[dict[str, Any]]


class ResourcesAccessibleBody(TypedDict, total=False):
    subject: dict[str, Any]
    permission: str
    type: str
    groups: list[str]
    limit: int
    starting_after: str


class ResourcesTypesCreateBody(TypedDict, total=False):
    key: str
    name: str
    description: str | None
    parent_type: str | None
    inherit: bool
    roles: list[dict[str, Any]]


class ResourcesTypesCreateResponse(TypedDict):
    object: Literal["resource_type"]
    key: str
    name: str
    description: str | None
    #: The type a resource of this type nests under.
    parent_type: str | None
    #: Whether assignments on a parent resource flow down to resources of this type.
    inherit: bool
    roles: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class ResourcesTypesGetResponse(TypedDict):
    object: Literal["resource_type"]
    key: str
    name: str
    description: str | None
    #: The type a resource of this type nests under.
    parent_type: str | None
    #: Whether assignments on a parent resource flow down to resources of this type.
    inherit: bool
    roles: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class ResourcesTypesUpdateBody(TypedDict, total=False):
    name: str
    description: str | None
    parent_type: str | None
    inherit: bool
    roles: list[dict[str, Any]]


class ResourcesTypesUpdateResponse(TypedDict):
    object: Literal["resource_type"]
    key: str
    name: str
    description: str | None
    #: The type a resource of this type nests under.
    parent_type: str | None
    #: Whether assignments on a parent resource flow down to resources of this type.
    inherit: bool
    roles: list[dict[str, Any]]
    #: Created (epoch ms).
    created_at: int
    #: Last updated (epoch ms).
    updated_at: int


class ResourcesAssignmentsAssignBody(TypedDict, total=False):
    resource: dict[str, Any]
    subject: dict[str, Any]
    role: str
    inherit: bool


class ResourcesAssignmentsAssignResponse(TypedDict):
    object: Literal["resource_role_assignment"]
    id: str
    resource_id: str
    subject: dict[str, Any]
    role: str
    inherit: bool
    #: Created (epoch ms).
    created_at: int


class OrgRoleGrantsCreateBody(TypedDict, total=False):
    grantor_org_id: str
    grantee_org_id: str
    role_keys: list[str]


class OrgRoleGrantsCreateResponse(TypedDict):
    object: Literal["org_role_grant"]
    id: str
    grantor_org_id: str
    grantee_org_id: str
    role_keys: list[str]
    status: Literal["active", "revoked"]
    #: Created (epoch ms).
    created_at: int
    revoked_at: int | None


class OrgRoleGrantsGetResponse(TypedDict):
    object: Literal["org_role_grant"]
    id: str
    grantor_org_id: str
    grantee_org_id: str
    role_keys: list[str]
    status: Literal["active", "revoked"]
    #: Created (epoch ms).
    created_at: int
    revoked_at: int | None


class OrgRoleGrantsUpdateBody(TypedDict, total=False):
    role_keys: list[str]


class OrgRoleGrantsUpdateResponse(TypedDict):
    object: Literal["org_role_grant"]
    id: str
    grantor_org_id: str
    grantee_org_id: str
    role_keys: list[str]
    status: Literal["active", "revoked"]
    #: Created (epoch ms).
    created_at: int
    revoked_at: int | None


class OrgRoleGrantsRevokeResponse(TypedDict):
    object: Literal["org_role_grant"]
    id: str
    grantor_org_id: str
    grantee_org_id: str
    role_keys: list[str]
    status: Literal["active", "revoked"]
    #: Created (epoch ms).
    created_at: int
    revoked_at: int | None


class OrgRoleGrantsDelegateBody(TypedDict, total=False):
    user_id: str
    role_key: str


class OrgRoleGrantsDelegateResponse(TypedDict):
    object: Literal["org_role_delegation"]
    id: str
    grant_id: str
    user_id: str
    role_key: str
    #: Created (epoch ms).
    created_at: int


class DevicesReportBody(TypedDict, total=False):
    external_id: str
    source: str
    user_id: str | None
    user_email: str
    name: str | None
    platform: str | None
    managed: bool
    compliant: bool
    posture: dict[str, Any]


class _DevicesReportResponseRequired(TypedDict):
    object: Literal["device"]
    id: str
    user_id: str | None
    source: str
    external_id: str
    managed: bool
    compliant: bool
    posture: dict[str, Any]
    #: Last posture report (epoch ms).
    last_reported_at: int
    #: Created (epoch ms).
    created_at: int


class DevicesReportResponse(_DevicesReportResponseRequired, total=False):
    name: str | None
    platform: str | None


class _DevicesGetResponseRequired(TypedDict):
    object: Literal["device"]
    id: str
    user_id: str | None
    source: str
    external_id: str
    managed: bool
    compliant: bool
    posture: dict[str, Any]
    #: Last posture report (epoch ms).
    last_reported_at: int
    #: Created (epoch ms).
    created_at: int


class DevicesGetResponse(_DevicesGetResponseRequired, total=False):
    name: str | None
    platform: str | None


class DevicesIngestPostureBody(TypedDict, total=False):
    devices: list[dict[str, Any]]


class _AuthzDecisionsStatsResponseRequired(TypedDict):
    object: Literal["authz_decision_stats"]
    recorded: int
    by_source: dict[str, Any]
    latency_ms: dict[str, Any]


class AuthzDecisionsStatsResponse(_AuthzDecisionsStatsResponseRequired, total=False):
    since: int
    until: int
    #: Recorded decisions scaled back up by their sample rates.
    estimated_total: int


class _AuthzDecisionsGetResponseRequired(TypedDict):
    object: Literal["authz_decision"]
    id: str
    source: Literal["abac", "authzen", "fga", "access_policy", "mcp_gateway"]
    decision: Literal["allow", "deny"]
    #: Reasons (policy names), matched policies, error counts, FGA `allowed` and whether it was
    #: served from cache.
    result: dict[str, Any]
    latency_ms: float
    #: The probability this decision was kept at; divide counts by it to estimate the true volume.
    sample_rate: float
    #: Decided (epoch ms).
    created_at: int


class AuthzDecisionsGetResponse(_AuthzDecisionsGetResponseRequired, total=False):
    #: Who asked: `Type::id` (ABAC / AuthZEN), the FGA user, or the user id (access policies).
    principal: str | None
    #: The action, the FGA relation, or the access-policy stage.
    action: str | None
    resource: str | None
    #: The request as kept by `input_mode`: identifiers only, or the whole request with the
    #: configured paths blanked.
    input: dict[str, Any] | None
    #: The signed-bundle revision in force when this was decided (`rev_…`); access-policy decisions
    #: carry an `ap_…` digest instead.
    policy_revision: str | None
    #: The exact policy versions or FGA model that evaluated.
    policy_version: dict[str, Any] | None
    actor_id: str | None


class AuthzDecisionsSettingsGetResponse(TypedDict):
    object: Literal["authz_decision_settings"]
    #: Record decisions. Off by default.
    enabled: bool
    #: Probability an allow is recorded.
    sample_rate_allow: float
    #: Probability a deny is recorded.
    sample_rate_deny: float
    #: `ids` keeps only identifiers; `full` keeps the request minus the `redact` paths; `none`
    #: keeps no input.
    input_mode: Literal["ids", "full", "none"]
    #: Dotted paths blanked in `full` mode; `*` matches one segment (`context.ip`,
    #: `principal.attributes.*`).
    redact: list[str]
    #: Also emit each recorded decision as an `authz.decision` event, so log streams, webhooks and
    #: event destinations receive it.
    ship_to_events: bool
    #: Days to keep decisions; null keeps them.
    retention_days: int | None


class AuthzDecisionsSettingsUpdateBody(TypedDict, total=False):
    enabled: bool
    sample_rate_allow: float
    sample_rate_deny: float
    input_mode: Literal["ids", "full", "none"]
    redact: list[str]
    ship_to_events: bool
    retention_days: int | None


class AuthzDecisionsSettingsUpdateResponse(TypedDict):
    object: Literal["authz_decision_settings"]
    #: Record decisions. Off by default.
    enabled: bool
    #: Probability an allow is recorded.
    sample_rate_allow: float
    #: Probability a deny is recorded.
    sample_rate_deny: float
    #: `ids` keeps only identifiers; `full` keeps the request minus the `redact` paths; `none`
    #: keeps no input.
    input_mode: Literal["ids", "full", "none"]
    #: Dotted paths blanked in `full` mode; `*` matches one segment (`context.ip`,
    #: `principal.attributes.*`).
    redact: list[str]
    #: Also emit each recorded decision as an `authz.decision` event, so log streams, webhooks and
    #: event destinations receive it.
    ship_to_events: bool
    #: Days to keep decisions; null keeps them.
    retention_days: int | None


class PolicyBundlesCurrentResponse(TypedDict):
    object: Literal["policy_bundle_revision"]
    revision: str


class _PolicyBundlesExportResponseRequired(TypedDict):
    object: Literal["policy_bundle"]
    #: A digest of the bundle CONTENT (`rev_…`): the same policy has the same revision on every
    #: instance.
    revision: str
    #: SHA-256 of the archive bytes.
    sha256: str
    size: int
    #: The instance signing key id (`kid`), published in the JWKS.
    key_id: str
    algorithm: Literal["RS256", "ES256"]
    #: A detached compact JWS (`header..signature`) over the archive bytes.
    signature: str
    origin: Literal["export", "import"]
    #: format, format_version, revision, created_at, contents and the SHA-256 of every file.
    manifest: dict[str, Any]
    #: Created (epoch ms).
    created_at: int


class PolicyBundlesExportResponse(_PolicyBundlesExportResponseRequired, total=False):
    #: The tar.gz, base64-encoded. Present on create and get; omitted from lists.
    bundle: str
    media_type: Literal["application/gzip"]


class _PolicyBundlesGetResponseRequired(TypedDict):
    object: Literal["policy_bundle"]
    #: A digest of the bundle CONTENT (`rev_…`): the same policy has the same revision on every
    #: instance.
    revision: str
    #: SHA-256 of the archive bytes.
    sha256: str
    size: int
    #: The instance signing key id (`kid`), published in the JWKS.
    key_id: str
    algorithm: Literal["RS256", "ES256"]
    #: A detached compact JWS (`header..signature`) over the archive bytes.
    signature: str
    origin: Literal["export", "import"]
    #: format, format_version, revision, created_at, contents and the SHA-256 of every file.
    manifest: dict[str, Any]
    #: Created (epoch ms).
    created_at: int


class PolicyBundlesGetResponse(_PolicyBundlesGetResponseRequired, total=False):
    #: The tar.gz, base64-encoded. Present on create and get; omitted from lists.
    bundle: str
    media_type: Literal["application/gzip"]


class _PolicyBundlesVerifyBodyRequired(TypedDict):
    #: The bundle (tar.gz), base64-encoded.
    bundle: str
    #: The detached compact JWS (`header..signature`) over the archive bytes.
    signature: str


class PolicyBundlesVerifyBody(_PolicyBundlesVerifyBodyRequired, total=False):
    #: Public keys to trust IN ADDITION to this instance's own, as a JWKS — for a bundle signed by
    #: another instance (promote staging to production). Private key material is rejected.
    trusted_jwks: dict[str, Any]


class _PolicyBundlesVerifyResponseRequired(TypedDict):
    object: Literal["policy_bundle_verification"]
    #: Signature AND integrity both check out.
    valid: bool
    signature: dict[str, Any]
    #: Every manifest digest matches, nothing is added or missing, and the revision recomputed from
    #: the content equals the manifest. `code`: invalid_archive, invalid_manifest, digest_mismatch,
    #: unlisted_file, missing_file, revision_mismatch, invalid_content, unsupported_version.
    integrity: dict[str, Any]


class PolicyBundlesVerifyResponse(_PolicyBundlesVerifyResponseRequired, total=False):
    revision: str | None
    manifest: dict[str, Any] | None


class _PolicyBundlesImportBodyRequired(TypedDict):
    #: The bundle (tar.gz), base64-encoded.
    bundle: str
    #: The detached compact JWS (`header..signature`) over the archive bytes.
    signature: str


class PolicyBundlesImportBody(_PolicyBundlesImportBodyRequired, total=False):
    #: Public keys to trust IN ADDITION to this instance's own, as a JWKS — for a bundle signed by
    #: another instance (promote staging to production). Private key material is rejected.
    trusted_jwks: dict[str, Any]
    #: Return the diff and apply nothing.
    dry_run: bool
    #: Also delete ABAC policies absent from the bundle.
    prune: bool


class _PolicyBundlesImportResponseRequired(TypedDict):
    object: Literal["policy_bundle_import"]
    dry_run: bool
    applied: bool
    revision: str
    #: What importing a bundle would change.
    diff: dict[str, Any]


class PolicyBundlesImportResponse(_PolicyBundlesImportResponseRequired, total=False):
    prune: bool


class _ProxyAppsCreateBodyRequired(TypedDict):
    name: str
    hostname: str
    upstream_url: str


class ProxyAppsCreateBody(_ProxyAppsCreateBodyRequired, total=False):
    #: Path / method rules requiring a role, permission or entitlement.
    rules: list[dict[str, Any]]
    public_paths: list[str]
    inject_headers: bool
    inject_token: bool
    #: Also let an active agent through with its machine token (for example to front an MCP
    #: gateway). Its scopes count as the permissions rules check. Default false.
    allow_agent_tokens: bool
    enabled: bool


class ProxyAppsCreateResponse(TypedDict, total=False):
    object: Literal["proxy_app"]
    id: str
    name: str
    hostname: str
    upstream_url: str
    rules: list[dict[str, Any]]
    public_paths: list[str]
    inject_headers: bool
    inject_token: bool
    allow_agent_tokens: bool
    enabled: bool
    created_at: int
    updated_at: int


class ProxyAppsGetResponse(TypedDict, total=False):
    object: Literal["proxy_app"]
    id: str
    name: str
    hostname: str
    upstream_url: str
    rules: list[dict[str, Any]]
    public_paths: list[str]
    inject_headers: bool
    inject_token: bool
    allow_agent_tokens: bool
    enabled: bool
    created_at: int
    updated_at: int


class ProxyAppsUpdateBody(TypedDict, total=False):
    name: str
    hostname: str
    upstream_url: str
    #: Path / method rules requiring a role, permission or entitlement.
    rules: list[dict[str, Any]]
    public_paths: list[str]
    inject_headers: bool
    inject_token: bool
    #: Also let an active agent through with its machine token (for example to front an MCP
    #: gateway). Its scopes count as the permissions rules check. Default false.
    allow_agent_tokens: bool
    enabled: bool


class ProxyAppsUpdateResponse(TypedDict, total=False):
    object: Literal["proxy_app"]
    id: str
    name: str
    hostname: str
    upstream_url: str
    rules: list[dict[str, Any]]
    public_paths: list[str]
    inject_headers: bool
    inject_token: bool
    allow_agent_tokens: bool
    enabled: bool
    created_at: int
    updated_at: int


class _McpGatewaysCreateBodyRequired(TypedDict):
    name: str
    upstream_url: str


class McpGatewaysCreateBody(_McpGatewaysCreateBodyRequired, total=False):
    upstream_authorization: str
    default_policy: Literal["allow", "deny"]
    enabled: bool
    #: Authorize every tool call through the ABAC policy engine as well as the tool policy. The
    #: principal is the agent (type Agent, with name, tier, owner_user_id, organization_id, scopes,
    #: data), the action is the tool name, and the resource is the tool (type McpTool, with
    #: gateway_id, gateway_name, tool an
    abac: dict[str, Any]
    #: Tool name to { allow?, scopes?, conditions?: [{ arg, op: eq|neq|lte|gte|in|not_in|present,
    #: value }], approval?, mask?: { fields?, presets?: email|card|ssn|phone } }.
    tools: dict[str, Any]


class McpGatewaysUpdateBody(TypedDict, total=False):
    #: Authorize every tool call through the ABAC policy engine as well as the tool policy. The
    #: principal is the agent (type Agent, with name, tier, owner_user_id, organization_id, scopes,
    #: data), the action is the tool name, and the resource is the tool (type McpTool, with
    #: gateway_id, gateway_name, tool an
    abac: dict[str, Any]


class McpGatewaysBudgetsCreateBody(TypedDict, total=False):
    name: str
    scope: Literal["agent", "session"]
    metric: Literal["calls", "cost", "rate"]
    #: The ceiling, in calls or cost units.
    limit: float
    #: Fixed window length in seconds; null never resets. Required for rate.
    window_seconds: int | None
    agent_id: str | None
    tool: str | None
    #: cost: what one call costs when cost_arg is not set. Default 1.
    cost_per_call: float
    #: cost: dot path to a number in the call arguments that is the cost of the call.
    cost_arg: str | None
    enabled: bool


class _McpGatewaysBudgetsCreateResponseRequired(TypedDict):
    object: Literal["mcp_budget"]
    id: str
    gateway_id: str
    name: str
    scope: Literal["agent", "session"]
    metric: Literal["calls", "cost", "rate"]
    limit: float
    enabled: bool
    created_at: int


class McpGatewaysBudgetsCreateResponse(_McpGatewaysBudgetsCreateResponseRequired, total=False):
    agent_id: str | None
    tool: str | None
    window_seconds: int | None
    cost_per_call: float
    cost_arg: str | None


class _McpGatewaysBudgetsGetResponseRequired(TypedDict):
    object: Literal["mcp_budget"]
    id: str
    gateway_id: str
    name: str
    scope: Literal["agent", "session"]
    metric: Literal["calls", "cost", "rate"]
    limit: float
    enabled: bool
    created_at: int


class McpGatewaysBudgetsGetResponse(_McpGatewaysBudgetsGetResponseRequired, total=False):
    agent_id: str | None
    tool: str | None
    window_seconds: int | None
    cost_per_call: float
    cost_arg: str | None


class McpGatewaysBudgetsUpdateBody(TypedDict, total=False):
    name: str
    scope: Literal["agent", "session"]
    metric: Literal["calls", "cost", "rate"]
    #: The ceiling, in calls or cost units.
    limit: float
    #: Fixed window length in seconds; null never resets. Required for rate.
    window_seconds: int | None
    agent_id: str | None
    tool: str | None
    #: cost: what one call costs when cost_arg is not set. Default 1.
    cost_per_call: float
    #: cost: dot path to a number in the call arguments that is the cost of the call.
    cost_arg: str | None
    enabled: bool


class _McpGatewaysBudgetsUpdateResponseRequired(TypedDict):
    object: Literal["mcp_budget"]
    id: str
    gateway_id: str
    name: str
    scope: Literal["agent", "session"]
    metric: Literal["calls", "cost", "rate"]
    limit: float
    enabled: bool
    created_at: int


class McpGatewaysBudgetsUpdateResponse(_McpGatewaysBudgetsUpdateResponseRequired, total=False):
    agent_id: str | None
    tool: str | None
    window_seconds: int | None
    cost_per_call: float
    cost_arg: str | None


class _McpGatewaysBudgetsUsageResponseRequired(TypedDict):
    object: Literal["mcp_budget_usage"]
    budget_id: str
    used: float
    limit: float
    remaining: float


class McpGatewaysBudgetsUsageResponse(_McpGatewaysBudgetsUsageResponseRequired, total=False):
    agent_id: str
    resets_at: int | None


class InstanceIntegrationsRotateEventsSecretBody(TypedDict, total=False):
    #: How long the previous secret keeps signing deliveries (default 0 = stop now).
    overlap_seconds: int


class InstanceIntegrationsRotateEventsSecretResponse(TypedDict):
    object: Literal["integration_events_secret"]
    integration: str
    endpoint_id: str
    url: str
    #: The new signing secret. Shown once.
    secret: str
    overlap_seconds: int
    #: Epoch ms when the old secret stops signing; null when it already has.
    previous_secret_expires_at: int | None
    #: What happens to the old secret, said plainly.
    warning: str


class _IntegrationsRunCardActionBodyRequired(TypedDict):
    sub: str


class IntegrationsRunCardActionBody(_IntegrationsRunCardActionBodyRequired, total=False):
    iss: str
    #: Who pressed the button in the integrated service (recorded in the audit log).
    agent: dict[str, Any]


class IntegrationsRunCardActionResponse(TypedDict):
    object: Literal["integration_card_action"]
    integration: str
    action: Literal["revoke_sessions"]
    ok: bool
    sessions_revoked: int
