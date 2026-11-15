"""OpenTelemetry for the SDK (opt-in): one client span and request metrics per API call.

    pip install 'atlas-backend[otel]'

    from atlas_backend import AtlasClient, Telemetry

    atlas = AtlasClient("sk_live_...", telemetry=Telemetry())   # or telemetry=True

With ``telemetry=None`` (the default) nothing is imported and nothing is recorded: the OpenTelemetry
packages are only needed when you turn this on. Spans are named ``Atlas <METHOD> <route>`` and carry
``http.request.method``, ``http.route``, ``http.response.status_code``, ``atlas.retries`` and the error
type; the secret key and query string never appear. Metrics: ``atlas.client.requests`` (counter),
``atlas.client.request.duration`` (histogram, seconds) and ``atlas.client.retries`` (counter). Without
an explicit ``traceparent`` the current trace context is sent on the request, so Atlas carries your
trace id onto the webhooks and logouts the call causes.
"""

from __future__ import annotations

import re
import time
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any

_ID_SEGMENT = re.compile(r"^(?:[A-Za-z]+_[A-Za-z0-9]{8,}|[0-9a-fA-F-]{16,}|\d+)$")


def route_of(path: str) -> str:
    """A low-cardinality route for ``path``: id-looking segments become ``{}``."""
    out = []
    for seg in path.split("?")[0].split("/"):
        out.append("{}" if seg and _ID_SEGMENT.match(seg) else seg)
    return "/".join(out)


class Telemetry:
    """Wraps each request in a client span and records metrics. Pass ``tracer`` / ``meter`` (or the providers)
    to use your own; by default the global OpenTelemetry providers are used."""

    def __init__(self, *, tracer: Any = None, meter: Any = None, tracer_provider: Any = None, meter_provider: Any = None) -> None:
        try:
            from opentelemetry import metrics, propagate, trace
        except ImportError as e:  # pragma: no cover - exercised only without the extra
            raise ImportError("Telemetry needs OpenTelemetry: pip install 'atlas-backend[otel]'") from e
        self._trace = trace
        self._propagate = propagate
        self._tracer = tracer or trace.get_tracer("atlas_backend", tracer_provider=tracer_provider)
        meter = meter or metrics.get_meter("atlas_backend", meter_provider=meter_provider)
        self._requests = meter.create_counter("atlas.client.requests", unit="1", description="Atlas API calls")
        self._duration = meter.create_histogram("atlas.client.request.duration", unit="s", description="Atlas API call duration")
        self._retries = meter.create_counter("atlas.client.retries", unit="1", description="Atlas API call retries")

    @contextmanager
    def request(self, method: str, path: str) -> Iterator[_Call]:
        route = route_of(path)
        start = time.perf_counter()
        call = _Call(self, method.upper(), route)
        with self._tracer.start_as_current_span(
            f"Atlas {method.upper()} {route}",
            kind=self._trace.SpanKind.CLIENT,
            attributes={"http.request.method": method.upper(), "http.route": route, "rpc.system": "atlas"},
        ) as span:
            call.span = span
            try:
                yield call
            except BaseException as e:
                call.error = type(e).__name__
                span.record_exception(e)
                span.set_status(self._trace.Status(self._trace.StatusCode.ERROR, call.error))
                raise
            finally:
                if call.status is not None:
                    span.set_attribute("http.response.status_code", call.status)
                span.set_attribute("atlas.retries", call.retries)
                attrs = {"http.request.method": method.upper(), "http.route": route}
                if call.status is not None:
                    attrs["http.response.status_code"] = call.status
                if call.error:
                    attrs["error.type"] = call.error
                self._requests.add(1, attrs)
                self._duration.record(time.perf_counter() - start, attrs)
                if call.retries:
                    self._retries.add(call.retries, {"http.request.method": method.upper(), "http.route": route})

    def inject(self, headers: dict[str, str]) -> None:
        """Add the current trace context as ``traceparent`` unless the caller set one."""
        if "traceparent" not in {k.lower() for k in headers}:
            self._propagate.inject(headers)


class _Call:
    def __init__(self, telemetry: Telemetry, method: str, route: str) -> None:
        self.telemetry, self.method, self.route = telemetry, method, route
        self.span: Any = None
        self.status: int | None = None
        self.retries = 0
        self.error: str | None = None
