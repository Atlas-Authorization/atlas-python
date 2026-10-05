"""FastAPI integration tests, driven through Starlette's TestClient in-process.

respx mocks the JWKS endpoint (a real outbound httpx call from the verifier);
the TestClient's own calls go to the ASGI app and bypass the mock layer.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from atlas_backend import SessionClaims
from atlas_backend.fastapi import AtlasAuth


def _app() -> FastAPI:
    app = FastAPI()
    atlas = AtlasAuth(jwks_url=JWKS_URL, issuer=ISSUER)

    @app.get("/me")
    def me(session: SessionClaims = Depends(atlas)) -> dict:
        return {"user": session.user_id, "role": session.org_role}

    return app


@respx.mock
def test_valid_token_passes_and_returns_session() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    client = TestClient(_app())

    resp = client.get("/me", headers={"Authorization": f"Bearer {mint_token()}"})
    assert resp.status_code == 200
    assert resp.json() == {"user": "user_test_1", "role": "admin"}


@respx.mock
def test_session_cookie_also_authenticates() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    client = TestClient(_app())
    client.cookies.set("__session", mint_token())

    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["user"] == "user_test_1"


def test_missing_token_is_401() -> None:
    # No token at all never reaches the JWKS fetch, so no respx needed.
    client = TestClient(_app())
    assert client.get("/me").status_code == 401


@respx.mock
def test_invalid_token_is_401() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    client = TestClient(_app())

    resp = client.get(
        "/me", headers={"Authorization": f"Bearer {mint_token(expires_in=-3600)}"}
    )
    assert resp.status_code == 401


@respx.mock
def test_require_auth_env_configured_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("ATLAS_ISSUER", ISSUER)
    import atlas_backend.fastapi as atlas_fastapi

    monkeypatch.setattr(atlas_fastapi, "_default_auth", None)
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))

    app = FastAPI()

    @app.get("/whoami")
    def whoami(session: SessionClaims = Depends(atlas_fastapi.require_auth)) -> dict:
        return {"user": session.user_id}

    client = TestClient(app)
    assert client.get("/whoami", headers={"Authorization": f"Bearer {mint_token()}"}).json() == {
        "user": "user_test_1"
    }
    assert client.get("/whoami").status_code == 401


def test_atlas_auth_requires_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_JWKS_URL", raising=False)
    monkeypatch.delenv("ATLAS_ISSUER", raising=False)
    with pytest.raises(RuntimeError):
        AtlasAuth()
