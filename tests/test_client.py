"""Tests for the Atlas Python backend SDK.

All HTTP is mocked with respx — no network. The suite exercises the request
core (auth header, base URL, method/path, body & query serialization,
Idempotency-Key), the error envelope, cursor pagination, and a handful of
representative namespaces across both the sync and async clients.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from atlas_backend import (
    AsyncAtlasClient,
    AtlasClient,
    AtlasError,
    acollect,
    collect,
    paginate,
)

SECRET = "sk_test_placeholder_not_a_real_key"
API_URL = "https://api.example.test"


def client() -> AtlasClient:
    return AtlasClient(SECRET, base_url=API_URL)


# --------------------------------------------------------------------------- #
# Request core: auth, method, path, serialization                             #
# --------------------------------------------------------------------------- #


@respx.mock
def test_sends_bearer_auth_method_and_path() -> None:
    route = respx.get(f"{API_URL}/v1/users/user_1").mock(
        return_value=httpx.Response(200, json={"object": "user", "id": "user_1"})
    )
    out = client().users.get("user_1")

    assert route.called
    req = route.calls.last.request
    assert req.method == "GET"
    assert str(req.url) == f"{API_URL}/v1/users/user_1"
    assert req.headers["authorization"] == f"Bearer {SECRET}"
    assert req.headers["accept"] == "application/json"
    # The secret must never appear in the URL.
    assert SECRET not in str(req.url)
    assert out["id"] == "user_1"
    assert out["object"] == "user"


@respx.mock
def test_json_encodes_body_and_sets_content_type() -> None:
    route = respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(201, json={"object": "user", "id": "u"})
    )
    client().users.create({"email_address": "a@b.com", "first_name": "A"})

    req = route.calls.last.request
    assert req.method == "POST"
    assert req.headers["content-type"] == "application/json"
    assert json.loads(req.content) == {"email_address": "a@b.com", "first_name": "A"}


@respx.mock
def test_serializes_query_dropping_none() -> None:
    respx.get(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(
            200, json={"data": [], "has_more": False, "next_cursor": None}
        )
    )
    c = client()

    c.users.list(limit=50, starting_after="user_9")
    assert (
        str(respx.calls.last.request.url)
        == f"{API_URL}/v1/users?limit=50&starting_after=user_9"
    )

    c.users.list(limit=10)
    assert str(respx.calls.last.request.url) == f"{API_URL}/v1/users?limit=10"


@respx.mock
def test_forwards_idempotency_key_on_create() -> None:
    route = respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(201, json={"object": "user", "id": "u"})
    )
    client().users.create({"email_address": "a@b.com"}, idempotency_key="idem-123")
    assert route.calls.last.request.headers["idempotency-key"] == "idem-123"


@respx.mock
def test_no_idempotency_header_when_absent() -> None:
    route = respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(201, json={"object": "user", "id": "u"})
    )
    client().users.create({"email_address": "a@b.com"})
    assert "idempotency-key" not in route.calls.last.request.headers


@respx.mock
def test_tolerates_trailing_slash_on_base_url() -> None:
    route = respx.get(f"{API_URL}/v1/users/u").mock(
        return_value=httpx.Response(200, json={"object": "user", "id": "u"})
    )
    AtlasClient(SECRET, base_url=f"{API_URL}/").users.get("u")
    assert route.called


@respx.mock
def test_returns_none_on_204() -> None:
    respx.post(f"{API_URL}/v1/sessions/sess_1/revoke").mock(
        return_value=httpx.Response(204)
    )
    assert client().sessions.revoke("sess_1") is None


def test_requires_secret_key() -> None:
    with pytest.raises(ValueError):
        AtlasClient("")


# --------------------------------------------------------------------------- #
# Error handling — the §9.1 envelope                                          #
# --------------------------------------------------------------------------- #


@respx.mock
def test_raises_atlas_error_with_status_and_code_on_4xx() -> None:
    respx.get(f"{API_URL}/v1/users/nope").mock(
        return_value=httpx.Response(
            404,
            json={"errors": [{"code": "NOT_FOUND", "message": "Unknown user."}]},
        )
    )
    # Mutation-check: if no error is raised, pytest.raises fails the test.
    with pytest.raises(AtlasError) as exc_info:
        client().users.get("nope")

    err = exc_info.value
    assert err.status == 404
    assert err.code == "NOT_FOUND"
    assert err.has_code("NOT_FOUND") is True
    assert str(err) == "Unknown user."


@respx.mock
def test_error_carries_param_from_envelope() -> None:
    respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(
            422,
            json={
                "errors": [
                    {
                        "code": "FORM_PARAM_FORMAT_INVALID",
                        "message": "is invalid",
                        "param": "email_address",
                    }
                ]
            },
        )
    )
    with pytest.raises(AtlasError) as exc_info:
        client().users.create({"email_address": "not-an-email"})

    assert exc_info.value.errors[0].get("param") == "email_address"


@respx.mock
def test_branches_on_conflict_code_like_last_admin() -> None:
    respx.patch(f"{API_URL}/v1/organizations/org_1/memberships/user_1").mock(
        return_value=httpx.Response(
            409,
            json={"errors": [{"code": "LAST_ADMIN", "message": "Cannot demote."}]},
        )
    )
    with pytest.raises(AtlasError) as exc_info:
        client().organizations.memberships.update("org_1", "user_1", role="member")

    assert exc_info.value.status == 409
    assert exc_info.value.has_code("LAST_ADMIN")


@respx.mock
def test_synthetic_error_for_non_json_body() -> None:
    respx.get(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(502, text="Bad Gateway")
    )
    with pytest.raises(AtlasError) as exc_info:
        client().users.list()

    assert exc_info.value.status == 502
    assert "Bad Gateway" in exc_info.value.errors[0]["message"]


# --------------------------------------------------------------------------- #
# Pagination helper                                                           #
# --------------------------------------------------------------------------- #


@respx.mock
def test_collect_walks_every_cursor_page() -> None:
    route = respx.get(f"{API_URL}/v1/users").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [{"id": "a"}, {"id": "b"}],
                    "has_more": True,
                    "next_cursor": "b",
                },
            ),
            httpx.Response(
                200,
                json={"data": [{"id": "c"}], "has_more": False, "next_cursor": None},
            ),
        ]
    )
    all_users = collect(client().users.list)
    assert [u["id"] for u in all_users] == ["a", "b", "c"]
    # The second request must carry the cursor from the first page.
    assert "starting_after=b" in str(route.calls[1].request.url)


@respx.mock
def test_paginate_yields_lazily_over_audit_logs() -> None:
    respx.get(f"{API_URL}/v1/audit_logs").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": [{"id": "1"}], "has_more": True, "next_cursor": "1"},
            ),
            httpx.Response(
                200,
                json={"data": [{"id": "2"}], "has_more": False, "next_cursor": None},
            ),
        ]
    )
    seen = [item["id"] for item in paginate(client().audit_logs.list)]
    assert seen == ["1", "2"]


# --------------------------------------------------------------------------- #
# Namespace routing (method + path + payload)                                 #
# --------------------------------------------------------------------------- #


@respx.mock
def test_users_ban_replace_metadata_and_provider_token() -> None:
    ban = respx.post(f"{API_URL}/v1/users/u1/ban").mock(
        return_value=httpx.Response(200, json={"object": "user", "id": "u1"})
    )
    meta = respx.put(f"{API_URL}/v1/users/u1/metadata").mock(
        return_value=httpx.Response(200, json={"object": "user", "id": "u1"})
    )
    token = respx.get(f"{API_URL}/v1/users/u1/oauth_access_tokens/google").mock(
        return_value=httpx.Response(200, json={"object": "oauth_access_token"})
    )
    c = client()

    c.users.ban("u1")
    assert ban.called

    c.users.replace_metadata("u1", {"public_metadata": {"tier": "gold"}})
    assert json.loads(meta.calls.last.request.content) == {
        "public_metadata": {"tier": "gold"}
    }

    c.users.get_oauth_access_token("u1", "google")
    assert token.called


@respx.mock
def test_organizations_create_and_list() -> None:
    create = respx.post(f"{API_URL}/v1/organizations").mock(
        return_value=httpx.Response(201, json={"object": "organization", "id": "o1"})
    )
    respx.get(f"{API_URL}/v1/organizations").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"object": "organization", "id": "o1"}],
                "has_more": False,
                "next_cursor": None,
            },
        )
    )
    c = client()

    org = c.organizations.create(
        {"name": "Acme", "slug": "acme", "created_by": "user_1"}
    )
    assert org["id"] == "o1"
    assert json.loads(create.calls.last.request.content)["slug"] == "acme"

    page = c.organizations.list(limit=20)
    assert page["data"][0]["id"] == "o1"


@respx.mock
def test_nested_org_namespaces_paths() -> None:
    add = respx.post(f"{API_URL}/v1/organizations/o1/memberships").mock(
        return_value=httpx.Response(200, json={})
    )
    revoke = respx.post(
        f"{API_URL}/v1/organizations/o1/invitations/inv1/revoke"
    ).mock(return_value=httpx.Response(200, json={}))
    verify = respx.post(f"{API_URL}/v1/organizations/o1/domains/d1/verify").mock(
        return_value=httpx.Response(200, json={})
    )
    grant = respx.put(f"{API_URL}/v1/organizations/o1/groups/g1/roles/r1").mock(
        return_value=httpx.Response(200, json={})
    )
    c = client()

    c.organizations.memberships.add("o1", {"user_id": "u1", "role": "admin"})
    c.organizations.invitations.revoke("o1", "inv1")
    c.organizations.domains.verify("o1", "d1")
    c.organizations.group_roles.grant("o1", "g1", "r1")

    assert add.called and revoke.called and verify.called and grant.called


@respx.mock
def test_delete_returns_parsed_ack() -> None:
    route = respx.delete(f"{API_URL}/v1/users/u1").mock(
        return_value=httpx.Response(
            200, json={"object": "user", "id": "u1", "deleted": True}
        )
    )
    out = client().users.delete("u1")
    assert route.calls.last.request.method == "DELETE"
    assert out == {"object": "user", "id": "u1", "deleted": True}


@respx.mock
def test_roles_set_permissions_and_restrictions() -> None:
    perms = respx.put(f"{API_URL}/v1/roles/r1/permissions").mock(
        return_value=httpx.Response(200, json={"object": "role", "id": "r1"})
    )
    allow = respx.post(f"{API_URL}/v1/allowlist_identifiers").mock(
        return_value=httpx.Response(200, json={"object": "allowlist_identifier"})
    )
    block = respx.delete(f"{API_URL}/v1/blocklist_identifiers/b1").mock(
        return_value=httpx.Response(200, json={})
    )
    c = client()

    c.roles.set_permissions("r1", ["org:a:read"])
    assert json.loads(perms.calls.last.request.content) == {
        "permissions": ["org:a:read"]
    }

    c.allowlist.add("a@b.com")
    assert json.loads(allow.calls.last.request.content) == {"identifier": "a@b.com"}

    c.blocklist.remove("b1")
    assert block.calls.last.request.method == "DELETE"


@respx.mock
def test_context_manager_closes() -> None:
    respx.get(f"{API_URL}/v1/roles").mock(
        return_value=httpx.Response(200, json={"object": "list", "data": []})
    )
    with AtlasClient(SECRET, base_url=API_URL) as c:
        c.roles.list()


# --------------------------------------------------------------------------- #
# Async client (bonus)                                                        #
# --------------------------------------------------------------------------- #


@respx.mock
async def test_async_create_and_error_and_pagination() -> None:
    respx.post(f"{API_URL}/v1/users").mock(
        return_value=httpx.Response(201, json={"object": "user", "id": "u"})
    )
    respx.get(f"{API_URL}/v1/users/nope").mock(
        return_value=httpx.Response(
            404, json={"errors": [{"code": "NOT_FOUND", "message": "nope"}]}
        )
    )
    respx.get(f"{API_URL}/v1/organizations").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"data": [{"id": "o1"}], "has_more": True, "next_cursor": "o1"},
            ),
            httpx.Response(
                200,
                json={"data": [{"id": "o2"}], "has_more": False, "next_cursor": None},
            ),
        ]
    )

    async with AsyncAtlasClient(SECRET, base_url=API_URL) as c:
        user = await c.users.create({"email_address": "a@b.com"})
        assert user["id"] == "u"

        with pytest.raises(AtlasError) as exc_info:
            await c.users.get("nope")
        assert exc_info.value.code == "NOT_FOUND"

        orgs = await acollect(c.organizations.list)
        assert [o["id"] for o in orgs] == ["o1", "o2"]
