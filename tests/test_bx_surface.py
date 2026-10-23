"""App roles, org teams/roles, user search + timed bans, API key controls, billing
providers and subscription management, OAuth server administration, ES256 session
verification, app-claim helpers and the access-token verifier.

HTTP is mocked with respx; tokens are genuine RS256 / ES256 JWTs.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import parse_qs

import httpx
import jwt
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.algorithms import ECAlgorithm

from atlas_backend import (
    SIGNING_ALGS,
    AccessTokenVerifier,
    AsyncAtlasClient,
    AtlasBackend,
    AtlasClient,
    VerificationError,
    build_www_authenticate,
    protected_resource_metadata,
    protected_resource_metadata_path,
)

SECRET = "sk_test_placeholder"
API_URL = "https://api.example.test"
OK: dict[str, Any] = {"object": "x", "id": "x_1", "data": [], "has_more": False}


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


def body_of(route: respx.Route) -> Any:
    content = route.calls.last.request.content
    return json.loads(content) if content else None


def query_of(route: respx.Route) -> dict[str, list[str]]:
    return parse_qs(route.calls.last.request.url.query.decode())


@respx.mock
def test_app_roles_surface() -> None:
    c = client()
    calls = [
        ("GET", "/v1/app_roles", lambda: c.app_roles.list()),
        (
            "POST",
            "/v1/app_roles",
            lambda: c.app_roles.create({"key": "support", "name": "Support"}),
        ),
        ("GET", "/v1/app_roles/support", lambda: c.app_roles.get("support")),
        (
            "PATCH",
            "/v1/app_roles/support",
            lambda: c.app_roles.update("support", {"permissions": ["a:b"]}),
        ),
        ("DELETE", "/v1/app_roles/ar_1", lambda: c.app_roles.delete("ar_1")),
        (
            "GET",
            "/v1/app_roles/ar_1/users",
            lambda: c.app_roles.list_users("ar_1", limit=5, offset=10),
        ),
        ("GET", "/v1/users/u_1/app_roles", lambda: c.app_roles.get_for_user("u_1")),
        (
            "POST",
            "/v1/users/u_1/app_roles",
            lambda: c.app_roles.set_for_user("u_1", {"add": ["support"]}),
        ),
        (
            "DELETE",
            "/v1/users/u_1/app_roles/support",
            lambda: c.app_roles.remove_from_user("u_1", "support"),
        ),
    ]
    for method, path, fn in calls:
        route = respx.route(method=method, url=f"{API_URL}{path}").mock(
            return_value=httpx.Response(200, json=OK)
        )
        fn()
        assert route.called, (method, path)
        if path.endswith("/users") and method == "GET":
            assert query_of(route) == {"limit": ["5"], "offset": ["10"]}
        if method == "POST" and path.endswith("/app_roles") and "users" in path:
            assert body_of(route) == {"add": ["support"]}


@respx.mock
def test_org_teams_roles_slugs_and_resend() -> None:
    c = client()
    org = f"{API_URL}/v1/organizations/org_1"
    teams = respx.get(f"{org}/teams").mock(return_value=httpx.Response(200, json=OK))
    c.organizations.teams.list("org_1", user_id="u_1")
    assert query_of(teams) == {"user_id": ["u_1"]}
    create = respx.post(f"{org}/teams").mock(return_value=httpx.Response(200, json=OK))
    c.organizations.teams.create("org_1", {"name": "Core", "description": None})
    assert body_of(create) == {"name": "Core", "description": None}
    for method, path, fn in [
        ("GET", "/teams/tm_1", lambda: c.organizations.teams.get("org_1", "tm_1")),
        (
            "PATCH",
            "/teams/tm_1",
            lambda: c.organizations.teams.update("org_1", "tm_1", {"name": "P"}),
        ),
        ("DELETE", "/teams/tm_1", lambda: c.organizations.teams.delete("org_1", "tm_1")),
        ("GET", "/teams/tm_1/members", lambda: c.organizations.teams.list_members("org_1", "tm_1")),
        (
            "DELETE",
            "/teams/tm_1/members/u_2",
            lambda: c.organizations.teams.remove_member("org_1", "tm_1", "u_2"),
        ),
        (
            "POST",
            "/roles",
            lambda: c.organizations.roles.create("org_1", {"key": "editor", "name": "Editor"}),
        ),
        (
            "PATCH",
            "/roles/r_1",
            lambda: c.organizations.roles.update("org_1", "r_1", {"name": "Writer"}),
        ),
        (
            "POST",
            "/invitations/inv_1/resend",
            lambda: c.organizations.invitations.resend("org_1", "inv_1"),
        ),
    ]:
        route = respx.route(method=method, url=f"{org}{path}").mock(
            return_value=httpx.Response(200, json=OK)
        )
        fn()
        assert route.called, (method, path)
    add = respx.post(f"{org}/teams/tm_1/members").mock(return_value=httpx.Response(201, json=OK))
    c.organizations.teams.add_member("org_1", "tm_1", "u_2")
    assert body_of(add) == {"user_id": "u_2"}
    roles = respx.get(f"{org}/roles").mock(return_value=httpx.Response(200, json=OK))
    c.organizations.roles.list("org_1", own=True)
    assert query_of(roles) == {"own": ["true"]}
    delete = respx.delete(f"{org}/roles/r_1").mock(
        return_value=httpx.Response(
            200, json={"object": "role", "id": "r_1", "deleted": True, "members_reassigned": 2}
        )
    )
    out = c.organizations.roles.delete("org_1", "r_1", reassign_to="member")
    assert query_of(delete) == {"reassign_to": ["member"]} and out["members_reassigned"] == 2
    respx.get(f"{API_URL}/v1/organizations/by_slug/acme").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.organizations.get_by_slug("acme")
    slug = respx.get(f"{API_URL}/v1/organizations/check_slug").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "organization_slug_check",
                "slug": "acme",
                "valid": True,
                "available": False,
            },
        )
    )
    assert c.organizations.check_slug("acme")["available"] is False
    assert query_of(slug) == {"slug": ["acme"]}


@respx.mock
def test_user_search_filters_and_timed_ban() -> None:
    c = client()
    route = respx.get(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": "u_1", "ban_expires_at": 1}],
                "has_more": False,
                "total_count": 1,
            },
        )
    )
    page = c.users.list(
        limit=5,
        offset=10,
        query="ada",
        email_address="a@x.io",
        username="ada",
        phone_number="+15550001",
        external_id="ext_1",
        banned=True,
        email_verified=False,
        organization_id="org_1",
        created_after=1000,
        created_before=2000,
        order_by="-created_at",
        include_total_count=True,
    )
    assert page["total_count"] == 1
    assert query_of(route) == {
        "limit": ["5"],
        "offset": ["10"],
        "query": ["ada"],
        "email_address": ["a@x.io"],
        "username": ["ada"],
        "phone_number": ["+15550001"],
        "external_id": ["ext_1"],
        "banned": ["true"],
        "email_verified": ["false"],
        "organization_id": ["org_1"],
        "created_after": ["1000"],
        "created_before": ["2000"],
        "order_by": ["-created_at"],
        "include_total_count": ["true"],
    }
    ban = respx.post(f"{API_URL}/v1/users/u_1/ban").mock(
        return_value=httpx.Response(200, json={"id": "u_1"})
    )
    c.users.ban("u_1", reason="spam", expires_in_seconds=3600)
    assert body_of(ban) == {"reason": "spam", "expires_in_seconds": 3600}
    c.users.ban("u_1")
    assert body_of(ban) is None


@respx.mock
def test_api_key_controls_and_coded_refusals() -> None:
    c = client()
    verify = respx.post(f"{API_URL}/v1/api_keys/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "api_key_verification",
                "valid": False,
                "code": "rate_limited",
                "id": "ak_1",
                "retry_after_ms": 900,
            },
        )
    )
    v = c.api_keys.verify({"secret": "ak_x", "required_scopes": ["read"]})
    assert body_of(verify) == {"secret": "ak_x", "required_scopes": ["read"]}
    assert v["valid"] is False and v["code"] == "rate_limited" and v["retry_after_ms"] == 900
    create = respx.post(f"{API_URL}/v1/api_keys").mock(return_value=httpx.Response(201, json=OK))
    c.api_keys.create(
        {
            "subject_type": "user",
            "subject_id": "u_1",
            "prefix": "acme",
            "expires_in_seconds": 60,
            "enabled": False,
            "rate_limit": {"max": 10, "window_seconds": 60},
            "remaining": 5,
        }
    )
    assert body_of(create)["rate_limit"] == {"max": 10, "window_seconds": 60}
    upd = respx.patch(f"{API_URL}/v1/api_keys/ak_1").mock(return_value=httpx.Response(200, json=OK))
    c.api_keys.update("ak_1", {"enabled": True, "rate_limit": None, "remaining": None})
    assert body_of(upd) == {"enabled": True, "rate_limit": None, "remaining": None}


@respx.mock
def test_billing_providers_and_subscription_management() -> None:
    c = client()
    base = f"{API_URL}/v1/billing"
    respx.get(f"{base}/providers").mock(return_value=httpx.Response(200, json=OK))
    c.billing.providers.list()
    got = respx.get(f"{base}/providers/polar").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "billing_provider",
                "provider": "polar",
                "secrets_set": {"access_token": True},
            },
        )
    )
    assert c.billing.providers.get("polar")["secrets_set"]["access_token"] is True and got.called
    put = respx.put(f"{base}/providers/polar").mock(return_value=httpx.Response(201, json=OK))
    c.billing.providers.set("polar", {"environment": "test", "config": {"access_token": "polar_x"}})
    assert body_of(put) == {"environment": "test", "config": {"access_token": "polar_x"}}
    respx.post(f"{base}/providers/polar/test").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    assert c.billing.providers.test("polar")["ok"] is True
    delete = respx.delete(f"{base}/providers/polar").mock(return_value=httpx.Response(200, json=OK))
    c.billing.providers.delete("polar", force=True)
    assert query_of(delete) == {"force": ["true"]}

    change = respx.post(f"{base}/subscriptions/sub_1/change").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "scheduled": True})
    )
    out = c.billing.subscriptions.change(
        "sub_1", {"plan_id": "p_2", "interval": "year", "schedule_at_period_end": True}
    )
    assert out["scheduled"] is True
    assert body_of(change) == {"plan_id": "p_2", "interval": "year", "schedule_at_period_end": True}
    cancel = respx.post(f"{base}/subscriptions/sub_1/cancel").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.billing.subscriptions.cancel("sub_1", immediately=True)
    assert body_of(cancel) == {"immediately": True}
    restore = respx.post(f"{base}/subscriptions/sub_1/restore").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.billing.subscriptions.restore("sub_1")
    assert restore.called


@respx.mock
def test_oauth_server_admin_and_logs() -> None:
    c = client()
    respx.get(f"{API_URL}/v1/instance/signing_keys").mock(
        return_value=httpx.Response(
            200,
            json={"object": "list", "data": [{"kid": "k1", "alg": "ES256", "status": "current"}]},
        )
    )
    assert c.instance.security.list_signing_keys()["data"][0]["alg"] == "ES256"
    rot = respx.post(f"{API_URL}/v1/instance/signing_keys/rotate").mock(
        return_value=httpx.Response(201, json=OK)
    )
    c.instance.security.rotate_signing_key({"alg": "ES256", "grace_period_seconds": 60})
    assert body_of(rot) == {"alg": "ES256", "grace_period_seconds": 60}
    iat = respx.post(f"{API_URL}/v1/oauth_initial_access_tokens").mock(
        return_value=httpx.Response(201, json={"id": "iat_1", "token": "secret"})
    )
    assert c.oauth_initial_access_tokens.create({"max_uses": 3})["token"] == "secret"
    assert body_of(iat) == {"max_uses": 3}
    respx.get(f"{API_URL}/v1/oauth_initial_access_tokens").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.oauth_initial_access_tokens.list()
    rev = respx.delete(f"{API_URL}/v1/oauth_initial_access_tokens/iat_1").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.oauth_initial_access_tokens.revoke("iat_1")
    assert rev.called
    scim = respx.patch(f"{API_URL}/v1/scim_tokens/st_1").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.scim_tokens.update(
        "st_1", {"scopes": ["read"], "role_mappings": [{"value": "Admins", "role": "admin"}]}
    )
    assert body_of(scim)["scopes"] == ["read"]
    calls = respx.get(f"{API_URL}/v1/instance/hooks/before_user_create/calls").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.instance.hooks.list_before_user_create_calls(status="failed", test=False)
    assert query_of(calls) == {"status": ["failed"], "test": ["false"]}
    respx.get(f"{API_URL}/v1/instance/referrals/calls/rc_1").mock(
        return_value=httpx.Response(200, json=OK)
    )
    c.instance.referrals.get_call("rc_1")


@respx.mock
async def test_async_client_mirrors_new_surface() -> None:
    c = AsyncAtlasClient(SECRET, base_url=API_URL)
    route = respx.post(f"{API_URL}/v1/billing/subscriptions/sub_1/restore").mock(
        return_value=httpx.Response(200, json=OK)
    )
    await c.billing.subscriptions.restore("sub_1")
    teams = respx.get(f"{API_URL}/v1/organizations/org_1/teams").mock(
        return_value=httpx.Response(200, json=OK)
    )
    await c.organizations.teams.list("org_1")
    roles = respx.get(f"{API_URL}/v1/app_roles").mock(return_value=httpx.Response(200, json=OK))
    await c.app_roles.list()
    assert route.called and teams.called and roles.called


# ── Verification: ES256, pinning, app claims, access tokens ─────────────────

_EC = ec.generate_private_key(ec.SECP256R1())


def _ec_jwk(kid: str = "ec-1") -> dict[str, Any]:
    jwk = json.loads(ECAlgorithm.to_jwk(_EC.public_key()))
    jwk.update({"kid": kid, "alg": "ES256", "use": "sig"})
    return jwk


def _mixed_jwks() -> dict[str, Any]:
    return {"keys": [_ec_jwk(), *jwks_document()["keys"]]}


def _es256(claims: dict[str, Any], kid: str = "ec-1") -> str:
    return jwt.encode(claims, _EC, algorithm="ES256", headers={"kid": kid})


def _session_claims(**extra: Any) -> dict[str, Any]:
    now = int(time.time())
    return {"iss": ISSUER, "sub": "u_1", "sid": "s_1", "exp": now + 300, "iat": now, **extra}


@respx.mock
def test_session_verifier_accepts_es256_and_pins_algorithms() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_mixed_jwks()))
    backend = AtlasBackend(jwks_url=JWKS_URL, issuer=ISSUER)
    claims = backend.verify(
        _es256(_session_claims(app_roles=["support"], app_permissions=["tickets:read"]))
    )
    assert claims.sub == "u_1"
    assert claims.has_app_role("support") and not claims.has_app_role("admin")
    assert claims.has_app_permission("tickets:read") and not claims.has_app_permission(
        "tickets:write"
    )
    assert backend.verify(mint_token()).sub == "user_test_1"  # RS256 still verifies
    assert SIGNING_ALGS == ("RS256", "ES256")
    # An ES256 signature presented under the RSA key's kid fails.
    with pytest.raises(VerificationError):
        backend.verify(_es256(_session_claims(), kid="kid-test-1"))
    # HS256 over the same claims never verifies.
    with pytest.raises(VerificationError):
        backend.verify(
            jwt.encode(_session_claims(), "secret", algorithm="HS256", headers={"kid": "ec-1"})
        )


AUD = "https://api.example.test"


def _access(**extra: Any) -> dict[str, Any]:
    now = int(time.time())
    return {
        "iss": ISSUER,
        "sub": "u_1",
        "aud": AUD,
        "exp": now + 300,
        "token_use": "access_token",
        "scope": "read write",
        "client_id": "oc_1",
        **extra,
    }


@respx.mock
def test_access_token_verifier() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_mixed_jwks()))
    v = AccessTokenVerifier(
        issuer=ISSUER,
        audience=AUD,
        required_scopes=["read"],
        jwks_url=JWKS_URL,
        resource_metadata_url=f"{AUD}/.well-known/oauth-protected-resource",
    )
    ok = v.verify(f"Bearer {_es256(_access())}")
    assert (
        ok.ok and ok.subject == "u_1" and ok.client_id == "oc_1" and ok.scopes == ["read", "write"]
    )

    none = v.verify(None)
    assert none.status == 401 and none.error is None
    assert (
        none.www_authenticate
        == f'Bearer scope="read", resource_metadata="{AUD}/.well-known/oauth-protected-resource"'
    )
    assert v.verify("Basic abc").status == 400
    wrong = v.verify(f"Bearer {_es256(_access(aud='https://other.test'))}")
    assert wrong.status == 401 and 'error="invalid_token"' in wrong.www_authenticate
    assert not v.verify(f"Bearer {_es256(_access(token_use='session'))}").ok
    assert not v.verify(f"Bearer {_es256(_access(cnf={'jkt': 'x'}))}").ok
    assert not v.verify(f"Bearer {_es256(_access(exp=int(time.time()) - 600))}").ok
    short = v.verify(f"Bearer {_es256(_access(scope='write'))}", required_scopes=["admin"])
    assert short.status == 403 and short.error == "insufficient_scope"
    assert 'scope="read admin"' in short.www_authenticate
    with pytest.raises(ValueError):
        AccessTokenVerifier(issuer=ISSUER, audience=[])


def test_challenge_and_metadata_helpers() -> None:
    assert build_www_authenticate() == "Bearer"
    assert build_www_authenticate(realm='a"b', error="invalid_token", description="no") == (
        'Bearer realm="a\\"b", error="invalid_token", error_description="no"'
    )
    assert (
        protected_resource_metadata_path("https://api.test/v1/")
        == "/.well-known/oauth-protected-resource/v1"
    )
    doc = protected_resource_metadata(resource=AUD, issuer=f"{ISSUER}/", scopes_supported=["read"])
    assert doc["authorization_servers"] == [ISSUER] and doc["scopes_supported"] == ["read"]


def test_fastapi_and_flask_access_token_guards() -> None:
    fastapi = pytest.importorskip("fastapi")
    flask = pytest.importorskip("flask")
    from fastapi.testclient import TestClient

    from atlas_backend.fastapi import AtlasAccessToken
    from atlas_backend.flask import access_token_required

    with respx.mock(assert_all_called=False) as mock:
        mock.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_mixed_jwks()))
        mock.route(host="testserver").pass_through()
        mock.route(host="localhost").pass_through()
        v = AccessTokenVerifier(issuer=ISSUER, audience=AUD, jwks_url=JWKS_URL)

        app = fastapi.FastAPI()

        @app.get("/items")
        def docs(token=fastapi.Depends(AtlasAccessToken(v, "read"))):  # noqa: B008
            return {"sub": token.subject}

        tc = TestClient(app)
        good = tc.get("/items", headers={"Authorization": f"Bearer {_es256(_access())}"})
        assert good.status_code == 200, (good.status_code, good.text)
        assert good.json() == {"sub": "u_1"}
        denied = tc.get("/items", headers={"Authorization": f"Bearer {_es256(_access(scope='x'))}"})
        assert (
            denied.status_code == 403 and "insufficient_scope" in denied.headers["www-authenticate"]
        )

        fapp = flask.Flask(__name__)

        @fapp.get("/items")
        @access_token_required(v, "read")
        def fdocs():
            return {"sub": flask.g.atlas_access_token.subject}

        fc = fapp.test_client()
        assert fc.get("/items", headers={"Authorization": f"Bearer {_es256(_access())}"}).json == {
            "sub": "u_1"
        }
        missing = fc.get("/items")
        assert missing.status_code == 401 and missing.headers["WWW-Authenticate"].startswith(
            "Bearer"
        )
