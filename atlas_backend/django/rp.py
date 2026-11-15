"""Django adapter for :class:`atlas_backend.RelyingParty`.

    # urls.py
    from atlas_backend.django.rp import rp_urlpatterns
    urlpatterns = [*rp_urlpatterns(rp), ...]       # /auth/sign-in, /auth/callback, /auth/sign-out

``rp_view(rp)`` is the single view behind them; mount it yourself on custom paths (set ``routes=`` on the
relying party to match). Add ``backchannel_logout`` to ``routes`` and ``on_backchannel_logout`` to the
relying party to receive Atlas's back-channel logout (the view is CSRF-exempt: the signed token is the proof).
"""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlsplit

from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .._rp import RelyingParty, RpRequest, RpResponse

__all__ = ["rp_view", "rp_urlpatterns", "to_rp_request", "to_django_response"]


def to_rp_request(request: HttpRequest) -> RpRequest:
    headers = {k[5:].replace("_", "-").lower(): v for k, v in request.META.items() if k.startswith("HTTP_")}
    if request.META.get("CONTENT_TYPE"):
        headers["content-type"] = request.META["CONTENT_TYPE"]
    form = {k: v for k, v in request.POST.items()} if request.method == "POST" else None
    return RpRequest(request.method or "GET", request.build_absolute_uri(), headers, form)


def to_django_response(out: RpResponse) -> HttpResponse:
    response = HttpResponse(out.body, status=out.status)
    cookies = []
    for k, v in out.headers:
        if k.lower() == "set-cookie":
            cookies.append(v)
        else:
            response[k] = v
    _install_set_cookie(response, cookies)
    return response


def _install_set_cookie(response: HttpResponse, values: list[str]) -> None:
    # HttpResponse.headers is case-insensitive and single-valued; ``cookies`` is the only multi-value
    # channel, so parse each raw cookie into it (attributes survive: path, max-age, secure, httponly, samesite).
    from http.cookies import SimpleCookie

    for raw in values:
        jar: SimpleCookie = SimpleCookie()
        jar.load(raw)
        for name, morsel in jar.items():
            response.cookies[name] = morsel.value
            for attr, v in morsel.items():
                if v not in ("", None):
                    response.cookies[name][attr] = v


def rp_view(rp: RelyingParty) -> Callable[[HttpRequest], HttpResponse]:
    """A view that answers the relying party's routes and 404s on anything else."""

    @csrf_exempt
    def view(request: HttpRequest) -> HttpResponse:
        out = rp.handle(to_rp_request(request))
        return HttpResponseNotFound() if out is None else to_django_response(out)

    return view


def rp_urlpatterns(rp: RelyingParty) -> list[Any]:
    """``path()`` entries for the sign-in, callback, sign-out (and back-channel logout) routes."""
    routes = {
        rp.routes.get("sign_in", "/auth/sign-in"),
        rp.routes.get("callback", urlsplit(rp.redirect_uri).path),
        rp.routes.get("sign_out", "/auth/sign-out"),
    }
    if rp.routes.get("backchannel_logout"):
        routes.add(rp.routes["backchannel_logout"])
    view = rp_view(rp)
    return [path(p.lstrip("/"), view) for p in sorted(routes)]
