"""The single error type every Backend API call raises on a non-2xx.

Atlas answers a failed BAPI call with the §9.1 envelope::

    { "errors": [ { "code", "message", "param?", "meta?" } ] }

``code`` is the stable, machine-readable part of that contract — integrators
branch on it (``LAST_ADMIN``, ``NOT_FOUND``, ``SCOPE_MISSING``, ...) — so it is
surfaced first-class here rather than buried in a parsed body. The raw
``errors`` list and the HTTP ``status`` are both kept so a caller can inspect
``param``/``meta`` (e.g. a rate limit's ``retry_after``) when they need to.
"""

from __future__ import annotations

from typing import Any, TypedDict


class ErrorItem(TypedDict, total=False):
    """One entry of the BAPI error envelope."""

    code: str
    message: str
    param: str
    meta: dict[str, Any]


class AtlasError(Exception):
    """Raised on any non-2xx response from the Backend API.

    Carries the HTTP ``status`` and the full parsed ``errors`` envelope. Branch
    on :attr:`code` (the first error's stable code) or use :meth:`has_code`.
    """

    status: int
    errors: list[ErrorItem]

    def __init__(
        self,
        status: int,
        errors: list[ErrorItem],
        message: str | None = None,
    ) -> None:
        first_message = errors[0].get("message") if errors else None
        super().__init__(
            message
            or first_message
            or f"Atlas API request failed with status {status}"
        )
        self.status = status
        self.errors = errors

    @property
    def code(self) -> str | None:
        """The first error's stable code, the field callers branch on most."""
        if not self.errors:
            return None
        return self.errors[0].get("code")

    def has_code(self, code: str) -> bool:
        """True when any error in the envelope carries the given stable code."""
        return any(e.get("code") == code for e in self.errors)
