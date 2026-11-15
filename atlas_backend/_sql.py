"""Executors that turn a database handle into the ``execute(sql, params) -> (rows, rowcount)`` callable the SQL
stores (:class:`SqlSidStore`, :class:`SqlWebhookDedupeStore`) take. Placeholders in the stores' statements are
``%s`` (postgres, mysql) or ``?`` (sqlite).

    store = SqlSidStore(dbapi_executor(psycopg.connect(DSN)))            # any DB-API 2.0 connection
    store = SqlSidStore(sqlalchemy_executor(engine), dialect="postgres")  # SQLAlchemy is optional
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any

Executor = Callable[[str, Sequence[Any]], "tuple[list[Any], int]"]


def dbapi_executor(connection: Any) -> Executor:
    """Run each statement on a DB-API 2.0 ``connection`` and commit it. Rows come back only for statements that
    produce a result set (a ``select`` or an ``insert ... returning``)."""

    def execute(sql: str, params: Sequence[Any]) -> tuple[list[Any], int]:
        cur = connection.cursor()
        try:
            cur.execute(sql, tuple(params))
            rows = list(cur.fetchall()) if cur.description else []
            count = cur.rowcount if cur.rowcount is not None else len(rows)
            connection.commit()
            return rows, count
        except BaseException:
            connection.rollback()
            raise
        finally:
            cur.close()

    return execute


def sqlalchemy_executor(engine: Any) -> Executor:
    """Run each statement on a SQLAlchemy ``Engine`` (``%s`` / ``?`` placeholders become bound parameters)."""
    from sqlalchemy import text

    def execute(sql: str, params: Sequence[Any]) -> tuple[list[Any], int]:
        names = iter(f"p{i}" for i in range(len(params)))
        named = re.sub(r"%s|\?", lambda _: f":{next(names)}", sql)
        with engine.begin() as conn:
            result = conn.execute(text(named), {f"p{i}": v for i, v in enumerate(params)})
            rows = [tuple(r) for r in result.fetchall()] if result.returns_rows else []
            return rows, result.rowcount if result.rowcount is not None else len(rows)

    return execute
