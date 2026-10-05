"""Flask integration for Atlas session verification (optional extra).

Importing this module requires Flask (``pip install 'atlas-backend[flask]'``);
``import atlas_backend`` on its own never pulls Flask in.

Register the extension and protect routes::

    from flask import Flask, g, jsonify
    from atlas_backend.flask import Atlas, atlas_required

    app = Flask(__name__)
    app.config["ATLAS_JWKS_URL"] = "https://id.atlasauth.net/.well-known/jwks.json"
    app.config["ATLAS_ISSUER"] = "https://id.atlasauth.net"
    Atlas(app)

    @app.get("/me")
    @atlas_required
    def me():
        return jsonify(user=g.atlas_user.id)

:func:`atlas_required` verifies the ``Authorization: Bearer <jwt>`` header
(preferred) or the ``__session`` cookie, exposes the verified claims on
``g.atlas`` and the principal on ``g.atlas_user``, and returns ``401`` when
there is no valid session.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Flask, current_app, g, jsonify, request
from flask.wrappers import Response

from .._verify import AtlasBackend, AtlasUser, SessionClaims, VerificationError

__all__ = ["Atlas", "atlas_required"]

_EXTENSION_KEY = "atlas_backend"


class Atlas:
    """Flask extension holding the shared :class:`AtlasBackend`.

    Config is read from ``app.config``: ``ATLAS_JWKS_URL`` and ``ATLAS_ISSUER``
    (required), plus the optional ``ATLAS_AUTHORIZED_PARTIES`` (a list) and
    ``ATLAS_SECRET_KEY``. Supports the app-factory pattern via
    :meth:`init_app`.
    """

    def __init__(self, app: Flask | None = None) -> None:
        self.backend: AtlasBackend | None = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        jwks_url = app.config.get("ATLAS_JWKS_URL")
        issuer = app.config.get("ATLAS_ISSUER")
        if not jwks_url or not issuer:
            raise RuntimeError(
                "atlas_backend.flask requires ATLAS_JWKS_URL and ATLAS_ISSUER "
                "in app.config."
            )
        self.backend = AtlasBackend(
            jwks_url=jwks_url,
            issuer=issuer,
            authorized_parties=app.config.get("ATLAS_AUTHORIZED_PARTIES"),
        )
        app.extensions[_EXTENSION_KEY] = self

    def verify_request(self) -> SessionClaims | None:
        """Verify the current request's session, or ``None``."""
        assert self.backend is not None
        try:
            return self.backend.authenticate(
                authorization=request.headers.get("Authorization"),
                session_cookie=request.cookies.get("__session"),
            )
        except VerificationError:
            return None


def _current_extension() -> Atlas:
    ext = current_app.extensions.get(_EXTENSION_KEY)
    if ext is None:
        raise RuntimeError(
            "The Atlas extension is not initialised. Call Atlas(app) or "
            "Atlas().init_app(app) during setup."
        )
    return ext


def atlas_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Route decorator that requires a valid Atlas session.

    On success, sets ``g.atlas`` (the :class:`SessionClaims`) and
    ``g.atlas_user`` (the :class:`AtlasUser`). On failure, returns ``401``.
    """

    @wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        claims = _current_extension().verify_request()
        if claims is None:
            response: Response = jsonify(
                errors=[{"code": "UNAUTHORIZED", "message": "Authentication required."}]
            )
            response.status_code = 401
            return response
        g.atlas = claims
        g.atlas_user = AtlasUser.from_claims(claims)
        return view_func(*args, **kwargs)

    return wrapper
