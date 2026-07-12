"""Shared SQLite contract for the Month 1, Week 2 context store.

Fellow-owned modules should use :func:`get_connection` instead of opening
SQLite directly. This keeps the schema, row format, database location, and
test isolation consistent across create, read, search, and manage operations.

The main pattern fellows need is:

    with database_connection() as connection:
        rows = connection.execute("SELECT * FROM context_items").fetchall()

The context manager commits successful writes, rolls back failed writes, and
closes the database file automatically.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# The real app uses data/local_context_store.db. Tests replace it through the
# environment variable so they never write test records into the real database.
DATABASE_PATH_ENV = "LOCAL_CONTEXT_DB_PATH"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "local_context_store.db"

# Keeping valid types in one shared set prevents each fellow from inventing
# slightly different spellings for the same kind of memory.
VALID_CONTEXT_TYPES = frozenset(
    {
        "user_note",
        "project_note",
        "device_log",
        "learning_record",
        "config_decision",
        "conversation_context",
    }
)

MIN_IMPORTANCE = 1
MAX_IMPORTANCE = 5

# This is the one table all four fellow modules share.
CONTEXT_ITEMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS context_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    tags TEXT,
    importance INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# Indexes are lookup shortcuts. They help SQLite find common filters without
# scanning every stored item.
CONTEXT_ITEM_INDEXES = (
    """
    CREATE INDEX IF NOT EXISTS idx_context_type
    ON context_items(context_type);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_created_at
    ON context_items(created_at);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_importance
    ON context_items(importance);
    """,
)


def get_database_path(db_path: str | Path | None = None) -> Path:
    """Return the active database path.

    An explicit path wins. Otherwise, tests and demos can set
    ``LOCAL_CONTEXT_DB_PATH``. Normal application use falls back to
    ``data/local_context_store.db`` at the repository root.
    """

    selected_path = db_path or os.getenv(DATABASE_PATH_ENV) or DEFAULT_DB_PATH
    return Path(selected_path).expanduser().resolve()


def initialize_database(db_path: str | Path | None = None) -> Path:
    """Create the database directory, table, and shared retrieval indexes."""

    database_path = get_database_path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    # A sqlite3 connection context manager commits but does not close the file.
    # Explicit try/finally is used so Windows can release the database cleanly.
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(CONTEXT_ITEMS_SCHEMA)
        for index_statement in CONTEXT_ITEM_INDEXES:
            connection.execute(index_statement)
        connection.commit()
    finally:
        connection.close()

    return database_path


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open an initialized connection that returns mapping-friendly rows.

    The caller owns the returned connection and must close it. For most fellow
    APIs, :func:`database_connection` is the safer option because it commits on
    success, rolls back on error, and always closes the connection.
    """

    database_path = initialize_database(db_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def database_connection(
    db_path: str | Path | None = None,
) -> Iterator[sqlite3.Connection]:
    """Yield a transaction-safe connection and always close it.

    Fellows should prefer this helper for create, read, search, and manage
    functions. A raised exception triggers rollback, so a half-finished write
    is not left in local memory.
    """

    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def utc_now() -> str:
    """Return a timezone-aware ISO 8601 timestamp for database records."""

    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def validate_context_type(context_type: str) -> str:
    """Normalize and validate one of the six Week 2 context types."""

    if not isinstance(context_type, str):
        raise ValueError("context_type must be a string")

    normalized = context_type.strip()
    if normalized not in VALID_CONTEXT_TYPES:
        allowed = ", ".join(sorted(VALID_CONTEXT_TYPES))
        raise ValueError(
            f"Invalid context_type {context_type!r}. Expected one of: {allowed}"
        )
    return normalized


def validate_required_text(value: str, field_name: str) -> str:
    """Return trimmed required text or raise a clear validation error."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def validate_importance(importance: int) -> int:
    """Validate the shared importance scale of 1 (lowest) to 5 (highest)."""

    if isinstance(importance, bool) or not isinstance(importance, int):
        raise ValueError("importance must be an integer from 1 to 5")
    if not MIN_IMPORTANCE <= importance <= MAX_IMPORTANCE:
        raise ValueError("importance must be an integer from 1 to 5")
    return importance


def normalize_optional_text(value: str | None, field_name: str) -> str | None:
    """Trim optional text, preserving ``None`` for absent values."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or None")
    normalized = value.strip()
    return normalized or None


def normalize_tags(tags: str | Iterable[str] | None) -> str | None:
    """Store tags as a predictable comma-separated string.

    Fellow APIs may accept either ``"sqlite,database"`` or an iterable such as
    ``["sqlite", "database"]``. Empty tags and duplicate tags are removed.
    """

    if tags is None:
        return None

    # SQLite stores the tags in one TEXT column, so both accepted input forms
    # are normalized to the same comma-separated representation.
    if isinstance(tags, str):
        candidates = tags.split(",")
    elif isinstance(tags, Iterable):
        candidates = list(tags)
    else:
        raise ValueError("tags must be a comma-separated string, an iterable, or None")

    normalized_tags: list[str] = []
    seen: set[str] = set()
    for tag in candidates:
        if not isinstance(tag, str):
            raise ValueError("every tag must be a string")
        normalized = tag.strip()
        if normalized and normalized not in seen:
            normalized_tags.append(normalized)
            seen.add(normalized)

    return ",".join(normalized_tags) or None


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a SQLite row to the common dictionary representation."""

    return dict(row) if row is not None else None


__all__ = [
    "CONTEXT_ITEMS_SCHEMA",
    "CONTEXT_ITEM_INDEXES",
    "DATABASE_PATH_ENV",
    "DEFAULT_DB_PATH",
    "MAX_IMPORTANCE",
    "MIN_IMPORTANCE",
    "PROJECT_ROOT",
    "VALID_CONTEXT_TYPES",
    "database_connection",
    "get_connection",
    "get_database_path",
    "initialize_database",
    "normalize_optional_text",
    "normalize_tags",
    "row_to_dict",
    "utc_now",
    "validate_context_type",
    "validate_importance",
    "validate_required_text",
]
