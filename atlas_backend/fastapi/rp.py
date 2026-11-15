"""FastAPI / Starlette adapter for :class:`atlas_backend.RelyingParty`.

    from atlas_backend.fastapi.rp import rp_router
    app.include_router(rp_router(rp))      # /auth/sign-in, /auth/callback, /auth/sign-out (+ back-channel logout)

Takes an :class:`~atlas_backend.AsyncRelyingParty`, so the handlers never block the event loop.
"""

from typing import Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Request, Response

from .._arp import AsyncRelyingParty
from .._rp import RpRequest, RpResponse

__all__ = ["rp_router", "to_starlette_response"]


def to_starlette_response(out: RpResponse) -> Response:
    response = Response(content=out.body, status_code=out.status)
    for k, v in out.headers:
        response.headers.append(k, v)  # append() keeps every Set-Cookie
    return response


def rp_router(rp: AsyncRelyingParty) -> APIRouter:
    router = APIRouter()
    paths = {
        rp.routes.get("sign_in", "/auth/sign-in"),
        rp.routes.get("callback", urlsplit(rp.redirect_uri).path),
        rp.routes.get("sign_out", "/auth/sign-out"),
    }
    if rp.routes.get("backchannel_logout"):
        paths.add(rp.routes["backchannel_logout"])

    async def endpoint(request: Request) -> Response:
        form: Optional[dict] = None
        if request.method == "POST":
            form = {k: str(v) for k, v in (await request.form()).items()}
        rp_request = RpRequest(request.method, str(request.url), dict(request.headers), form)
        out = await rp.handle(rp_request)
        return Response(status_code=404) if out is None else to_starlette_response(out)

    for p in sorted(paths):
        router.add_api_route(p, endpoint, methods=["GET", "POST"], include_in_schema=False)
    return router
