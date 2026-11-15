"""Status-aware resilience (opt-in): honour ``Retry-After``, back off on 429 / 502 / 503 / 504 with
jittered exponential delays, retry a network error, and (optionally) read the Atlas status endpoint.

    from atlas_backend import AtlasClient, RetryPolicy

    atlas = AtlasClient("sk_live_...", retry=RetryPolicy(max_retries=3, status_aware=True))

Off by default (``retry=None``): no behaviour changes for existing callers. A write is retried only when
it carries an ``idempotency_key`` (or ``retry_writes=True``), so a retry can never apply it twice.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def parse_retry_after(value: str | None, now: Callable[[], float] = time.time) -> float | None:
    """``Retry-After`` as seconds from now: a delay in seconds or an HTTP date. ``None`` when absent or unusable."""
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        return max(0.0, parsedate_to_datetime(value).timestamp() - now())
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class RetryPolicy:
    """How a failed call is retried.

    Args:
        max_retries: retries after the first attempt (``0`` turns retrying off).
        base_delay / max_delay: seconds. The wait is full-jitter ``uniform(0, min(max_delay, base_delay * 2**n))``,
            or the server's ``Retry-After`` (capped at ``max_delay``) when it sent one.
        statuses: the response statuses worth another try.
        retry_writes: also retry a write without an ``idempotency_key`` (it may then apply twice).
        retry_network_errors: retry connection errors and timeouts.
        status_aware: after a 5xx or a network error, read ``GET /v1/status`` (cached for
            ``status_cache_seconds``); during a ``major_outage`` (top level or the ``backend_api`` component) wait
            ``max_delay`` instead of hammering a down service. The status is attached to the raised error as
            ``status_indicator``.
        sleep / random_fn / on_retry: injection points for tests and logging; ``on_retry(info)`` gets
            ``{"attempt", "delay", "status", "method", "path"}``.
    """

    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 30.0
    statuses: frozenset[int] = frozenset({429, 502, 503, 504})
    retry_writes: bool = False
    retry_network_errors: bool = True
    status_aware: bool = False
    status_cache_seconds: float = 30.0
    sleep: Callable[[float], None] | None = None
    random_fn: Callable[[], float] | None = None
    on_retry: Callable[[dict[str, Any]], None] | None = None
    _cache: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)
    _lock: Any = field(default_factory=threading.Lock, compare=False, repr=False)

    def allows(self, method: str, idempotency_key: str | None) -> bool:
        return self.retry_writes or method.upper() in _SAFE_METHODS or bool(idempotency_key)

    def wait_for(self, attempt: int, retry_after: float | None, indicator: str | None = None) -> float:
        """Seconds to wait before retry number ``attempt`` (0-based)."""
        if retry_after is not None:
            delay = min(retry_after, self.max_delay)
        else:
            rnd = (self.random_fn or random.random)()
            delay = rnd * min(self.max_delay, self.base_delay * (2**attempt))
        floor = self.max_delay if indicator == "major_outage" else 0.0
        return max(delay, floor)

    # -- the status endpoint --------------------------------------------------------------------

    def cached_indicator(self, now: float) -> tuple[bool, str | None]:
        """``(fresh, indicator)`` from the cache."""
        with self._lock:
            at, indicator = self._cache.get("status", (0.0, None))
        return now - at < self.status_cache_seconds, indicator

    def remember_indicator(self, now: float, body: Any) -> str | None:
        """Cache and return ``major_outage`` when ``GET /v1/status`` reports one (top level or the
        ``backend_api`` component), else the top-level status string (``operational``, ``degraded`` ...)."""
        indicator = None
        if isinstance(body, dict) and isinstance(body.get("status"), str):
            indicator = body["status"]
            for comp in body.get("components") or []:
                if isinstance(comp, dict) and comp.get("id") == "backend_api" and comp.get("status") == "major_outage":
                    indicator = "major_outage"
        with self._lock:
            self._cache["status"] = (now, indicator)
        return indicator
