"""Django + DRF integration tests.

Spins up Django with ``settings.configure`` (no project, no DB) and drives the
middleware, the ``@atlas_login_required`` decorator, and the DRF
``AtlasAuthentication`` class in-process with a ``RequestFactory``.
"""

from __future__ import annotations

from collections.abc import Iterator

import django
import httpx
import pytest
import respx
from _verify_helpers import ISSUER, JWKS_URL, jwks_document, mint_token
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-only-not-secret",
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=[],
        DATABASES={},
        ATLAS_JWKS_URL=JWKS_URL,
        ATLAS_ISSUER=ISSUER,
        USE_TZ=True,
    )
    django.setup()

from django.http import HttpRequest, JsonResponse  # noqa: E402
from django.test import RequestFactory  # noqa: E402

import atlas_backend.django as atlas_django  # noqa: E402
from atlas_backend.django import AtlasMiddleware, atlas_login_required  # noqa: E402
from atlas_backend.django.authentication import AtlasAuthentication  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_backend() -> Iterator[None]:
    # Rebuild the backend each test so the JWKS is refetched (and respx's
    # assert-all-called is satisfied), independent of test order.
    atlas_django._reset_backend()
    yield
    atlas_django._reset_backend()


def _bearer_request(token: str) -> HttpRequest:
    return RequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")


@respx.mock
def test_middleware_attaches_claims_and_user_on_valid_token() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    captured = {}

    def view(request: HttpRequest) -> JsonResponse:
        captured["atlas"] = request.atlas
        captured["user"] = request.atlas_user
        return JsonResponse({"ok": True})

    AtlasMiddleware(view)(_bearer_request(mint_token()))
    assert captured["atlas"].user_id == "user_test_1"
    assert captured["user"].id == "user_test_1"
    assert captured["user"].is_authenticated


@respx.mock
def test_middleware_sets_none_without_token() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    captured = {}

    def view(request: HttpRequest) -> JsonResponse:
        captured["atlas"] = request.atlas
        captured["user"] = request.atlas_user
        return JsonResponse({"ok": True})

    # No Authorization/cookie: claims is None, but the request still passes.
    AtlasMiddleware(view)(RequestFactory().get("/"))
    assert captured["atlas"] is None
    assert captured["user"] is None


@respx.mock
def test_login_required_allows_valid_and_401s_missing() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))

    @atlas_login_required
    def protected(request: HttpRequest) -> JsonResponse:
        return JsonResponse({"user": request.atlas_user.id})

    ok = protected(_bearer_request(mint_token()))
    assert ok.status_code == 200

    denied = protected(RequestFactory().get("/"))
    assert denied.status_code == 401


@respx.mock
def test_login_required_401s_invalid_token() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))

    @atlas_login_required
    def protected(request: HttpRequest) -> JsonResponse:
        return JsonResponse({"ok": True})

    denied = protected(_bearer_request(mint_token(issuer="https://evil.example.com")))
    assert denied.status_code == 401


@respx.mock
def test_drf_authentication_authenticates_and_rejects() -> None:
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=jwks_document()))
    from rest_framework.exceptions import AuthenticationFailed

    auth = AtlasAuthentication()

    result = auth.authenticate(_bearer_request(mint_token()))
    assert result is not None
    user, claims = result
    assert user.id == "user_test_1"
    assert claims.user_id == "user_test_1"

    # No credentials → declines (returns None) so DRF can try the next scheme.
    assert auth.authenticate(RequestFactory().get("/")) is None

    # Present-but-invalid → AuthenticationFailed (→ 401).
    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_bearer_request(mint_token(expires_in=-3600)))


def test_atlas_authentication_lazy_export_matches() -> None:
    # `from atlas_backend.django import AtlasAuthentication` resolves lazily.
    assert atlas_django.AtlasAuthentication is AtlasAuthentication
