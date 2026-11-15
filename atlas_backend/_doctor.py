"""``atlas_backend.doctor``: check that this machine can talk to Atlas the way your app expects.

    python -m atlas_backend doctor            # reads ATLAS_SECRET_KEY, ATLAS_API_URL, ATLAS_JWKS_URL, ATLAS_ISSUER

    from atlas_backend import doctor
    report = doctor(secret_key="sk_live_...", jwks_url="https://id.example.com/.well-known/jwks.json")
    assert report.ok, report.format()

Checks: ``config`` (key shape, https base URL), ``api`` (reachable, latency), ``clock`` (local clock against the
API's ``Date`` header: skew breaks token ``iat`` / ``exp`` checks), ``auth`` (the key is accepted), ``jwks``
(reachable and parseable, when a URL is given), ``status`` (the Atlas status endpoint) and ``issuer``
(discovery document, when an issuer is given). A failed check never raises; read ``report.checks``.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

import httpx

from ._transport import DEFAULT_BASE_URL

#: Clock skew (seconds) past which token checks start to fail.
CLOCK_SKEW_WARN_SECONDS = 30


@dataclass
class DoctorCheck:
    name: str
    #: ``ok``, ``warn`` or ``fail``.
    status: str
    detail: str


@dataclass
class DoctorReport:
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.status != "fail" for c in self.checks)

    def add(self, name: str, status: str, detail: str) -> None:
        self.checks.append(DoctorCheck(name, status, detail))

    def format(self) -> str:
        mark = {"ok": "ok  ", "warn": "warn", "fail": "FAIL"}
        return "\n".join(f"[{mark[c.status]}] {c.name}: {c.detail}" for c in self.checks)


def doctor(
    *,
    secret_key: str | None = None,
    base_url: str | None = None,
    jwks_url: str | None = None,
    issuer: str | None = None,
    http_client: httpx.Client | None = None,
    timeout: float = 10.0,
) -> DoctorReport:
    """Run every check and return the report. Unset arguments fall back to ``ATLAS_SECRET_KEY``,
    ``ATLAS_API_URL``, ``ATLAS_JWKS_URL`` and ``ATLAS_ISSUER``. The key is never printed."""
    key = secret_key or os.environ.get("ATLAS_SECRET_KEY")
    base = (base_url or os.environ.get("ATLAS_API_URL") or DEFAULT_BASE_URL).rstrip("/")
    jwks_url = jwks_url or os.environ.get("ATLAS_JWKS_URL")
    issuer = issuer or os.environ.get("ATLAS_ISSUER")
    report = DoctorReport()
    client = http_client or httpx.Client(timeout=timeout)

    # config
    if not key:
        report.add("config", "fail", "no secret key: pass secret_key= or set ATLAS_SECRET_KEY")
    elif not key.startswith(("sk_", "psk_")):
        report.add("config", "fail", "the key does not start with sk_ (instance) or psk_ (platform)")
    else:
        kind = "platform key" if key.startswith("psk_") else "instance secret key"
        mode = "live" if "_live_" in key else "test" if "_test_" in key else "unknown mode"
        report.add("config", "ok", f"{kind} ({mode})")
    parts = urlsplit(base)
    if parts.scheme != "https" and parts.hostname not in ("localhost", "127.0.0.1"):
        report.add("config", "fail", f"base URL {base} is not https")

    try:
        # api + clock
        t0 = time.perf_counter()
        try:
            res = client.get(f"{base}/v1/status", headers={"accept": "application/json"})
            latency = (time.perf_counter() - t0) * 1000
            report.add("api", "ok" if res.status_code < 500 else "fail", f"{base} answered {res.status_code} in {latency:.0f} ms")
            date = res.headers.get("date")
            if date:
                skew = time.time() - parsedate_to_datetime(date).timestamp()
                if abs(skew) > CLOCK_SKEW_WARN_SECONDS:
                    report.add("clock", "fail", f"local clock is {skew:+.0f}s from Atlas; JWT iat / exp checks will fail")
                else:
                    report.add("clock", "ok", f"within {abs(skew):.1f}s of Atlas")
            else:
                report.add("clock", "warn", "the API sent no Date header")
            status = res.json() if res.status_code == 200 else None
            if isinstance(status, dict) and isinstance(status.get("status"), str):
                report.add("status", "ok" if status["status"] == "operational" else "warn", f"Atlas reports {status['status']}")
            else:
                report.add("status", "warn", "the status endpoint did not answer")
        except (httpx.HTTPError, ValueError) as e:
            report.add("api", "fail", f"{base} is unreachable: {type(e).__name__}")

        # auth
        if key:
            try:
                path = "/v1/platform/whoami" if key.startswith("psk_") else "/v1/instance"
                res = client.get(f"{base}{path}", headers={"authorization": f"Bearer {key}", "accept": "application/json"})
                if res.status_code == 200:
                    report.add("auth", "ok", "the key is accepted")
                elif res.status_code in (401, 403):
                    report.add("auth", "fail" if res.status_code == 401 else "warn", f"{res.status_code}: " + ("the key is invalid or revoked" if res.status_code == 401 else "the key works but lacks the instance:read scope"))
                else:
                    report.add("auth", "warn", f"unexpected answer {res.status_code}")
            except httpx.HTTPError as e:
                report.add("auth", "fail", f"request failed: {type(e).__name__}")

        # jwks
        if jwks_url:
            try:
                res = client.get(jwks_url, headers={"accept": "application/json"})
                keys = res.json().get("keys") if res.status_code == 200 else None
                if isinstance(keys, list) and keys:
                    report.add("jwks", "ok", f"{len(keys)} signing key(s) at {jwks_url}")
                else:
                    report.add("jwks", "fail", f"{jwks_url} answered {res.status_code} without keys")
            except (httpx.HTTPError, ValueError, AttributeError) as e:
                report.add("jwks", "fail", f"{jwks_url} is unreachable or malformed: {type(e).__name__}")
        else:
            report.add("jwks", "warn", "no JWKS URL given (ATLAS_JWKS_URL): skipped")

        # issuer
        if issuer:
            url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
            try:
                res = client.get(url, headers={"accept": "application/json"})
                doc: Any = res.json() if res.status_code == 200 else None
                if isinstance(doc, dict) and doc.get("issuer", "").rstrip("/") == issuer.rstrip("/"):
                    report.add("issuer", "ok", "discovery document matches the issuer")
                else:
                    report.add("issuer", "fail", f"{url} answered {res.status_code} or names another issuer")
            except (httpx.HTTPError, ValueError) as e:
                report.add("issuer", "fail", f"{url} failed: {type(e).__name__}")
    finally:
        if http_client is None:
            client.close()
    return report
