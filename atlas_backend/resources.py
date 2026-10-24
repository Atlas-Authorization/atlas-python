"""Synchronous resource namespaces — the method↔endpoint map for the BAPI.

Each class wraps the shared :class:`_SyncTransport` and turns a call into a
single request naming a method, a path, and its shapes. The surface mirrors the
official TypeScript SDK (``@atlas/backend``) namespace-for-namespace.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from typing import Any, Literal
from urllib.parse import quote, urlencode

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


def _dry(dry_run: bool) -> dict[str, Any] | None:
    """The ``dry_run=true`` query for a preview call (``None`` for a real one)."""
    return {"dry_run": True} if dry_run else None


def _meta(metadata: dict[str, Any] | None, **rest: Any) -> dict[str, Any]:
    """Flatten a ``metadata`` filter into ``metadata[key]=value`` query pairs."""
    out = _q(**rest)
    for k, v in (metadata or {}).items():
        out[f"metadata[{k}]"] = v
    return out


def _enc(value: str) -> str:
    """Percent-encode one path segment."""
    return quote(value, safe="")


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


#: Bytes per uploaded Better Auth bundle part (the API takes at most 10 MiB per part).
BETTER_AUTH_IMPORT_PART_BYTES = 8 * 1024 * 1024

#: Statuses an import stays in while Atlas is working on it (``wait_for`` polls through them).
BETTER_AUTH_IMPORT_IN_FLIGHT = ("analyzing", "queued", "applying")


def split_bundle_parts(
    bundle: str | bytes, max_bytes: int = BETTER_AUTH_IMPORT_PART_BYTES
) -> list[str]:
    """Split a sealed Better Auth bundle into upload parts of at most ``max_bytes``
    (UTF-8), each ending on a line boundary. Empty lines are dropped; a single line
    longer than ``max_bytes`` becomes a part of its own (the API refuses parts over
    10 MiB, so keep ``max_bytes`` at or under the default)."""
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive.")
    text = bundle.decode("utf-8") if isinstance(bundle, bytes) else bundle
    parts: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if not line:
            continue
        n = len(line.encode("utf-8")) + 1
        if size > 0 and size + n > max_bytes:
            parts.append("\n".join(current) + "\n")
            current = []
            size = 0
        current.append(line)
        size += n
    if current:
        parts.append("\n".join(current) + "\n")
    return parts


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

    def list(
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
    ) -> CursorPage:
        """List and search users. Every filter combines with AND. Page by cursor
        (``starting_after``) or, with ``offset``, by offset. ``query`` searches email,
        username, names, phone and ids; ``created_after`` / ``created_before`` are epoch
        ms, as are ``updated_after`` / ``updated_before`` (sync users changed since a
        checkpoint, with ``order_by="updated_at"``); ``include_total_count`` adds
        ``total_count`` to the page.
        """

        def _b(v: bool | None) -> str | None:
            return None if v is None else ("true" if v else "false")

        return self._t.request(
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
            ),
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

    def set_external_id(self, user_id: str, external_id: str | None) -> m.User:
        """Set (or clear with ``None``) the user's ``external_id``. With referral
        attribution on, Atlas forwards the change to the referral platform as an alias
        (old id, or the Atlas user id, to the new one), so later events under your id
        still match.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/users/{user_id}",
            body={"external_id": external_id},
        )

    def replace_metadata(self, user_id: str, body: m.ReplaceUserMetadataBody) -> m.User:
        return self._t.request(method="PUT", path=f"/v1/users/{user_id}/metadata", body=body)

    def ban(
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
        return self._t.request(
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

    def flag_referral(
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
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/referral/flag",
            body=_q(reason=reason),
            idempotency_key=idempotency_key,
        )

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

    def resend(self, org_id: str, invitation_id: str) -> JSON:
        """Resend a pending invitation: same id and role, a fresh expiry."""
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/invitations/{invitation_id}/resend",
        )


class _OrgTeams:
    """Teams inside an organization (``/v1/organizations/{id}/teams``)."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str, *, user_id: str | None = None) -> CursorPage:
        """The organization's teams; ``user_id`` narrows to the teams that user is in."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/teams",
            query=_q(user_id=user_id),
        )

    def create(self, org_id: str, body: m.TeamBody) -> m.Team:
        return self._t.request(method="POST", path=f"/v1/organizations/{org_id}/teams", body=body)

    def get(self, org_id: str, team_id: str) -> m.Team:
        return self._t.request(method="GET", path=f"/v1/organizations/{org_id}/teams/{team_id}")

    def update(self, org_id: str, team_id: str, body: m.TeamBody) -> m.Team:
        return self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/teams/{team_id}", body=body
        )

    def delete(self, org_id: str, team_id: str) -> DeletedObject:
        return self._t.request(method="DELETE", path=f"/v1/organizations/{org_id}/teams/{team_id}")

    def list_members(self, org_id: str, team_id: str) -> CursorPage:
        return self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/teams/{team_id}/members"
        )

    def add_member(self, org_id: str, team_id: str, user_id: str) -> m.TeamMember:
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{org_id}/teams/{team_id}/members",
            body={"user_id": user_id},
        )

    def remove_member(self, org_id: str, team_id: str, user_id: str) -> m.TeamMember:
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/teams/{team_id}/members/{user_id}",
        )


class _OrgRoles:
    """The roles an organization can assign: the instance roles plus its own custom
    roles (``organization_id`` set)."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str, *, own: bool | None = None) -> CursorPage:
        """``own=True`` lists only the organization's own custom roles."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{org_id}/roles",
            query=_q(own="true" if own else None),
        )

    def create(self, org_id: str, body: m.CreateOrgRoleBody) -> m.OrgRole:
        return self._t.request(method="POST", path=f"/v1/organizations/{org_id}/roles", body=body)

    def update(self, org_id: str, role_id: str, body: m.UpdateOrgRoleBody) -> m.OrgRole:
        return self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/roles/{role_id}", body=body
        )

    def delete(self, org_id: str, role_id: str, *, reassign_to: str | None = None) -> JSON:
        """Delete one of the organization's own roles; ``reassign_to`` (a role key) moves
        members and pending invitations first (409 ``ROLE_IN_USE`` without it)."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{org_id}/roles/{role_id}",
            query=_q(reassign_to=reassign_to),
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
        self.teams = _OrgTeams(transport)
        self.roles = _OrgRoles(transport)

    def get_by_slug(self, slug: str) -> m.Organization:
        """Fetch an organization by slug (case-insensitive)."""
        return self._t.request(method="GET", path=f"/v1/organizations/by_slug/{slug}")

    def check_slug(self, slug: str) -> m.SlugCheck:
        """Whether a slug is valid and free, for a create-organization form."""
        return self._t.request(
            method="GET", path="/v1/organizations/check_slug", query={"slug": slug}
        )

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

    def get_token(
        self, session_id: str, for_: str, *, audience_hint: str | None = None
    ) -> m.SessionToken:
        """``getToken({for})`` on the server: mint an integration token for a session, for a
        product that trusts Atlas sessions (e.g. ``for_="referalli"``)."""
        return self._t.request(
            method="POST",
            path=f"/v1/sessions/{_enc(session_id)}/integration_tokens/{_enc(for_)}",
            body={"audience_hint": audience_hint} if audience_hint else None,
        )

    def set_custom_data(self, session_id: str, custom_data: dict[str, Any] | None) -> m.Session:
        """Replace the session's custom data (``None`` clears it). At most 2 KB; only an
        active session can be changed. Not for secrets: the signed-in user can read it.
        Sends the ``session.updated`` webhook."""
        return self._t.request(
            method="PUT",
            path=f"/v1/sessions/{session_id}/custom_data",
            body={"custom_data": custom_data},
        )

    def update_custom_data(self, session_id: str, patch: dict[str, Any]) -> m.Session:
        """Merge keys into the session's custom data; a key set to ``None`` is removed."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/sessions/{session_id}/custom_data",
            body={"custom_data": patch},
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

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        include_deprecated: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> JSON:
        """List endpoints (cursor-paginated). ``include_deprecated`` adds the superseded
        event spellings to the catalog; ``metadata`` filters on ``metadata[key]=value``."""
        return self._t.request(
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

    def get(self, endpoint_id: str) -> m.WebhookEndpoint:
        """Read one endpoint, with its health fields (``failing_since``,
        ``last_failing_since``, ``consecutive_failures``, ...)."""
        return self._t.request(method="GET", path=f"/v1/webhook_endpoints/{_enc(endpoint_id)}")

    def create(
        self,
        body: m.CreateWebhookEndpointBody,
        *,
        idempotency_key: str | None = None,
        dry_run: bool = False,
    ) -> JSON:
        return self._t.request(
            method="POST",
            path="/v1/webhook_endpoints",
            body=body,
            idempotency_key=idempotency_key,
            query=_dry(dry_run),
        )

    def put_by_url(self, body: dict[str, Any], *, idempotency_key: str | None = None) -> JSON:
        """Create the endpoint for ``body["url"]`` or update it when one exists (idempotent
        provisioning)."""
        return self._t.request(
            method="PUT",
            path="/v1/webhook_endpoints/by_url",
            body=body,
            idempotency_key=idempotency_key,
        )

    def redeliver_window(self, endpoint_id: str, body: dict[str, Any] | None = None) -> JSON:
        """Redeliver every delivery in a window. ``body``: ``since`` (epoch ms, or
        ``"failing_since"`` for the start of the endpoint's last failure streak), ``until``,
        ``status``, ``event_type``."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(endpoint_id)}/redeliver",
            body=body if body is not None else {},
        )

    def replay(self, endpoint_id: str, body: dict[str, Any] | None = None) -> JSON:
        """Replay the events an endpoint missed since ``body["since"]`` (epoch ms, or
        ``"failing_since"`` to replay everything since it started failing)."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(endpoint_id)}/replay",
            body=body if body is not None else {},
        )

    def delete(self, endpoint_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/webhook_endpoints/{endpoint_id}")

    def list_deliveries(
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
        return self._t.request(
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

    def rotate_secret(
        self, endpoint_id: str, body: m.RotateWebhookSecretBody | None = None
    ) -> m.WebhookSecretRotation:
        """Rotate the endpoint signing secret; the new one is revealed exactly once. By
        default the old secret stops signing at once. With ``overlap_seconds`` (at most
        604800) every delivery is signed with both, so a verifier holding either passes.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/rotate_secret",
            body=body,
        )

    def test(self, endpoint_id: str, *, wait: int | None = None) -> m.WebhookDeliveryAttempt:
        """Send a synthetic webhook.test event to this endpoint only. With ``wait`` (seconds)
        the call holds until the delivery finishes and returns its outcome."""
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{endpoint_id}/test",
            query=_q(wait=wait),
        )


class Webhooks:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.endpoints = _WebhookEndpoints(transport)

    def deliveries(
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
        return self._t.request(
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

    def egress_ips(self) -> JSON:
        """The IP addresses Atlas delivers webhooks from (allow-list them)."""
        return self._t.request(method="GET", path="/v1/meta/egress_ips")


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

    def rotate_secret(
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
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{client_id}/rotate_secret",
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_backchannel_deliveries(
        self, client_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> m.BackchannelLogoutDeliveryList:
        """The client's back-channel logout delivery log, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{client_id}/backchannel_deliveries",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def test_backchannel_logout(self, client_id: str) -> m.BackchannelLogoutTest:
        """Send a test back-channel logout now and return what the receiver answered."""
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{client_id}/backchannel_logout/test",
        )

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

    def preview_profile_mapping(
        self, connection_id: str, body: m.ProfileMappingPreviewBody
    ) -> m.ProfileMappingPreview:
        """OIDC: run the connection's profile mapping (or the body's) against a sample."""
        return self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/profile_mapping/preview",
            body=body,
        )

    def list_signing_keys(self, connection_id: str) -> ListPage:
        """OIDC: the connection's private_key_jwt signing keys
        (:class:`~atlas_backend.models.UpstreamSigningKey`)."""
        return self._t.request(
            method="GET", path=f"/v1/sso_connections/{connection_id}/signing_keys"
        )

    def rotate_signing_key(
        self, connection_id: str, *, alg: Literal["RS256", "PS256", "ES256"] | None = None
    ) -> m.UpstreamSigningKey:
        """Generate a new active key; the previous one turns ``retiring`` (still published)."""
        return self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/signing_keys",
            body=_q(alg=alg),
        )

    def retire_signing_key(self, connection_id: str, kid: str) -> m.UpstreamSigningKey:
        """Retire a non-active key (it leaves the JWKS)."""
        return self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/signing_keys/{kid}/retire",
        )

    def get_saml_encryption_key(self, connection_id: str) -> m.SamlEncryptionKey:
        """The SAML connection's SP encryption certificate(s)."""
        return self._t.request(
            method="GET", path=f"/v1/sso_connections/{connection_id}/saml_encryption_key"
        )

    def create_saml_encryption_key(
        self, connection_id: str, *, idempotency_key: str | None = None
    ) -> m.SamlEncryptionKey:
        """Generate the SP encryption key pair, or ROTATE it when one exists: the current
        pair becomes the previous one (still advertised and accepted until
        :meth:`retire_previous_saml_encryption_key`)."""
        return self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{connection_id}/saml_encryption_key",
            idempotency_key=idempotency_key,
        )

    def retire_previous_saml_encryption_key(self, connection_id: str) -> m.SamlEncryptionKey:
        """Finish a rotation: stop accepting the previous encryption key."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/sso_connections/{connection_id}/saml_encryption_key/previous",
        )

    def delete_saml_encryption_key(self, connection_id: str) -> m.SamlEncryptionKey:
        """Turn assertion encryption off (refused while encrypted assertions are required)."""
        return self._t.request(
            method="DELETE", path=f"/v1/sso_connections/{connection_id}/saml_encryption_key"
        )


class CustomOAuthProviders:
    """Your own upstream OAuth 2.0 / OpenID Connect login providers, with Atlas as the
    relying party: endpoints (or just an OIDC issuer), token-endpoint client
    authentication (incl. private_key_jwt with an Atlas-held key), a declarative
    profile mapping, upstream logout and third-party initiated login. The provider then
    signs users in like any built-in one, under its ``provider_key``."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        """Each ``data`` item is a :class:`~atlas_backend.models.CustomOAuthProvider`."""
        return self._t.request(method="GET", path="/v1/custom_oauth_providers")

    def get(self, provider_id: str) -> m.CustomOAuthProvider:
        return self._t.request(method="GET", path=f"/v1/custom_oauth_providers/{provider_id}")

    def create(
        self, body: m.CreateCustomOAuthProviderBody, *, idempotency_key: str | None = None
    ) -> m.CustomOAuthProvider:
        return self._t.request(
            method="POST",
            path="/v1/custom_oauth_providers",
            body=body,
            idempotency_key=idempotency_key,
        )

    def update(
        self, provider_id: str, body: m.CustomOAuthProviderSettings
    ) -> m.CustomOAuthProvider:
        """Patch a provider; a ``None`` value clears a nullable setting."""
        return self._t.request(
            method="PATCH", path=f"/v1/custom_oauth_providers/{provider_id}", body=body
        )

    def delete(self, provider_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/custom_oauth_providers/{provider_id}")

    def discover(self, issuer: str, *, discovery_url: str | None = None) -> m.OidcDiscoveryResult:
        """Fetch and validate an issuer's OpenID configuration (for autofill)."""
        return self._t.request(
            method="POST",
            path="/v1/custom_oauth_providers/discover",
            body=_q(issuer=issuer, discovery_url=discovery_url),
        )

    def preview_profile_mapping(self, body: m.ProfileMappingPreviewBody) -> m.ProfileMappingPreview:
        """Run a mapping (``body["profile_mapping"]``) against a pasted sample."""
        return self._t.request(
            method="POST", path="/v1/custom_oauth_providers/profile_mapping/preview", body=body
        )

    def preview_provider_profile_mapping(
        self, provider_id: str, body: m.ProfileMappingPreviewBody
    ) -> m.ProfileMappingPreview:
        """Run a provider's stored mapping (or the body's) against a pasted sample."""
        return self._t.request(
            method="POST",
            path=f"/v1/custom_oauth_providers/{provider_id}/profile_mapping/preview",
            body=body,
        )

    def list_signing_keys(self, provider_id: str) -> ListPage:
        """The provider's private_key_jwt signing keys."""
        return self._t.request(
            method="GET", path=f"/v1/custom_oauth_providers/{provider_id}/signing_keys"
        )

    def rotate_signing_key(
        self, provider_id: str, *, alg: Literal["RS256", "PS256", "ES256"] | None = None
    ) -> m.UpstreamSigningKey:
        """Generate a new active key; the previous one turns ``retiring`` (still published)."""
        return self._t.request(
            method="POST",
            path=f"/v1/custom_oauth_providers/{provider_id}/signing_keys",
            body=_q(alg=alg),
        )

    def retire_signing_key(self, provider_id: str, kid: str) -> m.UpstreamSigningKey:
        """Retire a non-active key (it leaves the JWKS)."""
        return self._t.request(
            method="POST",
            path=f"/v1/custom_oauth_providers/{provider_id}/signing_keys/{kid}/retire",
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

    def update(self, token_id: str, body: m.UpdateScimTokenBody) -> m.ScimToken:
        """Change a SCIM token's name, scopes (``["read"]`` = read-only) or role mappings.
        The secret is unchanged."""
        return self._t.request(method="PATCH", path=f"/v1/scim_tokens/{token_id}", body=body)


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
        """Verify a presented ak_ secret. Send ``required_scopes`` to require scopes; a live
        key refused by its own policy answers ``valid: False`` with a ``code``
        (``insufficient_scope``, ``rate_limited`` or ``usage_exhausted``)."""
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
        self.providers = _BillingProviders(transport)

    def sync_seats(self, subject_type: str, subject_id: str) -> m.BillingSeats:
        """Sync a per-seat subscription's Stripe quantity to the org's current member count
        (proration applied).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/billing/subjects/{subject_type}/{subject_id}/sync_seats",
        )

    def record_usage(self, body: m.RecordUsageBody | None = None) -> m.BillingUsage:
        """Report metered usage for a subject (idempotent on idempotency_key); mirrored to
        the provider when the plan is metered. ``feature`` counts it against one provider
        feature; ``subscription_id`` attributes it when the subject holds several.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/usage",
            body=body,
        )

    def get_settings(self) -> m.BillingSettings:
        """How numeric limits merge across a subject's several subscriptions."""
        return self._t.request(method="GET", path="/v1/billing/settings")

    def update_settings(self, body: m.UpdateBillingSettingsBody) -> m.BillingSettings:
        return self._t.request(method="PUT", path="/v1/billing/settings", body=body)

    def check_feature(self, body: m.CheckBillingFeatureBody) -> m.BillingFeatureCheck:
        """May a subject use a feature? Asked live of Autumn/Commet when the subject is on
        one; otherwise answered from the resolved entitlement and this period's usage."""
        return self._t.request(method="POST", path="/v1/billing/check", body=body)


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

    def sync_entitlements(self, plan_id: str) -> m.BillingPlan:
        """Mirror a plan's features and limits from its provider (Autumn, Commet)."""
        return self._t.request(
            method="POST",
            path=f"/v1/billing/plans/{plan_id}/sync_entitlements",
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

    def get(self, subscription_id: str) -> m.Subscription:
        """One subscription (a subject may hold several: a base plan plus add-ons)."""
        return self._t.request(
            method="GET",
            path=f"/v1/billing/subscriptions/{subscription_id}",
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

    def change(self, subscription_id: str, body: m.ChangeSubscriptionBody) -> m.Subscription:
        """Switch a subscription to another plan or interval on the billing provider, now
        (prorated) or at the period end (``schedule_at_period_end``)."""
        return self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{subscription_id}/change",
            body=body,
        )

    def cancel(self, subscription_id: str, *, immediately: bool | None = None) -> m.Subscription:
        """Cancel at the end of the current period, or now with ``immediately=True``."""
        return self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{subscription_id}/cancel",
            body=_q(immediately=immediately),
        )

    def restore(self, subscription_id: str) -> m.Subscription:
        """Undo a cancellation scheduled for the period end."""
        return self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{subscription_id}/restore",
        )


class _BillingProviders:
    """The instance's own billing provider credentials (bring your own key): stripe,
    polar, dodo, creem, chargebee, autumn or commet. Secrets are write-only."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> CursorPage:
        return self._t.request(method="GET", path="/v1/billing/providers")

    def get(self, provider: str) -> m.BillingProvider:
        return self._t.request(method="GET", path=f"/v1/billing/providers/{provider}")

    def set(self, provider: str, body: m.SetBillingProviderBody) -> m.BillingProvider:
        """Store credentials (merged onto what is stored, encrypted at rest)."""
        return self._t.request(method="PUT", path=f"/v1/billing/providers/{provider}", body=body)

    def test(self, provider: str) -> m.BillingProviderTest:
        """Make one read-only call with the stored credentials."""
        return self._t.request(method="POST", path=f"/v1/billing/providers/{provider}/test")

    def delete(self, provider: str, *, force: bool | None = None) -> JSON:
        """Remove a provider's credentials; refused while subscriptions or plans depend on
        it unless ``force=True``."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/billing/providers/{provider}",
            query=_q(force="true" if force else None),
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
        since: int | str | None = None,
        until: int | str | None = None,
        order: Literal["asc", "desc"] | None = None,
    ) -> CursorPage:
        """Read the product activity feed (events), filterable by type and time and cursor-
        paginated, with the list of event types this instance has actually emitted. ``since``
        / ``until`` bound the window (epoch ms or ISO date); ``order="asc"`` reads forward
        from a checkpoint.
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
                    "since": since,
                    "until": until,
                    "order": order,
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
        self.integrations = _InstanceIntegrations(transport)
        self.referrals = _InstanceReferrals(transport)
        self.hooks = _InstanceHooks(transport)

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

    def set_account_linking_trust(self, trust: dict[str, str]) -> m.Instance:
        """Write ``auth_config.accountLinkingTrust``: keys are an exact provider key, a
        ``prefix*`` or ``*``; values ``always`` (vouch for the provider's email, for
        linking only), ``verified`` or ``never`` (refuse with 409
        ``IDENTITY_ALREADY_LINKED``). An account that never proved its email is never
        linked."""
        return self._t.request(
            method="PATCH",
            path="/v1/instance",
            body={"auth_config": {"accountLinkingTrust": trust}},
        )

    def set_captcha_config(self, captcha: dict[str, Any]) -> m.Instance:
        """Merge ``auth_config.captcha``: ``provider`` (see ``CAPTCHA_PROVIDERS``),
        ``siteKey``, ``widget``, ``minScore``, per-flow / per-action overrides, and for
        Vercel BotID ``attestationUrl`` (an https URL or a root-relative path)."""
        return self._t.request(
            method="PATCH",
            path="/v1/instance",
            body={"auth_config": {"captcha": captcha}},
        )

    def set_captcha_secret(self, body: m.SetCaptchaSecretBody | None = None) -> m.CaptchaSecret:
        """Store the captcha provider secret (write-only, encrypted; never read back)."""
        return self._t.request(
            method="PUT",
            path="/v1/instance/captcha_secret",
            body=body,
        )

    def delete_captcha_secret(
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
        return self._t.request(
            method="DELETE",
            path="/v1/instance/captcha_secret",
            query=query or None,
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

    def get_proxy_secret(self) -> m.ProxySecret:
        """Whether a trusted reverse proxy secret is set, and since when (never the
        secret).
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/proxy_secret",
        )

    def create_proxy_secret(
        self, body: m.CreateProxySecretBody | None = None
    ) -> m.ProxySecretCreated:
        """Create, or rotate, the trusted reverse proxy secret; it is returned once. On a
        rotation the replaced secret keeps working for ``overlap_seconds`` (default 86400,
        ``0`` = stop now, at most 604800).
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/proxy_secret",
            body=body,
        )

    def delete_proxy_secret(self) -> m.InstanceDeleteProxySecretResult:
        """Remove the trusted reverse proxy secret: ``X-Atlas-Client-IP`` is ignored again."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/proxy_secret",
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

    def preflight(
        self,
        *,
        min_severity: Literal["error", "warning", "info"] | None = None,
        include_suppressed: bool | None = None,
    ) -> m.Preflight:
        """Check your setup in one call. ``min_severity`` keeps only findings at least that
        severe (``ok`` still covers every finding); ``include_suppressed`` also lists the
        suppressed ones."""
        return self._t.request(
            method="GET",
            path="/v1/instance/preflight",
            query=_q(min_severity=min_severity, include_suppressed=include_suppressed),
        )

    def unknown_fields_report(self, *, days: int | None = None) -> JSON:
        """Which unknown body fields your writes sent (ignored, or refused in strict mode),
        aggregated over the last ``days``."""
        return self._t.request(
            method="GET", path="/v1/instance/unknown_fields_report", query=_q(days=days)
        )

    def move_origin(self, body: m.OriginMoveBody) -> m.OriginMove:
        """Move every URL that points at one origin to another (a domain move), across the
        instance, its OAuth clients, webhooks, redirect URLs and Sign in with Atlas apps.

        ``body`` is ``{"from": ..., "to": ..., "dry_run": ...}``; ``dry_run=True`` writes
        nothing. A repeated run returns an empty ``changes`` list.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/move_origin",
            body=body,
        )

    def connections(self) -> m.InstanceConnections:
        """The instance's links to other platforms and their health. Read-only."""
        return self._t.request(
            method="GET",
            path="/v1/instance/connections",
        )


class _InstanceIntegrations:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_chatly(self) -> m.ChatlyIntegration:
        """Read the Chatly connection (``enabled: False`` when none)."""
        return self._t.request(
            method="GET",
            path="/v1/instance/integrations/chatly",
        )

    def set_chatly(self, body: m.SetChatlyIntegrationBody) -> m.ChatlyIntegration:
        """Connect a Chatly channel: ``getToken({ template: 'chatly' })`` then mints tokens
        the channel's identity verification accepts.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/integrations/chatly",
            body=body,
        )

    def delete_chatly(self) -> m.ChatlyIntegration:
        """Remove the Chatly connection."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/integrations/chatly",
        )

    def get_forumulate(self) -> m.ForumulateIntegration:
        """Read the Forumulate connection (``enabled: False`` when none)."""
        return self._t.request(
            method="GET",
            path="/v1/instance/integrations/forumulate",
        )

    def set_forumulate(self, body: m.SetForumulateIntegrationBody) -> m.ForumulateIntegration:
        """Connect Forumulate spaces (replaces the whole connection). Store the returned
        ``reader_auth_provider`` on each space.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/integrations/forumulate",
            body=body,
        )

    def delete_forumulate(self) -> m.ForumulateIntegration:
        """Remove the Forumulate connection."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/integrations/forumulate",
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


class _InstanceReferrals:
    """Referral attribution: the instance's connection to a referral platform.

    With referrals on, every interactive sign-up is reported to the platform before
    ``user.created`` is sent; the answer lands on the user (``referral``,
    ``referral_code``, ``referral_link``). ``signing_secret`` and ``api_key`` are
    write-only.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.ReferralSettings:
        """Read the referral settings, the connection status and the supported providers."""
        return self._t.request(
            method="GET",
            path="/v1/instance/referrals",
        )

    def update(
        self,
        body: m.UpdateReferralSettingsBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.ReferralSettings:
        """Update the referral settings; only the fields sent change, ``None`` clears.
        Enabling without what the provider needs is 422 ``REFERRALS_NOT_CONFIGURED``.
        """
        return self._t.request(
            method="PATCH",
            path="/v1/instance/referrals",
            body=body,
            idempotency_key=idempotency_key,
        )

    def test(self) -> m.ReferralConnectionTest:
        """Test the connection: a ping where the provider answers one (``method``
        ``ping``, with ``ping`` and ``warnings`` such as clock skew), else a signed probe
        (``method`` ``probe``: ``ok`` on 2xx or 404). ``error.code``
        ``signature_rejected`` on 401/403.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/referrals/test",
        )

    def list_calls(
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
        return self._t.request(
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

    def get_call(self, call_id: str) -> m.ReferralCall:
        """One call of the delivery log, by id or the platform's request id."""
        return self._t.request(method="GET", path=f"/v1/instance/referrals/calls/{call_id}")

    def install(self, provider: str, body: dict[str, Any] | None = None) -> JSON:
        """One-click install of a referral platform (``referalli``; the old id ``referally``
        is accepted): Atlas connects, registers its signing secret and enables referrals."""
        return self._t.request(
            method="POST",
            path=f"/v1/instance/referrals/{_enc(provider)}/install",
            body=body,
        )

    def retry_call(self, call_id: str, *, idempotency_key: str | None = None) -> m.ReferralCall:
        """Retry a failed, retrying or skipped call now (not a connection test)."""
        return self._t.request(
            method="POST",
            path=f"/v1/instance/referrals/calls/{call_id}/retry",
            idempotency_key=idempotency_key,
        )

    def retry_failed(
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
        return self._t.request(
            method="POST",
            path="/v1/instance/referrals/calls/retry_failed",
            body=_q(kind=kind, error_code=error_code),
            idempotency_key=idempotency_key,
        )

    def simulate(self, *, code: str | None = None) -> m.ReferralSimulateResult:
        """Send a sign-up call for a made-up user (``atlas_test_<random>``, no user is
        created) with an optional ``code``, and return what the platform answered.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/referrals/simulate",
            body=_q(code=code),
        )

    def backfill(
        self,
        body: m.ReferralBackfillBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.ReferralBackfillJob:
        """Queue sign-up calls for existing users created at or after ``since``, with
        their real sign-up time. Users already reported are skipped. Referrals must be on
        (422 ``REFERRALS_NOT_CONFIGURED`` otherwise). Poll :meth:`get_backfill`.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/referrals/backfill",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_backfill(self, backfill_id: str) -> m.ReferralBackfillJob:
        """Read a backfill job: how many calls it queued and where they stand."""
        return self._t.request(
            method="GET",
            path=f"/v1/instance/referrals/backfill/{backfill_id}",
        )

    def get_for_user(self, user_id: str) -> m.UserReferralResult:
        """The stored referral result for one user (who referred them, how, their own
        code), with no call to the platform. 404 when the user was never reported.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/referral",
        )


class _InstanceHooks:
    """The ``before_user_create`` hook: just before Atlas creates a user from a
    self-service sign-up, it sends your endpoint a signed ``POST`` (the webhook headers;
    verify it with :func:`verify_webhook`) of type ``user.before_create`` and stamps the
    ``external_id`` and metadata you answer. A slow or failing hook never blocks a
    sign-up. ``signing_secret`` is write-only.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_before_user_create(self) -> m.BeforeUserCreateHook:
        """Read the hook settings and its last call."""
        return self._t.request(
            method="GET",
            path="/v1/instance/hooks/before_user_create",
        )

    def update_before_user_create(
        self,
        body: m.UpdateBeforeUserCreateHookBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.BeforeUserCreateHook:
        """Update the hook; only the fields sent change, ``None`` clears. Turning it on
        needs ``url`` and ``signing_secret``.
        """
        return self._t.request(
            method="PATCH",
            path="/v1/instance/hooks/before_user_create",
            body=body,
            idempotency_key=idempotency_key,
        )

    def test_before_user_create(self) -> m.BeforeUserCreateHookTest:
        """Send the hook a sample draft and return its answer; nothing is stored."""
        return self._t.request(
            method="POST",
            path="/v1/instance/hooks/before_user_create/test",
        )

    def list_before_user_create_calls(
        self,
        *,
        limit: int | None = None,
        status: Literal["ok", "failed", "timeout", "error", "invalid_response"] | None = None,
        test: bool | None = None,
        starting_after: str | None = None,
    ) -> CursorPage:
        """The hook's delivery log, newest first (kept 30 days)."""
        return self._t.request(
            method="GET",
            path="/v1/instance/hooks/before_user_create/calls",
            query=_q(
                limit=limit,
                status=status,
                test=None if test is None else ("true" if test else "false"),
                starting_after=starting_after,
            ),
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

    def list_signing_keys(self) -> m.SigningKeyList:
        """The published token-signing keys: ``current`` and, inside a rotation's grace
        window, ``previous`` with ``retires_at``."""
        return self._t.request(method="GET", path="/v1/instance/signing_keys")

    def rotate_signing_key(
        self, body: m.RotateSigningKeyBody | None = None
    ) -> m.SigningKeyRotation:
        """Rotate the instance signing key, optionally switching ``alg`` (RS256 or ES256)."""
        return self._t.request(
            method="POST", path="/v1/instance/signing_keys/rotate", body=body or {}
        )

    def get_signing_key_provider(self) -> m.SigningKeyProviderSettings:
        """The key management service the signing key lives in (``local`` when none)."""
        return self._t.request(method="GET", path="/v1/instance/signing_key_provider")

    def set_signing_key_provider(
        self, body: m.SetSigningKeyProviderBody
    ) -> m.SigningKeyProviderSettings:
        """Sign every token with a key in your own AWS KMS, Google Cloud KMS or Azure Key
        Vault. The result carries the ``rotation`` onto the KMS key."""
        return self._t.request(method="PUT", path="/v1/instance/signing_key_provider", body=body)

    def remove_signing_key_provider(
        self, body: m.RotateSigningKeyBody | None = None
    ) -> m.SigningKeyProviderSettings:
        """Stop using the KMS: rotate back to a key Atlas holds and forget the credentials."""
        return self._t.request(
            method="DELETE", path="/v1/instance/signing_key_provider", body=body or {}
        )

    def set_wallet_rpc_secret(self, *, chain_id: int, url: str) -> m.WalletRpcSecret:
        """Store (write-only, encrypted) the wallet RPC endpoint for an EIP-155 chain, used
        by wallet token gating and the Sign in with Ethereum ENS lookup. An empty ``url``
        removes it; the URL is never returned."""
        return self._t.request(
            method="PUT",
            path="/v1/instance/wallet_rpc_secret",
            body={"chain_id": chain_id, "url": url},
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


class BetterAuthImports:
    """Migrate from Better Auth: import a sealed bundle made by the Better Auth
    exporter (``npx atlas-better-auth-export``).

    1. :meth:`get_public_key` — the key the exporter seals the bundle to.
    2. :meth:`upload` (or :meth:`create`, :meth:`upload_part` per part and
       :meth:`finalize`) — Atlas opens the bundle and runs the dry run.
    3. Read the import's ``report``, then :meth:`apply`. Applying again after a
       failure resumes where it stopped; every record is an idempotent upsert.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_public_key(self) -> m.BetterAuthImportKey:
        """The instance's import public key (created on first read)."""
        return self._t.request(
            method="GET",
            path="/v1/better_auth_imports/public_key",
        )

    def rotate_public_key(self, *, idempotency_key: str | None = None) -> m.BetterAuthImportKey:
        """Replace the import key. The old one is retired: bundles sealed to it no
        longer finalize (``import_key_retired``)."""
        return self._t.request(
            method="POST",
            path="/v1/better_auth_imports/public_key/rotate",
            idempotency_key=idempotency_key,
        )

    def create(
        self,
        body: m.CreateBetterAuthImportBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.BetterAuthImport:
        """Start an import (status ``uploading``), optionally with import options."""
        return self._t.request(
            method="POST",
            path="/v1/better_auth_imports",
            body=body or {},
            idempotency_key=idempotency_key,
        )

    def list(self, *, limit: int | None = None, starting_after: str | None = None) -> CursorPage:
        """List imports, newest first. Each ``data`` item is a
        :class:`~atlas_backend.models.BetterAuthImport`."""
        return self._t.request(
            method="GET",
            path="/v1/better_auth_imports",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def get(self, import_id: str) -> m.BetterAuthImport:
        """Fetch an import: status, progress, the dry-run ``report`` and the ``result``."""
        return self._t.request(
            method="GET",
            path=f"/v1/better_auth_imports/{import_id}",
        )

    def upload_part(self, import_id: str, part: int, data: str | bytes) -> m.BetterAuthImportPart:
        """Upload part ``part`` (1-based) of the sealed bundle: whole lines, at most
        10 MiB. Re-sending a part replaces it."""
        if isinstance(data, bytes):
            # Raw bytes go up as-is (text/plain): the server reads them as the part's lines.
            return self._t.request(
                method="PUT",
                path=f"/v1/better_auth_imports/{import_id}/parts/{part}",
                content=data,
                content_type="text/plain; charset=utf-8",
            )
        return self._t.request(
            method="PUT",
            path=f"/v1/better_auth_imports/{import_id}/parts/{part}",
            body={"data": data},
        )

    def finalize(self, import_id: str) -> m.BetterAuthImport:
        """Close the upload: Atlas checks the parts and the key, then runs the dry run
        (inline up to 4 MiB, ``analyzing`` in the background above that)."""
        return self._t.request(
            method="POST",
            path=f"/v1/better_auth_imports/{import_id}/finalize",
        )

    def dry_run(
        self, import_id: str, body: m.CreateBetterAuthImportBody | None = None
    ) -> m.BetterAuthImport:
        """Run the dry run again; new ``options`` replace the stored ones."""
        return self._t.request(
            method="POST",
            path=f"/v1/better_auth_imports/{import_id}/dry_run",
            body=body or {},
        )

    def apply(
        self, import_id: str, body: m.ApplyBetterAuthImportBody | None = None
    ) -> m.BetterAuthImport:
        """Import (or resume a ``failed`` import from its cursor). Pass
        ``{"confirm_conflicts": True}`` when the dry run reported conflicts."""
        return self._t.request(
            method="POST",
            path=f"/v1/better_auth_imports/{import_id}/apply",
            body=body or {},
        )

    def delete(self, import_id: str) -> m.BetterAuthImportDeleted:
        """Remove the import and its stored bundle; data already imported stays."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/better_auth_imports/{import_id}",
        )

    def list_jwks(self) -> CursorPage:
        """The Better Auth JWT keys Atlas publishes in the instance JWKS for the
        cutover. Each ``data`` item is a :class:`~atlas_backend.models.ImportedJwk`."""
        return self._t.request(
            method="GET",
            path="/v1/better_auth_imports/jwks",
        )

    def delete_jwk(self, kid: str) -> m.ImportedJwkDeleted:
        """Stop publishing one imported Better Auth JWT key."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/better_auth_imports/jwks/{kid}",
        )

    def upload(
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
        created = self.create({"options": options} if options else None)
        import_id = created.get("id") if isinstance(created, dict) else None
        if not import_id:
            raise ValueError("Atlas did not return an import id.")
        for i, part in enumerate(parts, start=1):
            self.upload_part(import_id, i, part)
            if on_part is not None:
                on_part(i, len(parts))
        return self.finalize(import_id)

    def wait_for(
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
            imp = self.get(import_id)
            if on_progress is not None:
                on_progress(imp)
            if imp.get("status") not in BETTER_AUTH_IMPORT_IN_FLIGHT:
                return imp
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Timed out waiting for Better Auth import {import_id} "
                    f"(status {imp.get('status')})."
                )
            time.sleep(interval)


class BetterAuthBridge:
    """The Better Auth session bridge: during a migration window a returning user's
    Better Auth session is exchanged, once, for an Atlas session — nobody is signed
    out by the switch. See :func:`atlas_backend.exchange_better_auth_session` and the
    framework integrations' ``ATLAS_BETTER_AUTH_BRIDGE`` setting."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.BetterAuthBridgeSettings:
        """The bridge settings and exchange counts (``live_fallback.has_secret``, never
        the secret)."""
        return self._t.request(
            method="GET",
            path="/v1/migrations/better_auth/bridge",
        )

    def update(
        self, body: m.UpdateBetterAuthBridgeBody, *, idempotency_key: str | None = None
    ) -> m.BetterAuthBridgeSettings:
        """Create or update the settings. Every field is optional and merged onto the
        stored ones; ``live_fallback.secret`` is write-only (omit to keep, ``None`` to
        clear)."""
        return self._t.request(
            method="PUT",
            path="/v1/migrations/better_auth/bridge",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, *, idempotency_key: str | None = None) -> m.BetterAuthBridgeDeleted:
        """Remove the settings: the bridge is off and the stored secret is deleted."""
        return self._t.request(
            method="DELETE",
            path="/v1/migrations/better_auth/bridge",
            idempotency_key=idempotency_key,
        )

    def exchange(
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
        return self._t.request(
            method="POST",
            path="/v1/migrations/better_auth/exchange",
            body=body,
            headers=headers,
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
        self.managed_email = _ManagedEmail(transport)
        self.development_email = _DevelopmentEmail(transport)

    def list(self) -> m.MessagingProviders:
        """Read the instance's BYOK email and SMS provider config: transport, from-address and
        which secret keys are set.
        """
        return self._t.request(
            method="GET",
            path="/v1/messaging_providers",
        )

    def get_channel(self, channel: str) -> m.MessagingProvider:
        """Read one channel's provider configuration (``email`` or ``sms``)."""
        return self._t.request(method="GET", path=f"/v1/messaging_providers/{_enc(channel)}")

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


class _ManagedEmail:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.ManagedEmail:
        """Read the managed sending domain: status, records, limits and usage (404 when none
        is configured).
        """
        return self._t.request(
            method="GET",
            path="/v1/messaging_providers/email/managed",
        )

    def create(self, body: m.CreateManagedEmailBody) -> m.ManagedEmail:
        """Set your sending domain up on your own Resend or Brevo account: pass ``transport``
        with ``config.api_key``, or ``provider_id`` of your configured provider. Returns the
        DNS ``records`` to publish. With ``dns`` Atlas writes them itself (the token is
        write-only).
        """
        return self._t.request(
            method="POST",
            path="/v1/messaging_providers/email/managed",
            body=body,
        )

    def verify(self) -> m.ManagedEmail:
        """Re-check the DNS records now; ``verified`` is true once email can be sent."""
        return self._t.request(
            method="POST",
            path="/v1/messaging_providers/email/managed/verify",
        )

    def delete(self, *, force: bool = False) -> m.ManagedEmailDeleteResult:
        """Stop using managed email (DNS records are left in place).

        Refused with 409 ``EMAIL_PROVIDER_IN_USE`` while it is the only way the instance can
        send email; pass ``force=True`` to remove it anyway.
        """
        return self._t.request(
            method="DELETE",
            path="/v1/messaging_providers/email/managed",
            query={"force": True} if force else None,
        )


class _DevelopmentEmail:
    """Your own email provider in development mode: a development instance sends Atlas's
    sign-in emails without a verified domain (``[Atlas test]`` subjects, capped).
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.DevelopmentEmail:
        """Read the email provider in development mode (404 when it is not in development
        mode).
        """
        return self._t.request(
            method="GET",
            path="/v1/messaging_providers/email/development",
        )

    def enable(self, body: m.EnableDevelopmentEmailBody) -> m.DevelopmentEmail:
        """Put your email provider in development mode. 409 ``DEVELOPMENT_EMAIL_NOT_ALLOWED``
        on a production instance.
        """
        return self._t.request(
            method="POST",
            path="/v1/messaging_providers/email/development",
            body=body,
        )

    def disable(self) -> m.DevelopmentEmailDeleteResult:
        """Put the email provider back in standard mode (the provider and its key stay)."""
        return self._t.request(
            method="DELETE",
            path="/v1/messaging_providers/email/development",
        )


class LogoutNotifyEndpoints:
    """Logout fan-out endpoints: downstream services that receive the same signed
    ``logout_token`` as your OIDC apps whenever a session ends.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(
            method="GET",
            path="/v1/logout_notify_endpoints",
        )

    def create(
        self, body: m.CreateLogoutNotifyEndpointBody, *, idempotency_key: str | None = None
    ) -> m.LogoutNotifyEndpoint:
        """Register an endpoint (public https). With ``oauth_client_id`` it follows one
        client instead of the whole instance.
        """
        return self._t.request(
            method="POST",
            path="/v1/logout_notify_endpoints",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, endpoint_id: str) -> m.LogoutNotifyEndpoint:
        return self._t.request(
            method="GET",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}",
        )

    def update(
        self,
        endpoint_id: str,
        body: m.UpdateLogoutNotifyEndpointBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.LogoutNotifyEndpoint:
        return self._t.request(
            method="PATCH",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, endpoint_id: str, *, idempotency_key: str | None = None) -> DeletedObject:
        """Delete an endpoint; its queued deliveries go with it."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}",
            idempotency_key=idempotency_key,
        )

    def list_deliveries(self, endpoint_id: str, *, limit: int | None = None) -> ListPage:
        """The endpoint's delivery log, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/logout_notify_endpoints/{endpoint_id}/deliveries",
            query=_q(limit=limit),
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
        metadata: dict[str, Any] | None = None,
    ) -> ListPage:
        """List the apps (instances) this platform owns; ``metadata`` filters on
        ``metadata[key]=value``."""
        return self._t.request(
            method="GET",
            path="/v1/platform/apps",
            query=_meta(metadata, tag=tag, archived=archived, include_archived=include_archived)
            or None,
        )

    def create(
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
        return self._t.request(
            method="POST",
            path="/v1/platform/apps",
            body=body,
            idempotency_key=idempotency_key,
            query=_dry(dry_run),
        )

    def create_secret_key(
        self,
        app_id: str,
        body: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> JSON:
        """Mint another secret key for an owned app (scopes, ``owner``, ``expires_at``,
        ``allowed_origins``, ``external_ref``)."""
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/secret_keys",
            body=body if body is not None else {},
            idempotency_key=idempotency_key,
        )

    def clone_config(self, app_id: str, body: dict[str, Any], *, dry_run: bool = False) -> JSON:
        """Copy another app's configuration (``from_app_id``) onto this one."""
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/clone_config",
            body=body,
            query=_dry(dry_run),
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
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{app_id}/instances/{instance_id}/rotate_secret",
            body=body,
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

    def rotate_secret(
        self, app_id: str, body: m.RotateAtlasIdAppSecretBody | None = None
    ) -> m.AtlasIdApp:
        """Rotate a confidential app's client_secret (returned once). The previous one keeps
        working for ``overlap_seconds`` (default 86400 = 24 hours; ``0`` revokes it now).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/rotate_secret",
            body=body,
        )

    def list_backchannel_deliveries(
        self, app_id: str, *, limit: int | None = None, starting_after: str | None = None
    ) -> m.BackchannelLogoutDeliveryList:
        """The app's back-channel logout delivery log, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/backchannel_deliveries",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def test_backchannel_logout(self, app_id: str) -> m.BackchannelLogoutTest:
        """Send a test back-channel logout to the app now."""
        return self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/backchannel_logout/test",
        )

    def preflight(self, app_id: str) -> m.AtlasIdAppPreflightDetail:
        """Check one app's setup, in the instance preflight's finding shape."""
        return self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/preflight",
        )

    def find_users(self, app_id: str, email: str) -> m.AtlasIdAppUserList:
        """Privacy requests: is this person one of the app's users? Exact match on a
        verified email; anyone else gets the same empty list.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{app_id}/users",
            query={"email": email},
        )

    def revoke_grant(self, app_id: str, grant_id: str) -> m.AtlasIdGrantRevocation:
        """Revoke one user's grant (``grant_id`` from ``find_users``); the next sign-in shows
        the consent screen again.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{app_id}/grants/{grant_id}",
        )

    def set_managed_by(
        self, app_id: str, instance_id: str | None
    ) -> m.AtlasIdAppManagedBy:
        """Hand the app's grant management to an instance of the same account
        (``managed_via: "adopted"``), or take it back with ``None``. That instance's secret
        key, scoped to ``privacy:grants:revoke`` or ``atlas_id_grants:*``, then lists and
        revokes the app's grants, so a data-rights tool never needs the platform key.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/platform/atlas_id_apps/{app_id}/managed_by",
            body={"instance_id": instance_id},
        )

    def move_origin(self, app_id: str, body: m.OriginMoveBody) -> m.OriginMove:
        """Move the app's URLs from one origin to another. ``dry_run`` writes nothing."""
        return self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/move_origin",
            body=body,
        )

    def rotate_webhook_secret(
        self, app_id: str, body: m.RotateAtlasIdAppSecretBody | None = None
    ) -> m.AtlasIdApp:
        """Rotate the app's webhook signing secret (``webhook_secret``, returned once). By
        default the previous secret stops signing at once; with ``overlap_seconds`` it signs
        each delivery too until ``webhook_previous_secret_expires_at``.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{app_id}/webhook/rotate_secret",
            body=body,
        )


class PlatformAtlasIdPublisher:
    """The account's Sign in with Atlas publisher name and DNS-verified domain."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.AtlasIdPublisher:
        """Read the publisher (404 until claimed)."""
        return self._t.request(
            method="GET",
            path="/v1/platform/atlas_id_publisher",
        )

    def set(self, body: m.SetAtlasIdPublisherBody) -> m.AtlasIdPublisher:
        """Claim a publisher name and domain; returns the TXT record to publish."""
        return self._t.request(
            method="PUT",
            path="/v1/platform/atlas_id_publisher",
            body=body,
        )

    def update(self, body: m.UpdateAtlasIdPublisherBody) -> m.AtlasIdPublisher:
        """Turn publisher-wide consent (``skip_consent``) on or off."""
        return self._t.request(
            method="PATCH",
            path="/v1/platform/atlas_id_publisher",
            body=body,
        )

    def delete(self) -> m.AtlasIdPublisherDeleteResult:
        """Remove the publisher claim."""
        return self._t.request(
            method="DELETE",
            path="/v1/platform/atlas_id_publisher",
        )

    def verify(self) -> m.AtlasIdPublisher:
        """Look up the TXT record now (``record_found``)."""
        return self._t.request(
            method="POST",
            path="/v1/platform/atlas_id_publisher/verify",
        )


class PlatformConfigChangelog:
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
        """Config change history for the account's Sign in with Atlas apps."""
        return self._t.request(
            method="GET",
            path="/v1/platform/config_changelog",
            query=_q(action=action, limit=limit, starting_after=starting_after, since=since),
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


class AppRoles:
    """Instance-wide user roles (``/v1/app_roles``), not tied to any organization. A
    user's app roles ride on their session token as ``app_roles`` / ``app_permissions``;
    check them offline with :func:`has_app_role` / :func:`has_app_permission`.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> CursorPage:
        return self._t.request(method="GET", path="/v1/app_roles")

    def create(self, body: m.CreateAppRoleBody) -> m.AppRole:
        return self._t.request(method="POST", path="/v1/app_roles", body=body)

    def get(self, role_id: str) -> m.AppRole:
        """By id or key."""
        return self._t.request(method="GET", path=f"/v1/app_roles/{role_id}")

    def update(self, role_id: str, body: m.UpdateAppRoleBody) -> m.AppRole:
        return self._t.request(method="PATCH", path=f"/v1/app_roles/{role_id}", body=body)

    def delete(self, role_id: str) -> DeletedObject:
        return self._t.request(method="DELETE", path=f"/v1/app_roles/{role_id}")

    def list_users(
        self, role_id: str, *, limit: int | None = None, offset: int | None = None
    ) -> CursorPage:
        """The users holding a role, oldest assignment first."""
        return self._t.request(
            method="GET",
            path=f"/v1/app_roles/{role_id}/users",
            query=_q(limit=limit, offset=offset),
        )

    def get_for_user(self, user_id: str) -> m.UserAppRoles:
        """A user's app roles and effective permissions."""
        return self._t.request(method="GET", path=f"/v1/users/{user_id}/app_roles")

    def set_for_user(self, user_id: str, body: m.SetUserAppRolesBody) -> m.UserAppRoles:
        """``roles`` replaces the set; ``add`` / ``remove`` change it (keys or ids)."""
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/app_roles", body=body)

    def remove_from_user(self, user_id: str, role_id: str) -> m.UserAppRoles:
        return self._t.request(method="DELETE", path=f"/v1/users/{user_id}/app_roles/{role_id}")


class OAuthInitialAccessTokens:
    """Initial access tokens for OAuth dynamic client registration (RFC 7591 §3), needed
    once ``oauthProvider.requireInitialAccessToken`` is on."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> CursorPage:
        return self._t.request(method="GET", path="/v1/oauth_initial_access_tokens")

    def create(self, body: m.CreateInitialAccessTokenBody | None = None) -> m.InitialAccessToken:
        """Mint a token; ``token`` is returned exactly once."""
        return self._t.request(
            method="POST", path="/v1/oauth_initial_access_tokens", body=body or {}
        )

    def revoke(self, token_id: str) -> m.InitialAccessToken:
        return self._t.request(method="DELETE", path=f"/v1/oauth_initial_access_tokens/{token_id}")


class ActionGallery:
    """The community Actions gallery: browse reusable Action templates (first-party and
    community), install one as a DISABLED action, keep installed actions up to date."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        trigger: str | None = None,
        source: Literal["builtin", "community"] | None = None,
    ) -> ListPage:
        """The gallery, best first (:class:`~atlas_backend.models.ActionGalleryEntry`)."""
        return self._t.request(
            method="GET",
            path="/v1/action_gallery",
            query=_q(q=q, category=category, trigger=trigger, source=source),
        )

    def get(self, slug: str) -> m.ActionGalleryEntry:
        """One template with its code, secret names and versions."""
        return self._t.request(method="GET", path=f"/v1/action_gallery/{slug}")

    def install(
        self,
        slug: str,
        body: m.InstallTemplateBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.ActionGalleryInstallResult:
        """Install as a new, disabled action. Supply secrets, bind it, then enable it."""
        return self._t.request(
            method="POST",
            path=f"/v1/action_gallery/{slug}/install",
            body=body or {},
            idempotency_key=idempotency_key,
        )

    def installs(self) -> ListPage:
        """Actions installed from the gallery, with update status."""
        return self._t.request(method="GET", path="/v1/action_gallery_installs")

    def update(
        self, action_id: str, *, secrets: dict[str, str] | None = None
    ) -> m.ActionGalleryUpdateResult:
        """Move an installed action to its template's latest version."""
        return self._t.request(
            method="POST",
            path=f"/v1/actions/{action_id}/gallery_update",
            body=_q(secrets=secrets),
        )


class ActionTemplates:
    """Templates this instance publishes to the gallery (staff review them)."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/action_templates")

    def create(
        self, body: m.CreateActionTemplateBody, *, idempotency_key: str | None = None
    ) -> m.ActionTemplate:
        return self._t.request(
            method="POST",
            path="/v1/action_templates",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, template_id: str) -> m.ActionTemplate:
        return self._t.request(method="GET", path=f"/v1/action_templates/{template_id}")

    def update(self, template_id: str, body: m.ActionTemplateListing) -> m.ActionTemplate:
        return self._t.request(
            method="PATCH", path=f"/v1/action_templates/{template_id}", body=body
        )

    def delete(self, template_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/action_templates/{template_id}")

    def add_version(
        self, template_id: str, body: m.NewTemplateVersionBody
    ) -> m.ActionTemplateVersion:
        return self._t.request(
            method="POST", path=f"/v1/action_templates/{template_id}/versions", body=body
        )

    def submit_version(self, template_id: str, version: str) -> m.ActionTemplateVersion:
        return self._t.request(
            method="POST",
            path=f"/v1/action_templates/{template_id}/versions/{version}/submit",
        )

    def delete_version(self, template_id: str, version: str) -> JSON:
        return self._t.request(
            method="DELETE",
            path=f"/v1/action_templates/{template_id}/versions/{version}",
        )

    def publish(self, template_id: str) -> m.ActionTemplate:
        """List an approved template again after unlisting it."""
        return self._t.request(method="POST", path=f"/v1/action_templates/{template_id}/publish")

    def unlist(self, template_id: str) -> m.ActionTemplate:
        """Hide a template from the gallery (installs keep working)."""
        return self._t.request(method="POST", path=f"/v1/action_templates/{template_id}/unlist")


class Policies:
    """Policy acceptance: the policies (Terms of Service, privacy policy, any key) your
    users accept at sign-up - and, per policy, again at sign-in when a new version takes
    effect. A policy's versions go draft, published (with an ``effective_at``), retired.
    Acceptances are append-only evidence (version, content hash, how it was shown).
    ``id_or_key`` is the policy id or its key.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.versions = _PolicyVersions(transport)
        self.settings = _PolicySettings(transport)

    def list(self, *, include_retired: bool | None = None) -> ListPage:
        """Active policies (``include_retired`` for all), each with its current, upcoming
        and latest version."""
        return self._t.request(
            method="GET",
            path="/v1/policies",
            query=_q(include_retired=include_retired),
        )

    def create(self, body: m.CreatePolicyBody, *, idempotency_key: str | None = None) -> m.Policy:
        """Create a policy. It asks nobody anything until a version is published."""
        return self._t.request(
            method="POST", path="/v1/policies", body=body, idempotency_key=idempotency_key
        )

    def get(self, id_or_key: str) -> m.Policy:
        """One policy, by id or key."""
        return self._t.request(method="GET", path=f"/v1/policies/{id_or_key}")

    def update(
        self,
        id_or_key: str,
        body: m.UpdatePolicyBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.Policy:
        """Update a policy (the key cannot change). ``status: "retired"`` stops it gating."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/policies/{id_or_key}",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, id_or_key: str) -> JSON:
        """Delete a policy that was never published; one with a published version is
        retired instead (the response says which: ``deleted`` / ``retired``)."""
        return self._t.request(method="DELETE", path=f"/v1/policies/{id_or_key}")

    def list_acceptances(
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
        return self._t.request(
            method="GET",
            path=f"/v1/policies/{id_or_key}/acceptances",
            query=_q(version=version, status=status, limit=limit, starting_after=starting_after),
        )

    def export_acceptances_csv(
        self,
        id_or_key: str,
        *,
        version: str | None = None,
        status: Literal["accepted", "withdrawn", "all"] | None = None,
    ) -> str:
        """The same as CSV text (``format=csv``, up to 100,000 rows)."""
        return self._t.request(
            method="GET",
            path=f"/v1/policies/{id_or_key}/acceptances",
            query=_q(version=version, status=status, format="csv"),
            raw=True,
        )

    def for_user(self, user_id: str) -> m.UserPolicies:
        """A user's standing on every policy (accepted and current version,
        ``needs_reaccept``, ``blocking``, ``grace_ends_at``) and ``needs_acceptance``."""
        return self._t.request(method="GET", path=f"/v1/users/{user_id}/policies")


class _PolicyVersions:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, id_or_key: str) -> ListPage:
        """The policy's versions, newest first, each with ``acceptance_count``."""
        return self._t.request(method="GET", path=f"/v1/policies/{id_or_key}/versions")

    def create(
        self,
        id_or_key: str,
        body: m.CreatePolicyVersionBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Create a draft, or publish at once with ``publish: True`` (and ``effective_at``).
        400 for an external policy: its versions come from the policy source."""
        return self._t.request(
            method="POST",
            path=f"/v1/policies/{id_or_key}/versions",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(self, id_or_key: str, version_id_or_label: str) -> m.PolicyVersion:
        """One version, by id or label."""
        return self._t.request(
            method="GET", path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}"
        )

    def update(
        self,
        id_or_key: str,
        version_id_or_label: str,
        body: m.UpdatePolicyVersionBody,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Edit a draft (409 for a published version: publish a new one instead)."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}",
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(self, id_or_key: str, version_id_or_label: str) -> JSON:
        """Delete a draft (409 for a published version: retire it instead)."""
        return self._t.request(
            method="DELETE", path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}"
        )

    def publish(
        self,
        id_or_key: str,
        version_id_or_label: str,
        body: m.PublishPolicyVersionBody | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Publish a draft. ``effective_at`` (epoch ms or ISO, default now) is when
        sign-ups must accept it and sign-ins re-ask per the policy's ``reaccept`` rule."""
        return self._t.request(
            method="POST",
            path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}/publish",
            body=body if body is not None else {},
            idempotency_key=idempotency_key,
        )

    def retire(
        self,
        id_or_key: str,
        version_id_or_label: str,
        *,
        idempotency_key: str | None = None,
    ) -> m.PolicyVersion:
        """Retire a published version: it no longer gates or is offered; acceptances stay."""
        return self._t.request(
            method="POST",
            path=f"/v1/policies/{id_or_key}/versions/{version_id_or_label}/retire",
            idempotency_key=idempotency_key,
        )


class _PolicySettings:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.PolicySettings:
        """Policy settings: the optional ``pol`` session claim."""
        return self._t.request(method="GET", path="/v1/instance/policy_settings")

    def update(self, body: m.UpdatePolicySettingsBody) -> m.PolicySettings:
        """Turn the ``pol`` session claim on or off (tokens minted after the change; it
        can take 30 seconds to apply everywhere)."""
        return self._t.request(method="PATCH", path="/v1/instance/policy_settings", body=body)


class PolicySource:
    """The external policy source (Atlas policy source protocol v1): serve your policies
    from a CMS or your own service. Atlas fetches ``GET {endpoint_url}/policies`` signed
    with the source's signing secret (``verify_policy_feed_request`` checks it) and your
    source tells Atlas about changes with a signed event (``sign_policy_source_event``).
    ``signing_secret`` is write-only.
    """

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.PolicySource:
        """Endpoint, sync mode, the webhook URL to give the source and the last sync."""
        return self._t.request(method="GET", path="/v1/instance/policy_source")

    def update(self, body: m.UpdatePolicySourceBody) -> m.PolicySource:
        """Configure the source; only the fields sent change and ``None`` clears. Enabling
        needs ``endpoint_url`` and ``signing_secret``."""
        return self._t.request(method="PUT", path="/v1/instance/policy_source", body=body)

    def delete(self) -> m.PolicySource:
        """Disconnect the source (its policies and their history stay; they stop syncing)."""
        return self._t.request(method="DELETE", path="/v1/instance/policy_source")

    def test(self) -> m.PolicySourceTest:
        """A signed fetch of the feed, validated but not stored."""
        return self._t.request(method="POST", path="/v1/instance/policy_source/test")

    def sync(self) -> m.PolicySourceSync:
        """Fetch the feed now and store it. A published version whose content changed at
        the source is refused: publish a new version there."""
        return self._t.request(method="POST", path="/v1/instance/policy_source/sync")

    def list_deliveries(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        kind: str | None = None,
        status: str | None = None,
    ) -> CursorPage:
        """The delivery log: every fetch, test, poll and inbound event, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/instance/policy_source/deliveries",
            query=_q(limit=limit, starting_after=starting_after, kind=kind, status=status),
        )


# --------------------------------------------------------------------------- #
# Integrator platform                                                          #
# --------------------------------------------------------------------------- #


class Whoami:
    """``GET /v1/whoami``: introspect the key this client authenticates with (kind, scopes,
    expiry, owner, instance)."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> JSON:
        return self._t.request(method="GET", path="/v1/whoami")


class SecretKeys:
    """``/v1/secret_keys``: mint, list, rotate and revoke the instance's secret keys. A new
    secret is revealed exactly once (``secret``, or ``sealed_secret`` when
    ``secret_recipient`` is sent; open it with :class:`SealedBox`). Keys default to a
    one-year expiry, belong to their creator (``owner``) and can be locked to browser
    ``allowed_origins``."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self,
        body: m.CreateSecretKeyBody,
        *,
        idempotency_key: str | None = None,
        dry_run: bool = False,
    ) -> m.SecretKey:
        return self._t.request(
            method="POST",
            path="/v1/secret_keys",
            body=body,
            idempotency_key=idempotency_key,
            query=_dry(dry_run),
        )

    def list(self, *, metadata: dict[str, Any] | None = None) -> ListPage:
        return self._t.request(method="GET", path="/v1/secret_keys", query=_meta(metadata) or None)

    def get(self, key_id: str) -> m.SecretKey:
        return self._t.request(method="GET", path=f"/v1/secret_keys/{_enc(key_id)}")

    def update(self, key_id: str, body: m.UpdateSecretKeyBody) -> m.SecretKey:
        return self._t.request(method="PATCH", path=f"/v1/secret_keys/{_enc(key_id)}", body=body)

    def rotate(
        self,
        key_id: str,
        body: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> m.SecretKey:
        """A new key with the same scopes; the old one keeps working for ``overlap_seconds``
        (default 72 h, ``0`` revokes it now)."""
        return self._t.request(
            method="POST",
            path=f"/v1/secret_keys/{_enc(key_id)}/rotate",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, key_id: str) -> m.SecretKey:
        return self._t.request(method="POST", path=f"/v1/secret_keys/{_enc(key_id)}/revoke")


class Keys:
    """Keys across kinds, the operator document, token exchange and leaked-key revocation."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, kind: str | None = None) -> ListPage:
        """``GET /v1/keys``: every credential on the instance, standard shape."""
        return self._t.request(method="GET", path="/v1/keys", query=_q(kind=kind))

    def revoke_leaked(self, body: dict[str, Any]) -> JSON:
        """``POST /v1/keys/revoke_leaked``: revoke leaked Atlas credentials. Needs no key
        (the leaked secret is the proof)."""
        return self._t.request(method="POST", path="/v1/keys/revoke_leaked", body=body)

    def operator(self) -> JSON:
        """``GET /v1/operator``: where the operator device flow and token exchange live."""
        return self._t.request(method="GET", path="/v1/operator")

    def exchange_token(self, body: dict[str, Any]) -> JSON:
        """``POST /v1/oauth/token`` (form-encoded): RFC 8693 token exchange or
        ``client_credentials``."""
        form = urlencode({k: v for k, v in body.items() if v is not None})
        return self._t.request(
            method="POST",
            path="/v1/oauth/token",
            content=form.encode("utf-8"),
            content_type="application/x-www-form-urlencoded",
        )

    def client_credentials(
        self,
        *,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
        audience: str | None = None,
    ) -> JSON:
        return self.exchange_token(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
                "audience": audience,
            }
        )

    def token_exchange(
        self,
        *,
        subject_token: str,
        subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
        resource: str | None = None,
        scope: str | None = None,
        audience: str | None = None,
    ) -> JSON:
        return self.exchange_token(
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": subject_token,
                "subject_token_type": subject_token_type,
                "resource": resource,
                "scope": scope,
                "audience": audience,
            }
        )


class _PartnerLinkRequests:
    """Partner link requests: a partner asks, the owner approves or denies, and Atlas delivers
    the credentials to the partner's callback (the owner never sees the secret)."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        direction: Literal["inbound", "outbound"] | None = None,
        status: str | Sequence[str] | None = None,
    ) -> ListPage:
        return self._t.request(
            method="GET",
            path="/v1/partner_links/requests",
            query=_q(direction=direction, status=_csv(status)),
        )

    def get(self, request_id: str) -> m.PartnerLinkRequest:
        return self._t.request(method="GET", path=f"/v1/partner_links/requests/{_enc(request_id)}")

    def approve(
        self, request_id: str, body: m.ApprovePartnerLinkRequestBody | None = None
    ) -> m.PartnerLinkRequestApproval:
        """Approve: Atlas creates the link and delivers its credentials to the partner,
        signed. ``scopes`` may narrow the request, never widen it."""
        return self._t.request(
            method="POST",
            path=f"/v1/partner_links/requests/{_enc(request_id)}/approve",
            body=body if body is not None else {},
        )

    def deny(self, request_id: str) -> m.PartnerLinkRequest:
        return self._t.request(
            method="POST", path=f"/v1/partner_links/requests/{_enc(request_id)}/deny"
        )


class _OutboundPartnerLinks:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/partner_links/outbound")

    def save(self, partner: str, body: dict[str, Any]) -> JSON:
        return self._t.request(
            method="PUT", path=f"/v1/partner_links/outbound/{_enc(partner)}", body=body
        )

    def test(self, partner: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/partner_links/outbound/{_enc(partner)}/test"
        )

    def remove(self, partner: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/partner_links/outbound/{_enc(partner)}")

    def request(self, partner: str, body: dict[str, Any]) -> JSON:
        """Ask a partner for a link; its credentials arrive by themselves once the partner
        approves. ``body``: ``scopes``, optionally ``resource``, ``base_url``, ``token_url``,
        ``name``."""
        return self._t.request(
            method="POST",
            path=f"/v1/partner_links/outbound/{_enc(partner)}/request",
            body=body,
        )


class PartnerLinks:
    """``/v1/partner_links``: scoped credentials granted to a partner product, the requests
    partners make, and the outbound links this instance holds into partner products."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.requests = _PartnerLinkRequests(transport)
        self.outbound = _OutboundPartnerLinks(transport)

    def create(self, body: dict[str, Any], *, idempotency_key: str | None = None) -> m.PartnerLink:
        """Create a link by hand (the secret is returned once). Prefer approving a partner's
        request: there is no secret to hand over. ``body``: ``partner``, ``scopes``, optional
        ``name``, ``expires_at``, ``cert_fingerprints``."""
        return self._t.request(
            method="POST", path="/v1/partner_links", body=body, idempotency_key=idempotency_key
        )

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/partner_links")

    def get(self, link_id: str) -> m.PartnerLink:
        return self._t.request(method="GET", path=f"/v1/partner_links/{_enc(link_id)}")

    def set_certificates(self, link_id: str, cert_fingerprints: Sequence[str]) -> m.PartnerLink:
        """Lock a link to client certificates (mTLS); an empty list removes the lock."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/partner_links/{_enc(link_id)}",
            body={"cert_fingerprints": list(cert_fingerprints)},
        )

    def rotate_secret(self, link_id: str) -> m.PartnerLink:
        return self._t.request(
            method="POST", path=f"/v1/partner_links/{_enc(link_id)}/rotate_secret"
        )

    def revoke(self, link_id: str) -> m.PartnerLink:
        return self._t.request(method="DELETE", path=f"/v1/partner_links/{_enc(link_id)}")


class AtlasIdGrants:
    """``/v1/atlas_id_apps`` on the secret-key surface: the Sign in with Atlas apps this
    instance manages and their grants."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_apps(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/atlas_id_apps")

    def lookup(self, app_id: str, email: str) -> ListPage:
        """Is this verified email a user of the app? An empty list otherwise."""
        return self._t.request(
            method="GET", path=f"/v1/atlas_id_apps/{_enc(app_id)}/users", query={"email": email}
        )

    def preflight(self, app_id: str) -> m.AtlasIdAppPreflightDetail:
        """The setup check of an app this instance manages (``diagnostics:read`` is enough)."""
        return self._t.request(method="GET", path=f"/v1/atlas_id_apps/{_enc(app_id)}/preflight")

    def revoke_grant(self, app_id: str, grant_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"/v1/atlas_id_apps/{_enc(app_id)}/grants/{_enc(grant_id)}"
        )


class _PrivacyOrchestrator:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> JSON:
        return self._t.request(method="GET", path="/v1/instance/privacy_orchestrator")

    def set(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="PUT", path="/v1/instance/privacy_orchestrator", body=body)

    def delete(self) -> JSON:
        return self._t.request(method="DELETE", path="/v1/instance/privacy_orchestrator")


class Privacy:
    """The privacy-executor client: discovery, subject lookup, and idempotent privacy
    requests (restriction / deletion / export) a data-rights orchestrator executes; plus the
    instance's orchestrator setting."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.orchestrator = _PrivacyOrchestrator(transport)

    def discover(self) -> JSON:
        return self._t.request(method="GET", path="/v1/privacy")

    def preset(self, preset_id: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/privacy/presets/{_enc(preset_id)}")

    def lookup(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="POST", path="/v1/privacy/lookup", body=body)

    def create_request(self, body: dict[str, Any], *, idempotency_key: str | None = None) -> JSON:
        """Open a privacy request. Always send an ``Idempotency-Key`` (16-255 characters)."""
        return self._t.request(
            method="POST",
            path="/v1/privacy/requests",
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_request(self, request_id: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/privacy/requests/{_enc(request_id)}")

    def cancel_request(self, request_id: str, *, idempotency_key: str | None = None) -> JSON:
        return self._t.request(
            method="POST",
            path=f"/v1/privacy/requests/{_enc(request_id)}/cancel",
            idempotency_key=idempotency_key,
        )


class Integrations:
    """``/v1/instance/integrations/{product}``: identity integrations (a product that trusts
    Atlas sessions), their deliveries, the server-side token mint
    (``get_token(session_id, for_=...)``) and the integration card."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/instance/integrations")

    def get(self, product: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/instance/integrations/{_enc(product)}")

    def set(self, product: str, body: dict[str, Any], *, dry_run: bool = False) -> JSON:
        return self._t.request(
            method="PUT",
            path=f"/v1/instance/integrations/{_enc(product)}",
            body=body,
            query=_dry(dry_run),
        )

    def delete(self, product: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/instance/integrations/{_enc(product)}")

    def deliveries(
        self,
        product: str,
        *,
        trace: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        """The integration's outbound deliveries; ``trace`` filters by W3C trace id."""
        return self._t.request(
            method="GET",
            path=f"/v1/instance/integrations/{_enc(product)}/deliveries",
            query=_q(trace=trace, limit=limit, starting_after=starting_after),
        )

    def events_secret(self, product: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/instance/integrations/{_enc(product)}/events_secret"
        )

    def atlas_id_tokens(self, product: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/instance/integrations/{_enc(product)}/atlas_id_tokens"
        )

    def get_token(
        self, session_id: str, for_: str, *, audience_hint: str | None = None
    ) -> m.SessionToken:
        """Mint an integration token for a session on the server (``getToken({for})``)."""
        return self._t.request(
            method="POST",
            path=f"/v1/sessions/{_enc(session_id)}/integration_tokens/{_enc(for_)}",
            body={"audience_hint": audience_hint} if audience_hint else None,
        )

    def report_verify_error(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="POST", path="/v1/integrations/verify_errors", body=body)

    def card(self, product: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/integrations/{_enc(product)}/card")

    def card_revoke_sessions(self, product: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/integrations/{_enc(product)}/card/actions/revoke_sessions"
        )

    def public_instance(self, instance_id: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/public/instances/{_enc(instance_id)}")


class _StatusSubscription:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> JSON:
        return self._t.request(method="GET", path="/v1/instance/status_subscription")

    def set(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="PUT", path="/v1/instance/status_subscription", body=body)

    def delete(self) -> JSON:
        return self._t.request(method="DELETE", path="/v1/instance/status_subscription")

    def rotate_feed(self) -> JSON:
        return self._t.request(method="POST", path="/v1/instance/status_subscription/rotate_feed")


class _StatusDependencies:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/instance/status_dependencies")

    def create(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="POST", path="/v1/instance/status_dependencies", body=body)

    def get(self, dependency_id: str) -> JSON:
        return self._t.request(
            method="GET", path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}"
        )

    def update(self, dependency_id: str, body: dict[str, Any]) -> JSON:
        return self._t.request(
            method="PATCH",
            path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}",
            body=body,
        )

    def delete(self, dependency_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}"
        )

    def refresh(self, dependency_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/instance/status_dependencies/{_enc(dependency_id)}/refresh"
        )


class Status:
    """The Atlas status feed, this instance's subscription to it, its incidents and the
    upstream status dependencies it watches. Webhook events: ``status.incident.created`` /
    ``.updated`` / ``.resolved``."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.subscription = _StatusSubscription(transport)
        self.dependencies = _StatusDependencies(transport)

    def get(self, *, region: str | None = None) -> JSON:
        """``GET /v1/status`` (Statuspage-compatible); ``region`` narrows it."""
        return self._t.request(method="GET", path="/v1/status", query=_q(region=region))

    def incidents(self, *, open: bool | None = None, limit: int | None = None) -> ListPage:
        return self._t.request(
            method="GET", path="/v1/instance/status_incidents", query=_q(open=open, limit=limit)
        )


class Notices:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, all: bool | None = None) -> ListPage:
        return self._t.request(method="GET", path="/v1/instance/notices", query=_q(all=all))

    def acknowledge(self, notice_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/instance/notices/{_enc(notice_id)}/acknowledge"
        )


class SecurityAdvisories:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/security_advisories")

    def acknowledge(self, advisory_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/security_advisories/{_enc(advisory_id)}/acknowledge"
        )

    def list_public(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/public/security_advisories")


class AuditExports:
    """Audit-log exports to your SIEM as CloudEvents over a signed webhook."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/audit_exports")

    def get(self, export_id: str) -> JSON:
        return self._t.request(method="GET", path=f"/v1/audit_exports/{_enc(export_id)}")

    def create(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="POST", path="/v1/audit_exports", body=body)

    def update(self, export_id: str, body: dict[str, Any]) -> JSON:
        return self._t.request(
            method="PATCH", path=f"/v1/audit_exports/{_enc(export_id)}", body=body
        )

    def delete(self, export_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/audit_exports/{_enc(export_id)}")

    def test(self, export_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/audit_exports/{_enc(export_id)}/test")

    def rotate_secret(self, export_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/audit_exports/{_enc(export_id)}/rotate_secret"
        )


class SubProcessors:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/instance/sub_processors")


class Entitlements:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> JSON:
        return self._t.request(method="GET", path="/v1/entitlements")


class IntegrationHealth:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> JSON:
        return self._t.request(method="GET", path="/v1/integration-health")

    def providers(self) -> JSON:
        return self._t.request(method="GET", path="/v1/integration-health/providers")


class Embed:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, *, instance: str | None = None) -> JSON:
        return self._t.request(method="GET", path="/v1/embed", query=_q(instance=instance))

    def csp(self) -> JSON:
        return self._t.request(method="GET", path="/v1/instance/csp")


class OpenApi:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def diff(self, *, since: str | None = None, surface: str | None = None) -> JSON:
        """What changed in the API since a date (``x-since`` ledger)."""
        return self._t.request(
            method="GET", path="/v1/openapi/diff", query=_q(since=since, surface=surface)
        )

    def api_catalog(self) -> JSON:
        return self._t.request(method="GET", path="/.well-known/api-catalog")


class DeliveryHealth:
    """Delivery health of the instance's outbound targets (webhooks, back-channel logout
    receivers, referral connections, integrations) and their alert contacts."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self, *, kind: str | None = None) -> JSON:
        return self._t.request(method="GET", path="/v1/delivery_health", query=_q(kind=kind))

    def set_alert_contacts(self, kind: str, target_id: str, alert_contacts: Sequence[str]) -> JSON:
        return self._t.request(
            method="PUT",
            path=f"/v1/delivery_health/{_enc(kind)}/{_enc(target_id)}/alert_contacts",
            body={"alert_contacts": list(alert_contacts)},
        )


class Meta:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def egress_ips(self) -> JSON:
        """The IP addresses Atlas sends webhooks and other outbound calls from."""
        return self._t.request(method="GET", path="/v1/meta/egress_ips")


class PlatformWhoami:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> JSON:
        return self._t.request(method="GET", path="/v1/platform/whoami")


class PlatformKeys:
    """``/v1/platform/keys``: the platform's own keys (``owner``, ``expires_at``,
    ``allowed_origins``)."""

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, kind: str | None = None) -> ListPage:
        return self._t.request(method="GET", path="/v1/platform/keys", query=_q(kind=kind))

    def create(self, body: dict[str, Any]) -> m.PlatformKey:
        return self._t.request(method="POST", path="/v1/platform/keys", body=body)

    def update(self, key_id: str, body: dict[str, Any]) -> m.PlatformKey:
        return self._t.request(method="PATCH", path=f"/v1/platform/keys/{_enc(key_id)}", body=body)

    def revoke(self, key_id: str) -> m.PlatformKey:
        return self._t.request(method="POST", path=f"/v1/platform/keys/{_enc(key_id)}/revoke")


class _PlatformAuditStreams:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/platform/audit_streams")

    def create(self, body: dict[str, Any]) -> JSON:
        return self._t.request(method="POST", path="/v1/platform/audit_streams", body=body)

    def update(self, stream_id: str, body: dict[str, Any]) -> JSON:
        return self._t.request(
            method="PATCH", path=f"/v1/platform/audit_streams/{_enc(stream_id)}", body=body
        )

    def delete(self, stream_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"/v1/platform/audit_streams/{_enc(stream_id)}"
        )

    def test(self, stream_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/platform/audit_streams/{_enc(stream_id)}/test"
        )


class PlatformAudit:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.streams = _PlatformAuditStreams(transport)

    def list(
        self,
        *,
        action: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> ListPage:
        return self._t.request(
            method="GET",
            path="/v1/platform/audit_logs",
            query=_q(action=action, limit=limit, starting_after=starting_after),
        )
