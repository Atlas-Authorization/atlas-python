"""OpenTelemetry spans (opt-in) and the CLI device-flow login."""

from __future__ import annotations

import httpx
import pytest
import respx

from atlas_backend import AtlasClient, CliLogin, CliLoginRequiredError, OAuthFlowError, Telemetry
from atlas_backend._telemetry import route_of

API = "https://api.example.test"
ISSUER = "https://id.example.test"


def test_route_of_collapses_ids() -> None:
    assert route_of("/v1/users/usr_01H8ZABCDEFG/sessions") == "/v1/users/{}/sessions"


def test_telemetry_records_a_client_span() -> None:
    pytest.importorskip("opentelemetry.sdk")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with respx.mock(base_url=API) as mock:
        route = mock.get("/v1/users/usr_01H8ZABCDEFG").mock(return_value=httpx.Response(200, json={}))
        AtlasClient("sk_t", base_url=API, telemetry=Telemetry(tracer_provider=provider)).users.get("usr_01H8ZABCDEFG")
    (span,) = exporter.get_finished_spans()
    assert span.name == "Atlas GET /v1/users/{}"
    assert span.attributes["http.response.status_code"] == 200
    assert "sk_t" not in str(span.attributes)
    assert "traceparent" in route.calls.last.request.headers


def test_device_flow_login_stores_and_refreshes_a_session() -> None:
    store: dict = {}

    class Store:
        def load(self): return store.get("s")
        def save(self, s): store["s"] = s
        def clear(self): store.pop("s", None)

    clock = [1_000_000]
    with respx.mock() as mock:
        mock.post(f"{ISSUER}/oauth2/device_authorization").mock(return_value=httpx.Response(200, json={
            "device_code": "dc", "user_code": "ABCD-EFGH", "verification_uri_complete": f"{ISSUER}/device?c=1",
            "expires_in": 600, "interval": 1}))
        mock.post(f"{ISSUER}/oauth2/token").mock(side_effect=[
            httpx.Response(400, json={"error": "authorization_pending"}),
            httpx.Response(200, json={"access_token": "a1", "refresh_token": "r1", "expires_in": 30}),
            httpx.Response(200, json={"access_token": "a2", "expires_in": 3600}),
        ])
        lines: list[str] = []
        cli = CliLogin(issuer=ISSUER, client_id="c", app_name="mytool", mode="device", store=Store(), open_browser=False,
                       print_fn=lines.append, sleep=lambda s: None, now=lambda: clock[0])
        session = cli.login()
        assert session["access_token"] == "a1" and "ABCD-EFGH" in lines[1]
        assert cli.get_access_token() == "a2"  # a1 expires within 60 s: refreshed
        assert store["s"]["refresh_token"] == "r1"
    cli.store.clear()
    with pytest.raises(CliLoginRequiredError):
        cli.get_access_token()


def test_device_flow_denied() -> None:
    with respx.mock() as mock:
        mock.post(f"{ISSUER}/oauth2/device_authorization").mock(return_value=httpx.Response(200, json={
            "device_code": "dc", "user_code": "X", "verification_uri_complete": f"{ISSUER}/d", "expires_in": 600, "interval": 1}))
        mock.post(f"{ISSUER}/oauth2/token").mock(return_value=httpx.Response(400, json={"error": "access_denied"}))
        cli = CliLogin(issuer=ISSUER, client_id="c", app_name="t", mode="device", store=type("S", (), {"load": lambda s: None, "save": lambda s, x: None, "clear": lambda s: None})(),
                       open_browser=False, print_fn=lambda s: None, sleep=lambda s: None)
        with pytest.raises(OAuthFlowError) as e:
            cli.login()
    assert e.value.code == "access_denied"
