"""Django integration for Atlas session verification (optional extra).

Importing this module requires Django (``pip install 'atlas-backend[django]'``);
``import atlas_backend`` on its own never pulls Django in.

Configure three settings (a fourth is optional)::

    ATLAS_JWKS_URL = "https://id.atlasauth.net/.well-known/jwks.json"
    ATLAS_ISSUER = "https://id.atlasauth.net"
    ATLAS_SECRET_KEY = "sk_live_..."          # optional, for API-key verify
    ATLAS_AUTHORIZED_PARTIES = ["https://app.example.com"]  # optional azp allowlist

Then add the middleware and protect views::

    MIDDLEWARE = [..., "atlas_backend.django.AtlasMiddleware"]

    from atlas_backend.django import atlas_login_required

    @atlas_login_required
    def dashboard(request):
        return JsonResponse({"user": request.atlas_user.id})

The middleware ATTACHES ``request.atlas`` (the verified :class:`SessionClaims`,
or ``None``) and ``request.atlas_user`` (an :class:`AtlasUser`, or ``None``); it
never rejects on its own. :func:`atlas_login_required` is the gate that returns
``401``. DRF projects use :class:`AtlasAuthentication` instead.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from .._verify import AtlasBackend, AtlasUser, SessionClaims, VerificationError

__all__ = ["AtlasMiddleware", "atlas_login_required", "get_backend", "AtlasAuthentication"]

_backend: AtlasBackend | None = None


def get_backend() -> AtlasBackend:
    """The process-wide :class:`AtlasBackend`, built from Django settings once.

    Reads ``ATLAS_JWKS_URL``, ``ATLAS_ISSUER`` and (optionally)
    ``ATLAS_AUTHORIZED_PARTIES``. Cached so the JWKS cache is shared across
    requests rather than rebuilt per request.
    """
    global _backend
    if _backend is None:
        jwks_url = getattr(settings, "ATLAS_JWKS_URL", None)
        issuer = getattr(settings, "ATLAS_ISSUER", None)
        if not jwks_url or not issuer:
            raise RuntimeError(
                "atlas_backend.django requires ATLAS_JWKS_URL and ATLAS_ISSUER "
                "in your Django settings."
            )
        _backend = AtlasBackend(
            jwks_url=jwks_url,
            issuer=issuer,
            authorized_parties=getattr(settings, "ATLAS_AUTHORIZED_PARTIES", None),
        )
    return _backend


def _reset_backend() -> None:
    """Drop the cached backend (test hook; settings change between tests)."""
    global _backend
    _backend = None


def _verify_request(request: HttpRequest) -> SessionClaims | None:
    authorization = request.META.get("HTTP_AUTHORIZATION")
    session_cookie = request.COOKIES.get("__session")
    try:
        return get_backend().authenticate(
            authorization=authorization, session_cookie=session_cookie
        )
    except VerificationError:
        return None


class AtlasMiddleware:
    """Attaches ``request.atlas`` and ``request.atlas_user`` on every request.

    Reads the ``Authorization: Bearer <jwt>`` header (preferred) or the
    ``__session`` cookie, verifies it, and sets the verified claims — or
    ``None`` when there is no valid session. It does not short-circuit; use
    :func:`atlas_login_required` (or :class:`AtlasAuthentication` for DRF) to
    require a session.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        claims = _verify_request(request)
        request.atlas = claims
        request.atlas_user = (
            AtlasUser.from_claims(claims) if claims is not None else None
        )
        return self.get_response(request)


def atlas_login_required(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """View decorator that returns ``401`` unless the request has a session.

    Works with or without :class:`AtlasMiddleware`: if ``request.atlas`` is not
    already set (middleware absent), it verifies the request itself.
    """

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        claims = getattr(request, "atlas", None)
        if claims is None:
            claims = _verify_request(request)
            request.atlas = claims
            request.atlas_user = (
                AtlasUser.from_claims(claims) if claims is not None else None
            )
        if claims is None:
            return JsonResponse(
                {"errors": [{"code": "UNAUTHORIZED", "message": "Authentication required."}]},
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def __getattr__(name: str) -> Any:
    # Lazy so `import atlas_backend.django` (middleware/decorator) does not
    # require Django REST Framework to be installed; only touching
    # AtlasAuthentication pulls it in.
    if name == "AtlasAuthentication":
        from .authentication import AtlasAuthentication

        return AtlasAuthentication
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
