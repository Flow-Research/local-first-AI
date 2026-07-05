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


def create_context_item(
    context_type: str,
    title: str,
    content: str,
    source: str | None = None,
    tags: str | Iterable[str] | None = None,
    importance: int = 1,
) -> int:
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
