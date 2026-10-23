# atlas-backend

The official **Python backend SDK** for Atlas — a typed client over the `sk_`
Backend API (BAPI) and the `psk_` Platform API. It is the Python peer of the
TypeScript `@atlasauth/backend` SDK.

- Covers every Backend API and Platform API operation in the public API reference.
- Typed (`py.typed`): request bodies and responses are `TypedDict`s in
  `atlas_backend.models`, generated from the API reference.
- Sync `AtlasClient` **and** async `AsyncAtlasClient`, built on `httpx`; the
  platform-key surface is `AtlasPlatformClient` / `AsyncAtlasPlatformClient`.
- The `{ errors: [{ code, message, param }] }` envelope surfaces as `AtlasError`,
  with every stable code on `ErrorCode`.
- Cursor pagination helpers, `Idempotency-Key` on creates, strict request bodies.
- Session-token, API-key and back-channel logout-token verification.

## Install

```bash
pip install atlas-backend
```

## Quick start

```python
from atlas_backend import AtlasClient, AtlasError, paginate

atlas = AtlasClient("sk_live_...", base_url="https://api.atlasauth.net")

# Create a user (idempotency key optional, forwarded as Idempotency-Key).
user = atlas.users.create(
    {"email_address": "ada@example.com", "first_name": "Ada"},
    idempotency_key="signup-ada-001",
)
print(user["id"])

# List organizations (a single cursor page).
page = atlas.organizations.list(limit=20)
print(page["data"], page["has_more"], page["next_cursor"])

# Auto-iterate every page.
for org in paginate(atlas.organizations.list):
    print(org["name"])

# Errors carry the HTTP status and the stable BAPI error code.
try:
    atlas.users.get("user_does_not_exist")
except AtlasError as err:
    print(err.status)          # e.g. 404
    print(err.code)            # e.g. "NOT_FOUND"
    print(err.errors[0].get("param"))
    if err.has_code("NOT_FOUND"):
        ...
```

### Context manager

```python
with AtlasClient("sk_live_...") as atlas:
    atlas.users.list(limit=10)
# underlying httpx.Client is closed on exit
```

## Async

```python
import asyncio
from atlas_backend import AsyncAtlasClient, acollect

async def main() -> None:
    async with AsyncAtlasClient("sk_live_...") as atlas:
        user = await atlas.users.create({"email_address": "grace@example.com"})
        orgs = await acollect(atlas.organizations.list)
        print(user["id"], len(orgs))

asyncio.run(main())
```

## Configuration

| Argument            | Default                     | Notes                                                        |
| ------------------- | --------------------------- | ------------------------------------------------------------ |
| `secret_key`        | —                           | `sk_...`; sent as `Authorization: Bearer <key>`.             |
| `base_url`          | `https://api.atlasauth.net` | The instance's Backend API origin.                           |
| `timeout`           | `30.0`                      | Per-request timeout, seconds.                                |
| `http_client`       | a new `httpx.Client`        | Pass your own for pooling / proxies / retries.               |
| `strict`            | `None`                      | `True`/`False` sends `Atlas-Strict` on every write (below).  |
| `on_unknown_fields` | log a warning               | Called with fields Atlas ignored on a write (below).        |

## Strict request bodies

By default a write that includes a field the endpoint does not accept still
succeeds; Atlas ignores the field and names it in the `Atlas-Unknown-Fields`
response header. The SDK reports that header to you, so a typo never goes
unnoticed:

```python
def report(fields: list[str], method: str, path: str) -> None:
    print(f"Atlas ignored {fields} on {method} {path}")

atlas = AtlasClient("sk_live_...", on_unknown_fields=report)
```

Without a hook the SDK logs a warning on the `atlas_backend` logger.

To refuse unknown fields instead (`422` with code `UNKNOWN_FIELD`, before anything
changes), turn on strict mode for the whole client, or for one call:

```python
from atlas_backend import AtlasClient, AtlasError, ErrorCode

atlas = AtlasClient("sk_live_...", strict=True)       # every write is strict

try:
    AtlasClient("sk_live_...").with_options(strict=True).users.update(
        "user_123", {"first_name": "Ada", "nickname": "ada"}
    )
except AtlasError as err:
    if err.has_code(ErrorCode.UNKNOWN_FIELD):
        print("unknown field:", err.errors[0].get("param"))
```

`strict=False` sends `Atlas-Strict: false`, opting a request out when your
instance makes strict bodies the default. `with_options(...)` returns a copy that
shares the connection; it works on every client class.

## Platform client and Sign in with Atlas apps

A platform key (`psk_...`) manages the apps and instances your platform owns,
and registers **Sign in with Atlas** apps (OpenID Connect clients on
`https://atlasauth.net`):

```python
from atlas_backend import AtlasPlatformClient

platform = AtlasPlatformClient("psk_live_...")

app = platform.atlas_id_apps.create(
    {
        "name": "Acme",
        "redirect_uris": ["https://acme.example/auth/callback"],
        "post_logout_redirect_uris": ["https://acme.example/"],
        "backchannel_logout_uri": "https://acme.example/auth/backchannel-logout",
        "backchannel_logout_session_required": True,
        "allowed_scopes": ["openid", "profile", "email"],
        "branding": {
            "theme": "auto",
            "accent_color": "#4f46e5",
            "privacy_policy_url": "https://acme.example/privacy",
            "copy": {"sign_in_title": "Sign in to Acme"},
            "design": {"preset": "glass"},
        },
    },
    idempotency_key="acme-siwa-app",
)
print(app["client_id"], app.get("client_secret"))   # the secret is shown once

apps = platform.atlas_id_apps.list()
print(apps["issuer"], apps["discovery_url"])

platform.atlas_id_apps.update(app["id"], {"branding": {"copy": {"sign_in_title": None}}})
platform.atlas_id_apps.rotate_secret(app["id"])
preview = platform.atlas_id_apps.preview_design({"design": {"preset": "midnight"}})

with open("logo.png", "rb") as f:
    asset = platform.design_assets.upload(f.read(), kind="logo")
```

Other namespaces: `apps` (create, list, archive, transfer, instances, secret
rotation), `accountless_apps`, `design_assets`.

## Setup check (preflight)

```python
report = atlas.instance.preflight()
for finding in report["findings"]:      # errors first, then warnings, then info
    print(finding["severity"], finding["code"], finding["message"], "->", finding["fix"])
```

## Design

The sign-in page design is typed end to end (`models.AtlasDesign` for a full
design, `models.AtlasDesignPatch` for a partial update where `None` removes a
setting):

```python
atlas.design.update({"design": {"preset": "forest", "palette": {"primary": "#0f766e"}}})
atlas.design.replace({"design": {"version": 1, "preset": "atlas", "colorScheme": "auto"}})
preview = atlas.design.preview({"design": {"preset": "bold"}})
catalog = atlas.design.catalog()           # presets, fonts, CSS variables

# Per-organization overrides
atlas.organizations.design.update("org_123", {"design": {"palette": {"accent": "#f59e0b"}}})

# Images: send the raw bytes; the type is detected (PNG, JPEG, GIF, WebP)
with open("background.jpg", "rb") as f:
    asset = atlas.design.assets.upload(f.read(), kind="background")
atlas.design.update({"design": {"background": {"image": {"assetId": asset["asset_id"]}}}})
```

## Cookie consent

```python
atlas.instance.cookie_consent.set(
    {
        "script_url": "https://cmp.example/consent.js",
        "site_id": "site_123",
        # Optional "cookie settings" link that reopens the CMP preferences
        "settings_link": {"label": "Cookie settings", "preset": "cookiebot"},
    }
)
print(atlas.instance.cookie_consent.get()["enabled"])
atlas.instance.cookie_consent.delete()
```

A settings link needs a `preset` (`"cookiemunch"`, `"cookiebot"`, `"onetrust"` or
`"custom"`) or at least one entry in `attributes` (`data-*`, `aria-*`, `id`, `class`,
`href`). `None` removes the link. The response's `settings_link.rendered_attributes`
are the attributes the rendered link carries: yours plus the preset's trigger.

## Messaging providers

Each transport has its own typed config (`models.EmailProviderConfig`,
`models.SmsProviderConfig`):

```python
atlas.messaging_providers.set_email(
    {
        "transport": "smtp",
        "from_address": "Acme <no-reply@acme.example>",
        "config": {"host": "smtp.acme.example", "port": 587, "username": "u", "password": "p"},
    }
)
atlas.messaging_providers.set_sms(
    {"transport": "twilio", "config": {"account_sid": "AC...", "auth_token": "..."}}
)
atlas.messaging_providers.test("email", {"to": "ops@acme.example"})
```

Removing the email provider while email-dependent features are on (and nothing else
would deliver email) raises a 409 `EMAIL_PROVIDER_IN_USE`; the error's
`meta["features"]` lists them. Pass `force=True` to remove it anyway:

```python
atlas.messaging_providers.delete("email", force=True)
```

## Social and wallet sign-in providers

```python
configured = atlas.oauth_providers.list(provider=["google", "github"], configured=True)

# Re-brand a button without touching credentials; None clears an override
atlas.oauth_providers.upsert("google", {"display_name": "Google Workspace", "icon_url": None})

# Wallet providers take verifier settings instead of credentials
atlas.oauth_providers.upsert(
    "siwe", {"settings": {"domain": "app.acme.example", "chain_ids": [1, 10]}}
)
atlas.oauth_providers.set_enabled("siwe", {"enabled": True})
```

## Webhooks

```python
ep = atlas.webhooks.endpoints
created = ep.create({"url": "https://acme.example/hooks", "enabled_events": ["user.created"]})
ep.update(created["id"], {"active": False})
ep.reveal_secret(created["id"])
ep.rotate_secret(created["id"])
ep.test(created["id"])
for delivery in ep.list_deliveries(created["id"], limit=20)["data"]:
    ep.redeliver(created["id"], delivery["id"])
```

`verify_webhook` accepts an `atlas-signature` header that carries several signatures separated
by spaces (`v1,<sig> v1,<sig>`). While an endpoint secret rotates, Atlas may sign each delivery
with the old and the new secret; the delivery verifies when any one signature matches.

By default a rotation stops the old secret at once. Pass `overlap_seconds` (at most 7 days) to
keep it signing each delivery next to the new one while you deploy the new secret. Choose an
overlap only once every receiver verifies with a verifier that accepts several signatures.

```python
rotated = ep.rotate_secret(created["id"], {"overlap_seconds": 3600})
rotated["previous_secret_expires_at"]  # epoch ms, or None when the old secret already stopped
```

## Policy acceptance

Terms of Service, privacy policies and any other policy your users accept at sign-up (and again
at sign-in when a new version takes effect). A version goes draft, published (with an
`effective_at`), retired; each acceptance is kept as evidence.

```python
atlas.policies.create({"key": "tos", "title": "Terms of Service", "applies_to": "sign_in_and_sign_up",
                       "reaccept": "grace", "grace_days": 14})
atlas.policies.versions.create("tos", {"version": "2026-10-24", "content_markdown": "# Terms\n..."})
atlas.policies.versions.publish("tos", "2026-10-24", {"effective_at": "2026-11-01T00:00:00Z"})
atlas.policies.list_acceptances("tos", version="2026-10-24", limit=50)
csv_text = atlas.policies.export_acceptances_csv("tos")
atlas.policies.for_user("user_123")            # standing on every policy, incl. needs_acceptance
atlas.policies.settings.update({"session_claim": True})   # put `pol` on session tokens
```

With the session claim on, `SessionClaims.policies` / `accepted_policy_version("tos")` read the
`pol` claim. The `user.policy_accepted` and `policy.version_published` webhook events have the
constants `WEBHOOK_EVENT_USER_POLICY_ACCEPTED` and `WEBHOOK_EVENT_POLICY_VERSION_PUBLISHED`.

### Serving policies from your own system (policy source)

Point Atlas at a CMS or service with `atlas.policy_source.update({"enabled": True,
"endpoint_url": ..., "signing_secret": ...})` (the secret is write-only), then `test()` / `sync()`.
In your service, verify Atlas's signed `GET {endpoint}/policies[?key=...]` and answer a feed:

```python
from atlas_backend import verify_policy_feed_request, sign_policy_source_event

v = verify_policy_feed_request(request.method, request.full_path, request.headers, secret)
if not v.verified:
    abort(401)
feed = {"object": "policy_list", "policies": build_policies(only=v.key)}

# When a policy changes, tell Atlas (it re-fetches; nothing in the event is trusted as content):
signed = sign_policy_source_event({"type": "policy.published", "key": "tos", "version": "2026-10-24"}, secret)
httpx.post(webhook_url, content=signed.body, headers={"content-type": "application/json", **signed.headers})
```

## OAuth client secret rotation

The previous secret keeps working for `overlap_seconds` (default 24 hours, at most 7 days), so
you can deploy the new one without downtime. Pass `0` to revoke it now, for example after a leak.

```python
rotated = atlas.oauth_clients.rotate_secret(client_id, {"overlap_seconds": 3600})
rotated["client_secret"]               # shown once
rotated["previous_secret_expires_at"]  # epoch ms, or None when the old secret already stopped
```

## Trusted reverse proxy

If a reverse proxy serves the Frontend API from your own origin, give it a proxy secret. It
sends the secret in `X-Atlas-Proxy-Secret` and the browser's IP in `X-Atlas-Client-IP`; Atlas
then uses that IP for rate limits, lockout, risk signals and audit logs.

```python
created = atlas.instance.create_proxy_secret()
created["secret"]                      # shown once; store it in your proxy's environment
atlas.instance.get_proxy_secret()      # set, created_at, previous_expires_at (never the secret)
atlas.instance.create_proxy_secret({"overlap_seconds": 3600})  # rotate; the old one works 1 hour
atlas.instance.delete_proxy_secret()
```

## Rotation overlaps on the platform

```python
platform.apps.rotate_instance_secret(app_id, instance_id, {"overlap_seconds": 0})  # default 72 hours
platform.atlas_id_apps.rotate_secret(app["id"], {"overlap_seconds": 3600})        # default 24 hours
platform.atlas_id_apps.rotate_webhook_secret(app["id"], {"overlap_seconds": 3600}) # default 0
```

## Development email

A development instance can send Atlas's sign-in emails through your own provider without a
verified domain. Subjects start with `[Atlas test] ` and sends are capped.

```python
dev = atlas.messaging_providers.development_email
dev.enable({"provider_id": "mp_123"})  # or {"transport": "resend", "config": {"api_key": "re_..."}}
dev.get()
dev.disable()  # back to standard mode; the provider stays
```

## API key spend caps

Give an end-user API key caps per unit and period (`"request"`, `"day"`, `"month"` or
`"total"`), then meter what each call costs. A debit that would exceed a cap records
nothing and comes back with `allowed: False`; it is not raised as an error.

```python
key = atlas.api_keys.create({
    "subject_type": "user",
    "subject_id": "user_123",
    "limits": [
        {"unit": "requests", "amount": 1000, "period": "day"},
        {"unit": "usd_cents", "amount": 5000, "period": "month"},
    ],
})

debit = atlas.api_keys.record_usage(
    key["id"],
    {"unit": "usd_cents", "amount": 12, "idempotency_key": "req_8f2c"},  # retries count once
)
if not debit["allowed"]:
    ...  # debit["code"] == "LIMIT_EXCEEDED"; debit["exceeded"] lists the caps

print(atlas.api_keys.get_usage(key["id"])["usage"])  # used / remaining / resets_at per cap
atlas.api_keys.update(key["id"], {"limits": None})  # remove the caps
```

`api_keys.verify(...)` also returns the key's `name`, `scopes`, `constraints`, `limits`
and current `usage`.

## Session keep-alive

If your app loads the Atlas frontend SDK only on some pages, time spent on the other
pages can count as inactivity. Touch the session from your backend to slide its
inactivity window:

```python
s = atlas.sessions.touch(session_id)
# s["idle_expires_at"] is the new deadline; s["extended"] is False when a touch in the last minute already did it
```

A touch never extends past the session's absolute expiry and never revives an ended
session (409 `SESSION_REVOKED`, `SESSION_IDLE_EXPIRED` or `SESSION_EXPIRED`). It writes
at most once a minute, so calling it on every request is safe.

Every session read (`sessions.get`, `sessions.list`, `users.list_sessions`) carries
`idle_expires_at` (the same value as `abandon_at`), `last_active_organization_id` and
`impersonated_by`.

## Skipping the logout confirmation

A first-party OAuth client can set `skip_logout_confirmation=True` on
`oauth_clients.create` / `update`. Sign-out through `/oauth2/logout` with that
`client_id` and an exactly registered `post_logout_redirect_uri` then ends the session
and redirects straight back with `state`, without the confirmation page. A third-party
client is refused with 422 `VALIDATION_FAILED`.

```python
atlas.oauth_clients.update(client_id, {"skip_logout_confirmation": True})
```

## Entitlements and organization policy

```python
atlas.entitlement_overrides.create(
    {"subject_type": "org", "subject_id": "org_123", "limits": {"seats": -1}}  # -1 = unlimited
)
print(atlas.organizations.get_entitlements("org_123"))

# Policy keys are camelCase; None clears an override
atlas.organizations.update_policy(
    "org_123",
    {"requireMfa": True, "allowedSignInMethods": ["password", "oauth:google"], "ipAllowlist": None},
)
```

## Domain moves, logout fan-out and managed email

```python
# Move every URL from the old origin to the new one. dry_run first shows the diff.
preview = atlas.instance.move_origin({"from": "https://old.example.com", "to": "https://example.com", "dry_run": True})
for change in preview["changes"]:
    print(change["object"], change["field"], change["before"], "->", change["after"])

# Send the same logout_token your OIDC apps get to another service.
atlas.logout_notify_endpoints.create({"url": "https://api.example.com/atlas/logout"})

# Send email from your own domain through Atlas, then publish the returned DNS records.
managed = atlas.messaging_providers.managed_email.create({"from_address": "Acme <no-reply@example.com>"})
print(managed["records"])
```

On the platform client, `atlas_id_apps.find_users(app_id, email)` answers a privacy request for one app,
`atlas_id_apps.revoke_grant(app_id, grant_id)` revokes one person's approval, and `atlas_id_publisher` claims and
verifies the publisher name shown on consent screens.

## Referral attribution

With referral attribution on, Atlas reports every interactive sign-up to your referral platform
before `user.created` is sent. The user gains `referral` (where attribution stands and, once
attributed, who referred them; `None` when the user was never reported), `referral_code` and
`referral_link`. `referral["status"]` is `pending`, `attributed`, `none`, `failed`, `held` or
`flagged`; the platform's own status is `referral["referral_status"]`.

```python
atlas.instance.referrals.update({
    "enabled": True,
    "provider": "webhook",  # the Atlas referral protocol; or "referally" or another built-in adapter
    "endpoint_url": "https://referrals.example.com/atlas",
    "signing_secret": os.environ["REFERRAL_SIGNING_SECRET"],
    "auto_enroll_users": True,
    "security": {"on_high_risk": "hold"},
})
print(atlas.instance.referrals.test())            # {"ok": True, "http_status": 404, ...}
failed = atlas.instance.referrals.list_calls(status="failed", limit=20)
atlas.instance.referrals.retry_call(failed["data"][0]["id"])

atlas.users.update("user_123", {"referral_code": "ada-1"})   # 409 REFERRAL_CODE_TAKEN if held
atlas.users.flag_referral("user_123", reason="self-referral")
```

More tools for the connection:

```python
referrals = atlas.instance.referrals
referrals.update({"forward_lifecycle": True, "include_referral_claims": True,
                  "signup_code_field": True})
referrals.simulate(code="ACME10")             # a sign-up call for a made-up user; nothing is stored
referrals.retry_failed(error_code="signature_rejected")   # after pasting the new secret
page = referrals.list_calls(limit=1000, error_code="timeout")
while page["has_more"]:
    page = referrals.list_calls(limit=1000, starting_after=page["data"][-1]["id"])
job = referrals.backfill({"since": "2026-01-01", "code_metadata_path": "public_metadata.referral_code"})
referrals.get_backfill(job["id"])             # running, then completed
referrals.get_for_user("user_123")            # the stored result, no call to the platform

atlas.users.set_external_id("user_123", "cust_42")   # forwarded to the platform as an alias
```

To give each user your own id before the first referral call, turn on the `before_user_create`
hook. Atlas then sends your endpoint a signed `POST` (verify it with `verify_webhook`) of type
`user.before_create` for every self-service sign-up, and stamps the `external_id` and metadata you
answer:

```python
atlas.instance.hooks.update_before_user_create({
    "enabled": True,
    "url": "https://app.example.com/hooks/before-create",
    "signing_secret": os.environ["BEFORE_CREATE_SECRET"],
})
atlas.instance.hooks.test_before_user_create()   # {"ok": True, "answer": {...}}
```

Enabling without what the provider needs is `422 REFERRALS_NOT_CONFIGURED`. When the platform has
not answered by the time `user.created` is sent, `referral["status"]` is `pending` and the
`user.referral_resolved` webhook follows with the final user (`attributed`, `none` or `failed`).
`user.referral_attributed` (`UserReferralAttributedEvent`) still fires for a late attribution.

A referral platform that implements the Atlas referral protocol verifies Atlas's calls with
`verify_referral_request`. Every call is a POST signed like a webhook, and its JSON body says which
operation it is (`op`: `signup`, `erase`, `export`, `partner`, `signal`, `alias`, `user`, `ping`).
Pass the path the call arrived
on: a signed body whose `op` does not match the endpoint is refused (`op_mismatch`).

```python
from atlas_backend import verify_referral_request

result = verify_referral_request(raw_body, headers, secret, path=request.path)
if not result.verified:
    return 401
if result.op == "signup":
    return {"referral": match(result.payload), "partner": None}
if result.op == "export":
    return 404 if result.test else export_for(result.customer_ref)
if result.op == "alias":       # the user's external_id changed: re-key the customer
    rekey(result.payload["fromCustomerRef"], result.payload["toCustomerRef"])
if result.op == "ping":
    return {"ok": True, "serverTime": datetime.now(timezone.utc).isoformat()}
```

`result.protocol_version` is the `Atlas-Referrals-Version` header (`2026-10-21`).

A retry of one call keeps its `delivery_id`; sign-ups are idempotent on `customerRef`, so answer a
retry the same way.

Browser capture: `browser_sources` lists the referral programs whose script or cookie the browser
reads (`None` on update goes back to the provider's default, reported by `browser_sources_default`),
and `consent_provider` picks the consent manager that decides (`auto`, one manager, or `app`).

### Two-way sync

A provider with the `inbound` capability can send referral changes made after sign-up back to
Atlas. The settings report `inbound` (`url` to give the platform, `secret_set`, `endpoint_id` and
`last_event` with `at`, `type`, `outcome`). Store the platform's event secret with `inbound_secret`
(write-only, 16-512 characters) and its subscription id with `inbound_endpoint_id`; `None` clears.

A platform on the Atlas referral protocol sends a `referral.updated` event to `inbound.url`, signed
like an Atlas webhook with the inbound secret (or the connection's signing secret when none is set):

```python
from atlas_backend import sign_referral_updated_event

event = sign_referral_updated_event(
    inbound_url, secret, {"customerRef": "user_123", "referralId": "ref_1", "status": "qualified"}
)
httpx.post(event.url, content=event.body, headers=event.headers)
```

## Back-channel logout

When a user signs out of Atlas, Atlas POSTs a signed `logout_token` to your app's
`backchannel_logout_uri`. Verify it, end the matching local sessions, and answer
`200`:

```python
from atlas_backend import LogoutTokenVerifier, VerificationError, logout_token_from_form

verifier = LogoutTokenVerifier(
    issuer="https://atlasauth.net",        # the issuer in your id_tokens
    client_id="your_client_id",
)

def backchannel_logout(raw_body: bytes) -> tuple[int, dict[str, str]]:
    """Framework-agnostic handler: returns (status, headers)."""
    headers = {"Cache-Control": "no-store"}
    try:
        claims = verifier.verify(logout_token_from_form(raw_body))
    except VerificationError:
        return 400, headers
    if claims.sid:
        sessions.delete_by_atlas_sid(claims.sid)       # your session store
    else:
        sessions.delete_all_for_user(claims.sub)       # "sign out everywhere"
    return 200, headers
```

The verifier checks the RS256 signature against the issuer's keys (cached, with
a throttled refetch), `iss`, that `aud` contains your client id, `iat` (not in the
future), `exp` when present, `jti`, the back-channel logout event, that `sid` or
`sub` is present, that there is no `nonce`, and `typ: logout+jwt`.

**Replay protection.** Pass `jti_seen=` a callable that records each `jti` and
returns `True` when it has seen it before (the token is then refused with reason
`"replayed"`). Keep entries a few minutes — logout tokens live two. With several
app servers, back it with a shared store such as Redis (`SET jti 1 NX EX 300`).

## Namespaces

`AtlasClient` / `AsyncAtlasClient`:

`users` (+ `identities`, `phone_numbers`, `consents`, `deletion`, `directives`,
`approval_requests`, `grants`, `erasure`, `notification_preferences`),
`sessions`, `organizations` (+ `memberships`, `invitations`, `domains`,
`group_roles`, `audit_streams`, `branding`, `design`, `settings`, `end_users`,
`reader_domain`), `roles`, `permissions`, `oauth_clients` (+ `grants`),
`oauth_providers`, `resource_servers`, `sso_connections`, `sso_onboarding`,
`scim_tokens`, `scim_provisioning_targets`, `org_ldap_connections`, `domains`,
`redirect_urls`, `email_addresses`, `waitlist`, `allowlist`, `blocklist`,
`invitations`, `attack_protection`, `actor_tokens`, `sign_in_tokens`,
`api_keys`, `tokens`, `m2m_tokens`, `machines`, `machine_enrolment_tokens`,
`tickets`, `grants`, `session_exchange_apps`, `instance` (+ `cookie_consent`,
`security`), `design` (+ `assets`), `branding`, `localizations`,
`email_templates`, `sms_templates`, `messaging_providers`, `notifications` (+
`categories`, `templates`), `webhooks` (+ `endpoints`), `log_streams`,
`audit_logs`, `audit_events`, `config_changelog`, `events`, `usage`, `jobs`,
`user_imports`, `user_exports`, `data_subject_requests`, `entitlement_overrides`,
`organization_settings_schema`, `billing` (+ `plans`, `subscriptions`), `actions`,
`policies` (+ `versions`, `settings`), `policy_source`,
`connectors`, `directory`, `fga` (+ `stores`, `authorization_models`), `openfga`
(+ `stores`, `authorization_models`), `jwt_templates`, `legacy_auth_connection`,
`network_acls`, `radius_clients`, `lti_platforms`, `rate_limit_policy`,
`risk_based_mfa`, `bot_labels`, `bot_signals`, `captcha`, `managed_waf`,
`diagnostics`, `mcp`, `mcp_connector`, `pca`, `testing`.

`AtlasPlatformClient` / `AsyncAtlasPlatformClient`: `apps`, `accountless_apps`,
`atlas_id_apps`, `design_assets`.

## Pagination

`paginate(list_fn, **params)` and `collect(list_fn, **params)` walk every
cursor page of any `list` that returns `{ data, has_more, next_cursor }`. Async
peers: `aiterate` / `acollect`.

## Errors

Every non-2xx raises `AtlasError`, carrying:

- `status` — the HTTP status code.
- `errors` — the full `[{ code, message, param?, meta? }]` envelope.
- `code` — the first error's stable code (what you branch on).
- `has_code(code)` — True if any error in the envelope has that code.

`ErrorCode` lists the stable codes, for example `ErrorCode.UNKNOWN_FIELD`,
`ErrorCode.INVALID_KEY`, `ErrorCode.WRONG_KEY_SURFACE` (a valid key used on the
wrong API, e.g. a platform key on an instance route), `ErrorCode.PLAN_IN_USE`,
`ErrorCode.EMAIL_DELIVERY_NOT_CONFIGURED`, `ErrorCode.EMAIL_PROVIDER_REQUIRED` and
`ErrorCode.EMAIL_PROVIDER_IN_USE`.

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy
pytest
```

The async namespaces are generated from the sync ones. After editing
`atlas_backend/resources.py`, run:

```bash
python scripts/gen_async.py && ruff format atlas_backend/aresources.py
```

`tests/test_parity.py` fails if the two drift, and `tests/test_coverage.py`
checks every operation in `tests/openapi_operations.txt` has a method.
