"""Read layer for the Month 1, Week 2 local context store.

Fellow 2 owns these four read APIs. They return plain, complete dictionaries so
callers (and Fellow 3's search layer) can treat each item as a normal mapping
without knowing about SQLite rows.

    items = list_context_items()
    item = get_context_item(item_id)
    notes = list_context_by_type("user_note")
    recent = list_recent_context(limit=5)
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

from local_first_ai.storage.db_contract import (
    database_connection,
    row_to_dict,
    validate_context_type,
)


def _rows_to_complete_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert fetched rows into complete dictionaries without type suppression.

    ``database_connection`` configures ``sqlite3.Row`` as the connection row
    factory. Therefore, ``fetchall()`` returns a list of ``sqlite3.Row`` objects,
    or an empty list when no rows match. A ``None`` result from ``row_to_dict``
    would mean the shared database contract was violated.
    """

    results: list[dict[str, Any]] = []
    for row in rows:
        converted = row_to_dict(row)
        if converted is None:
            raise RuntimeError(
                "row_to_dict returned None for a fetched row; "
                "the database contract was violated"
            )
        results.append(converted)
    return results


def list_context_items() -> list[dict[str, Any]]:
    """Return every stored context item as a complete dict.

    Ordering is deterministic by ``id ASC`` for predictable browsing. Returns an
    empty list when the store is empty; never raises for "no rows".
    """

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM context_items
            ORDER BY id ASC
            """
        ).fetchall()

    return _rows_to_complete_dicts(rows)


def get_context_item(item_id: int) -> dict[str, Any] | None:
    """Return one complete context item by its integer ID.

    Returns ``None`` for an invalid ID (non-integer, boolean, or non-positive)
    or when no row with that ID exists. This keeps read access safe against bad
    input and missing records without raising.
    """

    if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
        return None

    with database_connection() as connection:
        row = connection.execute(
            "SELECT * FROM context_items WHERE id = ?",
            (item_id,),
        ).fetchone()

    # ``fetchone`` returns ``None`` for a missing row, and ``row_to_dict``
    # maps that to ``None`` -- exactly the documented "missing ID" result.
    return row_to_dict(row)


def list_context_by_type(context_type: str) -> list[dict[str, Any]]:
    """Return every stored item of one validated context type, ordered by ID.

    Uses the shared ``validate_context_type`` helper, so an unknown type raises
    a clear ``ValueError``. Results are ordered ``id ASC`` for predictable
    browsing. Returns an empty list when nothing matches.
    """

    context_type = validate_context_type(context_type)

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM context_items
            WHERE context_type = ?
            ORDER BY id ASC
            """,
            (context_type,),
        ).fetchall()

    return _rows_to_complete_dicts(rows)


def list_recent_context(limit: int = 10) -> list[dict[str, Any]]:
    """Return up to ``limit`` of the most recently created items.

    Ordering is newest first by ``created_at DESC``, then ``id DESC``. The
    ``limit`` must be a positive integer; anything else raises ``ValueError``.
    """

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM context_items
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return _rows_to_complete_dicts(rows)


__all__ = [
    "list_context_items",
    "get_context_item",
    "list_context_by_type",
    "list_recent_context",
]
