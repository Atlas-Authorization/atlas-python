"""FastAPI integration for Atlas session verification (optional extra).

Importing this module requires FastAPI/Starlette
(``pip install 'atlas-backend[fastapi]'``); ``import atlas_backend`` on its own
never pulls them in.

Use :class:`AtlasAuth` as a dependency (configured in code), or the
env-configured :func:`require_auth` shortcut::

    from fastapi import Depends, FastAPI
    from atlas_backend import SessionClaims
    from atlas_backend.fastapi import AtlasAuth

    app = FastAPI()
    atlas = AtlasAuth(
        jwks_url="https://id.atlasauth.net/.well-known/jwks.json",
        issuer="https://id.atlasauth.net",
    )

    @app.get("/me")
    def me(session: SessionClaims = Depends(atlas)) -> dict:
        return {"user": session.user_id}

The dependency reads the token via ``HTTPBearer`` (falling back to the
``__session`` cookie) and returns the verified :class:`SessionClaims`, or
raises ``HTTPException(401)``.
"""

import os
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .._verify import AtlasBackend, SessionClaims, VerificationError

__all__ = ["AtlasAuth", "require_auth"]


class AtlasAuth:
    """A FastAPI dependency that verifies an Atlas session.

    Config comes from constructor args, falling back to the ``ATLAS_JWKS_URL``,
    ``ATLAS_ISSUER`` and ``ATLAS_AUTHORIZED_PARTIES`` (comma-separated) env
    vars. Instances are callable, so pass one straight to ``Depends(...)``.

    Args:
        auto_error: When ``True`` (default) a missing/invalid session raises
            ``HTTPException(401)``. When ``False`` the dependency returns
            ``None`` instead, for routes that treat auth as optional.
    """

    def __init__(
        self,
        *,
        jwks_url: Optional[str] = None,
        issuer: Optional[str] = None,
        authorized_parties: Optional[list[str]] = None,
        auto_error: bool = True,
    ) -> None:
        jwks_url = jwks_url or os.environ.get("ATLAS_JWKS_URL")
        issuer = issuer or os.environ.get("ATLAS_ISSUER")
        if authorized_parties is None:
            env_azp = os.environ.get("ATLAS_AUTHORIZED_PARTIES")
            authorized_parties = (
                [p.strip() for p in env_azp.split(",") if p.strip()] if env_azp else None
            )
        if not jwks_url or not issuer:
            raise RuntimeError(
                "AtlasAuth requires jwks_url and issuer (constructor args or the "
                "ATLAS_JWKS_URL / ATLAS_ISSUER env vars)."
            )
        self._backend = AtlasBackend(
            jwks_url=jwks_url, issuer=issuer, authorized_parties=authorized_parties
        )
        self._auto_error = auto_error
        self._bearer = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request) -> Optional[SessionClaims]:
        credentials: Optional[HTTPAuthorizationCredentials] = await self._bearer(request)
        authorization = (
            f"{credentials.scheme} {credentials.credentials}" if credentials else None
        )
        session_cookie = request.cookies.get("__session")
        try:
            return self._backend.authenticate(
                authorization=authorization, session_cookie=session_cookie
            )
        except VerificationError:
            if self._auto_error:
                raise HTTPException(
                    status_code=401, detail="Authentication required."
                ) from None
            return None


_default_auth: Optional[AtlasAuth] = None


async def require_auth(request: Request) -> SessionClaims:
    """An env-configured :class:`AtlasAuth` dependency.

    The convenience form for apps that configure Atlas purely through the
    ``ATLAS_JWKS_URL`` / ``ATLAS_ISSUER`` env vars::

        @app.get("/me")
        def me(session: SessionClaims = Depends(require_auth)): ...
    """
    global _default_auth
    if _default_auth is None:
        _default_auth = AtlasAuth()
    result = await _default_auth(request)
    assert result is not None  # auto_error=True guarantees a non-None result
    return result
