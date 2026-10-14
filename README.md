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
    {"script_url": "https://cmp.example/consent.js", "site_id": "site_123"}
)
print(atlas.instance.cookie_consent.get()["enabled"])
atlas.instance.cookie_consent.delete()
```

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
`ErrorCode.EMAIL_DELIVERY_NOT_CONFIGURED` and `ErrorCode.EMAIL_PROVIDER_REQUIRED`.

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
