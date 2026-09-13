"""Cross-property SSO handshake — the satellite's server-side redeem step.

When a satellite (a property on a DIFFERENT registrable domain than the main
app) has no local session, its web handler bounces the browser through
``GET {fapi_origin}/v1/client/handshake?publishable_key={pk}&redirect_url={url}``
which — if the user has an Atlas session — redirects back with
``?__atlas_hs=ok&__atlas_hu=<user_id>&__atlas_hn=<nonce>``. This module exchanges
that single-use nonce for a fresh session, server-to-server, so the tokens are
returned in the response BODY (never a URL). The satellite then sets them as its
OWN first-party cookies — ``__session`` = ``jwt`` (script-readable, short-lived)
and ``__atlas_rt`` = ``refresh_token`` (HttpOnly).

**PKCE binding (RFC 7636, S256).** The return ``nonce`` rides ``redirect_url``,
which routinely lands in access logs, ``Referer`` headers, and browser history —
so it must NOT be a bearer credential on its own. The handshake is therefore
bound to a Proof Key for Code Exchange: on the OUTBOUND bounce the satellite
mints a :func:`create_pkce_pair`, appends ``code_challenge=<challenge>`` to the
handshake URL (the challenge is safe to log — it is a one-way SHA-256 of the
verifier), and stashes the ``verifier`` server-side out of band. On the return
leg it feeds that same ``verifier`` back to :func:`redeem_handshake` as
``code_verifier``; a leaked nonce alone cannot be redeemed without it. The Atlas
server now REQUIRES this — a redeem without a matching verifier is rejected.

The verifier is stashed as a short-lived HttpOnly cookie so it never reaches
page scripts and expires with the handshake window::

    from atlas_backend import (
        create_pkce_pair,
        read_handshake_params,
        redeem_handshake,
    )

    FAPI = "https://id.atlasauth.net"

    # OUTBOUND: no local session — bounce the browser to the handshake.
    def start_handshake(request, response):
        pkce = create_pkce_pair()
        # The challenge is a one-way hash — safe to place on a loggable URL.
        url = (
            f"{FAPI}/v1/client/handshake"
            f"?publishable_key=pk_live_..."
            f"&redirect_url={quote(current_url, safe='')}"
            f"&code_challenge={pkce.challenge}"
        )
        # Stash the VERIFIER server-side — HttpOnly so scripts can't read it,
        # path '/' and ~300s so it outlives only this handshake round trip.
        response.set_cookie(
            "__atlas_hv", pkce.verifier,
            path="/", max_age=300, httponly=True, samesite="lax", secure=True,
        )
        response.redirect(url)

    # RETURN LEG: exchange the single-use nonce + verifier for a session.
    def finish_handshake(request, response):
        params = read_handshake_params(request.url)
        if params is not None:
            user_id, nonce = params
            session = redeem_handshake(
                fapi_origin=FAPI,
                publishable_key="pk_live_...",
                user_id=user_id,
                nonce=nonce,
                code_verifier=request.cookies.get("__atlas_hv", ""),
            )
            if session is not None:
                # These are the cookie VALUES to set as first-party cookies:
                response.set_cookie(
                    "__session", session.jwt,
                    path="/", samesite="lax", secure=True,
                )
                response.set_cookie(
                    "__atlas_rt", session.refresh_token,
                    path="/", httponly=True, samesite="lax", secure=True,
                )
                response.delete_cookie("__atlas_hv", path="/")  # one-shot
            # else: nonce/verifier bad/expired/used — treat as signed-out.

A bad, expired, or already-used nonce (or a missing/mismatched verifier) is a
normal "signed-out" signal, so both helpers return ``None`` in that case rather
than raising — an auth miss should never take the satellite's page down.

(Same-registrable-domain SUBDOMAINS do not need this — the handshake sets a
parent-domain cookie directly; this is only the cross-domain path.)
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import NamedTuple
from urllib.parse import parse_qs, urlsplit

import httpx

#: The satellite redeem path, joined onto the caller's ``fapi_origin``.
_REDEEM_PATH = "/v1/client/handshake/redeem"


class PKCEPair(NamedTuple):
    """A PKCE (RFC 7636) ``(verifier, challenge)`` pair for one handshake.

    A :class:`typing.NamedTuple`, so it unpacks like a tuple
    (``verifier, challenge = pair``) and also reads by name
    (``pair.verifier``). Both members are ``str`` (unpadded base64url — URL-safe
    and header-safe with no percent-encoding needed).
    """

    #: The high-entropy secret. Stash server-side (HttpOnly cookie ``__atlas_hv``,
    #: path ``/``, ~300s) and feed back to :func:`redeem_handshake` as
    #: ``code_verifier``. NEVER put this on a URL.
    verifier: str
    #: ``base64url(sha256(verifier))`` — safe to place on the (loggable)
    #: handshake URL as ``code_challenge`` because it is a one-way hash.
    challenge: str


def create_pkce_pair() -> PKCEPair:
    """Mint a fresh PKCE ``(verifier, challenge)`` pair for a handshake bounce.

    The handshake return ``nonce`` travels on ``redirect_url`` and so leaks into
    access logs, ``Referer`` headers, and browser history; on its own it would
    be a bearer credential anyone with that log line could replay. PKCE closes
    that hole: only the ``challenge`` (a one-way SHA-256 hash) rides the URL,
    while the ``verifier`` that produced it is held server-side and required at
    redeem — so a stolen nonce is useless without the matching verifier.

    Uses the S256 method mandated by the Atlas server:

    * ``verifier``  = ``base64url(secrets.token_bytes(32))``, unpadded — 32 bytes
      of CSPRNG entropy (256 bits), comfortably inside RFC 7636's 43–128 char
      window and drawn from :mod:`secrets`, never :mod:`random`.
    * ``challenge`` = ``base64url(sha256(verifier.encode("ascii")))``, unpadded.

    Padding (``=``) is stripped from both because unpadded base64url needs no
    percent-encoding on a URL or in a cookie value, and the server compares the
    unpadded forms. Call this once per outbound bounce (never reuse a pair).
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PKCEPair(verifier=verifier, challenge=challenge)


@dataclass(frozen=True)
class HandshakeSession:
    """A fresh session minted from a redeemed handshake nonce.

    The satellite sets these as its own first-party cookies: ``jwt`` as
    ``__session`` (script-readable, short-lived) and ``refresh_token`` as
    ``__atlas_rt`` (HttpOnly).
    """

    #: The ``__session`` JWT value (script-readable, short-lived).
    jwt: str
    #: The ``__atlas_rt`` refresh value (set HttpOnly).
    refresh_token: str
    #: The server-side session id this JWT belongs to.
    session_id: str
    #: Seconds until the ``__session`` JWT expires.
    expires_in: int


class HandshakeParams(NamedTuple):
    """The ``(user_id, nonce)`` pair carried on the handshake return URL.

    A :class:`typing.NamedTuple`, so it unpacks like a tuple
    (``user_id, nonce = params``) and also reads by name (``params.user_id``).
    """

    user_id: str
    nonce: str


def read_handshake_params(url_or_query: str) -> HandshakeParams | None:
    """Parse a handshake return URL (or bare query string) into its params.

    Returns a :class:`HandshakeParams` — ``(user_id, nonce)`` — only when
    ``__atlas_hs == "ok"`` and both ``__atlas_hu`` (user id) and ``__atlas_hn``
    (nonce) are present; otherwise ``None``. Accepts a full URL
    (``https://sat.example.com/cb?__atlas_hs=ok&...``) or just its query part
    (``__atlas_hs=ok&...`` or ``?__atlas_hs=ok&...``).
    """
    # A full URL has a scheme/netloc/path; a bare query string does not. Split
    # on the first '?' when present, else treat the whole input as the query.
    if "?" in url_or_query:
        query = urlsplit(url_or_query).query or url_or_query.split("?", 1)[1]
    else:
        query = url_or_query.lstrip("?")

    parsed = parse_qs(query, keep_blank_values=True)

    def _first(key: str) -> str | None:
        values = parsed.get(key)
        return values[0] if values else None

    if _first("__atlas_hs") != "ok":
        return None
    user_id = _first("__atlas_hu")
    nonce = _first("__atlas_hn")
    if not user_id or not nonce:
        return None
    return HandshakeParams(user_id=user_id, nonce=nonce)


def _to_session(payload: object) -> HandshakeSession | None:
    """Build a :class:`HandshakeSession` from the redeem response body, or ``None``."""
    if not isinstance(payload, dict):
        return None
    jwt = payload.get("jwt")
    refresh_token = payload.get("refresh_token")
    if not isinstance(jwt, str) or not jwt:
        return None
    if not isinstance(refresh_token, str) or not refresh_token:
        return None
    session_id = payload.get("session_id")
    expires_in = payload.get("expires_in")
    return HandshakeSession(
        jwt=jwt,
        refresh_token=refresh_token,
        session_id=session_id if isinstance(session_id, str) else "",
        expires_in=expires_in if isinstance(expires_in, int) else 0,
    )


def redeem_handshake(
    *,
    fapi_origin: str,
    publishable_key: str,
    user_id: str,
    nonce: str,
    code_verifier: str,
    timeout: float = 30.0,
    http_client: httpx.Client | None = None,
) -> HandshakeSession | None:
    """Exchange a single-use handshake nonce for a fresh session (server-to-server).

    POSTs ``{"user_id", "nonce", "code_verifier"}`` to
    ``{fapi_origin}/v1/client/handshake/redeem`` with an ``x-publishable-key``
    header. On HTTP 2xx returns a :class:`HandshakeSession`; on any non-2xx, a
    transport error, or a malformed body returns ``None`` — a bad/expired/
    already-used nonce, or a ``code_verifier`` that does not hash to the
    ``code_challenge`` sent on the outbound bounce, is a normal signed-out
    signal, not an exception. The publishable key is non-secret, so it is sent
    as a header (never in the URL).

    Args:
        fapi_origin: Origin of the Atlas Frontend API, e.g.
            ``https://id.atlasauth.net``. Trailing slashes are tolerated.
        publishable_key: The instance publishable key (``pk_...``).
        user_id: The ``__atlas_hu`` value from the return URL.
        nonce: The single-use ``__atlas_hn`` nonce from the return URL.
        code_verifier: The PKCE verifier stashed on the outbound bounce (the
            ``verifier`` of the :func:`create_pkce_pair` whose ``challenge`` was
            sent as ``code_challenge``). The Atlas server requires it and checks
            that ``base64url(sha256(code_verifier)) == code_challenge``; without
            a match the redeem fails and this returns ``None``.
        timeout: Per-request timeout in seconds (ignored when ``http_client``
            is supplied).
        http_client: An optional pre-configured :class:`httpx.Client`. One is
            created and closed per call if omitted.
    """
    url = f"{fapi_origin.rstrip('/')}{_REDEEM_PATH}"
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
        "x-publishable-key": publishable_key,
    }
    body = {"user_id": user_id, "nonce": nonce, "code_verifier": code_verifier}

    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=timeout)
    try:
        response = client.post(url, headers=headers, json=body)
    except httpx.HTTPError:
        return None
    finally:
        if owns_client:
            client.close()

    if not response.is_success:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    return _to_session(payload)


async def aredeem_handshake(
    *,
    fapi_origin: str,
    publishable_key: str,
    user_id: str,
    nonce: str,
    code_verifier: str,
    timeout: float = 30.0,
    http_client: httpx.AsyncClient | None = None,
) -> HandshakeSession | None:
    """Async peer of :func:`redeem_handshake` (over ``asyncio``).

    Same contract and return semantics — including the required ``code_verifier``
    PKCE binding; accepts an optional pre-configured :class:`httpx.AsyncClient`.
    """
    url = f"{fapi_origin.rstrip('/')}{_REDEEM_PATH}"
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
        "x-publishable-key": publishable_key,
    }
    body = {"user_id": user_id, "nonce": nonce, "code_verifier": code_verifier}

    owns_client = http_client is None
    client = http_client or httpx.AsyncClient(timeout=timeout)
    try:
        response = await client.post(url, headers=headers, json=body)
    except httpx.HTTPError:
        return None
    finally:
        if owns_client:
            await client.aclose()

    if not response.is_success:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    return _to_session(payload)
