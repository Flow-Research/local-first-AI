"""Integration demo for the Month 1, Week 2 Local Context Store.

This file owns orchestration only. The create, read, search, and manage
implementations remain in the four fellow-owned modules described in the Week
2 plan. As those modules are merged, this demo connects them into one flow.

Expected fellow API return values:

* ``create_context_item`` and ``write_back_context`` return the new integer ID.
* list and search functions return lists of mapping-like context items.
* ``get_context_item`` returns one mapping-like item or ``None``.
* ``prepare_context_for_inference`` returns a formatted string.
* ``update_context_item``, ``delete_context_item``, and ``prove_persistence``
  return truthy values on success and falsey values when no item is found.
"""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any


if __package__ in {None, ""}:
    # Allow: python src/python/local_first_ai/storage/week_02_demo.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from local_first_ai.storage.db_contract import (  # noqa: E402
    DATABASE_PATH_ENV,
    initialize_database,
)


class FellowAPIsNotReadyError(RuntimeError):
    """Raised when one or more fellow-owned modules have not landed yet."""


REQUIRED_APIS = {
    "local_first_ai.storage.create_context": ("create_context_item",),
    "local_first_ai.storage.read_context": (
        "list_context_items",
        "get_context_item",
    ),
    "local_first_ai.storage.search_context": (
        "search_context_items",
        "prepare_context_for_inference",
    ),
    "local_first_ai.storage.manage_context": (
        "update_context_item",
        "delete_context_item",
        "prove_persistence",
        "write_back_context",
    ),
}


def load_fellow_apis() -> dict[str, Callable[..., Any]]:
    """Load the fellow-owned functions and report all missing APIs together."""

    loaded: dict[str, Callable[..., Any]] = {}
    missing: list[str] = []

    for module_name, function_names in REQUIRED_APIS.items():
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name:
                missing.extend(f"{module_name}.{name}" for name in function_names)
                continue
            raise

        for function_name in function_names:
            function = getattr(module, function_name, None)
            if callable(function):
                loaded[function_name] = function
            else:
                missing.append(f"{module_name}.{function_name}")

    if missing:
        missing_list = "\n- ".join(missing)
        raise FellowAPIsNotReadyError(
            "The Week 2 demo is waiting for these fellow APIs:\n"
            f"- {missing_list}"
        )

    return loaded


@contextmanager
def _selected_database(db_path: str | Path | None):
    """Temporarily select a database for the demo and restore the environment."""

    previous_path = os.environ.get(DATABASE_PATH_ENV)
    if db_path is not None:
        os.environ[DATABASE_PATH_ENV] = str(Path(db_path).resolve())

    try:
        database_path = initialize_database(db_path)
        yield database_path
    finally:
        if db_path is not None:
            if previous_path is None:
                os.environ.pop(DATABASE_PATH_ENV, None)
            else:
                os.environ[DATABASE_PATH_ENV] = previous_path


def _require_new_id(value: Any, operation: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeError(f"{operation} must return the new positive integer ID")
    return value


def _require_success(value: Any, operation: str) -> None:
    if not value:
        raise RuntimeError(f"{operation} did not report success")


def run_demo(
    db_path: str | Path | None = None,
    output: Callable[[str], None] = print,
) -> None:
    """Run the complete Week 2 scenario against the active SQLite database."""

    apis = load_fellow_apis()

    create_context_item = apis["create_context_item"]
    list_context_items = apis["list_context_items"]
    get_context_item = apis["get_context_item"]
    search_context_items = apis["search_context_items"]
    prepare_context_for_inference = apis["prepare_context_for_inference"]
    update_context_item = apis["update_context_item"]
    delete_context_item = apis["delete_context_item"]
    prove_persistence = apis["prove_persistence"]
    write_back_context = apis["write_back_context"]

    with _selected_database(db_path) as database_path:
        output("Week 2 Local Context Store Demo")
        output(f"Database: {database_path}")

        output("\n[1] Creating context items...")
        decision_id = _require_new_id(
            create_context_item(
                context_type="config_decision",
                title="Database choice",
                content=(
                    "We chose SQLite because it is local, lightweight, "
                    "file-based, and works offline."
                ),
                source="week-02-discussion",
                tags="sqlite,database,local-first",
                importance=5,
            ),
            "create_context_item",
        )
        project_id = _require_new_id(
            create_context_item(
                context_type="project_note",
                title="Week 2 goal",
                content=(
                    "Week 2 builds the Local Context Store for local-first "
                    "memory and future inference."
                ),
                source="week-02-plan",
                tags="week-02,context,local-first",
                importance=4,
            ),
            "create_context_item",
        )
        output("Done.")

        output("\n[2] Reading stored context...")
        items = list_context_items()
        if not isinstance(items, list) or len(items) < 2:
            raise RuntimeError("list_context_items must return the stored items")
        if get_context_item(decision_id) is None:
            raise RuntimeError("get_context_item could not read a created item")
        output(f"Found {len(items)} context item(s).")
        output("Done.")

        output("\n[3] Searching relevant context...")
        matches = search_context_items("SQLite")
        if not isinstance(matches, list) or not matches:
            raise RuntimeError("search_context_items did not find the SQLite item")
        output(f"Found {len(matches)} database-related item(s).")
        output("Done.")

        output("\n[4] Preparing context for inference...")
        prepared_context = prepare_context_for_inference("SQLite", limit=5)
        if not isinstance(prepared_context, str) or not prepared_context.strip():
            raise RuntimeError(
                "prepare_context_for_inference must return a non-empty string"
            )
        output(prepared_context)
        output("Done.")

        output("\n[5] Simulating LLM response...")
        simulated_answer = (
            "SQLite was selected because it provides lightweight, offline, "
            "file-based storage for the first local context layer."
        )
        output(simulated_answer)
        output("Done.")

        output("\n[6] Writing useful output back to local memory...")
        write_back_id = _require_new_id(
            write_back_context(
                context_type="conversation_context",
                title="Week 2 database explanation",
                content=simulated_answer,
                source="inference_output",
            ),
            "write_back_context",
        )
        if get_context_item(write_back_id) is None:
            raise RuntimeError("The write-back item could not be read")
        output("Done.")

        output("\n[7] Updating and deleting context...")
        _require_success(
            update_context_item(
                decision_id,
                tags="sqlite,database,local-first,offline",
                importance=5,
            ),
            "update_context_item",
        )
        _require_success(delete_context_item(project_id), "delete_context_item")
        if get_context_item(project_id) is not None:
            raise RuntimeError("delete_context_item did not remove the item")
        output("Done.")

        output("\n[8] Proving persistence...")
        _require_success(prove_persistence(), "prove_persistence")
        output("Done.")

        output("\nLocal Context Store demo completed successfully.")


def main() -> int:
    try:
        run_demo()
    except FellowAPIsNotReadyError as error:
        print(error, file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Week 2 demo failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
