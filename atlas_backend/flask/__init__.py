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

Moving from Better Auth? Set ``ATLAS_BETTER_AUTH_BRIDGE`` to ``True`` (or a dict of
``cookie_prefix``, ``cookie_name``, ``better_auth_cookie_domain``, ``secure`` and
``sign_in_url``) with ``ATLAS_SECRET_KEY``: a GET/HEAD carrying a Better Auth session
cookie and no Atlas session is exchanged once for an Atlas session and redirected to
the same URL with ``__session`` / ``__atlas_rt`` set and the Better Auth cookies
cleared (a user who owes a second factor goes to ``sign_in_url`` with
``__atlas_attempt`` / ``__atlas_status``). ``ATLAS_API_URL`` overrides the Backend
API origin.

:func:`atlas_required` verifies the ``Authorization: Bearer <jwt>`` header
(preferred) or the ``__session`` cookie, exposes the verified claims on
``g.atlas`` and the principal on ``g.atlas_user``, and returns ``401`` when
there is no valid session.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Flask, after_this_request, current_app, g, jsonify, redirect, request
from flask.wrappers import Response
from werkzeug.wrappers import Response as BaseResponse

from .._access_token import AccessTokenVerifier, dpop_header
from .._better_auth import BetterAuthBridge, BridgeCookie, bridge_from_setting
from .._verify import AtlasBackend, AtlasUser, SessionClaims, VerificationError

__all__ = ["Atlas", "atlas_required", "access_token_required"]

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
        self.bridge: BetterAuthBridge | None = None
        self.bridge_sign_in_url: str | None = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        jwks_url = app.config.get("ATLAS_JWKS_URL")
        issuer = app.config.get("ATLAS_ISSUER")
        if not jwks_url or not issuer:
            raise RuntimeError(
                "atlas_backend.flask requires ATLAS_JWKS_URL and ATLAS_ISSUER in app.config."
            )
        self.backend = AtlasBackend(
            jwks_url=jwks_url,
            issuer=issuer,
            authorized_parties=app.config.get("ATLAS_AUTHORIZED_PARTIES"),
            # Cutover from Better Auth: a list of LegacyIssuer.
            legacy_issuers=app.config.get("ATLAS_LEGACY_ISSUERS"),
            secret_key=app.config.get("ATLAS_SECRET_KEY"),
            **({"api_url": app.config["ATLAS_API_URL"]} if app.config.get("ATLAS_API_URL") else {}),
        )
        app.extensions[_EXTENSION_KEY] = self
        built = bridge_from_setting(
            app.config.get("ATLAS_BETTER_AUTH_BRIDGE"),
            secret_key=app.config.get("ATLAS_SECRET_KEY"),
            base_url=app.config.get("ATLAS_API_URL"),
        )
        if built is not None:
            self.bridge, self.bridge_sign_in_url = built
            app.before_request(self._better_auth_bridge)

    def _better_auth_bridge(self) -> BaseResponse | None:
        """Exchange a Better Auth session cookie for an Atlas session (GET/HEAD)."""
        if self.bridge is None or request.method not in ("GET", "HEAD"):
            return None
        forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        decision = self.bridge(
            request.cookies,
            client_ip=forwarded or request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )
        if decision.action == "none":
            return None
        if decision.action in ("signed_in", "needs_mfa"):
            target = (
                (request.full_path if request.query_string else request.path)
                if decision.action == "signed_in"
                else decision.continuation_url(self.bridge_sign_in_url or request.url)
            )
            response = redirect(target)
            for cookie in decision.cookies:
                _set_cookie(response, cookie)
            return response
        cookies = decision.cookies

        @after_this_request
        def _clear(resp: Response) -> Response:
            for cookie in cookies:
                _set_cookie(resp, cookie)
            return resp

        return None

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


def _set_cookie(response: BaseResponse, cookie: BridgeCookie) -> None:
    response.set_cookie(
        cookie.name,
        cookie.value,
        max_age=cookie.max_age,
        path=cookie.path,
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=cookie.http_only,
        samesite=cookie.same_site.capitalize() if cookie.same_site else None,
    )


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


def access_token_required(
    verifier: AccessTokenVerifier, *required_scopes: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Route decorator that requires an Atlas-issued OAuth access token for your API.

    On success sets ``g.atlas_access_token`` (the :class:`AccessTokenResult`). A refusal
    answers with the verifier's status and the RFC 6750 / RFC 9449 / RFC 9728
    ``WWW-Authenticate`` challenge. A DPoP-bound token must come with a valid ``DPoP``
    proof for this request; the verifier's ``DPoP-Nonce``, when it issues nonces, is set
    on every response.
    """

    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            path = request.full_path if request.query_string else request.path
            result = verifier.verify(
                request.headers.get("Authorization"),
                required_scopes=required_scopes,
                method=request.method,
                url=verifier.request_url(request.url, path),
                dpop=dpop_header(request.headers.getlist("DPoP")),
            )
            if not result.ok:
                response: Response = jsonify(error=result.error or "unauthorized")
                response.status_code = result.status
                response.headers["WWW-Authenticate"] = result.www_authenticate
                if result.dpop_nonce:
                    response.headers["DPoP-Nonce"] = result.dpop_nonce
                return response
            if result.dpop_nonce:
                nonce = result.dpop_nonce

                @after_this_request
                def _set_nonce(resp: Response) -> Response:
                    resp.headers["DPoP-Nonce"] = nonce
                    return resp

            g.atlas_access_token = result
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
