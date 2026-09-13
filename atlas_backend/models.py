"""Typed wire shapes for every namespace: returned objects and request bodies.

These mirror the Backend API JSON one-to-one (snake_case, no translation) and
are shared by both the sync and async clients. Bodies with required fields use
the ``Base(TypedDict)`` + ``Body(Base, total=False)`` split so the required keys
stay required and the rest optional — a pattern that works on Python 3.9, which
lacks ``Required``/``NotRequired``.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from ._types import Metadata

# --------------------------------------------------------------------------- #
# Users                                                                        #
# --------------------------------------------------------------------------- #


class User(TypedDict):
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


class EmailAddress(TypedDict):
    object: Literal["email_address"]
    id: str
    email_address: str
    verified: bool
    primary: bool
    created_at: int


class OAuthAccessToken(TypedDict):
    object: Literal["oauth_access_token"]
    provider: str
    token: str
    expires_at: int | None
    scopes: list[str]
    refreshed: bool


class _CreateUserRequired(TypedDict):
    email_address: str


class CreateUserBody(_CreateUserRequired, total=False):
    password: str
    first_name: str
    last_name: str
    email_verified: bool
    public_metadata: Metadata
    private_metadata: Metadata
    unsafe_metadata: Metadata


class UpdateUserBody(TypedDict, total=False):
    first_name: str
    last_name: str
    public_metadata: Metadata
    private_metadata: Metadata


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


class OrganizationPolicyPatch(TypedDict, total=False):
    requireMfa: bool
    ssoRequired: bool
    sessionIdleOverrideMs: int | None


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


class Session(TypedDict):
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


class _CreateWebhookEndpointRequired(TypedDict):
    url: str


class CreateWebhookEndpointBody(_CreateWebhookEndpointRequired, total=False):
    enabled_events: list[str]


# --------------------------------------------------------------------------- #
# OAuth clients                                                                #
# --------------------------------------------------------------------------- #

TokenAuthMethod = Literal["client_secret_basic", "client_secret_post", "none"]


class OAuthClient(TypedDict):
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


class UpdateOAuthClientBody(TypedDict, total=False):
    name: str
    redirect_uris: list[str]
    allowed_scopes: list[str]
    token_endpoint_auth_method: TokenAuthMethod
    logo_url: str | None
    first_party: bool


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
    signing_alg: str


class UpdateResourceServerBody(TypedDict, total=False):
    name: str
    scopes: list[Any]
    token_ttl_seconds: int
    signing_alg: str
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


class _CreateDomainRequired(TypedDict):
    host: str


class CreateDomainBody(_CreateDomainRequired, total=False):
    role: Literal["fapi", "accounts"]


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
