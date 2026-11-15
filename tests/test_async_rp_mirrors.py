"""The async relying party, mirrors, revocation, webhook dedupe and the SQL sid store."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import importlib.util
import ast
import json
import sqlite3
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
import respx
from cryptography.hazmat.primitives.asymmetric import rsa

from atlas_backend import (
    AsyncKeyMirror,
    AsyncMemorySidStore,
    AsyncMemoryWebhookStore,
    AsyncRelyingParty,
    AsyncResourceRoleMirror,
    AsyncSidRevocationList,
    AsyncSqlSidStore,
    OidcError,
    RpRequest,
    SqlSidStore,
    WebhookVerificationError,
    dbapi_executor,
    verify_and_dedupe_async,
)

ROOT = Path(__file__).resolve().parent.parent
ISSUER = "https://id.example.test"
REDIRECT = "https://app.example.test/auth/callback"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
JWK = {**json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key())), "kid": "k1", "alg": "RS256"}


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _issuer_mock(mock: respx.MockRouter, state: dict) -> None:
    mock.get(f"{ISSUER}/.well-known/openid-configuration").mock(return_value=httpx.Response(200, json={
        "issuer": ISSUER, "authorization_endpoint": f"{ISSUER}/oauth2/authorize",
        "token_endpoint": f"{ISSUER}/oauth2/token", "jwks_uri": f"{ISSUER}/jwks"}))
    mock.get(f"{ISSUER}/jwks").mock(return_value=httpx.Response(200, json={"keys": [JWK]}))

    def token(request: httpx.Request) -> httpx.Response:
        now = int(time.time())
        claims = {"iss": ISSUER, "aud": "client_1", "sub": "user_1", "sid": "sid_1", "iat": now, "exp": now + 300,
                  "nonce": state["nonce"], "email_verified": True}
        return httpx.Response(200, json={"id_token": jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "k1"}),
                                         "access_token": "at", "expires_in": 300})

    mock.post(f"{ISSUER}/oauth2/token").mock(side_effect=token)


def test_async_relying_party_round_trip_and_handle() -> None:
    async def run() -> None:
        state: dict = {}
        signed: list[str] = []

        async def on_signed_in(user: Any, tokens: Any, request: Any, result: Any) -> None:  # async callbacks work
            signed.append(user.sub)

        with respx.mock() as mock:
            _issuer_mock(mock, state)
            rp = AsyncRelyingParty(issuer=ISSUER, client_id="client_1", client_secret="s", redirect_uri=REDIRECT,
                                   secret="x" * 40, on_signed_in=on_signed_in, http_client=httpx.AsyncClient())
            started = await rp.handle(RpRequest("GET", "https://app.example.test/auth/sign-in"))
            assert started is not None and started.status == 302
            q = {k: v[0] for k, v in parse_qs(urlsplit(started.location or "").query).items()}
            state["nonce"] = q["nonce"]
            cookie = (started.header("set-cookie") or "").split(";")[0]
            done = await rp.handle(RpRequest("GET", f"{REDIRECT}?code=c&state={q['state']}", {"cookie": cookie}))
            assert done is not None and done.status == 302 and signed == ["user_1"]
            with pytest.raises(OidcError):
                await rp.callback(RpRequest("GET", f"{REDIRECT}?code=c&state=bad", {"cookie": cookie}))
            assert await rp.handle(RpRequest("GET", "https://app.example.test/other")) is None
            await rp.close()

    asyncio.run(run())


def test_async_sid_stores_and_bind() -> None:
    async def run() -> None:
        for store in (AsyncMemorySidStore(), AsyncSqlSidStore(_sqlite_exec(), "sqlite")):
            await store.bind("s", "a1", int(time.time() * 1000) + 60_000)
            await store.bind("s", "a2", int(time.time() * 1000) + 60_000)
            assert sorted(await store.take("s")) == ["a1", "a2"] and await store.take("s") == []

    asyncio.run(run())


def _sqlite_exec() -> Any:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("create table atlas_rp_sessions (sid text not null, app_session_id text not null, expires_at bigint not null, primary key (sid, app_session_id))")
    return dbapi_executor(conn)


def test_sql_sid_store_takes_once_and_drops_expired() -> None:
    clock = [1000]
    store = SqlSidStore(_sqlite_exec(), "sqlite", now=lambda: clock[0])
    store.bind("a", "x", 5000)
    store.bind("a", "x", 6000)  # re-binding replaces
    store.bind("a", "old", 1500)
    clock[0] = 2000
    assert store.take("a") == ["x"] and store.take("a") == []


class _AKeys:
    def __init__(self) -> None:
        self.revoked: list[str] = []

    async def create(self, body: dict, idempotency_key: str | None = None) -> dict:
        return {"id": "eak_1", "prefix": "ak_", "subject_type": "user", "subject_id": "u", "scopes": ["r:read"], "secret": "ak_secret"}

    async def revoke(self, key_id: str) -> None:
        self.revoked.append(key_id)

    async def list_revoked(self, **_: Any) -> dict:
        return {"data": [], "has_more": False, "next_cursor": None}


def test_async_key_mirror() -> None:
    async def run() -> None:
        keys = _AKeys()
        mirror = AsyncKeyMirror(api_keys=keys)
        await mirror.mint({})
        assert (await mirror.verify("ak_secret", required_scopes=["r:read"])).valid
        assert (await mirror.verify("ak_secret", required_scopes=["x"])).code == "insufficient_scope"
        await mirror.revoke("eak_1")
        assert keys.revoked == ["eak_1"] and not (await mirror.verify("ak_secret")).valid
        assert await mirror.sync() == 0

    asyncio.run(run())


class _AClient:
    class resources:  # noqa: N801
        class types:  # noqa: N801
            @staticmethod
            async def list() -> dict:
                return {"data": [{"key": "doc", "inherit": True, "roles": [{"key": "owner", "permissions": ["*"]}]}]}

        @staticmethod
        async def list(**_: Any) -> dict:
            return {"data": [{"id": "r1", "type": "doc", "external_id": "d", "parent_id": None}], "has_more": False}

    class resource_role_assignments:  # noqa: N801
        @staticmethod
        async def list_changes(**_: Any) -> dict:
            return {"data": [{"change": "created", "assignment_id": "a", "resource_id": "r1",
                              "subject": {"type": "user", "id": "u"}, "role": "owner", "inherit": True}],
                    "has_more": False, "next_cursor": "n"}


def test_async_resource_role_mirror() -> None:
    async def run() -> None:
        mirror = AsyncResourceRoleMirror(client=_AClient())
        assert await mirror.sync() == 1
        assert await mirror.can({"type": "user", "id": "u"}, "anything", {"type": "doc", "external_id": "d"})
        assert not await mirror.can({"type": "user", "id": "v"}, "anything", {"id": "r1"})

    asyncio.run(run())


def test_async_sid_revocation_list_and_webhook_dedupe() -> None:
    async def run() -> None:
        now = 10_000_000
        with respx.mock(base_url="https://api.example.test") as mock:
            mock.get("/v1/sessions/revoked").mock(return_value=httpx.Response(200, json={
                "data": [{"sid": "bad", "revoked_at": now}], "has_more": False, "next_cursor": None, "server_time": now}))
            lst = AsyncSidRevocationList(secret_key="sk", base_url="https://api.example.test", now=lambda: now, http_client=httpx.AsyncClient())
            assert await lst.is_revoked("bad") and not await lst.is_revoked("good")
        body = json.dumps({"id": "e", "type": "x", "data": {}}).encode()
        ts = int(time.time() * 1000)
        sig = base64.b64encode(hmac.new(b"sec", f"d1.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
        headers = {"atlas-id": "d1", "atlas-timestamp": str(ts), "atlas-signature": f"v1,{sig}"}
        store = AsyncMemoryWebhookStore()
        first = await verify_and_dedupe_async(body, headers, "sec", store)
        assert not first.duplicate and (await verify_and_dedupe_async(body, headers, "sec", store)).duplicate
        await first.release()
        assert not (await verify_and_dedupe_async(body, headers, "sec", store)).duplicate
        with pytest.raises(WebhookVerificationError):
            await verify_and_dedupe_async(body, headers, "other", store)

    asyncio.run(run())


def test_generated_async_modules_are_current() -> None:
    spec = importlib.util.spec_from_file_location("gen_async", ROOT / "scripts" / "gen_async.py")
    assert spec and spec.loader
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    for src, dst, fn in (("_rp.py", "_arp.py", gen.convert_rp), ("_mirrors.py", "_amirrors.py", gen.convert_mirrors)):
        expected = fn((ROOT / "atlas_backend" / src).read_text(encoding="utf-8"))
        actual = (ROOT / "atlas_backend" / dst).read_text(encoding="utf-8")
        assert ast.dump(ast.parse(expected)) == ast.dump(ast.parse(actual)), f"{dst} is stale: run python scripts/gen_async.py"
