"""Wire shapes shared across resource namespaces.

The wire is snake_case JSON; these types mirror it exactly (no camelCase
translation), because the SDK's job is to type the BAPI, not to invent a second
dialect a reader would then have to reconcile against the docs.

Return objects are ``TypedDict``s for editor/type-checker help, but every
namespace method ultimately hands back a plain ``dict`` parsed from JSON — a
``TypedDict`` *is* a ``dict`` at runtime, so nothing is wrapped or copied. Page
containers are kept non-generic so the package installs cleanly on Python 3.9,
which does not support generic ``TypedDict``; a page's ``data`` items follow the
object ``TypedDict`` documented on the method that returns them.
"""

from __future__ import annotations

from typing import Any, TypedDict

#: A free-form metadata bag. The BAPI stores arbitrary JSON objects here.
Metadata = dict[str, Any]

#: Any parsed JSON object the BAPI returns.
JSON = dict[str, Any]


class CursorPage(TypedDict):
    """The ``GET /v1/users``-style cursor page.

    No total, a boolean ``has_more``, and an opaque ``next_cursor`` to pass back
    as ``starting_after``.
    """

    data: list[Any]
    has_more: bool
    next_cursor: str | None


class ListPage(TypedDict, total=False):
    """The ``{ object: 'list', data, has_more }`` envelope some list routes use."""

    object: str
    data: list[Any]
    has_more: bool


class DeletedObject(TypedDict):
    """A minimal deletion acknowledgement several mutation routes return."""

    object: str
    id: str
    deleted: bool
