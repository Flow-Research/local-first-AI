"""Retrieval layer for the Month 1, Week 2 local context store.

Typical flow for a user question like "What did we decide about SQLite?":

    keyword = "SQLite"
    prompt_block = prepare_context_for_inference(keyword)
    # prompt_block is then prepended to the LLM prompt as extra context.
"""

from __future__ import annotations

import time
from typing import Any

from local_first_ai.storage.db_contract import (
    database_connection,
    row_to_dict,
    validate_context_type,
    validate_required_text,
)


def _search_rows(keyword: str, context_type: str | None = None) -> list[dict[str, Any]]:
    """Shared SQL for keyword search across title/content, optionally scoped.

    SQLite's LIKE operator is case-insensitive for ASCII by default, so a
    keyword like "sqlite" matches "SQLite" without extra normalization.
    Results are ordered by importance first (higher importance is more
    likely to matter for inference), then by recency.
    """

    keyword = validate_required_text(keyword, "keyword")
    like_pattern = f"%{keyword}%"

    query = """
        SELECT *
        FROM context_items
        WHERE (title LIKE ? OR content LIKE ?)
    """
    params: list[Any] = [like_pattern, like_pattern]

    if context_type is not None:
        query += " AND context_type = ?"
        params.append(context_type)

    query += " ORDER BY importance DESC, created_at DESC"

    with database_connection() as connection:
        cursor = connection.execute(query, params)
        rows = cursor.fetchall()

    return [row_to_dict(row) for row in rows] #type: ignore


def search_context_items(keyword: str) -> list[dict[str, Any]]:
    """Search title and content for a keyword across all context types.

    Returns an empty list when nothing matches, never raises for "no
    results" -- only invalid input (e.g. an empty keyword) raises.
    """

    return _search_rows(keyword)


def search_context_by_type(context_type: str, keyword: str) -> list[dict[str, Any]]:
    """Search title and content for a keyword, restricted to one context_type."""

    context_type = validate_context_type(context_type)
    return _search_rows(keyword, context_type=context_type)


def get_top_context_for_prompt(keyword: str, limit: int = 5) -> list[dict[str, Any]]:
    """Return up to `limit` of the most relevant matches for a keyword."""

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")

    return search_context_items(keyword)[:limit]


def prepare_context_for_inference(keyword: str, limit: int = 5) -> str:
    """Format the top matching context items into an LLM-ready text block.

    Example output:

        Relevant Local Context:
        [1] Type: config_decision
        Title: Database choice
        Content: We chose SQLite because it is local, lightweight, and works offline.
        [2] Type: project_note
        Title: Week 2 goal
        Content: Week 2 builds the Local Context Store for local-first memory.
    """

    top_results = get_top_context_for_prompt(keyword, limit=limit)

    if not top_results:
        return "Relevant Local Context:\nNo matching context found."

    lines = ["Relevant Local Context:"]
    for position, item in enumerate(top_results, start=1):
        lines.append(f"[{position}] Type: {item['context_type']}")
        lines.append(f"Title: {item['title']}")
        lines.append(f"Content: {item['content']}")

    return "\n".join(lines)


def measure_fetch_time(keyword: str) -> tuple[list[dict[str, Any]], float]:
    """Run a keyword search and return (results, elapsed_seconds).

    This gives a simple, dependency-free way to demonstrate that search
    over the local context store is fast, without needing a profiler.
    Use it in tests or the screenshot demo like:

        results, elapsed = measure_fetch_time("SQLite")
        print(f"Found {len(results)} matches in {elapsed * 1000:.2f} ms")
    """

    start = time.perf_counter()
    results = search_context_items(keyword)
    elapsed = time.perf_counter() - start
    return results, elapsed


__all__ = [
    "search_context_items",
    "search_context_by_type",
    "get_top_context_for_prompt",
    "prepare_context_for_inference",
    "measure_fetch_time",
]


if __name__ == "__main__":
    # Quick manual demo -- useful for capturing the fellow-3 screenshot.
    demo_keyword = "local"
    demo_results, demo_elapsed = measure_fetch_time(demo_keyword)

    print(f"search_context_items({demo_keyword!r}) -> {len(demo_results)} result(s)")
    print(f"Elapsed: {demo_elapsed * 1000:.3f} ms\n")

    print(prepare_context_for_inference(demo_keyword))