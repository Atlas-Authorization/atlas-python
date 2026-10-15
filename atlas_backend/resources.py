"""Synchronous resource namespaces — the method↔endpoint map for the BAPI.

Each class wraps the shared :class:`_SyncTransport` and turns a call into a
single request naming a method, a path, and its shapes. The surface mirrors the
official TypeScript SDK (``@atlas/backend``) namespace-for-namespace.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Literal

from . import models as m
from ._transport import _SyncTransport
from ._types import JSON, CursorPage, DeletedObject, ListPage


def _q(**kwargs: Any) -> dict[str, Any]:
    """Build a query mapping, dropping keys whose value is ``None``."""
    return {k: v for k, v in kwargs.items() if v is not None}


def _csv(value: str | Sequence[str] | None) -> str | None:
    """Join a list filter into the comma-separated form the API reads."""
    if value is None or isinstance(value, str):
        return value
    return ",".join(value)


def _json(value: dict[str, Any] | None) -> str | None:
    """Encode an object-valued query filter as compact JSON."""
    return None if value is None else json.dumps(value, separators=(",", ":"))


def _sniff_image_type(data: bytes) -> str:
    """Infer an upload's Content-Type from its magic bytes (PNG, JPEG, GIF, WebP)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError(
        "Could not tell the image type from its bytes; pass content_type= "
        "(image/png, image/jpeg, image/gif or image/webp)."
    )


class Users:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.identities = _UserIdentities(transport)
        self.phone_numbers = _UserPhoneNumbers(transport)
        self.consents = _UserConsents(transport)
        self.deletion = _UserDeletion(transport)
        self.directives = _UserDirectives(transport)
        self.approval_requests = _UserApprovalRequests(transport)
        self.grants = _UserGrants(transport)
        self.erasure = _UserErasure(transport)
        self.notification_preferences = _UserNotificationPreferences(transport)

    def list(self, *, limit: int | None = None, starting_after: str | None = None) -> CursorPage:
        return self._t.request(
            method="GET",
            path="/v1/users",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def get(self, user_id: str, *, include_deleted: bool | None = None) -> m.User:
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}",
            query=_q(include_deleted=include_deleted),
        )

    def create(self, body: m.CreateUserBody, *, idempotency_key: str | None = None) -> m.User:
        return self._t.request(
            method="POST", path="/v1/users", body=body, idempotency_key=idempotency_key
        )

    def update(self, user_id: str, body: m.UpdateUserBody) -> m.User:
        return self._t.request(method="PATCH", path=f"/v1/users/{user_id}", body=body)

    def replace_metadata(self, user_id: str, body: m.ReplaceUserMetadataBody) -> m.User:
        return self._t.request(method="PUT", path=f"/v1/users/{user_id}/metadata", body=body)

    def ban(
        self,
        user_id: str,
        *,
        reason: str | None = None,
        note: str | None = None,
        idempotency_key: str | None = None,
    ) -> m.User:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/ban",
            body=_q(reason=reason, note=note) or None,
            idempotency_key=idempotency_key,
        )

    def unban(self, user_id: str) -> m.User:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/unban")

    def lock(self, user_id: str, *, duration_in_seconds: int | None = None) -> m.User:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/lock",
            body=_q(duration_in_seconds=duration_in_seconds),
        )

    def unlock(self, user_id: str) -> m.User:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/unlock")

    def delete(
        self,
        user_id: str,
        *,
        audit_actor_ids: Sequence[str] | None = None,
        audit_actor_emails: Sequence[str] | None = None,
        idempotency_key: str | None = None,
    ) -> DeletedObject:
        """Delete a user.

        ``audit_actor_ids`` / ``audit_actor_emails`` also scrub this user from the
        actor fields of your custom audit events.
        """
        body = _q(
            audit_actor_ids=list(audit_actor_ids) if audit_actor_ids is not None else None,
            audit_actor_emails=(
                list(audit_actor_emails) if audit_actor_emails is not None else None
            ),
        )
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}",
            body=body or None,
            idempotency_key=idempotency_key,
        )

    def reset_mfa(self, user_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/reset_mfa")

    def delete_mfa_factor(self, user_id: str, factor_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/users/{user_id}/mfa/{factor_id}")

    def list_sessions(self, user_id: str) -> ListPage:
        """List a user's sessions. Each ``data`` item is a :class:`~atlas_backend.models.Session`
        (with ``idle_expires_at``, ``last_active_organization_id`` and ``impersonated_by``).
        """
        return self._t.request(method="GET", path=f"/v1/users/{user_id}/sessions")

    def revoke_sessions(
        self,
        user_id: str,
        *,
        all: bool | None = None,
        revoke_grants: bool | None = None,
    ) -> JSON:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/sessions/revoke",
            body=_q(all=all, revoke_grants=revoke_grants) or None,
        )

    def add_email(self, user_id: str, email_address: str) -> m.EmailAddress:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses",
            body={"email_address": email_address},
        )

    def verify_email(self, user_id: str, email_id: str) -> m.EmailAddress:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses/{email_id}/verify",
        )

    def set_primary_email(self, user_id: str, email_id: str) -> m.EmailAddress:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses/{email_id}/primary",
        )

    def get_oauth_access_token(self, user_id: str, provider: str) -> m.OAuthAccessToken:
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/oauth_access_tokens/{provider}",
        )

    def get_by_emails(self, body: m.UsersByEmailsBody) -> ListPage:
        """Resolve a batch of email addresses to user ids in one call."""
        return self._t.request(
            method="POST",
            path="/v1/users/by_emails",
            body=body,
        )

    def connect_external_account(
        self, user_id: str, body: m.ConnectExternalAccountBody | None = None
    ) -> m.UserConnectExternalAccountResult:
        """Backend-initiated connect: start an OAuth flow that links a NEW provider identity to
        this user (the caller supplies the user id).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/external_accounts/connect",
            body=body,
        )

    def list_organization_memberships(
        self, user_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        """List the organizations a user belongs to with each membership's role, the org's
        resolved plan, and the join time.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/organization_memberships",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def delete_passkey(
        self, user_id: str, passkey_id: str, *, idempotency_key: str | None = None
    ) -> DeletedObject:
        """Remove one of a user’s passkeys."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/passkeys/{passkey_id}",
            idempotency_key=idempotency_key,
        )

    def set_password(
        self, user_id: str, body: m.SetUserPasswordBody, *, idempotency_key: str | None = None
    ) -> m.User:
        """Set (reset) a user's password from the backend."""
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/password",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_profile_image(self, user_id: str, *, idempotency_key: str | None = None) -> m.User:
        """Clear a user’s profile image."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/profile_image",
            idempotency_key=idempotency_key,
        )

    def record_progression_event(
        self,
        user_id: str,
        body: m.ProgressionEventBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.ProgressionEvent:
        """Append an idempotent progression event (XP / level / state) for a user, scoped to
        the calling source.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/progression/events",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_resolved(self, user_id: str) -> m.ResolvedUser:
        """Resolve a user to a FLAT identity in one call: the real primary email (never the
        @no-email.invalid placeholder), email_verified, name, image_url, and the linked
        provider identities (provider + provider_user_id).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/resolved",
        )

    def sign_in_history(
        self, user_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        """A user's successful sign-ins, newest first, keyset-paginated."""
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/sign_in_history",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def get_state(self, user_id: str) -> m.UserState:
        """Read a user's portable state — progression, tier, flair, entitlements, directives
        and roles.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/state",
        )


class _OrgMemberships:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str, *, limit: int | None = None, offset: int | None = None) -> JSON:
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/memberships",
            query=_q(limit=limit, offset=offset),
        )

    def add(
        self,
        org_id: str,
        body: m.AddMembershipBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/memberships",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(self, org_id: str, user_id: str, role: str) -> JSON:
        return self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/memberships/{user_id}",
            body={"role": role},
        )

    def remove(self, org_id: str, user_id: str) -> JSON:
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/memberships/{user_id}",
        )


class _OrgInvitations:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str) -> ListPage:
        return self._t.request(method="GET", path=f"/v1/organizations/{org_id}/invitations")

    def create(
        self,
        org_id: str,
        body: m.CreateOrgInvitationBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/invitations",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, org_id: str, invitation_id: str) -> JSON:
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/invitations/{invitation_id}/revoke",
        )


class _OrgDomains:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/organizations/{org_id}/domains")

    def create(
        self,
        org_id: str,
        body: m.CreateOrgDomainBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgDomain:
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/domains",
            body=body,
            idempotency_key=idempotency_key,
        )

    def verify(self, org_id: str, domain_id: str) -> m.OrgDomain:
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/domains/{domain_id}/verify",
        )

    def delete(self, org_id: str, domain_id: str) -> JSON:
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/domains/{domain_id}",
        )


class _OrgGroupRoles:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def grant(self, org_id: str, group_id: str, role_id: str) -> JSON:
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/groups/{group_id}/roles/{role_id}",
        )

    def revoke(self, org_id: str, group_id: str, role_id: str) -> JSON:
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/groups/{group_id}/roles/{role_id}",
        )


class Organizations:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.memberships = _OrgMemberships(transport)
        self.invitations = _OrgInvitations(transport)
        self.domains = _OrgDomains(transport)
        self.group_roles = _OrgGroupRoles(transport)
        self.audit_streams = _OrgAuditStreams(transport)
        self.design = _OrgDesign(transport)
        self.settings = _OrgSettings(transport)
        self.end_users = _OrgEndUsers(transport)
        self.reader_domain = _OrgReaderDomain(transport)
        self.branding = _OrgBranding(transport)

    def list(self, *, limit: int | None = None, starting_after: str | None = None) -> CursorPage:
        return self._t.request(
            method="GET",
            path="/v1/organizations",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def get(self, org_id: str) -> m.Organization:
        return self._t.request(method="GET", path=f"/v1/organizations/{org_id}")

    def create(
        self,
        body: m.CreateOrganizationBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.Organization:
        return self._t.request(
            method="POST",
            path="/v1/organizations",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(self, org_id: str, body: m.UpdateOrganizationBody) -> m.Organization:
        return self._t.request(method="PATCH", path=f"/v1/organizations/{org_id}", body=body)

    def delete(self, org_id: str) -> DeletedObject:
        return self._t.request(method="DELETE", path=f"/v1/organizations/{org_id}")

    def update_metadata(
        self, org_id: str, body: m.ReplaceOrganizationMetadataBody
    ) -> m.Organization:
        return self._t.request(method="PUT", path=f"/v1/organizations/{org_id}/metadata", body=body)

    def update_policy(self, org_id: str, body: m.OrganizationPolicyPatch | dict[str, Any]) -> JSON:
        """Patch an organization's policy (camelCase keys; ``None`` clears an override)."""
        return self._t.request(method="PATCH", path=f"/v1/organizations/{org_id}/policy", body=body)

    def get_entitlements(self, org_id: str) -> m.OrganizationEntitlements:
        """The organization’s effective entitlement — resolved plan, feature keys and numeric
        limits, with sales-led overrides applied and plan limits merged.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/entitlements",
        )

    def get_hierarchy(self, org_id: str) -> m.OrganizationHierarchy:
        """The organization’s ancestor chain and direct children in the B2B2B hierarchy."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/hierarchy",
        )

    def set_parent(
        self, org_id: str, body: m.SetOrganizationParentBody | None = None
    ) -> m.Organization:
        """Set or clear (null) an organization’s parent in the B2B2B hierarchy; refuses a
        cycle.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/parent",
            body=body,
        )


class Sessions:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, user_id: str) -> ListPage:
        """List a user's sessions. Each ``data`` item is a
        :class:`~atlas_backend.models.Session`.
        """
        return self._t.request(method="GET", path="/v1/sessions", query={"user_id": user_id})

    def get(self, session_id: str) -> m.Session:
        return self._t.request(method="GET", path=f"/v1/sessions/{session_id}")

    def revoke(self, session_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/sessions/{session_id}/revoke")

    def create(self, body: m.CreateSessionBody) -> m.SessionCreated:
        """Establish a session for a user in one call — returns jwt + refresh_token, audited as
        a first-party sign-in (not impersonation unless actor.sub is set).
        """
        return self._t.request(
            method="POST",
            path="/v1/sessions",
            body=body,
        )

    def touch(self, session_id: str) -> m.TouchedSession:
        """Keep a session alive from your backend: slides its inactivity window as if the
        user had just loaded a page. Never extends past the absolute expiry and never
        revives an ended session (409 SESSION_REVOKED / SESSION_IDLE_EXPIRED /
        SESSION_EXPIRED). At most one effective write per minute, so calling it on every
        request is safe.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/sessions/{session_id}/touch",
        )

    def create_token(self, session_id: str, template: str) -> m.SessionToken:
        """Mint a named JWT-template token for a session."""
        return self._t.request(
            method="POST",
            path=f"/v1/sessions/{session_id}/tokens/{template}",
        )


class Invitations:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, limit: int | None = None, starting_after: str | None = None) -> CursorPage:
        return self._t.request(
            method="GET",
            path="/v1/invitations",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def create(
        self,
        body: m.CreateInvitationBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.Invitation:
        return self._t.request(
            method="POST",
            path="/v1/invitations",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, invitation_id: str) -> m.Invitation:
        return self._t.request(method="POST", path=f"/v1/invitations/{invitation_id}/revoke")

    def bulk_create(self, body: m.BulkCreateInvitationsBody | None = None) -> ListPage:
        """Bulk-create instance invitations (≤100)."""
        return self._t.request(
            method="POST",
            path="/v1/invitations/bulk",
            body=body,
        )


class Roles:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/roles")

    def create(self, body: m.CreateRoleBody, *, idempotency_key: str | None = None) -> m.Role:
        return self._t.request(
            method="POST", path="/v1/roles", body=body, idempotency_key=idempotency_key
        )

    def update(self, role_id: str, body: m.UpdateRoleBody) -> m.Role:
        return self._t.request(method="PATCH", path=f"/v1/roles/{role_id}", body=body)

    def set_permissions(self, role_id: str, permissions: Sequence[str]) -> JSON:
        return self._t.request(
            method="PUT",
            path=f"/v1/roles/{role_id}/permissions",
            body={"permissions": permissions},
        )

    def delete(self, role_id: str, *, reassign_to: str | None = None) -> JSON:
        """Delete a role; ``reassign_to`` moves its members to another role first."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/roles/{role_id}",
            query=_q(reassign_to=reassign_to),
        )


class Permissions:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/permissions")

    def create(
        self, body: m.CreatePermissionBody, *, idempotency_key: str | None = None
    ) -> m.Permission:
        return self._t.request(
            method="POST",
            path="/v1/permissions",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, permission_id: str) -> DeletedObject:
        """Delete a permission; it is removed from every role that held it."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/permissions/{permission_id}",
        )

    def update(
        self, permission_id: str, body: m.UpdatePermissionBody | None = None
    ) -> m.Permission:
        """Update a permission’s description or metadata."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/permissions/{permission_id}",
            body=body,
        )


class _WebhookEndpoints:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> JSON:
        return self._t.request(method="GET", path="/v1/webhook_endpoints")

    def create(
        self,
        body: m.CreateWebhookEndpointBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return self._t.request(
            method="POST",
            path="/v1/webhook_endpoints",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, endpoint_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/webhook_endpoints/{endpoint_id}")

    def list_deliveries(self, endpoint_id: str, *, limit: int | None = None) -> ListPage:
        """List an endpoint's recent deliveries, newest first (``limit`` 1-100)."""
        return self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries",
            query=_q(limit=limit),
        )

    def update(
        self, endpoint_id: str, body: m.UpdateWebhookEndpointBody | None = None
    ) -> m.WebhookEndpoint:
        """Update an endpoint’s url, enabled_events, or active flag in place."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/webhook_endpoints/{endpoint_id}",
            body=body,
        )

    def redeliver(self, endpoint_id: str, delivery_id: str) -> m.WebhookDeliveryAttempt:
        """Manually redeliver a past event as a fresh attempt."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries/{delivery_id}/redeliver",
        )

    def reveal_secret(self, endpoint_id: str) -> m.WebhookSecret:
        """Show the endpoint's current signing secret again (for a verifier that lost it)."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/reveal_secret",
        )

    def rotate_secret(self, endpoint_id: str) -> m.WebhookSecretRotation:
        """Rotate the endpoint signing secret."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/rotate_secret",
        )

    def test(self, endpoint_id: str) -> m.WebhookDeliveryAttempt:
        """Send a synthetic webhook.test event to this endpoint only."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/test",
        )


class Webhooks:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.endpoints = _WebhookEndpoints(transport)

    def deliveries(self, endpoint_id: str, *, limit: int | None = None) -> JSON:
        """List an endpoint's deliveries. Same as ``endpoints.list_deliveries``."""
        return self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries",
            query=_q(limit=limit),
        )


class _OAuthClientGrants:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, client_id: str) -> ListPage:
        return self._t.request(method="GET", path=f"/v1/oauth_clients/{client_id}/grants")

    def create(self, client_id: str, body: m.CreateGrantBody) -> m.ClientGrant:
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{client_id}/grants",
            body=body,
        )

    def delete(self, client_id: str, grant_id: str) -> JSON:
        return self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{client_id}/grants/{grant_id}",
        )


class OAuthClients:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.grants = _OAuthClientGrants(transport)

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/oauth_clients")

    def get(self, client_id: str) -> m.OAuthClient:
        return self._t.request(method="GET", path=f"/v1/oauth_clients/{client_id}")

    def create(
        self,
        body: m.CreateOAuthClientBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return self._t.request(
            method="POST",
            path="/v1/oauth_clients",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(self, client_id: str, body: m.UpdateOAuthClientBody) -> m.OAuthClient:
        return self._t.request(method="PATCH", path=f"/v1/oauth_clients/{client_id}", body=body)

    def rotate_secret(self, client_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/oauth_clients/{client_id}/rotate_secret")

    def delete(self, client_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/oauth_clients/{client_id}")

    def import_clients(
        self, body: m.ImportOAuthClientsBody, *, idempotency_key: str | None = None
    ) -> ListPage:
        """Bulk-import OAuth clients for a migration, optionally with a pre-hashed client
        secret.
        """
        return self._t.request(
            method="POST",
            path="/v1/oauth_clients/import",
            body=body,
            idempotency_key=idempotency_key,
        )


class ResourceServers:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/resource_servers")

    def get(self, server_id: str) -> m.ResourceServer:
        return self._t.request(method="GET", path=f"/v1/resource_servers/{server_id}")

    def create(self, body: m.CreateResourceServerBody) -> m.ResourceServer:
        return self._t.request(method="POST", path="/v1/resource_servers", body=body)

    def update(self, server_id: str, body: m.UpdateResourceServerBody) -> m.ResourceServer:
        return self._t.request(method="PATCH", path=f"/v1/resource_servers/{server_id}", body=body)

    def delete(self, server_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/resource_servers/{server_id}")


class SsoConnections:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, organization_id: str | None = None) -> ListPage:
        return self._t.request(
            method="GET",
            path="/v1/sso_connections",
            query=_q(organization_id=organization_id),
        )

    def get(self, connection_id: str) -> m.SsoConnection:
        return self._t.request(method="GET", path=f"/v1/sso_connections/{connection_id}")

    def create(
        self,
        body: m.CreateSsoConnectionBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.SsoConnection:
        return self._t.request(
            method="POST",
            path="/v1/sso_connections",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(self, connection_id: str, body: m.UpdateSsoConnectionBody) -> m.SsoConnection:
        return self._t.request(
            method="PATCH", path=f"/v1/sso_connections/{connection_id}", body=body
        )

    def delete(self, connection_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/sso_connections/{connection_id}")

    def saml_metadata(self, connection_id: str) -> m.SamlMetadata:
        return self._t.request(
            method="GET",
            path=f"/v1/sso_connections/{connection_id}/saml_metadata",
        )


class ScimTokens:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, organization_id: str | None = None) -> ListPage:
        return self._t.request(
            method="GET",
            path="/v1/scim_tokens",
            query=_q(organization_id=organization_id),
        )

    def create(self, body: m.CreateScimTokenBody, *, idempotency_key: str | None = None) -> JSON:
        return self._t.request(
            method="POST",
            path="/v1/scim_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, token_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/scim_tokens/{token_id}/revoke")


class Domains:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> JSON:
        return self._t.request(method="GET", path="/v1/domains")

    def create(self, body: m.CreateDomainBody, *, idempotency_key: str | None = None) -> JSON:
        return self._t.request(
            method="POST",
            path="/v1/domains",
            body=body,
            idempotency_key=idempotency_key,
        )

    def verify(self, domain_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/domains/{domain_id}/verify")

    def delete(self, domain_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/domains/{domain_id}")


class Waitlist:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        status: str | None = None,
        query: str | None = None,
    ) -> JSON:
        return self._t.request(
            method="GET",
            path="/v1/waitlist_entries",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                status=status,
                query=query,
            ),
        )

    def decide(self, entry_id: str, body: m.DecideWaitlistBody) -> m.WaitlistEntry:
        return self._t.request(
            method="POST",
            path=f"/v1/waitlist_entries/{entry_id}/decide",
            body=body,
        )

    def create(self, body: m.CreateWaitlistEntryBody | None = None) -> m.WaitlistEntry:
        """Admin-create a waitlist entry (idempotent on address)."""
        return self._t.request(
            method="POST",
            path="/v1/waitlist_entries",
            body=body,
        )

    def bulk_create(self, body: m.BulkCreateWaitlistEntriesBody | None = None) -> ListPage:
        """Bulk-create waitlist entries (≤100 addresses); per-entry errors returned."""
        return self._t.request(
            method="POST",
            path="/v1/waitlist_entries/bulk",
            body=body,
        )

    def delete(self, entry_id: str) -> DeletedObject:
        """Delete a waitlist entry."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/waitlist_entries/{entry_id}",
        )


class _Restriction:
    """Allowlist and blocklist share an identical route shape."""

    def __init__(self, transport: _SyncTransport, path: str) -> None:
        self._t = transport
        self._path = path

    def list(self) -> JSON:
        return self._t.request(method="GET", path=self._path)

    def add(self, identifier: str) -> JSON:
        return self._t.request(method="POST", path=self._path, body={"identifier": identifier})

    def remove(self, identifier_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"{self._path}/{identifier_id}")


class AttackProtection:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.AttackProtection:
        return self._t.request(method="GET", path="/v1/attack_protection")

    def update(self, body: m.UpdateAttackProtectionBody) -> m.AttackProtection:
        return self._t.request(method="PATCH", path="/v1/attack_protection", body=body)


class ActorTokens:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateActorTokenBody, *, idempotency_key: str | None = None
    ) -> m.ActorToken:
        return self._t.request(
            method="POST",
            path="/v1/actor_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, token_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/actor_tokens/{token_id}/revoke")


class SignInTokens:
    """The ``/v1/sign_in_tokens`` resource.

    .. deprecated::
        ``POST /v1/sign_in_tokens`` is deprecated (Sunset 2026-04-01). Use
        ``Sessions.create`` (``POST /v1/sessions``), which mints a real
        redeemable session in one call.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateSignInTokenBody, *, idempotency_key: str | None = None
    ) -> m.SignInToken:
        return self._t.request(
            method="POST",
            path="/v1/sign_in_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, token_id: str) -> m.SignInTokenRevokeResult:
        """DEPRECATED (Sunset 2027-04-01) — revoke an unused sign-in token before its 60s
        window elapses.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/sign_in_tokens/{token_id}/revoke",
        )


class AuditLogs:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        actor_id: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> CursorPage:
        return self._t.request(
            method="GET",
            path="/v1/audit_logs",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                actor_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
            ),
        )


class JwtTemplates:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/jwt_templates")

    def get(self, name: str) -> m.JwtTemplate:
        return self._t.request(method="GET", path=f"/v1/jwt_templates/{name}")

    def create(self, body: m.CreateJwtTemplateBody) -> m.JwtTemplate:
        return self._t.request(method="POST", path="/v1/jwt_templates", body=body)

    def update(self, name: str, claims: dict[str, str]) -> m.JwtTemplate:
        return self._t.request(
            method="PATCH",
            path=f"/v1/jwt_templates/{name}",
            body={"claims": claims},
        )

    def delete(self, name: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/jwt_templates/{name}")


class _UserIdentities:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, user_id: str) -> ListPage:
        """List a user's linked identities: their Atlas email/password identity plus each
        linked external/OAuth provider account.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/identities",
        )

    def link(
        self,
        user_id: str,
        body: m.LinkIdentityBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> ListPage:
        """Merge a secondary user into this primary: moves the secondary's provider accounts
        and verified identifiers over (skipping collisions), re-points org memberships
        without escalating role, revokes the secondary's...
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/identities",
            body=body,
            idempotency_key=idempotency_key,
        )

    def unlink_provider(
        self, user_id: str, provider: str, *, idempotency_key: str | None = None
    ) -> m.IdentityUnlinkProviderResult:
        """Hard-remove a provider identity from a user (undo a mis-import)."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/identities/by-provider/{provider}",
            idempotency_key=idempotency_key,
        )

    def import_identity(
        self,
        user_id: str,
        body: m.ImportIdentityBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.Identity:
        """Import a KNOWN provider identity (migration) without an interactive OAuth flow —
        link { provider, provider_user_id, email_address?, verified?
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/identities/import",
            body=body,
            idempotency_key=idempotency_key,
        )

    def unlink(
        self, user_id: str, identity_id: str, *, idempotency_key: str | None = None
    ) -> m.IdentityUnlinkResult:
        """Unlink a provider identity, extracting it into a new standalone user."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/identities/{identity_id}",
            idempotency_key=idempotency_key,
        )


class _UserPhoneNumbers:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def add(
        self,
        user_id: str,
        body: m.AddPhoneNumberBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PhoneNumber:
        """Add a phone number to a user."""
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/phone_numbers",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self, user_id: str, phone_number_id: str, *, idempotency_key: str | None = None
    ) -> DeletedObject:
        """Remove a phone number from a user."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/phone_numbers/{phone_number_id}",
            idempotency_key=idempotency_key,
        )

    def verify(
        self, user_id: str, phone_number_id: str, *, idempotency_key: str | None = None
    ) -> m.PhoneNumber:
        """Mark a phone number verified on the backend authority."""
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/phone_numbers/{phone_number_id}/verify",
            idempotency_key=idempotency_key,
        )


class _UserConsents:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def record(
        self,
        user_id: str,
        body: m.RecordConsentBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.Consent:
        """Record a versioned consent grant (or withdrawal, `status: "withdrawn"`) for a user."""
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/consents",
            body=body,
            idempotency_key=idempotency_key,
        )

    def list(self, user_id: str) -> ListPage:
        """List a user's recorded consents with their versions and timestamps."""
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/consents",
        )


class _UserDeletion:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def schedule(
        self,
        user_id: str,
        body: m.ScheduleUserDeletionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.User:
        """Schedule a GRACEFUL deletion of a user: opens a cancellation grace window
        (grace_seconds, default the instance erasure grace of 7 days) and emits
        user.deletion_scheduled.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/deletion",
            body=body,
            idempotency_key=idempotency_key,
        )

    def cancel(self, user_id: str, *, idempotency_key: str | None = None) -> m.User:
        """Cancel a scheduled deletion inside its grace window, aborting the purge so the
        account is NOT erased; emits user.deletion_canceled.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/deletion/cancel",
            idempotency_key=idempotency_key,
        )

    def finalize(self, user_id: str, *, idempotency_key: str | None = None) -> DeletedObject:
        """Finalize a scheduled deletion whose grace window has lapsed — the idempotent purge
        trigger the worker calls on schedule (a cron/operator may too).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/deletion/finalize",
            idempotency_key=idempotency_key,
        )


class _UserDirectives:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def set(
        self,
        user_id: str,
        body: m.SetUserDirectiveBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.Directive:
        """Impose a cross-property directive on a user (e.g. suspended_until / read_only /
        forced_logout).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/directives",
            body=body,
            idempotency_key=idempotency_key,
        )

    def lift(self, user_id: str) -> m.DirectiveLiftResult:
        """Lift a previously imposed directive from a user."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/directives",
        )


class _UserApprovalRequests:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, user_id: str, body: m.CreateApprovalRequestBody) -> m.ApprovalRequestCreated:
        """Request a transaction approval from a user: push a number-matching "approve this
        action" prompt (carrying a human-readable description and optional context) to the
        user's registered push devices.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/approval_requests",
            body=body,
        )

    def get(self, user_id: str, approval_id: str) -> m.ApprovalRequest:
        """Poll a transaction-approval request: pending | approved | denied | expired, with the
        approving device and resolution timestamp.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/approval_requests/{approval_id}",
        )


class _UserGrants:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, user_id: str) -> ListPage:
        """List the OAuth clients a user has authorized, with the granted scopes and grant
        time.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/grants",
        )

    def revoke_all(
        self, user_id: str, *, idempotency_key: str | None = None
    ) -> m.UserGrantRevokeAllResult:
        """Revoke every consent grant a user holds and cascade-revoke all associated tokens
        through the standard revocation path.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/grants",
            idempotency_key=idempotency_key,
        )


class _UserErasure:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def acknowledge(
        self, user_id: str, body: m.CreateErasureAckBody, *, idempotency_key: str | None = None
    ) -> m.UserErasureAck:
        """An integrating app acknowledges it has purged its copy of the user data during a
        scheduled deletion, identified by source (or the app_id alias), and may contribute a
        JSON payload Atlas folds into the DSAR erasure export.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/erasure_acks",
            body=body,
            idempotency_key=idempotency_key,
        )

    def export(self, user_id: str) -> m.UserErasureExport:
        """The DSAR erasure export: Atlas's own data about the subject (the same no-secret
        bundle the self-service export produces) PLUS every app's contributed blob from its
        erasure ack, aggregated into one package.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/erasure_export",
        )


class _UserNotificationPreferences:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, user_id: str) -> m.NotificationPreferences:
        """Read an end-user's security-notification preferences: every category with whether it
        is enabled and whether it is optional (security-critical categories are non-optional
        and always enabled).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/notification_preferences",
        )

    def update(
        self, user_id: str, body: m.UpdateNotificationPreferencesBody
    ) -> m.NotificationPreferences:
        """Change an end-user's security-notification preferences with a { preferences: {
        category: enabled } } patch.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/users/{user_id}/notification_preferences",
            body=body,
        )


class _OrgAuditStreams:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str) -> ListPage:
        """List an organization's registered audit stream destinations."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/audit_streams",
        )

    def create(
        self,
        org_id: str,
        body: m.CreateAuditStreamBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgAuditStream:
        """Register an audit stream destination for one organization: an HTTPS SIEM/collector
        URL plus a shared HMAC signing secret (write-only, stored encrypted, min 16 chars)
        and an optional format hint.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/audit_streams",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, org_id: str, stream_id: str) -> DeletedObject:
        """Delete one of an organization's audit stream destinations."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/audit_streams/{stream_id}",
        )


class _OrgDesign:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, org_id: str) -> m.DesignSettings:
        """Read an organization's design override and the result of layering it over the
        instance design.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/design",
        )

    def replace(self, org_id: str, body: m.ReplaceDesignBody) -> m.DesignSettings:
        """Replace an organization's design override ({ design: AtlasDesign }); { design: {} }
        removes it.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/design",
            body=body,
        )

    def update(self, org_id: str, body: m.UpdateDesignBody) -> m.DesignSettings:
        """Change part of an organization's design override; null removes a setting."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/design",
            body=body,
        )


class _OrgSettings:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, org_id: str) -> m.OrganizationSettings:
        """Fetch one organization's settings values."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/settings",
        )

    def replace(
        self, org_id: str, body: m.OrgSettingsBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettings:
        """Write one organization's settings values."""
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/settings",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(
        self, org_id: str, body: m.OrgSettingsBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettings:
        """Merge a partial object into an organization's settings values (RFC 7396 shallow
        merge): a key set to null is REMOVED, any other value sets/overwrites it, untouched
        keys are preserved — so a single settings key can be...
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/settings",
            body=body,
            idempotency_key=idempotency_key,
        )


class _OrgEndUsers:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        org_id: str,
        *,
        status: Literal["active", "pending", "blocked"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List an organization's end-user (reader) pool — the B2B2C tier of external users
        attached to the org, distinct from its staff members.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/end_users",
            query=_q(status=status, limit=limit, starting_after=starting_after),
        )

    def add(
        self, org_id: str, body: m.AddOrgEndUserBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationEndUser:
        """Attach an instance user to an organization's end-user pool as a reader (the token-
        exchange path).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/end_users",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(
        self, org_id: str, user_id: str, body: m.UpdateOrgEndUserBody
    ) -> m.OrganizationEndUser:
        """Approve (active), gate (pending) or block a reader in an organization end-user pool."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/end_users/{user_id}",
            body=body,
        )

    def remove(self, org_id: str, user_id: str) -> DeletedObject:
        """Remove a reader from an organization's end-user pool."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/end_users/{user_id}",
        )


class _OrgReaderDomain:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, org_id: str) -> ListPage:
        """List the organization's reader domain(s) — the host(s) whose sign-ups join this
        org's end-user pool, with DNS/certificate status.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/reader_domain",
        )

    def set(
        self, org_id: str, body: m.SetReaderDomainBody, *, idempotency_key: str | None = None
    ) -> JSON:
        """Bind a host to this organization's reader pool: a sign-up on it joins the pool."""
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/reader_domain",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, org_id: str) -> DeletedObject:
        """Remove the organization's reader domain binding and drop its edge router."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/reader_domain",
        )


class _OrgBranding:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, org_id: str) -> m.OrganizationBranding:
        """Read an organization's hosted-page branding overlay (display name, logo, primary
        colour, support URL, custom domain).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/branding",
        )

    def set(self, org_id: str, body: m.SetOrgBrandingBody | None = None) -> m.OrganizationBranding:
        """Set an organization's hosted-page branding overlay — a partial merge: a provided
        field overrides the instance brand, null (or empty string) clears it back.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/branding",
            body=body,
        )


class Actions:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List Actions (tenant code that runs at auth-pipeline hooks)."""
        return self._t.request(
            method="GET",
            path="/v1/actions",
        )

    def create(
        self, body: m.CreateActionBody | None = None, *, idempotency_key: str | None = None
    ) -> m.Action:
        """Create an Action for a trigger (post_login, pre_user_registration,
        post_user_registration).
        """
        return self._t.request(
            method="POST",
            path="/v1/actions",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_binding(self, trigger: str) -> m.ActionBindingList:
        """Read the ordered list of Action ids bound to a trigger."""
        return self._t.request(
            method="GET",
            path=f"/v1/actions/bindings/{trigger}",
        )

    def set_binding(
        self, trigger: str, body: m.SetActionBindingBody | None = None
    ) -> m.ActionBindingList:
        """Replace the ordered list of Actions bound to a trigger — the single source of truth
        for what runs, and in what order.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/actions/bindings/{trigger}",
            body=body,
        )

    def get(self, action_id: str) -> m.Action:
        """Read one Action."""
        return self._t.request(
            method="GET",
            path=f"/v1/actions/{action_id}",
        )

    def update(self, action_id: str, body: m.UpdateActionBody | None = None) -> m.Action:
        """Update an Action's name, code, enabled flag, or secrets."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/actions/{action_id}",
            body=body,
        )

    def delete(self, action_id: str) -> DeletedObject:
        """Delete an Action."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/actions/{action_id}",
        )

    def test(self, action_id: str, body: m.TestActionBody | None = None) -> m.ActionTestResult:
        """Dry-run an Action against a sample event in the sandbox and return its
        claims/deny/logs.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/actions/{action_id}/test",
            body=body,
        )


class ApiKeys:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        subject_type: Literal["user", "organization", "machine"] | None = None,
        subject_id: str | None = None,
    ) -> ListPage:
        """List end-user API keys the tenant minted for its users/organizations."""
        return self._t.request(
            method="GET",
            path="/v1/api_keys",
            query=_q(subject_type=subject_type, subject_id=subject_id),
        )

    def create(self, body: m.CreateApiKeyBody | None = None) -> m.ApiKeyCreate:
        """Mint an end-user API key for a user, organization or machine (returns the ak_ secret
        once), OR import an existing key by its SHA-256 hash (hash_algorithm "sha256" or
        "sha256_hex") so it verifies against the original...
        """
        return self._t.request(
            method="POST",
            path="/v1/api_keys",
            body=body,
        )

    def list_revoked(self, *, since: str | int | None = None, limit: int | None = None) -> ListPage:
        """Revocation feed: the keys revoked since a cursor (since=<iso|cursor>), so a resource
        can deny-list revoked key ids while their short-lived delegated tokens are still
        live.
        """
        return self._t.request(
            method="GET",
            path="/v1/api_keys/revoked",
            query=_q(since=since, limit=limit),
        )

    def create_token(self, body: m.CreateApiKeyTokenBody | None = None) -> m.ApiKeyToken:
        """Mint a short-lived, JWKS-signed access JWT (token_use:api_key, jti) whose exp is
        clamped to the smallest of the request, the key expiry and the org ceiling; scopes +
        constraints are embedded so a resource verifies it...
        """
        return self._t.request(
            method="POST",
            path="/v1/api_keys/token",
            body=body,
        )

    def verify(self, body: m.VerifyApiKeyBody | None = None) -> m.ApiKeyVerification:
        """Verify a presented ak_ secret."""
        return self._t.request(
            method="POST",
            path="/v1/api_keys/verify",
            body=body,
        )

    def get(self, key_id: str) -> m.ApiKey:
        """Read one end-user API key by id (prefix + metadata, never the secret)."""
        return self._t.request(
            method="GET",
            path=f"/v1/api_keys/{key_id}",
        )

    def update(self, key_id: str, body: m.UpdateApiKeyBody | None = None) -> m.ApiKey:
        """Update an end-user API key: name, claims, expiry, scopes, constraints, token
        lifetime or spend caps (``limits``; ``None`` clears them).
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/api_keys/{key_id}",
            body=body,
        )

    def record_usage(self, key_id: str, body: m.RecordApiKeyUsageBody) -> m.ApiKeyUsageDebit:
        """Meter usage against a key's spend caps, atomically. A debit that fits every cap
        for its unit is recorded (``allowed`` is ``True``); one that would exceed a cap
        records nothing and returns ``allowed: False`` with ``code: "LIMIT_EXCEEDED"``
        (not an exception). Reusing an ``idempotency_key`` with a different unit or amount
        raises a 409 IDEMPOTENCY_CONFLICT; a revoked or expired key a 409 CONFLICT.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/api_keys/{key_id}/usage",
            body=body,
        )

    def get_usage(self, key_id: str) -> m.ApiKeyUsage:
        """A key's current-window usage: each cap's state plus every unit's counters."""
        return self._t.request(
            method="GET",
            path=f"/v1/api_keys/{key_id}/usage",
        )

    def revoke(self, key_id: str) -> m.ApiKeyRevokeResult:
        """Revoke an end-user API key."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/api_keys/{key_id}",
        )


class AuditEvents:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, body: m.CreateAuditEventBody | None = None) -> m.AuditEvent:
        """Write one of the tenant's OWN custom audit events (actor, action, optional target,
        optional metadata).
        """
        return self._t.request(
            method="POST",
            path="/v1/audit_events",
            body=body,
        )

    def list(
        self,
        *,
        organization_id: str | None = None,
        actor_id: str | Sequence[str] | None = None,
        action: str | Sequence[str] | None = None,
        target_type: str | Sequence[str] | None = None,
        target_id: str | Sequence[str] | None = None,
        from_: str | int | None = None,
        to: str | int | None = None,
        any_of: bool | None = None,
        metadata_key: str | None = None,
        metadata_value: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Query the tenant's custom audit events, filterable by organization_id, actor_id,
        action, target_type, target_id and an occurred-at window (from/to), cursor-paginated
        with limit + starting_after.
        """
        return self._t.request(
            method="GET",
            path="/v1/audit_events",
            query=_q(
                **{
                    "organization_id": organization_id,
                    "actor_id": _csv(actor_id),
                    "action": _csv(action),
                    "target_type": _csv(target_type),
                    "target_id": _csv(target_id),
                    "from": from_,
                    "to": to,
                    "any_of": any_of,
                    "metadata_key": metadata_key,
                    "metadata_value": metadata_value,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    def delete(
        self, *, organization_id: str | None = None, action: str | None = None
    ) -> m.AuditEventDeleteResult:
        """Bulk-delete the instance's custom audit events — a TEST-MODE reset, allowed ONLY on
        a development instance (a production audit trail cannot be bulk-erased: 403).
        """
        return self._t.request(
            method="DELETE",
            path="/v1/audit_events",
            query=_q(organization_id=organization_id, action=action),
        )

    def create_batch(self, body: m.CreateBatchAuditEventBody | None = None) -> ListPage:
        """Write up to 100 custom audit events in one call."""
        return self._t.request(
            method="POST",
            path="/v1/audit_events/batch",
            body=body,
        )

    def export(
        self,
        *,
        format: Literal["jsonl", "csv"] | None = None,
        organization_id: str | None = None,
        actor_id: str | Sequence[str] | None = None,
        action: str | Sequence[str] | None = None,
        target_type: str | Sequence[str] | None = None,
        target_id: str | Sequence[str] | None = None,
        from_: str | int | None = None,
        to: str | int | None = None,
        any_of: bool | None = None,
        metadata_key: str | None = None,
        metadata_value: str | None = None,
        starting_after: str | None = None,
    ) -> str:
        """Bulk-export every matching custom audit event in one streamed response —
        `format=jsonl` (newline-delimited JSON, default) or `format=csv`.
        """
        return self._t.request(
            method="GET",
            path="/v1/audit_events/export",
            query=_q(
                **{
                    "format": format,
                    "organization_id": organization_id,
                    "actor_id": _csv(actor_id),
                    "action": _csv(action),
                    "target_type": _csv(target_type),
                    "target_id": _csv(target_id),
                    "from": from_,
                    "to": to,
                    "any_of": any_of,
                    "metadata_key": metadata_key,
                    "metadata_value": metadata_value,
                    "starting_after": starting_after,
                }
            ),
            raw=True,
        )


class Billing:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.plans = _BillingPlans(transport)
        self.subscriptions = _BillingSubscriptions(transport)

    def sync_seats(self, subject_type: str, subject_id: str) -> m.BillingSeats:
        """Sync a per-seat subscription's Stripe quantity to the org's current member count
        (proration applied).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/billing/subjects/{subject_type}/{subject_id}/sync_seats",
        )

    def record_usage(self, body: m.RecordUsageBody | None = None) -> m.BillingUsage:
        """Report metered usage for a subject (idempotent on idempotency_key); mirrored to a
        Stripe meter event when the plan is metered and configured.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/usage",
            body=body,
        )


class _BillingPlans:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List the plans the tenant defines for their app's users (end-user billing)."""
        return self._t.request(
            method="GET",
            path="/v1/billing/plans",
        )

    def create(
        self, body: m.CreateBillingPlanBody, *, idempotency_key: str | None = None
    ) -> m.BillingPlanCreateResult:
        """Create an end-user billing plan."""
        return self._t.request(
            method="POST",
            path="/v1/billing/plans",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, plan_id: str) -> m.BillingPlan:
        """Read one end-user billing plan, including its Stripe price id and granted features."""
        return self._t.request(
            method="GET",
            path=f"/v1/billing/plans/{plan_id}",
        )

    def update(self, plan_id: str, body: m.UpdateBillingPlanBody | None = None) -> m.BillingPlan:
        """Update an end-user billing plan's name, slug, price, interval, features, audience or
        active flag.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/billing/plans/{plan_id}",
            body=body,
        )

    def delete(self, plan_id: str) -> DeletedObject:
        """Delete an end-user billing plan."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/billing/plans/{plan_id}",
        )


class _BillingSubscriptions:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self, *, subject_type: Literal["user", "org"] | None = None, subject_id: str | None = None
    ) -> ListPage:
        """List end-user subscriptions, optionally filtered by subject_type (user/org) and
        subject_id.
        """
        return self._t.request(
            method="GET",
            path="/v1/billing/subscriptions",
            query=_q(subject_type=subject_type, subject_id=subject_id),
        )

    def import_subscription(
        self, body: m.ImportSubscriptionBody | None = None, *, idempotency_key: str | None = None
    ) -> m.Subscription:
        """Adopt an EXISTING Stripe subscription (same Stripe account) onto an Atlas user/org +
        plan, for migrating billing into Atlas without re-charging.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/subscriptions/import",
            body=body,
            idempotency_key=idempotency_key,
        )


class BotLabels:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, limit: int | None = None, before: int | None = None) -> ListPage:
        """Export the supervised training labels (bot / human / suspect) with their subject and
        source.
        """
        return self._t.request(
            method="GET",
            path="/v1/bot_labels",
            query=_q(limit=limit, before=before),
        )

    def create(self, body: m.CreateBotLabelBody | None = None) -> m.BotLabel:
        """Add a supervised training label to a subject (user / device / ip_hash / attempt) —
        an analyst confirming a bot or a human.
        """
        return self._t.request(
            method="POST",
            path="/v1/bot_labels",
            body=body,
        )


class BotSignals:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, limit: int | None = None, before: int | None = None) -> ListPage:
        """Export the anonymised anti-bot signal lake (device + behavioural + network features,
        risk verdict, heuristic score), newest first with a `before` epoch-ms cursor.
        """
        return self._t.request(
            method="GET",
            path="/v1/bot_signals",
            query=_q(limit=limit, before=before),
        )


class Branding:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.Branding:
        """Read the instance branding / hosted-page appearance and its resolved (renderer)
        form.
        """
        return self._t.request(
            method="GET",
            path="/v1/branding",
        )

    def update(self, body: JSON | None = None) -> m.Branding:
        """Change branding with a PARTIAL merge (unlike auth_config full-replace), validated
        the way the renderer resolves it — a value it would drop is refused, not silently
        ignored.
        """
        return self._t.request(
            method="PATCH",
            path="/v1/branding",
            body=body,
        )

    def preview(self, body: JSON | None = None) -> m.HostedPagePreview:
        """Render a draft branding through the real sign-in hosted-page renderer (same
        sanitizers + CSP) so an agent sees what would ship before saving.
        """
        return self._t.request(
            method="POST",
            path="/v1/branding/preview",
            body=body,
        )


class Captcha:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def verify(self, body: m.VerifyCaptchaBody | None = None) -> m.CaptchaVerification:
        """§5 "captcha anywhere": verify a CAPTCHA token server-side against the instance's
        centrally-configured provider.
        """
        return self._t.request(
            method="POST",
            path="/v1/captcha/verify",
            body=body,
        )


class ConfigChangelog:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        action: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        since: str | None = None,
    ) -> CursorPage:
        """Config change history for this instance — who changed which config, when, with the
        per-section before/after diff where the source recorded one (else the changed field
        names).
        """
        return self._t.request(
            method="GET",
            path="/v1/config_changelog",
            query=_q(action=action, limit=limit, starting_after=starting_after, since=since),
        )


class Connectors:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List the caller's own community connector profiles (draft + published), with
        adoption counts.
        """
        return self._t.request(
            method="GET",
            path="/v1/connectors",
        )

    def create(self, body: m.CreateConnectorBody | None = None) -> m.Connector:
        """Create a community connector profile (SEO profile + OAuth config + share modes)."""
        return self._t.request(
            method="POST",
            path="/v1/connectors",
            body=body,
        )

    def get(self, connector_id: str) -> m.Connector:
        """Fetch one of the caller's own connector profiles."""
        return self._t.request(
            method="GET",
            path=f"/v1/connectors/{connector_id}",
        )

    def update(self, connector_id: str, body: m.UpdateConnectorBody | None = None) -> m.Connector:
        """Edit a connector profile — SEO fields, OAuth config, and share modes."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/connectors/{connector_id}",
            body=body,
        )

    def delete(self, connector_id: str) -> DeletedObject:
        """Delete one of the caller's own connector profiles and cascade its installs, reviews,
        and reports.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/connectors/{connector_id}",
        )

    def publish(self, connector_id: str) -> m.Connector:
        """Publish a connector to the public directory."""
        return self._t.request(
            method="POST",
            path=f"/v1/connectors/{connector_id}/publish",
        )

    def set_shared_credentials(
        self, connector_id: str, body: m.SetConnectorSharedCredentialsBody | None = None
    ) -> m.Connector:
        """Set, rotate, or revoke the full_shared OAuth credentials."""
        return self._t.request(
            method="POST",
            path=f"/v1/connectors/{connector_id}/shared_credentials",
            body=body,
        )

    def unlist(self, connector_id: str) -> m.Connector:
        """Remove a published connector from the directory (back to unlisted) without deleting
        it.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connectors/{connector_id}/unlist",
        )

    def install(self, slug: str, body: m.InstallConnectorBody | None = None) -> m.ConnectorInstall:
        """Enable a published connector on the caller's instance (prefill, full_shared, or
        full_idp), snapshotting its OAuth config into the connection.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connectors/{slug}/install",
            body=body,
        )

    def review(self, slug: str, body: m.ReviewConnectorBody | None = None) -> m.ConnectorReview:
        """Rate a connector the caller installed (1–5, optional text)."""
        return self._t.request(
            method="POST",
            path=f"/v1/connectors/{slug}/reviews",
            body=body,
        )


class DataSubjectRequests:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateDataSubjectRequestBody, *, idempotency_key: str | None = None
    ) -> m.DataSubjectRequest:
        """Create a DSAR (export or erasure) for a user from the backend — the twin of the
        self-service /client/me flows, for a DSAR orchestrator.
        """
        return self._t.request(
            method="POST",
            path="/v1/data_subject_requests",
            body=body,
            idempotency_key=idempotency_key,
        )

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        type: Literal["export", "erasure"] | None = None,
        status: Literal["pending", "scheduled", "processing", "completed", "rejected", "cancelled"]
        | None = None,
        user_id: str | None = None,
    ) -> CursorPage:
        """List GDPR/DSAR export and erasure requests, filterable by type/status/user (cursor
        pagination).
        """
        return self._t.request(
            method="GET",
            path="/v1/data_subject_requests",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                type=type,
                status=status,
                user_id=user_id,
            ),
        )

    def get(self, request_id: str) -> m.DataSubjectRequest:
        """Fetch a data-subject request, including an export's produced package."""
        return self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{request_id}",
        )

    def cancel(
        self, request_id: str, *, idempotency_key: str | None = None
    ) -> m.DataSubjectRequest:
        """Cancel a scheduled erasure within its grace window — the sibling to /fulfill (which
        expedites).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{request_id}/cancel",
            idempotency_key=idempotency_key,
        )

    def fulfill(
        self, request_id: str, *, idempotency_key: str | None = None
    ) -> m.DataSubjectRequest:
        """Fulfil a request now: build the export package, or run the erasure through the same
        soft-delete + PII-purge path a user-delete uses, ahead of the grace window.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{request_id}/fulfill",
            idempotency_key=idempotency_key,
        )

    def reject(
        self,
        request_id: str,
        body: m.RejectDataSubjectRequestBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.DataSubjectRequest:
        """Reject a request with a recorded reason."""
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{request_id}/reject",
            body=body,
            idempotency_key=idempotency_key,
        )


class Design:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.assets = _DesignAssets(transport)

    def get(self) -> m.DesignSettings:
        """Read the instance's sign-in page design: stored overrides, the resolved design,
        contrast warnings and the legacy flag.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/design",
        )

    def replace(self, body: m.ReplaceDesignBody) -> m.DesignSettings:
        """Replace the instance design ({ design: AtlasDesign })."""
        return self._t.request(
            method="PUT",
            path="/v1/instance/design",
            body=body,
        )

    def update(self, body: m.UpdateDesignBody) -> m.DesignSettings:
        """Change part of the instance design ({ design: AtlasDesignPatch }): nested settings
        merge, null removes a setting.
        """
        return self._t.request(
            method="PATCH",
            path="/v1/instance/design",
            body=body,
        )

    def preview(self, body: m.PreviewDesignBody) -> m.DesignPreview:
        """Compile an unsaved design: CSS variables scoped to .atlas-root, data attributes,
        font stylesheet URLs, warnings, the resolved design and the rendered sign-in page.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/design/preview",
            body=body,
        )

    def catalog(self) -> JSON:
        """The design-system catalog: the sign-in page presets (each fully resolved), the
        curated font list, and the documented --atlas-* CSS variable set.
        """
        return self._t.request(
            method="GET",
            path="/v1/design/catalog",
        )


class _DesignAssets:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def upload(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        kind: Literal["background", "logo"] | None = None,
    ) -> m.DesignAsset:
        """Upload a design image (a background or a logo) for this instance."""
        return self._t.request(
            method="POST",
            path="/v1/design/assets",
            query=_q(kind=kind),
            content=data,
            content_type=content_type or _sniff_image_type(data),
        )

    def list(self) -> ListPage:
        """List this instance's uploaded design images, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/design/assets",
        )

    def delete(self, asset_id: str) -> m.DesignAssetDeleteResult:
        """Delete one of this instance's design images."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/design/assets/{asset_id}",
        )


class Diagnostics:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def login_readiness(
        self, *, origin: str | None = None, live: bool | None = None
    ) -> m.LoginReadiness:
        """End-to-end login-readiness probe for a given `origin` (CORS, cookie domain, email
        claim, JWKS), reporting the observed effective runtime values with a per-hop
        pass/fail and a specific fix.
        """
        return self._t.request(
            method="GET",
            path="/v1/diagnostics/login_readiness",
            query=_q(origin=origin, live=live),
        )

    def request_inspector(
        self,
        *,
        origin: str,
        method: str | None = None,
        path: str | None = None,
        token: str | None = None,
    ) -> m.RequestInspection:
        """Explain why a specific browser request would be rejected: CORS origin, CORS method
        (the DELETE/PATCH class), session-cookie delivery, rate-limit bucket, captcha
        requirement, and — with an optional `token` — JWT...
        """
        return self._t.request(
            method="GET",
            path="/v1/diagnostics/request_inspector",
            query=_q(origin=origin, method=method, path=path, token=token),
        )


class Directory:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        category: str | None = None,
        verified: bool | None = None,
        q: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ListPage:
        """Browse the unified connector directory — built-in providers plus published community
        connectors, ranked popular-first.
        """
        return self._t.request(
            method="GET",
            path="/v1/directory",
            query=_q(category=category, verified=verified, q=q, limit=limit, offset=offset),
        )


class EmailAddresses:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def set_primary(self, email_id: str, *, idempotency_key: str | None = None) -> m.EmailAddress:
        """Make a verified address primary — flat alias (user derived from the address)."""
        return self._t.request(
            method="POST",
            path=f"/v1/email_addresses/{email_id}/primary",
            idempotency_key=idempotency_key,
        )

    def verify(self, email_id: str, *, idempotency_key: str | None = None) -> m.EmailAddress:
        """Mark an address verified — flat alias (user derived from the address)."""
        return self._t.request(
            method="POST",
            path=f"/v1/email_addresses/{email_id}/verify",
            idempotency_key=idempotency_key,
        )


class EmailTemplates:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List email templates with their defaults and any instance override."""
        return self._t.request(
            method="GET",
            path="/v1/email_templates",
        )

    def set(
        self, name: str, body: m.SetEmailTemplateBody | None = None
    ) -> m.EmailTemplateSetResult:
        """Override a template."""
        return self._t.request(
            method="PUT",
            path=f"/v1/email_templates/{name}",
            body=body,
        )

    def reset(self, name: str) -> m.EmailTemplateResetResult:
        """Revert a template to the Atlas built-in."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/email_templates/{name}",
        )

    def preview(self, name: str, body: m.PreviewEmailTemplateBody | None = None) -> m.EmailPreview:
        """Render an email template (an unsaved draft if supplied, else the stored one) with
        SAMPLE variables — never a real code — so an agent can see the result before saving.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/email_templates/{name}/preview",
            body=body,
        )


class EntitlementOverrides:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateEntitlementOverrideBody, *, idempotency_key: str | None = None
    ) -> m.EntitlementOverride:
        """Grant a SALES-LED entitlement override (P1-6): pin a plan / features / limits onto a
        user or org without Stripe (e.g. an Enterprise contract).
        """
        return self._t.request(
            method="POST",
            path="/v1/entitlement_overrides",
            body=body,
            idempotency_key=idempotency_key,
        )

    def list(
        self, *, subject_type: Literal["user", "org"] | None = None, subject_id: str | None = None
    ) -> ListPage:
        """List sales-led entitlement overrides, optionally filtered by subject_type (user/org)
        and subject_id.
        """
        return self._t.request(
            method="GET",
            path="/v1/entitlement_overrides",
            query=_q(subject_type=subject_type, subject_id=subject_id),
        )

    def delete(self, override_id: str) -> DeletedObject:
        """Revoke (hard-delete) a sales-led entitlement override."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/entitlement_overrides/{override_id}",
        )


class Events:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        type: str | None = None,
        from_: str | int | None = None,
        to: str | int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Read the product activity feed (events), filterable by type and time and cursor-
        paginated, with the list of event types this instance has actually emitted.
        """
        return self._t.request(
            method="GET",
            path="/v1/events",
            query=_q(
                **{
                    "type": type,
                    "from": from_,
                    "to": to,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )


class Fga:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.stores = _FgaStores(transport)
        self.authorization_models = _FgaModels(transport)

    def batch_check(
        self, store_id: str, body: m.BatchCheckFgaBody | None = None
    ) -> m.FgaBatchCheck:
        """Check up to 100 (user, relation, object) tuples in one request."""
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/batch-check",
            body=body,
        )

    def check(self, store_id: str, body: m.CheckFgaBody | None = None) -> m.FgaCheck:
        """Check whether a user has a relation on an object, resolving the authorization model
        (direct tuples, computed usersets, tuple-to-userset hops, set operators) with cycle
        + depth safety.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/check",
            body=body,
        )

    def expand(self, store_id: str, body: m.ExpandFgaBody | None = None) -> m.FgaExpand:
        """Expand the userset tree for an (object, relation) — who would hold the relation,
        mirroring the model rewrite.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/expand",
            body=body,
        )

    def list_objects(
        self, store_id: str, body: m.ListObjectsFgaBody | None = None
    ) -> m.FgaListObjects:
        """List the object ids of a type that a user has a relation on."""
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/list-objects",
            body=body,
        )

    def read(self, store_id: str, body: m.ReadFgaBody | None = None) -> ListPage:
        """Query stored relationship tuples in a store, optionally filtered by user, relation
        and/or object.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/read",
            body=body,
        )

    def write(
        self,
        store_id: str,
        body: m.WriteFgaBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.FgaWriteResult:
        """Transactionally write and/or delete relationship tuples in a store."""
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/write",
            body=body,
            idempotency_key=idempotency_key,
        )


class _FgaStores:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List fine-grained authorization (ReBAC / Zanzibar) stores in the instance."""
        return self._t.request(
            method="GET",
            path="/v1/fga/stores",
        )

    def create(
        self, body: m.CreateFgaStoreBody | None = None, *, idempotency_key: str | None = None
    ) -> m.FgaStore:
        """Create a fine-grained authorization store — an isolated namespace for authorization
        models and relationship tuples.
        """
        return self._t.request(
            method="POST",
            path="/v1/fga/stores",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, store_id: str) -> m.FgaStore:
        """Read one FGA store."""
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{store_id}",
        )

    def delete(self, store_id: str) -> DeletedObject:
        """Delete an FGA store, cascading its authorization models and relationship tuples."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/fga/stores/{store_id}",
        )


class _FgaModels:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, store_id: str) -> ListPage:
        """List the immutable authorization-model versions of a store, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{store_id}/authorization-models",
        )

    def create(
        self,
        store_id: str,
        body: m.CreateFgaAuthorizationModelBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.FgaAuthorizationModel:
        """Write a new immutable authorization-model version (OpenFGA-shaped type_definitions
        with this/computedUserset/tupleToUserset and union/intersection/difference).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/authorization-models",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, store_id: str, model_id: str) -> m.FgaAuthorizationModel:
        """Read one authorization-model version, including its full model definition."""
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{store_id}/authorization-models/{model_id}",
        )


class OpenFga:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.stores = _OpenFgaStores(transport)
        self.authorization_models = _OpenFgaModels(transport)

    def batch_check(
        self, store_id: str, body: m.BatchCheckOpenFgaBody
    ) -> m.OpenFgaBatchCheckResult:
        """Check up to 100 tuples in one request, keyed by correlation id (OpenFGA-wire
        BatchCheck).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/batch-check",
            body=body,
        )

    def check(
        self, store_id: str, body: m.CheckOpenFgaBody
    ) -> m.OpenFgaBatchCheckResultResultValue:
        """Check whether a user has a relation on an object (OpenFGA-wire check)."""
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/check",
            body=body,
        )

    def expand(self, store_id: str, body: m.ExpandOpenFgaBody) -> m.OpenFgaExpandResult:
        """Expand the userset tree for an (object, relation) (OpenFGA-wire Expand)."""
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/expand",
            body=body,
        )

    def list_objects(
        self, store_id: str, body: m.ListObjectsOpenFgaBody
    ) -> m.OpenFgaListObjectsResult:
        """List the objects of a type a user has a relation on (OpenFGA-wire ListObjects)."""
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/list-objects",
            body=body,
        )

    def read(self, store_id: str, body: m.ReadOpenFgaBody | None = None) -> m.OpenFgaReadResult:
        """Read relationship tuples, optionally filtered by a tuple key (OpenFGA-wire Read)."""
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/read",
            body=body,
        )

    def write(self, store_id: str, body: m.WriteOpenFgaBody | None = None) -> JSON:
        """Write or delete relationship tuples in a store (OpenFGA-wire write)."""
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/write",
            body=body,
        )


class _OpenFgaStores:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> m.OpenFgaStoreList:
        """List the instance's OpenFGA (ReBAC) authorization stores."""
        return self._t.request(
            method="GET",
            path="/v1/openfga/stores",
        )

    def create(
        self, body: m.CreateOpenFgaStoreBody, *, idempotency_key: str | None = None
    ) -> m.OpenFgaStore:
        """Create an OpenFGA authorization store."""
        return self._t.request(
            method="POST",
            path="/v1/openfga/stores",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, store_id: str) -> m.OpenFgaStore:
        """Get one OpenFGA store (OpenFGA-wire GetStore)."""
        return self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{store_id}",
        )


class _OpenFgaModels:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, store_id: str) -> m.OpenFgaAuthorizationModelList:
        """List the authorization models in a store."""
        return self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{store_id}/authorization-models",
        )

    def create(
        self, store_id: str, body: m.CreateOpenFgaAuthorizationModelBody | None = None
    ) -> m.OpenFgaWriteModelResult:
        """Write a new authorization model to a store."""
        return self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/authorization-models",
            body=body,
        )

    def get(self, store_id: str, model_id: str) -> m.OpenFgaAuthorizationModelResult:
        """Read one authorization model (OpenFGA-wire ReadAuthorizationModel)."""
        return self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{store_id}/authorization-models/{model_id}",
        )


class Grants:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def revoke(self, grant_id: str, *, idempotency_key: str | None = None) -> m.GrantRevokeResult:
        """Revoke one consent grant and cascade-revoke its access/refresh grants through the
        standard revocation path, so the app stops working on its next request.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/grants/{grant_id}",
            idempotency_key=idempotency_key,
        )


class Instance:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.cookie_consent = _InstanceCookieConsent(transport)
        self.security = _InstanceSecurity(transport)

    def get(self) -> m.Instance:
        """Read instance configuration."""
        return self._t.request(
            method="GET",
            path="/v1/instance",
        )

    def update(self, body: m.UpdateInstanceBody | None = None) -> m.Instance:
        """Update allowed origins and auth_config (a partial, validated, merged patch — not a
        replace).
        """
        return self._t.request(
            method="PATCH",
            path="/v1/instance",
            body=body,
        )

    def set_captcha_secret(self, body: m.SetCaptchaSecretBody | None = None) -> m.CaptchaSecret:
        """Store the captcha provider secret (write-only, encrypted; never read back)."""
        return self._t.request(
            method="PUT",
            path="/v1/instance/captcha_secret",
            body=body,
        )

    def delete_captcha_secret(self) -> m.InstanceDeleteCaptchaSecretResult:
        """Clear the stored captcha provider secret for the current provider."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/captcha_secret",
        )

    def set_kerberos_secret(self, body: m.SetKerberosSecretBody | None = None) -> m.KerberosSecret:
        """Store the per-instance Kerberos/IWA trusted-proxy secret (write-only, encrypted;
        never read back).
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/kerberos_secret",
            body=body,
        )

    def delete_kerberos_secret(self) -> m.InstanceDeleteKerberosSecretResult:
        """Clear the stored Kerberos/IWA trusted-proxy secret for this instance."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/kerberos_secret",
        )

    def set_ldap_bind_password(
        self, connection_id: str, body: m.SetLdapBindPasswordBody | None = None
    ) -> m.LdapBindPassword:
        """Store an LDAP connection service-account bind password (write-only, encrypted; never
        read back).
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/instance/ldap_connections/{connection_id}/bind_password",
            body=body,
        )

    def delete_ldap_bind_password(
        self, connection_id: str
    ) -> m.InstanceDeleteLdapBindPasswordResult:
        """Clear the stored bind password for an LDAP connection."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/instance/ldap_connections/{connection_id}/bind_password",
        )

    def preflight(self) -> m.Preflight:
        """Check your setup in one call."""
        return self._t.request(
            method="GET",
            path="/v1/instance/preflight",
        )


class _InstanceCookieConsent:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.CookieConsent:
        """Read the cookie-consent CMP injected into the hosted sign-in, sign-up and account
        pages (enabled:false when none).
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/cookie_consent",
        )

    def set(self, body: m.SetCookieConsentBody) -> m.CookieConsent:
        """Set the cookie-consent CMP for the hosted pages (any provider)."""
        return self._t.request(
            method="PUT",
            path="/v1/instance/cookie_consent",
            body=body,
        )

    def delete(self) -> m.CookieConsent:
        """Turn off the hosted-page cookie-consent CMP: no script is injected and the CSP goes
        back to normal.
        """
        return self._t.request(
            method="DELETE",
            path="/v1/instance/cookie_consent",
        )


class _InstanceSecurity:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.InstanceSecurity:
        """Read the instance kill switches (per-flow on/off) and the customer IP allowlist."""
        return self._t.request(
            method="GET",
            path="/v1/instance/security",
        )

    def update(self, body: m.UpdateInstanceSecurityBody | None = None) -> m.InstanceSecurity:
        """Set the instance kill switches and/or IP allowlist."""
        return self._t.request(
            method="PATCH",
            path="/v1/instance/security",
            body=body,
        )


class Jobs:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, limit: int | None = None, starting_after: str | None = None) -> CursorPage:
        """List bulk import/export jobs, newest first (cursor pagination)."""
        return self._t.request(
            method="GET",
            path="/v1/jobs",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def get(self, job_id: str) -> m.Job:
        """Fetch a job: its status, counters and (for an export) result."""
        return self._t.request(
            method="GET",
            path=f"/v1/jobs/{job_id}",
        )

    def list_errors(self, job_id: str) -> ListPage:
        """List a job's per-row errors ({ index, email, code, message })."""
        return self._t.request(
            method="GET",
            path=f"/v1/jobs/{job_id}/errors",
        )


class LegacyAuthConnection:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.LegacyAuthConnection:
        """Read the instance's lazy-migration (legacy-auth / custom-DB) connection."""
        return self._t.request(
            method="GET",
            path="/v1/legacy_auth_connection",
        )

    def set(
        self, body: m.SetLegacyAuthConnectionBody, *, idempotency_key: str | None = None
    ) -> m.LegacyAuthConnection:
        """Create or replace the instance's lazy-migration connection (verify_url +
        signing_secret, enabled, import_on_login, timeout_ms).
        """
        return self._t.request(
            method="PUT",
            path="/v1/legacy_auth_connection",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, *, idempotency_key: str | None = None) -> m.LegacyAuthConnectionDeleteResult:
        """Delete the instance's lazy-migration (legacy-auth / custom-DB) connection."""
        return self._t.request(
            method="DELETE",
            path="/v1/legacy_auth_connection",
            idempotency_key=idempotency_key,
        )


class Localizations:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        resource_type: str | None = None,
        resource_name: str | None = None,
        locale: str | None = None,
    ) -> ListPage:
        """List per-language localization overrides (email/SMS templates, hosted-page copy)."""
        return self._t.request(
            method="GET",
            path="/v1/localizations",
            query=_q(resource_type=resource_type, resource_name=resource_name, locale=locale),
        )

    def create(self, body: m.CreateLocalizationBody | None = None) -> m.Localization:
        """Create or replace a localization override for one resource + locale."""
        return self._t.request(
            method="POST",
            path="/v1/localizations",
            body=body,
        )

    def get(self, localization_id: str) -> m.Localization:
        """Read one localization override by id."""
        return self._t.request(
            method="GET",
            path=f"/v1/localizations/{localization_id}",
        )

    def update(
        self, localization_id: str, body: m.UpdateLocalizationBody | None = None
    ) -> m.Localization:
        """Update a localization override content or enabled flag."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/localizations/{localization_id}",
            body=body,
        )

    def delete(self, localization_id: str) -> None:
        """Delete a localization override, reverting that locale to the base template/copy."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/localizations/{localization_id}",
        )


class LogStreams:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List log streams (event forwarding to Datadog, Splunk or a generic HTTP sink)."""
        return self._t.request(
            method="GET",
            path="/v1/log_streams",
        )

    def create(
        self, body: m.CreateLogStreamBody | None = None, *, idempotency_key: str | None = None
    ) -> m.LogStream:
        """Create a log stream."""
        return self._t.request(
            method="POST",
            path="/v1/log_streams",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, stream_id: str) -> m.LogStream:
        """Read one log stream, including its forwarding status, cursor and last error."""
        return self._t.request(
            method="GET",
            path=f"/v1/log_streams/{stream_id}",
        )

    def update(self, stream_id: str, body: m.UpdateLogStreamBody | None = None) -> m.LogStream:
        """Update a log stream's name, destination, event_filter, enabled flag, or status
        (active/paused).
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/log_streams/{stream_id}",
            body=body,
        )

    def delete(self, stream_id: str) -> DeletedObject:
        """Delete a log stream."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/log_streams/{stream_id}",
        )

    def test(self, stream_id: str) -> m.LogStreamTest:
        """Send one synthetic event to the sink with the stream's real credentials and return
        the sink's status.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/log_streams/{stream_id}/test",
        )


class LtiPlatforms:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List the LTI 1.3 platform registrations allowed to launch this instance."""
        return self._t.request(
            method="GET",
            path="/v1/lti_platforms",
        )

    def create(self, body: m.CreateLtiPlatformBody | None = None) -> m.LtiPlatform:
        """Register an LTI 1.3 platform (issuer, client_id, auth_login_url, jwks_uri,
        deployment_ids).
        """
        return self._t.request(
            method="POST",
            path="/v1/lti_platforms",
            body=body,
        )

    def get(self, platform_id: str) -> m.LtiPlatform:
        """Fetch one LTI 1.3 platform registration."""
        return self._t.request(
            method="GET",
            path=f"/v1/lti_platforms/{platform_id}",
        )

    def update(
        self, platform_id: str, body: m.UpdateLtiPlatformBody | None = None
    ) -> m.LtiPlatform:
        """Update an LTI 1.3 platform registration (URLs, deployment ids, org link)."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/lti_platforms/{platform_id}",
            body=body,
        )

    def delete(self, platform_id: str) -> DeletedObject:
        """Remove an LTI 1.3 platform registration."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/lti_platforms/{platform_id}",
        )


class M2mTokens:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def verify(self, body: m.VerifyM2mTokenBody | None = None) -> m.M2mTokenVerification:
        """Verify a presented machine secret → { valid, machine_id?"""
        return self._t.request(
            method="POST",
            path="/v1/m2m_tokens/verify",
            body=body,
        )


class MachineEnrolmentTokens:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateMachineEnrolmentTokenBody | None = None
    ) -> m.MachineEnrolmentTokenWithSecret:
        """Mint a machine enrolment token (single/multi-use, expiring, org-bound, approval-
        gated).
        """
        return self._t.request(
            method="POST",
            path="/v1/machine_enrolment_tokens",
            body=body,
        )

    def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List machine enrolment tokens (never the secret), newest first."""
        return self._t.request(
            method="GET",
            path="/v1/machine_enrolment_tokens",
            query=_q(organization_id=organization_id, limit=limit, starting_after=starting_after),
        )

    def delete(self, token_id: str) -> DeletedObject:
        """Delete a machine enrolment token; it can no longer enrol new devices."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/machine_enrolment_tokens/{token_id}",
        )


class Machines:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, body: m.CreateMachineBody | None = None) -> m.MachineWithSecret:
        """Create a named machine (M2M) identity; returns the machine secret (mk_) ONCE."""
        return self._t.request(
            method="POST",
            path="/v1/machines",
            body=body,
        )

    def list(
        self,
        *,
        status: Literal["active", "pending", "revoked"] | None = None,
        hostname: str | None = None,
        owner_user_id: str | None = None,
        organization_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List machine identities (device registry), filtered by lifecycle status, reported
        hostname, owning user, organization, and/or metadata, with keyset pagination.
        """
        return self._t.request(
            method="GET",
            path="/v1/machines",
            query=_q(
                status=status,
                hostname=hostname,
                owner_user_id=owner_user_id,
                organization_id=organization_id,
                metadata=_json(metadata),
                limit=limit,
                starting_after=starting_after,
            ),
        )

    def get(self, machine_id: str) -> m.Machine:
        """Fetch one named machine identity by id."""
        return self._t.request(
            method="GET",
            path=f"/v1/machines/{machine_id}",
        )

    def update(self, machine_id: str, body: m.UpdateMachineBody | None = None) -> m.Machine:
        """Rename a machine identity."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/machines/{machine_id}",
            body=body,
        )

    def delete(self, machine_id: str) -> DeletedObject:
        """Delete a machine identity."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/machines/{machine_id}",
        )

    def approve(self, machine_id: str) -> m.Machine:
        """Approve a device that enrolled under an approval-gated token (pending → active)."""
        return self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/approve",
        )

    def update_metadata(
        self, machine_id: str, body: m.UpdateMachineMetadataBody | None = None
    ) -> m.Machine:
        """Merge device metadata (hostname, os, app_version, last_seen_at) into a machine."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/machines/{machine_id}/metadata",
            body=body,
        )

    def list_organization_memberships(self, machine_id: str) -> ListPage:
        """List the organizations a machine belongs to with the org's resolved plan and the
        enrolment time — the machine-token counterpart of the user organization_memberships
        route.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/machines/{machine_id}/organization_memberships",
        )

    def revoke(self, machine_id: str) -> m.Machine:
        """Revoke a machine device; its key stops minting tokens immediately (record kept)."""
        return self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/revoke",
        )

    def rotate_key(self, machine_id: str, body: m.RotateMachineKeyBody) -> m.Machine:
        """Rotate a device keypair: register a new public key; the old private key stops
        verifying.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/rotate_key",
            body=body,
        )

    def rotate_secret(self, machine_id: str) -> m.MachineWithSecret:
        """Rotate a machine secret; the old one stops working and a new mk_ is shown once."""
        return self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/rotate_secret",
        )


class ManagedWaf:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.ManagedWaf:
        """§5 Read the managed AWS WAF configuration and provisioning state."""
        return self._t.request(
            method="GET",
            path="/v1/managed_waf",
        )

    def set(self, body: m.SetManagedWafBody | None = None) -> m.ManagedWaf:
        """§5 Configure the managed AWS WAF: scope/region, edge target, token domains, gated
        paths, and the write-only BYO AWS credentials.
        """
        return self._t.request(
            method="PUT",
            path="/v1/managed_waf",
            body=body,
        )

    def deprovision(self) -> JSON:
        """§5 Deprovision: disassociate the WebACL from the edge and delete it, then clear the
        stored state.
        """
        return self._t.request(
            method="POST",
            path="/v1/managed_waf/deprovision",
        )

    def provision(self) -> JSON:
        """§5 Provision now: idempotently create-or-update the AWS WAF WebACL with the CAPTCHA
        rule and associate it with the edge (ALB or CloudFront).
        """
        return self._t.request(
            method="POST",
            path="/v1/managed_waf/provision",
        )

    def status(self) -> m.ManagedWafStatus:
        """§5 Read just the managed AWS WAF provisioning state: status, WebACL id/arn, last
        error and last-provisioned time.
        """
        return self._t.request(
            method="GET",
            path="/v1/managed_waf/status",
        )


class Mcp:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.McpServer:
        """MCP server descriptor and the tools this key may call."""
        return self._t.request(
            method="GET",
            path="/v1/mcp",
        )

    def call(self, body: m.McpRequestBody | None = None) -> m.McpResponse:
        """MCP JSON-RPC endpoint: initialize, tools/list, tools/call, ping."""
        return self._t.request(
            method="POST",
            path="/v1/mcp",
            body=body,
        )


class McpConnector:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.McpConnector:
        """Read the instance's remote MCP connector: enabled state, exposed tool scopes,
        dynamic-registration policy, plus the computed discovery URL, resource identifier
        and whether the resource server exists.
        """
        return self._t.request(
            method="GET",
            path="/v1/mcp_connector",
        )

    def set(
        self, body: m.SetMcpConnectorBody | None = None, *, idempotency_key: str | None = None
    ) -> m.McpConnector:
        """Configure the remote MCP connector (enabled, name, exposed_scopes,
        dynamic_registration, allowed_redirect_hosts).
        """
        return self._t.request(
            method="PUT",
            path="/v1/mcp_connector",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, *, idempotency_key: str | None = None) -> m.McpConnector:
        """Disable the remote MCP connector."""
        return self._t.request(
            method="DELETE",
            path="/v1/mcp_connector",
            idempotency_key=idempotency_key,
        )


class MessagingProviders:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> m.MessagingProviders:
        """Read the instance's BYOK email and SMS provider config: transport, from-address and
        which secret keys are set.
        """
        return self._t.request(
            method="GET",
            path="/v1/messaging_providers",
        )

    def set_email(self, body: m.EmailProviderConfig) -> m.MessagingProvider:
        """Configure the email delivery provider."""
        return self._t.request(
            method="PUT",
            path="/v1/messaging_providers/email",
            body=body,
        )

    def set_sms(self, body: m.SmsProviderConfig) -> m.MessagingProvider:
        """Configure the SMS delivery provider."""
        return self._t.request(
            method="PUT",
            path="/v1/messaging_providers/sms",
            body=body,
        )

    def delete(self, channel: str, *, force: bool = False) -> m.MessagingProviderDeleteResult:
        """Remove the email or sms provider configuration for the instance.

        Removing the email provider is refused with 409 ``EMAIL_PROVIDER_IN_USE`` while
        email-dependent features are on and nothing else would deliver email (the
        error's ``meta.features`` lists them, e.g. ``"emailCode"``, ``"emailLink"``,
        ``"emailVerification"``, ``"passwordReset"``). Pass ``force=True`` to remove it
        anyway.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/messaging_providers/{channel}",
            query={"force": True} if force else None,
        )

    def test(
        self, channel: str, body: m.TestMessagingProviderBody | None = None
    ) -> m.MessagingTest:
        """Send a clearly-marked test message to a destination to verify the configured email
        or SMS provider delivers, without triggering a real auth flow.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/messaging_providers/{channel}/test",
            body=body,
        )


class NetworkAcls:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List network ACLs — per-instance IP allow/deny rules that gate access to the
        instance, in priority order.
        """
        return self._t.request(
            method="GET",
            path="/v1/network_acls",
        )

    def create(self, body: m.CreateNetworkAclBody | None = None) -> m.NetworkAcl:
        """Create a network ACL rule (allow|deny, a CIDR or single address, a priority)."""
        return self._t.request(
            method="POST",
            path="/v1/network_acls",
            body=body,
        )

    def get(self, acl_id: str) -> m.NetworkAcl:
        """Read one network ACL rule."""
        return self._t.request(
            method="GET",
            path=f"/v1/network_acls/{acl_id}",
        )

    def update(self, acl_id: str, body: m.UpdateNetworkAclBody | None = None) -> m.NetworkAcl:
        """Update a network ACL rule's action, cidr, description, priority or enabled flag."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/network_acls/{acl_id}",
            body=body,
        )

    def delete(self, acl_id: str) -> DeletedObject:
        """Delete a network ACL rule."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/network_acls/{acl_id}",
        )


class Notifications:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.categories = _NotificationCategories(transport)
        self.templates = _NotificationTemplates(transport)

    def send(self, body: m.SendNotificationBody) -> m.NotificationSend:
        """Send a templated, instance-branded security-notification email to one of your end-
        users, honouring their per-category notification preferences.
        """
        return self._t.request(
            method="POST",
            path="/v1/notifications",
            body=body,
        )


class _NotificationCategories:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, body: m.CreateNotificationCategoryBody) -> m.NotificationCategory:
        """Create a tenant-defined notification category: a key (unique per instance, cannot
        collide with a built-in) and the user-facing label shown on the end-user preference
        toggle.
        """
        return self._t.request(
            method="POST",
            path="/v1/notification_categories",
            body=body,
        )

    def list(self) -> ListPage:
        """List this instance's tenant-defined notification categories."""
        return self._t.request(
            method="GET",
            path="/v1/notification_categories",
        )

    def set(self, key: str, body: m.SetNotificationCategoryBody) -> m.NotificationCategory:
        """Update a tenant-defined notification category's user-facing label."""
        return self._t.request(
            method="PUT",
            path=f"/v1/notification_categories/{key}",
            body=body,
        )

    def delete(self, key: str) -> m.NotificationCategoryDeleteResult:
        """Delete a tenant-defined notification category."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/notification_categories/{key}",
        )


class _NotificationTemplates:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, body: m.CreateNotificationTemplateBody) -> m.NotificationTemplate:
        """Create a tenant-defined notification template: a name (unique per instance), a
        subject and body with `{{variables}}`, and the category whose per-user preference
        gates it.
        """
        return self._t.request(
            method="POST",
            path="/v1/notification_templates",
            body=body,
        )

    def list(self) -> ListPage:
        """List this instance's tenant-defined notification templates."""
        return self._t.request(
            method="GET",
            path="/v1/notification_templates",
        )

    def get(self, name: str) -> m.NotificationTemplate:
        """Retrieve one tenant-defined notification template by name."""
        return self._t.request(
            method="GET",
            path=f"/v1/notification_templates/{name}",
        )

    def set(self, name: str, body: m.SetNotificationTemplateBody) -> m.NotificationTemplate:
        """Update a tenant-defined notification template's subject, body and category by name."""
        return self._t.request(
            method="PUT",
            path=f"/v1/notification_templates/{name}",
            body=body,
        )

    def delete(self, name: str) -> m.NotificationTemplateDeleteResult:
        """Delete a tenant-defined notification template by name."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/notification_templates/{name}",
        )


class OAuthProviders:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self, *, provider: str | Sequence[str] | None = None, configured: bool | None = None
    ) -> ListPage:
        """List the social sign-in provider catalog with which are configured/enabled and each
        derived redirect URI.
        """
        return self._t.request(
            method="GET",
            path="/v1/oauth_providers",
            query=_q(provider=_csv(provider), configured=configured),
        )

    def get(self, provider: str) -> m.OAuthProvider:
        """Fetch one social sign-in provider: its catalog entry and configured state, no
        secret.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_providers/{provider}",
        )

    def upsert(
        self,
        provider: str,
        body: m.UpsertOAuthProviderBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OauthProvider:
        """Set a social sign-in provider's client id/secret (and scopes/settings)."""
        return self._t.request(
            method="PUT",
            path=f"/v1/oauth_providers/{provider}",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, provider: str) -> m.OAuthProviderDeleteResult:
        """Remove a social sign-in provider’s credentials."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/oauth_providers/{provider}",
        )

    def set_enabled(
        self, provider: str, body: m.SetOAuthProviderEnabledBody | None = None
    ) -> m.OAuthProviderSetEnabledResult:
        """Enable or disable a social sign-in provider — this is what turns it on (saving
        credentials via PUT does not).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_providers/{provider}/enabled",
            body=body,
        )

    def set_scope(
        self, provider: str, body: m.SetOAuthProviderScopeBody | None = None
    ) -> m.OAuthProviderSetScopeResult:
        """Scope a provider to sign-in, sign-up, or both (allow_sign_in / allow_sign_up)."""
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_providers/{provider}/scope",
            body=body,
        )

    def test(self, provider: str) -> m.OauthConnectionTest:
        """Test a social sign-in provider's stored credentials against the provider's token
        endpoint.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_providers/{provider}/test",
        )


class OrgLdapConnections:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, organization_id: str | None = None) -> ListPage:
        """List the organization-owned LDAP / AD connections."""
        return self._t.request(
            method="GET",
            path="/v1/org_ldap_connections",
            query=_q(organization_id=organization_id),
        )

    def create(
        self,
        body: m.CreateOrgLdapConnectionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgLdapConnection:
        """Create an organization-owned LDAP / AD connection (url, bind_dn, base_dn,
        user_filter, attributes).
        """
        return self._t.request(
            method="POST",
            path="/v1/org_ldap_connections",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, connection_id: str) -> m.OrgLdapConnection:
        """Fetch one organization-owned LDAP connection."""
        return self._t.request(
            method="GET",
            path=f"/v1/org_ldap_connections/{connection_id}",
        )

    def update(
        self,
        connection_id: str,
        body: m.UpdateOrgLdapConnectionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgLdapConnection:
        """Update an organization-owned LDAP connection."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/org_ldap_connections/{connection_id}",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, connection_id: str, *, idempotency_key: str | None = None) -> DeletedObject:
        """Delete an organization-owned LDAP connection."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/org_ldap_connections/{connection_id}",
            idempotency_key=idempotency_key,
        )

    def test(
        self, connection_id: str, body: m.TestOrgLdapConnectionBody | None = None
    ) -> m.OrgLdapConnectionTest:
        """Test an organization-owned LDAP connection: attempt a service-account bind and
        report ok/failure.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/org_ldap_connections/{connection_id}/test",
            body=body,
        )


class OrganizationSettingsSchema:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.OrganizationSettingsSchema:
        """Fetch the instance-wide JSON Schema registered for organization settings."""
        return self._t.request(
            method="GET",
            path="/v1/organization_settings_schema",
        )

    def create(
        self, body: m.CreateOrganizationSettingsSchemaBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettingsSchema:
        """Register the instance-wide JSON Schema for organization settings (first
        registration).
        """
        return self._t.request(
            method="POST",
            path="/v1/organization_settings_schema",
            body=body,
            idempotency_key=idempotency_key,
        )

    def replace(
        self, body: m.ReplaceOrganizationSettingsSchemaBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettingsSchema:
        """Replace the instance-wide organization-settings JSON Schema."""
        return self._t.request(
            method="PUT",
            path="/v1/organization_settings_schema",
            body=body,
            idempotency_key=idempotency_key,
        )


class Pca:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_attestors(self) -> m.PcaAttestors:
        """The instance's trusted software-attestor public keys."""
        return self._t.request(
            method="GET",
            path="/v1/pca/attestors",
        )

    def set_attestors(self, body: m.SetPcaAttestorsBody) -> m.PcaAttestors:
        """Replace the trusted software-attestor key list."""
        return self._t.request(
            method="PUT",
            path="/v1/pca/attestors",
            body=body,
        )

    def unfreeze(self) -> m.PcaFreeze:
        """Clear the instance-wide PCA kill switch."""
        return self._t.request(
            method="DELETE",
            path="/v1/pca/freeze",
        )

    def freeze(self, body: m.FreezePcaBody | None = None) -> m.PcaFreeze:
        """Engage the instance-wide PCA kill switch: every PCActn is denied until it is
        cleared.
        """
        return self._t.request(
            method="POST",
            path="/v1/pca/freeze",
            body=body,
        )

    def revoke(self, body: m.CreatePcaRevocationBody) -> m.PcaRevokeResult:
        """Revoke a capability id under a grant; any PCActn whose chain contains it is denied."""
        return self._t.request(
            method="POST",
            path="/v1/pca/revocations",
            body=body,
        )

    def deny_step_up(self, step_up_id: str, body: m.DenyPcaStepUpBody | None = None) -> m.PcaStepup:
        """Deny a pending step-up: the held action is never anchored."""
        return self._t.request(
            method="POST",
            path=f"/v1/pca/stepups/{step_up_id}/deny",
            body=body,
        )


class RadiusClients:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List the RADIUS NAS clients — the VPN/WiFi/firewall devices allowed to authenticate
        this instance's users over RADIUS.
        """
        return self._t.request(
            method="GET",
            path="/v1/radius_clients",
        )

    def create(self, body: m.CreateRadiusClientBody | None = None) -> m.RadiusClient:
        """Register a RADIUS NAS client (name, NAS-Identifier, optional source-IP bind, write-
        only shared secret).
        """
        return self._t.request(
            method="POST",
            path="/v1/radius_clients",
            body=body,
        )

    def get(self, radius_client_id: str) -> m.RadiusClient:
        """Read one RADIUS NAS client."""
        return self._t.request(
            method="GET",
            path=f"/v1/radius_clients/{radius_client_id}",
        )

    def update(
        self, radius_client_id: str, body: m.UpdateRadiusClientBody | None = None
    ) -> m.RadiusClient:
        """Update a RADIUS NAS client's name, NAS-Identifier, source-IP bind, enabled flag or
        shared secret.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/radius_clients/{radius_client_id}",
            body=body,
        )

    def delete(self, radius_client_id: str) -> DeletedObject:
        """Delete a RADIUS NAS client."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/radius_clients/{radius_client_id}",
        )


class RateLimitPolicy:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.RateLimitPolicy:
        """Read the per-instance rate-limit policy (sign-in/up create per IP, and BAPI per key)
        and its bounds.
        """
        return self._t.request(
            method="GET",
            path="/v1/rate_limit_policy",
        )

    def update(self, body: m.UpdateRateLimitPolicyBody | None = None) -> m.RateLimitPolicy:
        """Tune the per-instance rate-limit budgets."""
        return self._t.request(
            method="PATCH",
            path="/v1/rate_limit_policy",
            body=body,
        )


class RedirectUrls:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List the allowlisted OAuth/SSO redirect URLs."""
        return self._t.request(
            method="GET",
            path="/v1/redirect_urls",
        )

    def create(self, body: m.CreateRedirectUrlBody | None = None) -> m.RedirectUrl:
        """Add a permitted OAuth/SSO redirect URL (absolute http(s); idempotent on the URL)."""
        return self._t.request(
            method="POST",
            path="/v1/redirect_urls",
            body=body,
        )

    def get(self, redirect_url_id: str) -> m.RedirectUrl:
        """Fetch one allowlisted redirect URL."""
        return self._t.request(
            method="GET",
            path=f"/v1/redirect_urls/{redirect_url_id}",
        )

    def delete(self, redirect_url_id: str) -> DeletedObject:
        """Remove a redirect URL from the allowlist."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/redirect_urls/{redirect_url_id}",
        )


class RiskBasedMfa:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.RiskBasedMfa:
        """Read the instance's adaptive (risk-based) MFA policy: enabled, step-up threshold,
        no-factor handling, and the signal weights/toggles.
        """
        return self._t.request(
            method="GET",
            path="/v1/risk_based_mfa",
        )

    def update(self, body: m.UpdateRiskBasedMfaBody | None = None) -> m.RiskBasedMfa:
        """Tune adaptive MFA: enable it, set the step-up threshold and the high-risk-no-factor
        policy, and adjust the per-signal weights/toggles.
        """
        return self._t.request(
            method="PATCH",
            path="/v1/risk_based_mfa",
            body=body,
        )


class ScimProvisioningTargets:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List outbound SCIM provisioning targets (downstream SCIM 2.0 endpoints Atlas pushes
        users to).
        """
        return self._t.request(
            method="GET",
            path="/v1/scim_provisioning_targets",
        )

    def create(
        self, body: m.CreateScimProvisioningTargetBody, *, idempotency_key: str | None = None
    ) -> m.ScimProvisioningTarget:
        """Create an outbound SCIM provisioning target."""
        return self._t.request(
            method="POST",
            path="/v1/scim_provisioning_targets",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, target_id: str) -> m.ScimProvisioningTargetGetResult:
        """Read one outbound SCIM provisioning target, including its sync status, cursor and
        last error.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/scim_provisioning_targets/{target_id}",
        )

    def update(
        self, target_id: str, body: m.UpdateScimProvisioningTargetBody | None = None
    ) -> m.ScimProvisioningTargetGetResult:
        """Update a target's name, base_url (https), attribute_mapping, deprovision_action,
        enabled flag, or status (active/paused).
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/scim_provisioning_targets/{target_id}",
            body=body,
        )

    def delete(self, target_id: str) -> DeletedObject:
        """Delete an outbound SCIM provisioning target."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/scim_provisioning_targets/{target_id}",
        )

    def sync_group(self, target_id: str, body: m.SyncScimGroupBody) -> m.ScimSyncResult:
        """Force a single group's (organization's) outbound sync now to the downstream /Groups."""
        return self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{target_id}/sync_group",
            body=body,
        )

    def sync_user(self, target_id: str, body: m.SyncScimUserBody) -> m.ScimSyncResult:
        """Force a single user's outbound sync now (backfill / re-push)."""
        return self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{target_id}/sync_user",
            body=body,
        )

    def test(self, target_id: str) -> m.ScimProvisioningTargetTest:
        """Verify connectivity and auth to the downstream (GET ServiceProviderConfig) with the
        target's real bearer, and return the result.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{target_id}/test",
        )


class SessionExchangeApps:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List registered session-exchange apps (downstream apps that exchange an Atlas
        session for their own) and their back-channel logout endpoints.
        """
        return self._t.request(
            method="GET",
            path="/v1/session_exchange_apps",
        )

    def create(
        self, body: m.CreateSessionExchangeAppBody, *, idempotency_key: str | None = None
    ) -> m.SessionExchangeApp:
        """Register a session-exchange app and its backchannel_logout_uri."""
        return self._t.request(
            method="POST",
            path="/v1/session_exchange_apps",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, app_id: str) -> m.SessionExchangeApp:
        """Fetch one session-exchange app."""
        return self._t.request(
            method="GET",
            path=f"/v1/session_exchange_apps/{app_id}",
        )

    def update(
        self,
        app_id: str,
        body: m.UpdateSessionExchangeAppBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.SessionExchangeApp:
        """Update a session-exchange app's name, backchannel_logout_uri or audience."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/session_exchange_apps/{app_id}",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, app_id: str, *, idempotency_key: str | None = None) -> DeletedObject:
        """Delete a session-exchange app; its queued back-channel logout deliveries cascade
        with it.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/session_exchange_apps/{app_id}",
            idempotency_key=idempotency_key,
        )


class SmsTemplates:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """List SMS templates with their built-in defaults and any instance override."""
        return self._t.request(
            method="GET",
            path="/v1/sms_templates",
        )

    def create(self, body: m.CreateSmsTemplateBody | None = None) -> m.SmsTemplate:
        """Set an SMS body template."""
        return self._t.request(
            method="POST",
            path="/v1/sms_templates",
            body=body,
        )

    def get(self, name: str) -> m.SmsTemplate:
        """Read one SMS template: its built-in default and the instance override."""
        return self._t.request(
            method="GET",
            path=f"/v1/sms_templates/{name}",
        )

    def update(self, name: str, body: m.UpdateSmsTemplateBody | None = None) -> m.SmsTemplate:
        """Update an SMS template body or its enabled flag."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/sms_templates/{name}",
            body=body,
        )

    def delete(self, name: str) -> m.SmsTemplate:
        """Revert an SMS template to the Atlas built-in default body."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/sms_templates/{name}",
        )

    def preview(
        self, name: str, body: m.PreviewSmsTemplateBody | None = None
    ) -> m.SmsTemplatePreview:
        """Render an SMS body with a sample code — never a live OTP — for review."""
        return self._t.request(
            method="POST",
            path=f"/v1/sms_templates/{name}/preview",
            body=body,
        )


class SsoOnboarding:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_profiles(self) -> ListPage:
        """List self-service SSO onboarding profiles (the templates tickets are issued from)."""
        return self._t.request(
            method="GET",
            path="/v1/sso_onboarding_profiles",
        )

    def create_profile(
        self,
        body: m.CreateSsoOnboardingProfileBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.SsoOnboardingProfile:
        """Create a self-service SSO onboarding profile: allowed connection types and an
        optional bound organization.
        """
        return self._t.request(
            method="POST",
            path="/v1/sso_onboarding_profiles",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_profile(self, profile_id: str) -> m.SsoOnboardingProfile:
        """Fetch one onboarding profile."""
        return self._t.request(
            method="GET",
            path=f"/v1/sso_onboarding_profiles/{profile_id}",
        )

    def delete_profile(self, profile_id: str) -> DeletedObject:
        """Delete an onboarding profile; its issued tickets cascade away with it."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/sso_onboarding_profiles/{profile_id}",
        )

    def create_ticket(
        self,
        profile_id: str,
        body: m.CreateSsoOnboardingTicketBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Issue a scoped, one-time, expiring onboarding ticket for one organization."""
        return self._t.request(
            method="POST",
            path=f"/v1/sso_onboarding_profiles/{profile_id}/tickets",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke_ticket(self, ticket_id: str) -> m.SsoOnboardingRevokeTicketResult:
        """Revoke a pending onboarding ticket so it can no longer configure a connection."""
        return self._t.request(
            method="POST",
            path=f"/v1/sso_onboarding_tickets/{ticket_id}/revoke",
        )


class Testing:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create_test_instance(
        self, body: m.CreateTestInstanceBody | None = None, *, idempotency_key: str | None = None
    ) -> m.TestInstance:
        """Get (creating on first call) your production instance's paired test-mode
        (development) sibling — an isolated instance with its own pk_test/sk_test, user pool
        and JWKS.
        """
        return self._t.request(
            method="POST",
            path="/v1/test_instance",
            body=body,
            idempotency_key=idempotency_key,
        )

    def purge_test_users(
        self, body: m.PurgeTestUsersBody | None = None, *, idempotency_key: str | None = None
    ) -> m.TestingPurgeTestUsersResult:
        """Dispose test users in bulk (development instances only): soft-delete every user
        whose email carries a reserved test token (+clerk_test / +atlas_test).
        """
        return self._t.request(
            method="POST",
            path="/v1/test_users/purge",
            body=body,
            idempotency_key=idempotency_key,
        )

    def create_testing_token(self) -> m.TestingToken:
        """Mint a short-lived signed testing token (development instances only) that
        @atlasauth/testing presents to the sign-in gate to skip the human-only CAPTCHA.
        """
        return self._t.request(
            method="POST",
            path="/v1/testing_tokens",
        )


class Tickets:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, body: m.CreateTicketBody) -> m.Ticket:
        """Mint a one-time capability ticket: an opaque, high-entropy handle carrying an
        arbitrary JSON payload a holder can later redeem (e.g. a scoped download grant or
        short-lived action token).
        """
        return self._t.request(
            method="POST",
            path="/v1/tickets",
            body=body,
        )

    def redeem(self, body: m.RedeemTicketBody) -> m.RedeemedTicket:
        """Redeem a capability ticket server-to-server and return its payload."""
        return self._t.request(
            method="POST",
            path="/v1/tickets/redeem",
            body=body,
        )


class Tokens:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def verify(self, body: m.VerifyTokenBody | None = None) -> m.TokenVerification:
        """Authoritatively verify a session token, including revocation."""
        return self._t.request(
            method="POST",
            path="/v1/tokens/verify",
            body=body,
        )


class Usage:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, *, days: int | None = None) -> m.Usage:
        """Read usage analytics: daily sign-in/active-user series with peaks and trends over a
        window, plus monthly active users.
        """
        return self._t.request(
            method="GET",
            path="/v1/usage",
            query=_q(days=days),
        )


class UserExports:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(self, *, idempotency_key: str | None = None) -> m.Job:
        """Produce a job whose result is a present()-serialised array of the instance's users."""
        return self._t.request(
            method="POST",
            path="/v1/user_exports",
            idempotency_key=idempotency_key,
        )


class UserImports:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateUserImportBody | None = None, *, idempotency_key: str | None = None
    ) -> m.Job:
        """Bulk-create users from an array, deduping by verified email, through the same path
        sign-up uses.
        """
        return self._t.request(
            method="POST",
            path="/v1/user_imports",
            body=body,
            idempotency_key=idempotency_key,
        )


class PlatformApps:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        tag: str | None = None,
        archived: bool | None = None,
        include_archived: bool | None = None,
    ) -> ListPage:
        """List the apps (instances) this platform owns."""
        return self._t.request(
            method="GET",
            path="/v1/platform/apps",
            query=_q(tag=tag, archived=archived, include_archived=include_archived),
        )

    def create(
        self, body: m.CreatePlatformAppBody | None = None, *, idempotency_key: str | None = None
    ) -> m.PlatformAppProvisioned:
        """Provision a new app (instance) owned by the platform: mints its publishable key,
        signing key and first secret key.
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/apps",
            body=body,
            idempotency_key=idempotency_key,
        )

    def accept_transfer(
        self,
        body: m.AcceptPlatformAppTransferBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Accept a transfer by transfer_token: move the app's ownership to the calling
        platform and re-parent it to its account.
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/apps/accept_transfer",
            body=body,
            idempotency_key=idempotency_key,
        )

    def bulk_delete(self, body: m.BulkDeletePlatformAppsBody | None = None) -> m.BulkDeleteResult:
        """X8 housekeeping: delete up to 100 owned apps in one call, for tidying throwaway
        probes.
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/apps/bulk_delete",
            body=body,
        )

    def claim(
        self, body: m.ClaimPlatformAppBody | None = None, *, idempotency_key: str | None = None
    ) -> JSON:
        """Claim an accountless app into the calling platform by its claim_token."""
        return self._t.request(
            method="POST",
            path="/v1/platform/apps/claim",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, app_id: str) -> m.App:
        """Disable an owned app: refuse sign-ins and sign-ups via its kill switches."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/platform/apps/{app_id}",
        )

    def get(self, app_id: str) -> m.PlatformApp:
        """Fetch one owned app."""
        return self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{app_id}",
        )

    def update(self, app_id: str, body: m.UpdatePlatformAppBody | None = None) -> m.PlatformApp:
        """Update an owned app's safe config subset (name, allowed_origins, and X8 housekeeping
        tags).
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/platform/apps/{app_id}",
            body=body,
        )

    def archive(self, app_id: str) -> m.PlatformApp:
        """X8 housekeeping: archive an owned app so it drops out of the default app listing."""
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/archive",
        )

    def list_instances(self, app_id: str) -> ListPage:
        """List every instance under an owned app — its development/production siblings."""
        return self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{app_id}/instances",
        )

    def create_instance(
        self,
        app_id: str,
        body: m.CreatePlatformAppInstanceBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PlatformAppWithSecret:
        """Provision an additional instance (e.g. development beside production) under an owned
        app.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/instances",
            body=body,
            idempotency_key=idempotency_key,
        )

    def rotate_instance_secret(
        self, app_id: str, instance_id: str, *, idempotency_key: str | None = None
    ) -> m.AppSecret:
        """Rotate one specific instance's secret under an owned app: revoke its prior keys and
        mint a new one, revealed once.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/instances/{instance_id}/rotate_secret",
            idempotency_key=idempotency_key,
        )

    def rotate_secret(
        self,
        app_id: str,
        body: m.RotatePlatformAppSecretBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PlatformAppRotateSecretResult:
        """Rotate an owned app's secret key WITH OVERLAP (S3): mint a new sk_ (revealed exactly
        once) while the prior keys stay valid for a grace window so servers roll over
        without downtime.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/rotate_secret",
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_secret_keys(self, app_id: str) -> ListPage:
        """List an owned app's currently-valid secret keys (S3) — the primary key plus any
        prior key still inside its rotation overlap window.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{app_id}/secret_keys",
        )

    def transfer(self, app_id: str, *, idempotency_key: str | None = None) -> m.AppTransfer:
        """Initiate a transfer of an owned app: returns a one-time transfer_token bound to it
        (hashed, single-use, expiring).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/transfer",
            idempotency_key=idempotency_key,
        )

    def unarchive(self, app_id: str) -> m.PlatformApp:
        """X8 housekeeping: clear an owned app's archive flag, returning it to the default app
        listing.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/unarchive",
        )


class PlatformAccountlessApps:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self, body: m.CreateAccountlessAppBody | None = None, *, idempotency_key: str | None = None
    ) -> m.AccountlessApp:
        """Mint an app owned by no platform and return a one-time claim_token (hashed at rest,
        single-use, expiring).
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/accountless_apps",
            body=body,
            idempotency_key=idempotency_key,
        )


class PlatformAtlasIdApps:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> m.AtlasIdAppList:
        """List the Sign in with Atlas apps registered to this platform's account, with the
        issuer and discovery URL.
        """
        return self._t.request(
            method="GET",
            path="/v1/platform/atlas_id_apps",
        )

    def create(
        self, body: m.CreateAtlasIdAppBody | None = None, *, idempotency_key: str | None = None
    ) -> m.AtlasIdApp:
        """Register a Sign in with Atlas app (an OpenID Connect client on
        https://atlasauth.net) for this platform's account.
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/atlas_id_apps",
            body=body,
            idempotency_key=idempotency_key,
        )

    def preview_design(self, body: m.PreviewDesignBody) -> m.DesignPreview:
        """Preview a Sign in with Atlas app design without saving it: the compiled bundle plus
        the rendered Sign in with Atlas page (the Atlas trust strip, the destination line
        and "Secured by Atlas" are always there).
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/atlas_id_apps/design/preview",
            body=body,
        )

    def delete(self, app_id: str) -> DeletedObject:
        """Delete a Sign in with Atlas app."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{app_id}",
        )

    def get(self, app_id: str) -> m.AtlasIdApp:
        """Fetch one Sign in with Atlas app, including user_count (people who have approved
        it).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}",
        )

    def update(self, app_id: str, body: m.UpdateAtlasIdAppBody | None = None) -> m.AtlasIdApp:
        """Update a Sign in with Atlas app: name, redirect_uris, post_logout_redirect_uris ([]
        clears them), backchannel_logout_uri / frontchannel_logout_uri (empty or null
        clears) and their *_session_required flags,...
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/platform/atlas_id_apps/{app_id}",
            body=body,
        )

    def rotate_secret(self, app_id: str) -> m.AtlasIdApp:
        """Rotate a confidential app's client_secret."""
        return self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/rotate_secret",
        )


class PlatformDesignAssets:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def upload(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        kind: Literal["background", "logo"] | None = None,
    ) -> m.DesignAsset:
        """Upload a design image owned by the platform's account, for Sign in with Atlas app
        designs.
        """
        return self._t.request(
            method="POST",
            path="/v1/platform/design/assets",
            query=_q(kind=kind),
            content=data,
            content_type=content_type or _sniff_image_type(data),
        )

    def list(self) -> ListPage:
        """List the design images owned by the platform's account, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/platform/design/assets",
        )

    def delete(self, asset_id: str) -> m.DesignAssetDeleteResult:
        """Delete a design image owned by the platform's account."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/platform/design/assets/{asset_id}",
        )
