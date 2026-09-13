"""The typed management clients for the Atlas Backend API.

:class:`AtlasClient` is the secret-key surface — the Python peer of the official
TypeScript SDK's ``createAtlasClient``. Each namespace is one attribute handing
the shared, config-bound transport to a resource class, so this file reads as a
table of contents for the whole surface. :class:`AsyncAtlasClient` is the same
surface over ``asyncio``.
"""

from __future__ import annotations

from types import TracebackType

import httpx

from . import aresources as ar
from . import resources as r
from ._transport import DEFAULT_BASE_URL, _AsyncTransport, _SyncTransport


class AtlasClient:
    """Synchronous Backend API client.

    Args:
        secret_key: The instance secret key (``sk_...``). Sent as
            ``Authorization: Bearer <key>`` on every request; never logged,
            never placed in a URL.
        base_url: Base URL of the instance's Backend API. Defaults to
            ``https://api.atlas.dev``. Trailing slashes are tolerated.
        timeout: Per-request timeout in seconds.
        http_client: An optional pre-configured :class:`httpx.Client` (for
            connection pooling, proxies, retries). One is created if omitted.
    """

    def __init__(
        self,
        secret_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not secret_key:
            raise ValueError("AtlasClient requires a secret_key.")
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)
        transport = _SyncTransport(secret_key, base_url, self._http)

        self.users = r.Users(transport)
        self.sessions = r.Sessions(transport)
        self.organizations = r.Organizations(transport)
        self.roles = r.Roles(transport)
        self.permissions = r.Permissions(transport)
        self.oauth_clients = r.OAuthClients(transport)
        self.resource_servers = r.ResourceServers(transport)
        self.sso_connections = r.SsoConnections(transport)
        self.scim_tokens = r.ScimTokens(transport)
        self.domains = r.Domains(transport)
        self.waitlist = r.Waitlist(transport)
        self.allowlist = r._Restriction(transport, "/v1/allowlist_identifiers")
        self.blocklist = r._Restriction(transport, "/v1/blocklist_identifiers")
        self.attack_protection = r.AttackProtection(transport)
        self.actor_tokens = r.ActorTokens(transport)
        self.invitations = r.Invitations(transport)
        self.webhooks = r.Webhooks(transport)
        self.sign_in_tokens = r.SignInTokens(transport)
        self.audit_logs = r.AuditLogs(transport)
        self.jwt_templates = r.JwtTemplates(transport)

    def close(self) -> None:
        """Close the underlying HTTP client, if this client created it."""
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> AtlasClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncAtlasClient:
    """Asynchronous Backend API client — the ``asyncio`` peer of :class:`AtlasClient`."""

    def __init__(
        self,
        secret_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not secret_key:
            raise ValueError("AsyncAtlasClient requires a secret_key.")
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)
        transport = _AsyncTransport(secret_key, base_url, self._http)

        self.users = ar.AsyncUsers(transport)
        self.sessions = ar.AsyncSessions(transport)
        self.organizations = ar.AsyncOrganizations(transport)
        self.roles = ar.AsyncRoles(transport)
        self.permissions = ar.AsyncPermissions(transport)
        self.oauth_clients = ar.AsyncOAuthClients(transport)
        self.resource_servers = ar.AsyncResourceServers(transport)
        self.sso_connections = ar.AsyncSsoConnections(transport)
        self.scim_tokens = ar.AsyncScimTokens(transport)
        self.domains = ar.AsyncDomains(transport)
        self.waitlist = ar.AsyncWaitlist(transport)
        self.allowlist = ar._AsyncRestriction(transport, "/v1/allowlist_identifiers")
        self.blocklist = ar._AsyncRestriction(transport, "/v1/blocklist_identifiers")
        self.attack_protection = ar.AsyncAttackProtection(transport)
        self.actor_tokens = ar.AsyncActorTokens(transport)
        self.invitations = ar.AsyncInvitations(transport)
        self.webhooks = ar.AsyncWebhooks(transport)
        self.sign_in_tokens = ar.AsyncSignInTokens(transport)
        self.audit_logs = ar.AsyncAuditLogs(transport)
        self.jwt_templates = ar.AsyncJwtTemplates(transport)

    async def aclose(self) -> None:
        """Close the underlying async HTTP client, if this client created it."""
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncAtlasClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
