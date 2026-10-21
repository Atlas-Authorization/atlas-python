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


class User(_UserRequired, total=False):
    #: Strictly increases with every change to the user; webhook payloads carry the same
    #: value. Apply an update only if its version is higher than the one you hold.
    version: int


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


class UpdateUserBody(TypedDict, total=False):
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


class WebhookEndpoint(TypedDict):
    object: Literal["webhook_endpoint"]
    id: str
    url: str
    enabled_events: list[str]
    active: bool
    disabled_at: int | None
    created_at: int


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


class OAuthClient(_OAuthClientRequired, total=False):
    #: After a rotation with overlap: when the previous secret stops working (epoch ms).
    #: ``None`` when only the current secret is accepted.
    previous_secret_expires_at: int | None
    #: First-party only. When ``True``, ``/oauth2/logout`` with this client's
    #: ``client_id`` and an exactly registered ``post_logout_redirect_uri`` ends the
    #: session and redirects straight back (with ``state``), skipping the
    #: confirmation page. ``False`` by default.
    skip_logout_confirmation: bool


class RotateOAuthClientSecretBody(TypedDict, total=False):
    #: How long the previous secret keeps working, in seconds. Default 86400 (24 hours);
    #: 0 revokes it now; at most 604800 (7 days).
    overlap_seconds: int


class _OAuthClientSecretRotationRequired(_OAuthClientRequired):
    #: The new client secret. Returned exactly once.
    client_secret: str
    #: The overlap applied, in seconds.
    overlap_seconds: int
    #: When the previous secret stops working (epoch ms), or ``None`` when it already has.
    previous_secret_expires_at: int | None


class OAuthClientSecretRotation(_OAuthClientSecretRotationRequired, total=False):
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


class _CreateGrantRequired(TypedDict):
    resource_server_id: str


class CreateGrantBody(_CreateGrantRequired, total=False):
    scopes: list[str]


# --------------------------------------------------------------------------- #
# Resource servers                                                             #
# --------------------------------------------------------------------------- #


class ResourceServer(TypedDict):
    object: Literal["resource_server"]
    id: str
    identifier: str
    name: str
    scopes: list[dict[str, Any]]
    token_ttl_seconds: int
    signing_alg: str
    created_at: int
    updated_at: int


class _CreateResourceServerRequired(TypedDict):
    identifier: str
    name: str


class CreateResourceServerBody(_CreateResourceServerRequired, total=False):
    scopes: list[Any]
    token_ttl_seconds: int


class UpdateResourceServerBody(TypedDict, total=False):
    name: str
    scopes: list[Any]
    token_ttl_seconds: int
    identifier: str


# --------------------------------------------------------------------------- #
# SSO connections                                                              #
# --------------------------------------------------------------------------- #


class ClaimRoleMapping(TypedDict):
    claim: str
    value: str
    roleKey: str


class SsoConnection(TypedDict):
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


class SamlMetadata(TypedDict):
    object: Literal["sso_saml_metadata"]
    sp_entity_id: str
    acs_url: str
    metadata_xml: str


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


#: PATCH accepts everything create does except ``type``, which is immutable.
UpdateSsoConnectionBody = CreateSsoConnectionBody


# --------------------------------------------------------------------------- #
# SCIM tokens                                                                  #
# --------------------------------------------------------------------------- #


class ScimToken(TypedDict):
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


class _CreateScimTokenRequired(TypedDict):
    organization_id: str


class CreateScimTokenBody(_CreateScimTokenRequired, total=False):
    name: str
    connection_id: str


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


class AttackProtection(TypedDict):
    object: Literal["attack_protection"]
    brute_force: dict[str, Any]
    breached_password: dict[str, Any]
    suspicious_ip: dict[str, Any]
    captcha: dict[str, Any]


class UpdateAttackProtectionBody(TypedDict, total=False):
    brute_force: dict[str, Any]
    breached_password: dict[str, Any]


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


class AtlasIdApp(_AtlasIdAppRequired, total=False):
    """A Sign in with Atlas app (an OpenID Connect client on https://atlasauth.net)."""

    logo_url: str | None
    homepage_url: str | None
    branding: AtlasIdAppBranding
    secret_prefix: str | None
    managed_by_instance_id: str | None
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


class ApiKeyCreate(_ApiKeyCreateRequired, total=False):
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


class ApiKeyVerificationVariant1(TypedDict):
    object: Literal["api_key_verification"]
    valid: Literal[False]


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


class UpdateApiKeyBody(TypedDict, total=False):
    name: str | None
    claims: dict[str, Any]
    expires_at: float | None
    scopes: list[str]
    constraints: dict[str, Any]
    max_token_lifetime_seconds: float | None
    #: Replace the spend caps; ``None`` clears them (counters are kept).
    limits: list[ApiKeyLimit] | None


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


class Subscription(TypedDict):
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


class RecordUsageBody(TypedDict, total=False):
    subject_type: str
    subject_id: str
    quantity: float
    idempotency_key: str


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


class MachineWithSecret(_MachineWithSecretRequired, total=False):
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


class PlatformAppWithSecret(_PlatformAppWithSecretRequired, total=False):
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


class AppSecret(TypedDict):
    object: Literal["app_secret"]
    id: str
    secret: str
    note: str


class RotatePlatformAppSecretBody(TypedDict, total=False):
    overlap_seconds: float


class _PlatformAppRotateSecretResultRequired(TypedDict):
    object: Literal["app_secret"]
    app_id: str
    secret: str
    overlap_seconds: int
    note: str


class PlatformAppRotateSecretResult(_PlatformAppRotateSecretResultRequired, total=False):
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


class RateLimitPolicy(_RateLimitPolicyRequired, total=False):
    ldap_per_ip_per_min: int
    ldap_per_user_per_min: int


class UpdateRateLimitPolicyBody(TypedDict, total=False):
    fapi_create_per_min: Any
    fapi_verify_per_min: Any
    bapi_per_min: Any
    ldap_per_ip_per_min: Any
    ldap_per_user_per_min: Any


class CreateRedirectUrlBody(TypedDict, total=False):
    url: str


class RedirectUrl(TypedDict):
    object: Literal["redirect_url"]
    id: str
    url: str
    #: Created (epoch ms).
    created_at: int


class RiskBasedMfa(TypedDict):
    object: Literal["risk_based_mfa"]
    enabled: bool
    step_up_threshold: float
    on_high_risk_no_factor: str
    weights: dict[str, Any]
    signals: dict[str, Any]


class UpdateRiskBasedMfaBody(TypedDict, total=False):
    enabled: Any
    step_up_threshold: Any
    on_high_risk_no_factor: Any
    weights: Any
    signals: Any


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


class CreateUserImportBody(TypedDict, total=False):
    users: list[dict[str, Any]]
    upsert: bool
    #: Whether the import may notify the imported users. ``False`` (the default) sends nothing.
    notify: bool


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


class WebhookDeliveryAttempt(TypedDict):
    object: Literal["webhook_delivery"]
    id: str
    event_id: str
    status: str
    note: str


class WebhookSecret(TypedDict):
    object: Literal["webhook_secret"]
    #: The current whsec_ signing secret.
    secret: str


class _WebhookSecretRotationRequired(TypedDict):
    object: Literal["webhook_secret"]
    secret: str


class WebhookSecretRotation(_WebhookSecretRotationRequired, total=False):
    warning: str


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
