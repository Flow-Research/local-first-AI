from __future__ import annotations

from collections.abc import Iterable

from local_first_ai.storage.db_contract import (
    database_connection,
    normalize_optional_text,
    normalize_tags,
    utc_now,
    validate_context_type,
    validate_importance,
    validate_required_text,
)


def update_context_item(
    item_id: int,
    title: str | None = None,
    content: str | None = None,
    tags: str | Iterable[str] | None = None,
    importance: int | None = None,
) -> bool:
    """Update only the provided fields on an existing context item.

    This function keeps the original created_at value intact and updates
    updated_at when a real change is made. If the item does not exist or no
    fields are provided, it returns False.
    """

    if title is not None:
        title = validate_required_text(title, "title")
    if content is not None:
        content = validate_required_text(content, "content")
    if tags is not None:
        tags = normalize_tags(tags)
    if importance is not None:
        importance = validate_importance(importance)

    updates: list[str] = []
    parameters: list[object] = []

    if title is not None:
        updates.append("title = ?")
        parameters.append(title)
    if content is not None:
        updates.append("content = ?")
        parameters.append(content)
    if tags is not None:
        updates.append("tags = ?")
        parameters.append(tags)
    if importance is not None:
        updates.append("importance = ?")
        parameters.append(importance)

    if not updates:
        return False

    updates.append("updated_at = ?")
    parameters.append(utc_now())
    parameters.append(item_id)

    query = f"UPDATE context_items SET {', '.join(updates)} WHERE id = ?"

    with database_connection() as connection:
        cursor = connection.execute(query, tuple(parameters))
        return bool(cursor.rowcount)


def delete_context_item(item_id: int) -> bool:
    """Remove a context item by its ID and return whether it existed."""

    with database_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM context_items WHERE id = ?",
            (item_id,),
        )
        return bool(cursor.rowcount)


def prove_persistence() -> bool:
    """Open the database and run a simple query to prove it can be reopened."""

    try:
        with database_connection() as connection:
            connection.execute("SELECT 1").fetchone()
        return True
    except Exception:
        return False


def write_back_context(
    context_type: str,
    title: str,
    content: str,
    source: str | None = "inference_output",
    tags: str | Iterable[str] | None = None,
    importance: int = 1,
) -> int:
    """Write an inference result back into local context memory."""

    context_type = validate_context_type(context_type)
    title = validate_required_text(title, "title")
    content = validate_required_text(content, "content")
    source = normalize_optional_text(source, "source")
    tags = normalize_tags(tags)
    importance = validate_importance(importance)
    timestamp = utc_now()

    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO context_items (
                context_type,
                title,
                content,
                source,
                tags,
                importance,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                context_type,
                title,
                content,
                source,
                tags,
                importance,
                timestamp,
                timestamp,
            ),
        )
        return int(cursor.lastrowid)


__all__ = [
    "delete_context_item",
    "prove_persistence",
    "update_context_item",
    "write_back_context",
]
