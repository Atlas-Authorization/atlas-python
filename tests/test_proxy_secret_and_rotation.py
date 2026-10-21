"""The trusted reverse proxy secret and secret rotation with an overlap for webhook
endpoints, per-instance platform keys and Sign in with Atlas apps.

All HTTP is mocked with respx; each test asserts the method, path and body the SDK
sends, and that the response decodes.
"""

from __future__ import annotations

import json

import httpx
import respx

from atlas_backend import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasClient,
    AtlasPlatformClient,
)

API_URL = "https://api.example.test"
PROXY = f"{API_URL}/v1/instance/proxy_secret"

PROXY_VIEW = {
    "object": "proxy_secret",
    "set": True,
    "created_at": 1_800_000_000_000,
    "previous_expires_at": None,
    "secret_header": "X-Atlas-Proxy-Secret",
    "client_ip_header": "X-Atlas-Client-IP",
}


def client() -> AtlasClient:
    return AtlasClient("sk_test_x", base_url=API_URL)


def platform() -> AtlasPlatformClient:
    return AtlasPlatformClient("psk_test_x", base_url=API_URL)


def body_of(route: respx.Route) -> object:
    return json.loads(route.calls.last.request.content)


@respx.mock
def test_proxy_secret_get_create_rotate_delete() -> None:
    get = respx.get(PROXY).mock(return_value=httpx.Response(200, json=PROXY_VIEW))
    post = respx.post(PROXY).mock(
        return_value=httpx.Response(
            200,
            json={
                **PROXY_VIEW,
                "previous_expires_at": 1_800_003_600_000,
                "secret": "aps_new",
                "rotated": True,
            },
        )
    )
    delete = respx.delete(PROXY).mock(
        return_value=httpx.Response(200, json={"object": "proxy_secret", "deleted": True})
    )
    instance = client().instance

    view = instance.get_proxy_secret()
    assert get.called
    assert view["set"] is True and view["client_ip_header"] == "X-Atlas-Client-IP"

    # No body: create, or rotate with the server default overlap.
    instance.create_proxy_secret()
    assert post.calls.last.request.content == b""

    rotated = instance.create_proxy_secret({"overlap_seconds": 3600})
    assert body_of(post) == {"overlap_seconds": 3600}
    assert rotated["secret"] == "aps_new"
    assert rotated["rotated"] is True
    assert rotated["previous_expires_at"] == 1_800_003_600_000

    assert instance.delete_proxy_secret()["deleted"] is True
    assert delete.called


@respx.mock
def test_webhook_rotate_secret_with_overlap() -> None:
    route = respx.post(f"{API_URL}/v1/webhook_endpoints/whep_1/rotate_secret").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "webhook_secret",
                "secret": "whsec_new",
                "overlap_seconds": 3600,
                "previous_secret_expires_at": 1_800_003_600_000,
            },
        )
    )
    ep = client().webhooks.endpoints
    out = ep.rotate_secret("whep_1", {"overlap_seconds": 3600})
    assert body_of(route) == {"overlap_seconds": 3600}
    assert out["overlap_seconds"] == 3600
    assert out["previous_secret_expires_at"] == 1_800_003_600_000

    # The 0.7 call still works and sends no body (the server default: no overlap).
    ep.rotate_secret("whep_1")
    assert route.calls.last.request.content == b""


@respx.mock
def test_platform_instance_rotation_with_overlap_and_idempotency() -> None:
    route = respx.post(f"{API_URL}/v1/platform/apps/app_1/instances/ins_1/rotate_secret").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "app_secret",
                "app_id": "app_1",
                "instance_id": "ins_1",
                "secret": "sk_live_new",
                "overlap_seconds": 0,
                "previous_keys_expire_at": None,
                "note": "Store it now.",
            },
        )
    )
    apps = platform().apps
    out = apps.rotate_instance_secret(
        "app_1", "ins_1", {"overlap_seconds": 0}, idempotency_key="idem-1"
    )
    request = route.calls.last.request
    assert body_of(route) == {"overlap_seconds": 0}
    assert request.headers["idempotency-key"] == "idem-1"
    assert out["instance_id"] == "ins_1"
    assert out["previous_keys_expire_at"] is None

    # The 0.7 call: no body (default 72 hours), idempotency key by keyword.
    apps.rotate_instance_secret("app_1", "ins_1", idempotency_key="idem-2")
    request = route.calls.last.request
    assert request.content == b""
    assert request.headers["idempotency-key"] == "idem-2"


@respx.mock
def test_atlas_id_app_rotations_with_overlap() -> None:
    app = {
        "object": "atlas_id_app",
        "id": "aia_1",
        "client_secret": "cs_new",
        "overlap_seconds": 3600,
        "previous_secret_expires_at": 1_800_003_600_000,
        "secret_issued_at": 1_800_000_000_000,
        "webhook_previous_secret_expires_at": None,
    }
    secret = respx.post(f"{API_URL}/v1/platform/atlas_id_apps/aia_1/rotate_secret").mock(
        return_value=httpx.Response(200, json=app)
    )
    webhook = respx.post(f"{API_URL}/v1/platform/atlas_id_apps/aia_1/webhook/rotate_secret").mock(
        return_value=httpx.Response(
            200,
            json={
                **app,
                "webhook_secret": "whsec_new",
                "webhook_previous_secret_expires_at": 1_800_000_600_000,
            },
        )
    )
    p = platform().atlas_id_apps
    out = p.rotate_secret("aia_1", {"overlap_seconds": 3600})
    assert body_of(secret) == {"overlap_seconds": 3600}
    assert out["previous_secret_expires_at"] == 1_800_003_600_000
    assert out["secret_issued_at"] == 1_800_000_000_000
    p.rotate_secret("aia_1")
    assert secret.calls.last.request.content == b""

    hook = p.rotate_webhook_secret("aia_1", {"overlap_seconds": 600})
    assert body_of(webhook) == {"overlap_seconds": 600}
    assert hook["webhook_previous_secret_expires_at"] == 1_800_000_600_000


@respx.mock
async def test_async_proxy_secret_and_rotations() -> None:
    post = respx.post(PROXY).mock(
        return_value=httpx.Response(201, json={**PROXY_VIEW, "secret": "aps_1", "rotated": False})
    )
    webhook = respx.post(f"{API_URL}/v1/webhook_endpoints/whep_1/rotate_secret").mock(
        return_value=httpx.Response(200, json={"object": "webhook_secret", "secret": "whsec_new"})
    )
    instance = respx.post(f"{API_URL}/v1/platform/apps/app_1/instances/ins_1/rotate_secret").mock(
        return_value=httpx.Response(200, json={"object": "app_secret", "app_id": "app_1"})
    )
    async with AsyncAtlasClient("sk_test_x", base_url=API_URL) as c:
        created = await c.instance.create_proxy_secret({"overlap_seconds": 0})
        assert created["secret"] == "aps_1"
        await c.webhooks.endpoints.rotate_secret("whep_1", {"overlap_seconds": 60})
    assert body_of(post) == {"overlap_seconds": 0}
    assert body_of(webhook) == {"overlap_seconds": 60}
    async with AsyncAtlasPlatformClient("psk_test_x", base_url=API_URL) as p:
        await p.apps.rotate_instance_secret("app_1", "ins_1", {"overlap_seconds": 7200})
    assert body_of(instance) == {"overlap_seconds": 7200}
