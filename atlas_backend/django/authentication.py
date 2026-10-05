"""Django REST Framework authentication backed by Atlas session verification.

Requires ``djangorestframework`` in addition to Django. Wire it per-view or
globally::

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "atlas_backend.django.authentication.AtlasAuthentication",
        ],
    }

On success ``request.user`` becomes the :class:`AtlasUser` and
``request.auth`` the verified :class:`SessionClaims`.
"""

from __future__ import annotations

from rest_framework import authentication, exceptions

from .._verify import AtlasUser, SessionClaims, VerificationError
from . import get_backend


class AtlasAuthentication(authentication.BaseAuthentication):
    """A DRF ``BaseAuthentication`` that verifies an Atlas session.

    Returns ``None`` (declining, so DRF tries the next authenticator) when the
    request carries no Atlas credentials, and raises
    :class:`~rest_framework.exceptions.AuthenticationFailed` (→ ``401``) when a
    token is present but invalid.
    """

    def authenticate(
        self, request: object
    ) -> tuple[AtlasUser, SessionClaims] | None:
        authorization = request.META.get("HTTP_AUTHORIZATION")  # type: ignore[attr-defined]
        session_cookie = request.COOKIES.get("__session")  # type: ignore[attr-defined]
        if not authorization and not session_cookie:
            return None  # No Atlas credentials — let another authenticator try.
        try:
            claims = get_backend().authenticate(
                authorization=authorization, session_cookie=session_cookie
            )
        except VerificationError:
            raise exceptions.AuthenticationFailed(
                "Invalid Atlas session token."
            ) from None
        return AtlasUser.from_claims(claims), claims

    def authenticate_header(self, request: object) -> str:
        # Makes DRF answer with 401 (not 403) when authentication is required.
        return "Bearer"
