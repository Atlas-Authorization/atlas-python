"""Flask adapter for :class:`atlas_backend.RelyingParty`.

    from atlas_backend.flask.rp import register_rp
    register_rp(app, rp)       # /auth/sign-in, /auth/callback, /auth/sign-out (+ back-channel logout)
"""

from __future__ import annotations

from urllib.parse import urlsplit

from flask import Flask, Response, request

from .._rp import RelyingParty, RpRequest, RpResponse

__all__ = ["register_rp", "to_flask_response"]


def to_flask_response(out: RpResponse) -> Response:
    response = Response(out.body, status=out.status)
    for k, v in out.headers:
        response.headers.add(k, v)  # add() keeps every Set-Cookie
    return response


def register_rp(app: Flask, rp: RelyingParty, *, name: str = "atlas_rp") -> None:
    """Register one view on each of the relying party's routes."""
    paths = {
        rp.routes.get("sign_in", "/auth/sign-in"),
        rp.routes.get("callback", urlsplit(rp.redirect_uri).path),
        rp.routes.get("sign_out", "/auth/sign-out"),
    }
    if rp.routes.get("backchannel_logout"):
        paths.add(rp.routes["backchannel_logout"])

    def view() -> Response:
        out = rp.handle(
            RpRequest(request.method, request.url, dict(request.headers), dict(request.form) if request.method == "POST" else None)
        )
        if out is None:
            return Response(status=404)
        return to_flask_response(out)

    for i, p in enumerate(sorted(paths)):
        app.add_url_rule(p, endpoint=f"{name}_{i}", view_func=view, methods=["GET", "POST"])
