"""Synchronous resource namespaces — the method↔endpoint map for the BAPI.

Each class wraps the shared :class:`_SyncTransport` and turns a call into a
single request naming a method, a path, and its shapes. The surface mirrors the
official TypeScript SDK (``@atlas/backend``) namespace-for-namespace.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from . import models as m
from ._transport import _SyncTransport
from ._types import JSON, CursorPage, DeletedObject, ListPage


def _q(**kwargs: Any) -> dict[str, Any]:
    """Build a query mapping, dropping keys whose value is ``None``."""
    return {k: v for k, v in kwargs.items() if v is not None}


class Users:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        return self._t.request(
            method="GET",
            path="/v1/users",
            query=_q(limit=limit, starting_after=starting_after),
        )

    def get(self, user_id: str) -> m.User:
        return self._t.request(method="GET", path=f"/v1/users/{user_id}")

    def create(
        self, body: m.CreateUserBody, *, idempotency_key: str | None = None
    ) -> m.User:
        return self._t.request(
            method="POST", path="/v1/users", body=body, idempotency_key=idempotency_key
        )

    def update(self, user_id: str, body: m.UpdateUserBody) -> m.User:
        return self._t.request(method="PATCH", path=f"/v1/users/{user_id}", body=body)

    def replace_metadata(
        self, user_id: str, body: m.ReplaceUserMetadataBody
    ) -> m.User:
        return self._t.request(
            method="PUT", path=f"/v1/users/{user_id}/metadata", body=body
        )

    def ban(self, user_id: str) -> m.User:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/ban")

    def unban(self, user_id: str) -> m.User:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/unban")

    def lock(
        self, user_id: str, *, duration_in_seconds: int | None = None
    ) -> m.User:
        return self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/lock",
            body=_q(duration_in_seconds=duration_in_seconds),
        )

    def unlock(self, user_id: str) -> m.User:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/unlock")

    def delete(self, user_id: str) -> DeletedObject:
        return self._t.request(method="DELETE", path=f"/v1/users/{user_id}")

    def reset_mfa(self, user_id: str) -> JSON:
        return self._t.request(method="POST", path=f"/v1/users/{user_id}/reset_mfa")

    def delete_mfa_factor(self, user_id: str, factor_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"/v1/users/{user_id}/mfa/{factor_id}"
        )

    def list_sessions(self, user_id: str) -> ListPage:
        return self._t.request(method="GET", path=f"/v1/users/{user_id}/sessions")

    def revoke_sessions(self, user_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/users/{user_id}/sessions/revoke"
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

    def get_oauth_access_token(
        self, user_id: str, provider: str
    ) -> m.OAuthAccessToken:
        return self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/oauth_access_tokens/{provider}",
        )


class _OrgMemberships:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, org_id: str) -> JSON:
        return self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/memberships"
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
        return self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/invitations"
        )

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
        return self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/domains"
        )

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

    def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
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
        return self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}", body=body
        )

    def delete(self, org_id: str) -> DeletedObject:
        return self._t.request(method="DELETE", path=f"/v1/organizations/{org_id}")

    def update_metadata(
        self, org_id: str, body: m.ReplaceOrganizationMetadataBody
    ) -> m.Organization:
        return self._t.request(
            method="PUT", path=f"/v1/organizations/{org_id}/metadata", body=body
        )

    def update_policy(
        self, org_id: str, body: m.OrganizationPolicyPatch
    ) -> JSON:
        return self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/policy", body=body
        )


class Sessions:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, *, user_id: str) -> ListPage:
        return self._t.request(
            method="GET", path="/v1/sessions", query={"user_id": user_id}
        )

    def get(self, session_id: str) -> m.Session:
        return self._t.request(method="GET", path=f"/v1/sessions/{session_id}")

    def revoke(self, session_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/sessions/{session_id}/revoke"
        )


class Invitations:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
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
        return self._t.request(
            method="POST", path=f"/v1/invitations/{invitation_id}/revoke"
        )


class Roles:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/roles")

    def create(
        self, body: m.CreateRoleBody, *, idempotency_key: str | None = None
    ) -> m.Role:
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

    def delete(self, role_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/roles/{role_id}")


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
        return self._t.request(
            method="DELETE", path=f"/v1/webhook_endpoints/{endpoint_id}"
        )


class Webhooks:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport
        self.endpoints = _WebhookEndpoints(transport)

    def deliveries(self, endpoint_id: str) -> JSON:
        return self._t.request(
            method="GET", path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries"
        )


class _OAuthClientGrants:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self, client_id: str) -> ListPage:
        return self._t.request(
            method="GET", path=f"/v1/oauth_clients/{client_id}/grants"
        )

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
        return self._t.request(
            method="PATCH", path=f"/v1/oauth_clients/{client_id}", body=body
        )

    def rotate_secret(self, client_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/oauth_clients/{client_id}/rotate_secret"
        )

    def delete(self, client_id: str) -> JSON:
        return self._t.request(method="DELETE", path=f"/v1/oauth_clients/{client_id}")


class ResourceServers:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/resource_servers")

    def get(self, server_id: str) -> m.ResourceServer:
        return self._t.request(
            method="GET", path=f"/v1/resource_servers/{server_id}"
        )

    def create(self, body: m.CreateResourceServerBody) -> m.ResourceServer:
        return self._t.request(
            method="POST", path="/v1/resource_servers", body=body
        )

    def update(
        self, server_id: str, body: m.UpdateResourceServerBody
    ) -> m.ResourceServer:
        return self._t.request(
            method="PATCH", path=f"/v1/resource_servers/{server_id}", body=body
        )

    def delete(self, server_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"/v1/resource_servers/{server_id}"
        )


class SsoConnections:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/sso_connections")

    def get(self, connection_id: str) -> m.SsoConnection:
        return self._t.request(
            method="GET", path=f"/v1/sso_connections/{connection_id}"
        )

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

    def update(
        self, connection_id: str, body: m.UpdateSsoConnectionBody
    ) -> m.SsoConnection:
        return self._t.request(
            method="PATCH", path=f"/v1/sso_connections/{connection_id}", body=body
        )

    def delete(self, connection_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"/v1/sso_connections/{connection_id}"
        )

    def saml_metadata(self, connection_id: str) -> m.SamlMetadata:
        return self._t.request(
            method="GET",
            path=f"/v1/sso_connections/{connection_id}/saml_metadata",
        )


class ScimTokens:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> ListPage:
        return self._t.request(method="GET", path="/v1/scim_tokens")

    def create(
        self, body: m.CreateScimTokenBody, *, idempotency_key: str | None = None
    ) -> JSON:
        return self._t.request(
            method="POST",
            path="/v1/scim_tokens",
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke(self, token_id: str) -> JSON:
        return self._t.request(
            method="POST", path=f"/v1/scim_tokens/{token_id}/revoke"
        )


class Domains:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(self) -> JSON:
        return self._t.request(method="GET", path="/v1/domains")

    def create(
        self, body: m.CreateDomainBody, *, idempotency_key: str | None = None
    ) -> JSON:
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


class _Restriction:
    """Allowlist and blocklist share an identical route shape."""

    def __init__(self, transport: _SyncTransport, path: str) -> None:
        self._t = transport
        self._path = path

    def list(self) -> JSON:
        return self._t.request(method="GET", path=self._path)

    def add(self, identifier: str) -> JSON:
        return self._t.request(
            method="POST", path=self._path, body={"identifier": identifier}
        )

    def remove(self, identifier_id: str) -> JSON:
        return self._t.request(
            method="DELETE", path=f"{self._path}/{identifier_id}"
        )


class AttackProtection:
    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(self) -> m.AttackProtection:
        return self._t.request(method="GET", path="/v1/attack_protection")

    def update(self, body: m.UpdateAttackProtectionBody) -> m.AttackProtection:
        return self._t.request(
            method="PATCH", path="/v1/attack_protection", body=body
        )


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
        return self._t.request(
            method="POST", path=f"/v1/actor_tokens/{token_id}/revoke"
        )


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
    ) -> CursorPage:
        return self._t.request(
            method="GET",
            path="/v1/audit_logs",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                actor_id=actor_id,
                action=action,
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
