"""Asynchronous resource namespaces — the async peer of :mod:`resources`.

Same method↔endpoint map, same shapes, over an :class:`httpx.AsyncClient`.
Generated from :mod:`resources` by ``scripts/gen_async.py``; edit the sync
module and regenerate rather than editing this file.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Sequence
from typing import Any, Literal
from urllib.parse import urlencode

from . import models as m
from ._transport import _AsyncTransport
from ._types import JSON, CursorPage, DeletedObject, ListPage
from .resources import (
    BETTER_AUTH_IMPORT_IN_FLIGHT,
    BETTER_AUTH_IMPORT_PART_BYTES,
    _audience_query,
    _csv,
    _dry,
    _enc,
    _json,
    _meta,
    _q,
    _sniff_image_type,
    split_bundle_parts,
)


class AsyncUsers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.required_actions = _AsyncUsersRequiredActions(transport)
        self.notes = _AsyncUsersNotes(transport)
        self.guardians = _AsyncUsersGuardians(transport)
        self.search = _AsyncUsersSearch(transport)
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
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        offset: int | None = None,
        query: str | None = None,
        email_address: str | None = None,
        username: str | None = None,
        phone_number: str | None = None,
        external_id: str | None = None,
        banned: bool | None = None,
        email_verified: bool | None = None,
        organization_id: str | None = None,
        created_after: int | None = None,
        created_before: int | None = None,
        updated_after: int | None = None,
        updated_before: int | None = None,
        order_by: Literal[
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
            "last_sign_in_at",
            "-last_sign_in_at",
        ]
        | None = None,
        include_total_count: bool | None = None,
        include_deleted: bool | None = None,
    ) -> CursorPage:
        """List and search users. Every filter combines with AND. Page by cursor
        (``starting_after``) or, with ``offset``, by offset. ``query`` searches email,
        username, names, phone and ids; ``created_after`` / ``created_before`` are epoch
        ms, as are ``updated_after`` / ``updated_before`` (sync users changed since a
        checkpoint, with ``order_by="updated_at"``); ``include_total_count`` adds
        ``total_count`` to the page. Soft-deleted users are left out unless
        ``include_deleted=True``.
        """

        def _b(v: bool | None) -> str | None:
            return None if v is None else ("true" if v else "false")

        return await self._t.request(
            method="GET",
            path="/v1/users",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                offset=offset,
                query=query,
                email_address=email_address,
                username=username,
                phone_number=phone_number,
                external_id=external_id,
                banned=_b(banned),
                email_verified=_b(email_verified),
                organization_id=organization_id,
                created_after=created_after,
                created_before=created_before,
                updated_after=updated_after,
                updated_before=updated_before,
                order_by=order_by,
                include_total_count=_b(include_total_count),
                include_deleted=_b(include_deleted),
            ),
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
        expires_in_seconds: int | None = None,
        expires_at: int | None = None,
        idempotency_key: str | None = None,
    ) -> m.User:
        """Ban a user and revoke every session. Permanent unless ``expires_in_seconds`` or
        ``expires_at`` (epoch ms) is given: a timed ban lifts itself (``user.unbanned``).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/ban",
            body=_q(
                reason=reason,
                note=note,
                expires_in_seconds=expires_in_seconds,
                expires_at=expires_at,
            )
            or None,
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

    async def history(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        action: str | None = None,
    ) -> CursorPage:
        """The user change history, newest first: every profile, metadata and status change (ban,
        lock, directives and their reversal) with who made it, the reason and expiry, and each
        changed field with its value before and after. A password change and private_metadata
        values are recorded as redacted (the field name only). Pages with starting_after.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/history",
            query=_q(limit=limit, starting_after=starting_after, action=action),
        )

    async def minor_status(
        self,
        id: str,
    ) -> m.UsersMinorStatusResponse:
        """A user's parental-consent state (not_required for anyone at or above the age of
        digital consent) and their guardian links, newest first.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/minor_status",
        )

    async def assess_minor(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersAssessMinorResponse:
        """Re-assess a user from their date-of-birth trait now (for users created before age
        gating was turned on). 400 when compliance.minors is off.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/minor_status/assess",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def create_link(
        self,
        id: str,
        body: m.UsersCreateLinkBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersCreateLinkResponse:
        """Mint an email-verification or password-reset link (and code) for a user WITHOUT
        sending it, for support tools and invite flows that deliver it themselves. type
        "email_verification" needs an unverified address (default: the primary); the url opens
        GET /v1/client/email_addresses/verify and the code works wherever the address is
        verified by code. type "password_reset" needs a verified address and returns the url
        and/or code the instance's password-reset setting would have mailed, plus the reset
        attempt_id; redeeming it is the ordinary reset (it still asks for the second factor
        and sets a new password). Single-use, expires_in_seconds 60 to 86400 (default 3600).
        Audited as user.link_generated, never with the secret. Treat the response as a
        credential. → 201.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/links",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_device_keys(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List a user’s device keys (native biometric sign-in). Never returns key material."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/device_keys",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def delete_device_key(
        self,
        id: str,
        key_id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Revoke one of a user’s device keys so that device can no longer sign in. Scoped to the
        user; the account holder is notified when account-change notices are on.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(id)}/device_keys/{_enc(key_id)}",
            query=_q(dry_run=dry_run),
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

    async def resend(self, org_id: str, invitation_id: str) -> JSON:
        """Resend a pending invitation: same id and role, a fresh expiry."""
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/invitations/{invitation_id}/resend",
        )


class _AsyncOrgTeams:
    """Teams inside an organization (``/v1/organizations/{id}/teams``)."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, org_id: str, *, user_id: str | None = None) -> CursorPage:
        """The organization's teams; ``user_id`` narrows to the teams that user is in."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/teams",
            query=_q(user_id=user_id),
        )

    async def create(self, org_id: str, body: m.TeamBody) -> m.Team:
        return await self._t.request(
            method="POST", path=f"/v1/organizations/{org_id}/teams", body=body
        )

    async def get(self, org_id: str, team_id: str) -> m.Team:
        return await self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/teams/{team_id}"
        )

    async def update(self, org_id: str, team_id: str, body: m.TeamBody) -> m.Team:
        return await self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/teams/{team_id}", body=body
        )

    async def delete(self, org_id: str, team_id: str) -> DeletedObject:
        return await self._t.request(
            method="DELETE", path=f"/v1/organizations/{org_id}/teams/{team_id}"
        )

    async def list_members(self, org_id: str, team_id: str) -> CursorPage:
        return await self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/teams/{team_id}/members"
        )

    async def add_member(self, org_id: str, team_id: str, user_id: str) -> m.TeamMember:
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/teams/{team_id}/members",
            body={"user_id": user_id},
        )

    async def remove_member(self, org_id: str, team_id: str, user_id: str) -> m.TeamMember:
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/teams/{team_id}/members/{user_id}",
        )


class _AsyncOrgRoles:
    """The roles an organization can assign: the instance roles plus its own custom
    roles (``organization_id`` set)."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, org_id: str, *, own: bool | None = None) -> CursorPage:
        """``own=True`` lists only the organization's own custom roles."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/roles",
            query=_q(own="true" if own else None),
        )

    async def create(self, org_id: str, body: m.CreateOrgRoleBody) -> m.OrgRole:
        return await self._t.request(
            method="POST", path=f"/v1/organizations/{org_id}/roles", body=body
        )

    async def update(self, org_id: str, role_id: str, body: m.UpdateOrgRoleBody) -> m.OrgRole:
        return await self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/roles/{role_id}", body=body
        )

    async def delete(self, org_id: str, role_id: str, *, reassign_to: str | None = None) -> JSON:
        """Delete one of the organization's own roles; ``reassign_to`` (a role key) moves
        members and pending invitations first (409 ``ROLE_IN_USE`` without it)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/roles/{role_id}",
            query=_q(reassign_to=reassign_to),
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
        self.webhook_endpoints = _AsyncOrganizationsWebhookEndpoints(transport)
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
        self.teams = _AsyncOrgTeams(transport)
        self.roles = _AsyncOrgRoles(transport)

    async def get_by_slug(self, slug: str) -> m.Organization:
        """Fetch an organization by slug (case-insensitive)."""
        return await self._t.request(method="GET", path=f"/v1/organizations/by_slug/{slug}")

    async def check_slug(self, slug: str) -> m.SlugCheck:
        """Whether a slug is valid and free, for a create-organization form."""
        return await self._t.request(
            method="GET", path="/v1/organizations/check_slug", query={"slug": slug}
        )

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

    async def list_connected_apps(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the apps (OAuth clients) that hold an active grant in this organization's
        context, one entry per grant.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(id)}/connected_apps",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def revoke_connected_app(
        self,
        id: str,
        grant_id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Revoke one connected app grant of the organization: its tokens and any session minted
        from it stop working. Emits grant.revoked; audited as
        organization.connected_app_revoked.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{_enc(id)}/connected_apps/{_enc(grant_id)}",
            query=_q(dry_run=dry_run),
        )

    async def get_connection_secret(
        self,
        id: str,
        connection_id: str,
        *,
        version: str | None = None,
    ) -> m.OrganizationsGetConnectionSecretResponse:
        """The same read, scoped to an organization: 404 unless the connection is owned by that
        organization. Needs connections:secret_read; audited.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(id)}/connections/{_enc(connection_id)}/secret",
            query=_q(version=version),
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

    async def get_token(
        self,
        session_id: str,
        for_: str,
        *,
        audience_hint: str | None = None,
        audience: str | None = None,
        cbid: str | None = None,
        audience_params: dict[str, str] | None = None,
    ) -> m.SessionToken:
        """``getToken({for})`` on the server: mint an integration token for a session, for a
        product that trusts Atlas sessions (e.g. ``for_="referalli"``).

        A per-call audience picks the token's ``aud`` for this one mint, when the integration's
        ``per_call_audience`` permits it (otherwise 403): ``audience`` is the whole audience,
        ``cbid`` is the site id of an integration whose parameter is ``cbid``, and
        ``audience_params`` carries any integration's own parameter (``{"tenant": "t1"}``).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/sessions/{_enc(session_id)}/integration_tokens/{_enc(for_)}",
            query=_audience_query(audience, cbid, audience_params) or None,
            body={"audience_hint": audience_hint} if audience_hint else None,
        )

    async def set_custom_data(
        self, session_id: str, custom_data: dict[str, Any] | None
    ) -> m.Session:
        """Replace the session's custom data (``None`` clears it). At most 2 KB; only an
        active session can be changed. Not for secrets: the signed-in user can read it.
        Sends the ``session.updated`` webhook."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/sessions/{session_id}/custom_data",
            body={"custom_data": custom_data},
        )

    async def update_custom_data(self, session_id: str, patch: dict[str, Any]) -> m.Session:
        """Merge keys into the session's custom data; a key set to ``None`` is removed."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/sessions/{session_id}/custom_data",
            body={"custom_data": patch},
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

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        include_deprecated: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> JSON:
        """List endpoints (cursor-paginated). ``include_deprecated`` adds the superseded
        event spellings to the catalog; ``metadata`` filters on ``metadata[key]=value``."""
        return await self._t.request(
            method="GET",
            path="/v1/webhook_endpoints",
            query=_meta(
                metadata,
                limit=limit,
                starting_after=starting_after,
                include_deprecated=include_deprecated,
            )
            or None,
        )

    async def get(self, endpoint_id: str) -> m.WebhookEndpoint:
        """Read one endpoint, with its health fields (``failing_since``,
        ``last_failing_since``, ``consecutive_failures``, ...)."""
        return await self._t.request(
            method="GET", path=f"/v1/webhook_endpoints/{_enc(endpoint_id)}"
        )

    async def create(
        self,
        body: m.CreateWebhookEndpointBody,
        *,
        idempotency_key: str | None = None,
        dry_run: bool = False,
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path="/v1/webhook_endpoints",
            body=body,
            idempotency_key=idempotency_key,
            query=_dry(dry_run),
        )

    async def put_by_url(self, body: dict[str, Any], *, idempotency_key: str | None = None) -> JSON:
        """Create the endpoint for ``body["url"]`` or update it when one exists (idempotent
        provisioning)."""
        return await self._t.request(
            method="PUT",
            path="/v1/webhook_endpoints/by_url",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def redeliver_window(self, endpoint_id: str, body: dict[str, Any] | None = None) -> JSON:
        """Redeliver every delivery in a window. ``body``: ``since`` (epoch ms, or
        ``"failing_since"`` for the start of the endpoint's last failure streak), ``until``,
        ``status``, ``event_type``."""
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(endpoint_id)}/redeliver",
            body=body if body is not None else {},
        )

    async def replay(self, endpoint_id: str, body: dict[str, Any] | None = None) -> JSON:
        """Replay the events an endpoint missed since ``body["since"]`` (epoch ms, or
        ``"failing_since"`` to replay everything since it started failing)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(endpoint_id)}/replay",
            body=body if body is not None else {},
        )

    async def delete(self, endpoint_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/webhook_endpoints/{endpoint_id}")

    async def list_deliveries(
        self,
        endpoint_id: str,
        *,
        limit: int | None = None,
        status: str | None = None,
        event_type: str | None = None,
        since: int | str | None = None,
        until: int | str | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List an endpoint's recent deliveries, newest first (``limit`` 1-100), filtered by
        ``status``, ``event_type`` and a ``since`` / ``until`` window; cursor-paginated. Each
        delivery carries ``latency_ms``."""
        return await self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries",
            query=_q(
                limit=limit,
                status=status,
                event_type=event_type,
                since=since,
                until=until,
                starting_after=starting_after,
            ),
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

    async def test(self, endpoint_id: str, *, wait: int | None = None) -> m.WebhookDeliveryAttempt:
        """Send a synthetic webhook.test event to this endpoint only. With ``wait`` (seconds)
        the call holds until the delivery finishes and returns its outcome."""
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/test",
            query=_q(wait=wait),
        )


class AsyncWebhooks:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.endpoints = _AsyncWebhookEndpoints(transport)

    async def deliveries(
        self,
        endpoint_id: str,
        *,
        limit: int | None = None,
        status: str | None = None,
        event_type: str | None = None,
        since: int | str | None = None,
        until: int | str | None = None,
        starting_after: str | None = None,
    ) -> JSON:
        """List an endpoint's deliveries. Same as ``endpoints.list_deliveries``."""
        return await self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries",
            query=_q(
                limit=limit,
                status=status,
                event_type=event_type,
                since=since,
                until=until,
                starting_after=starting_after,
            ),
        )

    async def egress_ips(self) -> JSON:
        """The IP addresses Atlas delivers webhooks from (allow-list them)."""
        return await self._t.request(method="GET", path="/v1/meta/egress_ips")


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
        self.app_settings = _AsyncOAuthClientsAppSettings(transport)
        self.workload_identity = _AsyncOAuthClientsWorkloadIdentity(transport)
        self.trusted_issuers = _AsyncOAuthClientsTrustedIssuers(transport)
        self.login_requests = _AsyncOAuthClientsLoginRequests(transport)
        self.consent_requests = _AsyncOAuthClientsConsentRequests(transport)
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

    async def get_exchange_policy(
        self,
        id: str,
    ) -> m.OauthClientsGetExchangePolicyResponse:
        """Read the token-exchange policy of an OAuth client (the defaults, with
        configured=false, when none is set).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(id)}/exchange_policy",
        )

    async def set_exchange_policy(
        self,
        id: str,
        body: m.OauthClientsSetExchangePolicyBody,
        *,
        dry_run: bool | None = None,
    ) -> m.OauthClientsSetExchangePolicyResponse:
        """Set the token-exchange policy of an OAuth client: allowed audiences and scopes,
        whether it may impersonate (no actor_token), whether delegation needs may_act, and the
        maximum act-chain depth. Audited as oauth_exchange_policy.updated.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(id)}/exchange_policy",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete_exchange_policy(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Remove the token-exchange policy of an OAuth client, restoring the defaults."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{_enc(id)}/exchange_policy",
            query=_q(dry_run=dry_run),
        )

    async def set_profile(
        self,
        id: str,
        body: m.OauthClientsSetProfileBody,
        *,
        dry_run: bool | None = None,
    ) -> m.OauthClientsSetProfileResponse:
        """Assign a policy profile to an OAuth client (profile null clears it). The client must
        already conform (auth method, redirect URIs); the profile is then enforced at
        /oauth2/authorize, /oauth2/par and /oauth2/token.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(id)}/profile",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def set_delegated_ui(
        self,
        id: str,
        body: m.OauthClientsSetDelegatedUiBody,
        *,
        dry_run: bool | None = None,
    ) -> m.OauthClientsSetDelegatedUiResponse:
        """Set (or clear, with null) the URLs of your own sign-in and consent pages for an OAuth
        client. /oauth2/authorize then sends the browser there with a login_challenge /
        consent_challenge instead of Atlas’s pages. A client URL overrides the instance-wide
        oauthProvider.loginUrl / consentUrl.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(id)}/delegated_ui",
            query=_q(dry_run=dry_run),
            body=body,
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

    async def preview_profile_mapping(
        self, connection_id: str, body: m.ProfileMappingPreviewBody
    ) -> m.ProfileMappingPreview:
        """OIDC: run the connection's profile mapping (or the body's) against a sample."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/profile_mapping/preview",
            body=body,
        )

    async def list_signing_keys(self, connection_id: str) -> ListPage:
        """OIDC: the connection's private_key_jwt signing keys
        (:class:`~atlas_backend.models.UpstreamSigningKey`)."""
        return await self._t.request(
            method="GET", path=f"/v1/sso_connections/{connection_id}/signing_keys"
        )

    async def rotate_signing_key(
        self, connection_id: str, *, alg: Literal["RS256", "PS256", "ES256"] | None = None
    ) -> m.UpstreamSigningKey:
        """Generate a new active key; the previous one turns ``retiring`` (still published)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/signing_keys",
            body=_q(alg=alg),
        )

    async def retire_signing_key(self, connection_id: str, kid: str) -> m.UpstreamSigningKey:
        """Retire a non-active key (it leaves the JWKS)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/signing_keys/{kid}/retire",
        )

    async def get_saml_encryption_key(self, connection_id: str) -> m.SamlEncryptionKey:
        """The SAML connection's SP encryption certificate(s)."""
        return await self._t.request(
            method="GET", path=f"/v1/sso_connections/{connection_id}/saml_encryption_key"
        )

    async def create_saml_encryption_key(
        self, connection_id: str, *, idempotency_key: str | None = None
    ) -> m.SamlEncryptionKey:
        """Generate the SP encryption key pair, or ROTATE it when one exists: the current
        pair becomes the previous one (still advertised and accepted until
        :meth:`retire_previous_saml_encryption_key`)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/saml_encryption_key",
            idempotency_key=idempotency_key,
        )

    async def retire_previous_saml_encryption_key(self, connection_id: str) -> m.SamlEncryptionKey:
        """Finish a rotation: stop accepting the previous encryption key."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/sso_connections/{connection_id}/saml_encryption_key/previous",
        )

    async def delete_saml_encryption_key(self, connection_id: str) -> m.SamlEncryptionKey:
        """Turn assertion encryption off (refused while encrypted assertions are required)."""
        return await self._t.request(
            method="DELETE", path=f"/v1/sso_connections/{connection_id}/saml_encryption_key"
        )


class AsyncCustomOAuthProviders:
    """Your own upstream OAuth 2.0 / OpenID Connect login providers, with Atlas as the
    relying party: endpoints (or just an OIDC issuer), token-endpoint client
    authentication (incl. private_key_jwt with an Atlas-held key), a declarative
    profile mapping, upstream logout and third-party initiated login. The provider then
    signs users in like any built-in one, under its ``provider_key``."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        """Each ``data`` item is a :class:`~atlas_backend.models.CustomOAuthProvider`."""
        return await self._t.request(method="GET", path="/v1/custom_oauth_providers")

    async def get(self, provider_id: str) -> m.CustomOAuthProvider:
        return await self._t.request(method="GET", path=f"/v1/custom_oauth_providers/{provider_id}")

    async def create(
        self, body: m.CreateCustomOAuthProviderBody, *, idempotency_key: str | None = None
    ) -> m.CustomOAuthProvider:
        return await self._t.request(
            method="POST",
            path="/v1/custom_oauth_providers",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self, provider_id: str, body: m.CustomOAuthProviderSettings
    ) -> m.CustomOAuthProvider:
        """Patch a provider; a ``None`` value clears a nullable setting."""
        return await self._t.request(
            method="PATCH", path=f"/v1/custom_oauth_providers/{provider_id}", body=body
        )

    async def delete(self, provider_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/custom_oauth_providers/{provider_id}"
        )

    async def discover(
        self, issuer: str, *, discovery_url: str | None = None
    ) -> m.OidcDiscoveryResult:
        """Fetch and validate an issuer's OpenID configuration (for autofill)."""
        return await self._t.request(
            method="POST",
            path="/v1/custom_oauth_providers/discover",
            body=_q(issuer=issuer, discovery_url=discovery_url),
        )

    async def preview_profile_mapping(
        self, body: m.ProfileMappingPreviewBody
    ) -> m.ProfileMappingPreview:
        """Run a mapping (``body["profile_mapping"]``) against a pasted sample."""
        return await self._t.request(
            method="POST", path="/v1/custom_oauth_providers/profile_mapping/preview", body=body
        )

    async def preview_provider_profile_mapping(
        self, provider_id: str, body: m.ProfileMappingPreviewBody
    ) -> m.ProfileMappingPreview:
        """Run a provider's stored mapping (or the body's) against a pasted sample."""
        return await self._t.request(
            method="POST",
            path=f"/v1/custom_oauth_providers/{provider_id}/profile_mapping/preview",
            body=body,
        )

    async def list_signing_keys(self, provider_id: str) -> ListPage:
        """The provider's private_key_jwt signing keys."""
        return await self._t.request(
            method="GET", path=f"/v1/custom_oauth_providers/{provider_id}/signing_keys"
        )

    async def rotate_signing_key(
        self, provider_id: str, *, alg: Literal["RS256", "PS256", "ES256"] | None = None
    ) -> m.UpstreamSigningKey:
        """Generate a new active key; the previous one turns ``retiring`` (still published)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/custom_oauth_providers/{provider_id}/signing_keys",
            body=_q(alg=alg),
        )

    async def retire_signing_key(self, provider_id: str, kid: str) -> m.UpstreamSigningKey:
        """Retire a non-active key (it leaves the JWKS)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/custom_oauth_providers/{provider_id}/signing_keys/{kid}/retire",
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

    async def update(self, token_id: str, body: m.UpdateScimTokenBody) -> m.ScimToken:
        """Change a SCIM token's name, scopes (``["read"]`` = read-only) or role mappings.
        The secret is unchanged."""
        return await self._t.request(method="PATCH", path=f"/v1/scim_tokens/{token_id}", body=body)


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

    async def set_app_attestation_secret(
        self,
        body: m.AttackProtectionSetAppAttestationSecretBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.AttackProtectionSetAppAttestationSecretResponse:
        """Store the Play Integrity response-decryption key (base64 AES-256) for app attestation.
        Write-only; the public verification key is
        attackProtection.appAttestation.android.verificationKey.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/attack_protection/app_attestation_secret",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def remove_app_attestation_secret(
        self,
        *,
        dry_run: bool | None = None,
        kind: Literal["play_integrity", "devicecheck"] | None = None,
    ) -> m.AttackProtectionRemoveAppAttestationSecretResponse:
        """Remove a stored attestation secret: the Play Integrity decryption key (default) or,
        with kind=devicecheck, the Apple DeviceCheck key. That platform then refuses every
        request.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/attack_protection/app_attestation_secret",
            query=_q(dry_run=dry_run, kind=kind),
        )


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
        ``Sessions.create`` (``POST /v1/sessions``), which mints a real
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
        """List Actions (tenant code that runs at auth-pipeline hooks)."""
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
        """Replace the ordered list of Actions bound to a trigger — the single source of truth
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

    async def calls(
        self,
        id: str,
        *,
        limit: int | None = None,
        status: Literal["ok", "denied", "failed", "timeout", "error", "invalid_response"]
        | None = None,
        test: bool | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The call log of an `http` Action (an Action that calls your own endpoint), newest
        first, with 24 hour stats: calls, denied, failed, timeouts and p95 latency. Real calls
        and dry-run tests are both logged (`test`). 409 for a `node` Action.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/actions/{_enc(id)}/calls",
            query=_q(limit=limit, status=status, test=test, starting_after=starting_after),
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
        """Verify a presented ak_ secret. Send ``required_scopes`` to require scopes; a live
        key refused by its own policy answers ``valid: False`` with a ``code``
        (``insufficient_scope``, ``rate_limited`` or ``usage_exhausted``)."""
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
        self.providers = _AsyncBillingProviders(transport)

    async def sync_seats(self, subject_type: str, subject_id: str) -> m.BillingSeats:
        """Sync a per-seat subscription's Stripe quantity to the org's current member count
        (proration applied).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subjects/{subject_type}/{subject_id}/sync_seats",
        )

    async def record_usage(self, body: m.RecordUsageBody | None = None) -> m.BillingUsage:
        """Report metered usage for a subject (idempotent on idempotency_key); mirrored to
        the provider when the plan is metered. ``feature`` counts it against one provider
        feature; ``subscription_id`` attributes it when the subject holds several.
        """
        return await self._t.request(
            method="POST",
            path="/v1/billing/usage",
            body=body,
        )

    async def get_settings(self) -> m.BillingSettings:
        """How numeric limits merge across a subject's several subscriptions."""
        return await self._t.request(method="GET", path="/v1/billing/settings")

    async def update_settings(self, body: m.UpdateBillingSettingsBody) -> m.BillingSettings:
        return await self._t.request(method="PUT", path="/v1/billing/settings", body=body)

    async def check_feature(self, body: m.CheckBillingFeatureBody) -> m.BillingFeatureCheck:
        """May a subject use a feature? Asked live of Autumn/Commet when the subject is on
        one; otherwise answered from the resolved entitlement and this period's usage."""
        return await self._t.request(method="POST", path="/v1/billing/check", body=body)


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

    async def sync_entitlements(self, plan_id: str) -> m.BillingPlan:
        """Mirror a plan's features and limits from its provider (Autumn, Commet)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/plans/{plan_id}/sync_entitlements",
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

    async def get(self, subscription_id: str) -> m.Subscription:
        """One subscription (a subject may hold several: a base plan plus add-ons)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/billing/subscriptions/{subscription_id}",
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

    async def change(self, subscription_id: str, body: m.ChangeSubscriptionBody) -> m.Subscription:
        """Switch a subscription to another plan or interval on the billing provider, now
        (prorated) or at the period end (``schedule_at_period_end``)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{subscription_id}/change",
            body=body,
        )

    async def cancel(
        self, subscription_id: str, *, immediately: bool | None = None
    ) -> m.Subscription:
        """Cancel at the end of the current period, or now with ``immediately=True``."""
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{subscription_id}/cancel",
            body=_q(immediately=immediately),
        )

    async def restore(self, subscription_id: str) -> m.Subscription:
        """Undo a cancellation scheduled for the period end."""
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{subscription_id}/restore",
        )


class _AsyncBillingProviders:
    """The instance's own billing provider credentials (bring your own key): stripe,
    polar, dodo, creem, chargebee, autumn or commet. Secrets are write-only."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> CursorPage:
        return await self._t.request(method="GET", path="/v1/billing/providers")

    async def get(self, provider: str) -> m.BillingProvider:
        return await self._t.request(method="GET", path=f"/v1/billing/providers/{provider}")

    async def set(self, provider: str, body: m.SetBillingProviderBody) -> m.BillingProvider:
        """Store credentials (merged onto what is stored, encrypted at rest)."""
        return await self._t.request(
            method="PUT", path=f"/v1/billing/providers/{provider}", body=body
        )

    async def test(self, provider: str) -> m.BillingProviderTest:
        """Make one read-only call with the stored credentials."""
        return await self._t.request(method="POST", path=f"/v1/billing/providers/{provider}/test")

    async def delete(self, provider: str, *, force: bool | None = None) -> JSON:
        """Remove a provider's credentials; refused while subscriptions or plans depend on
        it unless ``force=True``."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/billing/providers/{provider}",
            query=_q(force="true" if force else None),
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
        since: int | str | None = None,
        until: int | str | None = None,
        order: Literal["asc", "desc"] | None = None,
    ) -> CursorPage:
        """Read the product activity feed (events), filterable by type and time and cursor-
        paginated, with the list of event types this instance has actually emitted. ``since``
        / ``until`` bound the window (epoch ms or ISO date); ``order="asc"`` reads forward
        from a checkpoint.
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
                    "since": since,
                    "until": until,
                    "order": order,
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

    async def list_users(
        self,
        id: str,
        body: m.FgaListUsersBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.FgaListUsersResponse:
        """List the users that have a relation on an object, filtered to one user type (or to
        `type#relation` usersets via `user_filters[0].relation`). Exact for wildcards
        (`type:*` plus `excluded_users` under `but not`), nested groups and contextual tuples;
        tuple conditions are evaluated against `context`. Pages with `page_size` /
        `continuation_token`; `consistency` / `consistency_token` behave as on check.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(id)}/list-users",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def read_changes(
        self,
        id: str,
        *,
        type: str | None = None,
        page_size: int | None = None,
        continuation_token: str | None = None,
        start_time: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """Read the store’s tuple changelog: every tuple write and delete in commit order,
        resumable with `continuation_token` (returned even on the last page — pass it later to
        receive only newer changes). Filter by object `type` and `start_time`.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(id)}/changes",
            query=_q(
                type=type,
                page_size=page_size,
                continuation_token=continuation_token,
                start_time=start_time,
                limit=limit,
                starting_after=starting_after,
            ),
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

    async def list_users(
        self,
        store: str,
        body: m.OpenfgaListUsersBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.OpenfgaListUsersResponse:
        """List the users that have a relation on an object (OpenFGA-wire ListUsers): concrete
        users, usersets (`user_filters[0].relation`), and the `type:*` wildcard with
        `excluded_users`. Honours contextual tuples and tuple conditions; pages with
        `page_size` / `continuation_token`.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/openfga/stores/{_enc(store)}/list-users",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def read_changes(
        self,
        store: str,
        *,
        type: str | None = None,
        page_size: int | None = None,
        continuation_token: str | None = None,
        start_time: str | None = None,
    ) -> m.OpenfgaReadChangesResponse:
        """Read the tuple changelog (OpenFGA-wire ReadChanges): every tuple write and delete in
        order, resumable with `continuation_token` (the token is returned even on the last
        page — pass it later to receive only newer changes).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{_enc(store)}/changes",
            query=_q(
                type=type,
                page_size=page_size,
                continuation_token=continuation_token,
                start_time=start_time,
            ),
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
        self.integrations = _AsyncInstanceIntegrations(transport)
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

    async def set_account_linking_trust(self, trust: dict[str, str]) -> m.Instance:
        """Write ``auth_config.accountLinkingTrust``: keys are an exact provider key, a
        ``prefix*`` or ``*``; values ``always`` (vouch for the provider's email, for
        linking only), ``verified`` or ``never`` (refuse with 409
        ``IDENTITY_ALREADY_LINKED``). An account that never proved its email is never
        linked."""
        return await self._t.request(
            method="PATCH",
            path="/v1/instance",
            body={"auth_config": {"accountLinkingTrust": trust}},
        )

    async def set_captcha_config(self, captcha: dict[str, Any]) -> m.Instance:
        """Merge ``auth_config.captcha``: ``provider`` (see ``CAPTCHA_PROVIDERS``),
        ``siteKey``, ``widget``, ``minScore``, per-flow / per-action overrides, and for
        Vercel BotID ``attestationUrl`` (an https URL or a root-relative path)."""
        return await self._t.request(
            method="PATCH",
            path="/v1/instance",
            body={"auth_config": {"captcha": captcha}},
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

    async def preflight(
        self,
        *,
        min_severity: Literal["error", "warning", "info"] | None = None,
        include_suppressed: bool | None = None,
    ) -> m.Preflight:
        """Check your setup in one call. ``min_severity`` keeps only findings at least that
        severe (``ok`` still covers every finding); ``include_suppressed`` also lists the
        suppressed ones."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/preflight",
            query=_q(min_severity=min_severity, include_suppressed=include_suppressed),
        )

    async def unknown_fields_report(self, *, days: int | None = None) -> JSON:
        """Which unknown body fields your writes sent (ignored, or refused in strict mode),
        aggregated over the last ``days``."""
        return await self._t.request(
            method="GET", path="/v1/instance/unknown_fields_report", query=_q(days=days)
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

    async def rotate_events_secret(
        self,
        product: str,
        body: m.InstanceIntegrationsRotateEventsSecretBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.InstanceIntegrationsRotateEventsSecretResponse:
        """Rotate the signing secret of the integration's event receiver. The new secret is
        revealed exactly once. By default (`overlap_seconds` 0) the old secret stops signing
        at once. With `overlap_seconds` (at most 604800 = 7 days) every delivery carries two
        signatures in `Atlas-Signature` (`v1,<new> v1,<old>`, the new one first), so the
        service verifies with either secret while it deploys the new one; after that only the
        new secret signs. `previous_secret_expires_at` says when the old secret stops signing
        (epoch ms), or null when it already has. Audited as
        integration.<id>.events_secret_rotated. 404 when the integration has no event
        receiver.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/integrations/{_enc(product)}/events_secret/rotate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
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

    async def get_call(self, call_id: str) -> m.ReferralCall:
        """One call of the delivery log, by id or the platform's request id."""
        return await self._t.request(method="GET", path=f"/v1/instance/referrals/calls/{call_id}")

    async def install(self, provider: str, body: dict[str, Any] | None = None) -> JSON:
        """One-click install of a referral platform (``referalli``; the old id ``referally``
        is accepted): Atlas connects, registers its signing secret and enables referrals."""
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/referrals/{_enc(provider)}/install",
            body=body,
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
        their real sign-up time. Users already reported are skipped. Referrals must be on
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

    async def list_before_user_create_calls(
        self,
        *,
        limit: int | None = None,
        status: Literal["ok", "failed", "timeout", "error", "invalid_response"] | None = None,
        test: bool | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The hook's delivery log, newest first (kept 30 days)."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/hooks/before_user_create/calls",
            query=_q(
                limit=limit,
                status=status,
                test=None if test is None else ("true" if test else "false"),
                starting_after=starting_after,
            ),
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

    async def list_signing_keys(self) -> m.SigningKeyList:
        """The published token-signing keys: ``current`` and, inside a rotation's grace
        window, ``previous`` with ``retires_at``."""
        return await self._t.request(method="GET", path="/v1/instance/signing_keys")

    async def rotate_signing_key(
        self, body: m.RotateSigningKeyBody | None = None
    ) -> m.SigningKeyRotation:
        """Rotate the instance signing key, optionally switching ``alg`` (RS256 or ES256)."""
        return await self._t.request(
            method="POST", path="/v1/instance/signing_keys/rotate", body=body or {}
        )

    async def get_signing_key_provider(self) -> m.SigningKeyProviderSettings:
        """The key management service the signing key lives in (``local`` when none)."""
        return await self._t.request(method="GET", path="/v1/instance/signing_key_provider")

    async def set_signing_key_provider(
        self, body: m.SetSigningKeyProviderBody
    ) -> m.SigningKeyProviderSettings:
        """Sign every token with a key in your own AWS KMS, Google Cloud KMS or Azure Key
        Vault. The result carries the ``rotation`` onto the KMS key."""
        return await self._t.request(
            method="PUT", path="/v1/instance/signing_key_provider", body=body
        )

    async def remove_signing_key_provider(
        self, body: m.RotateSigningKeyBody | None = None
    ) -> m.SigningKeyProviderSettings:
        """Stop using the KMS: rotate back to a key Atlas holds and forget the credentials."""
        return await self._t.request(
            method="DELETE", path="/v1/instance/signing_key_provider", body=body or {}
        )

    async def set_wallet_rpc_secret(self, *, chain_id: int, url: str) -> m.WalletRpcSecret:
        """Store (write-only, encrypted) the wallet RPC endpoint for an EIP-155 chain, used
        by wallet token gating and the Sign in with Ethereum ENS lookup. An empty ``url``
        removes it; the URL is never returned."""
        return await self._t.request(
            method="PUT",
            path="/v1/instance/wallet_rpc_secret",
            body={"chain_id": chain_id, "url": url},
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


class AsyncBetterAuthImports:
    """Migrate from Better Auth: import a sealed bundle made by the Better Auth
    exporter (``npx atlas-better-auth-export``).

    1. :meth:`get_public_key` — the key the exporter seals the bundle to.
    2. :meth:`upload` (or :meth:`create`, :meth:`upload_part` per part and
       :meth:`finalize`) — Atlas opens the bundle and runs the dry run.
    3. Read the import's ``report``, then :meth:`apply`. Applying again after a
       failure resumes where it stopped; every record is an idempotent upsert.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_public_key(self) -> m.BetterAuthImportKey:
        """The instance's import public key (created on first read)."""
        return await self._t.request(
            method="GET",
            path="/v1/better_auth_imports/public_key",
        )

    async def rotate_public_key(
        self, *, idempotency_key: str | None = None
    ) -> m.BetterAuthImportKey:
        """Replace the import key. The old one is retired: bundles sealed to it no
        longer finalize (``import_key_retired``)."""
        return await self._t.request(
            method="POST",
            path="/v1/better_auth_imports/public_key/rotate",
            idempotency_key=idempotency_key,
        )

    async def create(
        self,
        body: m.CreateBetterAuthImportBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.BetterAuthImport:
        """Start an import (status ``uploading``), optionally with import options."""
        return await self._t.request(
            method="POST",
            path="/v1/better_auth_imports",
            body=body or {},
            idempotency_key=idempotency_key,
        )

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        """List imports, newest first. Each ``data`` item is a
        :class:`~atlas_backend.models.BetterAuthImport`."""
        return await self._t.request(
            method="GET",
            path="/v1/better_auth_imports",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(self, import_id: str) -> m.BetterAuthImport:
        """Fetch an import: status, progress, the dry-run ``report`` and the ``result``."""
        return await self._t.request(
            method="GET",
            path=f"/v1/better_auth_imports/{import_id}",
        )

    async def upload_part(
        self, import_id: str, part: int, data: str | bytes
    ) -> m.BetterAuthImportPart:
        """Upload part ``part`` (1-based) of the sealed bundle: whole lines, at most
        10 MiB. Re-sending a part replaces it."""
        if isinstance(data, bytes):
            # Raw bytes go up as-is (text/plain): the server reads them as the part's lines.
            return await self._t.request(
                method="PUT",
                path=f"/v1/better_auth_imports/{import_id}/parts/{part}",
                content=data,
                content_type="text/plain; charset=utf-8",
            )
        return await self._t.request(
            method="PUT",
            path=f"/v1/better_auth_imports/{import_id}/parts/{part}",
            body={"data": data},
        )

    async def finalize(self, import_id: str) -> m.BetterAuthImport:
        """Close the upload: Atlas checks the parts and the key, then runs the dry run
        (inline up to 4 MiB, ``analyzing`` in the background above that)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/better_auth_imports/{import_id}/finalize",
        )

    async def dry_run(
        self, import_id: str, body: m.CreateBetterAuthImportBody | None = None
    ) -> m.BetterAuthImport:
        """Run the dry run again; new ``options`` replace the stored ones."""
        return await self._t.request(
            method="POST",
            path=f"/v1/better_auth_imports/{import_id}/dry_run",
            body=body or {},
        )

    async def apply(
        self, import_id: str, body: m.ApplyBetterAuthImportBody | None = None
    ) -> m.BetterAuthImport:
        """Import (or resume a ``failed`` import from its cursor). Pass
        ``{"confirm_conflicts": True}`` when the dry run reported conflicts."""
        return await self._t.request(
            method="POST",
            path=f"/v1/better_auth_imports/{import_id}/apply",
            body=body or {},
        )

    async def delete(self, import_id: str) -> m.BetterAuthImportDeleted:
        """Remove the import and its stored bundle; data already imported stays."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/better_auth_imports/{import_id}",
        )

    async def list_jwks(self) -> CursorPage:
        """The Better Auth JWT keys Atlas publishes in the instance JWKS for the
        cutover. Each ``data`` item is a :class:`~atlas_backend.models.ImportedJwk`."""
        return await self._t.request(
            method="GET",
            path="/v1/better_auth_imports/jwks",
        )

    async def delete_jwk(self, kid: str) -> m.ImportedJwkDeleted:
        """Stop publishing one imported Better Auth JWT key."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/better_auth_imports/jwks/{kid}",
        )

    async def upload(
        self,
        bundle: str | bytes,
        *,
        options: m.BetterAuthImportOptions | None = None,
        part_bytes: int = BETTER_AUTH_IMPORT_PART_BYTES,
        on_part: Callable[[int, int], None] | None = None,
    ) -> m.BetterAuthImport:
        """Create an import, upload the sealed bundle in line-aligned parts of at most
        ``part_bytes`` and finalize it. Returns the finalized import (``ready`` /
        ``invalid``, or ``analyzing`` for a large bundle — see :meth:`wait_for`)."""
        parts = split_bundle_parts(bundle, part_bytes)
        if not parts:
            raise ValueError("The bundle is empty.")
        created = await self.create({"options": options} if options else None)
        import_id = created.get("id") if isinstance(created, dict) else None
        if not import_id:
            raise ValueError("Atlas did not return an import id.")
        for i, part in enumerate(parts, start=1):
            await self.upload_part(import_id, i, part)
            if on_part is not None:
                on_part(i, len(parts))
        return await self.finalize(import_id)

    async def wait_for(
        self,
        import_id: str,
        *,
        interval: float = 2.0,
        timeout: float = 6 * 3600.0,
        on_progress: Callable[[m.BetterAuthImport], None] | None = None,
    ) -> m.BetterAuthImport:
        """Poll until the import leaves ``analyzing`` / ``queued`` / ``applying`` and
        return it (``ready``, ``invalid``, ``completed`` or ``failed``). Raises
        :class:`TimeoutError` after ``timeout`` seconds."""
        deadline = time.monotonic() + timeout
        while True:
            imp = await self.get(import_id)
            if on_progress is not None:
                on_progress(imp)
            if imp.get("status") not in BETTER_AUTH_IMPORT_IN_FLIGHT:
                return imp
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Timed out waiting for Better Auth import {import_id} "
                    f"(status {imp.get('status')})."
                )
            await asyncio.sleep(interval)


class AsyncBetterAuthBridge:
    """The Better Auth session bridge: during a migration window a returning user's
    Better Auth session is exchanged, once, for an Atlas session — nobody is signed
    out by the switch. See :func:`atlas_backend.exchange_better_auth_session` and the
    framework integrations' ``ATLAS_BETTER_AUTH_BRIDGE`` setting."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.BetterAuthBridgeSettings:
        """The bridge settings and exchange counts (``live_fallback.has_secret``, never
        the secret)."""
        return await self._t.request(
            method="GET",
            path="/v1/migrations/better_auth/bridge",
        )

    async def update(
        self, body: m.UpdateBetterAuthBridgeBody, *, idempotency_key: str | None = None
    ) -> m.BetterAuthBridgeSettings:
        """Create or update the settings. Every field is optional and merged onto the
        stored ones; ``live_fallback.secret`` is write-only (omit to keep, ``None`` to
        clear)."""
        return await self._t.request(
            method="PUT",
            path="/v1/migrations/better_auth/bridge",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, *, idempotency_key: str | None = None) -> m.BetterAuthBridgeDeleted:
        """Remove the settings: the bridge is off and the stored secret is deleted."""
        return await self._t.request(
            method="DELETE",
            path="/v1/migrations/better_auth/bridge",
            idempotency_key=idempotency_key,
        )

    async def exchange(
        self,
        token: str,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
        remember: bool | None = None,
    ) -> m.BetterAuthExchangeResponse:
        """Exchange a Better Auth session (the raw cookie value or the bare token) for
        an Atlas session, once. Returns ``session_tokens`` or, when a second factor is
        owed, a ``sign_in_attempt``. ``client_ip`` / ``user_agent`` are the END USER's,
        forwarded so Atlas's guards, risk and geo checks and the device record see the
        user rather than your server. Raises :class:`AtlasError` on refusal — use
        :func:`atlas_backend.exchange_better_auth_session` for a classified result."""
        headers: dict[str, str] = {}
        if client_ip:
            headers["x-atlas-client-ip"] = client_ip
        if user_agent:
            headers["x-atlas-client-user-agent"] = user_agent
        body: dict[str, Any] = {"token": token}
        if remember is False:
            body["remember"] = False
        return await self._t.request(
            method="POST",
            path="/v1/migrations/better_auth/exchange",
            body=body,
            headers=headers,
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

    async def get_channel(self, channel: str) -> m.MessagingProvider:
        """Read one channel's provider configuration (``email`` or ``sms``)."""
        return await self._t.request(method="GET", path=f"/v1/messaging_providers/{_enc(channel)}")

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
        self.sync_runs = _AsyncOrgLdapConnectionsSyncRuns(transport)

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

    async def get_sync(
        self,
        id: str,
    ) -> m.OrgLdapConnectionsGetSyncResponse:
        """Read the directory-sync settings of an organization LDAP / Active Directory connection
        (schedule, filters, group-to-role mapping, disable-on-removal).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/org_ldap_connections/{_enc(id)}/sync",
        )

    async def set_sync(
        self,
        id: str,
        body: m.OrgLdapConnectionsSetSyncBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Set the directory-sync settings. Fields you omit keep their value. Enabling requires
        an active connection and schedules the first run immediately; disabling clears the
        schedule. Role mappings are matched in order, by group DN.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/org_ldap_connections/{_enc(id)}/sync",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def get_relay(
        self,
        id: str,
    ) -> m.OrgLdapConnectionsGetRelayResponse:
        """Which relay agent an organization LDAP connection reaches its directory through, if
        any.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/org_ldap_connections/{_enc(id)}/relay",
        )

    async def set_relay(
        self,
        id: str,
        body: m.OrgLdapConnectionsSetRelayBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Route an LDAP connection through a relay agent (agent_id), or back to a direct
        connection (null). The agent must be active and allow the LDAP server.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/org_ldap_connections/{_enc(id)}/relay",
            query=_q(dry_run=dry_run),
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

    async def list_events(
        self,
        *,
        user_id: str | None = None,
        level: str | None = None,
        limit: int | None = None,
        before: str | None = None,
    ) -> ListPage:
        """The risk-event timeline (every scored sign-in), newest first. ``before`` is an ISO
        timestamp cursor on ``created_at``; ``limit`` is 1-200.
        """
        return await self._t.request(
            method="GET",
            path="/v1/risk_events",
            query=_q(user_id=user_id, level=level, limit=limit, before=before),
        )

    async def event_metrics(self, *, days: int | None = None) -> m.RiskEventMetrics:
        """Counts per level/action/mode over the last ``days`` (1-90, default 7)."""
        return await self._t.request(
            method="GET",
            path="/v1/risk_events/metrics",
            query=_q(days=days),
        )

    async def event_feedback(
        self, risk_event_id: str, body: m.RiskEventFeedbackBody | None = None
    ) -> m.RiskEvent:
        """Mark a scored sign-in ``legit`` or ``fraud``; the weight of each signal that fired
        moves by 5 (up for fraud, down for legit).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/risk_events/{risk_event_id}/feedback",
            body=body,
        )

    async def fraud_lookup(self, body: m.FraudLookupBody | None = None) -> m.FraudLookup:
        """Allow / challenge / block verdict for a sign-up, sign-in or checkout from the client
        IP, user agent, SDK ``device_id``, optional device features and email.
        """
        return await self._t.request(
            method="POST",
            path="/v1/fraud/lookup",
            body=body,
        )

    async def set_reputation_secret(
        self,
        body: m.RiskBasedMfaSetReputationSecretBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.RiskBasedMfaSetReputationSecretResponse:
        """Store (write-only, encrypted) the API key of your IP-reputation provider (ipqs, spur
        or minfraud; minFraud uses "<account id>:<license key>"). Then set
        `reputation.provider` on PATCH /v1/risk_based_mfa. Lookups are cached and fail open: a
        provider outage never blocks a sign-in.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/risk_based_mfa/reputation_secret",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def remove_reputation_secret(
        self,
        *,
        dry_run: bool | None = None,
        provider: str | None = None,
    ) -> m.RiskBasedMfaRemoveReputationSecretResponse:
        """Remove a stored IP-reputation provider key (default: the configured provider). IP
        lookups for that provider stop; sign-in is unaffected.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/risk_based_mfa/reputation_secret",
            query=_q(dry_run=dry_run, provider=provider),
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
        metadata: dict[str, Any] | None = None,
    ) -> ListPage:
        """List the apps (instances) this platform owns; ``metadata`` filters on
        ``metadata[key]=value``."""
        return await self._t.request(
            method="GET",
            path="/v1/platform/apps",
            query=_meta(metadata, tag=tag, archived=archived, include_archived=include_archived)
            or None,
        )

    async def create(
        self,
        body: m.CreatePlatformAppBody | None = None,
        *,
        idempotency_key: str | None = None,
        dry_run: bool = False,
    ) -> m.PlatformAppProvisioned:
        """Provision a new app (instance) owned by the platform: mints its publishable key,
        signing key and first secret key. ``external_ref`` makes the call idempotent per
        reference; ``dry_run=True`` previews it.
        """
        return await self._t.request(
            method="POST",
            path="/v1/platform/apps",
            body=body,
            idempotency_key=idempotency_key,
            query=_dry(dry_run),
        )

    async def create_secret_key(
        self,
        app_id: str,
        body: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Mint another secret key for an owned app (scopes, ``owner``, ``expires_at``,
        ``allowed_origins``, ``external_ref``)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/secret_keys",
            body=body if body is not None else {},
            idempotency_key=idempotency_key,
        )

    async def clone_config(
        self, app_id: str, body: dict[str, Any], *, dry_run: bool = False
    ) -> JSON:
        """Copy another app's configuration (``from_app_id``) onto this one."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/clone_config",
            body=body,
            query=_dry(dry_run),
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
        self.provisioned_accounts = AsyncPlatformAtlasIdProvisionedAccounts(transport)

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

    async def preflight(self, app_id: str) -> m.AtlasIdAppPreflightDetail:
        """Check one app's setup, in the instance preflight's finding shape."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/preflight",
        )

    async def find_users(self, app_id: str, email: str) -> m.AtlasIdAppUserList:
        """Privacy requests: is this person one of the app's users? Exact match on a
        verified email; anyone else gets the same empty list. An instance secret key of the
        instance that manages the app (see ``set_managed_by``) can call this route too, and
        ``atlas_id_grants.lookup`` is the same call on the instance client.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/users",
            query={"email": email},
        )

    async def revoke_grant(self, app_id: str, grant_id: str) -> m.AtlasIdGrantRevocation:
        """Revoke one user's grant (``grant_id`` from ``find_users``); the next sign-in shows
        the consent screen again. An instance secret key of the instance that manages the app
        can call this route too (``atlas_id_grants.revoke_grant`` on the instance client).
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{app_id}/grants/{grant_id}",
        )

    async def set_managed_by(self, app_id: str, instance_id: str | None) -> m.AtlasIdAppManagedBy:
        """Hand the app's grant management to an instance of the same account
        (``managed_via: "adopted"``), or take it back with ``None``. That instance's secret
        key, scoped to ``privacy:grants:revoke`` or ``atlas_id_grants:*``, then lists and
        revokes the app's grants, so a data-rights tool never needs the platform key.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/platform/atlas_id_apps/{app_id}/managed_by",
            body={"instance_id": instance_id},
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


def _secret_recipient_headers(secret_recipient: str | None) -> dict[str, str] | None:
    """Ask Atlas to seal the shown-once password to this key (``x25519:<base64>``)."""
    return {"X-Secret-Recipient": secret_recipient} if secret_recipient else None


class AsyncPlatformAtlasIdProvisionedAccounts:
    """Test and review accounts for one Sign in with Atlas app (reviewer logins, CI,
    demos). Needs the ``platform:atlas_id_apps:provision`` scope, or the per-app
    ``atlas_id_apps:<app id>:provision`` scope. The password comes back exactly once, on
    ``create`` and ``rotate_password``: as ``password``, or as ``sealed_password`` when a
    ``secret_recipient`` is sent (per call, or on the client).
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, app_id: str) -> m.AtlasIdProvisionedAccountList:
        """The app's test accounts, with the account-wide cap (``limit``) and ``total``."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{_enc(app_id)}/provisioned_accounts",
        )

    async def create(
        self,
        app_id: str,
        body: m.CreateAtlasIdProvisionedAccountBody,
        *,
        idempotency_key: str | None = None,
        secret_recipient: str | None = None,
    ) -> m.AtlasIdProvisionedAccount:
        """Create a test account confined to this app. The password is returned once."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{_enc(app_id)}/provisioned_accounts",
            body=body,
            idempotency_key=idempotency_key,
            headers=_secret_recipient_headers(secret_recipient),
        )

    async def get(self, app_id: str, account_id: str) -> m.AtlasIdProvisionedAccount:
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{_enc(app_id)}/provisioned_accounts/{_enc(account_id)}",
        )

    async def remove(self, app_id: str, account_id: str) -> m.AtlasIdProvisionedAccountDeleted:
        """Delete the account and end every session and grant it holds."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{_enc(app_id)}/provisioned_accounts/{_enc(account_id)}",
        )

    async def rotate_password(
        self,
        app_id: str,
        account_id: str,
        body: m.RotateAtlasIdProvisionedPasswordBody | None = None,
        *,
        secret_recipient: str | None = None,
    ) -> m.AtlasIdProvisionedAccount:
        """A new password (yours, or one Atlas generates), returned once."""
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{_enc(app_id)}/provisioned_accounts/{_enc(account_id)}/password",
            body=body,
            headers=_secret_recipient_headers(secret_recipient),
        )


class AsyncPlatformDomains:
    """Domains the account verified by DNS; they gate test sign-in mode and the
    test-account domain restriction."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> m.AccountDomainList:
        return await self._t.request(method="GET", path="/v1/platform/domains")

    async def claim(self, domain: str) -> m.AccountDomain:
        """Claim a domain; returns the TXT record to publish."""
        return await self._t.request(
            method="POST", path="/v1/platform/domains", body={"domain": domain}
        )

    async def check(self, domain_id: str) -> m.AccountDomain:
        """Check the DNS record now (``POST /v1/platform/domains/{id}/verify``)."""
        return await self._t.request(
            method="POST", path=f"/v1/platform/domains/{_enc(domain_id)}/verify"
        )

    async def verify(self, domain_id: str) -> m.AccountDomain:
        """Alias of :meth:`check`."""
        return await self.check(domain_id)

    async def remove(self, domain_id: str) -> Any:
        return await self._t.request(
            method="DELETE", path=f"/v1/platform/domains/{_enc(domain_id)}"
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


class AsyncAppRoles:
    """Instance-wide user roles (``/v1/app_roles``), not tied to any organization. A
    user's app roles ride on their session token as ``app_roles`` / ``app_permissions``;
    check them offline with :func:`has_app_role` / :func:`has_app_permission`.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> CursorPage:
        return await self._t.request(method="GET", path="/v1/app_roles")

    async def create(self, body: m.CreateAppRoleBody) -> m.AppRole:
        return await self._t.request(method="POST", path="/v1/app_roles", body=body)

    async def get(self, role_id: str) -> m.AppRole:
        """By id or key."""
        return await self._t.request(method="GET", path=f"/v1/app_roles/{role_id}")

    async def update(self, role_id: str, body: m.UpdateAppRoleBody) -> m.AppRole:
        return await self._t.request(method="PATCH", path=f"/v1/app_roles/{role_id}", body=body)

    async def delete(self, role_id: str) -> DeletedObject:
        return await self._t.request(method="DELETE", path=f"/v1/app_roles/{role_id}")

    async def list_users(
        self, role_id: str, *, limit: int | None = None, offset: int | None = None
    ) -> CursorPage:
        """The users holding a role, oldest assignment first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/app_roles/{role_id}/users",
            query=_q(limit=limit, offset=offset),
        )

    async def get_for_user(self, user_id: str) -> m.UserAppRoles:
        """A user's app roles and effective permissions."""
        return await self._t.request(method="GET", path=f"/v1/users/{user_id}/app_roles")

    async def set_for_user(self, user_id: str, body: m.SetUserAppRolesBody) -> m.UserAppRoles:
        """``roles`` replaces the set; ``add`` / ``remove`` change it (keys or ids)."""
        return await self._t.request(
            method="POST", path=f"/v1/users/{user_id}/app_roles", body=body
        )

    async def remove_from_user(self, user_id: str, role_id: str) -> m.UserAppRoles:
        return await self._t.request(
            method="DELETE", path=f"/v1/users/{user_id}/app_roles/{role_id}"
        )


class AsyncOAuthInitialAccessTokens:
    """Initial access tokens for OAuth dynamic client registration (RFC 7591 §3), needed
    once ``oauthProvider.requireInitialAccessToken`` is on."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> CursorPage:
        return await self._t.request(method="GET", path="/v1/oauth_initial_access_tokens")

    async def create(
        self, body: m.CreateInitialAccessTokenBody | None = None
    ) -> m.InitialAccessToken:
        """Mint a token; ``token`` is returned exactly once."""
        return await self._t.request(
            method="POST", path="/v1/oauth_initial_access_tokens", body=body or {}
        )

    async def revoke(self, token_id: str) -> m.InitialAccessToken:
        return await self._t.request(
            method="DELETE", path=f"/v1/oauth_initial_access_tokens/{token_id}"
        )


class AsyncActionGallery:
    """The community Actions gallery: browse reusable Action templates (first-party and
    community), install one as a DISABLED action, keep installed actions up to date."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        trigger: str | None = None,
        source: Literal["builtin", "community"] | None = None,
    ) -> ListPage:
        """The gallery, best first (:class:`~atlas_backend.models.ActionGalleryEntry`)."""
        return await self._t.request(
            method="GET",
            path="/v1/action_gallery",
            query=_q(q=q, category=category, trigger=trigger, source=source),
        )

    async def get(self, slug: str) -> m.ActionGalleryEntry:
        """One template with its code, secret names and versions."""
        return await self._t.request(method="GET", path=f"/v1/action_gallery/{slug}")

    async def install(
        self,
        slug: str,
        body: m.InstallTemplateBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.ActionGalleryInstallResult:
        """Install as a new, disabled action. Supply secrets, bind it, then enable it."""
        return await self._t.request(
            method="POST",
            path=f"/v1/action_gallery/{slug}/install",
            body=body or {},
            idempotency_key=idempotency_key,
        )

    async def installs(self) -> ListPage:
        """Actions installed from the gallery, with update status."""
        return await self._t.request(method="GET", path="/v1/action_gallery_installs")

    async def update(
        self, action_id: str, *, secrets: dict[str, str] | None = None
    ) -> m.ActionGalleryUpdateResult:
        """Move an installed action to its template's latest version."""
        return await self._t.request(
            method="POST",
            path=f"/v1/actions/{action_id}/gallery_update",
            body=_q(secrets=secrets),
        )


class AsyncActionTemplates:
    """Templates this instance publishes to the gallery (staff review them)."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/action_templates")

    async def create(
        self, body: m.CreateActionTemplateBody, *, idempotency_key: str | None = None
    ) -> m.ActionTemplate:
        return await self._t.request(
            method="POST",
            path="/v1/action_templates",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, template_id: str) -> m.ActionTemplate:
        return await self._t.request(method="GET", path=f"/v1/action_templates/{template_id}")

    async def update(self, template_id: str, body: m.ActionTemplateListing) -> m.ActionTemplate:
        return await self._t.request(
            method="PATCH", path=f"/v1/action_templates/{template_id}", body=body
        )

    async def delete(self, template_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/action_templates/{template_id}")

    async def add_version(
        self, template_id: str, body: m.NewTemplateVersionBody
    ) -> m.ActionTemplateVersion:
        return await self._t.request(
            method="POST", path=f"/v1/action_templates/{template_id}/versions", body=body
        )

    async def submit_version(self, template_id: str, version: str) -> m.ActionTemplateVersion:
        return await self._t.request(
            method="POST",
            path=f"/v1/action_templates/{template_id}/versions/{version}/submit",
        )

    async def delete_version(self, template_id: str, version: str) -> JSON:
        return await self._t.request(
            method="DELETE",
            path=f"/v1/action_templates/{template_id}/versions/{version}",
        )

    async def publish(self, template_id: str) -> m.ActionTemplate:
        """List an approved template again after unlisting it."""
        return await self._t.request(
            method="POST", path=f"/v1/action_templates/{template_id}/publish"
        )

    async def unlist(self, template_id: str) -> m.ActionTemplate:
        """Hide a template from the gallery (installs keep working)."""
        return await self._t.request(
            method="POST", path=f"/v1/action_templates/{template_id}/unlist"
        )


class AsyncPolicies:
    """Policy acceptance: the policies (Terms of Service, privacy policy, any key) your
    users accept at sign-up - and, per policy, again at sign-in when a new version takes
    effect. A policy's versions go draft, published (with an ``effective_at``), retired.
    Acceptances are append-only evidence (version, content hash, how it was shown).
    ``id_or_key`` is the policy id or its key.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.versions = _AsyncPolicyVersions(transport)
        self.settings = _AsyncPolicySettings(transport)

    async def list(self, *, include_retired: bool | None = None) -> ListPage:
        """Active policies (``include_retired`` for all), each with its current, upcoming
        and latest version."""
        return await self._t.request(
            method="GET",
            path="/v1/policies",
            query=_q(include_retired=include_retired),
        )

    async def create(
        self, body: m.CreatePolicyBody, *, idempotency_key: str | None = None
    ) -> m.Policy:
        """Create a policy. It asks nobody anything until a version is published."""
        return await self._t.request(
            method="POST", path="/v1/policies", body=body, idempotency_key=idempotency_key
        )

    async def get(self, id_or_key: str) -> m.Policy:
        """One policy, by id or key."""
        return await self._t.request(method="GET", path=f"/v1/policies/{id_or_key}")

    async def update(
        self,
        id_or_key: str,
        body: m.UpdatePolicyBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.Policy:
        """Update a policy (the key cannot change). ``status: "retired"`` stops it gating."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/policies/{id_or_key}",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, id_or_key: str) -> JSON:
        """Delete a policy that was never published; one with a published version is
        retired instead (the response says which: ``deleted`` / ``retired``)."""
        return await self._t.request(method="DELETE", path=f"/v1/policies/{id_or_key}")

    async def list_acceptances(
        self,
        id_or_key: str,
        *,
        version: str | None = None,
        status: Literal["accepted", "withdrawn", "all"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Who accepted the policy (optionally one version, a version id or label), newest
        first, with the evidence."""
        return await self._t.request(
            method="GET",
            path=f"/v1/policies/{id_or_key}/acceptances",
            query=_q(version=version, status=status, limit=limit, starting_after=starting_after),
        )

    async def export_acceptances_csv(
        self,
        id_or_key: str,
        *,
        version: str | None = None,
        status: Literal["accepted", "withdrawn", "all"] | None = None,
    ) -> str:
        """The same as CSV text (``format=csv``, up to 100,000 rows)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/policies/{id_or_key}/acceptances",
            query=_q(version=version, status=status, format="csv"),
            raw=True,
        )

    async def for_user(self, user_id: str) -> m.UserPolicies:
        """A user's standing on every policy (accepted and current version,
        ``needs_reaccept``, ``blocking``, ``grace_ends_at``) and ``needs_acceptance``."""
        return await self._t.request(method="GET", path=f"/v1/users/{user_id}/policies")


class _AsyncPolicyVersions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, id_or_key: str) -> ListPage:
        """The policy's versions, newest first, each with ``acceptance_count``."""
        return await self._t.request(method="GET", path=f"/v1/policies/{id_or_key}/versions")

    async def create(
        self,
        id_or_key: str,
        body: m.CreatePolicyVersionBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Create a draft, or publish at once with ``publish: True`` (and ``effective_at``).
        400 for an external policy: its versions come from the policy source."""
        return await self._t.request(
            method="POST",
            path=f"/v1/policies/{id_or_key}/versions",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(self, id_or_key: str, version_id_or_label: str) -> m.PolicyVersion:
        """One version, by id or label."""
        return await self._t.request(
            method="GET", path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}"
        )

    async def update(
        self,
        id_or_key: str,
        version_id_or_label: str,
        body: m.UpdatePolicyVersionBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Edit a draft (409 for a published version: publish a new one instead)."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(self, id_or_key: str, version_id_or_label: str) -> JSON:
        """Delete a draft (409 for a published version: retire it instead)."""
        return await self._t.request(
            method="DELETE", path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}"
        )

    async def publish(
        self,
        id_or_key: str,
        version_id_or_label: str,
        body: m.PublishPolicyVersionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Publish a draft. ``effective_at`` (epoch ms or ISO, default now) is when
        sign-ups must accept it and sign-ins re-ask per the policy's ``reaccept`` rule."""
        return await self._t.request(
            method="POST",
            path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}/publish",
            body=body if body is not None else {},
            idempotency_key=idempotency_key,
        )

    async def retire(
        self,
        id_or_key: str,
        version_id_or_label: str,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Retire a published version: it no longer gates or is offered; acceptances stay."""
        return await self._t.request(
            method="POST",
            path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}/retire",
            idempotency_key=idempotency_key,
        )


class _AsyncPolicySettings:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.PolicySettings:
        """Policy settings: the optional ``pol`` session claim."""
        return await self._t.request(method="GET", path="/v1/instance/policy_settings")

    async def update(self, body: m.UpdatePolicySettingsBody) -> m.PolicySettings:
        """Turn the ``pol`` session claim on or off (tokens minted after the change; it
        can take 30 seconds to apply everywhere)."""
        return await self._t.request(method="PATCH", path="/v1/instance/policy_settings", body=body)


class AsyncPolicySource:
    """The external policy source (Atlas policy source protocol v1): serve your policies
    from a CMS or your own service. Atlas fetches ``GET {endpoint_url}/policies`` signed
    with the source's signing secret (``verify_policy_feed_request`` checks it) and your
    source tells Atlas about changes with a signed event (``sign_policy_source_event``).
    ``signing_secret`` is write-only.
    """

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.PolicySource:
        """Endpoint, sync mode, the webhook URL to give the source and the last sync."""
        return await self._t.request(method="GET", path="/v1/instance/policy_source")

    async def update(self, body: m.UpdatePolicySourceBody) -> m.PolicySource:
        """Configure the source; only the fields sent change and ``None`` clears. Enabling
        needs ``endpoint_url`` and ``signing_secret``."""
        return await self._t.request(method="PUT", path="/v1/instance/policy_source", body=body)

    async def delete(self) -> m.PolicySource:
        """Disconnect the source (its policies and their history stay; they stop syncing)."""
        return await self._t.request(method="DELETE", path="/v1/instance/policy_source")

    async def test(self) -> m.PolicySourceTest:
        """A signed fetch of the feed, validated but not stored."""
        return await self._t.request(method="POST", path="/v1/instance/policy_source/test")

    async def sync(self) -> m.PolicySourceSync:
        """Fetch the feed now and store it. A published version whose content changed at
        the source is refused: publish a new version there."""
        return await self._t.request(method="POST", path="/v1/instance/policy_source/sync")

    async def list_deliveries(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        kind: str | None = None,
        status: str | None = None,
    ) -> CursorPage:
        """The delivery log: every fetch, test, poll and inbound event, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/policy_source/deliveries",
            query=_q(limit=limit, starting_after=starting_after, kind=kind, status=status),
        )


# --------------------------------------------------------------------------- #
# Integrator platform                                                          #
# --------------------------------------------------------------------------- #


class AsyncWhoami:
    """``GET /v1/whoami``: introspect the key this client authenticates with (kind, scopes,
    expiry, owner, instance)."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/whoami")


class AsyncSecretKeys:
    """``/v1/secret_keys``: mint, list, rotate and revoke the instance's secret keys. A new
    secret is revealed exactly once (``secret``, or ``sealed_secret`` when
    ``secret_recipient`` is sent; open it with :class:`SealedBox`). Keys default to a
    one-year expiry, belong to their creator (``owner``) and can be locked to browser
    ``allowed_origins``."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self,
        body: m.CreateSecretKeyBody,
        *,
        idempotency_key: str | None = None,
        dry_run: bool = False,
    ) -> m.SecretKey:
        return await self._t.request(
            method="POST",
            path="/v1/secret_keys",
            body=body,
            idempotency_key=idempotency_key,
            query=_dry(dry_run),
        )

    async def list(self, *, metadata: dict[str, Any] | None = None) -> ListPage:
        return await self._t.request(
            method="GET", path="/v1/secret_keys", query=_meta(metadata) or None
        )

    async def get(self, key_id: str) -> m.SecretKey:
        return await self._t.request(method="GET", path=f"/v1/secret_keys/{_enc(key_id)}")

    async def update(self, key_id: str, body: m.UpdateSecretKeyBody) -> m.SecretKey:
        return await self._t.request(
            method="PATCH", path=f"/v1/secret_keys/{_enc(key_id)}", body=body
        )

    async def rotate(
        self,
        key_id: str,
        body: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.SecretKey:
        """A new key with the same scopes; the old one keeps working for ``overlap_seconds``
        (default 72 h, ``0`` revokes it now)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/secret_keys/{_enc(key_id)}/rotate",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(self, key_id: str) -> m.SecretKey:
        return await self._t.request(method="POST", path=f"/v1/secret_keys/{_enc(key_id)}/revoke")


class AsyncKeys:
    """Keys across kinds, the operator document, token exchange and leaked-key revocation."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, kind: str | None = None) -> ListPage:
        """``GET /v1/keys``: every credential on the instance, standard shape."""
        return await self._t.request(method="GET", path="/v1/keys", query=_q(kind=kind))

    async def revoke_leaked(self, body: dict[str, Any]) -> JSON:
        """``POST /v1/keys/revoke_leaked``: revoke leaked Atlas credentials. Needs no key
        (the leaked secret is the proof)."""
        return await self._t.request(method="POST", path="/v1/keys/revoke_leaked", body=body)

    async def operator(self) -> m.OperatorConfiguration:
        """``GET /v1/operator``: where the operator device flow and token exchange live, the
        other products that accept Atlas operators (``audiences``) and the claims an
        operator access token carries (``access_token_claims``)."""
        return await self._t.request(method="GET", path="/v1/operator")

    async def exchange_token(self, body: dict[str, Any]) -> JSON:
        """``POST /v1/oauth/token`` (form-encoded): RFC 8693 token exchange or
        ``client_credentials``."""
        form = urlencode({k: v for k, v in body.items() if v is not None})
        return await self._t.request(
            method="POST",
            path="/v1/oauth/token",
            content=form.encode("utf-8"),
            content_type="application/x-www-form-urlencoded",
        )

    async def client_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
        audience: str | None = None,
    ) -> JSON:
        return await self.exchange_token(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
                "audience": audience,
            }
        )

    async def token_exchange(
        self,
        *,
        subject_token: str,
        subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
        resource: str | None = None,
        scope: str | None = None,
        audience: str | None = None,
    ) -> JSON:
        return await self.exchange_token(
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": subject_token,
                "subject_token_type": subject_token_type,
                "resource": resource,
                "scope": scope,
                "audience": audience,
            }
        )


class _AsyncPartnerLinkRequests:
    """Partner link requests: a partner asks, the owner approves or denies, and Atlas delivers
    the credentials to the partner's callback (the owner never sees the secret)."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        direction: Literal["inbound", "outbound"] | None = None,
        status: str | Sequence[str] | None = None,
    ) -> ListPage:
        return await self._t.request(
            method="GET",
            path="/v1/partner_links/requests",
            query=_q(direction=direction, status=_csv(status)),
        )

    async def get(self, request_id: str) -> m.PartnerLinkRequest:
        return await self._t.request(
            method="GET", path=f"/v1/partner_links/requests/{_enc(request_id)}"
        )

    async def approve(
        self, request_id: str, body: m.ApprovePartnerLinkRequestBody | None = None
    ) -> m.PartnerLinkRequestApproval:
        """Approve: Atlas creates the link and delivers its credentials to the partner,
        signed. ``scopes`` may narrow the request, never widen it."""
        return await self._t.request(
            method="POST",
            path=f"/v1/partner_links/requests/{_enc(request_id)}/approve",
            body=body if body is not None else {},
        )

    async def deny(self, request_id: str) -> m.PartnerLinkRequest:
        return await self._t.request(
            method="POST", path=f"/v1/partner_links/requests/{_enc(request_id)}/deny"
        )


class _AsyncOutboundPartnerLinks:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/partner_links/outbound")

    async def save(self, partner: str, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="PUT", path=f"/v1/partner_links/outbound/{_enc(partner)}", body=body
        )

    async def test(self, partner: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/partner_links/outbound/{_enc(partner)}/test"
        )

    async def remove(self, partner: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/partner_links/outbound/{_enc(partner)}"
        )

    async def request(self, partner: str, body: dict[str, Any]) -> JSON:
        """Ask a partner for a link; its credentials arrive by themselves once the partner
        approves. ``body``: ``scopes``, optionally ``resource``, ``base_url``, ``token_url``,
        ``name``."""
        return await self._t.request(
            method="POST",
            path=f"/v1/partner_links/outbound/{_enc(partner)}/request",
            body=body,
        )


class AsyncPartnerPlatforms:
    """``/v1/partner_platforms``: this instance as a partner platform of another product, a
    product that signs its partner deliveries with a published Ed25519 key set. The partner
    delivers signed consent events to this instance's receiver; registering is done by the
    partner from ``registration(...)``, and the partner token it hands back is stored once,
    encrypted, and never returned by any call."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> m.PartnerPlatformList:
        return await self._t.request(method="GET", path="/v1/partner_platforms")

    async def get(self, partner: str) -> m.PartnerPlatform:
        return await self._t.request(method="GET", path=f"/v1/partner_platforms/{_enc(partner)}")

    async def set(
        self, partner: str, body: m.PartnerPlatformInput | None = None
    ) -> m.PartnerPlatform:
        """Set up or change a partner platform (a preset id fills the defaults)."""
        return await self._t.request(
            method="PUT", path=f"/v1/partner_platforms/{_enc(partner)}", body=body or {}
        )

    async def delete(self, partner: str) -> m.PartnerPlatformDeleted:
        return await self._t.request(method="DELETE", path=f"/v1/partner_platforms/{_enc(partner)}")

    async def registration(self, partner: str) -> m.PartnerPlatformRegistration:
        """What to send the partner to be registered: receiver URL, signature expectations."""
        return await self._t.request(
            method="GET", path=f"/v1/partner_platforms/{_enc(partner)}/registration"
        )

    async def store_token(
        self,
        partner: str,
        token: str,
        *,
        rotate: bool | None = None,
        api_base_url: str | None = None,
    ) -> m.PartnerPlatform:
        """Store the partner token the partner handed over (once; ``rotate=True`` replaces it).
        The token is write-only: no response carries it, only ``token_set`` and ``token_prefix``."""
        return await self._t.request(
            method="POST",
            path=f"/v1/partner_platforms/{_enc(partner)}/token",
            body=_q(token=token, rotate=rotate, api_base_url=api_base_url),
        )

    async def deliveries(self, partner: str, *, limit: int | None = None) -> ListPage:
        """The partner's recent deliveries and what became of each."""
        return await self._t.request(
            method="GET",
            path=f"/v1/partner_platforms/{_enc(partner)}/deliveries",
            query=_q(limit=limit),
        )


class AsyncPartnerLinks:
    """``/v1/partner_links``: scoped credentials granted to a partner product, the requests
    partners make, and the outbound links this instance holds into partner products."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.requests = _AsyncPartnerLinkRequests(transport)
        self.outbound = _AsyncOutboundPartnerLinks(transport)

    async def create(
        self, body: dict[str, Any], *, idempotency_key: str | None = None
    ) -> m.PartnerLink:
        """Create a link by hand (the secret is returned once). Prefer approving a partner's
        request: there is no secret to hand over. ``body``: ``partner``, ``scopes``, optional
        ``name``, ``expires_at``, ``cert_fingerprints``."""
        return await self._t.request(
            method="POST", path="/v1/partner_links", body=body, idempotency_key=idempotency_key
        )

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/partner_links")

    async def get(self, link_id: str) -> m.PartnerLink:
        return await self._t.request(method="GET", path=f"/v1/partner_links/{_enc(link_id)}")

    async def set_certificates(
        self, link_id: str, cert_fingerprints: Sequence[str]
    ) -> m.PartnerLink:
        """Lock a link to client certificates (mTLS); an empty list removes the lock."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/partner_links/{_enc(link_id)}",
            body={"cert_fingerprints": list(cert_fingerprints)},
        )

    async def rotate_secret(self, link_id: str) -> m.PartnerLink:
        return await self._t.request(
            method="POST", path=f"/v1/partner_links/{_enc(link_id)}/rotate_secret"
        )

    async def revoke(self, link_id: str) -> m.PartnerLink:
        return await self._t.request(method="DELETE", path=f"/v1/partner_links/{_enc(link_id)}")


class AsyncAtlasIdGrants:
    """``/v1/atlas_id_apps`` on the secret-key surface: the Sign in with Atlas apps this
    instance manages and their grants."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_apps(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/atlas_id_apps")

    async def lookup(self, app_id: str, email: str) -> ListPage:
        """Is this verified email a user of the app? An empty list otherwise."""
        return await self._t.request(
            method="GET", path=f"/v1/atlas_id_apps/{_enc(app_id)}/users", query={"email": email}
        )

    async def preflight(self, app_id: str) -> m.AtlasIdAppPreflightDetail:
        """The setup check of an app this instance manages (``diagnostics:read`` is enough)."""
        return await self._t.request(
            method="GET", path=f"/v1/atlas_id_apps/{_enc(app_id)}/preflight"
        )

    async def revoke_grant(self, app_id: str, grant_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/atlas_id_apps/{_enc(app_id)}/grants/{_enc(grant_id)}"
        )


class _AsyncPrivacyOrchestrator:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.PrivacyOrchestrator:
        return await self._t.request(method="GET", path="/v1/instance/privacy_orchestrator")

    async def set(self, body: m.PrivacyOrchestratorInput) -> m.PrivacyOrchestrator:
        """Set the orchestrator. ``site_id`` is the orchestrator-side site a case is for,
        ``partner_link_id`` calls through a partner link (implies ``use_partner_link``) and
        ``cancel_deletion_on_sign_in`` cancels a self-scheduled deletion when the person signs
        back in during the grace period."""
        return await self._t.request(
            method="PUT", path="/v1/instance/privacy_orchestrator", body=body
        )

    async def delete(self) -> JSON:
        return await self._t.request(method="DELETE", path="/v1/instance/privacy_orchestrator")


class AsyncPrivacy:
    """The privacy-executor client: discovery, subject lookup, and idempotent privacy
    requests (restriction / deletion / export) a data-rights orchestrator executes; plus the
    instance's orchestrator setting."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.orchestrator = _AsyncPrivacyOrchestrator(transport)

    async def discover(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/privacy")

    async def preset(self, preset_id: str) -> JSON:
        return await self._t.request(method="GET", path=f"/v1/privacy/presets/{_enc(preset_id)}")

    async def lookup(self, body: dict[str, Any]) -> JSON:
        return await self._t.request(method="POST", path="/v1/privacy/lookup", body=body)

    async def create_request(
        self, body: dict[str, Any], *, idempotency_key: str | None = None
    ) -> JSON:
        """Open a privacy request. Always send an ``Idempotency-Key`` (16-255 characters)."""
        return await self._t.request(
            method="POST",
            path="/v1/privacy/requests",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_request(self, request_id: str) -> JSON:
        return await self._t.request(method="GET", path=f"/v1/privacy/requests/{_enc(request_id)}")

    async def cancel_request(self, request_id: str, *, idempotency_key: str | None = None) -> JSON:
        return await self._t.request(
            method="POST",
            path=f"/v1/privacy/requests/{_enc(request_id)}/cancel",
            idempotency_key=idempotency_key,
        )


class AsyncIntegrations:
    """``/v1/instance/integrations/{product}``: identity integrations (a product that trusts
    Atlas sessions), their deliveries, the server-side token mint
    (``get_token(session_id, for_=...)``) and the integration card."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/instance/integrations")

    async def get(self, product: str) -> JSON:
        return await self._t.request(
            method="GET", path=f"/v1/instance/integrations/{_enc(product)}"
        )

    async def set(self, product: str, body: dict[str, Any], *, dry_run: bool = False) -> JSON:
        return await self._t.request(
            method="PUT",
            path=f"/v1/instance/integrations/{_enc(product)}",
            body=body,
            query=_dry(dry_run),
        )

    async def delete(self, product: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/instance/integrations/{_enc(product)}"
        )

    async def deliveries(
        self,
        product: str,
        *,
        trace: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The integration's outbound deliveries; ``trace`` filters by W3C trace id."""
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/integrations/{_enc(product)}/deliveries",
            query=_q(trace=trace, limit=limit, starting_after=starting_after),
        )

    async def events_secret(self, product: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/instance/integrations/{_enc(product)}/events_secret"
        )

    async def atlas_id_tokens(self, product: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/instance/integrations/{_enc(product)}/atlas_id_tokens"
        )

    async def get_token(
        self,
        session_id: str,
        for_: str,
        *,
        audience_hint: str | None = None,
        audience: str | None = None,
        cbid: str | None = None,
        audience_params: dict[str, str] | None = None,
    ) -> m.SessionToken:
        """Mint an integration token for a session on the server (``getToken({for})``). A
        per-call audience (``audience``, ``cbid`` or ``audience_params``) follows the
        integration's ``per_call_audience``; one it does not permit is refused with 403."""
        return await self._t.request(
            method="POST",
            path=f"/v1/sessions/{_enc(session_id)}/integration_tokens/{_enc(for_)}",
            query=_audience_query(audience, cbid, audience_params) or None,
            body={"audience_hint": audience_hint} if audience_hint else None,
        )

    async def report_verify_error(self, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="POST", path="/v1/integrations/verify_errors", body=body
        )

    async def card(self, product: str) -> JSON:
        return await self._t.request(method="GET", path=f"/v1/integrations/{_enc(product)}/card")

    async def card_revoke_sessions(self, product: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/integrations/{_enc(product)}/card/actions/revoke_sessions"
        )

    async def public_instance(self, instance_id: str) -> JSON:
        return await self._t.request(method="GET", path=f"/v1/public/instances/{_enc(instance_id)}")

    async def run_card_action(
        self,
        integration: str,
        action: str,
        body: m.IntegrationsRunCardActionBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IntegrationsRunCardActionResponse:
        """Run a card action. revoke_sessions signs the user out of every device (their sessions
        end, back-channel logouts go out) and is audited with the agent the integration names.
        Partner link with sessions:write, or the secret key.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/integrations/{_enc(integration)}/card/actions/{_enc(action)}",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncStatusSubscription:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/instance/status_subscription")

    async def set(self, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="PUT", path="/v1/instance/status_subscription", body=body
        )

    async def delete(self) -> JSON:
        return await self._t.request(method="DELETE", path="/v1/instance/status_subscription")

    async def rotate_feed(self) -> JSON:
        return await self._t.request(
            method="POST", path="/v1/instance/status_subscription/rotate_feed"
        )


class _AsyncStatusDependencies:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/instance/status_dependencies")

    async def create(self, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="POST", path="/v1/instance/status_dependencies", body=body
        )

    async def get(self, dependency_id: str) -> JSON:
        return await self._t.request(
            method="GET", path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}"
        )

    async def update(self, dependency_id: str, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="PATCH",
            path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}",
            body=body,
        )

    async def delete(self, dependency_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}"
        )

    async def refresh(self, dependency_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}/refresh"
        )


class AsyncStatus:
    """The Atlas status feed, this instance's subscription to it, its incidents and the
    upstream status dependencies it watches. Webhook events: ``status.incident.created`` /
    ``.updated`` / ``.resolved``."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.subscription = _AsyncStatusSubscription(transport)
        self.dependencies = _AsyncStatusDependencies(transport)

    async def get(self, *, region: str | None = None) -> JSON:
        """``GET /v1/status`` (Statuspage-compatible); ``region`` narrows it."""
        return await self._t.request(method="GET", path="/v1/status", query=_q(region=region))

    async def incidents(self, *, open: bool | None = None, limit: int | None = None) -> ListPage:
        return await self._t.request(
            method="GET", path="/v1/instance/status_incidents", query=_q(open=open, limit=limit)
        )


class AsyncNotices:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, all: bool | None = None) -> ListPage:
        return await self._t.request(method="GET", path="/v1/instance/notices", query=_q(all=all))

    async def acknowledge(self, notice_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/instance/notices/{_enc(notice_id)}/acknowledge"
        )


class AsyncSecurityAdvisories:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/security_advisories")

    async def acknowledge(self, advisory_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/security_advisories/{_enc(advisory_id)}/acknowledge"
        )

    async def list_public(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/public/security_advisories")


class AsyncAuditExports:
    """Audit-log exports to your SIEM as CloudEvents over a signed webhook."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/audit_exports")

    async def get(self, export_id: str) -> JSON:
        return await self._t.request(method="GET", path=f"/v1/audit_exports/{_enc(export_id)}")

    async def create(self, body: dict[str, Any]) -> JSON:
        return await self._t.request(method="POST", path="/v1/audit_exports", body=body)

    async def update(self, export_id: str, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="PATCH", path=f"/v1/audit_exports/{_enc(export_id)}", body=body
        )

    async def delete(self, export_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/audit_exports/{_enc(export_id)}")

    async def test(self, export_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/audit_exports/{_enc(export_id)}/test"
        )

    async def rotate_secret(self, export_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/audit_exports/{_enc(export_id)}/rotate_secret"
        )


class AsyncSubProcessors:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/instance/sub_processors")


class AsyncEntitlements:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/entitlements")


class AsyncIntegrationHealth:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/integration-health")

    async def providers(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/integration-health/providers")


class AsyncEmbed:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, *, instance: str | None = None) -> JSON:
        return await self._t.request(method="GET", path="/v1/embed", query=_q(instance=instance))

    async def csp(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/instance/csp")


class AsyncOpenApi:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def diff(self, *, since: str | None = None, surface: str | None = None) -> JSON:
        """What changed in the API since a date (``x-since`` ledger)."""
        return await self._t.request(
            method="GET", path="/v1/openapi/diff", query=_q(since=since, surface=surface)
        )

    async def api_catalog(self) -> JSON:
        return await self._t.request(method="GET", path="/.well-known/api-catalog")


class AsyncDeliveryHealth:
    """Delivery health of the instance's outbound targets (webhooks, back-channel logout
    receivers, referral connections, integrations) and their alert contacts."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self, *, kind: str | None = None) -> JSON:
        return await self._t.request(method="GET", path="/v1/delivery_health", query=_q(kind=kind))

    async def set_alert_contacts(
        self, kind: str, target_id: str, alert_contacts: Sequence[str]
    ) -> JSON:
        return await self._t.request(
            method="PUT",
            path=f"/v1/delivery_health/{_enc(kind)}/{_enc(target_id)}/alert_contacts",
            body={"alert_contacts": list(alert_contacts)},
        )

    async def get_for_target(
        self,
        kind: str,
        id: str,
    ) -> m.DeliveryHealthGetResponse:
        """Delivery health of one target. 404 until a delivery to it has been recorded."""
        return await self._t.request(
            method="GET",
            path=f"/v1/delivery_health/{_enc(kind)}/{_enc(id)}",
        )


class AsyncMeta:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def egress_ips(self) -> JSON:
        """The IP addresses Atlas sends webhooks and other outbound calls from."""
        return await self._t.request(method="GET", path="/v1/meta/egress_ips")


class AsyncPlatformWhoami:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/platform/whoami")


class AsyncPlatformKeys:
    """``/v1/platform/keys``: the platform's own keys (``owner``, ``expires_at``,
    ``allowed_origins``)."""

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, kind: str | None = None) -> ListPage:
        return await self._t.request(method="GET", path="/v1/platform/keys", query=_q(kind=kind))

    async def create(self, body: dict[str, Any]) -> m.PlatformKey:
        return await self._t.request(method="POST", path="/v1/platform/keys", body=body)

    async def update(self, key_id: str, body: dict[str, Any]) -> m.PlatformKey:
        return await self._t.request(
            method="PATCH", path=f"/v1/platform/keys/{_enc(key_id)}", body=body
        )

    async def revoke(self, key_id: str) -> m.PlatformKey:
        return await self._t.request(method="POST", path=f"/v1/platform/keys/{_enc(key_id)}/revoke")


class _AsyncPlatformAuditStreams:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/platform/audit_streams")

    async def create(self, body: dict[str, Any]) -> JSON:
        return await self._t.request(method="POST", path="/v1/platform/audit_streams", body=body)

    async def update(self, stream_id: str, body: dict[str, Any]) -> JSON:
        return await self._t.request(
            method="PATCH", path=f"/v1/platform/audit_streams/{_enc(stream_id)}", body=body
        )

    async def delete(self, stream_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/platform/audit_streams/{_enc(stream_id)}"
        )

    async def test(self, stream_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/platform/audit_streams/{_enc(stream_id)}/test"
        )


class AsyncPlatformAudit:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.streams = _AsyncPlatformAuditStreams(transport)

    async def list(
        self,
        *,
        action: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        return await self._t.request(
            method="GET",
            path="/v1/platform/audit_logs",
            query=_q(action=action, limit=limit, starting_after=starting_after),
        )


class AsyncAppCatalog:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def presets(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AppCatalogPresetsResponse:
        """List the app presets: about 100 SAML apps (Slack, GitHub, Snowflake, Notion, HubSpot
        and more) and about 45 OpenID Connect apps (Grafana, GitLab, Argo CD, Vault,
        Cloudflare Zero Trust and more), each with its protocol, category, the parameters it
        needs, whether its values were confirmed in the vendor's docs (verified) and that page
        (source_url).
        """
        return await self._t.request(
            method="GET",
            path="/v1/app_catalog",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def installed(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AppCatalogInstalledResponse:
        """List the installed apps (SAML and OpenID Connect) with their email-domain allow-list
        and assignment.
        """
        return await self._t.request(
            method="GET",
            path="/v1/app_catalog/installed",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def install(
        self,
        id: str,
        body: m.AppCatalogInstallBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AppCatalogInstallResponse:
        """Install a catalog app from its preset and params, with an optional name, installed_id,
        allowed_email_domains and assignment. A SAML preset becomes a SAML service provider;
        an OIDC preset registers a confidential OAuth client with the preset's redirect URIs
        and returns client_id, client_secret (shown once), redirect_uri and issuer to paste
        into the app. 409 if the installed_id exists. → 201.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/app_catalog/{_enc(id)}/install",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self,
        id: str,
        body: m.AppCatalogUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.AppCatalogUpdateResponse:
        """Change an installed app's name, allowed_email_domains or assignment. Assignment
        applies to the launcher and to single sign-on: someone not assigned is refused with
        403.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/app_catalog/installed/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def uninstall(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Uninstall an app: it disappears from the launcher and Atlas stops signing people in to
        it (an OIDC app's OAuth client and its grants are deleted).
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/app_catalog/installed/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncLdapServerClients:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List the LDAP interface service accounts with their base DN, bind DN and allowed
        source networks. Secrets are never returned.
        """
        return await self._t.request(
            method="GET",
            path="/v1/ldap_server_clients",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.LdapServerClientsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.LdapServerClientsCreateResponse:
        """Create a service account for the LDAPS interface: base_dn (dc=/o=/ou= parts, unique
        across Atlas), bind_cn, allowed_cidrs (empty = nobody may connect), allow_user_bind
        and size_limit. The secret is returned once as secret.
        """
        return await self._t.request(
            method="POST",
            path="/v1/ldap_server_clients",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.LdapServerClientsGetResponse:
        """Read one LDAP interface service account."""
        return await self._t.request(
            method="GET",
            path=f"/v1/ldap_server_clients/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.LdapServerClientsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.LdapServerClientsUpdateResponse:
        """Change the name, allowed networks, user-bind switch, size limit or status (active or
        disabled).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/ldap_server_clients/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a service account; its connections can no longer bind."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/ldap_server_clients/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def rotate_secret(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.LdapServerClientsRotateSecretResponse:
        """Issue a new service-account secret (returned once); the old one stops working
        immediately.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/ldap_server_clients/{_enc(id)}/rotate_secret",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )


class _AsyncUsersRequiredActions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def request(
        self,
        id: str,
        body: m.UsersRequiredActionsRequestBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersRequiredActionsRequestResponse:
        """Make a user owe an action at their next sign-in, whatever the method: update_password,
        verify_email, accept_policy, configure_mfa, update_profile, or custom (sent to an
        https url; the app closes it with DELETE). The sign-in attempt holds at
        needs_required_action until it is done (configure_mfa alone routes through MFA
        enrollment; accept_policy is closed once the policy gate passes; verify_email and
        configure_mfa clear themselves when already true). Re-requesting an open action is a
        200 with the same row. Emits user.required_action_requested. → 201.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/required_actions",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The actions a user currently owes, oldest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/required_actions",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def clear(
        self,
        id: str,
        rid: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Withdraw an owed action. This is also how an application closes a custom action once
        the user has finished its step. Emits user.required_action_cleared. 404 when it is not
        open.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(id)}/required_actions/{_enc(rid)}",
            query=_q(dry_run=dry_run),
        )

    async def bulk(
        self,
        body: m.UsersRequiredActionsBulkBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Owe the same action for many users at once: every member of one organization
        (organization_id) or an explicit user_ids list, at most 5000. Users outside the
        instance are skipped, and an already-open action counts as already_open. Emits
        user.required_action_requested per newly opened action.
        """
        return await self._t.request(
            method="POST",
            path="/v1/required_actions/bulk",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncUsersNotes:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The notes on a user: pinned notes first, then newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/notes",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        id: str,
        body: m.UsersNotesCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersNotesCreateResponse:
        """Add a note to a user (up to 5000 characters; at most 500 notes per user). The audit
        log records that a note was added, never its text. → 201.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/notes",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self,
        id: str,
        note_id: str,
        body: m.UsersNotesUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.UsersNotesUpdateResponse:
        """Edit a note: its text, its pin, or both."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/users/{_enc(id)}/notes/{_enc(note_id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        note_id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a note from a user. The audit log keeps that it was deleted."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(id)}/notes/{_enc(note_id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncUsersGuardians:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def request(
        self,
        id: str,
        body: m.UsersGuardiansRequestBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersGuardiansRequestResponse:
        """Ask a parent or guardian to approve a minor's account. Name them by email or by
        guardian_user_id (their address is used). Returns the pending link with a one-time
        consent_url that expires after compliance.minors.consentTtlHours. With send_email:
        true Atlas mails it through the application's own email provider (422 when none is set
        up); otherwise deliver consent_url yourself. → 201.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/guardians",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def approve(
        self,
        id: str,
        link_id: str,
        body: m.UsersGuardiansApproveBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersGuardiansApproveResponse:
        """Record consent obtained another way (a signed form, a verified call): the link becomes
        active with consent_method admin and the account is consented. 409 for a revoked link.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/guardians/{_enc(link_id)}/approve",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(
        self,
        id: str,
        link_id: str,
        *,
        dry_run: bool | None = None,
    ) -> m.UsersGuardiansRevokeResponse:
        """Withdraw a guardian link. When no active guardian is left, the account needs consent
        again.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(id)}/guardians/{_enc(link_id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncUsersSearch:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.views = _AsyncUsersSearchViews(transport)

    async def query(
        self,
        body: m.UsersSearchQueryBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """Search users with a boolean filter tree (and/or/not) over profile columns, traits and
        metadata keys, organization and org role, MFA enrolled/strategy, sign-in strategy,
        last sign-in country or IP, and date ranges. Sort with order_by; page with
        starting_after (creation/update order) or offset (last_sign_in_at order).
        include_total_count adds total_count. Containment tests on public metadata and traits
        are answered by an index. Same user objects as GET /v1/users.
        """
        return await self._t.request(
            method="POST",
            path="/v1/users/search",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def export(
        self,
        body: m.UsersSearchExportBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Export every user a search matches (up to 10,000; x-export-truncated says when more
        matched) as CSV (default) or NDJSON. fields picks columns: id, primary_email,
        username, first_name, last_name, external_id, created_at, last_sign_in_at, banned,
        mfa_enrolled, plus traits.<key> / public_metadata.<path>. CSV cells that start with =
        + - @ are prefixed with an apostrophe so a spreadsheet never runs them as formulas.
        """
        return await self._t.request(
            method="POST",
            path="/v1/users/search/export",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncUsersSearchViews:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The saved user-search views of the instance, by name."""
        return await self._t.request(
            method="GET",
            path="/v1/users/search/views",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.UsersSearchViewsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.UsersSearchViewsCreateResponse:
        """Save a named filter (and sort) to re-run. A filter that could never run is refused; a
        duplicate name is a 400. → 201.
        """
        return await self._t.request(
            method="POST",
            path="/v1/users/search/views",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self,
        id: str,
        body: m.UsersSearchViewsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.UsersSearchViewsUpdateResponse:
        """Rename a saved view or change its filter or sort."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/users/search/views/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a saved user-search view."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/search/views/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncJourneys:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The sign-in journeys."""
        return await self._t.request(
            method="GET",
            path="/v1/flows",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.JourneysCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.JourneysCreateResponse:
        """Create a sign-in journey (version 1, active unless activate is false). Steps run top
        to bottom once a sign-in has passed its factors: refusals (deny, require_method,
        require_mfa), required actions the user must finish first, Action calls that may
        refuse, session claims and the redirect after sign-in. Action steps must name
        workflow_step Actions. → 201.
        """
        return await self._t.request(
            method="POST",
            path="/v1/flows",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.JourneysGetResponse:
        """One journey with its active definition (else the latest)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.JourneysUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.JourneysUpdateResponse:
        """Change a journey. A definition becomes the next version (immutable), active unless
        activate is false.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/flows/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a journey and its versions."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/flows/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def versions(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.JourneysVersionsResponse:
        """Every version of a journey, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(id)}/versions",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def activate(
        self,
        id: str,
        body: m.JourneysActivateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.JourneysActivateResponse:
        """Make a version the active one (roll forward or back)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(id)}/activate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def simulate(
        self,
        id: str,
        body: m.JourneysSimulateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.JourneysSimulateResponse:
        """What-if: run a version (default the active one) for a user and a described sign-in
        (method, mfa_verified, ip, application_id) without changing anything. Returns the
        outcome (allowed, held or refused), the effects and a per-step trace.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(id)}/simulate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncGroups:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.rules = _AsyncGroupsRules(transport)

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Every instance group with its member count, by slug."""
        return await self._t.request(
            method="GET",
            path="/v1/groups",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.GroupsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.GroupsCreateResponse:
        """Create an instance group. Emits group.created. → 201."""
        return await self._t.request(
            method="POST",
            path="/v1/groups",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.GroupsGetResponse:
        """One group, by id or slug."""
        return await self._t.request(
            method="GET",
            path=f"/v1/groups/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.GroupsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.GroupsUpdateResponse:
        """Change a group. Emits group.updated."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/groups/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a group: its memberships go, its children move to the top level. Emits
        group.deleted.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/groups/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def list_members(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The members of one group (direct members only), with how each joined (manual, dynamic,
        sso, rule). Cursor paged by user id.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/groups/{_enc(id)}/members",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def add_members(
        self,
        id: str,
        body: m.GroupsAddMembersBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Add up to 500 users by hand. A member who joined by filter, SSO or rule becomes
        manual, so a re-apply leaves them. Emits group.member_added per new member.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/groups/{_enc(id)}/members",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def remove_members(
        self,
        id: str,
        body: m.GroupsRemoveMembersBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Remove up to 500 users from a group. Emits group.member_removed."""
        return await self._t.request(
            method="POST",
            path=f"/v1/groups/{_enc(id)}/members/remove",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def reapply(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.GroupsReapplyResponse:
        """Re-evaluate a dynamic group now: users matching dynamic_filter are added, those who no
        longer match are removed; manual members are never touched (400 when the group has no
        dynamic_filter, or the filter matches over 50,000 users).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/groups/{_enc(id)}/reapply",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def for_user(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """A user's direct groups and how they joined each."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/groups",
            query=_q(limit=limit, starting_after=starting_after),
        )


class _AsyncGroupsRules:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Group rules, lowest priority number first."""
        return await self._t.request(
            method="GET",
            path="/v1/group_rules",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.GroupsRulesCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.GroupsRulesCreateResponse:
        """Create a rule: when a user matches condition, run the actions (add to a group, grant
        an app role, set a trait). → 201.
        """
        return await self._t.request(
            method="POST",
            path="/v1/group_rules",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def apply_all(
        self,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """Run every enabled rule in priority order. One result per rule."""
        return await self._t.request(
            method="POST",
            path="/v1/group_rules/apply",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.GroupsRulesGetResponse:
        """One group rule, with its condition and actions."""
        return await self._t.request(
            method="GET",
            path=f"/v1/group_rules/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.GroupsRulesUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.GroupsRulesUpdateResponse:
        """Change a group rule, its condition or actions."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/group_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a rule. Memberships it created stay until removed."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/group_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def apply(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.GroupsRulesApplyResponse:
        """Run one rule against every matching user now. Returns the match count and what
        changed.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/group_rules/{_enc(id)}/apply",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )


class AsyncMigrations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.imports = _AsyncMigrationsImports(transport)

    async def exchange(
        self,
        source: str,
        body: m.MigrationsExchangeBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MigrationsExchangeResponse:
        """Server-to-server exchange of an old `source` session for an Atlas session, once (what
        migrationBridge({ source }) calls with the secret key). The token is verified (vendor
        JWT against the bridge's issuer and keys, or sha256 matched against imported
        sessions), mapped to the imported user, spent in the single-use ledger and then takes
        the normal sign-in path (guards, MFA policy, post_login Actions, audit). Returns
        tokens in the body, or a sign_in_attempt when a second factor is owed. Limited per
        instance (6000/min), per end-user IP (60/min) and per user (10/min). Send the end
        user's IP / user agent in X-Atlas-Client-IP / X-Atlas-Client-User-Agent.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/exchange",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def sources(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Every migration source: what it exports, whether passwords move (or need lazy
        migration), its bridge preset and variables, and its lazy-migration preset.
        """
        return await self._t.request(
            method="GET",
            path="/v1/migrations/sources",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get_bridge(
        self,
        source: str,
    ) -> m.MigrationsGetBridgeResponse:
        """Read the zero-logout bridge settings for `source` (window, JWT preset / issuer / keys,
        claims, cookie names) and exchange counts. Never returns a shared secret.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/migrations/{_enc(source)}/bridge",
        )

    async def set_bridge(
        self,
        source: str,
        body: m.MigrationsSetBridgeBody,
        *,
        dry_run: bool | None = None,
    ) -> m.MigrationsSetBridgeResponse:
        """Create or update the bridge settings for `source`. Every field is optional and merged
        onto the stored ones; a preset fills the JWT settings from its variables, explicit
        fields override it. The keys URL must be public https on a production instance.
        `better_auth` takes the Better Auth bridge body (see
        /v1/migrations/better_auth/bridge).
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/migrations/{_enc(source)}/bridge",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete_bridge(
        self,
        source: str,
        *,
        dry_run: bool | None = None,
    ) -> m.MigrationsDeleteBridgeResponse:
        """Remove the bridge settings for `source` (the bridge is off and any stored secret
        deleted).
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/migrations/{_enc(source)}/bridge",
            query=_q(dry_run=dry_run),
        )


class _AsyncMigrationsImports:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_public_key(
        self,
        source: str,
    ) -> m.MigrationsImportsGetPublicKeyResponse:
        """The instance's import public key (created on first read). Seal the export to it; only
        this instance can open the bundle. One key serves every source. A key with jobs:write
        may read it too.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/migrations/{_enc(source)}/imports/public_key",
        )

    async def rotate_public_key(
        self,
        source: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MigrationsImportsRotatePublicKeyResponse:
        """Replace the import key. A bundle sealed to the old key no longer finalizes; export
        again with the new key.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/imports/public_key/rotate",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def create(
        self,
        source: str,
        body: m.MigrationsImportsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MigrationsImportsCreateResponse:
        """Start an import from `source` (status `uploading`). Then upload the sealed bundle with
        PUT …/parts/{part} and call …/finalize. Nothing is written to users until apply.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/imports",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        source: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the imports from `source`, newest first (cursor pagination)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/migrations/{_enc(source)}/imports",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(
        self,
        source: str,
        id: str,
    ) -> m.MigrationsImportsGetResponse:
        """Fetch one import: status, the dry-run report, live progress and the apply result."""
        return await self._t.request(
            method="GET",
            path=f"/v1/migrations/{_enc(source)}/imports/{_enc(id)}",
        )

    async def delete(
        self,
        source: str,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete an import and its stored bundle. Data it already imported stays. Refused (409)
        while analyzing or applying.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/migrations/{_enc(source)}/imports/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def put_part(
        self,
        source: str,
        id: str,
        part: str,
        body: m.MigrationsImportsPutPartBody,
        *,
        dry_run: bool | None = None,
    ) -> m.MigrationsImportsPutPartResponse:
        """Upload part `part` (1, 2, …) of the sealed bundle: whole lines, at most 10 MiB, as `{
        "data": "…" }` or a text/plain body. Re-sending a part replaces it. Only while
        `uploading`.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/migrations/{_enc(source)}/imports/{_enc(id)}/parts/{_enc(part)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def finalize(
        self,
        source: str,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MigrationsImportsFinalizeResponse:
        """Close the upload: every part 1..n present, the bundle sealed to the active import key
        and in a format `source` reads (else 400 or status `invalid`). The dry run follows:
        inline up to 4 MiB (200, `ready`), else in the background (202, `analyzing`; poll
        GET).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/imports/{_enc(id)}/finalize",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def dry_run(
        self,
        source: str,
        id: str,
        body: m.MigrationsImportsDryRunBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MigrationsImportsDryRunResponse:
        """Run the dry run again, optionally with new options (they replace the stored ones).
        Reads only.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/imports/{_enc(id)}/dry_run",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def apply(
        self,
        source: str,
        id: str,
        body: m.MigrationsImportsApplyBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MigrationsImportsApplyResponse:
        """Import the bundle. Every record is an idempotent upsert keyed by its source id, so
        applying a failed import again resumes where it stopped. Up to 1,000 remaining records
        run inline (200), more are queued (202). With conflicts in the dry run, send
        confirm_conflicts: true.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/imports/{_enc(id)}/apply",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncManagedGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        user_id: str | None = None,
        client_id: str | None = None,
        status: Literal["active", "revoked"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.ManagedGrantsListResponse:
        """List OpenID Grant Management grants: what each OAuth client holds for each user under
        a `grant_id`, newest first. Filter by `user_id`, `client_id` (the public client id)
        and `status`.
        """
        return await self._t.request(
            method="GET",
            path="/v1/grant_management/grants",
            query=_q(
                user_id=user_id,
                client_id=client_id,
                status=status,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def get(
        self,
        id: str,
    ) -> m.ManagedGrantsGetResponse:
        """Read one grant: its scopes, resource, authorization_details, status and revision."""
        return await self._t.request(
            method="GET",
            path=f"/v1/grant_management/grants/{_enc(id)}",
        )

    async def narrow(
        self,
        id: str,
        body: m.ManagedGrantsNarrowBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.ManagedGrantsNarrowResponse:
        """Narrow a grant: send the `scopes` and/or `authorization_details` it should keep.
        Anything it does not already hold is a 400 (only the user widens a grant, by
        authorizing again with `grant_management_action=merge`). Refresh tokens under the
        grant are clamped to the narrower scope; a revoked grant is a 404.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/grant_management/grants/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def revoke(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> m.ManagedGrantsRevokeResponse:
        """Revoke a grant and everything issued under it: refresh tokens stop refreshing and
        access tokens that carry the `grant_id` stop validating at once. `tokens_ended` counts
        the refresh grants that ended with it. Revoking an already-revoked grant answers 200
        with `tokens_ended: 0`.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/grant_management/grants/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncLeastPrivilege:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def report(
        self,
        *,
        days: int | None = None,
        subject_type: Literal["api_key", "oauth_client", "mcp_gateway", "agent"] | None = None,
        subject_id: str | None = None,
        only_unused: bool | None = None,
        limit: int | None = None,
        format: Literal["json", "csv"] | None = None,
        starting_after: str | None = None,
    ) -> m.LeastPrivilegeReportResponse:
        """The least-privilege report: for every active secret key, OAuth client, MCP gateway and
        agent, what it is allowed to do against what it used over the window, the permissions
        never used, and the narrower grant that would still cover its use. Credentials with
        something unused come first. `format=csv` exports one row per permission.
        """
        return await self._t.request(
            method="GET",
            path="/v1/least_privilege/report",
            query=_q(
                days=days,
                subject_type=subject_type,
                subject_id=subject_id,
                only_unused=only_unused,
                limit=limit,
                format=format,
                starting_after=starting_after,
            ),
        )

    async def get(
        self,
        type: str,
        id: str,
        *,
        days: int | None = None,
    ) -> m.LeastPrivilegeGetResponse:
        """The least-privilege report of one credential (`type` is api_key, oauth_client,
        mcp_gateway or agent). 404 for a credential the report does not cover, such as a
        revoked key.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/least_privilege/report/{_enc(type)}/{_enc(id)}",
            query=_q(days=days),
        )

    async def apply(
        self,
        body: m.LeastPrivilegeApplyBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.LeastPrivilegeApplyResponse:
        """Apply a credential's suggestion: narrow a secret key's scopes, an OAuth client's
        allowed scopes, an MCP gateway's tool policy, or revoke an agent's unused tool grants.
        Preview it first with `?dry_run=true`, then send the same body for real. `digest`
        (from the report) must match the current suggestion, else 409, so what you previewed
        is what is applied; the write is conditional on the credential being unchanged. A
        suggestion only ever removes permissions. Over a window the data does not fully cover
        (`confidence: low`) it needs `acknowledge_short_window: true`. Audited as
        `least_privilege.applied`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/least_privilege/apply",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncFlags:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def assign_organization_entitlements(
        self,
        id: str,
        body: m.FlagsAssignOrganizationEntitlementsBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.FlagsAssignOrganizationEntitlementsResponse:
        """Assign an organization's entitlements (a plan, a feature list and/or limits,
        optionally expiring) without a billing subscription. Replaces whatever was assigned or
        overridden before; an empty body clears it and the organization falls back to its
        billing plan. Reaches the `pla`, `fea` and `ent` session claims on the next token.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(id)}/entitlements",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def create(
        self,
        body: m.FlagsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.FlagsCreateResponse:
        """Create a feature flag: a typed value (`boolean`, `string`, `int` or `json`) with a
        `default_value`, an `off_value` (served while `enabled` is false; defaults to false
        for a boolean, else the default) and ordered targeting `rules` by org, user, plan and
        percentage. 409 when the key exists.
        """
        return await self._t.request(
            method="POST",
            path="/v1/feature_flags",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        *,
        starting_after: str | None = None,
        limit: int | None = None,
    ) -> CursorPage:
        """List feature flags ordered by key. `starting_after` is the key of the last flag of the
        previous page.
        """
        return await self._t.request(
            method="GET",
            path="/v1/feature_flags",
            query=_q(starting_after=starting_after, limit=limit),
        )

    async def retrieve(
        self,
        key: str,
    ) -> m.FlagsRetrieveResponse:
        """Read one feature flag."""
        return await self._t.request(
            method="GET",
            path=f"/v1/feature_flags/{_enc(key)}",
        )

    async def update(
        self,
        key: str,
        body: m.FlagsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.FlagsUpdateResponse:
        """Change a flag's description, kill switch, default or off value, or replace its rules.
        The type and key are fixed.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/feature_flags/{_enc(key)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        key: str,
        *,
        dry_run: bool | None = None,
    ) -> m.FlagsDeleteResponse:
        """Delete a feature flag."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/feature_flags/{_enc(key)}",
            query=_q(dry_run=dry_run),
        )

    async def evaluate(
        self,
        body: m.FlagsEvaluateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.FlagsEvaluateResponse:
        """Evaluate every flag (or the listed `keys`) for a subject (`user_id`, `org_id`,
        `plan`). When `plan` is omitted it is the organization's (else the user's) resolved
        plan. Each result carries the `value` and a `reason` (`off`, `default` or
        `rule:<index>`).
        """
        return await self._t.request(
            method="POST",
            path="/v1/feature_flags/evaluate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def assign_user_entitlements(
        self,
        id: str,
        body: m.FlagsAssignUserEntitlementsBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.FlagsAssignUserEntitlementsResponse:
        """Assign a user's entitlements the same way as for an organization."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/users/{_enc(id)}/entitlements",
            query=_q(dry_run=dry_run),
            body=body,
        )


class AsyncMfaFactors:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.yubikeys = _AsyncMfaFactorsYubikeys(transport)
        self.smart_card_mappings = _AsyncMfaFactorsSmartCardMappings(transport)

    async def set_yubico_secret(
        self,
        body: m.MfaFactorsSetYubicoSecretBody,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsSetYubicoSecretResponse:
        """Store (write-only, encrypted) the Yubico cloud API secret key (base64, from
        upgrade.yubico.com/getapikey). The client id is mfa.yubikey.clientId. Used when
        mfa.yubikey.mode is "cloud".
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/yubico_secret",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def remove_yubico_secret(
        self,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsRemoveYubicoSecretResponse:
        """Remove the stored Yubico cloud secret. Cloud-mode YubiKey sign-ins then fail until a
        new one is stored.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/yubico_secret",
            query=_q(dry_run=dry_run),
        )

    async def set_duo_secret(
        self,
        body: m.MfaFactorsSetDuoSecretBody,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsSetDuoSecretResponse:
        """Store (write-only, encrypted) the Duo Web SDK / Universal Prompt client secret. The
        client id (integration key) and API host are mfa.duo.clientId and mfa.duo.apiHost.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/duo_secret",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def remove_duo_secret(
        self,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsRemoveDuoSecretResponse:
        """Remove the stored Duo client secret."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/duo_secret",
            query=_q(dry_run=dry_run),
        )

    async def set_smart_card_secret(
        self,
        body: m.MfaFactorsSetSmartCardSecretBody,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsSetSmartCardSecretResponse:
        """Store (write-only, encrypted) the shared secret your TLS proxy sends in the
        mfa.smartCard.secretHeader header, so Atlas believes the certificate headers only from
        your proxy. Use a random value of at least 24 characters.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/smart_card_secret",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def remove_smart_card_secret(
        self,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsRemoveSmartCardSecretResponse:
        """Remove the stored proxy secret. Smart card sign-in then refuses every request."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/smart_card_secret",
            query=_q(dry_run=dry_run),
        )

    async def duo_health_check(
        self,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MfaFactorsDuoHealthCheckResponse:
        """Ask Duo whether the configured integration key, stored secret and API host are
        accepted (Duo's health check). Reports ok and a message; nothing is changed.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/duo_health_check",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def reset_security_questions(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> m.MfaFactorsResetSecurityQuestionsResponse:
        """Clear a user's security-question answers (and any lockout). They set new ones from
        their account.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(id)}/security_questions",
            query=_q(dry_run=dry_run),
        )


class _AsyncMfaFactorsYubikeys:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.MfaFactorsYubikeysListResponse:
        """List the registered self-held YubiKeys (public id, owner, replay counter). The AES
        keys are never returned.
        """
        return await self._t.request(
            method="GET",
            path="/v1/yubikeys",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def register(
        self,
        body: m.MfaFactorsYubikeysRegisterBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MfaFactorsYubikeysRegisterResponse:
        """Register a YubiKey's AES key for self-held Yubico OTP (mfa.yubikey.mode "self_held").
        The key is stored encrypted and never returned. Give user_id to assign it; otherwise
        the first user to enrol it with a valid OTP claims it. 409 when the public id is
        already registered.
        """
        return await self._t.request(
            method="POST",
            path="/v1/yubikeys",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def remove(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Remove a registered YubiKey. A factor already enrolled with it stops verifying."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/yubikeys/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncMfaFactorsSmartCardMappings:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.MfaFactorsSmartCardMappingsListResponse:
        """List the certificate attributes registered for a user."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/smartcard_mappings",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def add(
        self,
        id: str,
        body: m.MfaFactorsSmartCardMappingsAddBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.MfaFactorsSmartCardMappingsAddResponse:
        """Pre-register the certificate attribute that signs this user in with a smart card: kind
        fingerprint (SHA-256, 64 hex), serial (hex, plus the issuer DN), san_email, san_upn or
        subject_cn. A registered mapping only applies while its kind is listed in
        mfa.smartCard.mappingRules. 409 when the value is already mapped.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/smartcard_mappings",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def remove(
        self,
        id: str,
        mapping_id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Remove a registered certificate mapping."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(id)}/smartcard_mappings/{_enc(mapping_id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncAnalytics:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.reports = _AsyncAnalyticsReports(transport)
        self.alert_rules = _AsyncAnalyticsAlertRules(transport)

    async def funnel(
        self,
        *,
        kind: Literal["sign_in", "sign_up"] | None = None,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsFunnelResponse:
        """Where sign-in or sign-up attempts end, per method: started, completed, abandoned, and
        the step each unfinished attempt stopped at, with the completion rate. Each attempt is
        counted once, at its final state.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/funnel",
            query=_q(
                **{
                    "kind": kind,
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def journey_funnel(
        self,
        *,
        journey_id: str,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsJourneyFunnelResponse:
        """What happened at each step of a sign-in journey: how often it held a sign-in (a
        required action or form), was completed, ran at the sign-in (an Action, claim or
        redirect) or refused it, with the completion rate of its holds. Steps follow the
        active version; a sub-flow's steps are prefixed with the sub-flow step id. No
        organization slice.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/journey_funnel",
            query=_q(
                **{
                    "journey_id": journey_id,
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def failures(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsFailuresResponse:
        """Failed first- and second-factor attempts by reason and method, most frequent first. No
        organization slice (a failed attempt belongs to no organization).
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/failures",
            query=_q(
                **{
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def breakdown(
        self,
        *,
        dimension: Literal["method", "device", "browser", "os", "country"] | None = None,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsBreakdownResponse:
        """Sign-ins split by one dimension: method, device type, browser, operating system or
        country (country needs a GeoIP database on the deployment; otherwise it reports
        `unknown`).
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/breakdown",
            query=_q(
                **{
                    "dimension": dimension,
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def active_users(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsActiveUsersResponse:
        """Distinct active users and sign-ins per bucket, each bucket split into new users
        (signed up in that bucket) and returning users, plus trailing 1/7/30-day active-user
        counts (dau, wau, mau) ending at `to`.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/active_users",
            query=_q(
                **{
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def passkey_adoption(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsPasskeyAdoptionResponse:
        """How many users hold a passkey (adoption rate), and the passkey share of sign-ins per
        bucket.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/passkey_adoption",
            query=_q(
                **{
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def api_usage(
        self,
        *,
        subject_type: Literal["api_key", "end_user_api_key", "organization"] | None = None,
        subject_id: str | None = None,
        window_minutes: int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsApiUsageResponse:
        """API usage per subject against its own baseline: secret keys calling the Backend API,
        end-user API keys verified through /v1/api_keys/verify, and organizations (Backend API
        calls on the organization plus verifications of its keys). For each: requests and the
        failure rate in the window, the average hourly rate over the 7 days before, and the
        ratio between them, highest ratio first (at most 100). Counts are written in batches
        and can lag by up to a minute.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/api_usage",
            query=_q(
                subject_type=subject_type,
                subject_id=subject_id,
                window_minutes=window_minutes,
                limit=limit,
                starting_after=starting_after,
            ),
        )


class _AsyncAnalyticsReports:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def inactive_users(
        self,
        *,
        inactive_days: int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
    ) -> CursorPage:
        """Compliance report: users who have not signed in for `inactive_days` (default 90),
        oldest id first, cursor-paginated (an export returns up to 50,000 rows).
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/reports/inactive_users",
            query=_q(
                **{
                    "inactive_days": inactive_days,
                    "limit": limit,
                    "starting_after": starting_after,
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                }
            ),
        )

    async def mfa_coverage(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsReportsMfaCoverageResponse:
        """Compliance report: how many users are protected by a second factor, a passkey, either,
        or neither.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/reports/mfa_coverage",
            query=_q(
                **{
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )

    async def access_by_app(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal["day", "week", "month"] | None = None,
        organization_id: str | None = None,
        format: Literal["json", "csv", "parquet"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> m.AnalyticsReportsAccessByAppResponse:
        """Compliance report: for each application (OAuth client), how many users have access,
        how many grants are active and how many users signed in during the window.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/reports/access_by_app",
            query=_q(
                **{
                    "from": from_,
                    "to": to,
                    "days": days,
                    "granularity": granularity,
                    "organization_id": organization_id,
                    "format": format,
                    "limit": limit,
                    "starting_after": starting_after,
                }
            ),
        )


class _AsyncAnalyticsAlertRules:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List analytics alert rules with their state and last measured value. The metric
        catalog is included.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/alert_rules",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.AnalyticsAlertRulesCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AnalyticsAlertRulesCreateResponse:
        """Create an alert rule: tell me when a sign-in health metric, or a key or organization's
        API usage against its baseline, crosses a threshold over a trailing window. It must
        have email_contacts, a webhook_url or ssf. A webhook signing secret is returned once.
        """
        return await self._t.request(
            method="POST",
            path="/v1/analytics/alert_rules",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.AnalyticsAlertRulesGetResponse:
        """One analytics alert rule."""
        return await self._t.request(
            method="GET",
            path=f"/v1/analytics/alert_rules/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.AnalyticsAlertRulesUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.AnalyticsAlertRulesUpdateResponse:
        """Edit an alert rule. Editing re-arms it."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/analytics/alert_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete an alert rule."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/analytics/alert_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def test(
        self,
        id: str,
        body: m.AnalyticsAlertRulesTestBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AnalyticsAlertRulesTestResponse:
        """Measure the rule now. With `notify: true` it also sends the rule's email and webhook,
        whether or not the rule is breaching, to prove the delivery path.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/analytics/alert_rules/{_enc(id)}/test",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMarketing:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_settings(
        self,
    ) -> m.MarketingGetSettingsResponse:
        """The marketing settings: which UTM / ad-click-id parameters the SDK captures onto new
        users, and the GA4, GTM and Hotjar ids hosted pages load after consent.
        """
        return await self._t.request(
            method="GET",
            path="/v1/marketing_settings",
        )

    async def update_settings(
        self,
        body: m.MarketingUpdateSettingsBody,
        *,
        dry_run: bool | None = None,
    ) -> m.MarketingUpdateSettingsResponse:
        """Change the marketing settings. `capture.params` empty means the standard set
        (utm_source, utm_medium, utm_campaign, utm_term, utm_content, utm_id and the common ad
        click ids). Hosted pages load a configured script only when the visitor's consent
        manager grants `scripts.consent_category` (default analytics); with no consent signal
        nothing loads.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/marketing_settings",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def list_leads(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        form: str | None = None,
        format: Literal["json", "csv"] | None = None,
    ) -> CursorPage:
        """The lead / subscribe form's submissions, newest first, with the first-touch
        attribution captured with each. `format=csv` exports up to 50,000.
        """
        return await self._t.request(
            method="GET",
            path="/v1/leads",
            query=_q(limit=limit, starting_after=starting_after, form=form, format=format),
        )

    async def delete_lead(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete one captured lead."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/leads/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncAuditEventSchemas:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the registered audit event schemas, by action then version (newest first)."""
        return await self._t.request(
            method="GET",
            path="/v1/audit_event_schemas",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def register(
        self,
        body: m.AuditEventSchemasRegisterBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AuditEventSchemasRegisterResponse:
        """Register a schema for an action: the target types and actor types it allows and a JSON
        Schema its metadata must satisfy. `version` defaults to the next number for that
        action; a version is immutable (registering it again is a 409) - change a schema by
        registering a new version. From then on events with this action are validated on
        write.
        """
        return await self._t.request(
            method="POST",
            path="/v1/audit_event_schemas",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.AuditEventSchemasGetResponse:
        """One audit event schema."""
        return await self._t.request(
            method="GET",
            path=f"/v1/audit_event_schemas/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.AuditEventSchemasUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.AuditEventSchemasUpdateResponse:
        """Change a schema version's description or status. A deprecated version is no longer
        applied by default but still validates events that name it with `schema_version`.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/audit_event_schemas/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Remove a schema version. Events already recorded keep their `schema_version` number."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/audit_event_schemas/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def redact(
        self,
        id: str,
        body: m.AuditEventSchemasRedactBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AuditEventSchemasRedactResponse:
        """Blank named fields of one audit event (replaced by [redacted]) without deleting it:
        `actor_id`, `target_id`, `target_name` or `metadata.<dotted.path>`. A `reason` is
        required. The redaction is recorded in its own log (GET
        /v1/audit_events/:id/redactions) and in Atlas's audit log as `audit_event.redacted` -
        the fields and the reason, never the removed values.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/audit_events/{_enc(id)}/redact",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def redactions(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """An audit event's redaction history: which fields were blanked, why, and by which key."""
        return await self._t.request(
            method="GET",
            path=f"/v1/audit_events/{_enc(id)}/redactions",
            query=_q(limit=limit, starting_after=starting_after),
        )


class AsyncDirectoryPullSources:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.sync_runs = _AsyncDirectoryPullSourcesSyncRuns(transport)

    async def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List HR / directory pull sources, optionally for one organization (organization_id).
        Credentials are never returned.
        """
        return await self._t.request(
            method="GET",
            path="/v1/directory_pull_sources",
            query=_q(organization_id=organization_id, limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.DirectoryPullSourcesCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.DirectoryPullSourcesCreateResponse:
        """Create a pull source for an organization: provider (entra, google_workspace, bamboohr,
        hibob, personio, csv, rest_json), config, write-only credentials and settings
        (schedule, role mappings, disable on removal).
        """
        return await self._t.request(
            method="POST",
            path="/v1/directory_pull_sources",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.DirectoryPullSourcesGetResponse:
        """Read one pull source."""
        return await self._t.request(
            method="GET",
            path=f"/v1/directory_pull_sources/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.DirectoryPullSourcesUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.DirectoryPullSourcesUpdateResponse:
        """Change the source name, status (active or paused), config, credentials, default role
        or settings. Settings are merged.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/directory_pull_sources/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a pull source and its run log. Users it created are kept."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/directory_pull_sources/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def set_csv(
        self,
        id: str,
        body: m.DirectoryPullSourcesSetCsvBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Upload the CSV a csv source without a URL reads on its next run (up to 5 MiB)."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/directory_pull_sources/{_enc(id)}/csv",
            query=_q(dry_run=dry_run),
            body=body,
        )


class _AsyncDirectoryPullSourcesSyncRuns:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.DirectoryPullSourcesSyncRunsCreateResponse:
        """Queue a pull now. One run at a time per source (409 otherwise); the worker executes
        it.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/directory_pull_sources/{_enc(id)}/sync_runs",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List the runs of a source with counts of people seen, created, re-roled, disabled and
        re-enabled.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/directory_pull_sources/{_enc(id)}/sync_runs",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(
        self,
        id: str,
        run_id: str,
    ) -> m.DirectoryPullSourcesSyncRunsGetResponse:
        """Read one directory pull run with its counts and error."""
        return await self._t.request(
            method="GET",
            path=f"/v1/directory_pull_sources/{_enc(id)}/sync_runs/{_enc(run_id)}",
        )


class _AsyncOrgLdapConnectionsSyncRuns:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self,
        id: str,
        body: m.OrgLdapConnectionsSyncRunsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Queue a sync run now (202). `full` (default) lists the whole directory and, when
        disable-on-removal is on, bans users that left it; `delta` only reads entries changed
        since the last successful run. Refused with 409 while another run is queued or
        running.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/org_ldap_connections/{_enc(id)}/sync_runs",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The sync run log, newest first, with per-run counts (seen, created, updated, skipped,
        disabled, role changes, groups, errors) and any failure message.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/org_ldap_connections/{_enc(id)}/sync_runs",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(
        self,
        id: str,
        run_id: str,
    ) -> m.OrgLdapConnectionsSyncRunsGetResponse:
        """Read one LDAP directory sync run with its counts and error."""
        return await self._t.request(
            method="GET",
            path=f"/v1/org_ldap_connections/{_enc(id)}/sync_runs/{_enc(run_id)}",
        )


class AsyncRelayAgents:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List the on-prem relay agents with their allowed destinations and whether each is
        online. Secrets are never returned.
        """
        return await self._t.request(
            method="GET",
            path="/v1/relay_agents",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.RelayAgentsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.RelayAgentsCreateResponse:
        """Register an outbound-only relay agent. The response carries the agent token once; it
        cannot be read back. An agent can reach only the destinations in allowed_destinations
        (host, host:port, *.domain).
        """
        return await self._t.request(
            method="POST",
            path="/v1/relay_agents",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.RelayAgentsGetResponse:
        """Read one relay agent, including when it last polled."""
        return await self._t.request(
            method="GET",
            path=f"/v1/relay_agents/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.RelayAgentsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.RelayAgentsUpdateResponse:
        """Rename an agent, change its allowed destinations or pinned client-certificate
        thumbprints, or revoke it (status: revoked).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/relay_agents/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a relay agent and its queued jobs."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/relay_agents/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def rotate_secret(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.RelayAgentsRotateSecretResponse:
        """Issue a new agent token (returned once). The old token stops working immediately."""
        return await self._t.request(
            method="POST",
            path=f"/v1/relay_agents/{_enc(id)}/rotate_secret",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )


class _AsyncOAuthClientsAppSettings:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        id: str,
    ) -> m.OauthClientsAppSettingsGetResponse:
        """The per-application settings of an OAuth client: allowed sign-in methods, hosted-page
        branding, the user-claim allow-list for ID tokens and userinfo, and the traits a
        session from this app may write. Null = no restriction.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(id)}/app_settings",
        )

    async def update(
        self,
        id: str,
        body: m.OauthClientsAppSettingsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.OauthClientsAppSettingsUpdateResponse:
        """Change the per-application settings. Each field sent replaces the stored one and null
        clears it; fields left out keep their value. Unknown fields and malformed values are
        refused.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/oauth_clients/{_enc(id)}/app_settings",
            query=_q(dry_run=dry_run),
            body=body,
        )


class _AsyncOAuthClientsWorkloadIdentity:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def presets(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the workload platforms Atlas knows defaults for (SPIFFE, Kubernetes, GitHub
        Actions, GCP, Azure): issuer, JWKS URL and the shape of the token subject.
        """
        return await self._t.request(
            method="GET",
            path="/v1/workload_identity/presets",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def cloud_trust(
        self,
        *,
        provider: Literal["aws", "gcp", "azure"],
        audience: str,
        subject: str,
        tenant_id: str | None = None,
    ) -> m.OauthClientsWorkloadIdentityCloudTrustResponse:
        """Trust-policy snippets that make AWS (AssumeRoleWithWebIdentity), GCP (workload
        identity federation) or Azure (federated credentials) accept an access token issued by
        this instance. Nothing is changed in the cloud.
        """
        return await self._t.request(
            method="GET",
            path="/v1/workload_identity/cloud_trust",
            query=_q(provider=provider, audience=audience, subject=subject, tenant_id=tenant_id),
        )


class _AsyncOAuthClientsTrustedIssuers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the external issuers this OAuth client trusts to assert users through the RFC
        7523 jwt-bearer grant.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(id)}/trusted_issuers",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        id: str,
        body: m.OauthClientsTrustedIssuersCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.OauthClientsTrustedIssuersCreateResponse:
        """Trust an external issuer for this client. With purpose user_assertion (default) its
        signed JWTs (verified against the inline jwks or the https jwks_uri) can then be
        presented to POST /oauth2/token with
        grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer. subject_mapping says how the
        JWT sub names an Atlas user. With purpose client_auth or both (PRO-06 workload
        identity) a client registered with token_endpoint_auth_method workload_jwt
        authenticates by presenting a token from this issuer as its client_assertion;
        subject_pattern is then required and must name the workload. workload_kind
        github_actions, gcp and azure fill in the issuer and JWKS URL. Audited as
        oauth_trusted_issuer.created.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{_enc(id)}/trusted_issuers",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        id: str,
        issuer_id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Stop trusting an issuer: its assertions are refused at once. Audited as
        oauth_trusted_issuer.deleted.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{_enc(id)}/trusted_issuers/{_enc(issuer_id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncOAuthClientsLoginRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        *,
        login_challenge: str,
    ) -> m.OauthClientsLoginRequestsGetResponse:
        """Read a login challenge: which application is signing a user in, with what scopes, and
        who (if anyone) is already signed in on this browser.
        """
        return await self._t.request(
            method="GET",
            path="/v1/oauth_login_requests",
            query=_q(login_challenge=login_challenge),
        )

    async def accept(
        self,
        body: m.OauthClientsLoginRequestsAcceptBody,
        *,
        login_challenge: str,
        dry_run: bool | None = None,
    ) -> m.OauthClientsLoginRequestsAcceptResponse:
        """Accept a login challenge: the visitor authenticated as `subject` (an Atlas user id).
        Returns redirect_to; when the browser follows it Atlas signs the user in and continues
        the authorization. The returned link is single-use and valid for five minutes.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_login_requests/accept",
            query=_q(dry_run=dry_run, login_challenge=login_challenge),
            body=body,
        )

    async def reject(
        self,
        body: m.OauthClientsLoginRequestsRejectBody,
        *,
        login_challenge: str,
        dry_run: bool | None = None,
    ) -> m.OauthClientsLoginRequestsRejectResponse:
        """Reject a login challenge. Following redirect_to returns the application to its
        redirect_uri with the OAuth error.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_login_requests/reject",
            query=_q(dry_run=dry_run, login_challenge=login_challenge),
            body=body,
        )


class _AsyncOAuthClientsConsentRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        *,
        consent_challenge: str,
    ) -> m.OauthClientsConsentRequestsGetResponse:
        """Read a consent challenge: the signed-in user, the application and the scopes,
        audience, authorization details and organization it asks for.
        """
        return await self._t.request(
            method="GET",
            path="/v1/oauth_consent_requests",
            query=_q(consent_challenge=consent_challenge),
        )

    async def accept(
        self,
        body: m.OauthClientsConsentRequestsAcceptBody,
        *,
        consent_challenge: str,
        dry_run: bool | None = None,
    ) -> m.OauthClientsConsentRequestsAcceptResponse:
        """Accept a consent challenge, optionally narrowing the granted scopes. Following
        redirect_to (in the same browser that started the flow) records the consent unless
        remember is false, and returns the application to its redirect_uri with a code.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_consent_requests/accept",
            query=_q(dry_run=dry_run, consent_challenge=consent_challenge),
            body=body,
        )

    async def reject(
        self,
        body: m.OauthClientsConsentRequestsRejectBody,
        *,
        consent_challenge: str,
        dry_run: bool | None = None,
    ) -> m.OauthClientsConsentRequestsRejectResponse:
        """Reject a consent challenge. Following redirect_to returns the application to its
        redirect_uri with the OAuth error.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_consent_requests/reject",
            query=_q(dry_run=dry_run, consent_challenge=consent_challenge),
            body=body,
        )


class _AsyncOrganizationsWebhookEndpoints:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the organization's own webhook endpoints. Backend API. Never returns a secret."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        id: str,
        body: m.OrganizationsWebhookEndpointsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Register a webhook endpoint for one organization. It receives only that organization's
        events (membership, invitation, role, domain and organization events). The signing
        secret is returned in this response only. Backend API. At most 20 per organization.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
        endpoint_id: str,
    ) -> m.OrganizationsWebhookEndpointsGetResponse:
        """Retrieve one of the organization's webhook endpoints, with its delivery health."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}",
        )

    async def update(
        self,
        id: str,
        endpoint_id: str,
        body: m.OrganizationsWebhookEndpointsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.OrganizationsWebhookEndpointsUpdateResponse:
        """Update the url, subscribed events, description or active flag of one of the
        organization's endpoints. Never re-reveals the secret.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        endpoint_id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete one of the organization's webhook endpoints and its delivery log. An id from
        another organization is a 404.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}",
            query=_q(dry_run=dry_run),
        )

    async def rotate_secret(
        self,
        id: str,
        endpoint_id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.OrganizationsWebhookEndpointsRotateSecretResponse:
        """Rotate the signing secret. The previous secret keeps signing alongside the new one for
        24 hours so the receiver can switch over without dropping events.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}/rotate_secret",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def deliveries(
        self,
        id: str,
        endpoint_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        status: Literal["pending", "success", "failed"] | None = None,
        event_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        trace: str | None = None,
    ) -> CursorPage:
        """The endpoint's delivery log: payload, response and retry state for each attempt,
        filterable by status, event type and time.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}/deliveries",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                status=status,
                event_type=event_type,
                since=since,
                until=until,
                trace=trace,
            ),
        )


class AsyncOauthClientProfiles:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the OAuth client policy profiles: the built-ins (fapi2_security,
        fapi2_message_signing, pkce_required, par_required, dpop_required) and your custom
        ones.
        """
        return await self._t.request(
            method="GET",
            path="/v1/oauth_client_profiles",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def set(
        self,
        name: str,
        body: m.OauthClientProfilesSetBody,
        *,
        dry_run: bool | None = None,
    ) -> m.OauthClientProfilesSetResponse:
        """Create or replace a custom client policy profile (rules: PKCE, PAR, sender constraint,
        signed request object, allowed auth methods and signing algorithms, https-only
        redirects, allowed claims). Built-in names are reserved.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_client_profiles/{_enc(name)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        name: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a custom client policy profile. 409 while any client is assigned it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_client_profiles/{_enc(name)}",
            query=_q(dry_run=dry_run),
        )


class AsyncPasskeyApi:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def registration_init(
        self,
        body: m.PasskeyApiRegistrationInitBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PasskeyApiRegistrationInitResponse:
        """Start registering a passkey for one of your users. Returns WebAuthn creation options
        for the browser.
        """
        return await self._t.request(
            method="POST",
            path="/v1/passkey_api/registration/init",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def registration_finalize(
        self,
        body: m.PasskeyApiRegistrationFinalizeBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PasskeyApiRegistrationFinalizeResponse:
        """Verify the browser’s attestation and store the passkey for the user. 409 if the
        credential is already registered; 403 if the authenticator is blocked by the passkey
        policy.
        """
        return await self._t.request(
            method="POST",
            path="/v1/passkey_api/registration/finalize",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def login_init(
        self,
        body: m.PasskeyApiLoginInitBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PasskeyApiLoginInitResponse:
        """Start a passkey login. With user_id the user’s credentials are listed; without it the
        login is discoverable and the credential names the user.
        """
        return await self._t.request(
            method="POST",
            path="/v1/passkey_api/login/init",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def login_finalize(
        self,
        body: m.PasskeyApiLoginFinalizeBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PasskeyApiLoginFinalizeResponse:
        """Verify the browser’s assertion. Returns the user_id the passkey belongs to; your
        backend then starts its own session. Pass user_id to require that exact user.
        Challenges are single use.
        """
        return await self._t.request(
            method="POST",
            path="/v1/passkey_api/login/finalize",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the passkeys registered for one of your users."""
        return await self._t.request(
            method="GET",
            path=f"/v1/passkey_api/users/{_enc(user_id)}/passkeys",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def delete(
        self,
        user_id: str,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete one of your user’s passkeys."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/passkey_api/users/{_enc(user_id)}/passkeys/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def usage(
        self,
    ) -> m.PasskeyApiUsageResponse:
        """Passkeys stored through the Passkey API on this instance (the metered quantity)."""
        return await self._t.request(
            method="GET",
            path="/v1/passkey_api/usage",
        )


class AsyncVc:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.credential_types = _AsyncVcCredentialTypes(transport)
        self.credentials = _AsyncVcCredentials(transport)
        self.presentation_requests = _AsyncVcPresentationRequests(transport)

    async def create_offer(
        self,
        body: m.VcCreateOfferBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.VcCreateOfferResponse:
        """Create a wallet offer for a user (pre-authorized code flow). The response carries the
        code once, as an openid-credential-offer:// link.
        """
        return await self._t.request(
            method="POST",
            path="/v1/vc/offers",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncVcCredentialTypes:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the credential types you issue."""
        return await self._t.request(
            method="GET",
            path="/v1/vc/credential_types",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.VcCredentialTypesCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.VcCredentialTypesCreateResponse:
        """Define a credential type: its vct, and how each claim is filled from a user’s
        attributes. Issued as SD-JWT VC.
        """
        return await self._t.request(
            method="POST",
            path="/v1/vc/credential_types",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.VcCredentialTypesGetResponse:
        """Read one credential type."""
        return await self._t.request(
            method="GET",
            path=f"/v1/vc/credential_types/{_enc(id)}",
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a credential type and the records of what was issued under it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/vc/credential_types/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncVcCredentials:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List issued credentials (most recent 200), optionally for one user."""
        return await self._t.request(
            method="GET",
            path="/v1/vc/credentials",
            query=_q(user_id=user_id, limit=limit, starting_after=starting_after),
        )

    async def revoke(
        self,
        id: str,
        body: dict[str, Any],
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.VcCredentialsRevokeResponse:
        """Revoke an issued credential: its status-list bit is set and later presentations are
        refused.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/vc/credentials/{_enc(id)}/revoke",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncVcPresentationRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self,
        body: m.VcPresentationRequestsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.VcPresentationRequestsCreateResponse:
        """Start a verifier request for a credential type and claims. Show
        authorization_request_uri to the wallet, then read the request for the outcome.
        """
        return await self._t.request(
            method="POST",
            path="/v1/vc/presentation_requests",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.VcPresentationRequestsGetResponse:
        """Read a presentation request and its outcome."""
        return await self._t.request(
            method="GET",
            path=f"/v1/vc/presentation_requests/{_enc(id)}",
        )


class AsyncListen:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create_session(
        self,
        body: m.ListenCreateSessionBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ListenCreateSessionResponse:
        """Start a local webhook forwarding session (what `atlas listen` uses). Returns a session
        id, a signing secret for that session only (it is unrelated to any registered
        endpoint's secret) and the stream URL. The session needs no storage: it expires at
        `expires_at` (default 1 hour, `ttl_seconds` 60 to 43200).
        """
        return await self._t.request(
            method="POST",
            path="/v1/listen/sessions",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def stream_session(
        self,
        id: str,
        *,
        events: str | None = None,
        after: str | None = None,
        max_events: int | None = None,
        poll_ms: int | None = None,
        max_wait_seconds: int | None = None,
    ) -> str:
        """Server-Sent Events stream of the instance's new events for a listen session. Each
        `webhook` event carries `{id, type, headers, body}`: the headers (`atlas-id`,
        `atlas-timestamp`, `atlas-signature`) and the exact JSON body of a would-be delivery,
        signed with the session secret. Starts at "now" unless resumed with `Last-Event-ID` or
        `after`. Query: `events` (comma-separated types or patterns), `max_events` and
        `max_wait_seconds` (end the stream early, for scripts and CI). A `: keep-alive`
        comment is sent every 15 seconds; an `expired` event ends the stream at the session
        expiry. 404 for an unknown session id, 400 once expired.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/listen/sessions/{_enc(id)}/stream",
            query=_q(
                events=events,
                after=after,
                max_events=max_events,
                poll_ms=poll_ms,
                max_wait_seconds=max_wait_seconds,
            ),
            raw=True,
            headers={"accept": "text/event-stream"},
        )


class AsyncAgentRegistration:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> m.AgentRegistrationGetResponse:
        """Read the agent registration settings (enabled, allowed identity kinds, untrusted and
        trusted scopes, claim code lifetime).
        """
        return await self._t.request(
            method="GET",
            path="/v1/agent_registration",
        )

    async def replace(
        self,
        body: m.AgentRegistrationReplaceBody,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Update the agent registration settings. Partial: only the fields sent change."""
        return await self._t.request(
            method="PUT",
            path="/v1/agent_registration",
            query=_q(dry_run=dry_run),
            body=body,
        )


class AsyncAgents:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def claim(
        self,
        id: str,
        body: m.AgentsClaimBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Backend-assisted claim: bind an agent to a user you already know and promote it to
        trusted. Audited as agent.claimed.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/agents/{_enc(id)}/claim",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        *,
        owner_user_id: str | None = None,
        tier: Literal["untrusted", "trusted"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The agent registry: every registered agent with its tier, owner and status. Filter by
        owner_user_id or tier; page with limit and starting_after.
        """
        return await self._t.request(
            method="GET",
            path="/v1/agents",
            query=_q(
                owner_user_id=owner_user_id, tier=tier, limit=limit, starting_after=starting_after
            ),
        )

    async def get(
        self,
        id: str,
    ) -> JSON:
        """One agent with its currently valid access grants."""
        return await self._t.request(
            method="GET",
            path=f"/v1/agents/{_enc(id)}",
        )

    async def set_owner(
        self,
        id: str,
        body: m.AgentsSetOwnerBody,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Set the owning user of an agent, or null to remove the owner (which also drops the
        agent back to untrusted).
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/agents/{_enc(id)}/owner",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def revoke_access(
        self,
        id: str,
        body: m.AgentsRevokeAccessBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Revoke every grant and cancel every pending request of an agent. With disable: true
        the agent itself is revoked and can no longer get tokens. Emits agent.access_revoked.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/agents/{_enc(id)}/revoke_access",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAgentAccessRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def approve(
        self,
        id: str,
        body: m.AgentAccessRequestsApproveBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Approve a pending request, optionally for a limited time (expires_in_seconds). 409
        when it is no longer pending. Emits agent.access_decided.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/agent_access_requests/{_enc(id)}/approve",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def deny(
        self,
        id: str,
        body: m.AgentAccessRequestsDenyBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Deny a pending request. 409 when it is no longer pending. Emits agent.access_decided."""
        return await self._t.request(
            method="POST",
            path=f"/v1/agent_access_requests/{_enc(id)}/deny",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        *,
        status: Literal["pending", "approved", "denied", "revoked"] | None = None,
        agent_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List agent access requests, newest first. Filter by status (pending, approved, denied,
        revoked) or agent_id.
        """
        return await self._t.request(
            method="GET",
            path="/v1/agent_access_requests",
            query=_q(status=status, agent_id=agent_id, limit=limit, starting_after=starting_after),
        )


class AsyncWorkflows:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List lifecycle workflows: a trigger (cron, user created, inactive for N days,
        membership age, trial end, webhook event) plus ordered steps, run by the worker.
        """
        return await self._t.request(
            method="GET",
            path="/v1/workflows",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.WorkflowsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.WorkflowsCreateResponse:
        """Create a lifecycle workflow. Steps are notify, disable, delete, invite, add_to_org,
        remove_from_org, add_to_team, remove_from_team, add_to_group, remove_from_group (an
        instance group by id or slug) and call_action (an Action with the `workflow_step`
        trigger, which may be an `http` Action). Each subject runs once per workflow; the
        first failing step stops the run.
        """
        return await self._t.request(
            method="POST",
            path="/v1/workflows",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.WorkflowsGetResponse:
        """Read one lifecycle workflow."""
        return await self._t.request(
            method="GET",
            path=f"/v1/workflows/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.WorkflowsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.WorkflowsUpdateResponse:
        """Update a workflow's name, enabled flag, trigger or steps. Changing the trigger resets
        its cron slot and event cursor.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/workflows/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a workflow and its run history."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/workflows/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def dry_run(
        self,
        id: str,
        body: m.WorkflowsDryRunBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.WorkflowsDryRunResponse:
        """Check what a workflow would do for a user (`user_id`; none for cron) without changing
        anything. Every step is validated against live data and reported as `would_run` or
        `failed`.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(id)}/dry_run",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def run(
        self,
        id: str,
        body: m.WorkflowsRunBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.WorkflowsRunResponse:
        """Run a workflow now for one user (`user_id`; none for cron), outside its trigger.
        Returns the finished run.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(id)}/run",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def runs(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Run history, newest first, dry runs included (`dry_run`)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/workflows/{_enc(id)}/runs",
            query=_q(limit=limit, starting_after=starting_after),
        )


class AsyncPageTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The hosted-page templates of the instance: for each page (sign-in, sign-up,
        user-profile) the live template and the draft waiting to be previewed or promoted.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/page_templates",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(
        self,
        page: str,
    ) -> m.PageTemplatesGetResponse:
        """Read one page's live and draft template."""
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/page_templates/{_enc(page)}",
        )

    async def save_draft(
        self,
        page: str,
        body: m.PageTemplatesSaveDraftBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.PageTemplatesSaveDraftResponse:
        """Save a page template as the page's draft. A template is data: components (heading,
        text, image, link, button_link, list, divider, spacer, columns) in four regions
        (header, above_form, below_form, footer). It is validated on save: no raw HTML, CSS or
        script, https and mailto links only. The live page is unchanged until you promote.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/instance/page_templates/{_enc(page)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def discard(
        self,
        page: str,
        *,
        dry_run: bool | None = None,
        status: Literal["draft", "live"] | None = None,
    ) -> m.PageTemplatesDiscardResponse:
        """Drop the draft or take the live template down (`status`)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/instance/page_templates/{_enc(page)}",
            query=_q(dry_run=dry_run, status=status),
        )

    async def preview(
        self,
        page: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PageTemplatesPreviewResponse:
        """A signed link to the hosted page with the draft template applied (valid for one hour,
        noindex, with a preview banner). 409 when the page has no template.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/page_templates/{_enc(page)}/preview",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def promote(
        self,
        page: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PageTemplatesPromoteResponse:
        """Make the draft the live template."""
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/page_templates/{_enc(page)}/promote",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )


class AsyncServiceConnectors:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def catalog(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The services you can connect: for each kind the credential fields, the config fields
        and the operations with their inputs. Messaging (Twilio, SendGrid, Slack), CRM
        (HubSpot, Salesforce), analytics (Segment), fraud (Fingerprint, Arkose Labs, Forter,
        Sardine), identity verification (Persona, Onfido, Veriff, Stripe Identity) and a
        generic HTTPS connector.
        """
        return await self._t.request(
            method="GET",
            path="/v1/service_connector_catalog",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the instance's service connectors. Credentials are never returned."""
        return await self._t.request(
            method="GET",
            path="/v1/service_connectors",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.ServiceConnectorsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ServiceConnectorsCreateResponse:
        """Connect a service. `credentials` are checked against the kind's fields and stored in
        the vault (never returned again); `config` holds the non-secret settings. 409 when the
        name is taken.
        """
        return await self._t.request(
            method="POST",
            path="/v1/service_connectors",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.ServiceConnectorsGetResponse:
        """Read one service connector."""
        return await self._t.request(
            method="GET",
            path=f"/v1/service_connectors/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.ServiceConnectorsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.ServiceConnectorsUpdateResponse:
        """Rename, enable or disable a connector, merge new `config` values, or replace
        individual `credentials` (written as a new vault version; the others are kept).
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/service_connectors/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a connector and its stored credentials."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/service_connectors/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def invoke(
        self,
        id: str,
        body: m.ServiceConnectorsInvokeBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ServiceConnectorsInvokeResponse:
        """Run one operation of the connector (send a message, read a fraud signal, start an
        identity check). `input` is checked against the operation's fields. A refusal or
        failure from the service is 502 CONNECTOR_UPSTREAM_ERROR with its own message. Each
        call is audited without its input or output.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/service_connectors/{_enc(id)}/invoke",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncDesktopMfa:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_policy(
        self,
    ) -> m.DesktopMfaGetPolicyResponse:
        """The desktop-login MFA policy: who must pass a second factor at OS login, the allowed
        factors and the offline grace window.
        """
        return await self._t.request(
            method="GET",
            path="/v1/desktop_mfa/policy",
        )

    async def update_policy(
        self,
        body: m.DesktopMfaUpdatePolicyBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.DesktopMfaUpdatePolicyResponse:
        """Change the desktop-login MFA policy. Send only the fields to change. `applies_to:
        "selected"` needs at least one user or organization while enabled.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/desktop_mfa/policy",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def create_enrolment_code(
        self,
        body: m.DesktopMfaCreateEnrolmentCodeBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.DesktopMfaCreateEnrolmentCodeResponse:
        """Issue a single-use code a user types into the workstation agent to enrol it. Valid for
        `expires_in_minutes` (default 60, at most 7 days). Shown once.
        """
        return await self._t.request(
            method="POST",
            path="/v1/desktop_mfa/enrolment_codes",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_devices(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List enrolled workstations, optionally for one `user_id`."""
        return await self._t.request(
            method="GET",
            path="/v1/desktop_mfa/devices",
            query=_q(user_id=user_id, limit=limit, starting_after=starting_after),
        )

    async def get_device(
        self,
        id: str,
    ) -> m.DesktopMfaGetDeviceResponse:
        """Read one workstation with the offline verifiers issued to it."""
        return await self._t.request(
            method="GET",
            path=f"/v1/desktop_mfa/devices/{_enc(id)}",
        )

    async def delete_device(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a workstation and its device key."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/desktop_mfa/devices/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def revoke_device(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.DesktopMfaRevokeDeviceResponse:
        """Revoke a workstation. Its next call is refused with `device_status: revoked` and it
        wipes its offline cache; offline unlock stops working at the latest when the cached
        verifier expires.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/desktop_mfa/devices/{_enc(id)}/revoke",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def revoke_offline_cache(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.DesktopMfaRevokeOfflineCacheResponse:
        """Void every offline verifier issued to the workstation without revoking it. It receives
        a fresh one on its next sync.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/desktop_mfa/devices/{_enc(id)}/revoke_offline_cache",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )


class AsyncIdentityVerification:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def settings(
        self,
    ) -> m.IdentityVerificationSettingsResponse:
        """Whether identity verification is on, and which connector does the checking."""
        return await self._t.request(
            method="GET",
            path="/v1/identity_verification/settings",
        )

    async def update_settings(
        self,
        body: m.IdentityVerificationUpdateSettingsBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.IdentityVerificationUpdateSettingsResponse:
        """Turn identity verification on or off and choose the connector (a Persona, Onfido,
        Veriff or Stripe Identity service connector; its credentials stay in the vault).
        `as_challenge` offers a verified identity as the custom second step of sign-in (the
        custom challenge factor must be enabled).
        """
        return await self._t.request(
            method="PUT",
            path="/v1/identity_verification/settings",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def list(
        self,
        *,
        status: Literal["pending", "approved", "declined", "needs_review"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List checks by status (default `needs_review`, the review queue), newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/identity_verifications",
            query=_q(status=status, limit=limit, starting_after=starting_after),
        )

    async def get(
        self,
        id: str,
    ) -> m.IdentityVerificationGetResponse:
        """Read one check. A pending check is refreshed from the verification service first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/identity_verifications/{_enc(id)}",
        )

    async def decide(
        self,
        id: str,
        body: m.IdentityVerificationDecideBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IdentityVerificationDecideResponse:
        """Decide a check that is waiting for review (or override a pending one) as `approved` or
        `declined`. The outcome is written to the user as `verification.identity`. 409 when
        the check is already approved or declined.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/identity_verifications/{_enc(id)}/decide",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def for_user(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """A user's identity checks, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(id)}/identity_verifications",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def start(
        self,
        id: str,
        body: m.IdentityVerificationStartBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IdentityVerificationStartResponse:
        """Start an identity check for a user and get the verification service's hosted page
        (`url`) to send them to. A check started in the last 30 minutes and still pending is
        returned instead of a new one; at most 5 checks per user per hour. 409 when identity
        verification is not turned on.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(id)}/identity_verifications",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncIga:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.entitlements = _AsyncIgaEntitlements(transport)
        self.requests = _AsyncIgaRequests(transport)
        self.grants = _AsyncIgaGrants(transport)
        self.delegations = _AsyncIgaDelegations(transport)
        self.sod = _AsyncIgaSod(transport)
        self.lifecycle = _AsyncIgaLifecycle(transport)
        self.campaigns = _AsyncIgaCampaigns(transport)


class _AsyncIgaEntitlements:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        kind: Literal[
            "role", "org_membership", "group", "resource_role", "app_assignment", "custom"
        ]
        | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the governed entitlement catalog."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/entitlements",
            query=_q(kind=kind, limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.IgaEntitlementsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaEntitlementsCreateResponse:
        """Add an entitlement to the catalog: a role, organization membership, group, resource
        role, installed-app assignment or custom item, with an owner, a risk level and
        approval rules. The target must exist. 409 for a key already in use.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/entitlements",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.IgaEntitlementsGetResponse:
        """Read one entitlement by id or key."""
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/entitlements/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.IgaEntitlementsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.IgaEntitlementsUpdateResponse:
        """Change an entitlement (its kind cannot change). A change to the approval rules applies
        to requests filed afterwards.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/iga/entitlements/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Remove an entitlement. 409 while it still has active grants."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/entitlements/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncIgaRequests:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        status: Literal["pending", "approved", "denied", "cancelled", "fulfilled", "failed"]
        | None = None,
        user_id: str | None = None,
        requester_user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List access requests, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/requests",
            query=_q(
                status=status,
                user_id=user_id,
                requester_user_id=requester_user_id,
                entitlement=entitlement,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def create(
        self,
        body: m.IgaRequestsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaRequestsCreateResponse:
        """File an access request on behalf of a user. It follows the entitlement's approval
        steps (and any extra step a separation-of-duties rule adds); with no steps it is
        fulfilled at once. A blocking separation-of-duties conflict, a user who already holds
        the access, or a pending duplicate is a 409. `duration_seconds` makes the grant
        time-bound (default and maximum: the entitlement's limit).
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/requests",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.IgaRequestsGetResponse:
        """Read one request with its steps and the approvals recorded so far."""
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/requests/{_enc(id)}",
        )

    async def decide(
        self,
        id: str,
        body: m.IgaRequestsDecideBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaRequestsDecideResponse:
        """Decide the open step. With `approver_user_id` the decision is recorded as that person
        (who must be an approver of the step or hold a delegation); without it the call is an
        administrator override that settles the step. A denial ends the request. 409 when it
        is no longer pending.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/requests/{_enc(id)}/decide",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def cancel(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaRequestsCancelResponse:
        """Cancel a pending request."""
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/requests/{_enc(id)}/cancel",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def inbox(
        self,
        *,
        approver_user_id: str,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The requests waiting on one person's decision, including those delegated to them."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/approvals",
            query=_q(approver_user_id=approver_user_id, limit=limit, starting_after=starting_after),
        )


class _AsyncIgaGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        status: Literal["active", "revoked", "expired"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List grants (what each user was given through governance), newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/grants",
            query=_q(
                user_id=user_id,
                entitlement=entitlement,
                status=status,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def create(
        self,
        body: m.IgaGrantsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaGrantsCreateResponse:
        """Give a user an entitlement now, without a request. `expires_at` makes it time-bound. A
        blocking separation-of-duties rule refuses it; a require-approval rule refuses unless
        `override_reason` is given, which records an accepted violation.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/grants",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(
        self,
        id: str,
        body: m.IgaGrantsRevokeBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaGrantsRevokeResponse:
        """Take the access away and close the grant, including access that existed before
        governance adopted it (an expiry, by contrast, leaves adopted access in place).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/grants/{_enc(id)}/revoke",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncIgaDelegations:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        delegator_user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List approval delegations."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/delegations",
            query=_q(
                delegator_user_id=delegator_user_id, limit=limit, starting_after=starting_after
            ),
        )

    async def create(
        self,
        body: m.IgaDelegationsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaDelegationsCreateResponse:
        """Let another user decide a person's approvals (and reviews) for a period of up to a
        year.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/delegations",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """End an approval delegation."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/delegations/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncIgaSod:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_rules(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List separation-of-duties rules: pairs of entitlements one person should not hold
        together.
        """
        return await self._t.request(
            method="GET",
            path="/v1/iga/sod_rules",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create_rule(
        self,
        body: m.IgaSodCreateRuleBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaSodCreateRuleResponse:
        """Create a rule. `mode` is `block` (refuse) or `require_approval` (an extra approval
        step on a request; `approver` names who, default the owner).
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/sod_rules",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update_rule(
        self,
        id: str,
        body: m.IgaSodUpdateRuleBody,
        *,
        dry_run: bool | None = None,
    ) -> m.IgaSodUpdateRuleResponse:
        """Change a separation-of-duties rule."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/iga/sod_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete_rule(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a rule and its recorded violations."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/sod_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def violations(
        self,
        *,
        status: Literal["open", "accepted", "resolved"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The violations report: users who hold both sides of a rule (found by a scan, or
        accepted at request or assignment time).
        """
        return await self._t.request(
            method="GET",
            path="/v1/iga/sod_violations",
            query=_q(status=status, limit=limit, starting_after=starting_after),
        )

    async def scan(
        self,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaSodScanResponse:
        """Check every rule against what people hold right now: record new conflicts and resolve
        those that cleared.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/sod_violations/scan",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )


class _AsyncIgaLifecycle:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_birthright_rules(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List birthright rules."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/birthright_rules",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create_birthright_rule(
        self,
        body: m.IgaLifecycleCreateBirthrightRuleBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaLifecycleCreateBirthrightRuleResponse:
        """Create a birthright rule: everyone matching `match` (a group, organization and role,
        app role or verified email domain; all conditions must hold) holds the listed
        entitlements. When someone stops matching, the grants the rule gave are revoked unless
        `revoke_on_unmatch` is false.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/birthright_rules",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update_birthright_rule(
        self,
        id: str,
        body: m.IgaLifecycleUpdateBirthrightRuleBody,
        *,
        dry_run: bool | None = None,
    ) -> m.IgaLifecycleUpdateBirthrightRuleResponse:
        """Change a birthright rule."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/iga/birthright_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete_birthright_rule(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a birthright rule (grants it already gave stay until revoked)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/birthright_rules/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def reconcile(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaLifecycleReconcileResponse:
        """Re-evaluate one user's birthright access now (joiner or mover)."""
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/users/{_enc(id)}/reconcile",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def offboard(
        self,
        id: str,
        body: m.IgaLifecycleOffboardBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaLifecycleOffboardResponse:
        """Offboard a leaver: revoke every grant, cancel pending requests and delegations, and
        with `close_account` schedule the account closure through the data-rights path (so
        downstream erasure webhooks and any DSAR orchestrator run as for any deletion).
        `grace_seconds` sets the cancellation window.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/users/{_enc(id)}/offboard",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def settings(
        self,
    ) -> m.IgaLifecycleSettingsResponse:
        """Joiner/mover/leaver settings."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/settings",
        )

    async def update_settings(
        self,
        body: m.IgaLifecycleUpdateSettingsBody,
        *,
        dry_run: bool | None = None,
    ) -> m.IgaLifecycleUpdateSettingsResponse:
        """Turn the joiner/mover/leaver automation on or off and choose what a deactivated
        account triggers: `revoke` (end the grants) or `revoke_and_close` (also schedule the
        closure after `leaver_close_grace_seconds`).
        """
        return await self._t.request(
            method="PUT",
            path="/v1/iga/settings",
            query=_q(dry_run=dry_run),
            body=body,
        )


class _AsyncIgaCampaigns:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        status: Literal["draft", "active", "closed"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List certification (access review) campaigns."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/campaigns",
            query=_q(status=status, limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.IgaCampaignsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaCampaignsCreateResponse:
        """Create a draft campaign scoped to everything, specific entitlements, or the
        entitlements for an app, role, group or organization, with reviewers (the person's
        manager, the entitlement owner, or named users), a due date and reminder days. With
        `auto_revoke` the access reviewers mark for revocation is removed when the campaign
        closes.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/campaigns",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.IgaCampaignsGetResponse:
        """Read a campaign with its progress."""
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/campaigns/{_enc(id)}",
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a draft or closed campaign."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/campaigns/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def launch(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaCampaignsLaunchResponse:
        """Launch a draft campaign: it adopts access that exists in Atlas but was never granted
        through governance, freezes the review list and notifies reviewers.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/campaigns/{_enc(id)}/launch",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def close(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaCampaignsCloseResponse:
        """Close a campaign and apply its revoke decisions (with `auto_revoke`). Items nobody
        reviewed are left in place and reported as pending.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/campaigns/{_enc(id)}/close",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def items(
        self,
        id: str,
        *,
        decision: Literal["pending", "certified", "revoked"] | None = None,
        reviewer_user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The review items of a campaign."""
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/campaigns/{_enc(id)}/items",
            query=_q(
                decision=decision,
                reviewer_user_id=reviewer_user_id,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def progress(
        self,
        id: str,
    ) -> m.IgaCampaignsProgressResponse:
        """Progress: totals, percent complete, whether it is overdue, and per-reviewer counts."""
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/campaigns/{_enc(id)}/progress",
        )

    async def evidence(
        self,
        id: str,
        *,
        format: Literal["json", "csv"] | None = None,
        masked_emails: bool | None = None,
    ) -> m.IgaCampaignsEvidenceResponse:
        """The audit evidence for a campaign as JSON, or CSV with `format=csv`. People are
        identified by id only (an erased user is flagged), free-text comments are never
        included, and `masked_emails=true` adds an address reduced to its first letter and
        domain.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/campaigns/{_enc(id)}/evidence",
            query=_q(format=format, masked_emails=masked_emails),
        )

    async def decide(
        self,
        id: str,
        body: m.IgaCampaignsDecideBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.IgaCampaignsDecideResponse:
        """Certify or revoke one review item. With `reviewer_user_id` the decision is the
        reviewer's (they must be allowed to review it, and may not review their own access);
        without it it is an administrator decision.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/campaign_items/{_enc(id)}/decide",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncScimProvisioningPresets:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List the pre-built outbound provisioning targets (Slack, GitHub, Zoom, Salesforce,
        Atlassian) with their base-URL template and required parameters.
        """
        return await self._t.request(
            method="GET",
            path="/v1/scim_provisioning_presets",
            query=_q(limit=limit, starting_after=starting_after),
        )


class AsyncVault:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.key_provider = _AsyncVaultKeyProvider(transport)

    async def create(
        self,
        body: m.VaultCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.VaultCreateResponse:
        """Store a secret. `key_context` (1–10 string labels) is mandatory and is authenticated
        into the encryption: the value can only be opened with the context it was written
        under. The value (up to 64 KiB) is sealed under a fresh data key wrapped by the
        instance key, or by your own cloud KMS key when one is configured. 409 when the name
        is taken.
        """
        return await self._t.request(
            method="POST",
            path="/v1/vault/objects",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        *,
        name_prefix: str | None = None,
        key_context: str | None = None,
        starting_after: str | None = None,
        limit: int | None = None,
    ) -> CursorPage:
        """List vault objects (metadata only, never values), newest first. Filter by
        `name_prefix` or by `key_context` (a JSON object; objects whose context contains every
        given label).
        """
        return await self._t.request(
            method="GET",
            path="/v1/vault/objects",
            query=_q(
                name_prefix=name_prefix,
                key_context=key_context,
                starting_after=starting_after,
                limit=limit,
            ),
        )

    async def metadata(
        self,
        id: str,
    ) -> m.VaultMetadataResponse:
        """Read a vault object's metadata without its value."""
        return await self._t.request(
            method="GET",
            path=f"/v1/vault/objects/{_enc(id)}/metadata",
        )

    async def versions(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the versions of a vault object (number, which key protects it, when written) —
        never values.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/vault/objects/{_enc(id)}/versions",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def read(
        self,
        id: str,
        *,
        version: int | None = None,
    ) -> m.VaultReadResponse:
        """Read a vault object with its decrypted value (the current version, or `version`).
        Every read is audited. 409 if the version's wrapping key provider is no longer
        configured; 502 VAULT_KMS_ERROR when your KMS refuses.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/vault/objects/{_enc(id)}",
            query=_q(version=version),
        )

    async def update(
        self,
        id: str,
        body: m.VaultUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.VaultUpdateResponse:
        """Append a new version with a new value. Earlier versions stay readable. Pass
        `version_check` (the version you last read) for optimistic concurrency: 409 if another
        update landed since.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/vault/objects/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> DeletedObject:
        """Delete a vault object and every version of it. Irreversible."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/vault/objects/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncVaultKeyProvider:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> m.VaultKeyProviderGetResponse:
        """The customer-managed key that wraps new vault data keys. 404 when none is configured
        (the instance key is used).
        """
        return await self._t.request(
            method="GET",
            path="/v1/vault/key_provider",
        )

    async def set(
        self,
        body: m.VaultKeyProviderSetBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.VaultKeyProviderSetResponse:
        """Bring your own key: wrap new vault data keys with your AWS KMS (`config.region`,
        `config.key_id`; symmetric key), Google Cloud KMS (`config.crypto_key`; symmetric key)
        or Azure Key Vault (`config.vault_url`, `config.key_name`; RSA key with wrap/unwrap)
        key. Atlas proves access with a wrap/unwrap round trip before saving (422 or 502 on
        refusal). Credentials are write-only. Existing versions stay on the key that wrapped
        them; switching provider type is a 409 while versions remain on the old one.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/vault/key_provider",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def remove(
        self,
        *,
        dry_run: bool | None = None,
    ) -> m.VaultKeyProviderRemoveResponse:
        """Stop using your own key for new versions. 409 while any version is still wrapped by
        it.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/vault/key_provider",
            query=_q(dry_run=dry_run),
        )


class AsyncConnections:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.oauth_clients = _AsyncConnectionsOauthClients(transport)
        self.webhooks = _AsyncConnectionsWebhooks(transport)

    async def create(
        self,
        body: m.ConnectionsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsCreateResponse:
        """Define a connection: an owner (an organization or a user) and a third-party API.
        `kind` is oauth (rides a linked provider account; for an organization, the account of
        the member who shared it), api_key or client_credentials (a credential the owner
        enters). `allowed_hosts` lists the only hosts the relay may call. An owner may hold
        several connections of one provider (one per provider account): create one per
        account, then call `POST /v1/connections/{id}/connect`. A connection is never a
        sign-in method.
        """
        return await self._t.request(
            method="POST",
            path="/v1/connections",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list(
        self,
        *,
        owner_type: Literal["organization", "user"] | None = None,
        owner_id: str | None = None,
        provider: str | None = None,
        environment: Literal["production", "sandbox"] | None = None,
        status: Literal["connected", "needs_reauth", "revoked", "error", "not_connected"]
        | None = None,
        starting_after: str | None = None,
        limit: int | None = None,
    ) -> CursorPage:
        """List connections, newest first, with each one's live status. Filter by owner or
        provider.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connections",
            query=_q(
                owner_type=owner_type,
                owner_id=owner_id,
                provider=provider,
                environment=environment,
                status=status,
                starting_after=starting_after,
                limit=limit,
            ),
        )

    async def get(
        self,
        id: str,
    ) -> m.ConnectionsGetResponse:
        """Read one connection with its current status."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.ConnectionsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.ConnectionsUpdateResponse:
        """Rename a connection, change its allowed hosts or settings, transfer it to another
        owner with `owner` (the stored tokens move with it, no reconnect), change
        `environment` or `host_params` (an oauth connection that already holds a token becomes
        needs_reauth, because the token belongs to the old host), or (organization-owned
        oauth) set `shared_by_user_id` to copy that member's linked account into the
        connection.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/connections/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        revoke: bool | None = None,
    ) -> JSON:
        """Delete a connection and its stored credential (204). With `revoke=true` the token is
        first revoked at the provider and the answer is 200 with what the provider said
        (provider_revoked true, false or "unsupported", provider_error, local_cleared); the
        connection is deleted either way.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connections/{_enc(id)}",
            query=_q(dry_run=dry_run, revoke=revoke),
        )

    async def set_credentials(
        self,
        id: str,
        body: m.ConnectionsSetCredentialsBody,
        *,
        dry_run: bool | None = None,
    ) -> m.ConnectionsSetCredentialsResponse:
        """Enter the credential for a non-OAuth connection (api_key, bearer, basic,
        custom_header, hmac_secret, client_credentials, jwt_bearer, oauth1,
        github_app_installation). Write-only: it is sealed in the vault and never returned.
        Replaces the earlier credential as a new vault version; use POST
        .../credentials/rotate to keep the old version valid for an overlap window.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/connections/{_enc(id)}/credentials",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def connect(
        self,
        id: str,
        body: m.ConnectionsConnectBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsConnectResponse:
        """Start the provider authorization for this connection and return the URL to send the
        owner to. The tokens are stored on the connection itself, never on a user: no external
        account is created, no sign-in method is added, no email is proven and no step-up is
        needed. `host_params` fill the provider's host templates for this connection
        (validated against a per-provider allowlist; 400 `host_params.<key>` otherwise).
        Reconnecting the same provider account updates the same connection; a different
        account answers 409 unless `create_if_new` is true. An owner OAuth client (`PUT
        /v1/connections/oauth_clients`) overrides the instance client.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/connect",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(
        self,
        id: str,
        body: dict[str, Any] | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Revoke the stored token at the provider, delete it from the vault and mark the
        connection revoked (connection.revoked is sent once). The response is the connection
        plus what the provider said: provider_revoked is true only when it confirmed,
        "unsupported" when it has no revoke endpoint, false when it refused or was unreachable
        (provider_error says why). The local token is cleared in every case. Connect again to
        use it.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/revoke",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def oauth1_sign(
        self,
        id: str,
        body: m.ConnectionsOauth1SignBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsOauth1SignResponse:
        """Have Atlas sign a request with an oauth1 connection (NetSuite token-based
        authentication: HMAC-SHA256 with the realm; X Ads and other three-legged providers:
        HMAC-SHA1) and return the `Authorization: OAuth ...` header. The consumer and token
        secrets never leave Atlas. The URL must be https on an allowed host; a form-encoded
        body is part of the signature. Needs connections:sign.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/oauth1/sign",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def relay(
        self,
        id: str,
        body: m.ConnectionsRelayBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsRelayResponse:
        """Make a provider API call server-side with this connection's credential, so the
        credential never reaches your code: Atlas injects an api_key (header or query),
        bearer, basic or custom header, signs with an hmac_secret or OAuth 1.0a, or sends a
        minted client_credentials / jwt_bearer / GitHub App installation / admin consent
        token. Only https calls to the connection's allowed_hosts are made, with the verbs in
        allowed_methods (default GET, HEAD, POST). When the connection is not connected, or
        the provider rejects the credential, the answer is 402 CONNECTION_REQUIRED with
        `meta.reason` (not_connected or needs_reauth) and, for a user-owned OAuth connection
        when you pass `redirect_url`, `meta.authorize_url`. The audit log records the method,
        host and status only.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/relay",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def token(
        self,
        id: str,
        *,
        min_ttl_seconds: int | None = None,
        subject: str | None = None,
        refresh: str | None = None,
    ) -> m.ConnectionsTokenResponse:
        """The connection's live token for your backend. An oauth connection's token is refreshed
        first when it is expired or about to be (single-flight across processes, using the
        client that issued it and the connection's host_params). Built for sync workers: the
        response carries an `ETag` and `Cache-Control: private, max-age=<seconds until just
        before expires_at>`, so cache it until then; send `If-None-Match` and an unchanged,
        still-valid token answers 304 with no body and no vault read; `min_ttl_seconds`
        refreshes first when less than that much validity remains. A grant connection
        (client_credentials, jwt_bearer, github_app_installation, admin_consent) has its token
        minted from the credential Atlas holds instead, answered with `Cache-Control:
        no-store` (no ETag); pass `subject` to a jwt_bearer connection to act as that user
        (Google domain-wide delegation). Includes the captured handles (`metadata`,
        `token_response`) and any further named credentials. 402 CONNECTION_REQUIRED with
        `meta.reason` not_connected, needs_reauth, revoked or refresh_failed when there is no
        usable token. When the provider answers 401 to the token, call `POST
        /v1/connections/{id}/token/refresh` instead of re-reading. Rate limit: 6,000 reads per
        minute per secret key and 300 per minute per connection (RateLimit-* headers on every
        response, 429 with Retry-After beyond them). Reads are audited as
        connection.token_read once per connection per minute with the read count (a read that
        refreshed is always audited); the token itself is never logged.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(id)}/token",
            query=_q(min_ttl_seconds=min_ttl_seconds, subject=subject, refresh=refresh),
        )

    async def refresh_token(
        self,
        id: str,
        body: m.ConnectionsRefreshTokenBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsRefreshTokenResponse:
        """Force a refresh after the provider refused the access token (401). Single-flight:
        however many callers saw the same 401, the provider is called once. Send
        `stale_token_hash` (lowercase hex SHA-256 of the access token you were refused with);
        if the stored token is already a different one, a peer has refreshed and the current
        token is returned without calling the provider (`refreshed: false`). Same body, ETag
        and 402 behaviour as the token read; the response is never cached. Counts against the
        same rate limit as the token read.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/token/refresh",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def tokens(
        self,
        body: m.ConnectionsTokensBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """Read the tokens of up to 100 connections in one call (min_ttl_seconds applies to
        each). Each id gets its own result: status ok with the token, or status error with a
        code and reason (not_connected, needs_reauth, revoked, refresh_failed,
        unknown_connection), so one dead connection never fails the batch. The response is
        never cached. Counts once against the token-read rate limit.
        """
        return await self._t.request(
            method="POST",
            path="/v1/connections/tokens/batch",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def import_connections(
        self,
        body: m.ConnectionsImportConnectionsBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsImportConnectionsResponse:
        """Bulk-import existing provider refresh tokens as connections, up to 500 rows, so nobody
        reconnects. Each row: provider, owner, external_id (the provider-side account: how a
        re-import finds the same connection), refresh_token (or access_token), and optionally
        scopes, metadata, environment, host_params, name, allowed_hosts. By default (validate
        true) each refresh token is spent once against the provider with the OAuth client that
        will own the connection, and the tokens the provider issues are stored, so the
        imported copy stops being current on a rotating provider. A failing row creates and
        changes nothing. dry_run checks shapes only and never calls the provider. Idempotent
        on Idempotency-Key. Tokens go straight to the vault and never appear in the answer or
        the audit log.
        """
        return await self._t.request(
            method="POST",
            path="/v1/connections/import",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def export_connections(
        self,
        body: m.ConnectionsExportConnectionsBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsExportConnectionsResponse:
        """Export connections. Without include_secrets: metadata only (provider, owner, account,
        environment, scopes, status), scope connections:export. With include_secrets: needs
        scope connections:export_secrets, the header X-Atlas-Confirm: export-secrets and
        recipient_public_key (a public JWK: RSA of 3072 bits or more, or EC P-256/384/521).
        The tokens come back as one compact JWE sealed to that key that only its holder can
        open; Atlas keeps no plaintext. Pages hold up to 200 connections with secrets (500
        without); follow next_cursor with starting_after. Every export is audited with its
        count, never the secrets. Opened, each connection is a valid import row.
        """
        return await self._t.request(
            method="POST",
            path="/v1/connections/export",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def secret(
        self,
        id: str,
        *,
        version: str | None = None,
    ) -> m.ConnectionsSecretResponse:
        """Read the credential an api_key, bearer, basic, custom_header or hmac_secret connection
        stores, for your backend. Needs the dedicated connections:secret_read scope; every
        read is audited as connection.secret.read with the caller, connection and version
        (never the value) and the response is `Cache-Control: no-store`. `version` is current
        (default), previous (only while a rotation's overlap window is open) or a version
        number. A signing grant's private key is never readable: 409 `not_readable`. There is
        no browser or session route that reads a credential.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(id)}/secret",
            query=_q(version=version),
        )

    async def secret_versions(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The vault versions of a connection's entered credential (numbers and times only, never
        values) and the open rotation window.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(id)}/credentials/versions",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def rotate_credentials(
        self,
        id: str,
        body: m.ConnectionsRotateCredentialsBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsRotateCredentialsResponse:
        """Rotate the credential: the body is the new credential (the same fields as PUT
        credentials). It becomes the current vault version; the replaced one stays valid for
        `overlap_seconds` (default 3600, up to 30 days): the relay falls back to it when the
        provider refuses the new one, and GET secret?version=previous returns it. `expires_at`
        sets the new credential's expiry. The secret never reaches the audit log.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/credentials/rotate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncConnectionsOauthClients:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def set(
        self,
        body: m.ConnectionsOauthClientsSetBody,
        *,
        dry_run: bool | None = None,
    ) -> m.ConnectionsOauthClientsSetResponse:
        """Set an owner's own OAuth client (their registered app) for a provider and environment.
        It overrides the instance client for that owner's connections to connect and to
        refresh. Write-only secret, sealed in the vault. Creates the client or replaces it.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/connections/oauth_clients",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def list(
        self,
        *,
        owner_type: Literal["organization", "user"] | None = None,
        owner_id: str | None = None,
        provider: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List owner OAuth clients. The secret is never returned."""
        return await self._t.request(
            method="GET",
            path="/v1/connections/oauth_clients",
            query=_q(
                owner_type=owner_type,
                owner_id=owner_id,
                provider=provider,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def get(
        self,
        id: str,
    ) -> m.ConnectionsOauthClientsGetResponse:
        """Read one owner OAuth client."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/oauth_clients/{_enc(id)}",
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete an owner OAuth client and its sealed secret. 409 while connections still hold
        tokens it issued (they could no longer refresh).
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connections/oauth_clients/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncConnectionsWebhooks:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def verify(
        self,
        id: str,
        body: m.ConnectionsWebhooksVerifyBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsWebhooksVerifyResponse:
        """Verify a provider webhook signature with the connection's secret (the endpoint's own
        signing secret, else the connection's hmac_secret, else its OAuth client secret).
        Schemes: hubspot_v3 (needs method and url), shopify_hmac, intercom, zoom, slack_v0,
        calendly, stripe, generic_hmac_sha256. Constant-time comparison; a signed timestamp
        must be within the tolerance (5 minutes, Calendly 3); a delivery id or signature
        already seen on the connection answers `replayed`. Send the body exactly as received
        (`raw_body`, or base64 with raw_body_encoding). Zoom and Slack handshakes come back in
        `handshake`. Needs connections:webhook_verify.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/webhooks/verify",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_endpoint(
        self,
        id: str,
        body: m.ConnectionsWebhooksCreateEndpointBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ConnectionsWebhooksCreateEndpointResponse:
        """Create a webhook ingress endpoint on a connection. Point the provider at
        `ingress_url`; Atlas verifies each delivery, refuses forged, stale and replayed ones,
        answers Zoom and Slack handshakes, and forwards only genuine deliveries to
        `forward_url` as Atlas-signed webhooks (atlas-id, atlas-timestamp, atlas-signature
        with `forward_secret`, returned once). Bodies over 1 MiB are refused; the ingress is
        rate limited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(id)}/webhook_endpoints",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_endpoints(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List a connection's webhook ingress endpoints."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(id)}/webhook_endpoints",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def update_endpoint(
        self,
        id: str,
        endpoint_id: str,
        body: m.ConnectionsWebhooksUpdateEndpointBody,
        *,
        dry_run: bool | None = None,
    ) -> m.ConnectionsWebhooksUpdateEndpointResponse:
        """Change an endpoint's forward_url, enabled flag or signing secret."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/connections/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete_endpoint(
        self,
        id: str,
        endpoint_id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a webhook ingress endpoint and its secrets."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connections/{_enc(id)}/webhook_endpoints/{_enc(endpoint_id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncSsf:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.streams = _AsyncSsfStreams(transport)
        self.receivers = _AsyncSsfReceivers(transport)


class _AsyncSsfStreams:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the Shared Signals streams this instance transmits on (push and poll), with their
        delivery method, requested events and status.
        """
        return await self._t.request(
            method="GET",
            path="/v1/ssf/streams",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.SsfStreamsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Create a stream. `delivery_method` is `push` (we POST each signed SET to
        `endpoint_url`, with the optional `authorization_header`) or `poll` (the receiver
        pulls from the returned `poll_endpoint` with the one-time `poll_token`).
        `events_requested` limits the events sent (empty = all supported). SETs are signed
        with the instance signing key.
        """
        return await self._t.request(
            method="POST",
            path="/v1/ssf/streams",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.SsfStreamsGetResponse:
        """Read a stream, including how many events are waiting to be delivered or acknowledged."""
        return await self._t.request(
            method="GET",
            path=f"/v1/ssf/streams/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.SsfStreamsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Change a stream: its events, endpoint, authorization header, description, or status
        (`enabled`, `paused`, `disabled`). A paused stream stops receiving new events.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/ssf/streams/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a stream and its queued events."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/ssf/streams/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def verify(
        self,
        id: str,
        body: m.SsfStreamsVerifyBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Queue an SSF verification event carrying `state`, so a receiver can confirm the stream
        works end to end.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/ssf/streams/{_enc(id)}/verify",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_status(
        self,
        id: str,
    ) -> m.SsfStreamsGetStatusResponse:
        """The stream's delivery status: enabled, paused or disabled (SSF stream status)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/ssf/streams/{_enc(id)}/status",
        )

    async def update_status(
        self,
        id: str,
        body: m.SsfStreamsUpdateStatusBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.SsfStreamsUpdateStatusResponse:
        """Set the stream's delivery status to enabled, paused or disabled. A paused stream
        collects nothing.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/ssf/streams/{_enc(id)}/status",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def events(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The stream's recent events with delivery status, attempts and the last error (the
        dashboard activity view).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/ssf/streams/{_enc(id)}/events",
            query=_q(limit=limit, starting_after=starting_after),
        )


class _AsyncSsfReceivers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List inbound Shared Signals receivers: transmitters whose signed events act on this
        instance's users.
        """
        return await self._t.request(
            method="GET",
            path="/v1/ssf/receivers",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.SsfReceiversCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Register a transmitter. Its SETs are POSTed (`application/secevent+jwt`) to the
        returned `receive_endpoint` and verified against `jwks_uri`, `issuer` and the optional
        `audience`. `actions` maps an event type URI to `revoke_sessions`, `refresh_claims`
        (invalidate minted tokens so the next refresh carries fresh claims, sessions stay),
        `ban` or `ignore`; unmapped events are ignored. The default maps session-revoked,
        credential-change, credential-compromise and device-compliance-change (only when the
        new status is not-compliant) to `revoke_sessions`, token-claims-change to
        `refresh_claims` and account-disabled to `ban`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/ssf/receivers",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update(
        self,
        id: str,
        body: m.SsfReceiversUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Change a receiver: name, JWKS URI, audience, action mapping, or enabled."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/ssf/receivers/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete an inbound SSF receiver; its endpoint stops accepting events."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/ssf/receivers/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncNetworkZones:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List reusable network zones — named sets of CIDRs, countries, ASNs and anonymizer
        classes (tor, datacenter, vpn) that network ACL rules reference by zone_id.
        """
        return await self._t.request(
            method="GET",
            path="/v1/network_zones",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.NetworkZonesCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.NetworkZonesCreateResponse:
        """Create a network zone. `name` is unique per instance; `cidrs`, `countries` (ISO
        alpha-2), `asns` and `anonymizers` are unioned (any match = in the zone). Malformed
        entries are refused.
        """
        return await self._t.request(
            method="POST",
            path="/v1/network_zones",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.NetworkZonesGetResponse:
        """Read one network zone."""
        return await self._t.request(
            method="GET",
            path=f"/v1/network_zones/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.NetworkZonesUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.NetworkZonesUpdateResponse:
        """Update a network zone. Sending any of cidrs/countries/asns/anonymizers replaces that
        list; omitted lists keep their value.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/network_zones/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a network zone. The network ACL rules that reference it are deleted with it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/network_zones/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def check(
        self,
        id: str,
        body: m.NetworkZonesCheckBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.NetworkZonesCheckResponse:
        """What-if: does an IP address fall inside this zone? Returns the resolved country / ASN
        / Tor / datacenter facts alongside the answer. Facts the instance has no
        IP-intelligence data for are null and never match.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/network_zones/{_enc(id)}/check",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAccessPolicies:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List conditional-access policies, in evaluation order."""
        return await self._t.request(
            method="GET",
            path="/v1/access_policies",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.AccessPoliciesCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AccessPoliciesCreateResponse:
        """Create a conditional-access policy. `conditions` (applications, userIds, groups, orgs,
        roles, networkZones {include, exclude}, countries, riskLevels, deviceTrust,
        authMethods, timeWindow) are ANDed; an empty condition matches anything. `grants` are
        allow, block, require_mfa, require_acr, require_policy_acceptance or require_action.
        `stages` limits it to sign_in, authorize and/or token (default all). A matching block
        wins; step-up grants are unioned.
        """
        return await self._t.request(
            method="POST",
            path="/v1/access_policies",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def simulate(
        self,
        body: m.AccessPoliciesSimulateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AccessPoliciesSimulateResponse:
        """What-if: describe a request (stage, ip, application, orgs, roles, country, risk level,
        device trust, auth methods, whether MFA was verified) and see the decision, the
        policies that matched and the unmet step-up requirements. Pass `policy_id` to test one
        policy even if it is disabled.
        """
        return await self._t.request(
            method="POST",
            path="/v1/access_policies/simulate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.AccessPoliciesGetResponse:
        """Read one access policy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/access_policies/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.AccessPoliciesUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.AccessPoliciesUpdateResponse:
        """Update an access policy. Sent fields replace the stored value."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/access_policies/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete an access policy."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/access_policies/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncAbac:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.templates = _AsyncAbacTemplates(transport)
        self.links = _AsyncAbacLinks(transport)
        self.schema = _AsyncAbacSchema(transport)

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the ABAC policies (current version of each)."""
        return await self._t.request(
            method="GET",
            path="/v1/abac_policies",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.AbacCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacCreateResponse:
        """Create an ABAC policy from `source` written in the Cedar-subset policy language
        (permit/forbid with when/unless over principal, action, resource and context
        attributes; `fga.check(...)` consults the policy’s FGA store). Source that does not
        parse is refused with the character position; with an entity schema set it is also
        type-checked and every problem is reported. Optional `tests` are saved with version 1.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac_policies",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.AbacGetResponse:
        """Read one ABAC policy with its current source and tests."""
        return await self._t.request(
            method="GET",
            path=f"/v1/abac_policies/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.AbacUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.AbacUpdateResponse:
        """Update an ABAC policy. Sending `source` appends a new version and makes it current;
        `current_version` (without `source`) rolls back to an earlier version; name,
        description, enabled and fga_store_id change in place.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/abac_policies/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete an ABAC policy and all its versions."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/abac_policies/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def versions(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List every saved version of an ABAC policy, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/abac_policies/{_enc(id)}/versions",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def test(
        self,
        id: str,
        body: m.AbacTestBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacTestResponse:
        """Run test cases against a policy version (default: the current one), or against a draft
        `source` and `tests` sent in the body, without saving anything. Each test is a request
        plus the expected decision; the policy is evaluated on its own, not with the rest of
        the set. The response also carries `coverage`: which rules and `when`/`unless` clauses
        the tests exercised (a clause no test saw both true and false is listed as a gap),
        with line numbers.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/abac_policies/{_enc(id)}/test",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def evaluate(
        self,
        body: m.AbacEvaluateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacEvaluateResponse:
        """Policy decision point: ask whether `principal` may perform `action` on `resource`
        given `context` (and optional extra `entities` for hierarchy). All enabled policies
        are evaluated together with Cedar semantics: a matching forbid wins, otherwise a
        matching permit allows, otherwise deny. Each decision is written to the event feed
        (type authz.decision), so log streams carry it.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac/evaluate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def partial_evaluate(
        self,
        body: m.AbacPartialEvaluateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacPartialEvaluateResponse:
        """Partial evaluation (data filtering): ask what is left of the decision when an entity
        is unknown. With a known principal, an action and a resource TYPE, the response is a
        residual `filter` over the resource attributes (or constant `true`/`false`) that is
        equivalent to evaluating the policies on each resource. `unknowns: ["principal"]`
        answers "who may do this on that resource". Relationship conditions (`fga.check`) are
        resolved to id lists from the policy’s FGA store unless `resolve_relations` is false.
        `output` asks for a ready-made parameterised SQL WHERE (`sql`: dialect and a
        field-to-column map) and/or a Prisma where object (`prisma`: a field map). Policies
        that build sets from unknown attributes cannot be expressed as a filter and are
        refused with a message naming the policy.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac/partial_evaluate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def accessible_resources(
        self,
        body: m.AbacAccessibleResourcesBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """List the resources of a type a principal may perform an action on, paged (`limit`,
        `starting_after`; the response carries `has_more` and `next_cursor`). Candidates are
        the Atlas resources of that type (their metadata are the attributes) or the
        `candidates` you send. The policies are reduced to one filter and applied to every
        candidate; `method` says whether that worked or each candidate was evaluated in full.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac/accessible_resources",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def diff(
        self,
        id: str,
        *,
        from_: int | None = None,
        to: int | None = None,
        semantic: bool | None = None,
        max_requests: int | None = None,
        max_changes: int | None = None,
    ) -> m.AbacDiffResponse:
        """Compare two versions of a policy: a line diff of the source and, unless
        `semantic=false`, the requests whose decision changes. The semantic part enumerates a
        bounded set of requests built from the attributes, groups and actions the policies
        test (from the entity schema when one is set), and lists those that come out
        differently, with newly-allowed and newly-denied counts per action. `exhaustive` says
        whether every request in the space was compared or the space was sampled.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/abac_policies/{_enc(id)}/diff",
            query=_q(
                **{
                    "from": from_,
                    "to": to,
                    "semantic": semantic,
                    "max_requests": max_requests,
                    "max_changes": max_changes,
                }
            ),
        )

    async def diff_sources(
        self,
        body: m.AbacDiffSourcesBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacDiffSourcesResponse:
        """The same comparison for two policy sources you send (a draft against the saved
        version, or two templates), without saving anything.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac/diff",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def authzen_evaluation(
        self,
        body: m.AbacAuthzenEvaluationBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacAuthzenEvaluationResponse:
        """AuthZEN Access Evaluation: `{subject, resource, action, context}` → `{decision:
        boolean}`. Entity types map to PascalCase policy types.
        """
        return await self._t.request(
            method="POST",
            path="/v1/authzen/access/v1/evaluation",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def authzen_evaluations(
        self,
        body: m.AbacAuthzenEvaluationsBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacAuthzenEvaluationsResponse:
        """AuthZEN Access Evaluations (batch, up to 100): shared defaults plus an `evaluations`
        array, with `options.evaluations_semantic` of execute_all (default),
        deny_on_first_deny or permit_on_first_permit.
        """
        return await self._t.request(
            method="POST",
            path="/v1/authzen/access/v1/evaluations",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def authzen_search_subject(
        self,
        body: m.AbacAuthzenSearchSubjectBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacAuthzenSearchSubjectResponse:
        """AuthZEN Subject Search: which subjects of `subject.type` may perform `action` on
        `resource` (give the resource a `type` and `id`). Answers from the same ABAC policies
        as an evaluation, reduced once by partial evaluation and applied to the candidates
        Atlas knows: your users (type `user`, their public metadata as attributes) and the
        users in the FGA stores the policies consult. `page.limit` and `page.token` page the
        result; the response carries `page.next_token` (empty on the last page), `count` and
        `total`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/authzen/access/v1/search/subject",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def authzen_search_resource(
        self,
        body: m.AbacAuthzenSearchResourceBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacAuthzenSearchResourceResponse:
        """AuthZEN Resource Search: which resources of `resource.type` the `subject` may perform
        `action` on. Candidates are your synced Atlas resources of that type (their metadata
        are the attributes) and the objects of that type in the FGA stores the policies
        consult. Paged with `page.limit` and `page.token`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/authzen/access/v1/search/resource",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def authzen_search_action(
        self,
        body: m.AbacAuthzenSearchActionBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacAuthzenSearchActionResponse:
        """AuthZEN Action Search: which actions the `subject` may perform on the `resource`. The
        actions considered are the ones the policies name (and the entity schema declares),
        each evaluated in full; the result lists the permitted action names.
        """
        return await self._t.request(
            method="POST",
            path="/v1/authzen/access/v1/search/action",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncAbacTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the ABAC policy templates, with their slots and how many links each has."""
        return await self._t.request(
            method="GET",
            path="/v1/abac_templates",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.AbacTemplatesCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacTemplatesCreateResponse:
        """Create a policy template: policy source whose scope uses the slots `?principal` and/or
        `?resource` (`principal == ?principal`, `resource in ?resource`, `resource is Doc in
        ?resource`). Slots are filled by a link. With an entity schema set, the template is
        type-checked on save (a slot stands for any entity type).
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac_templates",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.AbacTemplatesGetResponse:
        """Read one policy template."""
        return await self._t.request(
            method="GET",
            path=f"/v1/abac_templates/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.AbacTemplatesUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.AbacTemplatesUpdateResponse:
        """Change a template. A new `source` bumps `version` and takes effect on every link at
        once (`links_updated` counts them). It is refused, with one error per problem and the
        link named, if any link could no longer be filled in or would fail the entity schema.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/abac_templates/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
        force: bool | None = None,
    ) -> JSON:
        """Delete a template. A template with links is refused with 409 unless `force=true`,
        which deletes the links too.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/abac_templates/{_enc(id)}",
            query=_q(dry_run=dry_run, force=force),
        )


class _AsyncAbacLinks:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        template_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List template links: a template with its slots filled by entities. Each link’s
        `source` is what the policy engine evaluates.
        """
        return await self._t.request(
            method="GET",
            path="/v1/abac_policy_links",
            query=_q(template_id=template_id, limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.AbacLinksCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacLinksCreateResponse:
        """Link a template to entities. Every slot the template uses needs its entity
        (`principal` for `?principal`, `resource` for `?resource`); one it does not use is
        refused. The link is evaluated together with the other enabled policies, always from
        the template’s current source, and is type-checked against the entity schema when one
        is set.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac_policy_links",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.AbacLinksGetResponse:
        """Read one template link."""
        return await self._t.request(
            method="GET",
            path=f"/v1/abac_policy_links/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.AbacLinksUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.AbacLinksUpdateResponse:
        """Rename, enable or disable a link, or point its slots at other entities."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/abac_policy_links/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a link; the template stays."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/abac_policy_links/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncAbacSchema:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> m.AbacSchemaGetResponse:
        """The instance’s ABAC entity schema (`schema` is null and `version` 0 when none is set)."""
        return await self._t.request(
            method="GET",
            path="/v1/abac_schema",
        )

    async def set(
        self,
        body: m.AbacSchemaSetBody,
        *,
        dry_run: bool | None = None,
    ) -> m.AbacSchemaSetResponse:
        """Set the ABAC entity schema: `entity_types` (attributes with `boolean`, `long`,
        `string`, `set`, `entity` and `record` types, `required: false` for optional ones, and
        `member_of`) and `actions` (`applies_to` principal and resource types and a
        `context`). Every problem is reported with its path. Once set, policies and templates
        are type-checked when saved: unknown attributes, optional attributes read without a
        `has` guard, wrong operand types, unknown entity types and actions, and actions that
        do not apply to the policy’s principal and resource types. The response lists the
        errors the schema would give the policies and links already stored.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/abac_schema",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Remove the entity schema; policies are no longer type-checked."""
        return await self._t.request(
            method="DELETE",
            path="/v1/abac_schema",
            query=_q(dry_run=dry_run),
        )

    async def validate(
        self,
        body: m.AbacSchemaValidateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.AbacSchemaValidateResponse:
        """Type-check policy (or, with `template: true`, template) source against the saved
        schema, or one sent as `schema`, without saving anything. Returns every issue with its
        policy number, clause, character offset, line and column. A syntax error is reported
        as an issue too.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac_schema/validate",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncResources:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.types = _AsyncResourcesTypes(transport)
        self.assignments = _AsyncResourcesAssignments(transport)

    async def list(
        self,
        *,
        type: str | None = None,
        parent_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List resources, optionally filtered by `type` or `parent_id`."""
        return await self._t.request(
            method="GET",
            path="/v1/resources",
            query=_q(type=type, parent_id=parent_id, limit=limit, starting_after=starting_after),
        )

    async def upsert(
        self,
        body: m.ResourcesUpsertBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.ResourcesUpsertResponse:
        """Create or update one resource by `type` + `external_id` (your own id for it). `parent`
        is `{id}` or `{type, external_id}` of an existing resource, or null; it must match the
        type’s `parent_type`.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/resources",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def sync(
        self,
        body: m.ResourcesSyncBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """Discovery sync: upsert up to 500 resources in order (list parents before children).
        Idempotent; call it whenever your app creates or moves resources.
        """
        return await self._t.request(
            method="POST",
            path="/v1/resources/sync",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.ResourcesGetResponse:
        """Read one resource, with its type and parent."""
        return await self._t.request(
            method="GET",
            path=f"/v1/resources/{_enc(id)}",
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a resource and its role assignments. Its children are detached to the root."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/resources/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def check(
        self,
        body: m.ResourcesCheckBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ResourcesCheckResponse:
        """Does `subject` hold `permission` on `resource`? A user subject also holds the roles of
        the organizations they belong to, plus any `groups` ids you pass. The response lists
        the grants that allow it.
        """
        return await self._t.request(
            method="POST",
            path="/v1/resource_checks",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def check_batch(
        self,
        body: m.ResourcesCheckBatchBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """Up to 100 resource checks in one call."""
        return await self._t.request(
            method="POST",
            path="/v1/resource_checks/batch",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def accessible(
        self,
        body: m.ResourcesAccessibleBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """List the resources of an optional `type` on which `subject` holds `permission`, paged
        with `limit` and `starting_after` (the response carries `has_more` and `next_cursor`).
        """
        return await self._t.request(
            method="POST",
            path="/v1/resource_checks/list",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class _AsyncResourcesTypes:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the resource types (roles, permissions, parent type)."""
        return await self._t.request(
            method="GET",
            path="/v1/resource_types",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.ResourcesTypesCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ResourcesTypesCreateResponse:
        """Define a resource type: a `key`, its `roles` (each a set of permissions, optionally
        `includes` other roles), an optional `parent_type` resources nest under, and `inherit`
        (default true) controlling whether assignments on a parent flow down.
        """
        return await self._t.request(
            method="POST",
            path="/v1/resource_types",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        key: str,
    ) -> m.ResourcesTypesGetResponse:
        """Read one resource type."""
        return await self._t.request(
            method="GET",
            path=f"/v1/resource_types/{_enc(key)}",
        )

    async def update(
        self,
        key: str,
        body: m.ResourcesTypesUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.ResourcesTypesUpdateResponse:
        """Change a resource type’s name, roles, parent type or inheritance."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/resource_types/{_enc(key)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        key: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a resource type together with its resources and their role assignments."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/resource_types/{_enc(key)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncResourcesAssignments:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        resource_id: str | None = None,
        subject_type: Literal["user", "group", "organization"] | None = None,
        subject_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List role assignments, filtered by `resource_id`, `subject_type` or `subject_id`."""
        return await self._t.request(
            method="GET",
            path="/v1/resource_role_assignments",
            query=_q(
                resource_id=resource_id,
                subject_type=subject_type,
                subject_id=subject_id,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def assign(
        self,
        body: m.ResourcesAssignmentsAssignBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ResourcesAssignmentsAssignResponse:
        """Assign a `role` on a `resource` to a `subject` (`{type: user|group|org, id}`).
        `inherit` (default true) also applies it to the resource’s descendants. Re-assigning
        the same role updates `inherit`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/resource_role_assignments",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Revoke a role assignment."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/resource_role_assignments/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncOrgRoleGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        grantor_org_id: str | None = None,
        grantee_org_id: str | None = None,
        status: Literal["active"] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List cross-organization role grants, filtered by grantor_org_id, grantee_org_id or
        status=active.
        """
        return await self._t.request(
            method="GET",
            path="/v1/org_role_grants",
            query=_q(
                grantor_org_id=grantor_org_id,
                grantee_org_id=grantee_org_id,
                status=status,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def create(
        self,
        body: m.OrgRoleGrantsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.OrgRoleGrantsCreateResponse:
        """Let a grantee organization hand out a bounded set of the grantor organization’s roles
        (role_keys) to its own members. One active grant per pair.
        """
        return await self._t.request(
            method="POST",
            path="/v1/org_role_grants",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.OrgRoleGrantsGetResponse:
        """Fetch one cross-organization role grant."""
        return await self._t.request(
            method="GET",
            path=f"/v1/org_role_grants/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.OrgRoleGrantsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.OrgRoleGrantsUpdateResponse:
        """Replace the granted role_keys. Delegations of roles no longer granted are removed."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/org_role_grants/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def revoke(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> m.OrgRoleGrantsRevokeResponse:
        """Revoke a grant. Every delegation under it stops taking effect immediately."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/org_role_grants/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def list_delegations(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List the members holding roles under a grant."""
        return await self._t.request(
            method="GET",
            path=f"/v1/org_role_grants/{_enc(id)}/delegations",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def delegate(
        self,
        id: str,
        body: m.OrgRoleGrantsDelegateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.OrgRoleGrantsDelegateResponse:
        """Delegate one granted role_key to a member (user_id) of the grantee organization."""
        return await self._t.request(
            method="POST",
            path=f"/v1/org_role_grants/{_enc(id)}/delegations",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def undelegate(
        self,
        id: str,
        delegation_id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Remove a delegation of a granted role."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/org_role_grants/{_enc(id)}/delegations/{_enc(delegation_id)}",
            query=_q(dry_run=dry_run),
        )

    async def effective(
        self,
        *,
        user_id: str,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The roles and permissions a user (user_id) holds in a grantor organization
        (organization_id, optional) through active delegations.
        """
        return await self._t.request(
            method="GET",
            path="/v1/org_role_grants/effective",
            query=_q(
                user_id=user_id,
                organization_id=organization_id,
                limit=limit,
                starting_after=starting_after,
            ),
        )


class AsyncDevices:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        user_id: str | None = None,
        source: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """List registered devices, filtered by user_id or source."""
        return await self._t.request(
            method="GET",
            path="/v1/devices",
            query=_q(user_id=user_id, source=source, limit=limit, starting_after=starting_after),
        )

    async def report(
        self,
        body: m.DevicesReportBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.DevicesReportResponse:
        """Create or refresh one device by (source, external_id), reporting managed/compliant
        posture. Tie it to a user with user_id or a verified user_email. Access policies read
        the result through the deviceTrust condition: trusted = a managed, compliant device
        reported within 30 days.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/devices",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def get(
        self,
        id: str,
    ) -> m.DevicesGetResponse:
        """Fetch a device and its latest posture."""
        return await self._t.request(
            method="GET",
            path=f"/v1/devices/{_enc(id)}",
        )

    async def remove(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Remove a device from the registry."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/devices/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )

    async def ingest_posture(
        self,
        body: m.DevicesIngestPostureBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> CursorPage:
        """Posture ingestion for your MDM/EDR or its relay: up to 500 device reports per call,
        same fields as PUT /v1/devices.
        """
        return await self._t.request(
            method="POST",
            path="/v1/device_posture",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAuthzDecisions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.settings = _AsyncAuthzDecisionsSettings(transport)

    async def list(
        self,
        *,
        source: Literal["abac", "authzen", "fga", "access_policy", "mcp_gateway"] | None = None,
        decision: Literal["allow", "deny"] | None = None,
        principal: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        policy_revision: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """Query the authorization decision log, newest first: ABAC, AuthZEN, FGA-check and
        access-policy decisions with their redacted input, result, the policy revision in
        force and latency. Only decisions that passed sampling are stored.
        """
        return await self._t.request(
            method="GET",
            path="/v1/authz_decisions",
            query=_q(
                source=source,
                decision=decision,
                principal=principal,
                action=action,
                resource=resource,
                policy_revision=policy_revision,
                since=since,
                until=until,
                limit=limit,
                starting_after=starting_after,
            ),
        )

    async def stats(
        self,
        *,
        since: str | None = None,
        until: str | None = None,
    ) -> m.AuthzDecisionsStatsResponse:
        """Decision counts per engine and outcome over a window (the last 24 hours by default),
        with a sampling-corrected estimate of the true volume and latency percentiles of the
        recorded decisions.
        """
        return await self._t.request(
            method="GET",
            path="/v1/authz_decisions/stats",
            query=_q(since=since, until=until),
        )

    async def get(
        self,
        id: str,
    ) -> m.AuthzDecisionsGetResponse:
        """Read one logged decision."""
        return await self._t.request(
            method="GET",
            path=f"/v1/authz_decisions/{_enc(id)}",
        )


class _AsyncAuthzDecisionsSettings:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> m.AuthzDecisionsSettingsGetResponse:
        """How authorization decisions are captured: on or off, sampling per outcome, how much of
        each request is kept, redaction paths, event shipping and retention.
        """
        return await self._t.request(
            method="GET",
            path="/v1/authz_decision_settings",
        )

    async def update(
        self,
        body: m.AuthzDecisionsSettingsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.AuthzDecisionsSettingsUpdateResponse:
        """Change how decisions are captured. Fields you omit keep their value. Capture is off by
        default; `input_mode` defaults to `ids` (identifiers only) so nothing personal is
        stored until you ask for it. With `ship_to_events` each recorded decision is also an
        `authz.decision` event for your log streams and webhooks.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/authz_decision_settings",
            query=_q(dry_run=dry_run),
            body=body,
        )


class AsyncPolicyBundles:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def current(
        self,
    ) -> m.PolicyBundlesCurrentResponse:
        """The bundle revision the instance policy is at right now. Compare it with a deployed
        bundle’s revision to detect drift.
        """
        return await self._t.request(
            method="GET",
            path="/v1/policy_bundles/current",
        )

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List the signed policy bundles exported or imported on this instance, newest first
        (without the archives).
        """
        return await self._t.request(
            method="GET",
            path="/v1/policy_bundles",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def export(
        self,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PolicyBundlesExportResponse:
        """Export the instance policy — every ABAC policy (current version), the ABAC entity
        schema, templates and template links, and every FGA store’s latest authorization model
        — as a versioned tar.gz with a manifest of file digests, signed with the instance
        signing key (detached JWS). The same policy always has the same revision.
        """
        return await self._t.request(
            method="POST",
            path="/v1/policy_bundles",
            query=_q(dry_run=dry_run),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        revision: str,
    ) -> m.PolicyBundlesGetResponse:
        """Read a stored bundle by revision, with the base64 archive and its signature."""
        return await self._t.request(
            method="GET",
            path=f"/v1/policy_bundles/{_enc(revision)}",
        )

    async def archive(
        self,
        revision: str,
    ) -> bytes:
        """Download a stored bundle as the raw tar.gz (`application/gzip`). The detached
        signature is in the `Atlas-Bundle-Signature` header, with `Atlas-Bundle-Revision` and
        `Atlas-Bundle-Key-Id`.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/policy_bundles/{_enc(revision)}/archive",
            raw="bytes",
        )

    async def verify(
        self,
        body: m.PolicyBundlesVerifyBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PolicyBundlesVerifyResponse:
        """Check a bundle without importing it: the detached signature against this instance's
        signing keys (plus any `trusted_jwks` you supply) and the archive's integrity. The SDK
        can do the same check offline.
        """
        return await self._t.request(
            method="POST",
            path="/v1/policy_bundles/verify",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def import_(
        self,
        body: m.PolicyBundlesImportBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.PolicyBundlesImportResponse:
        """Import a signed bundle. The signature and the archive integrity must both check out or
        nothing is touched (422). With `dry_run: true` it returns the diff of what would
        change and applies nothing (needs only policy_bundles:read). Otherwise it applies
        everything in one transaction: stores and models first, then the ABAC schema,
        templates, links and policies; a changed policy appends a version. `prune` also
        deletes ABAC policies, templates and links the bundle does not name (and the schema
        when it has none); FGA stores are never deleted.
        """
        return await self._t.request(
            method="POST",
            path="/v1/policy_bundles/import",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncProxyApps:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """List the identity-aware proxy apps — hostnames protected by the forward-auth endpoint,
        with their path rules.
        """
        return await self._t.request(
            method="GET",
            path="/v1/proxy_apps",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        body: m.ProxyAppsCreateBody | None = None,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.ProxyAppsCreateResponse:
        """Create a proxy app: a hostname, optional upstream URL, ordered path/method rules
        requiring a role, permission or entitlement, public paths, and header/token injection.
        The hostname is unique across the deployment.
        """
        return await self._t.request(
            method="POST",
            path="/v1/proxy_apps",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> m.ProxyAppsGetResponse:
        """Read one identity-aware proxy app."""
        return await self._t.request(
            method="GET",
            path=f"/v1/proxy_apps/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.ProxyAppsUpdateBody | None = None,
        *,
        dry_run: bool | None = None,
    ) -> m.ProxyAppsUpdateResponse:
        """Update a proxy app. Omitted fields keep their value."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/proxy_apps/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a proxy app. Its hostname stops resolving at the forward-auth endpoint."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/proxy_apps/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class AsyncMcpGateways:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.budgets = _AsyncMcpGatewaysBudgets(transport)

    async def list(
        self,
    ) -> JSON:
        """List the MCP tool gateways of the instance."""
        return await self._t.request(
            method="GET",
            path="/v1/mcp_gateways",
        )

    async def create(
        self,
        body: m.McpGatewaysCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Create an MCP gateway: one URL (`url` in the response) that fronts your MCP server.
        `tools` maps a tool name to its policy (allow, scopes the agent token must hold,
        argument conditions, approval, response masking); `default_policy` (deny by default)
        decides tools not listed. upstream_authorization is write-only and sent to the
        upstream as its Authorization header.
        """
        return await self._t.request(
            method="POST",
            path="/v1/mcp_gateways",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
    ) -> JSON:
        """Read one MCP gateway."""
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(id)}",
        )

    async def update(
        self,
        id: str,
        body: m.McpGatewaysUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Update an MCP gateway. Omitted fields keep their value; `tools` is replaced as a
        whole. `abac` turns on authorization of every tool call through the ABAC policy
        engine.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/mcp_gateways/{_enc(id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete an MCP gateway."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(id)}",
            query=_q(dry_run=dry_run),
        )


class _AsyncMcpGatewaysBudgets:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The cross-call budgets of a gateway, newest first (at most 50): ceilings on how many
        calls, how much cost, or how many calls per window one agent or one session may make.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(id)}/budgets",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def create(
        self,
        id: str,
        body: m.McpGatewaysBudgetsCreateBody,
        *,
        dry_run: bool | None = None,
        idempotency_key: str | None = None,
    ) -> m.McpGatewaysBudgetsCreateResponse:
        """Add a budget. `metric` is `calls` (a count), `cost` (the sum of each call's cost:
        `cost_per_call`, or the number found at `cost_arg` in the call arguments, such as an
        amount) or `rate` (calls per `window_seconds`, required). `limit` is the ceiling.
        `window_seconds` makes the counter reset in fixed windows; without it a counter never
        resets (a per-session one ends with the session). `scope` is `agent` (each agent
        counts separately) or `session` (each session of each agent; the client must echo the
        `Mcp-Session-Id` from initialize). `agent_id` limits it to one agent and `tool` to one
        tool. A call is charged against every budget it touches at once, or against none; only
        a call that is allowed and about to run is charged.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(id)}/budgets",
            query=_q(dry_run=dry_run),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        id: str,
        budget_id: str,
    ) -> m.McpGatewaysBudgetsGetResponse:
        """Read one budget of an MCP gateway."""
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(id)}/budgets/{_enc(budget_id)}",
        )

    async def update(
        self,
        id: str,
        budget_id: str,
        body: m.McpGatewaysBudgetsUpdateBody,
        *,
        dry_run: bool | None = None,
    ) -> m.McpGatewaysBudgetsUpdateResponse:
        """Change a budget. Omitted fields keep their value. Raising the limit takes effect on
        the next call; counters are kept.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/mcp_gateways/{_enc(id)}/budgets/{_enc(budget_id)}",
            query=_q(dry_run=dry_run),
            body=body,
        )

    async def delete(
        self,
        id: str,
        budget_id: str,
        *,
        dry_run: bool | None = None,
    ) -> JSON:
        """Delete a budget and stop counting against it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(id)}/budgets/{_enc(budget_id)}",
            query=_q(dry_run=dry_run),
        )

    async def usage(
        self,
        id: str,
        budget_id: str,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> m.McpGatewaysBudgetsUsageResponse:
        """What one agent has used of a budget right now, with the room left and when the window
        resets. A per-session budget also needs the `session_id` (the Mcp-Session-Id of that
        session).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(id)}/budgets/{_enc(budget_id)}/usage",
            query=_q(agent_id=agent_id, session_id=session_id),
        )
