"""The typed management clients for the Atlas Backend API.

:class:`AtlasClient` is the secret-key surface — the Python peer of the official
TypeScript SDK's ``createAtlasClient``. Each namespace is one attribute handing
the shared, config-bound transport to a resource class, so this file reads as a
table of contents for the whole surface. :class:`AsyncAtlasClient` is the same
surface over ``asyncio``.

:class:`AtlasPlatformClient` (and its async peer) is the platform-key (``psk_``)
surface: provisioning apps and instances, and registering Sign in with Atlas apps.
"""

from __future__ import annotations

from types import TracebackType

import httpx

from . import aresources as ar
from . import resources as r
from ._transport import (
    DEFAULT_BASE_URL,
    UnknownFieldsHook,
    _AsyncTransport,
    _SyncTransport,
)


class AtlasClient:
    """Synchronous Backend API client.

    Args:
        secret_key: The instance secret key (``sk_...``). Sent as
            ``Authorization: Bearer <key>`` on every request; never logged,
            never placed in a URL.
        base_url: Base URL of the instance's Backend API. Defaults to
            ``https://api.atlasauth.net``. Trailing slashes are tolerated.
        timeout: Per-request timeout in seconds.
        http_client: An optional pre-configured :class:`httpx.Client` (for
            connection pooling, proxies, retries). One is created if omitted.
        strict: ``True`` sends ``Atlas-Strict: true`` on every write, so a body
            field the endpoint does not accept is refused with
            ``422 UNKNOWN_FIELD`` instead of being ignored. ``False`` sends
            ``Atlas-Strict: false`` (opting out of an instance-wide strict
            default). ``None`` (the default) sends nothing.
        traceparent: A W3C ``traceparent`` sent on every request. Atlas carries its trace id
            onto the webhooks, back-channel logouts and privacy cases the call causes.
        on_unknown_fields: Called as ``hook(fields, method, path)`` when a write
            succeeded but Atlas ignored some body fields (the
            ``Atlas-Unknown-Fields`` response header). Without a hook the SDK
            logs a warning on the ``atlas_backend`` logger.
    """

    def __init__(
        self,
        secret_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        if not secret_key:
            raise ValueError("AtlasClient requires a secret_key.")
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)
        self._wire(
            _SyncTransport(
                secret_key,
                base_url,
                self._http,
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )

    def _wire(self, transport: _SyncTransport) -> None:
        self._transport = transport
        self.users = r.Users(transport)
        self.sessions = r.Sessions(transport)
        self.organizations = r.Organizations(transport)
        self.roles = r.Roles(transport)
        self.permissions = r.Permissions(transport)
        self.oauth_clients = r.OAuthClients(transport)
        self.resource_servers = r.ResourceServers(transport)
        self.app_roles = r.AppRoles(transport)
        self.oauth_initial_access_tokens = r.OAuthInitialAccessTokens(transport)
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
        self.actions = r.Actions(transport)
        self.action_gallery = r.ActionGallery(transport)
        self.action_templates = r.ActionTemplates(transport)
        self.api_keys = r.ApiKeys(transport)
        self.audit_events = r.AuditEvents(transport)
        self.better_auth_imports = r.BetterAuthImports(transport)
        self.better_auth_bridge = r.BetterAuthBridge(transport)
        self.billing = r.Billing(transport)
        self.policies = r.Policies(transport)
        self.policy_source = r.PolicySource(transport)
        self.bot_labels = r.BotLabels(transport)
        self.bot_signals = r.BotSignals(transport)
        self.branding = r.Branding(transport)
        self.captcha = r.Captcha(transport)
        self.config_changelog = r.ConfigChangelog(transport)
        self.connectors = r.Connectors(transport)
        self.data_subject_requests = r.DataSubjectRequests(transport)
        self.design = r.Design(transport)
        self.diagnostics = r.Diagnostics(transport)
        self.directory = r.Directory(transport)
        self.email_addresses = r.EmailAddresses(transport)
        self.email_templates = r.EmailTemplates(transport)
        self.entitlement_overrides = r.EntitlementOverrides(transport)
        self.events = r.Events(transport)
        self.fga = r.Fga(transport)
        self.openfga = r.OpenFga(transport)
        self.grants = r.Grants(transport)
        self.instance = r.Instance(transport)
        self.jobs = r.Jobs(transport)
        self.legacy_auth_connection = r.LegacyAuthConnection(transport)
        self.localizations = r.Localizations(transport)
        self.log_streams = r.LogStreams(transport)
        self.logout_notify_endpoints = r.LogoutNotifyEndpoints(transport)
        self.lti_platforms = r.LtiPlatforms(transport)
        self.m2m_tokens = r.M2mTokens(transport)
        self.machine_enrolment_tokens = r.MachineEnrolmentTokens(transport)
        self.machines = r.Machines(transport)
        self.managed_waf = r.ManagedWaf(transport)
        self.mcp = r.Mcp(transport)
        self.mcp_connector = r.McpConnector(transport)
        self.messaging_providers = r.MessagingProviders(transport)
        self.network_acls = r.NetworkAcls(transport)
        self.notifications = r.Notifications(transport)
        self.oauth_providers = r.OAuthProviders(transport)
        self.custom_oauth_providers = r.CustomOAuthProviders(transport)
        self.org_ldap_connections = r.OrgLdapConnections(transport)
        self.organization_settings_schema = r.OrganizationSettingsSchema(transport)
        self.pca = r.Pca(transport)
        self.radius_clients = r.RadiusClients(transport)
        self.rate_limit_policy = r.RateLimitPolicy(transport)
        self.redirect_urls = r.RedirectUrls(transport)
        self.risk_based_mfa = r.RiskBasedMfa(transport)
        self.scim_provisioning_targets = r.ScimProvisioningTargets(transport)
        self.session_exchange_apps = r.SessionExchangeApps(transport)
        self.sms_templates = r.SmsTemplates(transport)
        self.sso_onboarding = r.SsoOnboarding(transport)
        self.testing = r.Testing(transport)
        self.tickets = r.Tickets(transport)
        self.tokens = r.Tokens(transport)
        self.usage = r.Usage(transport)
        self.user_exports = r.UserExports(transport)
        self.user_imports = r.UserImports(transport)
        self.whoami = r.Whoami(transport)
        self.secret_keys = r.SecretKeys(transport)
        self.keys = r.Keys(transport)
        self.partner_links = r.PartnerLinks(transport)
        self.partner_platforms = r.PartnerPlatforms(transport)
        self.atlas_id_grants = r.AtlasIdGrants(transport)
        self.privacy = r.Privacy(transport)
        self.integrations = r.Integrations(transport)
        self.status = r.Status(transport)
        self.notices = r.Notices(transport)
        self.security_advisories = r.SecurityAdvisories(transport)
        self.audit_exports = r.AuditExports(transport)
        self.sub_processors = r.SubProcessors(transport)
        self.entitlements = r.Entitlements(transport)
        self.integration_health = r.IntegrationHealth(transport)
        self.embed = r.Embed(transport)
        self.openapi = r.OpenApi(transport)
        self.delivery_health = r.DeliveryHealth(transport)
        self.meta = r.Meta(transport)
        self.app_catalog = r.AppCatalog(transport)
        self.ldap_server_clients = r.LdapServerClients(transport)
        self.journeys = r.Journeys(transport)
        self.groups = r.Groups(transport)
        self.migrations = r.Migrations(transport)
        self.managed_grants = r.ManagedGrants(transport)
        self.least_privilege = r.LeastPrivilege(transport)
        self.flags = r.Flags(transport)
        self.mfa_factors = r.MfaFactors(transport)
        self.analytics = r.Analytics(transport)
        self.marketing = r.Marketing(transport)
        self.audit_event_schemas = r.AuditEventSchemas(transport)
        self.directory_pull_sources = r.DirectoryPullSources(transport)
        self.relay_agents = r.RelayAgents(transport)
        self.oauth_client_profiles = r.OauthClientProfiles(transport)
        self.passkey_api = r.PasskeyApi(transport)
        self.vc = r.Vc(transport)
        self.listen = r.Listen(transport)
        self.agent_registration = r.AgentRegistration(transport)
        self.agents = r.Agents(transport)
        self.agent_access_requests = r.AgentAccessRequests(transport)
        self.workflows = r.Workflows(transport)
        self.page_templates = r.PageTemplates(transport)
        self.service_connectors = r.ServiceConnectors(transport)
        self.desktop_mfa = r.DesktopMfa(transport)
        self.identity_verification = r.IdentityVerification(transport)
        self.iga = r.Iga(transport)
        self.scim_provisioning_presets = r.ScimProvisioningPresets(transport)
        self.vault = r.Vault(transport)
        self.connections = r.Connections(transport)
        self.ssf = r.Ssf(transport)
        self.network_zones = r.NetworkZones(transport)
        self.access_policies = r.AccessPolicies(transport)
        self.abac = r.Abac(transport)
        self.resources = r.Resources(transport)
        self.org_role_grants = r.OrgRoleGrants(transport)
        self.devices = r.Devices(transport)
        self.authz_decisions = r.AuthzDecisions(transport)
        self.policy_bundles = r.PolicyBundles(transport)
        self.proxy_apps = r.ProxyApps(transport)
        self.mcp_gateways = r.McpGateways(transport)

    def with_options(
        self,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> AtlasClient:
        """A copy of this client with per-call overrides, sharing its connection.

        ``atlas.with_options(strict=True).users.update(...)`` makes just that
        call strict. Closing the copy never closes the shared HTTP client.
        """
        clone = object.__new__(AtlasClient)
        clone._owns_client = False
        clone._http = self._http
        clone._wire(
            self._transport.with_options(
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )
        return clone

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
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        if not secret_key:
            raise ValueError("AsyncAtlasClient requires a secret_key.")
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)
        self._wire(
            _AsyncTransport(
                secret_key,
                base_url,
                self._http,
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )

    def _wire(self, transport: _AsyncTransport) -> None:
        self._transport = transport
        self.users = ar.AsyncUsers(transport)
        self.sessions = ar.AsyncSessions(transport)
        self.organizations = ar.AsyncOrganizations(transport)
        self.roles = ar.AsyncRoles(transport)
        self.permissions = ar.AsyncPermissions(transport)
        self.oauth_clients = ar.AsyncOAuthClients(transport)
        self.resource_servers = ar.AsyncResourceServers(transport)
        self.app_roles = ar.AsyncAppRoles(transport)
        self.oauth_initial_access_tokens = ar.AsyncOAuthInitialAccessTokens(transport)
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
        self.actions = ar.AsyncActions(transport)
        self.action_gallery = ar.AsyncActionGallery(transport)
        self.action_templates = ar.AsyncActionTemplates(transport)
        self.api_keys = ar.AsyncApiKeys(transport)
        self.audit_events = ar.AsyncAuditEvents(transport)
        self.better_auth_imports = ar.AsyncBetterAuthImports(transport)
        self.better_auth_bridge = ar.AsyncBetterAuthBridge(transport)
        self.billing = ar.AsyncBilling(transport)
        self.policies = ar.AsyncPolicies(transport)
        self.policy_source = ar.AsyncPolicySource(transport)
        self.bot_labels = ar.AsyncBotLabels(transport)
        self.bot_signals = ar.AsyncBotSignals(transport)
        self.branding = ar.AsyncBranding(transport)
        self.captcha = ar.AsyncCaptcha(transport)
        self.config_changelog = ar.AsyncConfigChangelog(transport)
        self.connectors = ar.AsyncConnectors(transport)
        self.data_subject_requests = ar.AsyncDataSubjectRequests(transport)
        self.design = ar.AsyncDesign(transport)
        self.diagnostics = ar.AsyncDiagnostics(transport)
        self.directory = ar.AsyncDirectory(transport)
        self.email_addresses = ar.AsyncEmailAddresses(transport)
        self.email_templates = ar.AsyncEmailTemplates(transport)
        self.entitlement_overrides = ar.AsyncEntitlementOverrides(transport)
        self.events = ar.AsyncEvents(transport)
        self.fga = ar.AsyncFga(transport)
        self.openfga = ar.AsyncOpenFga(transport)
        self.grants = ar.AsyncGrants(transport)
        self.instance = ar.AsyncInstance(transport)
        self.jobs = ar.AsyncJobs(transport)
        self.legacy_auth_connection = ar.AsyncLegacyAuthConnection(transport)
        self.localizations = ar.AsyncLocalizations(transport)
        self.log_streams = ar.AsyncLogStreams(transport)
        self.logout_notify_endpoints = ar.AsyncLogoutNotifyEndpoints(transport)
        self.lti_platforms = ar.AsyncLtiPlatforms(transport)
        self.m2m_tokens = ar.AsyncM2mTokens(transport)
        self.machine_enrolment_tokens = ar.AsyncMachineEnrolmentTokens(transport)
        self.machines = ar.AsyncMachines(transport)
        self.managed_waf = ar.AsyncManagedWaf(transport)
        self.mcp = ar.AsyncMcp(transport)
        self.mcp_connector = ar.AsyncMcpConnector(transport)
        self.messaging_providers = ar.AsyncMessagingProviders(transport)
        self.network_acls = ar.AsyncNetworkAcls(transport)
        self.notifications = ar.AsyncNotifications(transport)
        self.oauth_providers = ar.AsyncOAuthProviders(transport)
        self.custom_oauth_providers = ar.AsyncCustomOAuthProviders(transport)
        self.org_ldap_connections = ar.AsyncOrgLdapConnections(transport)
        self.organization_settings_schema = ar.AsyncOrganizationSettingsSchema(transport)
        self.pca = ar.AsyncPca(transport)
        self.radius_clients = ar.AsyncRadiusClients(transport)
        self.rate_limit_policy = ar.AsyncRateLimitPolicy(transport)
        self.redirect_urls = ar.AsyncRedirectUrls(transport)
        self.risk_based_mfa = ar.AsyncRiskBasedMfa(transport)
        self.scim_provisioning_targets = ar.AsyncScimProvisioningTargets(transport)
        self.session_exchange_apps = ar.AsyncSessionExchangeApps(transport)
        self.sms_templates = ar.AsyncSmsTemplates(transport)
        self.sso_onboarding = ar.AsyncSsoOnboarding(transport)
        self.testing = ar.AsyncTesting(transport)
        self.tickets = ar.AsyncTickets(transport)
        self.tokens = ar.AsyncTokens(transport)
        self.usage = ar.AsyncUsage(transport)
        self.user_exports = ar.AsyncUserExports(transport)
        self.user_imports = ar.AsyncUserImports(transport)
        self.whoami = ar.AsyncWhoami(transport)
        self.secret_keys = ar.AsyncSecretKeys(transport)
        self.keys = ar.AsyncKeys(transport)
        self.partner_links = ar.AsyncPartnerLinks(transport)
        self.partner_platforms = ar.AsyncPartnerPlatforms(transport)
        self.atlas_id_grants = ar.AsyncAtlasIdGrants(transport)
        self.privacy = ar.AsyncPrivacy(transport)
        self.integrations = ar.AsyncIntegrations(transport)
        self.status = ar.AsyncStatus(transport)
        self.notices = ar.AsyncNotices(transport)
        self.security_advisories = ar.AsyncSecurityAdvisories(transport)
        self.audit_exports = ar.AsyncAuditExports(transport)
        self.sub_processors = ar.AsyncSubProcessors(transport)
        self.entitlements = ar.AsyncEntitlements(transport)
        self.integration_health = ar.AsyncIntegrationHealth(transport)
        self.embed = ar.AsyncEmbed(transport)
        self.openapi = ar.AsyncOpenApi(transport)
        self.delivery_health = ar.AsyncDeliveryHealth(transport)
        self.meta = ar.AsyncMeta(transport)
        self.app_catalog = ar.AsyncAppCatalog(transport)
        self.ldap_server_clients = ar.AsyncLdapServerClients(transport)
        self.journeys = ar.AsyncJourneys(transport)
        self.groups = ar.AsyncGroups(transport)
        self.migrations = ar.AsyncMigrations(transport)
        self.managed_grants = ar.AsyncManagedGrants(transport)
        self.least_privilege = ar.AsyncLeastPrivilege(transport)
        self.flags = ar.AsyncFlags(transport)
        self.mfa_factors = ar.AsyncMfaFactors(transport)
        self.analytics = ar.AsyncAnalytics(transport)
        self.marketing = ar.AsyncMarketing(transport)
        self.audit_event_schemas = ar.AsyncAuditEventSchemas(transport)
        self.directory_pull_sources = ar.AsyncDirectoryPullSources(transport)
        self.relay_agents = ar.AsyncRelayAgents(transport)
        self.oauth_client_profiles = ar.AsyncOauthClientProfiles(transport)
        self.passkey_api = ar.AsyncPasskeyApi(transport)
        self.vc = ar.AsyncVc(transport)
        self.listen = ar.AsyncListen(transport)
        self.agent_registration = ar.AsyncAgentRegistration(transport)
        self.agents = ar.AsyncAgents(transport)
        self.agent_access_requests = ar.AsyncAgentAccessRequests(transport)
        self.workflows = ar.AsyncWorkflows(transport)
        self.page_templates = ar.AsyncPageTemplates(transport)
        self.service_connectors = ar.AsyncServiceConnectors(transport)
        self.desktop_mfa = ar.AsyncDesktopMfa(transport)
        self.identity_verification = ar.AsyncIdentityVerification(transport)
        self.iga = ar.AsyncIga(transport)
        self.scim_provisioning_presets = ar.AsyncScimProvisioningPresets(transport)
        self.vault = ar.AsyncVault(transport)
        self.connections = ar.AsyncConnections(transport)
        self.ssf = ar.AsyncSsf(transport)
        self.network_zones = ar.AsyncNetworkZones(transport)
        self.access_policies = ar.AsyncAccessPolicies(transport)
        self.abac = ar.AsyncAbac(transport)
        self.resources = ar.AsyncResources(transport)
        self.org_role_grants = ar.AsyncOrgRoleGrants(transport)
        self.devices = ar.AsyncDevices(transport)
        self.authz_decisions = ar.AsyncAuthzDecisions(transport)
        self.policy_bundles = ar.AsyncPolicyBundles(transport)
        self.proxy_apps = ar.AsyncProxyApps(transport)
        self.mcp_gateways = ar.AsyncMcpGateways(transport)

    def with_options(
        self,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> AsyncAtlasClient:
        """A copy of this client with per-call overrides, sharing its connection."""
        clone = object.__new__(AsyncAtlasClient)
        clone._owns_client = False
        clone._http = self._http
        clone._wire(
            self._transport.with_options(
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )
        return clone

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


class AtlasPlatformClient:
    """Synchronous Platform API client, authenticated by a platform key (``psk_...``).

    The platform key is the management-plane credential above a per-instance
    ``sk_``: it provisions and manages the apps and instances a platform owns and
    registers Sign in with Atlas apps. Takes the same options as
    :class:`AtlasClient`.
    """

    def __init__(
        self,
        platform_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        if not platform_key:
            raise ValueError("AtlasPlatformClient requires a platform_key.")
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)
        self._wire(
            _SyncTransport(
                platform_key,
                base_url,
                self._http,
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )

    def _wire(self, transport: _SyncTransport) -> None:
        self._transport = transport
        self.apps = r.PlatformApps(transport)
        self.accountless_apps = r.PlatformAccountlessApps(transport)
        self.atlas_id_apps = r.PlatformAtlasIdApps(transport)
        self.domains = r.PlatformDomains(transport)
        self.atlas_id_publisher = r.PlatformAtlasIdPublisher(transport)
        self.config_changelog = r.PlatformConfigChangelog(transport)
        self.design_assets = r.PlatformDesignAssets(transport)
        self.whoami = r.PlatformWhoami(transport)
        self.keys = r.PlatformKeys(transport)
        self.audit = r.PlatformAudit(transport)

    def with_options(
        self,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> AtlasPlatformClient:
        """A copy of this client with per-call overrides, sharing its connection."""
        clone = object.__new__(AtlasPlatformClient)
        clone._owns_client = False
        clone._http = self._http
        clone._wire(
            self._transport.with_options(
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )
        return clone

    def close(self) -> None:
        """Close the underlying HTTP client, if this client created it."""
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> AtlasPlatformClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncAtlasPlatformClient:
    """Asynchronous Platform API client — the ``asyncio`` peer of :class:`AtlasPlatformClient`."""

    def __init__(
        self,
        platform_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> None:
        if not platform_key:
            raise ValueError("AsyncAtlasPlatformClient requires a platform_key.")
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)
        self._wire(
            _AsyncTransport(
                platform_key,
                base_url,
                self._http,
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )

    def _wire(self, transport: _AsyncTransport) -> None:
        self._transport = transport
        self.apps = ar.AsyncPlatformApps(transport)
        self.accountless_apps = ar.AsyncPlatformAccountlessApps(transport)
        self.atlas_id_apps = ar.AsyncPlatformAtlasIdApps(transport)
        self.domains = ar.AsyncPlatformDomains(transport)
        self.atlas_id_publisher = ar.AsyncPlatformAtlasIdPublisher(transport)
        self.config_changelog = ar.AsyncPlatformConfigChangelog(transport)
        self.design_assets = ar.AsyncPlatformDesignAssets(transport)
        self.whoami = ar.AsyncPlatformWhoami(transport)
        self.keys = ar.AsyncPlatformKeys(transport)
        self.audit = ar.AsyncPlatformAudit(transport)

    def with_options(
        self,
        *,
        strict: bool | None = None,
        on_unknown_fields: UnknownFieldsHook | None = None,
        traceparent: str | None = None,
        secret_recipient: str | None = None,
    ) -> AsyncAtlasPlatformClient:
        """A copy of this client with per-call overrides, sharing its connection."""
        clone = object.__new__(AsyncAtlasPlatformClient)
        clone._owns_client = False
        clone._http = self._http
        clone._wire(
            self._transport.with_options(
                strict=strict,
                on_unknown_fields=on_unknown_fields,
                traceparent=traceparent,
                secret_recipient=secret_recipient,
            )
        )
        return clone

    async def aclose(self) -> None:
        """Close the underlying async HTTP client, if this client created it."""
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncAtlasPlatformClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
