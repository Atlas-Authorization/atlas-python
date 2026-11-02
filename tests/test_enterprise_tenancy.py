"""Request shapes for tenant organizations (external_id / metadata filters, by_domain,
policy, domain verification methods), trusted-JWT connections, setup-link return_url,
chosen webhook secrets, the platform initial-secret reveal, path-mount domains,
referral and cookie-consent fields, and ``previous_issuers`` on the session verifier.
Each row asserts method, path, query and body on both the sync and the async clients.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import httpx
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token

import atlas_backend
from atlas_backend import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasBackend,
    AtlasClient,
    AtlasPlatformClient,
    VerificationError,
)

API_URL = "https://api.example.test"
SECRET = "whsec_" + "A" * 40

Row = tuple[str, str, dict[str, str], Any, Callable[[Any], Any]]

BAPI: list[Row] = [
    (
        "POST",
        "/v1/organizations",
        {},
        {"name": "Acme", "slug": "acme", "external_id": "cus_1", "owner_email": "it@acme.com",
         "role_mappings": {"org:admin": "owner"}, "public_metadata": {"plan": "pro"}},
        lambda c: c.organizations.create(
            {"name": "Acme", "slug": "acme", "external_id": "cus_1", "owner_email": "it@acme.com",
             "role_mappings": {"org:admin": "owner"}, "public_metadata": {"plan": "pro"}}
        ),
    ),
    (
        "GET",
        "/v1/organizations",
        {"external_id": "cus_1", "metadata[plan]": "pro"},
        None,
        lambda c: c.organizations.list(external_id="cus_1", metadata={"plan": "pro"}),
    ),
    (
        "GET",
        "/v1/organizations/by_domain/acme.com",
        {"include_unverified": "true"},
        None,
        lambda c: c.organizations.find_by_domain("acme.com", include_unverified=True),
    ),
    ("GET", "/v1/organizations/by_domain/acme.com", {}, None,
     lambda c: c.organizations.find_by_domain("acme.com")),
    ("GET", "/v1/organizations/org_1/policy", {}, None,
     lambda c: c.organizations.get_policy("org_1")),
    # No method / code: no body, so the DNS check runs as before.
    ("POST", "/v1/organizations/org_1/domains/dom_1/verify", {}, None,
     lambda c: c.organizations.domains.verify("org_1", "dom_1")),
    ("POST", "/v1/organizations/org_1/domains/dom_1/verify", {}, {"method": "email", "code": "123456"},
     lambda c: c.organizations.domains.verify("org_1", "dom_1", method="email", code="123456")),
    ("POST", "/v1/organizations/org_1/domains/dom_1/verification_email", {}, {"address": "admin"},
     lambda c: c.organizations.domains.send_verification_email("org_1", "dom_1", address="admin")),
    ("GET", "/v1/jwt_connections", {}, None, lambda c: c.jwt_connections.list()),
    ("GET", "/v1/jwt_connections/jwc_1", {}, None, lambda c: c.jwt_connections.get("jwc_1")),
    (
        "POST",
        "/v1/jwt_connections",
        {},
        {"jwks_uri": "https://idp.example.com/jwks.json", "issuer": "https://idp.example.com",
         "audience": "atlas"},
        lambda c: c.jwt_connections.create(
            {"jwks_uri": "https://idp.example.com/jwks.json", "issuer": "https://idp.example.com",
             "audience": "atlas"}
        ),
    ),
    ("PATCH", "/v1/jwt_connections/jwc_1", {}, {"status": "active"},
     lambda c: c.jwt_connections.update("jwc_1", {"status": "active"})),
    ("DELETE", "/v1/jwt_connections/jwc_1", {}, None, lambda c: c.jwt_connections.delete("jwc_1")),
    ("GET", "/v1/sso_onboarding_profiles", {"name": "Default"}, None,
     lambda c: c.sso_onboarding.list_profiles(name="Default")),
    ("POST", "/v1/sso_onboarding_profiles/sop_1/tickets", {}, {"return_url": "https://app.example.com/done"},
     lambda c: c.sso_onboarding.create_ticket("sop_1", {"return_url": "https://app.example.com/done"})),
    (
        "POST",
        "/v1/webhook_endpoints",
        {},
        {"url": "https://hooks.example.com/atlas", "active": False, "secret": SECRET},
        lambda c: c.webhooks.endpoints.create(
            {"url": "https://hooks.example.com/atlas", "active": False, "secret": SECRET}
        ),
    ),
    ("POST", "/v1/webhook_endpoints/we_1/rotate_secret", {}, {"secret": SECRET},
     lambda c: c.webhooks.endpoints.rotate_secret("we_1", {"secret": SECRET})),
    (
        "POST",
        "/v1/users",
        {},
        {"email_address": ["a@example.com"], "password_hash": "c2FsdA==$aGFzaA==",
         "password_hash_algorithm": "scrypt", "password_hash_params": {"n": 16384, "r": 8, "p": 1}},
        lambda c: c.users.create(
            {"email_address": ["a@example.com"], "password_hash": "c2FsdA==$aGFzaA==",
             "password_hash_algorithm": "scrypt", "password_hash_params": {"n": 16384, "r": 8, "p": 1}}
        ),
    ),
    (
        "PATCH",
        "/v1/instance/referrals",
        {},
        {"report_linked_atlas_id_signups": True, "partner_portal_url": "https://partners.example.com"},
        lambda c: c.instance.referrals.update(
            {"report_linked_atlas_id_signups": True, "partner_portal_url": "https://partners.example.com"}
        ),
    ),
    ("PUT", "/v1/instance/cookie_consent", {}, {"host_aliases": ["acme-fapi.example.com"]},
     lambda c: c.instance.cookie_consent.set({"host_aliases": ["acme-fapi.example.com"]})),
    (
        "POST",
        "/v1/domains",
        {},
        {"method": "path", "hostname": "app.example.com", "base_path": "/__atlas"},
        lambda c: c.domains.create({"method": "path", "hostname": "app.example.com", "base_path": "/__atlas"}),
    ),
]

PLATFORM: list[Row] = [
    ("POST", "/v1/platform/apps/app_1/initial_secret/reveal", {}, None,
     lambda c: c.apps.reveal_initial_secret("app_1")),
    ("POST", "/v1/platform/apps/app_1/initial_secret/reveal", {"dry_run": "true"}, None,
     lambda c: c.apps.reveal_initial_secret("app_1", dry_run=True)),
]


def _check(route: respx.Route, method: str, path: str, query: dict[str, str], body: Any) -> None:
    req = route.calls.last.request
    assert req.method == method
    assert req.url.path == path
    assert dict(req.url.params) == query
    if body is None:
        assert not req.content
    else:
        assert json.loads(req.content) == body


def _sync(client: Any, row: Row) -> None:
    method, path, query, body, call = row
    with respx.mock(base_url=API_URL) as mock:
        route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
        call(client)
        _check(route, method, path, query, body)


def _async(client: Any, row: Row) -> None:
    method, path, query, body, call = row

    async def run() -> None:
        with respx.mock(base_url=API_URL) as mock:
            route = mock.route().mock(return_value=httpx.Response(200, json={"object": "x"}))
            await call(client)
            _check(route, method, path, query, body)

    asyncio.run(run())


@pytest.mark.parametrize("row", BAPI)
def test_bapi(row: Row) -> None:
    _sync(AtlasClient("sk_test_x", base_url=API_URL), row)
    _async(AsyncAtlasClient("sk_test_x", base_url=API_URL), row)


@pytest.mark.parametrize("row", PLATFORM)
def test_platform(row: Row) -> None:
    _sync(AtlasPlatformClient("psk_test_x", base_url=API_URL), row)
    _async(AsyncAtlasPlatformClient("psk_test_x", base_url=API_URL), row)


def test_new_webhook_event_constants() -> None:
    assert atlas_backend.WEBHOOK_EVENT_SSO_CONNECTION_ACTIVATED == "sso_connection.activated"
    assert (
        atlas_backend.WEBHOOK_EVENT_SSO_ONBOARDING_TICKET_COMPLETED
        == "sso_onboarding_ticket.completed"
    )
    assert atlas_backend.WEBHOOK_EVENT_SCIM_GROUP_MEMBER_REMOVED == "scim_group.member_removed"


OLD_ISSUER = "https://acme-fapi.example.test"


@respx.mock
def test_previous_issuer_accepted_only_when_configured() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    old = mint_token(issuer=OLD_ISSUER)

    with_prev = AtlasBackend(jwks_url=JWKS_URL, issuer=ISSUER, previous_issuers=[OLD_ISSUER])
    assert with_prev.verify(old).raw["iss"] == OLD_ISSUER
    assert with_prev.verify(mint_token()).raw["iss"] == ISSUER
    with pytest.raises(VerificationError):
        with_prev.verify(mint_token(issuer="https://evil.example.com"))

    with pytest.raises(VerificationError):
        AtlasBackend(jwks_url=JWKS_URL, issuer=ISSUER).verify(old)
