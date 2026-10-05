"""Flask integration tests, driven through Flask's test client in-process."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token
from flask import Flask, g, jsonify

from atlas_backend.flask import Atlas, atlas_required


def _app() -> Flask:
    app = Flask(__name__)
    app.config["ATLAS_JWKS_URL"] = JWKS_URL
    app.config["ATLAS_ISSUER"] = ISSUER
    Atlas(app)

    @app.get("/me")
    @atlas_required
    def me() -> Any:
        return jsonify(
            user=g.atlas_user.id,
            role=g.atlas.org_role,
            authed=g.atlas_user.is_authenticated,
        )

    return app


@respx.mock
def test_valid_token_passes_and_exposes_g() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    client = _app().test_client()

    resp = client.get("/me", headers={"Authorization": f"Bearer {mint_token()}"})
    assert resp.status_code == 200
    assert resp.get_json() == {"user": "user_test_1", "role": "admin", "authed": True}


@respx.mock
def test_session_cookie_authenticates() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    client = _app().test_client()
    client.set_cookie("__session", mint_token())

    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.get_json()["user"] == "user_test_1"


def test_missing_token_is_401() -> None:
    client = _app().test_client()
    resp = client.get("/me")
    assert resp.status_code == 401
    assert resp.get_json()["errors"][0]["code"] == "UNAUTHORIZED"


@respx.mock
def test_invalid_token_is_401() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    client = _app().test_client()

    resp = client.get(
        "/me", headers={"Authorization": f"Bearer {mint_token(issuer='https://evil.example.com')}"}
    )
    assert resp.status_code == 401


def test_init_requires_config() -> None:
    app = Flask(__name__)
    with pytest.raises(RuntimeError):
        Atlas(app)


def test_decorator_without_extension_errors() -> None:
    app = Flask(__name__)  # Atlas() never registered.
    app.testing = True  # propagate the error instead of turning it into a 500.

    @app.get("/x")
    @atlas_required
    def x() -> str:
        return "ok"

    with pytest.raises(RuntimeError):
        app.test_client().get("/x", headers={"Authorization": "Bearer whatever"})
