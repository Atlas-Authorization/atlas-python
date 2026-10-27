# Changelog

All notable changes to the `atlas-backend` Python package are documented here.

## Unreleased

### Added

- **Catch-up with the live Backend API: 452 more operations**, sync and async, each with a typed request body (`<Resource><Method>Body`) and response (`<Resource><Method>Response`) in `atlas_backend.models`. New namespaces: `app_catalog`, `ldap_server_clients`, `journeys`, `groups` (with `groups.rules`), `migrations` (with `migrations.imports`), `managed_grants`, `least_privilege`, `flags`, `mfa_factors` (with `yubikeys` and `smart_card_mappings`), `analytics` (with `reports` and `alert_rules`), `marketing`, `audit_event_schemas`, `directory_pull_sources` (with `sync_runs`), `relay_agents`, `oauth_client_profiles`, `passkey_api`, `vc` (credential types, credentials, presentation requests), `listen`, `agent_registration`, `agents`, `agent_access_requests`, `workflows`, `page_templates`, `service_connectors`, `desktop_mfa`, `identity_verification`, `iga` (entitlements, requests, grants, delegations, sod, lifecycle, campaigns), `scim_provisioning_presets`, `vault`, `connections`, `ssf` (streams, receivers), `network_zones`, `access_policies`, `abac` (templates, links, schema), `resources` (types, assignments), `org_role_grants`, `devices`, `authz_decisions`, `policy_bundles`, `proxy_apps` and `mcp_gateways` (with `budgets`). Further methods on `users` (required actions, notes, guardians, saved searches), `organizations` (webhook endpoints), `oauth_clients` (app settings, workload identity, trusted issuers, login and consent requests), `org_ldap_connections` (sync runs), `fga`, `openfga`, `attack_protection`, `risk_based_mfa`, `delivery_health`, `actions`, `instance` and `integrations`.
- `policy_bundles.archive` returns the raw gzip bytes; `listen.stream_session` asks for `text/event-stream` and returns the stream text once it closes. `delivery_health.get_for_target` reads `GET /v1/delivery_health/{kind}/{target_id}`.
- API coverage list: 1,201 operations.
- **Risk-event timeline.** `risk_based_mfa.list_events` (`GET /v1/risk_events`), `event_metrics` (`GET /v1/risk_events/metrics`) and `event_feedback` (`POST /v1/risk_events/{id}/feedback`), sync and async, with typed `RiskEvent`, `RiskEventMetrics` and `RiskEventFeedbackBody`.
- **Fraud lookup.** `risk_based_mfa.fraud_lookup` (`POST /v1/fraud/lookup`) with typed `FraudLookupBody` and `FraudLookup`.
- `RiskBasedMfa` and `UpdateRiskBasedMfaBody` gain `mode`, `level_actions`, `reputation`, `fraud`, `baseline` and `mid_session`.

## 0.20.0 — 2026-10-25

### Added

- **Test and review accounts for Sign in with Atlas apps.** `atlas_id_apps.provisioned_accounts` (`list`, `create`, `get`, `remove`, `rotate_password`), sync and async, on `/v1/platform/atlas_id_apps/{id}/provisioned_accounts`. Needs the `platform:atlas_id_apps:provision` scope, or the per-app `atlas_id_apps:<app id>:provision` scope. The password is returned once, on `create` and `rotate_password`; pass `secret_recipient=` (per call, or on the client) to receive it as `sealed_password` instead. Typed `AtlasIdProvisionedAccount`, `AtlasIdProvisionedAccountList`, `CreateAtlasIdProvisionedAccountBody`, `RotateAtlasIdProvisionedPasswordBody`.
- **Verified domains.** `platform.domains` (`list`, `claim`, `check`, with `verify` as an alias, `remove`), typed `AccountDomain`. Verified domains gate test sign-in mode and the test-account domain restriction.
- `AtlasIdApp` and `UpdateAtlasIdAppBody` gain `test_mode` and `provisioned_verified_domains_only`.
- `ErrorCode.TEST_ACCOUNT_RESTRICTED` (403), `PROVISIONED_ACCOUNT_LIMIT_REACHED` (409) and `DOMAIN_NOT_VERIFIED` (422).
- API coverage list: 749 operations.

## 0.19.0 — 2026-10-25

### Added

- **Partner platforms.** `partner_platforms` (`list`, `get`, `set`, `delete`, `registration`, `store_token(partner, token, rotate=, api_base_url=)`, `deliveries(limit=)`), sync and async. Typed `PartnerPlatform`, `PartnerPlatformInput`, `PartnerPlatformRegistration`, `PartnerDelivery`, `PartnerPlatformList`. The partner token is write-only: no response carries it, only `token_set` and `token_prefix`.
- **Per-call audience.** `sessions.get_token` and `integrations.get_token` take `audience=`, `cbid=` and `audience_params=` (the integration's own parameter), sent as query parameters; the integration's `per_call_audience` (`param`, `template`, `allowed`, `any_matching`; `None` turns it off) decides what is permitted. Typed `PerCallAudience`.
- **Privacy orchestrator.** Typed `PrivacyOrchestrator` / `PrivacyOrchestratorInput` with `site_id`, `partner_link_id` and `cancel_deletion_on_sign_in`; presets may carry `case_format`. `OutboundPartnerLink.source` gains `registration`.
- **Operator.** `keys.operator()` returns the typed `OperatorConfiguration`, with `audiences` and `access_token_claims`.
- `users.list(include_deleted=True)` returns soft-deleted users, which the list leaves out by default.
- `ErrorCode.MANAGED_WAF_NOT_CONFIGURED` (422, `meta.action`).
- The Sign in with Atlas grant routes (`atlas_id_apps.find_users`, `revoke_grant`) also accept the secret key of the instance that manages the app; `atlas_id_grants` is the same on the instance client.
- API coverage list: 740 operations.

## 0.18.0 — 2026-10-24

### Added

- **Enterprise SSO claims.** `SessionClaims` reads `sso_connection_id`, `sso_organization_id` and `sso_connection_type`; `oidc_sso_of` returns `organization_id` and `type` next to `connection_id`. `OidcSsoContext` gains both. Scope a per-organization "require SSO" rule on `sso_organization_id`, never on "signed in via SSO".
- **Adopting a Sign in with Atlas app.** `atlas_id_apps.set_managed_by(app_id, instance_id | None)` (`PUT /v1/platform/atlas_id_apps/{id}/managed_by`, sync and async) hands an app's grants to an instance, or takes them back; typed `AtlasIdAppManagedBy`. `AtlasIdApp` gains `managed_via` (`instance_toggle` | `adopted`) and `button_rendered_origins`.
- **Instance-surface app setup check.** `atlas_id_grants.preflight(app_id)` (`GET /v1/atlas_id_apps/{id}/preflight`). The app setup check type `AtlasIdAppPreflightDetail` adds `button_rendered_origins`, `authorize_requests_7d`, `fallback_origins` and `homepage_includes_script`.
- **Dry run.** `DryRunResult` types the answer to `dry_run=True`: `mode` (`native` | `rollback` | `plan`), `validated`, `warnings`, `would_return_status`, `would_return`, `suppressed`, `validation_skipped`.
- **Sealed secrets.** `secret_recipient=` on `AtlasClient`, `AsyncAtlasClient`, the platform clients and `with_options(...)` sends `X-Secret-Recipient` on every request, so every route that returns a shown-once secret answers sealed. `SealedSecrets` (`sealed_secret`, `sealed_client_secret`, `sealed_webhook_secret`, `secrets_sealed`) and `SecretsSealed` are mixed into the secret-bearing response types.
- `CursorPage` accepts `object: "list"`.
- API coverage list: 733 operations.

## 0.17.0 — 2026-10-24

### Added

- **Credentials.** `whoami`, `secret_keys` (`create` / `list` / `get` / `update` / `rotate` / `revoke`), `keys` (`list`, `revoke_leaked`, `operator`, `exchange_token`, `client_credentials`, `token_exchange`), `partner_links`, `atlas_id_grants`, and on the platform client `whoami`, `keys` and `audit` (+ `streams`). Typed `SecretKey`, `CreateSecretKeyBody`, `UpdateSecretKeyBody`, `PlatformKey`, `PartnerLink`. Keys carry `owner`, `expires_at` (a default one-year expiry; `null` is refused) and `allowed_origins`, a browser-origin lock refused with `ORIGIN_NOT_ALLOWED`.
- **Partner link requests, no pasted key.** `partner_links.requests` (`list`, `get`, `approve`, `deny`), `partner_links.set_certificates` (mTLS `cert_fingerprints`), `partner_links.outbound` (`list`, `save`, `test`, `remove`, `request`). For a partner product: `request_partner_link`, `get_partner_link_request`, `verify_partner_link_delivery` (the signed `partner_link.credentials` / `partner_link.denied` delivery). Typed `PartnerLinkRequest`, `PartnerLinkRequestApproval`, `PartnerLinkRequestInput`, `PartnerLinkRequestCreated`.
- **OIDC relying parties.** `oidc_organization_of` (`org_id`, `org_slug`, `org_role`, `org_permissions`), `oidc_organizations_of` (the `orgs` claim of the `organizations` scope), `oidc_sso_of` (`sso_connection_id`, `sso_tenant_id`, `sso_issuer`, `sso_domain`), `oidc_authorize_url_with_organization` (the `organization` authorize parameter), `OIDC_SCOPE_ORGANIZATIONS`. Typed `OidcOrganization`, `OidcOrganizationMembership`, `OidcSsoContext`.
- **Webhooks.** `endpoints.get`, `put_by_url`, `test(wait=)`, `redeliver_window`, `replay`, `list(include_deprecated=, metadata=, starting_after=)`, delivery filters (`status`, `event_type`, `since`, `until`, `starting_after`), `webhooks.egress_ips`, `delivery_health`. Replay and window redelivery accept `since="failing_since"`; endpoints report `last_failing_since`, `event_naming`, `signature_versions`, `destination`, health and alert fields. `verify_webhook(url=, require_v2=)` verifies URL-bound `v2` signatures; unknown signature versions are ignored. `canonical_webhook_event`, `webhook_event_spellings`, `webhook_event_matches`, `WEBHOOK_EVENT_ALIASES` and the new event-name constants.
- **Privacy executor.** `privacy` (`discover`, `preset`, `lookup`, `create_request`, `get_request`, `cancel_request`, `orchestrator`), `verify_privacy_case_request`, `verify_privacy_completion`, `valid_privacy_idempotency_key`, `is_privacy_event`.
- **Integrations.** `integrations` and `sessions.get_token(session_id, for_=)`, `atlas_id_integration_token` / `aatlas_id_integration_token` (the browser `atlas_id_tokens` route for Sign in with Atlas users, Bearer or DPoP).
- **Platform surface.** `status` (subscription, incidents, dependencies), `notices`, `security_advisories`, `audit_exports`, `sub_processors`, `entitlements`, `integration_health`, `embed`, `openapi.diff`, `instance.unknown_fields_report`, `instance.preflight(min_severity=, include_suppressed=)`, `messaging_providers.get_channel`, `instance.referrals.install`, `platform.apps` `create_secret_key` / `clone_config` / metadata filter, `users.list(updated_after=, updated_before=)`, `events.list(since=, until=, order=)`.
- **Options.** `dry_run=True` on the provisioning calls, a W3C `traceparent` on the client and `with_options(traceparent=)`, `Traceparent` helpers, `KeyFormat` / `parse_key` for `atlas_<env>_<kind>_...` and the legacy `sk_` / `pk_` / `psk_` / `whsec_` formats.
- **Errors.** `ErrorCode.INSUFFICIENT_SCOPE` (the former `SCOPE_MISSING` is still matched), `ORIGIN_NOT_ALLOWED`, `ROUTE_NOT_FOUND`, `NOT_A_LIVE_INSTANCE`, `TEST_MODE_ONLY`, `TESTING_UNAVAILABLE`, `PARTNER_LINK_UNAVAILABLE`; `AtlasError.is_insufficient_scope`, `required_scope`, `is_step_up_required`, `is_origin_not_allowed`, `did_you_mean`, `allowed_methods`, `docs_url`.
- **Helpers.** `BackchannelLogoutApp` (WSGI) and `handle_backchannel_logout`, `OperatorLogin` / `AsyncOperatorLogin` (device flow, RFC 8693 exchange, `client_credentials`, leaked-key revocation), `SealedBox` for `sealed_*` secrets (needs the new `sealed` extra: PyNaCl).
- Referral provider `referalli` (the former `referally` is still accepted).
- API coverage list: 731 operations.

## 0.16.0 — 2026-10-24

### Added

- **Policy acceptance.** `policies` (`list`, `create`, `get`, `update`, `delete`, `list_acceptances`, `export_acceptances_csv`, `for_user`) with `policies.versions` (`list`, `create`, `get`, `update`, `delete`, `publish`, `retire`) and `policies.settings` (`get`, `update`: the `pol` session claim), `policy_source` (`get`, `update`, `delete`, `test`, `sync`, `list_deliveries`; the signing secret is write-only), sync and async. Typed `Policy`, `PolicyVersion`, `PolicyAcceptance`, `PolicyStanding`, `UserPolicies`, `PolicySource` and friends. `users.consents.record` / `Consent` carry the acceptance evidence (`policy_version_id`, `content_sha256`, `display`, `scrolled_to_end`, `view_ms`, `locale`).
- **Policy source helpers** for a CMS written in Python: `verify_policy_feed_request(method, path_and_query, headers, secret)` checks Atlas's signed feed request (`atlas-id`, `atlas-timestamp` in ms, `atlas-signature` with one or more `v1,<base64 HMAC-SHA256>` values over `{id}.{ts}.GET\n{path+query}`, five-minute window) and returns the `key` Atlas asked for; `sign_policy_source_event(event, secret)` signs a `policy.published` / `policy.retired` event for Atlas. Typed `PolicyFeed`, `PolicyFeedPolicy`, `PolicyFeedVersion`, `PolicySourceEvent`; `POLICY_SOURCE_PROTOCOL_VERSION`.
- `SessionClaims.policies` and `accepted_policy_version(key)` read the `pol` session claim. `WEBHOOK_EVENT_USER_POLICY_ACCEPTED`, `WEBHOOK_EVENT_POLICY_VERSION_PUBLISHED`.
- API coverage list: 626 operations.

## 0.15.0 — 2026-10-24

### Added

- **Migrate from Better Auth: sealed-bundle imports.** `better_auth_imports` (sync and async): `get_public_key`, `rotate_public_key`, `create`, `list`, `get`, `upload_part`, `finalize`, `dry_run`, `apply` (resumes a failed import), `delete`, `list_jwks`, `delete_jwk`. Helpers: `upload(bundle, options=, part_bytes=, on_part=)` creates the import, uploads the bundle in line-aligned parts of at most 8 MiB (`split_bundle_parts`, `BETTER_AUTH_IMPORT_PART_BYTES`) and finalizes it; `wait_for(id, interval=, timeout=, on_progress=)` polls until the import leaves `analyzing` / `queued` / `applying`. Typed `BetterAuthImport`, `BetterAuthImportKey`, `BetterAuthImportOptions`, `ImportedJwk`.
- **Better Auth session bridge.** `better_auth_bridge.get` / `update` / `delete` (migration window, cookie prefix, live fallback; the old app's secret is write-only) and `better_auth_bridge.exchange(token, client_ip=, user_agent=, remember=)` on the secret-key Backend API route, forwarding the end user's IP and user agent (`X-Atlas-Client-IP`, `X-Atlas-Client-User-Agent`). `exchange_better_auth_session` / `async_exchange_better_auth_session` classify the outcome (`session`, `needs_mfa`, `refused` with `meta.bridge_outcome`; never raise). `BetterAuthBridge` / `AsyncBetterAuthBridge` turn a request's cookies into a `BridgeDecision` (Atlas cookies to set, Better Auth cookies to clear only on a final refusal, `continuation_url` for a second factor); `read_better_auth_session_cookie`, `better_auth_cookie_names`, `serialize_bridge_cookie`. Django (`AtlasMiddleware`) and Flask (`Atlas`) take `ATLAS_BETTER_AUTH_BRIDGE` (with `ATLAS_SECRET_KEY`, optional `ATLAS_API_URL`): a GET/HEAD with a Better Auth cookie is exchanged and redirected to the same URL signed in.
- **Better Auth JWTs during the cutover.** `AtlasBackend(legacy_issuers=[LegacyIssuer(issuer=, until=, jwks= | jwks_url=, audience=, algorithms=, resolve_subject=)], secret_key=, api_url=)`: a token from that issuer, inside its window, is verified against that issuer's keys only (EdDSA, ES256, ES512, RS256, PS256; `exp` required) and its `sub` is mapped to the Atlas user id through `external_id` (Backend API lookup cached 5 minutes, at most 10 000 entries; failures are not cached). The claims carry `external_id` and `legacy`. Django and Flask read `ATLAS_LEGACY_ISSUERS`.
- API coverage list: 604 operations.

## 0.14.0 — 2026-10-24

### Added

- **DPoP (RFC 9449) on the access-token verifier.** A DPoP-bound token (`cnf.jkt`) is accepted only with the DPoP scheme and a valid proof (never as Bearer): `typ` `dpop+jwt`, `DPOP_ALGS` (ES256/384/512, RS256/384/512, PS256/384/512, EdDSA), public embedded JWK, signature, `htm`, normalised `htu` (`normalize_htu`; `public_origin` for path-only URLs), `iat` window, `ath` (`dpop_access_token_hash`), `jti` replay via a `DpopReplayStore` (`MemoryDpopReplayStore` by default), RFC 7638 `jwk_thumbprint` match. `require_dpop` refuses unbound tokens; `dpop_nonces` (`HmacDpopNonceSource`) demands a server nonce (`use_dpop_nonce`, `AccessTokenResult.dpop_nonce` for the `DPoP-Nonce` header). `verify(..., method=, url=, dpop=)`; challenges use the `DPoP` scheme with `algs`. The FastAPI and Flask guards pass the request method, URL and `DPoP` header and set `DPoP-Nonce`. `protected_resource_metadata` advertises `dpop_signing_alg_values_supported` and takes `dpop_bound_access_tokens_required`.
- **Billing: several subscriptions per subject, add-ons, Chargebee / Autumn / Commet.** Providers `chargebee`, `autumn`, `commet` (`BILLING_PROVIDERS`; config keys on `SetBillingProviderBody`). Plans: `kind` (`base` / `addon`), `limits`, `seat_feature_id` (Autumn; `None` clears). Subscriptions carry `entitlements`. New `billing.subscriptions.get`, `billing.plans.sync_entitlements`, `billing.get_settings` / `update_settings` (limit merge `max` / `sum`), `billing.check_feature`. Usage takes `feature` and `subscription_id`.
- **Custom OAuth / OIDC providers.** `custom_oauth_providers`: `list`, `get`, `create`, `update`, `delete`, `discover`, `preview_profile_mapping`, `preview_provider_profile_mapping`, `list_signing_keys` / `rotate_signing_key` / `retire_signing_key`. Typed `ProfileMapping`, `UpstreamLogoutSettings`, `IdpInitiatedLoginSettings`, `UpstreamUrls`. OIDC SSO connections take the same relying-party settings and gain `preview_profile_mapping` and the signing-key methods.
- **Actions gallery.** `action_gallery` (`list` with filters, `get`, `install`, `installs`, `update`) and `action_templates` (`list`, `create`, `get`, `update`, `delete`, `add_version`, `submit_version`, `delete_version`, `publish`, `unlist`). Action dry runs report `http_requests`; sample events take `request.country`.
- **Session custom data.** `sessions.set_custom_data` (replace; `None` clears) and `update_custom_data` (merge; `None` removes a key); sessions carry `custom_data`; `sessions.create` takes `custom_data`. `WEBHOOK_EVENT_SESSION_UPDATED`.
- **Sign-in settings.** `instance.security.set_wallet_rpc_secret(chain_id=, url=)`; rate-limit `rules` (`RateLimitRule`) and the group catalog on the rate-limit policy; `instance.set_account_linking_trust`; `instance.set_captcha_config`; `CAPTCHA_PROVIDERS` (incl. `captchafox`, `vercel_botid`), `LINKING_TRUST_LEVELS`.
- **Vercel BotID attestations.** `create_botid_attestation(secret, is_bot=, is_verified_bot=, ttl_seconds=)` signs a verdict in Atlas's `atlas_botid.v1` format.
- **Enterprise SSO.** SAML Single Logout fields (`saml_single_logout`, `saml_idp_slo_url`, `saml_idp_slo_response_url`, `saml_idp_slo_binding`, `saml_idp_slo_soap_url`), `saml_require_encrypted_assertions` and the encryption-key flags; `SamlMetadata.slo_url`; `sso_connections.get_saml_encryption_key`, `create_saml_encryption_key` (create or rotate), `retire_previous_saml_encryption_key`, `delete_saml_encryption_key`. Attack protection `dormant_accounts`; risk weight / signal `dormantAccount`; `EMAIL_TEMPLATE_ACCOUNT_REACTIVATED`; `WEBHOOK_EVENT_USER_REACTIVATED`.
- **Atlas as OAuth provider.** OAuth clients: `access_token_format`, `token_lifetimes` (`OAuthTokenLifetimes`). Resource servers: `access_token_format`, refresh-token lifetimes, `introspection_client_ids`. Signing keys report `provider`; `instance.security.get_signing_key_provider` / `set_signing_key_provider` / `remove_signing_key_provider` (AWS KMS, Google Cloud KMS, Azure Key Vault).
- **Opaque access tokens.** `AccessTokenVerifier(introspection=IntrospectionOptions(...))` validates non-JWT access tokens at Atlas's RFC 7662 endpoint with your API's client credentials, cached by token hash (TTL, negative TTL, never past `exp`, bounded); `introspect_jwts=True` checks JWTs live too. `Introspector` is exported.
- **Device sign-in approval.** `DeviceAuthorizations(frontend_api, session_token)`: `lookup`, `approve`, `deny` on the Frontend API with the user's session token; `DeviceAuthorizationError` (`needs_reverification`, `is_invalid_code`); `format_user_code`, `user_code_from_url`; `AsyncDeviceAuthorizations` over an `httpx.AsyncClient`.
- The coverage list now holds all 588 Backend and Platform API operations.

### Changed

- Without `introspection`, a token that is not a JWT is refused with "configure `introspection` to accept opaque tokens" instead of "malformed".

## 0.13.0 — 2026-10-23

### Added

- **App roles.** `client.app_roles`: `list`, `create`, `get`, `update`, `delete`, `list_users`, and per user `get_for_user`, `set_for_user` (replace, or add/remove), `remove_from_user`. `SessionClaims.has_app_role` / `has_app_permission` read the `app_roles` / `app_permissions` claims (no active organization needed).
- **Organization teams and custom roles.** `organizations.teams` (list, create, get, update, delete, members list/add/remove) and `organizations.roles` (the roles an org can assign; create/update/delete its own, with `reassign_to`). `organizations.get_by_slug`, `organizations.check_slug`, `organizations.invitations.resend`.
- **User search.** `users.list(...)` takes `query`, `email_address`, `username`, `phone_number`, `external_id`, `banned`, `email_verified`, `organization_id`, `created_after` / `created_before`, `order_by`, `offset` and `include_total_count`.
- **Timed bans.** `users.ban(..., expires_in_seconds=, expires_at=)`; users carry `ban_expires_at`.
- **API key controls.** Create bodies take `prefix`, `expires_in_seconds`, `enabled`, `rate_limit`, `remaining`; updates take `enabled`, `rate_limit` / `remaining` (`None` removes them). `api_keys.verify` takes `required_scopes`; a refusal of a live key carries `code` (`insufficient_scope`, `rate_limited`, `usage_exhausted`), `missing_scopes`, `retry_after_ms`.
- **Billing providers (bring your own key).** `billing.providers` (`list`, `get`, `set`, `test`, `delete(force=)`); `billing.subscriptions.change`, `cancel(immediately=)`, `restore`. Plans take `provider`, `provider_price_id`, `annual_price_id`, `annual_amount`; subscriptions report the provider, account, interval, scheduled change, trial and cancellation fields.
- **OAuth server administration.** `instance.security.list_signing_keys` / `rotate_signing_key` (`alg` RS256 or ES256); `client.oauth_initial_access_tokens` (list, create, revoke). OAuth client bodies take `disabled`, `require_pkce`, `subject_type`, `sector_identifier_uri`, `secret_expires_in_seconds`; resource servers take `signing_alg` and `publish_resource_metadata`.
- **Access-token verification for your API.** `AccessTokenVerifier` checks an Atlas-issued OAuth access token locally (issuer, expiry, `token_use`, audience, scopes) and returns the RFC 6750 / RFC 9728 `WWW-Authenticate` challenge on refusal; `build_www_authenticate`, `protected_resource_metadata`, `protected_resource_metadata_path`; the FastAPI `AtlasAccessToken` dependency and the Flask `access_token_required` decorator. DPoP-bound tokens are refused.
- SCIM tokens: `scopes`, `role_mappings`, `scim_tokens.update`. User imports: row `external_id`, `created_at`, `password_salt`, `phone_number(s)`, `organization_memberships`; job `create_organizations`, `password_hash_config`. `instance.hooks.list_before_user_create_calls`, `instance.referrals.get_call`.

### Changed

- Session and logout-token verification accept **ES256** as well as RS256 (`SIGNING_ALGS`), and nothing else; the token's `kid` selects one key whose type fixes the algorithm.

## 0.12.0

### Added

- Referral settings carry browser capture: `browser_sources` (the referral programs whose script or cookie the browser reads; null on update resets to the provider's default), `browser_sources_default`, and `consent_provider` (`auto`, one consent manager, or `app`).

## 0.11.0

### Added

- **Two-way referral sync.** Referral settings carry two-way sync: `inbound` (`url`, `secret_set`, `endpoint_id`, `last_event`) on reads, write-only `inbound_secret` and `inbound_endpoint_id` on updates (null clears), and provider capability `inbound`.
- `sign_referral_updated_event(...)`: builds and signs a `referral.updated` event (atlas-id / atlas-timestamp / atlas-signature) for a referral platform reporting changes to `POST /v1/webhooks/referrals/{instance_id}`.

## 0.10.0

### Added

- **Referral attribution v2.** `instance.referrals.retry_failed(*, kind=None, error_code=None,
  idempotency_key=None)` (`POST /v1/instance/referrals/calls/retry_failed`,
  `ReferralRetryFailedResult` with `requeued`), `instance.referrals.simulate(*, code=None)`
  (`POST /v1/instance/referrals/simulate`, `ReferralSimulateResult`: `call_id`, `customer_ref`,
  `result`, `response`), `instance.referrals.backfill(body, *, idempotency_key=None)` and
  `instance.referrals.get_backfill(backfill_id)` (`POST /v1/instance/referrals/backfill`,
  `GET /v1/instance/referrals/backfill/{id}`; `ReferralBackfillBody`: `since`, `codes`,
  `code_metadata_path`; `ReferralBackfillJob`: `users_scanned`, `users_skipped`, `calls_queued`,
  `truncated`, `next_since`, `calls`), and `instance.referrals.get_for_user(user_id)`
  (`GET /v1/users/{id}/referral`, `UserReferralResult`).
- **Settings.** `ReferralSettings` and `UpdateReferralSettingsBody` gain `tracking_token`,
  `code_lookup_url`, `signup_code_field`, `forward_lifecycle`, `mirror_to_public_metadata` and
  `include_referral_claims`. `provider` can be `referally`. `ReferralProviderCapabilities` gains
  `alias`, `user` and `ping`. `ReferralConnectionStatus` gains `last_ping` (`ReferralPing`) and
  `alert` (`ReferralAlert`: `signature_rejected` or `connection_paused`).
  `ReferralConnectionTest` gains `method` (`ping` or `probe`), `ping` and `warnings`.
- **Call log.** `instance.referrals.list_calls` takes `error_code` and `starting_after`; `limit`
  goes up to 1000. `ReferralCall.kind` adds `alias`, `user` and `ping`; calls gain `latency_ms`,
  `error_code`, `response`, `highlights` (`ReferralCallHighlights`), `request_id` and `batch_id`.
- **Users.** `users.set_external_id(user_id, external_id)` (`PATCH /v1/users/{id}`; with referrals
  on, the change is forwarded to the platform as an alias). `UserReferral` gains
  `partner_external_ref`, `referral_status` and `notes`. `UserReferralResolvedEvent` types the
  `data` of the new `user.referral_resolved` webhook (the full user).
- **before_user_create hook.** New `instance.hooks` namespace: `get_before_user_create()`,
  `update_before_user_create(body, *, idempotency_key=None)` and `test_before_user_create()`
  (`/v1/instance/hooks/before_user_create`; `BeforeUserCreateHook`,
  `UpdateBeforeUserCreateHookBody`, `BeforeUserCreateHookTest`). The hook call is signed like a
  webhook with type `user.before_create`; verify it with `verify_webhook`.
- **Preflight** can report `referrals_secret_invalid`, `referrals_program_inactive`,
  `referrals_unreachable`, `referrals_clock_skew` and `referrals_external_id_unset`.
- **Referral protocol receiver.** `verify_referral_request` accepts the operations `alias`
  (`/aliases`, `ReferralAliasPayload`), `user` (`/users`, `ReferralUserPayload`) and `ping`
  (`/ping`, `ReferralPingPayload`; answer `ReferralPingResponse`), and
  `ReferralVerification` gains `protocol_version` (the `Atlas-Referrals-Version` header).
  `ReferralSignupResponse` gains optional `notes`. New constants `REFERRAL_PROTOCOL_VERSION`
  (`2026-10-21`) and `REFERRAL_PROTOCOL_VERSION_HEADER`.

### Changed

- On the server, `user["referral"]["status"]` is now where attribution stands (`pending`,
  `attributed`, `none`, `failed`, `held`, `flagged`); the platform's own status moved to
  `referral_status`. The user `referral` is present for every user reported to the platform, and
  `user.created` carries `status: "pending"` while the platform has not answered.

## 0.9.0

### Added

- **Referral attribution settings.** `instance.referrals.get()` and
  `instance.referrals.update(body=None, *, idempotency_key=None)` (`GET`/`PATCH
  /v1/instance/referrals`; `ReferralSettings`, `UpdateReferralSettingsBody` with nested
  `security`: `ReferralSecuritySettings`), `instance.referrals.test()`
  (`ReferralConnectionTest`), `instance.referrals.list_calls(*, limit, status, kind, user_id)`
  (`ReferralCall`) and `instance.referrals.retry_call(call_id, *, idempotency_key=None)`.
  Also `ReferralProvider`, `ReferralProviderCapabilities`, `ReferralConnectionStatus`,
  `ReferralRisk`.
- **Users.** `User` gains `referral` (`UserReferral`: `partner_id`, `referrer_external_id`,
  `referrer_user_id`, `matched_via`, `status`, `risk_level`, `flagged`), `referral_code` and
  `referral_link`. `CreateUserBody` accepts `referral` (`CreateUserReferral`: `code`,
  `click_id`, `anon_id`) and `referral_code`; `UpdateUserBody` accepts `referral_code` (`None`
  clears). New `users.flag_referral(user_id, *, reason=None, idempotency_key=None)`
  (`UserReferralFlag`).
- **Webhooks.** `UserReferralAttributedEvent` types the `data` of the new
  `user.referral_attributed` event.
- **Error codes.** `ErrorCode.REFERRALS_NOT_CONFIGURED` (422) and
  `ErrorCode.REFERRAL_CODE_TAKEN` (409). Preflight can report `referrals_enabled_unverified`
  and `referrals_without_bot_protection`.
- **Referral protocol receiver.** `verify_referral_request(body, headers, secret, *, path=None,
  expected_op=None, now_ms=None, tolerance_ms=...)` verifies a call from Atlas to a referral platform
  (the webhook signature scheme; every call is a POST whose signed body carries `op` and
  `customerRef`) and returns `ReferralVerification` (`op`: `signup`, `erase`, `export`, `partner`,
  `signal`; `payload`, `customer_ref`, `test`, `delivery_id`, `timestamp`, `idempotency_key`). It
  refuses a body that is not an object (`malformed_body`), a missing or unknown `op`, a path that is
  not a protocol endpoint (`unknown_endpoint`) and an `op` that does not match the path or
  `expected_op` (`op_mismatch`). Payload types `ReferralSignupPayload`, `ReferralSignupResponse`,
  `ReferralErasePayload`, `ReferralExportPayload`, `ReferralPartnerPayload`,
  `ReferralSignalPayload`, `ReferralContext`, `ReferralRiskVerdict`, `ReferralOp`;
  `referral_op_for_path`; constants `REFERRAL_OP_ENDPOINTS`, `REFERRAL_CONNECTION_TEST_REF`,
  `REFERRAL_PROTOCOL_USER_AGENT`, `REFERRAL_SIGNAL_TYPES`.

## 0.8.0

### Added

- **Trusted reverse proxy secret.** `instance.get_proxy_secret()` (`ProxySecret`: `set`,
  `created_at`, `previous_expires_at`, `secret_header`, `client_ip_header`),
  `instance.create_proxy_secret(body=None)` (`CreateProxySecretBody`: `overlap_seconds`;
  returns `ProxySecretCreated` with `secret`, shown once, and `rotated`) and
  `instance.delete_proxy_secret()` (`InstanceDeleteProxySecretResult`).
- **Webhook secret rotation with an overlap.** `webhooks.endpoints.rotate_secret(endpoint_id,
  body=None)` takes `RotateWebhookSecretBody` (`overlap_seconds`, default 0, at most 604800).
  `WebhookSecretRotation` gains `overlap_seconds` and `previous_secret_expires_at`;
  `WebhookEndpoint` gains `previous_secret_expires_at` (and `failing_since`).
- **Per-instance platform rotation with an overlap.** `apps.rotate_instance_secret(app_id,
  instance_id, body=None, *, idempotency_key=None)` takes `RotatePlatformSecretBody`
  (`overlap_seconds`, default 259200, `0` revokes the prior keys now) and returns
  `PlatformInstanceSecretRotation` (`app_id`, `instance_id`, `secret`, `overlap_seconds`,
  `previous_keys_expire_at`).
- **Sign in with Atlas apps.** `atlas_id_apps.rotate_secret(app_id, body=None)` (default 24
  hours, `0` = now) and `atlas_id_apps.rotate_webhook_secret(app_id, body=None)` (default 0)
  take `RotateAtlasIdAppSecretBody`. `AtlasIdApp` gains `previous_secret_expires_at`,
  `secret_issued_at`, `webhook_previous_secret_expires_at` and `overlap_seconds`.

### Changed

- `apps.rotate_instance_secret` is typed `PlatformInstanceSecretRotation` (was `AppSecret`,
  whose `id` the API never sent). Calls without a body keep working; note that the server now
  keeps the prior keys for 72 hours by default. Pass `{"overlap_seconds": 0}` to revoke them at
  once, as before.

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
