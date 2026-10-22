"""Asynchronous resource namespaces — the async peer of :mod:`resources`.

Same method↔endpoint map, same shapes, over an :class:`httpx.AsyncClient`.
Generated from :mod:`resources` by ``scripts/gen_async.py``; edit the sync
module and regenerate rather than editing this file.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from . import models as m
from ._transport import _AsyncTransport
from ._types import JSON, CursorPage, DeletedObject, ListPage
from .resources import _csv, _json, _q, _sniff_image_type


class AsyncUsers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.identities = _AsyncUserIdentities(transport)
        self.phone_numbers = _AsyncUserPhoneNumbers(transport)
        self.consents = _AsyncUserConsents(transport)
        self.deletion = _AsyncUserDeletion(transport)
        self.directives = _AsyncUserDirectives(transport)
        self.approval_requests = _AsyncUserApprovalRequests(transport)
        self.grants = _AsyncUserGrants(transport)
        self.erasure = _AsyncUserErasure(transport)
        self.notification_preferences = _AsyncUserNotificationPreferences(transport)

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        return await self._t.request(
            method="GET",
            path="/v1/users",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(self, user_id: str, *, include_deleted: bool | None = None) -> m.User:
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}",
            query=_q(include_deleted=include_deleted),
        )

    async def create(self, body: m.CreateUserBody, *, idempotency_key: str | None = None) -> m.User:
        return await self._t.request(
            method="POST", path="/v1/users", body=body, idempotency_key=idempotency_key
        )

    async def update(self, user_id: str, body: m.UpdateUserBody) -> m.User:
        return await self._t.request(method="PATCH", path=f"/v1/users/{user_id}", body=body)

    async def set_external_id(self, user_id: str, external_id: str | None) -> m.User:
        """Set (or clear with ``None``) the user's ``external_id``. With referral
        attribution on, Atlas forwards the change to the referral platform as an alias
        (old id, or the Atlas user id, to the new one), so later events under your id
        still match.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/users/{user_id}",
            body={"external_id": external_id},
        )

    async def replace_metadata(self, user_id: str, body: m.ReplaceUserMetadataBody) -> m.User:
        return await self._t.request(method="PUT", path=f"/v1/users/{user_id}/metadata", body=body)

    async def ban(
        self,
        user_id: str,
        *,
        reason: str | None = None,
        note: str | None = None,
        idempotency_key: str | None = None,
    ) -> m.User:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/ban",
            body=_q(reason=reason, note=note) or None,
            idempotency_key=idempotency_key,
        )

    async def unban(self, user_id: str) -> m.User:
        return await self._t.request(method="POST", path=f"/v1/users/{user_id}/unban")

    async def lock(self, user_id: str, *, duration_in_seconds: int | None = None) -> m.User:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/lock",
            body=_q(duration_in_seconds=duration_in_seconds),
        )

    async def unlock(self, user_id: str) -> m.User:
        return await self._t.request(method="POST", path=f"/v1/users/{user_id}/unlock")

    async def flag_referral(
        self,
        user_id: str,
        *,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> m.UserReferralFlag:
        """Mark the user's referral fraudulent. The referral reads ``flagged``, the
        referral platform is sent a ``fraud_confirmed`` signal (when referrals are on) and
        the action is audited; the account is not changed. 404 when the user has no
        referral. ``reason`` (at most 500 characters) is sent to the platform.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/referral/flag",
            body=_q(reason=reason),
            idempotency_key=idempotency_key,
        )

    async def delete(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}",
            body=body or None,
            idempotency_key=idempotency_key,
        )

    async def reset_mfa(self, user_id: str) -> JSON:
        return await self._t.request(method="POST", path=f"/v1/users/{user_id}/reset_mfa")

    async def delete_mfa_factor(self, user_id: str, factor_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/users/{user_id}/mfa/{factor_id}")

    async def list_sessions(self, user_id: str) -> ListPage:
        """List a user's sessions. Each ``data`` item is a :class:`~atlas_backend.models.Session`
        (with ``idle_expires_at``, ``last_active_organization_id`` and ``impersonated_by``).
        """
        return await self._t.request(method="GET", path=f"/v1/users/{user_id}/sessions")

    async def revoke_sessions(
        self,
        user_id: str,
        *,
        all: bool | None = None,
        revoke_grants: bool | None = None,
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/sessions/revoke",
            body=_q(all=all, revoke_grants=revoke_grants) or None,
        )

    async def add_email(self, user_id: str, email_address: str) -> m.EmailAddress:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses",
            body={"email_address": email_address},
        )

    async def verify_email(self, user_id: str, email_id: str) -> m.EmailAddress:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses/{email_id}/verify",
        )

    async def set_primary_email(self, user_id: str, email_id: str) -> m.EmailAddress:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses/{email_id}/primary",
        )

    async def get_oauth_access_token(self, user_id: str, provider: str) -> m.OAuthAccessToken:
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/oauth_access_tokens/{provider}",
        )

    async def get_by_emails(self, body: m.UsersByEmailsBody) -> ListPage:
        """Resolve a batch of email addresses to user ids in one call."""
        return await self._t.request(
            method="POST",
            path="/v1/users/by_emails",
            body=body,
        )

    async def connect_external_account(
        self, user_id: str, body: m.ConnectExternalAccountBody | None = None
    ) -> m.UserConnectExternalAccountResult:
        """Backend-initiated connect: start an OAuth flow that links a NEW provider identity to
        this user (the caller supplies the user id).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/external_accounts/connect",
            body=body,
        )

    async def list_organization_memberships(
        self, user_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        """List the organizations a user belongs to with each membership's role, the org's
        resolved plan, and the join time.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/organization_memberships",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def delete_passkey(
        self, user_id: str, passkey_id: str, *, idempotency_key: str | None = None
    ) -> DeletedObject:
        """Remove one of a user’s passkeys."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/passkeys/{passkey_id}",
            idempotency_key=idempotency_key,
        )

    async def set_password(
        self, user_id: str, body: m.SetUserPasswordBody, *, idempotency_key: str | None = None
    ) -> m.User:
        """Set (reset) a user's password from the backend."""
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/password",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_profile_image(
        self, user_id: str, *, idempotency_key: str | None = None
    ) -> m.User:
        """Clear a user’s profile image."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/profile_image",
            idempotency_key=idempotency_key,
        )

    async def record_progression_event(
        self,
        user_id: str,
        body: m.ProgressionEventBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.ProgressionEvent:
        """Append an idempotent progression event (XP / level / state) for a user, scoped to
        the calling source.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/progression/events",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_resolved(self, user_id: str) -> m.ResolvedUser:
        """Resolve a user to a FLAT identity in one call: the real primary email (never the
        @no-email.invalid placeholder), email_verified, name, image_url, and the linked
        provider identities (provider + provider_user_id).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/resolved",
        )

    async def sign_in_history(
        self, user_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        """A user's successful sign-ins, newest first, keyset-paginated."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/sign_in_history",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get_state(self, user_id: str) -> m.UserState:
        """Read a user's portable state — progression, tier, flair, entitlements, directives
        and roles.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/state",
        )


class _AsyncOrgMemberships:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self, org_id: str, *, limit: int | None = None, offset: int | None = None
    ) -> JSON:
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/memberships",
            query=_q(limit=limit, offset=offset),
        )

    async def add(
        self,
        org_id: str,
        body: m.AddMembershipBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/memberships",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(self, org_id: str, user_id: str, role: str) -> JSON:
        return await self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/memberships/{user_id}",
            body={"role": role},
        )

    async def remove(self, org_id: str, user_id: str) -> JSON:
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/memberships/{user_id}",
        )


class _AsyncOrgInvitations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, org_id: str) -> ListPage:
        return await self._t.request(method="GET", path=f"/v1/organizations/{org_id}/invitations")

    async def create(
        self,
        org_id: str,
        body: m.CreateOrgInvitationBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/invitations",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(self, org_id: str, invitation_id: str) -> JSON:
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/invitations/{invitation_id}/revoke",
        )


class _AsyncOrgDomains:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, org_id: str) -> JSON:
        return await self._t.request(method="GET", path=f"/v1/organizations/{org_id}/domains")

    async def create(
        self,
        org_id: str,
        body: m.CreateOrgDomainBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgDomain:
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/domains",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verify(self, org_id: str, domain_id: str) -> m.OrgDomain:
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/domains/{domain_id}/verify",
        )

    async def delete(self, org_id: str, domain_id: str) -> JSON:
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/domains/{domain_id}",
        )


class _AsyncOrgGroupRoles:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def grant(self, org_id: str, group_id: str, role_id: str) -> JSON:
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/groups/{group_id}/roles/{role_id}",
        )

    async def revoke(self, org_id: str, group_id: str, role_id: str) -> JSON:
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/groups/{group_id}/roles/{role_id}",
        )


class AsyncOrganizations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.memberships = _AsyncOrgMemberships(transport)
        self.invitations = _AsyncOrgInvitations(transport)
        self.domains = _AsyncOrgDomains(transport)
        self.group_roles = _AsyncOrgGroupRoles(transport)
        self.audit_streams = _AsyncOrgAuditStreams(transport)
        self.design = _AsyncOrgDesign(transport)
        self.settings = _AsyncOrgSettings(transport)
        self.end_users = _AsyncOrgEndUsers(transport)
        self.reader_domain = _AsyncOrgReaderDomain(transport)
        self.branding = _AsyncOrgBranding(transport)

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        return await self._t.request(
            method="GET",
            path="/v1/organizations",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(self, org_id: str) -> m.Organization:
        return await self._t.request(method="GET", path=f"/v1/organizations/{org_id}")

    async def create(
        self,
        body: m.CreateOrganizationBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.Organization:
        return await self._t.request(
            method="POST",
            path="/v1/organizations",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(self, org_id: str, body: m.UpdateOrganizationBody) -> m.Organization:
        return await self._t.request(method="PATCH", path=f"/v1/organizations/{org_id}", body=body)

    async def delete(self, org_id: str) -> DeletedObject:
        return await self._t.request(method="DELETE", path=f"/v1/organizations/{org_id}")

    async def update_metadata(
        self, org_id: str, body: m.ReplaceOrganizationMetadataBody
    ) -> m.Organization:
        return await self._t.request(
            method="PUT", path=f"/v1/organizations/{org_id}/metadata", body=body
        )

    async def update_policy(
        self, org_id: str, body: m.OrganizationPolicyPatch | dict[str, Any]
    ) -> JSON:
        """Patch an organization's policy (camelCase keys; ``None`` clears an override)."""
        return await self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/policy", body=body
        )

    async def get_entitlements(self, org_id: str) -> m.OrganizationEntitlements:
        """The organization’s effective entitlement — resolved plan, feature keys and numeric
        limits, with sales-led overrides applied and plan limits merged.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/entitlements",
        )

    async def get_hierarchy(self, org_id: str) -> m.OrganizationHierarchy:
        """The organization’s ancestor chain and direct children in the B2B2B hierarchy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/hierarchy",
        )

    async def set_parent(
        self, org_id: str, body: m.SetOrganizationParentBody | None = None
    ) -> m.Organization:
        """Set or clear (null) an organization’s parent in the B2B2B hierarchy; refuses a
        cycle.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/parent",
            body=body,
        )


class AsyncSessions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, user_id: str) -> ListPage:
        """List a user's sessions. Each ``data`` item is a
        :class:`~atlas_backend.models.Session`.
        """
        return await self._t.request(method="GET", path="/v1/sessions", query={"user_id": user_id})

    async def get(self, session_id: str) -> m.Session:
        return await self._t.request(method="GET", path=f"/v1/sessions/{session_id}")

    async def revoke(self, session_id: str) -> JSON:
        return await self._t.request(method="POST", path=f"/v1/sessions/{session_id}/revoke")

    async def create(self, body: m.CreateSessionBody) -> m.SessionCreated:
        """Establish a session for a user in one call — returns jwt + refresh_token, audited as
        a first-party sign-in (not impersonation unless actor.sub is set).
        """
        return await self._t.request(
            method="POST",
            path="/v1/sessions",
            body=body,
        )

    async def touch(self, session_id: str) -> m.TouchedSession:
        """Keep a session alive from your backend: slides its inactivity window as if the
        user had just loaded a page. Never extends past the absolute expiry and never
        revives an ended session (409 SESSION_REVOKED / SESSION_IDLE_EXPIRED /
        SESSION_EXPIRED). At most one effective write per minute, so calling it on every
        request is safe.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/sessions/{session_id}/touch",
        )

    async def create_token(self, session_id: str, template: str) -> m.SessionToken:
        """Mint a named JWT-template token for a session."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sessions/{session_id}/tokens/{template}",
        )


class AsyncInvitations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        return await self._t.request(
            method="GET",
            path="/v1/invitations",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.CreateInvitationBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.Invitation:
        return await self._t.request(
            method="POST",
            path="/v1/invitations",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(self, invitation_id: str) -> m.Invitation:
        return await self._t.request(method="POST", path=f"/v1/invitations/{invitation_id}/revoke")

    async def bulk_create(self, body: m.BulkCreateInvitationsBody | None = None) -> ListPage:
        """Bulk-create instance invitations (≤100)."""
        return await self._t.request(
            method="POST",
            path="/v1/invitations/bulk",
            body=body,
        )


class AsyncRoles:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/roles")

    async def create(self, body: m.CreateRoleBody, *, idempotency_key: str | None = None) -> m.Role:
        return await self._t.request(
            method="POST", path="/v1/roles", body=body, idempotency_key=idempotency_key
        )

    async def update(self, role_id: str, body: m.UpdateRoleBody) -> m.Role:
        return await self._t.request(method="PATCH", path=f"/v1/roles/{role_id}", body=body)

    async def set_permissions(self, role_id: str, permissions: Sequence[str]) -> JSON:
        return await self._t.request(
            method="PUT",
            path=f"/v1/roles/{role_id}/permissions",
            body={"permissions": permissions},
        )

    async def delete(self, role_id: str, *, reassign_to: str | None = None) -> JSON:
        """Delete a role; ``reassign_to`` moves its members to another role first."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/roles/{role_id}",
            query=_q(reassign_to=reassign_to),
        )


class AsyncPermissions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/permissions")

    async def create(
        self, body: m.CreatePermissionBody, *, idempotency_key: str | None = None
    ) -> m.Permission:
        return await self._t.request(
            method="POST",
            path="/v1/permissions",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, permission_id: str) -> DeletedObject:
        """Delete a permission; it is removed from every role that held it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/permissions/{permission_id}",
        )

    async def update(
        self, permission_id: str, body: m.UpdatePermissionBody | None = None
    ) -> m.Permission:
        """Update a permission’s description or metadata."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/permissions/{permission_id}",
            body=body,
        )


class _AsyncWebhookEndpoints:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/webhook_endpoints")

    async def create(
        self,
        body: m.CreateWebhookEndpointBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path="/v1/webhook_endpoints",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, endpoint_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/webhook_endpoints/{endpoint_id}")

    async def list_deliveries(self, endpoint_id: str, *, limit: int | None = None) -> ListPage:
        """List an endpoint's recent deliveries, newest first (``limit`` 1-100)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries",
            query=_q(limit=limit),
        )

    async def update(
        self, endpoint_id: str, body: m.UpdateWebhookEndpointBody | None = None
    ) -> m.WebhookEndpoint:
        """Update an endpoint’s url, enabled_events, or active flag in place."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/webhook_endpoints/{endpoint_id}",
            body=body,
        )

    async def redeliver(self, endpoint_id: str, delivery_id: str) -> m.WebhookDeliveryAttempt:
        """Manually redeliver a past event as a fresh attempt."""
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries/{delivery_id}/redeliver",
        )

    async def reveal_secret(self, endpoint_id: str) -> m.WebhookSecret:
        """Show the endpoint's current signing secret again (for a verifier that lost it)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/reveal_secret",
        )

    async def rotate_secret(
        self, endpoint_id: str, body: m.RotateWebhookSecretBody | None = None
    ) -> m.WebhookSecretRotation:
        """Rotate the endpoint signing secret; the new one is revealed exactly once. By
        default the old secret stops signing at once. With ``overlap_seconds`` (at most
        604800) every delivery is signed with both, so a verifier holding either passes.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/rotate_secret",
            body=body,
        )

    async def test(self, endpoint_id: str) -> m.WebhookDeliveryAttempt:
        """Send a synthetic webhook.test event to this endpoint only."""
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/test",
        )


class AsyncWebhooks:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.endpoints = _AsyncWebhookEndpoints(transport)

    async def deliveries(self, endpoint_id: str, *, limit: int | None = None) -> JSON:
        """List an endpoint's deliveries. Same as ``endpoints.list_deliveries``."""
        return await self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries",
            query=_q(limit=limit),
        )


class _AsyncOAuthClientGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, client_id: str) -> ListPage:
        return await self._t.request(method="GET", path=f"/v1/oauth_clients/{client_id}/grants")

    async def create(self, client_id: str, body: m.CreateGrantBody) -> m.ClientGrant:
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{client_id}/grants",
            body=body,
        )

    async def delete(self, client_id: str, grant_id: str) -> JSON:
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{client_id}/grants/{grant_id}",
        )


class AsyncOAuthClients:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.grants = _AsyncOAuthClientGrants(transport)

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/oauth_clients")

    async def get(self, client_id: str) -> m.OAuthClient:
        return await self._t.request(method="GET", path=f"/v1/oauth_clients/{client_id}")

    async def create(
        self,
        body: m.CreateOAuthClientBody,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path="/v1/oauth_clients",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(self, client_id: str, body: m.UpdateOAuthClientBody) -> m.OAuthClient:
        return await self._t.request(
            method="PATCH", path=f"/v1/oauth_clients/{client_id}", body=body
        )

    async def rotate_secret(
        self,
        client_id: str,
        body: m.RotateOAuthClientSecretBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OAuthClientSecretRotation:
        """Mint a new secret (shown once). The previous one keeps working for
        ``overlap_seconds`` (default 86400 = 24 hours, at most 604800 = 7 days; ``0`` revokes
        it now). ``previous_secret_expires_at`` says when it stops working.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{client_id}/rotate_secret",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_backchannel_deliveries(
        self, client_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> m.BackchannelLogoutDeliveryList:
        """The client's back-channel logout delivery log, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{client_id}/backchannel_deliveries",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def test_backchannel_logout(self, client_id: str) -> m.BackchannelLogoutTest:
        """Send a test back-channel logout now and return what the receiver answered."""
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{client_id}/backchannel_logout/test",
        )

    async def delete(self, client_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/oauth_clients/{client_id}")

    async def import_clients(
        self, body: m.ImportOAuthClientsBody, *, idempotency_key: str | None = None
    ) -> ListPage:
        """Bulk-import OAuth clients for a migration, optionally with a pre-hashed client
        secret.
        """
        return await self._t.request(
            method="POST",
            path="/v1/oauth_clients/import",
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncResourceServers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/resource_servers")

    async def get(self, server_id: str) -> m.ResourceServer:
        return await self._t.request(method="GET", path=f"/v1/resource_servers/{server_id}")

    async def create(self, body: m.CreateResourceServerBody) -> m.ResourceServer:
        return await self._t.request(method="POST", path="/v1/resource_servers", body=body)

    async def update(self, server_id: str, body: m.UpdateResourceServerBody) -> m.ResourceServer:
        return await self._t.request(
            method="PATCH", path=f"/v1/resource_servers/{server_id}", body=body
        )

    async def delete(self, server_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/resource_servers/{server_id}")


class AsyncSsoConnections:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, organization_id: str | None = None) -> ListPage:
        return await self._t.request(
            method="GET",
            path="/v1/sso_connections",
            query=_q(organization_id=organization_id),
        )

    async def get(self, connection_id: str) -> m.SsoConnection:
        return await self._t.request(method="GET", path=f"/v1/sso_connections/{connection_id}")

    async def create(
        self,
        body: m.CreateSsoConnectionBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.SsoConnection:
        return await self._t.request(
            method="POST",
            path="/v1/sso_connections",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(self, connection_id: str, body: m.UpdateSsoConnectionBody) -> m.SsoConnection:
        return await self._t.request(
            method="PATCH", path=f"/v1/sso_connections/{connection_id}", body=body
        )

    async def delete(self, connection_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/sso_connections/{connection_id}")

    async def saml_metadata(self, connection_id: str) -> m.SamlMetadata:
        return await self._t.request(
            method="GET",
            path=f"/v1/sso_connections/{connection_id}/saml_metadata",
        )


class AsyncScimTokens:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, organization_id: str | None = None) -> ListPage:
        return await self._t.request(
            method="GET",
            path="/v1/scim_tokens",
            query=_q(organization_id=organization_id),
        )

    async def create(
        self, body: m.CreateScimTokenBody, *, idempotency_key: str | None = None
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path="/v1/scim_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(self, token_id: str) -> JSON:
        return await self._t.request(method="POST", path=f"/v1/scim_tokens/{token_id}/revoke")


class AsyncDomains:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/domains")

    async def create(self, body: m.CreateDomainBody, *, idempotency_key: str | None = None) -> JSON:
        return await self._t.request(
            method="POST",
            path="/v1/domains",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verify(self, domain_id: str) -> JSON:
        return await self._t.request(method="POST", path=f"/v1/domains/{domain_id}/verify")

    async def delete(self, domain_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/domains/{domain_id}")


class AsyncWaitlist:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        status: str | None = None,
        query: str | None = None,
    ) -> JSON:
        return await self._t.request(
            method="GET",
            path="/v1/waitlist_entries",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                status=status,
                query=query,
            ),
        )

    async def decide(self, entry_id: str, body: m.DecideWaitlistBody) -> m.WaitlistEntry:
        return await self._t.request(
            method="POST",
            path=f"/v1/waitlist_entries/{entry_id}/decide",
            body=body,
        )

    async def create(self, body: m.CreateWaitlistEntryBody | None = None) -> m.WaitlistEntry:
        """Admin-create a waitlist entry (idempotent on address)."""
        return await self._t.request(
            method="POST",
            path="/v1/waitlist_entries",
            body=body,
        )

    async def bulk_create(self, body: m.BulkCreateWaitlistEntriesBody | None = None) -> ListPage:
        """Bulk-create waitlist entries (≤100 addresses); per-entry errors returned."""
        return await self._t.request(
            method="POST",
            path="/v1/waitlist_entries/bulk",
            body=body,
        )

    async def delete(self, entry_id: str) -> DeletedObject:
        """Delete a waitlist entry."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/waitlist_entries/{entry_id}",
        )


class _AsyncRestriction:
    """Allowlist and blocklist share an identical route shape."""

    def __init__(self, transport: _AsyncTransport, path: str) -> None:
        self._t = transport
        self._path = path

    async def list(self) -> JSON:
        return await self._t.request(method="GET", path=self._path)

    async def add(self, identifier: str) -> JSON:
        return await self._t.request(
            method="POST", path=self._path, body={"identifier": identifier}
        )

    async def remove(self, identifier_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"{self._path}/{identifier_id}")


class AsyncAttackProtection:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.AttackProtection:
        return await self._t.request(method="GET", path="/v1/attack_protection")

    async def update(self, body: m.UpdateAttackProtectionBody) -> m.AttackProtection:
        return await self._t.request(method="PATCH", path="/v1/attack_protection", body=body)


class AsyncActorTokens:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateActorTokenBody, *, idempotency_key: str | None = None
    ) -> m.ActorToken:
        return await self._t.request(
            method="POST",
            path="/v1/actor_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(self, token_id: str) -> JSON:
        return await self._t.request(method="POST", path=f"/v1/actor_tokens/{token_id}/revoke")


class AsyncSignInTokens:
    """The ``/v1/sign_in_tokens`` resource.

    .. deprecated::
        ``POST /v1/sign_in_tokens`` is deprecated (Sunset 2026-04-01). Use
        ``AsyncSessions.create`` (``POST /v1/sessions``), which mints a real
        redeemable session in one call.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateSignInTokenBody, *, idempotency_key: str | None = None
    ) -> m.SignInToken:
        return await self._t.request(
            method="POST",
            path="/v1/sign_in_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(self, token_id: str) -> m.SignInTokenRevokeResult:
        """DEPRECATED (Sunset 2027-04-01) — revoke an unused sign-in token before its 60s
        window elapses.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/sign_in_tokens/{token_id}/revoke",
        )


class AsyncAuditLogs:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        actor_id: str | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> CursorPage:
        return await self._t.request(
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


class AsyncJwtTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/jwt_templates")

    async def get(self, name: str) -> m.JwtTemplate:
        return await self._t.request(method="GET", path=f"/v1/jwt_templates/{name}")

    async def create(self, body: m.CreateJwtTemplateBody) -> m.JwtTemplate:
        return await self._t.request(method="POST", path="/v1/jwt_templates", body=body)

    async def update(self, name: str, claims: dict[str, str]) -> m.JwtTemplate:
        return await self._t.request(
            method="PATCH",
            path=f"/v1/jwt_templates/{name}",
            body={"claims": claims},
        )

    async def delete(self, name: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/jwt_templates/{name}")


class _AsyncUserIdentities:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, user_id: str) -> ListPage:
        """List a user's linked identities: their Atlas email/password identity plus each
        linked external/OAuth provider account.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/identities",
        )

    async def link(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/identities",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def unlink_provider(
        self, user_id: str, provider: str, *, idempotency_key: str | None = None
    ) -> m.IdentityUnlinkProviderResult:
        """Hard-remove a provider identity from a user (undo a mis-import)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/identities/by-provider/{provider}",
            idempotency_key=idempotency_key,
        )

    async def import_identity(
        self,
        user_id: str,
        body: m.ImportIdentityBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.Identity:
        """Import a KNOWN provider identity (migration) without an interactive OAuth flow —
        link { provider, provider_user_id, email_address?, verified?
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/identities/import",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def unlink(
        self, user_id: str, identity_id: str, *, idempotency_key: str | None = None
    ) -> m.IdentityUnlinkResult:
        """Unlink a provider identity, extracting it into a new standalone user."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/identities/{identity_id}",
            idempotency_key=idempotency_key,
        )


class _AsyncUserPhoneNumbers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def add(
        self,
        user_id: str,
        body: m.AddPhoneNumberBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PhoneNumber:
        """Add a phone number to a user."""
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/phone_numbers",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self, user_id: str, phone_number_id: str, *, idempotency_key: str | None = None
    ) -> DeletedObject:
        """Remove a phone number from a user."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/phone_numbers/{phone_number_id}",
            idempotency_key=idempotency_key,
        )

    async def verify(
        self, user_id: str, phone_number_id: str, *, idempotency_key: str | None = None
    ) -> m.PhoneNumber:
        """Mark a phone number verified on the backend authority."""
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/phone_numbers/{phone_number_id}/verify",
            idempotency_key=idempotency_key,
        )


class _AsyncUserConsents:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def record(
        self,
        user_id: str,
        body: m.RecordConsentBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.Consent:
        """Record a versioned consent grant (or withdrawal, `status: "withdrawn"`) for a user."""
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/consents",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(self, user_id: str) -> ListPage:
        """List a user's recorded consents with their versions and timestamps."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/consents",
        )


class _AsyncUserDeletion:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def schedule(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/deletion",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def cancel(self, user_id: str, *, idempotency_key: str | None = None) -> m.User:
        """Cancel a scheduled deletion inside its grace window, aborting the purge so the
        account is NOT erased; emits user.deletion_canceled.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/deletion/cancel",
            idempotency_key=idempotency_key,
        )

    async def finalize(self, user_id: str, *, idempotency_key: str | None = None) -> DeletedObject:
        """Finalize a scheduled deletion whose grace window has lapsed — the idempotent purge
        trigger the worker calls on schedule (a cron/operator may too).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/deletion/finalize",
            idempotency_key=idempotency_key,
        )


class _AsyncUserDirectives:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def set(
        self,
        user_id: str,
        body: m.SetUserDirectiveBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.Directive:
        """Impose a cross-property directive on a user (e.g. suspended_until / read_only /
        forced_logout).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/directives",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def lift(self, user_id: str) -> m.DirectiveLiftResult:
        """Lift a previously imposed directive from a user."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/directives",
        )


class _AsyncUserApprovalRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, user_id: str, body: m.CreateApprovalRequestBody
    ) -> m.ApprovalRequestCreated:
        """Request a transaction approval from a user: push a number-matching "approve this
        action" prompt (carrying a human-readable description and optional context) to the
        user's registered push devices.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/approval_requests",
            body=body,
        )

    async def get(self, user_id: str, approval_id: str) -> m.ApprovalRequest:
        """Poll a transaction-approval request: pending | approved | denied | expired, with the
        approving device and resolution timestamp.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/approval_requests/{approval_id}",
        )


class _AsyncUserGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, user_id: str) -> ListPage:
        """List the OAuth clients a user has authorized, with the granted scopes and grant
        time.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/grants",
        )

    async def revoke_all(
        self, user_id: str, *, idempotency_key: str | None = None
    ) -> m.UserGrantRevokeAllResult:
        """Revoke every consent grant a user holds and cascade-revoke all associated tokens
        through the standard revocation path.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{user_id}/grants",
            idempotency_key=idempotency_key,
        )


class _AsyncUserErasure:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def acknowledge(
        self, user_id: str, body: m.CreateErasureAckBody, *, idempotency_key: str | None = None
    ) -> m.UserErasureAck:
        """An integrating app acknowledges it has purged its copy of the user data during a
        scheduled deletion, identified by source (or the app_id alias), and may contribute a
        JSON payload Atlas folds into the DSAR erasure export.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/erasure_acks",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def export(self, user_id: str) -> m.UserErasureExport:
        """The DSAR erasure export: Atlas's own data about the subject (the same no-secret
        bundle the self-service export produces) PLUS every app's contributed blob from its
        erasure ack, aggregated into one package.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/erasure_export",
        )


class _AsyncUserNotificationPreferences:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, user_id: str) -> m.NotificationPreferences:
        """Read an end-user's security-notification preferences: every category with whether it
        is enabled and whether it is optional (security-critical categories are non-optional
        and always enabled).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/notification_preferences",
        )

    async def update(
        self, user_id: str, body: m.UpdateNotificationPreferencesBody
    ) -> m.NotificationPreferences:
        """Change an end-user's security-notification preferences with a { preferences: {
        category: enabled } } patch.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/users/{user_id}/notification_preferences",
            body=body,
        )


class _AsyncOrgAuditStreams:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, org_id: str) -> ListPage:
        """List an organization's registered audit stream destinations."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/audit_streams",
        )

    async def create(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/audit_streams",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, org_id: str, stream_id: str) -> DeletedObject:
        """Delete one of an organization's audit stream destinations."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/audit_streams/{stream_id}",
        )


class _AsyncOrgDesign:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, org_id: str) -> m.DesignSettings:
        """Read an organization's design override and the result of layering it over the
        instance design.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/design",
        )

    async def replace(self, org_id: str, body: m.ReplaceDesignBody) -> m.DesignSettings:
        """Replace an organization's design override ({ design: AtlasDesign }); { design: {} }
        removes it.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/design",
            body=body,
        )

    async def update(self, org_id: str, body: m.UpdateDesignBody) -> m.DesignSettings:
        """Change part of an organization's design override; null removes a setting."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/design",
            body=body,
        )


class _AsyncOrgSettings:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, org_id: str) -> m.OrganizationSettings:
        """Fetch one organization's settings values."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/settings",
        )

    async def replace(
        self, org_id: str, body: m.OrgSettingsBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettings:
        """Write one organization's settings values."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/settings",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self, org_id: str, body: m.OrgSettingsBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettings:
        """Merge a partial object into an organization's settings values (RFC 7396 shallow
        merge): a key set to null is REMOVED, any other value sets/overwrites it, untouched
        keys are preserved — so a single settings key can be...
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/settings",
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncOrgEndUsers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/end_users",
            query=_q(status=status, limit=limit, starting_after=starting_after),
        )

    async def add(
        self, org_id: str, body: m.AddOrgEndUserBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationEndUser:
        """Attach an instance user to an organization's end-user pool as a reader (the token-
        exchange path).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/end_users",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self, org_id: str, user_id: str, body: m.UpdateOrgEndUserBody
    ) -> m.OrganizationEndUser:
        """Approve (active), gate (pending) or block a reader in an organization end-user pool."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{org_id}/end_users/{user_id}",
            body=body,
        )

    async def remove(self, org_id: str, user_id: str) -> DeletedObject:
        """Remove a reader from an organization's end-user pool."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/end_users/{user_id}",
        )


class _AsyncOrgReaderDomain:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, org_id: str) -> ListPage:
        """List the organization's reader domain(s) — the host(s) whose sign-ups join this
        org's end-user pool, with DNS/certificate status.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/reader_domain",
        )

    async def set(
        self, org_id: str, body: m.SetReaderDomainBody, *, idempotency_key: str | None = None
    ) -> JSON:
        """Bind a host to this organization's reader pool: a sign-up on it joins the pool."""
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/reader_domain",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, org_id: str) -> DeletedObject:
        """Remove the organization's reader domain binding and drop its edge router."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/reader_domain",
        )


class _AsyncOrgBranding:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, org_id: str) -> m.OrganizationBranding:
        """Read an organization's hosted-page branding overlay (display name, logo, primary
        colour, support URL, custom domain).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/branding",
        )

    async def set(
        self, org_id: str, body: m.SetOrgBrandingBody | None = None
    ) -> m.OrganizationBranding:
        """Set an organization's hosted-page branding overlay — a partial merge: a provided
        field overrides the instance brand, null (or empty string) clears it back.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{org_id}/branding",
            body=body,
        )


class AsyncActions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List AsyncActions (tenant code that runs at auth-pipeline hooks)."""
        return await self._t.request(
            method="GET",
            path="/v1/actions",
        )

    async def create(
        self, body: m.CreateActionBody | None = None, *, idempotency_key: str | None = None
    ) -> m.Action:
        """Create an Action for a trigger (post_login, pre_user_registration,
        post_user_registration).
        """
        return await self._t.request(
            method="POST",
            path="/v1/actions",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_binding(self, trigger: str) -> m.ActionBindingList:
        """Read the ordered list of Action ids bound to a trigger."""
        return await self._t.request(
            method="GET",
            path=f"/v1/actions/bindings/{trigger}",
        )

    async def set_binding(
        self, trigger: str, body: m.SetActionBindingBody | None = None
    ) -> m.ActionBindingList:
        """Replace the ordered list of AsyncActions bound to a trigger — the single source of truth
        for what runs, and in what order.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/actions/bindings/{trigger}",
            body=body,
        )

    async def get(self, action_id: str) -> m.Action:
        """Read one Action."""
        return await self._t.request(
            method="GET",
            path=f"/v1/actions/{action_id}",
        )

    async def update(self, action_id: str, body: m.UpdateActionBody | None = None) -> m.Action:
        """Update an Action's name, code, enabled flag, or secrets."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/actions/{action_id}",
            body=body,
        )

    async def delete(self, action_id: str) -> DeletedObject:
        """Delete an Action."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/actions/{action_id}",
        )

    async def test(
        self, action_id: str, body: m.TestActionBody | None = None
    ) -> m.ActionTestResult:
        """Dry-run an Action against a sample event in the sandbox and return its
        claims/deny/logs.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/actions/{action_id}/test",
            body=body,
        )


class AsyncApiKeys:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        subject_type: Literal["user", "organization", "machine"] | None = None,
        subject_id: str | None = None,
    ) -> ListPage:
        """List end-user API keys the tenant minted for its users/organizations."""
        return await self._t.request(
            method="GET",
            path="/v1/api_keys",
            query=_q(subject_type=subject_type, subject_id=subject_id),
        )

    async def create(self, body: m.CreateApiKeyBody | None = None) -> m.ApiKeyCreate:
        """Mint an end-user API key for a user, organization or machine (returns the ak_ secret
        once), OR import an existing key by its SHA-256 hash (hash_algorithm "sha256" or
        "sha256_hex") so it verifies against the original...
        """
        return await self._t.request(
            method="POST",
            path="/v1/api_keys",
            body=body,
        )

    async def list_revoked(
        self, *, since: str | int | None = None, limit: int | None = None
    ) -> ListPage:
        """Revocation feed: the keys revoked since a cursor (since=<iso|cursor>), so a resource
        can deny-list revoked key ids while their short-lived delegated tokens are still
        live.
        """
        return await self._t.request(
            method="GET",
            path="/v1/api_keys/revoked",
            query=_q(since=since, limit=limit),
        )

    async def create_token(self, body: m.CreateApiKeyTokenBody | None = None) -> m.ApiKeyToken:
        """Mint a short-lived, JWKS-signed access JWT (token_use:api_key, jti) whose exp is
        clamped to the smallest of the request, the key expiry and the org ceiling; scopes +
        constraints are embedded so a resource verifies it...
        """
        return await self._t.request(
            method="POST",
            path="/v1/api_keys/token",
            body=body,
        )

    async def verify(self, body: m.VerifyApiKeyBody | None = None) -> m.ApiKeyVerification:
        """Verify a presented ak_ secret."""
        return await self._t.request(
            method="POST",
            path="/v1/api_keys/verify",
            body=body,
        )

    async def get(self, key_id: str) -> m.ApiKey:
        """Read one end-user API key by id (prefix + metadata, never the secret)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/api_keys/{key_id}",
        )

    async def update(self, key_id: str, body: m.UpdateApiKeyBody | None = None) -> m.ApiKey:
        """Update an end-user API key: name, claims, expiry, scopes, constraints, token
        lifetime or spend caps (``limits``; ``None`` clears them).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/api_keys/{key_id}",
            body=body,
        )

    async def record_usage(self, key_id: str, body: m.RecordApiKeyUsageBody) -> m.ApiKeyUsageDebit:
        """Meter usage against a key's spend caps, atomically. A debit that fits every cap
        for its unit is recorded (``allowed`` is ``True``); one that would exceed a cap
        records nothing and returns ``allowed: False`` with ``code: "LIMIT_EXCEEDED"``
        (not an exception). Reusing an ``idempotency_key`` with a different unit or amount
        raises a 409 IDEMPOTENCY_CONFLICT; a revoked or expired key a 409 CONFLICT.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/api_keys/{key_id}/usage",
            body=body,
        )

    async def get_usage(self, key_id: str) -> m.ApiKeyUsage:
        """A key's current-window usage: each cap's state plus every unit's counters."""
        return await self._t.request(
            method="GET",
            path=f"/v1/api_keys/{key_id}/usage",
        )

    async def revoke(self, key_id: str) -> m.ApiKeyRevokeResult:
        """Revoke an end-user API key."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/api_keys/{key_id}",
        )


class AsyncAuditEvents:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(self, body: m.CreateAuditEventBody | None = None) -> m.AuditEvent:
        """Write one of the tenant's OWN custom audit events (actor, action, optional target,
        optional metadata).
        """
        return await self._t.request(
            method="POST",
            path="/v1/audit_events",
            body=body,
        )

    async def list(
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
        return await self._t.request(
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

    async def delete(
        self, *, organization_id: str | None = None, action: str | None = None
    ) -> m.AuditEventDeleteResult:
        """Bulk-delete the instance's custom audit events — a TEST-MODE reset, allowed ONLY on
        a development instance (a production audit trail cannot be bulk-erased: 403).
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/audit_events",
            query=_q(organization_id=organization_id, action=action),
        )

    async def create_batch(self, body: m.CreateBatchAuditEventBody | None = None) -> ListPage:
        """Write up to 100 custom audit events in one call."""
        return await self._t.request(
            method="POST",
            path="/v1/audit_events/batch",
            body=body,
        )

    async def export(
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
        return await self._t.request(
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


class AsyncBilling:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.plans = _AsyncBillingPlans(transport)
        self.subscriptions = _AsyncBillingSubscriptions(transport)

    async def sync_seats(self, subject_type: str, subject_id: str) -> m.BillingSeats:
        """Sync a per-seat subscription's Stripe quantity to the org's current member count
        (proration applied).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subjects/{subject_type}/{subject_id}/sync_seats",
        )

    async def record_usage(self, body: m.RecordUsageBody | None = None) -> m.BillingUsage:
        """Report metered usage for a subject (idempotent on idempotency_key); mirrored to a
        Stripe meter event when the plan is metered and configured.
        """
        return await self._t.request(
            method="POST",
            path="/v1/billing/usage",
            body=body,
        )


class _AsyncBillingPlans:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List the plans the tenant defines for their app's users (end-user billing)."""
        return await self._t.request(
            method="GET",
            path="/v1/billing/plans",
        )

    async def create(
        self, body: m.CreateBillingPlanBody, *, idempotency_key: str | None = None
    ) -> m.BillingPlanCreateResult:
        """Create an end-user billing plan."""
        return await self._t.request(
            method="POST",
            path="/v1/billing/plans",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, plan_id: str) -> m.BillingPlan:
        """Read one end-user billing plan, including its Stripe price id and granted features."""
        return await self._t.request(
            method="GET",
            path=f"/v1/billing/plans/{plan_id}",
        )

    async def update(
        self, plan_id: str, body: m.UpdateBillingPlanBody | None = None
    ) -> m.BillingPlan:
        """Update an end-user billing plan's name, slug, price, interval, features, audience or
        active flag.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/billing/plans/{plan_id}",
            body=body,
        )

    async def delete(self, plan_id: str) -> DeletedObject:
        """Delete an end-user billing plan."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/billing/plans/{plan_id}",
        )


class _AsyncBillingSubscriptions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self, *, subject_type: Literal["user", "org"] | None = None, subject_id: str | None = None
    ) -> ListPage:
        """List end-user subscriptions, optionally filtered by subject_type (user/org) and
        subject_id.
        """
        return await self._t.request(
            method="GET",
            path="/v1/billing/subscriptions",
            query=_q(subject_type=subject_type, subject_id=subject_id),
        )

    async def import_subscription(
        self, body: m.ImportSubscriptionBody | None = None, *, idempotency_key: str | None = None
    ) -> m.Subscription:
        """Adopt an EXISTING Stripe subscription (same Stripe account) onto an Atlas user/org +
        plan, for migrating billing into Atlas without re-charging.
        """
        return await self._t.request(
            method="POST",
            path="/v1/billing/subscriptions/import",
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncBotLabels:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, limit: int | None = None, before: int | None = None) -> ListPage:
        """Export the supervised training labels (bot / human / suspect) with their subject and
        source.
        """
        return await self._t.request(
            method="GET",
            path="/v1/bot_labels",
            query=_q(limit=limit, before=before),
        )

    async def create(self, body: m.CreateBotLabelBody | None = None) -> m.BotLabel:
        """Add a supervised training label to a subject (user / device / ip_hash / attempt) —
        an analyst confirming a bot or a human.
        """
        return await self._t.request(
            method="POST",
            path="/v1/bot_labels",
            body=body,
        )


class AsyncBotSignals:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, limit: int | None = None, before: int | None = None) -> ListPage:
        """Export the anonymised anti-bot signal lake (device + behavioural + network features,
        risk verdict, heuristic score), newest first with a `before` epoch-ms cursor.
        """
        return await self._t.request(
            method="GET",
            path="/v1/bot_signals",
            query=_q(limit=limit, before=before),
        )


class AsyncBranding:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.Branding:
        """Read the instance branding / hosted-page appearance and its resolved (renderer)
        form.
        """
        return await self._t.request(
            method="GET",
            path="/v1/branding",
        )

    async def update(self, body: JSON | None = None) -> m.Branding:
        """Change branding with a PARTIAL merge (unlike auth_config full-replace), validated
        the way the renderer resolves it — a value it would drop is refused, not silently
        ignored.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/branding",
            body=body,
        )

    async def preview(self, body: JSON | None = None) -> m.HostedPagePreview:
        """Render a draft branding through the real sign-in hosted-page renderer (same
        sanitizers + CSP) so an agent sees what would ship before saving.
        """
        return await self._t.request(
            method="POST",
            path="/v1/branding/preview",
            body=body,
        )


class AsyncCaptcha:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def verify(self, body: m.VerifyCaptchaBody | None = None) -> m.CaptchaVerification:
        """§5 "captcha anywhere": verify a CAPTCHA token server-side against the instance's
        centrally-configured provider.
        """
        return await self._t.request(
            method="POST",
            path="/v1/captcha/verify",
            body=body,
        )


class AsyncConfigChangelog:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/config_changelog",
            query=_q(action=action, limit=limit, starting_after=starting_after, since=since),
        )


class AsyncConnectors:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List the caller's own community connector profiles (draft + published), with
        adoption counts.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connectors",
        )

    async def create(self, body: m.CreateConnectorBody | None = None) -> m.Connector:
        """Create a community connector profile (SEO profile + OAuth config + share modes)."""
        return await self._t.request(
            method="POST",
            path="/v1/connectors",
            body=body,
        )

    async def get(self, connector_id: str) -> m.Connector:
        """Fetch one of the caller's own connector profiles."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connectors/{connector_id}",
        )

    async def update(
        self, connector_id: str, body: m.UpdateConnectorBody | None = None
    ) -> m.Connector:
        """Edit a connector profile — SEO fields, OAuth config, and share modes."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/connectors/{connector_id}",
            body=body,
        )

    async def delete(self, connector_id: str) -> DeletedObject:
        """Delete one of the caller's own connector profiles and cascade its installs, reviews,
        and reports.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connectors/{connector_id}",
        )

    async def publish(self, connector_id: str) -> m.Connector:
        """Publish a connector to the public directory."""
        return await self._t.request(
            method="POST",
            path=f"/v1/connectors/{connector_id}/publish",
        )

    async def set_shared_credentials(
        self, connector_id: str, body: m.SetConnectorSharedCredentialsBody | None = None
    ) -> m.Connector:
        """Set, rotate, or revoke the full_shared OAuth credentials."""
        return await self._t.request(
            method="POST",
            path=f"/v1/connectors/{connector_id}/shared_credentials",
            body=body,
        )

    async def unlist(self, connector_id: str) -> m.Connector:
        """Remove a published connector from the directory (back to unlisted) without deleting
        it.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connectors/{connector_id}/unlist",
        )

    async def install(
        self, slug: str, body: m.InstallConnectorBody | None = None
    ) -> m.ConnectorInstall:
        """Enable a published connector on the caller's instance (prefill, full_shared, or
        full_idp), snapshotting its OAuth config into the connection.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connectors/{slug}/install",
            body=body,
        )

    async def review(
        self, slug: str, body: m.ReviewConnectorBody | None = None
    ) -> m.ConnectorReview:
        """Rate a connector the caller installed (1–5, optional text)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/connectors/{slug}/reviews",
            body=body,
        )


class AsyncDataSubjectRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateDataSubjectRequestBody, *, idempotency_key: str | None = None
    ) -> m.DataSubjectRequest:
        """Create a DSAR (export or erasure) for a user from the backend — the twin of the
        self-service /client/me flows, for a DSAR orchestrator.
        """
        return await self._t.request(
            method="POST",
            path="/v1/data_subject_requests",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
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
        return await self._t.request(
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

    async def get(self, request_id: str) -> m.DataSubjectRequest:
        """Fetch a data-subject request, including an export's produced package."""
        return await self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{request_id}",
        )

    async def cancel(
        self, request_id: str, *, idempotency_key: str | None = None
    ) -> m.DataSubjectRequest:
        """Cancel a scheduled erasure within its grace window — the sibling to /fulfill (which
        expedites).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{request_id}/cancel",
            idempotency_key=idempotency_key,
        )

    async def fulfill(
        self, request_id: str, *, idempotency_key: str | None = None
    ) -> m.DataSubjectRequest:
        """Fulfil a request now: build the export package, or run the erasure through the same
        soft-delete + PII-purge path a user-delete uses, ahead of the grace window.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{request_id}/fulfill",
            idempotency_key=idempotency_key,
        )

    async def reject(
        self,
        request_id: str,
        body: m.RejectDataSubjectRequestBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.DataSubjectRequest:
        """Reject a request with a recorded reason."""
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{request_id}/reject",
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncDesign:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.assets = _AsyncDesignAssets(transport)

    async def get(self) -> m.DesignSettings:
        """Read the instance's sign-in page design: stored overrides, the resolved design,
        contrast warnings and the legacy flag.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/design",
        )

    async def replace(self, body: m.ReplaceDesignBody) -> m.DesignSettings:
        """Replace the instance design ({ design: AtlasDesign })."""
        return await self._t.request(
            method="PUT",
            path="/v1/instance/design",
            body=body,
        )

    async def update(self, body: m.UpdateDesignBody) -> m.DesignSettings:
        """Change part of the instance design ({ design: AtlasDesignPatch }): nested settings
        merge, null removes a setting.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/instance/design",
            body=body,
        )

    async def preview(self, body: m.PreviewDesignBody) -> m.DesignPreview:
        """Compile an unsaved design: CSS variables scoped to .atlas-root, data attributes,
        font stylesheet URLs, warnings, the resolved design and the rendered sign-in page.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/design/preview",
            body=body,
        )

    async def catalog(self) -> JSON:
        """The design-system catalog: the sign-in page presets (each fully resolved), the
        curated font list, and the documented --atlas-* CSS variable set.
        """
        return await self._t.request(
            method="GET",
            path="/v1/design/catalog",
        )


class _AsyncDesignAssets:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def upload(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        kind: Literal["background", "logo"] | None = None,
    ) -> m.DesignAsset:
        """Upload a design image (a background or a logo) for this instance."""
        return await self._t.request(
            method="POST",
            path="/v1/design/assets",
            query=_q(kind=kind),
            content=data,
            content_type=content_type or _sniff_image_type(data),
        )

    async def list(self) -> ListPage:
        """List this instance's uploaded design images, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/design/assets",
        )

    async def delete(self, asset_id: str) -> m.DesignAssetDeleteResult:
        """Delete one of this instance's design images."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/design/assets/{asset_id}",
        )


class AsyncDiagnostics:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def login_readiness(
        self, *, origin: str | None = None, live: bool | None = None
    ) -> m.LoginReadiness:
        """End-to-end login-readiness probe for a given `origin` (CORS, cookie domain, email
        claim, JWKS), reporting the observed effective runtime values with a per-hop
        pass/fail and a specific fix.
        """
        return await self._t.request(
            method="GET",
            path="/v1/diagnostics/login_readiness",
            query=_q(origin=origin, live=live),
        )

    async def request_inspector(
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
        return await self._t.request(
            method="GET",
            path="/v1/diagnostics/request_inspector",
            query=_q(origin=origin, method=method, path=path, token=token),
        )


class AsyncDirectory:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/directory",
            query=_q(category=category, verified=verified, q=q, limit=limit, offset=offset),
        )


class AsyncEmailAddresses:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def set_primary(
        self, email_id: str, *, idempotency_key: str | None = None
    ) -> m.EmailAddress:
        """Make a verified address primary — flat alias (user derived from the address)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/email_addresses/{email_id}/primary",
            idempotency_key=idempotency_key,
        )

    async def verify(self, email_id: str, *, idempotency_key: str | None = None) -> m.EmailAddress:
        """Mark an address verified — flat alias (user derived from the address)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/email_addresses/{email_id}/verify",
            idempotency_key=idempotency_key,
        )


class AsyncEmailTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List email templates with their defaults and any instance override."""
        return await self._t.request(
            method="GET",
            path="/v1/email_templates",
        )

    async def set(
        self, name: str, body: m.SetEmailTemplateBody | None = None
    ) -> m.EmailTemplateSetResult:
        """Override a template."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/email_templates/{name}",
            body=body,
        )

    async def reset(self, name: str) -> m.EmailTemplateResetResult:
        """Revert a template to the Atlas built-in."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/email_templates/{name}",
        )

    async def preview(
        self, name: str, body: m.PreviewEmailTemplateBody | None = None
    ) -> m.EmailPreview:
        """Render an email template (an unsaved draft if supplied, else the stored one) with
        SAMPLE variables — never a real code — so an agent can see the result before saving.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/email_templates/{name}/preview",
            body=body,
        )


class AsyncEntitlementOverrides:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateEntitlementOverrideBody, *, idempotency_key: str | None = None
    ) -> m.EntitlementOverride:
        """Grant a SALES-LED entitlement override (P1-6): pin a plan / features / limits onto a
        user or org without Stripe (e.g. an Enterprise contract).
        """
        return await self._t.request(
            method="POST",
            path="/v1/entitlement_overrides",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self, *, subject_type: Literal["user", "org"] | None = None, subject_id: str | None = None
    ) -> ListPage:
        """List sales-led entitlement overrides, optionally filtered by subject_type (user/org)
        and subject_id.
        """
        return await self._t.request(
            method="GET",
            path="/v1/entitlement_overrides",
            query=_q(subject_type=subject_type, subject_id=subject_id),
        )

    async def delete(self, override_id: str) -> DeletedObject:
        """Revoke (hard-delete) a sales-led entitlement override."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/entitlement_overrides/{override_id}",
        )


class AsyncEvents:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
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


class AsyncFga:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.stores = _AsyncFgaStores(transport)
        self.authorization_models = _AsyncFgaModels(transport)

    async def batch_check(
        self, store_id: str, body: m.BatchCheckFgaBody | None = None
    ) -> m.FgaBatchCheck:
        """Check up to 100 (user, relation, object) tuples in one request."""
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/batch-check",
            body=body,
        )

    async def check(self, store_id: str, body: m.CheckFgaBody | None = None) -> m.FgaCheck:
        """Check whether a user has a relation on an object, resolving the authorization model
        (direct tuples, computed usersets, tuple-to-userset hops, set operators) with cycle
        + depth safety.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/check",
            body=body,
        )

    async def expand(self, store_id: str, body: m.ExpandFgaBody | None = None) -> m.FgaExpand:
        """Expand the userset tree for an (object, relation) — who would hold the relation,
        mirroring the model rewrite.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/expand",
            body=body,
        )

    async def list_objects(
        self, store_id: str, body: m.ListObjectsFgaBody | None = None
    ) -> m.FgaListObjects:
        """List the object ids of a type that a user has a relation on."""
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/list-objects",
            body=body,
        )

    async def read(self, store_id: str, body: m.ReadFgaBody | None = None) -> ListPage:
        """Query stored relationship tuples in a store, optionally filtered by user, relation
        and/or object.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/read",
            body=body,
        )

    async def write(
        self,
        store_id: str,
        body: m.WriteFgaBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.FgaWriteResult:
        """Transactionally write and/or delete relationship tuples in a store."""
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/write",
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncFgaStores:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List fine-grained authorization (ReBAC / Zanzibar) stores in the instance."""
        return await self._t.request(
            method="GET",
            path="/v1/fga/stores",
        )

    async def create(
        self, body: m.CreateFgaStoreBody | None = None, *, idempotency_key: str | None = None
    ) -> m.FgaStore:
        """Create a fine-grained authorization store — an isolated namespace for authorization
        models and relationship tuples.
        """
        return await self._t.request(
            method="POST",
            path="/v1/fga/stores",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, store_id: str) -> m.FgaStore:
        """Read one FGA store."""
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{store_id}",
        )

    async def delete(self, store_id: str) -> DeletedObject:
        """Delete an FGA store, cascading its authorization models and relationship tuples."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/fga/stores/{store_id}",
        )


class _AsyncFgaModels:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, store_id: str) -> ListPage:
        """List the immutable authorization-model versions of a store, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{store_id}/authorization-models",
        )

    async def create(
        self,
        store_id: str,
        body: m.CreateFgaAuthorizationModelBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.FgaAuthorizationModel:
        """Write a new immutable authorization-model version (OpenFGA-shaped type_definitions
        with this/computedUserset/tupleToUserset and union/intersection/difference).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{store_id}/authorization-models",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, store_id: str, model_id: str) -> m.FgaAuthorizationModel:
        """Read one authorization-model version, including its full model definition."""
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{store_id}/authorization-models/{model_id}",
        )


class AsyncOpenFga:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.stores = _AsyncOpenFgaStores(transport)
        self.authorization_models = _AsyncOpenFgaModels(transport)

    async def batch_check(
        self, store_id: str, body: m.BatchCheckOpenFgaBody
    ) -> m.OpenFgaBatchCheckResult:
        """Check up to 100 tuples in one request, keyed by correlation id (OpenFGA-wire
        BatchCheck).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/batch-check",
            body=body,
        )

    async def check(
        self, store_id: str, body: m.CheckOpenFgaBody
    ) -> m.OpenFgaBatchCheckResultResultValue:
        """Check whether a user has a relation on an object (OpenFGA-wire check)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/check",
            body=body,
        )

    async def expand(self, store_id: str, body: m.ExpandOpenFgaBody) -> m.OpenFgaExpandResult:
        """Expand the userset tree for an (object, relation) (OpenFGA-wire Expand)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/expand",
            body=body,
        )

    async def list_objects(
        self, store_id: str, body: m.ListObjectsOpenFgaBody
    ) -> m.OpenFgaListObjectsResult:
        """List the objects of a type a user has a relation on (OpenFGA-wire ListObjects)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/list-objects",
            body=body,
        )

    async def read(
        self, store_id: str, body: m.ReadOpenFgaBody | None = None
    ) -> m.OpenFgaReadResult:
        """Read relationship tuples, optionally filtered by a tuple key (OpenFGA-wire Read)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/read",
            body=body,
        )

    async def write(self, store_id: str, body: m.WriteOpenFgaBody | None = None) -> JSON:
        """Write or delete relationship tuples in a store (OpenFGA-wire write)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/write",
            body=body,
        )


class _AsyncOpenFgaStores:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> m.OpenFgaStoreList:
        """List the instance's OpenFGA (ReBAC) authorization stores."""
        return await self._t.request(
            method="GET",
            path="/v1/openfga/stores",
        )

    async def create(
        self, body: m.CreateOpenFgaStoreBody, *, idempotency_key: str | None = None
    ) -> m.OpenFgaStore:
        """Create an OpenFGA authorization store."""
        return await self._t.request(
            method="POST",
            path="/v1/openfga/stores",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, store_id: str) -> m.OpenFgaStore:
        """Get one OpenFGA store (OpenFGA-wire GetStore)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{store_id}",
        )


class _AsyncOpenFgaModels:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, store_id: str) -> m.OpenFgaAuthorizationModelList:
        """List the authorization models in a store."""
        return await self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{store_id}/authorization-models",
        )

    async def create(
        self, store_id: str, body: m.CreateOpenFgaAuthorizationModelBody | None = None
    ) -> m.OpenFgaWriteModelResult:
        """Write a new authorization model to a store."""
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{store_id}/authorization-models",
            body=body,
        )

    async def get(self, store_id: str, model_id: str) -> m.OpenFgaAuthorizationModelResult:
        """Read one authorization model (OpenFGA-wire ReadAuthorizationModel)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{store_id}/authorization-models/{model_id}",
        )


class AsyncGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def revoke(
        self, grant_id: str, *, idempotency_key: str | None = None
    ) -> m.GrantRevokeResult:
        """Revoke one consent grant and cascade-revoke its access/refresh grants through the
        standard revocation path, so the app stops working on its next request.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/grants/{grant_id}",
            idempotency_key=idempotency_key,
        )


class AsyncInstance:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.cookie_consent = _AsyncInstanceCookieConsent(transport)
        self.security = _AsyncInstanceSecurity(transport)
        self.integrations = _AsyncInstanceIntegrations(transport)
        self.referrals = _AsyncInstanceReferrals(transport)
        self.hooks = _AsyncInstanceHooks(transport)

    async def get(self) -> m.Instance:
        """Read instance configuration."""
        return await self._t.request(
            method="GET",
            path="/v1/instance",
        )

    async def update(self, body: m.UpdateInstanceBody | None = None) -> m.Instance:
        """Update allowed origins and auth_config (a partial, validated, merged patch — not a
        replace).
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/instance",
            body=body,
        )

    async def set_captcha_secret(
        self, body: m.SetCaptchaSecretBody | None = None
    ) -> m.CaptchaSecret:
        """Store the captcha provider secret (write-only, encrypted; never read back)."""
        return await self._t.request(
            method="PUT",
            path="/v1/instance/captcha_secret",
            body=body,
        )

    async def delete_captcha_secret(
        self, *, provider: str | None = None, force: bool = False
    ) -> m.InstanceDeleteCaptchaSecretResult:
        """Clear the stored captcha provider secret (the configured provider unless
        ``provider`` names another).

        Refused with 409 ``CAPTCHA_IN_USE`` while a captcha flow uses that secret (the
        error's ``meta.flows`` lists them). Pass ``force=True`` to remove it anyway; those
        flows are turned off and returned in ``flows_turned_off``.
        """
        query: dict[str, str | bool] = {}
        if provider:
            query["provider"] = provider
        if force:
            query["force"] = True
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/captcha_secret",
            query=query or None,
        )

    async def set_kerberos_secret(
        self, body: m.SetKerberosSecretBody | None = None
    ) -> m.KerberosSecret:
        """Store the per-instance Kerberos/IWA trusted-proxy secret (write-only, encrypted;
        never read back).
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/kerberos_secret",
            body=body,
        )

    async def delete_kerberos_secret(self) -> m.InstanceDeleteKerberosSecretResult:
        """Clear the stored Kerberos/IWA trusted-proxy secret for this instance."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/kerberos_secret",
        )

    async def get_proxy_secret(self) -> m.ProxySecret:
        """Whether a trusted reverse proxy secret is set, and since when (never the
        secret).
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/proxy_secret",
        )

    async def create_proxy_secret(
        self, body: m.CreateProxySecretBody | None = None
    ) -> m.ProxySecretCreated:
        """Create, or rotate, the trusted reverse proxy secret; it is returned once. On a
        rotation the replaced secret keeps working for ``overlap_seconds`` (default 86400,
        ``0`` = stop now, at most 604800).
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/proxy_secret",
            body=body,
        )

    async def delete_proxy_secret(self) -> m.InstanceDeleteProxySecretResult:
        """Remove the trusted reverse proxy secret: ``X-Atlas-Client-IP`` is ignored again."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/proxy_secret",
        )

    async def set_ldap_bind_password(
        self, connection_id: str, body: m.SetLdapBindPasswordBody | None = None
    ) -> m.LdapBindPassword:
        """Store an LDAP connection service-account bind password (write-only, encrypted; never
        read back).
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/instance/ldap_connections/{connection_id}/bind_password",
            body=body,
        )

    async def delete_ldap_bind_password(
        self, connection_id: str
    ) -> m.InstanceDeleteLdapBindPasswordResult:
        """Clear the stored bind password for an LDAP connection."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/instance/ldap_connections/{connection_id}/bind_password",
        )

    async def preflight(self) -> m.Preflight:
        """Check your setup in one call."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/preflight",
        )

    async def move_origin(self, body: m.OriginMoveBody) -> m.OriginMove:
        """Move every URL that points at one origin to another (a domain move), across the
        instance, its OAuth clients, webhooks, redirect URLs and Sign in with Atlas apps.

        ``body`` is ``{"from": ..., "to": ..., "dry_run": ...}``; ``dry_run=True`` writes
        nothing. A repeated run returns an empty ``changes`` list.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/move_origin",
            body=body,
        )

    async def connections(self) -> m.InstanceConnections:
        """The instance's links to other platforms and their health. Read-only."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/connections",
        )


class _AsyncInstanceIntegrations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_chatly(self) -> m.ChatlyIntegration:
        """Read the Chatly connection (``enabled: False`` when none)."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/integrations/chatly",
        )

    async def set_chatly(self, body: m.SetChatlyIntegrationBody) -> m.ChatlyIntegration:
        """Connect a Chatly channel: ``getToken({ template: 'chatly' })`` then mints tokens
        the channel's identity verification accepts.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/integrations/chatly",
            body=body,
        )

    async def delete_chatly(self) -> m.ChatlyIntegration:
        """Remove the Chatly connection."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/integrations/chatly",
        )

    async def get_forumulate(self) -> m.ForumulateIntegration:
        """Read the Forumulate connection (``enabled: False`` when none)."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/integrations/forumulate",
        )

    async def set_forumulate(self, body: m.SetForumulateIntegrationBody) -> m.ForumulateIntegration:
        """Connect Forumulate spaces (replaces the whole connection). Store the returned
        ``reader_auth_provider`` on each space.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/integrations/forumulate",
            body=body,
        )

    async def delete_forumulate(self) -> m.ForumulateIntegration:
        """Remove the Forumulate connection."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/integrations/forumulate",
        )


class _AsyncInstanceCookieConsent:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.CookieConsent:
        """Read the cookie-consent CMP injected into the hosted sign-in, sign-up and account
        pages (enabled:false when none).
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/cookie_consent",
        )

    async def set(self, body: m.SetCookieConsentBody) -> m.CookieConsent:
        """Set the cookie-consent CMP for the hosted pages (any provider)."""
        return await self._t.request(
            method="PUT",
            path="/v1/instance/cookie_consent",
            body=body,
        )

    async def delete(self) -> m.CookieConsent:
        """Turn off the hosted-page cookie-consent CMP: no script is injected and the CSP goes
        back to normal.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/cookie_consent",
        )


class _AsyncInstanceReferrals:
    """Referral attribution: the instance's connection to a referral platform.

    With referrals on, every interactive sign-up is reported to the platform before
    ``user.created`` is sent; the answer lands on the user (``referral``,
    ``referral_code``, ``referral_link``). ``signing_secret`` and ``api_key`` are
    write-only.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.ReferralSettings:
        """Read the referral settings, the connection status and the supported providers."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/referrals",
        )

    async def update(
        self,
        body: m.UpdateReferralSettingsBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.ReferralSettings:
        """Update the referral settings; only the fields sent change, ``None`` clears.
        Enabling without what the provider needs is 422 ``REFERRALS_NOT_CONFIGURED``.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/instance/referrals",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test(self) -> m.ReferralConnectionTest:
        """Test the connection: a ping where the provider answers one (``method``
        ``ping``, with ``ping`` and ``warnings`` such as clock skew), else a signed probe
        (``method`` ``probe``: ``ok`` on 2xx or 404). ``error.code``
        ``signature_rejected`` on 401/403.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/referrals/test",
        )

    async def list_calls(
        self,
        *,
        limit: int | None = None,
        status: str | None = None,
        kind: str | None = None,
        user_id: str | None = None,
        error_code: str | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The referral call log, newest first (``limit`` 1-1000, default 50; servers
        before referral attribution v2 take at most 200). Page with ``starting_after``
        (the id of the last call of the previous page) while ``has_more``; filter on
        ``error_code`` (e.g. ``signature_rejected``).
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/referrals/calls",
            query=_q(
                limit=limit,
                status=status,
                kind=kind,
                user_id=user_id,
                error_code=error_code,
                starting_after=starting_after,
            ),
        )

    async def retry_call(
        self, call_id: str, *, idempotency_key: str | None = None
    ) -> m.ReferralCall:
        """Retry a failed, retrying or skipped call now (not a connection test)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/referrals/calls/{call_id}/retry",
            idempotency_key=idempotency_key,
        )

    async def retry_failed(
        self,
        *,
        kind: str | None = None,
        error_code: str | None = None,
        idempotency_key: str | None = None,
    ) -> m.ReferralRetryFailedResult:
        """Re-queue every failed call (not tests) to send now, optionally only one
        ``kind`` or one ``error_code`` (e.g. ``signature_rejected`` after replacing the
        secret).
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/referrals/calls/retry_failed",
            body=_q(kind=kind, error_code=error_code),
            idempotency_key=idempotency_key,
        )

    async def simulate(self, *, code: str | None = None) -> m.ReferralSimulateResult:
        """Send a sign-up call for a made-up user (``atlas_test_<random>``, no user is
        created) with an optional ``code``, and return what the platform answered.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/referrals/simulate",
            body=_q(code=code),
        )

    async def backfill(
        self,
        body: m.ReferralBackfillBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.ReferralBackfillJob:
        """Queue sign-up calls for existing users created at or after ``since``, with
        their real sign-up time. AsyncUsers already reported are skipped. Referrals must be on
        (422 ``REFERRALS_NOT_CONFIGURED`` otherwise). Poll :meth:`get_backfill`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/referrals/backfill",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_backfill(self, backfill_id: str) -> m.ReferralBackfillJob:
        """Read a backfill job: how many calls it queued and where they stand."""
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/referrals/backfill/{backfill_id}",
        )

    async def get_for_user(self, user_id: str) -> m.UserReferralResult:
        """The stored referral result for one user (who referred them, how, their own
        code), with no call to the platform. 404 when the user was never reported.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/referral",
        )


class _AsyncInstanceHooks:
    """The ``before_user_create`` hook: just before Atlas creates a user from a
    self-service sign-up, it sends your endpoint a signed ``POST`` (the webhook headers;
    verify it with :func:`verify_webhook`) of type ``user.before_create`` and stamps the
    ``external_id`` and metadata you answer. A slow or failing hook never blocks a
    sign-up. ``signing_secret`` is write-only.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_before_user_create(self) -> m.BeforeUserCreateHook:
        """Read the hook settings and its last call."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/hooks/before_user_create",
        )

    async def update_before_user_create(
        self,
        body: m.UpdateBeforeUserCreateHookBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.BeforeUserCreateHook:
        """Update the hook; only the fields sent change, ``None`` clears. Turning it on
        needs ``url`` and ``signing_secret``.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/instance/hooks/before_user_create",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test_before_user_create(self) -> m.BeforeUserCreateHookTest:
        """Send the hook a sample draft and return its answer; nothing is stored."""
        return await self._t.request(
            method="POST",
            path="/v1/instance/hooks/before_user_create/test",
        )


class _AsyncInstanceSecurity:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.InstanceSecurity:
        """Read the instance kill switches (per-flow on/off) and the customer IP allowlist."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/security",
        )

    async def update(self, body: m.UpdateInstanceSecurityBody | None = None) -> m.InstanceSecurity:
        """Set the instance kill switches and/or IP allowlist."""
        return await self._t.request(
            method="PATCH",
            path="/v1/instance/security",
            body=body,
        )


class AsyncJobs:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        """List bulk import/export jobs, newest first (cursor pagination)."""
        return await self._t.request(
            method="GET",
            path="/v1/jobs",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(self, job_id: str) -> m.Job:
        """Fetch a job: its status, counters and (for an export) result."""
        return await self._t.request(
            method="GET",
            path=f"/v1/jobs/{job_id}",
        )

    async def list_errors(self, job_id: str) -> ListPage:
        """List a job's per-row errors ({ index, email, code, message })."""
        return await self._t.request(
            method="GET",
            path=f"/v1/jobs/{job_id}/errors",
        )


class AsyncLegacyAuthConnection:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.LegacyAuthConnection:
        """Read the instance's lazy-migration (legacy-auth / custom-DB) connection."""
        return await self._t.request(
            method="GET",
            path="/v1/legacy_auth_connection",
        )

    async def set(
        self, body: m.SetLegacyAuthConnectionBody, *, idempotency_key: str | None = None
    ) -> m.LegacyAuthConnection:
        """Create or replace the instance's lazy-migration connection (verify_url +
        signing_secret, enabled, import_on_login, timeout_ms).
        """
        return await self._t.request(
            method="PUT",
            path="/v1/legacy_auth_connection",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self, *, idempotency_key: str | None = None
    ) -> m.LegacyAuthConnectionDeleteResult:
        """Delete the instance's lazy-migration (legacy-auth / custom-DB) connection."""
        return await self._t.request(
            method="DELETE",
            path="/v1/legacy_auth_connection",
            idempotency_key=idempotency_key,
        )


class AsyncLocalizations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        resource_type: str | None = None,
        resource_name: str | None = None,
        locale: str | None = None,
    ) -> ListPage:
        """List per-language localization overrides (email/SMS templates, hosted-page copy)."""
        return await self._t.request(
            method="GET",
            path="/v1/localizations",
            query=_q(resource_type=resource_type, resource_name=resource_name, locale=locale),
        )

    async def create(self, body: m.CreateLocalizationBody | None = None) -> m.Localization:
        """Create or replace a localization override for one resource + locale."""
        return await self._t.request(
            method="POST",
            path="/v1/localizations",
            body=body,
        )

    async def get(self, localization_id: str) -> m.Localization:
        """Read one localization override by id."""
        return await self._t.request(
            method="GET",
            path=f"/v1/localizations/{localization_id}",
        )

    async def update(
        self, localization_id: str, body: m.UpdateLocalizationBody | None = None
    ) -> m.Localization:
        """Update a localization override content or enabled flag."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/localizations/{localization_id}",
            body=body,
        )

    async def delete(self, localization_id: str) -> None:
        """Delete a localization override, reverting that locale to the base template/copy."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/localizations/{localization_id}",
        )


class AsyncLogStreams:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List log streams (event forwarding to Datadog, Splunk or a generic HTTP sink)."""
        return await self._t.request(
            method="GET",
            path="/v1/log_streams",
        )

    async def create(
        self, body: m.CreateLogStreamBody | None = None, *, idempotency_key: str | None = None
    ) -> m.LogStream:
        """Create a log stream."""
        return await self._t.request(
            method="POST",
            path="/v1/log_streams",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, stream_id: str) -> m.LogStream:
        """Read one log stream, including its forwarding status, cursor and last error."""
        return await self._t.request(
            method="GET",
            path=f"/v1/log_streams/{stream_id}",
        )

    async def update(
        self, stream_id: str, body: m.UpdateLogStreamBody | None = None
    ) -> m.LogStream:
        """Update a log stream's name, destination, event_filter, enabled flag, or status
        (active/paused).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/log_streams/{stream_id}",
            body=body,
        )

    async def delete(self, stream_id: str) -> DeletedObject:
        """Delete a log stream."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/log_streams/{stream_id}",
        )

    async def test(self, stream_id: str) -> m.LogStreamTest:
        """Send one synthetic event to the sink with the stream's real credentials and return
        the sink's status.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/log_streams/{stream_id}/test",
        )


class AsyncLtiPlatforms:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List the LTI 1.3 platform registrations allowed to launch this instance."""
        return await self._t.request(
            method="GET",
            path="/v1/lti_platforms",
        )

    async def create(self, body: m.CreateLtiPlatformBody | None = None) -> m.LtiPlatform:
        """Register an LTI 1.3 platform (issuer, client_id, auth_login_url, jwks_uri,
        deployment_ids).
        """
        return await self._t.request(
            method="POST",
            path="/v1/lti_platforms",
            body=body,
        )

    async def get(self, platform_id: str) -> m.LtiPlatform:
        """Fetch one LTI 1.3 platform registration."""
        return await self._t.request(
            method="GET",
            path=f"/v1/lti_platforms/{platform_id}",
        )

    async def update(
        self, platform_id: str, body: m.UpdateLtiPlatformBody | None = None
    ) -> m.LtiPlatform:
        """Update an LTI 1.3 platform registration (URLs, deployment ids, org link)."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/lti_platforms/{platform_id}",
            body=body,
        )

    async def delete(self, platform_id: str) -> DeletedObject:
        """Remove an LTI 1.3 platform registration."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/lti_platforms/{platform_id}",
        )


class AsyncM2mTokens:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def verify(self, body: m.VerifyM2mTokenBody | None = None) -> m.M2mTokenVerification:
        """Verify a presented machine secret → { valid, machine_id?"""
        return await self._t.request(
            method="POST",
            path="/v1/m2m_tokens/verify",
            body=body,
        )


class AsyncMachineEnrolmentTokens:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateMachineEnrolmentTokenBody | None = None
    ) -> m.MachineEnrolmentTokenWithSecret:
        """Mint a machine enrolment token (single/multi-use, expiring, org-bound, approval-
        gated).
        """
        return await self._t.request(
            method="POST",
            path="/v1/machine_enrolment_tokens",
            body=body,
        )

    async def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List machine enrolment tokens (never the secret), newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/machine_enrolment_tokens",
            query=_q(organization_id=organization_id, limit=limit, starting_after=starting_after),
        )

    async def delete(self, token_id: str) -> DeletedObject:
        """Delete a machine enrolment token; it can no longer enrol new devices."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/machine_enrolment_tokens/{token_id}",
        )


class AsyncMachines:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(self, body: m.CreateMachineBody | None = None) -> m.MachineWithSecret:
        """Create a named machine (M2M) identity; returns the machine secret (mk_) ONCE."""
        return await self._t.request(
            method="POST",
            path="/v1/machines",
            body=body,
        )

    async def list(
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
        return await self._t.request(
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

    async def get(self, machine_id: str) -> m.Machine:
        """Fetch one named machine identity by id."""
        return await self._t.request(
            method="GET",
            path=f"/v1/machines/{machine_id}",
        )

    async def update(self, machine_id: str, body: m.UpdateMachineBody | None = None) -> m.Machine:
        """Rename a machine identity."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/machines/{machine_id}",
            body=body,
        )

    async def delete(self, machine_id: str) -> DeletedObject:
        """Delete a machine identity."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/machines/{machine_id}",
        )

    async def approve(self, machine_id: str) -> m.Machine:
        """Approve a device that enrolled under an approval-gated token (pending → active)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/approve",
        )

    async def update_metadata(
        self, machine_id: str, body: m.UpdateMachineMetadataBody | None = None
    ) -> m.Machine:
        """Merge device metadata (hostname, os, app_version, last_seen_at) into a machine."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/machines/{machine_id}/metadata",
            body=body,
        )

    async def list_organization_memberships(self, machine_id: str) -> ListPage:
        """List the organizations a machine belongs to with the org's resolved plan and the
        enrolment time — the machine-token counterpart of the user organization_memberships
        route.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/machines/{machine_id}/organization_memberships",
        )

    async def revoke(self, machine_id: str) -> m.Machine:
        """Revoke a machine device; its key stops minting tokens immediately (record kept)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/revoke",
        )

    async def rotate_key(self, machine_id: str, body: m.RotateMachineKeyBody) -> m.Machine:
        """Rotate a device keypair: register a new public key; the old private key stops
        verifying.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/rotate_key",
            body=body,
        )

    async def rotate_secret(self, machine_id: str) -> m.MachineWithSecret:
        """Rotate a machine secret; the old one stops working and a new mk_ is shown once."""
        return await self._t.request(
            method="POST",
            path=f"/v1/machines/{machine_id}/rotate_secret",
        )


class AsyncManagedWaf:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.ManagedWaf:
        """§5 Read the managed AWS WAF configuration and provisioning state."""
        return await self._t.request(
            method="GET",
            path="/v1/managed_waf",
        )

    async def set(self, body: m.SetManagedWafBody | None = None) -> m.ManagedWaf:
        """§5 Configure the managed AWS WAF: scope/region, edge target, token domains, gated
        paths, and the write-only BYO AWS credentials.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/managed_waf",
            body=body,
        )

    async def deprovision(self) -> JSON:
        """§5 Deprovision: disassociate the WebACL from the edge and delete it, then clear the
        stored state.
        """
        return await self._t.request(
            method="POST",
            path="/v1/managed_waf/deprovision",
        )

    async def provision(self) -> JSON:
        """§5 Provision now: idempotently create-or-update the AWS WAF WebACL with the CAPTCHA
        rule and associate it with the edge (ALB or CloudFront).
        """
        return await self._t.request(
            method="POST",
            path="/v1/managed_waf/provision",
        )

    async def status(self) -> m.ManagedWafStatus:
        """§5 Read just the managed AWS WAF provisioning state: status, WebACL id/arn, last
        error and last-provisioned time.
        """
        return await self._t.request(
            method="GET",
            path="/v1/managed_waf/status",
        )


class AsyncMcp:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.McpServer:
        """MCP server descriptor and the tools this key may call."""
        return await self._t.request(
            method="GET",
            path="/v1/mcp",
        )

    async def call(self, body: m.McpRequestBody | None = None) -> m.McpResponse:
        """MCP JSON-RPC endpoint: initialize, tools/list, tools/call, ping."""
        return await self._t.request(
            method="POST",
            path="/v1/mcp",
            body=body,
        )


class AsyncMcpConnector:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.McpConnector:
        """Read the instance's remote MCP connector: enabled state, exposed tool scopes,
        dynamic-registration policy, plus the computed discovery URL, resource identifier
        and whether the resource server exists.
        """
        return await self._t.request(
            method="GET",
            path="/v1/mcp_connector",
        )

    async def set(
        self, body: m.SetMcpConnectorBody | None = None, *, idempotency_key: str | None = None
    ) -> m.McpConnector:
        """Configure the remote MCP connector (enabled, name, exposed_scopes,
        dynamic_registration, allowed_redirect_hosts).
        """
        return await self._t.request(
            method="PUT",
            path="/v1/mcp_connector",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, *, idempotency_key: str | None = None) -> m.McpConnector:
        """Disable the remote MCP connector."""
        return await self._t.request(
            method="DELETE",
            path="/v1/mcp_connector",
            idempotency_key=idempotency_key,
        )


class AsyncMessagingProviders:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.managed_email = _AsyncManagedEmail(transport)
        self.development_email = _AsyncDevelopmentEmail(transport)

    async def list(self) -> m.MessagingProviders:
        """Read the instance's BYOK email and SMS provider config: transport, from-address and
        which secret keys are set.
        """
        return await self._t.request(
            method="GET",
            path="/v1/messaging_providers",
        )

    async def set_email(self, body: m.EmailProviderConfig) -> m.MessagingProvider:
        """Configure the email delivery provider."""
        return await self._t.request(
            method="PUT",
            path="/v1/messaging_providers/email",
            body=body,
        )

    async def set_sms(self, body: m.SmsProviderConfig) -> m.MessagingProvider:
        """Configure the SMS delivery provider."""
        return await self._t.request(
            method="PUT",
            path="/v1/messaging_providers/sms",
            body=body,
        )

    async def delete(self, channel: str, *, force: bool = False) -> m.MessagingProviderDeleteResult:
        """Remove the email or sms provider configuration for the instance.

        Removing the email provider is refused with 409 ``EMAIL_PROVIDER_IN_USE`` while
        email-dependent features are on and nothing else would deliver email (the
        error's ``meta.features`` lists them, e.g. ``"emailCode"``, ``"emailLink"``,
        ``"emailVerification"``, ``"passwordReset"``). Pass ``force=True`` to remove it
        anyway.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/messaging_providers/{channel}",
            query={"force": True} if force else None,
        )

    async def test(
        self, channel: str, body: m.TestMessagingProviderBody | None = None
    ) -> m.MessagingTest:
        """Send a clearly-marked test message to a destination to verify the configured email
        or SMS provider delivers, without triggering a real auth flow.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/messaging_providers/{channel}/test",
            body=body,
        )


class _AsyncManagedEmail:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.ManagedEmail:
        """Read the managed sending domain: status, records, limits and usage (404 when none
        is configured).
        """
        return await self._t.request(
            method="GET",
            path="/v1/messaging_providers/email/managed",
        )

    async def create(self, body: m.CreateManagedEmailBody) -> m.ManagedEmail:
        """Set your sending domain up on your own Resend or Brevo account: pass ``transport``
        with ``config.api_key``, or ``provider_id`` of your configured provider. Returns the
        DNS ``records`` to publish. With ``dns`` Atlas writes them itself (the token is
        write-only).
        """
        return await self._t.request(
            method="POST",
            path="/v1/messaging_providers/email/managed",
            body=body,
        )

    async def verify(self) -> m.ManagedEmail:
        """Re-check the DNS records now; ``verified`` is true once email can be sent."""
        return await self._t.request(
            method="POST",
            path="/v1/messaging_providers/email/managed/verify",
        )

    async def delete(self, *, force: bool = False) -> m.ManagedEmailDeleteResult:
        """Stop using managed email (DNS records are left in place).

        Refused with 409 ``EMAIL_PROVIDER_IN_USE`` while it is the only way the instance can
        send email; pass ``force=True`` to remove it anyway.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/messaging_providers/email/managed",
            query={"force": True} if force else None,
        )


class _AsyncDevelopmentEmail:
    """Your own email provider in development mode: a development instance sends Atlas's
    sign-in emails without a verified domain (``[Atlas test]`` subjects, capped).
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.DevelopmentEmail:
        """Read the email provider in development mode (404 when it is not in development
        mode).
        """
        return await self._t.request(
            method="GET",
            path="/v1/messaging_providers/email/development",
        )

    async def enable(self, body: m.EnableDevelopmentEmailBody) -> m.DevelopmentEmail:
        """Put your email provider in development mode. 409 ``DEVELOPMENT_EMAIL_NOT_ALLOWED``
        on a production instance.
        """
        return await self._t.request(
            method="POST",
            path="/v1/messaging_providers/email/development",
            body=body,
        )

    async def disable(self) -> m.DevelopmentEmailDeleteResult:
        """Put the email provider back in standard mode (the provider and its key stay)."""
        return await self._t.request(
            method="DELETE",
            path="/v1/messaging_providers/email/development",
        )


class AsyncLogoutNotifyEndpoints:
    """Logout fan-out endpoints: downstream services that receive the same signed
    ``logout_token`` as your OIDC apps whenever a session ends.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(
            method="GET",
            path="/v1/logout_notify_endpoints",
        )

    async def create(
        self, body: m.CreateLogoutNotifyEndpointBody, *, idempotency_key: str | None = None
    ) -> m.LogoutNotifyEndpoint:
        """Register an endpoint (public https). With ``oauth_client_id`` it follows one
        client instead of the whole instance.
        """
        return await self._t.request(
            method="POST",
            path="/v1/logout_notify_endpoints",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, endpoint_id: str) -> m.LogoutNotifyEndpoint:
        return await self._t.request(
            method="GET",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}",
        )

    async def update(
        self,
        endpoint_id: str,
        body: m.UpdateLogoutNotifyEndpointBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.LogoutNotifyEndpoint:
        return await self._t.request(
            method="PATCH",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self, endpoint_id: str, *, idempotency_key: str | None = None
    ) -> DeletedObject:
        """Delete an endpoint; its queued deliveries go with it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}",
            idempotency_key=idempotency_key,
        )

    async def list_deliveries(self, endpoint_id: str, *, limit: int | None = None) -> ListPage:
        """The endpoint's delivery log, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}/deliveries",
            query=_q(limit=limit),
        )


class AsyncNetworkAcls:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List network ACLs — per-instance IP allow/deny rules that gate access to the
        instance, in priority order.
        """
        return await self._t.request(
            method="GET",
            path="/v1/network_acls",
        )

    async def create(self, body: m.CreateNetworkAclBody | None = None) -> m.NetworkAcl:
        """Create a network ACL rule (allow|deny, a CIDR or single address, a priority)."""
        return await self._t.request(
            method="POST",
            path="/v1/network_acls",
            body=body,
        )

    async def get(self, acl_id: str) -> m.NetworkAcl:
        """Read one network ACL rule."""
        return await self._t.request(
            method="GET",
            path=f"/v1/network_acls/{acl_id}",
        )

    async def update(self, acl_id: str, body: m.UpdateNetworkAclBody | None = None) -> m.NetworkAcl:
        """Update a network ACL rule's action, cidr, description, priority or enabled flag."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/network_acls/{acl_id}",
            body=body,
        )

    async def delete(self, acl_id: str) -> DeletedObject:
        """Delete a network ACL rule."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/network_acls/{acl_id}",
        )


class AsyncNotifications:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.categories = _AsyncNotificationCategories(transport)
        self.templates = _AsyncNotificationTemplates(transport)

    async def send(self, body: m.SendNotificationBody) -> m.NotificationSend:
        """Send a templated, instance-branded security-notification email to one of your end-
        users, honouring their per-category notification preferences.
        """
        return await self._t.request(
            method="POST",
            path="/v1/notifications",
            body=body,
        )


class _AsyncNotificationCategories:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(self, body: m.CreateNotificationCategoryBody) -> m.NotificationCategory:
        """Create a tenant-defined notification category: a key (unique per instance, cannot
        collide with a built-in) and the user-facing label shown on the end-user preference
        toggle.
        """
        return await self._t.request(
            method="POST",
            path="/v1/notification_categories",
            body=body,
        )

    async def list(self) -> ListPage:
        """List this instance's tenant-defined notification categories."""
        return await self._t.request(
            method="GET",
            path="/v1/notification_categories",
        )

    async def set(self, key: str, body: m.SetNotificationCategoryBody) -> m.NotificationCategory:
        """Update a tenant-defined notification category's user-facing label."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/notification_categories/{key}",
            body=body,
        )

    async def delete(self, key: str) -> m.NotificationCategoryDeleteResult:
        """Delete a tenant-defined notification category."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/notification_categories/{key}",
        )


class _AsyncNotificationTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(self, body: m.CreateNotificationTemplateBody) -> m.NotificationTemplate:
        """Create a tenant-defined notification template: a name (unique per instance), a
        subject and body with `{{variables}}`, and the category whose per-user preference
        gates it.
        """
        return await self._t.request(
            method="POST",
            path="/v1/notification_templates",
            body=body,
        )

    async def list(self) -> ListPage:
        """List this instance's tenant-defined notification templates."""
        return await self._t.request(
            method="GET",
            path="/v1/notification_templates",
        )

    async def get(self, name: str) -> m.NotificationTemplate:
        """Retrieve one tenant-defined notification template by name."""
        return await self._t.request(
            method="GET",
            path=f"/v1/notification_templates/{name}",
        )

    async def set(self, name: str, body: m.SetNotificationTemplateBody) -> m.NotificationTemplate:
        """Update a tenant-defined notification template's subject, body and category by name."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/notification_templates/{name}",
            body=body,
        )

    async def delete(self, name: str) -> m.NotificationTemplateDeleteResult:
        """Delete a tenant-defined notification template by name."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/notification_templates/{name}",
        )


class AsyncOAuthProviders:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self, *, provider: str | Sequence[str] | None = None, configured: bool | None = None
    ) -> ListPage:
        """List the social sign-in provider catalog with which are configured/enabled and each
        derived redirect URI.
        """
        return await self._t.request(
            method="GET",
            path="/v1/oauth_providers",
            query=_q(provider=_csv(provider), configured=configured),
        )

    async def get(self, provider: str) -> m.OAuthProvider:
        """Fetch one social sign-in provider: its catalog entry and configured state, no
        secret.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_providers/{provider}",
        )

    async def upsert(
        self,
        provider: str,
        body: m.UpsertOAuthProviderBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OauthProvider:
        """Set a social sign-in provider's client id/secret (and scopes/settings)."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_providers/{provider}",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, provider: str) -> m.OAuthProviderDeleteResult:
        """Remove a social sign-in provider’s credentials."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_providers/{provider}",
        )

    async def set_enabled(
        self, provider: str, body: m.SetOAuthProviderEnabledBody | None = None
    ) -> m.OAuthProviderSetEnabledResult:
        """Enable or disable a social sign-in provider — this is what turns it on (saving
        credentials via PUT does not).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_providers/{provider}/enabled",
            body=body,
        )

    async def set_scope(
        self, provider: str, body: m.SetOAuthProviderScopeBody | None = None
    ) -> m.OAuthProviderSetScopeResult:
        """Scope a provider to sign-in, sign-up, or both (allow_sign_in / allow_sign_up)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_providers/{provider}/scope",
            body=body,
        )

    async def test(self, provider: str) -> m.OauthConnectionTest:
        """Test a social sign-in provider's stored credentials against the provider's token
        endpoint.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_providers/{provider}/test",
        )


class AsyncOrgLdapConnections:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, organization_id: str | None = None) -> ListPage:
        """List the organization-owned LDAP / AD connections."""
        return await self._t.request(
            method="GET",
            path="/v1/org_ldap_connections",
            query=_q(organization_id=organization_id),
        )

    async def create(
        self,
        body: m.CreateOrgLdapConnectionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgLdapConnection:
        """Create an organization-owned LDAP / AD connection (url, bind_dn, base_dn,
        user_filter, attributes).
        """
        return await self._t.request(
            method="POST",
            path="/v1/org_ldap_connections",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, connection_id: str) -> m.OrgLdapConnection:
        """Fetch one organization-owned LDAP connection."""
        return await self._t.request(
            method="GET",
            path=f"/v1/org_ldap_connections/{connection_id}",
        )

    async def update(
        self,
        connection_id: str,
        body: m.UpdateOrgLdapConnectionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.OrgLdapConnection:
        """Update an organization-owned LDAP connection."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/org_ldap_connections/{connection_id}",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self, connection_id: str, *, idempotency_key: str | None = None
    ) -> DeletedObject:
        """Delete an organization-owned LDAP connection."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/org_ldap_connections/{connection_id}",
            idempotency_key=idempotency_key,
        )

    async def test(
        self, connection_id: str, body: m.TestOrgLdapConnectionBody | None = None
    ) -> m.OrgLdapConnectionTest:
        """Test an organization-owned LDAP connection: attempt a service-account bind and
        report ok/failure.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/org_ldap_connections/{connection_id}/test",
            body=body,
        )


class AsyncOrganizationSettingsSchema:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.OrganizationSettingsSchema:
        """Fetch the instance-wide JSON Schema registered for organization settings."""
        return await self._t.request(
            method="GET",
            path="/v1/organization_settings_schema",
        )

    async def create(
        self, body: m.CreateOrganizationSettingsSchemaBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettingsSchema:
        """Register the instance-wide JSON Schema for organization settings (first
        registration).
        """
        return await self._t.request(
            method="POST",
            path="/v1/organization_settings_schema",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def replace(
        self, body: m.ReplaceOrganizationSettingsSchemaBody, *, idempotency_key: str | None = None
    ) -> m.OrganizationSettingsSchema:
        """Replace the instance-wide organization-settings JSON Schema."""
        return await self._t.request(
            method="PUT",
            path="/v1/organization_settings_schema",
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPca:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_attestors(self) -> m.PcaAttestors:
        """The instance's trusted software-attestor public keys."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/attestors",
        )

    async def set_attestors(self, body: m.SetPcaAttestorsBody) -> m.PcaAttestors:
        """Replace the trusted software-attestor key list."""
        return await self._t.request(
            method="PUT",
            path="/v1/pca/attestors",
            body=body,
        )

    async def unfreeze(self) -> m.PcaFreeze:
        """Clear the instance-wide PCA kill switch."""
        return await self._t.request(
            method="DELETE",
            path="/v1/pca/freeze",
        )

    async def freeze(self, body: m.FreezePcaBody | None = None) -> m.PcaFreeze:
        """Engage the instance-wide PCA kill switch: every PCActn is denied until it is
        cleared.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/freeze",
            body=body,
        )

    async def revoke(self, body: m.CreatePcaRevocationBody) -> m.PcaRevokeResult:
        """Revoke a capability id under a grant; any PCActn whose chain contains it is denied."""
        return await self._t.request(
            method="POST",
            path="/v1/pca/revocations",
            body=body,
        )

    async def deny_step_up(
        self, step_up_id: str, body: m.DenyPcaStepUpBody | None = None
    ) -> m.PcaStepup:
        """Deny a pending step-up: the held action is never anchored."""
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/stepups/{step_up_id}/deny",
            body=body,
        )


class AsyncRadiusClients:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List the RADIUS NAS clients — the VPN/WiFi/firewall devices allowed to authenticate
        this instance's users over RADIUS.
        """
        return await self._t.request(
            method="GET",
            path="/v1/radius_clients",
        )

    async def create(self, body: m.CreateRadiusClientBody | None = None) -> m.RadiusClient:
        """Register a RADIUS NAS client (name, NAS-Identifier, optional source-IP bind, write-
        only shared secret).
        """
        return await self._t.request(
            method="POST",
            path="/v1/radius_clients",
            body=body,
        )

    async def get(self, radius_client_id: str) -> m.RadiusClient:
        """Read one RADIUS NAS client."""
        return await self._t.request(
            method="GET",
            path=f"/v1/radius_clients/{radius_client_id}",
        )

    async def update(
        self, radius_client_id: str, body: m.UpdateRadiusClientBody | None = None
    ) -> m.RadiusClient:
        """Update a RADIUS NAS client's name, NAS-Identifier, source-IP bind, enabled flag or
        shared secret.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/radius_clients/{radius_client_id}",
            body=body,
        )

    async def delete(self, radius_client_id: str) -> DeletedObject:
        """Delete a RADIUS NAS client."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/radius_clients/{radius_client_id}",
        )


class AsyncRateLimitPolicy:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.RateLimitPolicy:
        """Read the per-instance rate-limit policy (sign-in/up create per IP, and BAPI per key)
        and its bounds.
        """
        return await self._t.request(
            method="GET",
            path="/v1/rate_limit_policy",
        )

    async def update(self, body: m.UpdateRateLimitPolicyBody | None = None) -> m.RateLimitPolicy:
        """Tune the per-instance rate-limit budgets."""
        return await self._t.request(
            method="PATCH",
            path="/v1/rate_limit_policy",
            body=body,
        )


class AsyncRedirectUrls:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List the allowlisted OAuth/SSO redirect URLs."""
        return await self._t.request(
            method="GET",
            path="/v1/redirect_urls",
        )

    async def create(self, body: m.CreateRedirectUrlBody | None = None) -> m.RedirectUrl:
        """Add a permitted OAuth/SSO redirect URL (absolute http(s); idempotent on the URL)."""
        return await self._t.request(
            method="POST",
            path="/v1/redirect_urls",
            body=body,
        )

    async def get(self, redirect_url_id: str) -> m.RedirectUrl:
        """Fetch one allowlisted redirect URL."""
        return await self._t.request(
            method="GET",
            path=f"/v1/redirect_urls/{redirect_url_id}",
        )

    async def delete(self, redirect_url_id: str) -> DeletedObject:
        """Remove a redirect URL from the allowlist."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/redirect_urls/{redirect_url_id}",
        )


class AsyncRiskBasedMfa:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.RiskBasedMfa:
        """Read the instance's adaptive (risk-based) MFA policy: enabled, step-up threshold,
        no-factor handling, and the signal weights/toggles.
        """
        return await self._t.request(
            method="GET",
            path="/v1/risk_based_mfa",
        )

    async def update(self, body: m.UpdateRiskBasedMfaBody | None = None) -> m.RiskBasedMfa:
        """Tune adaptive MFA: enable it, set the step-up threshold and the high-risk-no-factor
        policy, and adjust the per-signal weights/toggles.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/risk_based_mfa",
            body=body,
        )


class AsyncScimProvisioningTargets:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List outbound SCIM provisioning targets (downstream SCIM 2.0 endpoints Atlas pushes
        users to).
        """
        return await self._t.request(
            method="GET",
            path="/v1/scim_provisioning_targets",
        )

    async def create(
        self, body: m.CreateScimProvisioningTargetBody, *, idempotency_key: str | None = None
    ) -> m.ScimProvisioningTarget:
        """Create an outbound SCIM provisioning target."""
        return await self._t.request(
            method="POST",
            path="/v1/scim_provisioning_targets",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, target_id: str) -> m.ScimProvisioningTargetGetResult:
        """Read one outbound SCIM provisioning target, including its sync status, cursor and
        last error.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/scim_provisioning_targets/{target_id}",
        )

    async def update(
        self, target_id: str, body: m.UpdateScimProvisioningTargetBody | None = None
    ) -> m.ScimProvisioningTargetGetResult:
        """Update a target's name, base_url (https), attribute_mapping, deprovision_action,
        enabled flag, or status (active/paused).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/scim_provisioning_targets/{target_id}",
            body=body,
        )

    async def delete(self, target_id: str) -> DeletedObject:
        """Delete an outbound SCIM provisioning target."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/scim_provisioning_targets/{target_id}",
        )

    async def sync_group(self, target_id: str, body: m.SyncScimGroupBody) -> m.ScimSyncResult:
        """Force a single group's (organization's) outbound sync now to the downstream /Groups."""
        return await self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{target_id}/sync_group",
            body=body,
        )

    async def sync_user(self, target_id: str, body: m.SyncScimUserBody) -> m.ScimSyncResult:
        """Force a single user's outbound sync now (backfill / re-push)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{target_id}/sync_user",
            body=body,
        )

    async def test(self, target_id: str) -> m.ScimProvisioningTargetTest:
        """Verify connectivity and auth to the downstream (GET ServiceProviderConfig) with the
        target's real bearer, and return the result.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{target_id}/test",
        )


class AsyncSessionExchangeApps:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List registered session-exchange apps (downstream apps that exchange an Atlas
        session for their own) and their back-channel logout endpoints.
        """
        return await self._t.request(
            method="GET",
            path="/v1/session_exchange_apps",
        )

    async def create(
        self, body: m.CreateSessionExchangeAppBody, *, idempotency_key: str | None = None
    ) -> m.SessionExchangeApp:
        """Register a session-exchange app and its backchannel_logout_uri."""
        return await self._t.request(
            method="POST",
            path="/v1/session_exchange_apps",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, app_id: str) -> m.SessionExchangeApp:
        """Fetch one session-exchange app."""
        return await self._t.request(
            method="GET",
            path=f"/v1/session_exchange_apps/{app_id}",
        )

    async def update(
        self,
        app_id: str,
        body: m.UpdateSessionExchangeAppBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.SessionExchangeApp:
        """Update a session-exchange app's name, backchannel_logout_uri or audience."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/session_exchange_apps/{app_id}",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, app_id: str, *, idempotency_key: str | None = None) -> DeletedObject:
        """Delete a session-exchange app; its queued back-channel logout deliveries cascade
        with it.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/session_exchange_apps/{app_id}",
            idempotency_key=idempotency_key,
        )


class AsyncSmsTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """List SMS templates with their built-in defaults and any instance override."""
        return await self._t.request(
            method="GET",
            path="/v1/sms_templates",
        )

    async def create(self, body: m.CreateSmsTemplateBody | None = None) -> m.SmsTemplate:
        """Set an SMS body template."""
        return await self._t.request(
            method="POST",
            path="/v1/sms_templates",
            body=body,
        )

    async def get(self, name: str) -> m.SmsTemplate:
        """Read one SMS template: its built-in default and the instance override."""
        return await self._t.request(
            method="GET",
            path=f"/v1/sms_templates/{name}",
        )

    async def update(self, name: str, body: m.UpdateSmsTemplateBody | None = None) -> m.SmsTemplate:
        """Update an SMS template body or its enabled flag."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/sms_templates/{name}",
            body=body,
        )

    async def delete(self, name: str) -> m.SmsTemplate:
        """Revert an SMS template to the Atlas built-in default body."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/sms_templates/{name}",
        )

    async def preview(
        self, name: str, body: m.PreviewSmsTemplateBody | None = None
    ) -> m.SmsTemplatePreview:
        """Render an SMS body with a sample code — never a live OTP — for review."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sms_templates/{name}/preview",
            body=body,
        )


class AsyncSsoOnboarding:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_profiles(self) -> ListPage:
        """List self-service SSO onboarding profiles (the templates tickets are issued from)."""
        return await self._t.request(
            method="GET",
            path="/v1/sso_onboarding_profiles",
        )

    async def create_profile(
        self,
        body: m.CreateSsoOnboardingProfileBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.SsoOnboardingProfile:
        """Create a self-service SSO onboarding profile: allowed connection types and an
        optional bound organization.
        """
        return await self._t.request(
            method="POST",
            path="/v1/sso_onboarding_profiles",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_profile(self, profile_id: str) -> m.SsoOnboardingProfile:
        """Fetch one onboarding profile."""
        return await self._t.request(
            method="GET",
            path=f"/v1/sso_onboarding_profiles/{profile_id}",
        )

    async def delete_profile(self, profile_id: str) -> DeletedObject:
        """Delete an onboarding profile; its issued tickets cascade away with it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/sso_onboarding_profiles/{profile_id}",
        )

    async def create_ticket(
        self,
        profile_id: str,
        body: m.CreateSsoOnboardingTicketBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Issue a scoped, one-time, expiring onboarding ticket for one organization."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_onboarding_profiles/{profile_id}/tickets",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke_ticket(self, ticket_id: str) -> m.SsoOnboardingRevokeTicketResult:
        """Revoke a pending onboarding ticket so it can no longer configure a connection."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_onboarding_tickets/{ticket_id}/revoke",
        )


class AsyncTesting:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create_test_instance(
        self, body: m.CreateTestInstanceBody | None = None, *, idempotency_key: str | None = None
    ) -> m.TestInstance:
        """Get (creating on first call) your production instance's paired test-mode
        (development) sibling — an isolated instance with its own pk_test/sk_test, user pool
        and JWKS.
        """
        return await self._t.request(
            method="POST",
            path="/v1/test_instance",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def purge_test_users(
        self, body: m.PurgeTestUsersBody | None = None, *, idempotency_key: str | None = None
    ) -> m.TestingPurgeTestUsersResult:
        """Dispose test users in bulk (development instances only): soft-delete every user
        whose email carries a reserved test token (+clerk_test / +atlas_test).
        """
        return await self._t.request(
            method="POST",
            path="/v1/test_users/purge",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_testing_token(self) -> m.TestingToken:
        """Mint a short-lived signed testing token (development instances only) that
        @atlasauth/testing presents to the sign-in gate to skip the human-only CAPTCHA.
        """
        return await self._t.request(
            method="POST",
            path="/v1/testing_tokens",
        )


class AsyncTickets:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(self, body: m.CreateTicketBody) -> m.Ticket:
        """Mint a one-time capability ticket: an opaque, high-entropy handle carrying an
        arbitrary JSON payload a holder can later redeem (e.g. a scoped download grant or
        short-lived action token).
        """
        return await self._t.request(
            method="POST",
            path="/v1/tickets",
            body=body,
        )

    async def redeem(self, body: m.RedeemTicketBody) -> m.RedeemedTicket:
        """Redeem a capability ticket server-to-server and return its payload."""
        return await self._t.request(
            method="POST",
            path="/v1/tickets/redeem",
            body=body,
        )


class AsyncTokens:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def verify(self, body: m.VerifyTokenBody | None = None) -> m.TokenVerification:
        """Authoritatively verify a session token, including revocation."""
        return await self._t.request(
            method="POST",
            path="/v1/tokens/verify",
            body=body,
        )


class AsyncUsage:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, *, days: int | None = None) -> m.Usage:
        """Read usage analytics: daily sign-in/active-user series with peaks and trends over a
        window, plus monthly active users.
        """
        return await self._t.request(
            method="GET",
            path="/v1/usage",
            query=_q(days=days),
        )


class AsyncUserExports:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(self, *, idempotency_key: str | None = None) -> m.Job:
        """Produce a job whose result is a present()-serialised array of the instance's users."""
        return await self._t.request(
            method="POST",
            path="/v1/user_exports",
            idempotency_key=idempotency_key,
        )


class AsyncUserImports:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateUserImportBody | None = None, *, idempotency_key: str | None = None
    ) -> m.Job:
        """Bulk-create users from an array, deduping by verified email, through the same path
        sign-up uses.
        """
        return await self._t.request(
            method="POST",
            path="/v1/user_imports",
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPlatformApps:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        tag: str | None = None,
        archived: bool | None = None,
        include_archived: bool | None = None,
    ) -> ListPage:
        """List the apps (instances) this platform owns."""
        return await self._t.request(
            method="GET",
            path="/v1/platform/apps",
            query=_q(tag=tag, archived=archived, include_archived=include_archived),
        )

    async def create(
        self, body: m.CreatePlatformAppBody | None = None, *, idempotency_key: str | None = None
    ) -> m.PlatformAppProvisioned:
        """Provision a new app (instance) owned by the platform: mints its publishable key,
        signing key and first secret key.
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/apps",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def accept_transfer(
        self,
        body: m.AcceptPlatformAppTransferBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Accept a transfer by transfer_token: move the app's ownership to the calling
        platform and re-parent it to its account.
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/apps/accept_transfer",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def bulk_delete(
        self, body: m.BulkDeletePlatformAppsBody | None = None
    ) -> m.BulkDeleteResult:
        """X8 housekeeping: delete up to 100 owned apps in one call, for tidying throwaway
        probes.
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/apps/bulk_delete",
            body=body,
        )

    async def claim(
        self, body: m.ClaimPlatformAppBody | None = None, *, idempotency_key: str | None = None
    ) -> JSON:
        """Claim an accountless app into the calling platform by its claim_token."""
        return await self._t.request(
            method="POST",
            path="/v1/platform/apps/claim",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, app_id: str) -> m.App:
        """Disable an owned app: refuse sign-ins and sign-ups via its kill switches."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/apps/{app_id}",
        )

    async def get(self, app_id: str) -> m.PlatformApp:
        """Fetch one owned app."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{app_id}",
        )

    async def update(
        self, app_id: str, body: m.UpdatePlatformAppBody | None = None
    ) -> m.PlatformApp:
        """Update an owned app's safe config subset (name, allowed_origins, and X8 housekeeping
        tags).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/platform/apps/{app_id}",
            body=body,
        )

    async def archive(self, app_id: str) -> m.PlatformApp:
        """X8 housekeeping: archive an owned app so it drops out of the default app listing."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/archive",
        )

    async def list_instances(self, app_id: str) -> ListPage:
        """List every instance under an owned app — its development/production siblings."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{app_id}/instances",
        )

    async def create_instance(
        self,
        app_id: str,
        body: m.CreatePlatformAppInstanceBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PlatformAppWithSecret:
        """Provision an additional instance (e.g. development beside production) under an owned
        app.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/instances",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def rotate_instance_secret(
        self,
        app_id: str,
        instance_id: str,
        body: m.RotatePlatformSecretBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PlatformInstanceSecretRotation:
        """Mint a new secret key for one instance under an owned app, revealed once. The
        prior keys stay valid for ``overlap_seconds`` (default 259200 = 72 hours, at most
        604800; ``0`` revokes them now), like ``rotate_secret``.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/instances/{instance_id}/rotate_secret",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def rotate_secret(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/rotate_secret",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_secret_keys(self, app_id: str) -> ListPage:
        """List an owned app's currently-valid secret keys (S3) — the primary key plus any
        prior key still inside its rotation overlap window.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{app_id}/secret_keys",
        )

    async def transfer(self, app_id: str, *, idempotency_key: str | None = None) -> m.AppTransfer:
        """Initiate a transfer of an owned app: returns a one-time transfer_token bound to it
        (hashed, single-use, expiring).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/transfer",
            idempotency_key=idempotency_key,
        )

    async def unarchive(self, app_id: str) -> m.PlatformApp:
        """X8 housekeeping: clear an owned app's archive flag, returning it to the default app
        listing.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/unarchive",
        )


class AsyncPlatformAccountlessApps:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self, body: m.CreateAccountlessAppBody | None = None, *, idempotency_key: str | None = None
    ) -> m.AccountlessApp:
        """Mint an app owned by no platform and return a one-time claim_token (hashed at rest,
        single-use, expiring).
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/accountless_apps",
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPlatformAtlasIdApps:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> m.AtlasIdAppList:
        """List the Sign in with Atlas apps registered to this platform's account, with the
        issuer and discovery URL.
        """
        return await self._t.request(
            method="GET",
            path="/v1/platform/atlas_id_apps",
        )

    async def create(
        self, body: m.CreateAtlasIdAppBody | None = None, *, idempotency_key: str | None = None
    ) -> m.AtlasIdApp:
        """Register a Sign in with Atlas app (an OpenID Connect client on
        https://atlasauth.net) for this platform's account.
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/atlas_id_apps",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def preview_design(self, body: m.PreviewDesignBody) -> m.DesignPreview:
        """Preview a Sign in with Atlas app design without saving it: the compiled bundle plus
        the rendered Sign in with Atlas page (the Atlas trust strip, the destination line
        and "Secured by Atlas" are always there).
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/atlas_id_apps/design/preview",
            body=body,
        )

    async def delete(self, app_id: str) -> DeletedObject:
        """Delete a Sign in with Atlas app."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{app_id}",
        )

    async def get(self, app_id: str) -> m.AtlasIdApp:
        """Fetch one Sign in with Atlas app, including user_count (people who have approved
        it).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}",
        )

    async def update(self, app_id: str, body: m.UpdateAtlasIdAppBody | None = None) -> m.AtlasIdApp:
        """Update a Sign in with Atlas app: name, redirect_uris, post_logout_redirect_uris ([]
        clears them), backchannel_logout_uri / frontchannel_logout_uri (empty or null
        clears) and their *_session_required flags,...
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/platform/atlas_id_apps/{app_id}",
            body=body,
        )

    async def rotate_secret(
        self, app_id: str, body: m.RotateAtlasIdAppSecretBody | None = None
    ) -> m.AtlasIdApp:
        """Rotate a confidential app's client_secret (returned once). The previous one keeps
        working for ``overlap_seconds`` (default 86400 = 24 hours; ``0`` revokes it now).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/rotate_secret",
            body=body,
        )

    async def list_backchannel_deliveries(
        self, app_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> m.BackchannelLogoutDeliveryList:
        """The app's back-channel logout delivery log, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/backchannel_deliveries",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def test_backchannel_logout(self, app_id: str) -> m.BackchannelLogoutTest:
        """Send a test back-channel logout to the app now."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/backchannel_logout/test",
        )

    async def preflight(self, app_id: str) -> m.AtlasIdAppPreflight:
        """Check one app's setup, in the instance preflight's finding shape."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/preflight",
        )

    async def find_users(self, app_id: str, email: str) -> m.AtlasIdAppUserList:
        """Privacy requests: is this person one of the app's users? Exact match on a
        verified email; anyone else gets the same empty list.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/users",
            query={"email": email},
        )

    async def revoke_grant(self, app_id: str, grant_id: str) -> m.AtlasIdGrantRevocation:
        """Revoke one user's grant (``grant_id`` from ``find_users``); the next sign-in shows
        the consent screen again.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{app_id}/grants/{grant_id}",
        )

    async def move_origin(self, app_id: str, body: m.OriginMoveBody) -> m.OriginMove:
        """Move the app's URLs from one origin to another. ``dry_run`` writes nothing."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/move_origin",
            body=body,
        )

    async def rotate_webhook_secret(
        self, app_id: str, body: m.RotateAtlasIdAppSecretBody | None = None
    ) -> m.AtlasIdApp:
        """Rotate the app's webhook signing secret (``webhook_secret``, returned once). By
        default the previous secret stops signing at once; with ``overlap_seconds`` it signs
        each delivery too until ``webhook_previous_secret_expires_at``.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/webhook/rotate_secret",
            body=body,
        )


class AsyncPlatformAtlasIdPublisher:
    """The account's Sign in with Atlas publisher name and DNS-verified domain."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.AtlasIdPublisher:
        """Read the publisher (404 until claimed)."""
        return await self._t.request(
            method="GET",
            path="/v1/platform/atlas_id_publisher",
        )

    async def set(self, body: m.SetAtlasIdPublisherBody) -> m.AtlasIdPublisher:
        """Claim a publisher name and domain; returns the TXT record to publish."""
        return await self._t.request(
            method="PUT",
            path="/v1/platform/atlas_id_publisher",
            body=body,
        )

    async def update(self, body: m.UpdateAtlasIdPublisherBody) -> m.AtlasIdPublisher:
        """Turn publisher-wide consent (``skip_consent``) on or off."""
        return await self._t.request(
            method="PATCH",
            path="/v1/platform/atlas_id_publisher",
            body=body,
        )

    async def delete(self) -> m.AtlasIdPublisherDeleteResult:
        """Remove the publisher claim."""
        return await self._t.request(
            method="DELETE",
            path="/v1/platform/atlas_id_publisher",
        )

    async def verify(self) -> m.AtlasIdPublisher:
        """Look up the TXT record now (``record_found``)."""
        return await self._t.request(
            method="POST",
            path="/v1/platform/atlas_id_publisher/verify",
        )


class AsyncPlatformConfigChangelog:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        action: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        since: str | None = None,
    ) -> CursorPage:
        """Config change history for the account's Sign in with Atlas apps."""
        return await self._t.request(
            method="GET",
            path="/v1/platform/config_changelog",
            query=_q(action=action, limit=limit, starting_after=starting_after, since=since),
        )


class AsyncPlatformDesignAssets:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def upload(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        kind: Literal["background", "logo"] | None = None,
    ) -> m.DesignAsset:
        """Upload a design image owned by the platform's account, for Sign in with Atlas app
        designs.
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/design/assets",
            query=_q(kind=kind),
            content=data,
            content_type=content_type or _sniff_image_type(data),
        )

    async def list(self) -> ListPage:
        """List the design images owned by the platform's account, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/platform/design/assets",
        )

    async def delete(self, asset_id: str) -> m.DesignAssetDeleteResult:
        """Delete a design image owned by the platform's account."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/design/assets/{asset_id}",
        )
