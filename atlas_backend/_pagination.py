"""Cursor-pagination helpers.

Walk every page of a cursor-paginated BAPI list, yielding items one at a time.
Works with any resource ``list`` that takes keyword ``limit``/``starting_after``
(plus any route-specific filters) and returns a ``{ data, has_more,
next_cursor }`` page — ``users.list``, ``organizations.list``,
``invitations.list``, ``audit_logs.list``, ``waitlist.list``.

    for user in paginate(client.users.list):
        ...

Kept as free functions rather than bolted onto every return value: the page is
the primitive most callers want, and a caller who needs the whole set opts into
the extra round trips explicitly.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Iterator, Mapping
from typing import (
    Any,
    Callable,
)

# A ``list`` method returns a page ``TypedDict`` (``CursorPage``, ``ListPage``,
# ...); these helpers only duck-type over ``data``/``has_more``/``next_cursor``,
# so they accept any callable returning a string-keyed mapping.
_SyncList = Callable[..., Mapping[str, Any]]
_AsyncList = Callable[..., Awaitable[Mapping[str, Any]]]


def paginate(
    list_fn: _SyncList,
    /,
    **params: Any,
) -> Iterator[Any]:
    """Yield every item across every cursor page of a sync ``list`` method."""
    cursor = params.get("starting_after")
    while True:
        page = list_fn(**{**params, "starting_after": cursor})
        yield from page.get("data", [])
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor:
            return


def collect(
    list_fn: _SyncList,
    /,
    **params: Any,
) -> list[Any]:
    """Collect every page of a sync cursor-paginated list into one list."""
    return list(paginate(list_fn, **params))


async def aiterate(
    list_fn: _AsyncList,
    /,
    **params: Any,
) -> AsyncIterator[Any]:
    """Yield every item across every cursor page of an async ``list`` method."""
    cursor = params.get("starting_after")
    while True:
        page = await list_fn(**{**params, "starting_after": cursor})
        for item in page.get("data", []):
            yield item
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor:
            return


async def acollect(
    list_fn: _AsyncList,
    /,
    **params: Any,
) -> list[Any]:
    """Collect every page of an async cursor-paginated list into one list."""
    out: list[Any] = []
    async for item in aiterate(list_fn, **params):
        out.append(item)
    return out
