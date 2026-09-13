# atlas-backend

The official **Python backend SDK** for Atlas — a typed client over the `sk_`
Backend API (BAPI). It is the Python peer of the TypeScript `@atlas/backend`
SDK and mirrors it namespace-for-namespace.

- Typed (`py.typed`), one namespace per BAPI area.
- Sync `AtlasClient` **and** async `AsyncAtlasClient`, built on `httpx`.
- The `{ errors: [{ code, message, param }] }` envelope surfaces as `AtlasError`.
- Cursor pagination helper, `Idempotency-Key` on creates.

## Install

```bash
pip install atlas-backend
```

## Quick start

```python
from atlas_backend import AtlasClient, AtlasError, paginate

atlas = AtlasClient("sk_live_...", base_url="https://api.atlas.dev")

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

| Argument      | Default                   | Notes                                            |
| ------------- | ------------------------- | ------------------------------------------------ |
| `secret_key`  | —                         | `sk_...`; sent as `Authorization: Bearer <key>`. |
| `base_url`    | `https://api.atlas.dev`   | The instance's BAPI origin (`BAPI_ORIGIN`).      |
| `timeout`     | `30.0`                    | Per-request timeout, seconds.                    |
| `http_client` | a new `httpx.Client`      | Pass your own for pooling / proxies / retries.   |

## Namespaces

`users`, `sessions`, `organizations` (+ `memberships`, `invitations`,
`domains`, `group_roles`), `roles`, `permissions`, `oauth_clients` (+ `grants`),
`resource_servers`, `sso_connections`, `scim_tokens`, `domains`, `waitlist`,
`allowlist`, `blocklist`, `attack_protection`, `actor_tokens`, `invitations`,
`webhooks` (+ `endpoints`), `sign_in_tokens`, `audit_logs`, `jwt_templates`.

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

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy .
pytest
```
