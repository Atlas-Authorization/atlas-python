"""Tiny helpers shared by the hand-written and the generated resource modules."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote


def _enc(value: str) -> str:
    """Percent-encode one path segment."""
    return quote(value, safe="")


def _qd(params: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values from a query mapping (keys may be any wire name)."""
    return {k: v for k, v in params.items() if v is not None}
