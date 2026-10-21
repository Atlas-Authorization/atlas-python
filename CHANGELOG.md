# Changelog

All notable changes to the `atlas-backend` Python package are documented here.

## 0.7.0

### Added

- **OAuth client secret rotation with overlap.** `oauth_clients.rotate_secret(client_id, body=None,
  *, idempotency_key=None)` takes `{"overlap_seconds": int}` (default 86400, `0` revokes the old
  secret now, at most 604800) and returns `OAuthClientSecretRotation` (`client_secret`,
  `overlap_seconds`, `previous_secret_expires_at`). `OAuthClient` gains `previous_secret_expires_at`.
  New type `RotateOAuthClientSecretBody`.
- **Issuer and verification endpoints.** `Instance` gains `issuer`, `discovery_url`, `jwks_uri`
  and `allowed_origin_integrations`; `PlatformApp` / `PlatformAppWithSecret` gain
  `frontend_api_host`, `issuer`, `discovery_url`, `jwks_uri` and `allowed_origin_integrations`.
- **Allowed origins with an integration.** `allowed_origins` entries may be
  `{"origin": ..., "integration": "redirect" | "embedded" | "auto" | None}` on `instance.update`
  and the platform app, instance and accountless-app bodies (`AllowedOriginEntry`,
  `AllowedOriginInput`).
- **Login readiness.** `LoginReadiness` gains `integration` (`LoginReadinessIntegration`:
  `assumed`, `source`, `reason`); each check gains `applies`.
- **Branding audiences.** `BrandingAudience` documents `branding.audiences` (hint →
  `heading`, `subheading`, `logoUrl`, `primaryColor`; `None` deletes one).
- **Auth config.** `InstanceAuthConfigResolved` gains `strictRequestBodies`,
  `dangerouslyReportSkippedEmailsAsVerified`, `originIntegrations` and `branding`.
- **Email verification.** `EmailAddress` gains `verification` (`EmailAddressVerification`:
  `status`, `strategy`).
- **Development email sender.** New `messaging_providers.development_email.get / enable / disable`
  (`DevelopmentEmail`, `EnableDevelopmentEmailBody`, `DevelopmentEmailDeleteResult`).
  `MessagingProviders` gains `development_email`.
- **Managed email on your own provider account.** `CreateManagedEmailBody` gains `transport`
  (`resend` | `brevo`), `config.api_key` and `provider_id`. `ManagedEmail` gains `backend`,
  `provider_id` and `feedback_webhook`; `limits` is now `None` and `reputation` is
  `your_provider_account`. `ManagedEmailDeleteResult` gains `provider_removed`;
  `ManagedEmailRecord.purpose` adds `ownership` and `dmarc`.
- **Provider mode.** Email provider bodies accept `mode` (`standard` | `development`);
  `MessagingProvider` gains `id` and `mode` (`standard` | `development` | `managed_domain`).
- **Error codes.** `ErrorCode` adds `READ_ONLY_FIELD`, `DEVELOPMENT_EMAIL_NOT_ALLOWED`,
  `DEVELOPMENT_EMAIL_UNAVAILABLE`, `DEVELOPMENT_EMAIL_LIMIT_REACHED` and
  `DEVELOPMENT_EMAIL_TEMPLATE_NOT_ALLOWED`.
- **Webhooks, several signatures.** `verify_webhook` accepts an `atlas-signature` header with
  several space-separated `v1,<signature>` entries and verifies when any one matches (each
  compared in constant time). A single signature works as before.

### Changed

- `oauth_clients.rotate_secret` is typed `OAuthClientSecretRotation` (was a plain dict); calls
  without a body behave as before.

## 0.6.0

### Added

- **Back-channel logout, retryable failures.** `VerificationError.retryable` (bool) is `True` for
  `no_keys`: the issuer's keys could not be fetched (a network error, a JWKS outage, or a
  just-rotated key whose refetch failed). Answer `503` with `Retry-After` then, so Atlas retries the
  delivery, and `400` otherwise. A token whose `kid` is unknown after a failed JWKS refetch is now
  `no_keys` (was `invalid`).
- **Webhook verification.** `verify_webhook(body, headers, secret, *, now_ms=None, tolerance_ms=300000)`
  returns `WebhookVerification` (`verified`, `reason`, `event`, `delivery_id`, `timestamp`). `delivery_id`
  is the signed `atlas-id` header, the same on every retry of one event: deduplicate on it.
- **Domain moves.** `instance.move_origin({"from": ..., "to": ..., "dry_run": ...})` rewrites every URL on one
  origin to another across the instance, its OAuth clients, webhooks, redirect URLs and Sign in with Atlas apps
  (`OriginMove`: `changes`, `problems`, `applied`). The platform client's `atlas_id_apps.move_origin(app_id, body)`
  does the same for one app.
- **Connections and integrations.** `instance.connections()` (`InstanceConnections`) and
  `instance.integrations.get_chatly / set_chatly / delete_chatly / get_forumulate / set_forumulate /
  delete_forumulate` (`ChatlyIntegration`, `ForumulateIntegration`).
- **Logout fan-out.** New `logout_notify_endpoints` namespace: `list`, `create`, `get`, `update`, `delete`,
  `list_deliveries` (`LogoutNotifyEndpoint`, `LogoutNotifyDelivery`).
- **Managed email.** `messaging_providers.managed_email.get / create / verify / delete(force=...)`
  (`ManagedEmail`, `CreateManagedEmailBody`). `MessagingProviders` gains `managed_email`.
- **Back-channel logout logs.** `oauth_clients.list_backchannel_deliveries(client_id, limit=, starting_after=)` and
  `oauth_clients.test_backchannel_logout(client_id)`, plus the same two on `atlas_id_apps`
  (`BackchannelLogoutDeliveryList`, `BackchannelLogoutTest`).
- **Sign in with Atlas apps.** `atlas_id_apps.preflight(app_id)` (`AtlasIdAppPreflight`), `find_users(app_id, email)`,
  `revoke_grant(app_id, grant_id)` and `rotate_webhook_secret(app_id)`. `AtlasIdApp` gains `webhook_url`,
  `webhook_events`, `webhook_active` and `webhook_secret`; `UpdateAtlasIdAppBody` accepts `webhook_url`.
- **Publisher.** The platform client's new `atlas_id_publisher` namespace: `get`, `set`, `update`, `delete`,
  `verify` (`AtlasIdPublisher`), and `config_changelog.list(...)` for the account's config history.
- **More fields.** `User.version`; `CookieConsent.culture` and `declared_cookies` (`DeclaredCookie`);
  `SetCookieConsentBody.culture`; `Preflight.sdk_versions_seen` (`SdkVersionSeen`, `SdkAdvisory`);
  `WebhookDelivery` (`error`, `location`) and `WebhookEventCatalogEntry`; `CustomDomain.dns` and
  `CreateDomainBody.dns` (`CustomDomainDnsInput`).

## 0.5.1

### Added

- **Captcha is bring-your-own-keys.** `ErrorCode.CAPTCHA_KEYS_REQUIRED` (422: captcha can only be turned
  on once its own site key and secret are stored) and `ErrorCode.CAPTCHA_IN_USE` (409: removing a key a
  live flow uses; `meta.flows`).
- `SetCaptchaSecretBody` accepts `provider`, so the secret can be stored before captcha is turned on.
- `instance.delete_captcha_secret(provider=..., force=...)`: `force=True` removes a secret a flow uses and
  turns those flows off; `InstanceDeleteCaptchaSecretResult` gains optional `flows_turned_off`.

## 0.5.0

### Added

- **Skip the logout confirmation.** `CreateOAuthClientBody` and `UpdateOAuthClientBody`
  accept `skip_logout_confirmation`; `OAuthClient` gains `skip_logout_confirmation`
  (`False` by default). First-party clients only (a third-party client gets 422
  `VALIDATION_FAILED`, param `skip_logout_confirmation`). When `True`, `/oauth2/logout`
  with that `client_id` and an exactly registered `post_logout_redirect_uri` ends the
  session and redirects straight back with `state`, without the confirmation page.
- **Cookie settings link.** `SetCookieConsentBody` accepts `settings_link`
  (`CookieConsentSettingsLinkInput`: `label`, `preset`?, `attributes`?; `None` or
  omitted means no link). `CookieConsent` gains `settings_link`
  (`CookieConsentSettingsLink`: `label`, `preset`, `attributes`,
  `rendered_attributes`, or `None`). New `CookieConsentSettingsLinkPreset`
  (`"cookiemunch"`, `"cookiebot"`, `"onetrust"`, `"custom"`); responses keep `preset`
  a plain `str` so new presets still decode.
- **Force-remove the email provider.** `messaging_providers.delete(channel, force=False)`
  takes `force`; `force=True` sends `?force=true` and removes the email provider even
  while email-dependent features are on (otherwise refused with 409
  `EMAIL_PROVIDER_IN_USE`, with the features in `meta.features`).
- **Error codes.** `ErrorCode.EMAIL_PROVIDER_IN_USE`.
- **Sessions.** `sessions.list` and `users.list_sessions` document their items as
  `Session`, which carries `idle_expires_at`, `last_active_organization_id` and
  `impersonated_by`.

All of these are on both the sync and the async clients. The changes are backward
compatible: every new field and parameter is optional, and nothing was removed or
renamed.

## 0.4.0

### Added

- **API key spend caps.** `api_keys.create` and `api_keys.update` accept `limits`
  (a list of `ApiKeyLimit`: `unit`, `amount`, `period` — `"request"`, `"day"`,
  `"month"` or `"total"`; `None` on update clears them). `ApiKey` and `ApiKeyCreate`
  gain `limits` and `usage` (a list of `ApiKeyLimitState`: `unit`, `period`, `amount`,
  `used`, `remaining`, `window_start`, `resets_at`).
- **Usage metering.** `api_keys.record_usage(key_id, {"amount", "unit",
  "idempotency_key"?})` returns `ApiKeyUsageDebit` (`key_id`, `unit`, `amount`,
  `allowed`, `code`, `exceeded`, `usage`, `counters`, `idempotent_replay`). A refusal
  is returned with `allowed: False` and `code: "LIMIT_EXCEEDED"`, not raised.
  `api_keys.get_usage(key_id)` returns `ApiKeyUsage` (`key_id`, `limits`, `usage`,
  `counters`). New types: `ApiKeyLimit`, `ApiKeyLimitPeriod`, `ApiKeyLimitState`,
  `ApiKeyUsageCounter`, `RecordApiKeyUsageBody`, `ApiKeyUsageDebit`, `ApiKeyUsage`.
- **Verify.** A valid `ApiKeyVerification` gains `name`, `scopes`, `constraints`,
  `limits` and `usage`.
- **Session keep-alive.** `sessions.touch(session_id)` returns `TouchedSession` (the
  session plus `extended`). `Session` gains `idle_expires_at`.
- **Users.** `CreateUserBody` and `CreateUserImportBody` accept `notify` (`False`, the
  default, sends nothing to the user).
- **Error codes.** `ErrorCode.LIMIT_EXCEEDED`, `SESSION_REVOKED`,
  `SESSION_IDLE_EXPIRED` and `SESSION_EXPIRED`.

All of these are on both the sync and the async clients. Nothing was removed or
renamed.

### Changed

- `AtlasIdAppCopy.sign_in_title` / `sign_up_title` comments state the current
  defaults ("Sign in", "Create your Atlas Account"); no type change.

## 0.3.0

Full coverage of the Backend API and the Platform API: every operation in the
public API reference now has a method, on both the sync and the async clients.

### Added

- **Platform client.** `AtlasPlatformClient` / `AsyncAtlasPlatformClient`, authenticated
  by a platform key (`psk_...`), with `apps`, `accountless_apps`, `atlas_id_apps` and
  `design_assets`.
- **Sign in with Atlas apps.** `atlas_id_apps.create / list / get / update / delete /
  rotate_secret / preview_design`, with post-logout redirect URIs, back- and
  front-channel logout URIs, and typed branding (theme, colours, policy links, page
  copy, design).
- **Back-channel logout.** `LogoutTokenVerifier` verifies a `logout_token` (OpenID
  Connect Back-Channel Logout 1.0) against the issuer's keys and returns
  `LogoutTokenClaims` (`sub`, `sid`, `jti`, `iat`); optional `jti_seen=` replay guard.
  `logout_token_from_form()` reads the token from a form body.
- **Strict request bodies.** `strict=True/False` on every client sends `Atlas-Strict`
  on writes; `client.with_options(strict=...)` overrides it for a single call. The
  `Atlas-Unknown-Fields` response header is reported to an `on_unknown_fields` hook,
  or logged as a warning on the `atlas_backend` logger.
- **Setup check.** `instance.preflight()` with typed findings (severity, code,
  message, fix, subject).
- **Design.** `design.get / replace / update / preview / catalog`,
  `organizations.design.get / replace / update`, and image uploads
  (`design.assets.upload / list / delete`, `design_assets` on the platform client).
  Uploads send raw bytes; the image type is detected or can be passed as
  `content_type=`. The design object is fully typed (`models.AtlasDesign`,
  `models.AtlasDesignPatch`).
- **Cookie consent.** `instance.cookie_consent.get / set / delete`.
- **Typed messaging providers.** `messaging_providers.set_email / set_sms` take a
  per-transport config (`models.EmailProviderConfig`, `models.SmsProviderConfig`);
  plus `list`, `delete` and `test`.
- **OAuth providers.** `oauth_providers.list(provider=..., configured=...)`, `get`,
  `upsert` (credentials, `display_name`, `icon_url`, `mode`, wallet verifier settings;
  `None` clears), `delete`, `set_enabled`, `set_scope`, `test`.
- **Webhooks.** `webhooks.endpoints.update / reveal_secret / rotate_secret / test /
  list_deliveries / redeliver`.
- **Entitlements.** `entitlement_overrides.create / list / delete` and
  `organizations.get_entitlements`.
- **Organization policy.** `models.OrganizationPolicyPatch` now types every policy
  field (`allowedSignInMethods`, `ipAllowlist`, `maxSessionAgeSeconds`, `endUserPool`,
  ...); `update_policy` also accepts a plain `dict` for fields newer than this release.
- **Error codes.** `ErrorCode` lists every stable error code (`UNKNOWN_FIELD`,
  `INVALID_KEY`, `WRONG_KEY_SURFACE`, `PLAN_IN_USE`, `EMAIL_DELIVERY_NOT_CONFIGURED`,
  `EMAIL_PROVIDER_REQUIRED`, ...).
- **Everything else in the API reference**, including: actions, API keys and
  token minting, custom audit events (with export), billing plans / subscriptions /
  usage, bot signals and labels, branding, captcha verification, config changelog,
  community connectors and the directory, data subject requests, diagnostics,
  email and SMS templates, events, FGA and the OpenFGA-compatible API, grants,
  instance settings and secrets, jobs, user imports and exports, legacy auth
  connection, localizations, log streams, LTI platforms, machines and enrolment
  tokens, M2M token verification, managed WAF, MCP and the MCP connector, network
  ACLs, notifications (categories, templates, preferences), org LDAP connections,
  organization settings and its schema, org audit streams, branding, end users and
  reader domains, proof-carrying authority controls, RADIUS clients, rate limits,
  redirect URLs, risk-based MFA, outbound SCIM provisioning targets, session
  exchange apps, session creation and token minting, SSO onboarding, tickets,
  token verification, usage, and the user sub-resources (identities, phone
  numbers, consents, deletion, directives, approval requests, grants, erasure,
  passwords, passkeys, sign-in history, resolved profile and state).
- **Typed models.** Request bodies and responses are `TypedDict`s in
  `atlas_backend.models`, generated from the API reference.
- New options on existing methods: `users.get(include_deleted=)`,
  `users.delete(audit_actor_ids=, audit_actor_emails=)`,
  `users.ban(reason=, note=)`, `users.revoke_sessions(all=, revoke_grants=)`,
  `roles.delete(reassign_to=)`, `organizations.memberships.list(limit=, offset=)`,
  `sso_connections.list(organization_id=)`, `scim_tokens.list(organization_id=)`,
  `audit_logs.list(target_type=, target_id=)`, `webhooks.deliveries(limit=)`.
- Request bodies brought up to date: user create (`password_hash`,
  `password_digest`, `external_id`, `identities`, `mfa`), user update
  (`external_id`, `password`, `unsafe_metadata`), OAuth client logout URIs, SSO
  connection `provisioning_mode` / `manual_endpoints`.

### Changed

- `__version__` now matches the package version.
- `aresources.py` is generated from `resources.py` (`scripts/gen_async.py`), so
  the async client can never fall behind the sync one.

### Removed

- `signing_alg` from the resource-server create/update body types: the API never
  accepted it on writes (it is read-only and still present on `ResourceServer`).

## 0.2.0

- Framework integrations: Django, FastAPI and Flask helpers.

## 0.1.0

- Initial release.
