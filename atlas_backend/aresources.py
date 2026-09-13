"""Asynchronous resource namespaces — the async peer of :mod:`resources`.

Same method↔endpoint map, same shapes, over an :class:`httpx.AsyncClient`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from . import models as m
from ._transport import _AsyncTransport
from ._types import JSON, CursorPage, DeletedObject, ListPage


def _q(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}


class AsyncUsers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        return await self._t.request(
            method="GET",
            path="/v1/users",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(self, user_id: str) -> m.User:
        return await self._t.request(method="GET", path=f"/v1/users/{user_id}")

    async def create(
        self, body: m.CreateUserBody, *, idempotency_key: str | None = None
    ) -> m.User:
        return await self._t.request(
            method="POST", path="/v1/users", body=body, idempotency_key=idempotency_key
        )

    async def update(self, user_id: str, body: m.UpdateUserBody) -> m.User:
        return await self._t.request(
            method="PATCH", path=f"/v1/users/{user_id}", body=body
        )

    async def replace_metadata(
        self, user_id: str, body: m.ReplaceUserMetadataBody
    ) -> m.User:
        return await self._t.request(
            method="PUT", path=f"/v1/users/{user_id}/metadata", body=body
        )

    async def ban(self, user_id: str) -> m.User:
        return await self._t.request(method="POST", path=f"/v1/users/{user_id}/ban")

    async def unban(self, user_id: str) -> m.User:
        return await self._t.request(method="POST", path=f"/v1/users/{user_id}/unban")

    async def lock(
        self, user_id: str, *, duration_in_seconds: int | None = None
    ) -> m.User:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/lock",
            body=_q(duration_in_seconds=duration_in_seconds),
        )

    async def unlock(self, user_id: str) -> m.User:
        return await self._t.request(
            method="POST", path=f"/v1/users/{user_id}/unlock"
        )

    async def delete(self, user_id: str) -> DeletedObject:
        return await self._t.request(method="DELETE", path=f"/v1/users/{user_id}")

    async def reset_mfa(self, user_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/users/{user_id}/reset_mfa"
        )

    async def delete_mfa_factor(self, user_id: str, factor_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/users/{user_id}/mfa/{factor_id}"
        )

    async def list_sessions(self, user_id: str) -> ListPage:
        return await self._t.request(
            method="GET", path=f"/v1/users/{user_id}/sessions"
        )

    async def revoke_sessions(self, user_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/users/{user_id}/sessions/revoke"
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

    async def set_primary_email(
        self, user_id: str, email_id: str
    ) -> m.EmailAddress:
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{user_id}/email_addresses/{email_id}/primary",
        )

    async def get_oauth_access_token(
        self, user_id: str, provider: str
    ) -> m.OAuthAccessToken:
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{user_id}/oauth_access_tokens/{provider}",
        )


class _AsyncOrgMemberships:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, org_id: str) -> JSON:
        return await self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/memberships"
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
        return await self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/invitations"
        )

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
        return await self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}/domains"
        )

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

    async def list(
        self, *, limit: int | None = None, starting_after: str | None = None
    ) -> CursorPage:
        return await self._t.request(
            method="GET",
            path="/v1/organizations",
            query=_q(limit=limit, starting_after=starting_after),
        )

    async def get(self, org_id: str) -> m.Organization:
        return await self._t.request(
            method="GET", path=f"/v1/organizations/{org_id}"
        )

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

    async def update(
        self, org_id: str, body: m.UpdateOrganizationBody
    ) -> m.Organization:
        return await self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}", body=body
        )

    async def delete(self, org_id: str) -> DeletedObject:
        return await self._t.request(
            method="DELETE", path=f"/v1/organizations/{org_id}"
        )

    async def update_metadata(
        self, org_id: str, body: m.ReplaceOrganizationMetadataBody
    ) -> m.Organization:
        return await self._t.request(
            method="PUT", path=f"/v1/organizations/{org_id}/metadata", body=body
        )

    async def update_policy(
        self, org_id: str, body: m.OrganizationPolicyPatch
    ) -> JSON:
        return await self._t.request(
            method="PATCH", path=f"/v1/organizations/{org_id}/policy", body=body
        )


class AsyncSessions:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, *, user_id: str) -> ListPage:
        return await self._t.request(
            method="GET", path="/v1/sessions", query={"user_id": user_id}
        )

    async def get(self, session_id: str) -> m.Session:
        return await self._t.request(method="GET", path=f"/v1/sessions/{session_id}")

    async def revoke(self, session_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/sessions/{session_id}/revoke"
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
        return await self._t.request(
            method="POST", path=f"/v1/invitations/{invitation_id}/revoke"
        )


class AsyncRoles:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/roles")

    async def create(
        self, body: m.CreateRoleBody, *, idempotency_key: str | None = None
    ) -> m.Role:
        return await self._t.request(
            method="POST", path="/v1/roles", body=body, idempotency_key=idempotency_key
        )

    async def update(self, role_id: str, body: m.UpdateRoleBody) -> m.Role:
        return await self._t.request(
            method="PATCH", path=f"/v1/roles/{role_id}", body=body
        )

    async def set_permissions(self, role_id: str, permissions: Sequence[str]) -> JSON:
        return await self._t.request(
            method="PUT",
            path=f"/v1/roles/{role_id}/permissions",
            body={"permissions": permissions},
        )

    async def delete(self, role_id: str) -> JSON:
        return await self._t.request(method="DELETE", path=f"/v1/roles/{role_id}")


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
        return await self._t.request(
            method="DELETE", path=f"/v1/webhook_endpoints/{endpoint_id}"
        )


class AsyncWebhooks:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport
        self.endpoints = _AsyncWebhookEndpoints(transport)

    async def deliveries(self, endpoint_id: str) -> JSON:
        return await self._t.request(
            method="GET", path=f"/v1/webhook_endpoints/{endpoint_id}/deliveries"
        )


class _AsyncOAuthClientGrants:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self, client_id: str) -> ListPage:
        return await self._t.request(
            method="GET", path=f"/v1/oauth_clients/{client_id}/grants"
        )

    async def create(
        self, client_id: str, body: m.CreateGrantBody
    ) -> m.ClientGrant:
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
        return await self._t.request(
            method="GET", path=f"/v1/oauth_clients/{client_id}"
        )

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

    async def update(
        self, client_id: str, body: m.UpdateOAuthClientBody
    ) -> m.OAuthClient:
        return await self._t.request(
            method="PATCH", path=f"/v1/oauth_clients/{client_id}", body=body
        )

    async def rotate_secret(self, client_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/oauth_clients/{client_id}/rotate_secret"
        )

    async def delete(self, client_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/oauth_clients/{client_id}"
        )


class AsyncResourceServers:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/resource_servers")

    async def get(self, server_id: str) -> m.ResourceServer:
        return await self._t.request(
            method="GET", path=f"/v1/resource_servers/{server_id}"
        )

    async def create(self, body: m.CreateResourceServerBody) -> m.ResourceServer:
        return await self._t.request(
            method="POST", path="/v1/resource_servers", body=body
        )

    async def update(
        self, server_id: str, body: m.UpdateResourceServerBody
    ) -> m.ResourceServer:
        return await self._t.request(
            method="PATCH", path=f"/v1/resource_servers/{server_id}", body=body
        )

    async def delete(self, server_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/resource_servers/{server_id}"
        )


class AsyncSsoConnections:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/sso_connections")

    async def get(self, connection_id: str) -> m.SsoConnection:
        return await self._t.request(
            method="GET", path=f"/v1/sso_connections/{connection_id}"
        )

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

    async def update(
        self, connection_id: str, body: m.UpdateSsoConnectionBody
    ) -> m.SsoConnection:
        return await self._t.request(
            method="PATCH", path=f"/v1/sso_connections/{connection_id}", body=body
        )

    async def delete(self, connection_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/sso_connections/{connection_id}"
        )

    async def saml_metadata(self, connection_id: str) -> m.SamlMetadata:
        return await self._t.request(
            method="GET",
            path=f"/v1/sso_connections/{connection_id}/saml_metadata",
        )


class AsyncScimTokens:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/scim_tokens")

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
        return await self._t.request(
            method="POST", path=f"/v1/scim_tokens/{token_id}/revoke"
        )


class AsyncDomains:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> JSON:
        return await self._t.request(method="GET", path="/v1/domains")

    async def create(
        self, body: m.CreateDomainBody, *, idempotency_key: str | None = None
    ) -> JSON:
        return await self._t.request(
            method="POST",
            path="/v1/domains",
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verify(self, domain_id: str) -> JSON:
        return await self._t.request(
            method="POST", path=f"/v1/domains/{domain_id}/verify"
        )

    async def delete(self, domain_id: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/domains/{domain_id}"
        )


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

    async def decide(
        self, entry_id: str, body: m.DecideWaitlistBody
    ) -> m.WaitlistEntry:
        return await self._t.request(
            method="POST",
            path=f"/v1/waitlist_entries/{entry_id}/decide",
            body=body,
        )


class _AsyncRestriction:
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
        return await self._t.request(
            method="DELETE", path=f"{self._path}/{identifier_id}"
        )


class AsyncAttackProtection:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(self) -> m.AttackProtection:
        return await self._t.request(method="GET", path="/v1/attack_protection")

    async def update(
        self, body: m.UpdateAttackProtectionBody
    ) -> m.AttackProtection:
        return await self._t.request(
            method="PATCH", path="/v1/attack_protection", body=body
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
        return await self._t.request(
            method="POST", path=f"/v1/actor_tokens/{token_id}/revoke"
        )


class AsyncSignInTokens:
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
    ) -> CursorPage:
        return await self._t.request(
            method="GET",
            path="/v1/audit_logs",
            query=_q(
                limit=limit,
                starting_after=starting_after,
                actor_id=actor_id,
                action=action,
            ),
        )


class AsyncJwtTemplates:
    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(self) -> ListPage:
        return await self._t.request(method="GET", path="/v1/jwt_templates")

    async def get(self, name: str) -> m.JwtTemplate:
        return await self._t.request(
            method="GET", path=f"/v1/jwt_templates/{name}"
        )

    async def create(self, body: m.CreateJwtTemplateBody) -> m.JwtTemplate:
        return await self._t.request(
            method="POST", path="/v1/jwt_templates", body=body
        )

    async def update(self, name: str, claims: dict[str, str]) -> m.JwtTemplate:
        return await self._t.request(
            method="PATCH",
            path=f"/v1/jwt_templates/{name}",
            body={"claims": claims},
        )

    async def delete(self, name: str) -> JSON:
        return await self._t.request(
            method="DELETE", path=f"/v1/jwt_templates/{name}"
        )
