"""Contract tests for all four Month 1, Week 2 fellow slices.

Run from the repository root:

    python -m unittest discover -s tests/python/storage -v

Each fellow-owned test class is skipped only while its module does not exist.
Once a fellow adds their module, that slice's tests become active. The shared
database contract tests always run.
"""

from __future__ import annotations

import importlib
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PYTHON_SOURCE_ROOT = REPOSITORY_ROOT / "src" / "python"
sys.path.insert(0, str(PYTHON_SOURCE_ROOT))

from local_first_ai.storage import db_contract  # noqa: E402
from local_first_ai.storage import week_02_demo  # noqa: E402


def _optional_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name == module_name:
            return None
        raise


CREATE_MODULE = _optional_module("local_first_ai.storage.create_context")
READ_MODULE = _optional_module("local_first_ai.storage.read_context")
SEARCH_MODULE = _optional_module("local_first_ai.storage.search_context")
MANAGE_MODULE = _optional_module("local_first_ai.storage.manage_context")


class TemporaryContextDatabaseTestCase(unittest.TestCase):
    """Provide an isolated database without changing fellow API signatures."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temporary_directory.name) / "local_context_store.db"
        )
        self.environment = patch.dict(
            os.environ,
            {db_contract.DATABASE_PATH_ENV: str(self.database_path)},
        )
        self.environment.start()
        db_contract.initialize_database()

    def tearDown(self):
        self.environment.stop()
        self.temporary_directory.cleanup()

    def insert_context(
        self,
        *,
        context_type: str = "project_note",
        title: str = "Test context",
        content: str = "Useful local context for a test.",
        source: str | None = "contract-test",
        tags: str | None = "test,local",
        importance: int = 3,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> int:
        created_at = created_at or db_contract.utc_now()
        updated_at = updated_at or created_at
        with db_contract.database_connection() as connection:
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
                    created_at,
                    updated_at,
                ),
            )
            return int(cursor.lastrowid)

    def fetch_context(self, item_id: int) -> dict | None:
        with db_contract.database_connection() as connection:
            row = connection.execute(
                "SELECT * FROM context_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        return db_contract.row_to_dict(row)

    def assert_context_mapping(self, item) -> Mapping:
        self.assertIsInstance(item, Mapping)
        required_fields = {
            "id",
            "context_type",
            "title",
            "content",
            "source",
            "tags",
            "importance",
            "created_at",
            "updated_at",
        }
        self.assertTrue(required_fields.issubset(item.keys()))
        return item


class TestDatabaseContract(TemporaryContextDatabaseTestCase):
    def test_database_uses_requested_test_path(self):
        self.assertEqual(db_contract.get_database_path(), self.database_path.resolve())
        self.assertTrue(self.database_path.exists())

    def test_schema_contains_the_shared_columns_and_indexes(self):
        with db_contract.database_connection() as connection:
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(context_items)"
                ).fetchall()
            }
            indexes = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA index_list(context_items)"
                ).fetchall()
            }

        self.assertEqual(
            columns,
            {
                "id",
                "context_type",
                "title",
                "content",
                "source",
                "tags",
                "importance",
                "created_at",
                "updated_at",
            },
        )
        self.assertTrue(
            {"idx_context_type", "idx_created_at", "idx_importance"}.issubset(
                indexes
            )
        )

    def test_connection_returns_mapping_friendly_rows(self):
        item_id = self.insert_context()
        with db_contract.database_connection() as connection:
            row = connection.execute(
                "SELECT * FROM context_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        self.assertIsInstance(row, sqlite3.Row)
        self.assertEqual(row["id"], item_id)

    def test_shared_validation_helpers(self):
        self.assertEqual(
            db_contract.validate_context_type(" config_decision "),
            "config_decision",
        )
        self.assertEqual(db_contract.validate_required_text(" title ", "title"), "title")
        self.assertEqual(
            db_contract.normalize_tags(["sqlite", "local-first", "sqlite"]),
            "sqlite,local-first",
        )
        self.assertEqual(db_contract.validate_importance(5), 5)

        with self.assertRaises(ValueError):
            db_contract.validate_context_type("unknown")
        with self.assertRaises(ValueError):
            db_contract.validate_required_text(" ", "title")
        with self.assertRaises(ValueError):
            db_contract.validate_importance(6)


@unittest.skipUnless(
    CREATE_MODULE,
    "Fellow 1: add local_first_ai.storage.create_context to activate these tests",
)
class TestCreateContext(TemporaryContextDatabaseTestCase):
    def test_create_returns_unique_ids_and_stores_complete_items(self):
        first_id = CREATE_MODULE.create_context_item(
            context_type="config_decision",
            title="Database choice",
            content="SQLite is local, lightweight, and works offline.",
            source="week-02-discussion",
            tags="sqlite,database,local-first",
            importance=5,
        )
        second_id = CREATE_MODULE.create_context_item(
            context_type="user_note",
            title="Offline requirement",
            content="The application must remain useful without cloud access.",
        )

        self.assertIsInstance(first_id, int)
        self.assertGreater(first_id, 0)
        self.assertIsInstance(second_id, int)
        self.assertNotEqual(first_id, second_id)

        stored = self.fetch_context(first_id)
        self.assertEqual(stored["context_type"], "config_decision")
        self.assertEqual(stored["title"], "Database choice")
        self.assertEqual(
            stored["content"],
            "SQLite is local, lightweight, and works offline.",
        )
        self.assertEqual(stored["source"], "week-02-discussion")
        self.assertEqual(stored["tags"], "sqlite,database,local-first")
        self.assertEqual(stored["importance"], 5)
        self.assertTrue(stored["created_at"])
        self.assertTrue(stored["updated_at"])
        datetime.fromisoformat(stored["created_at"])
        datetime.fromisoformat(stored["updated_at"])

    def test_create_rejects_empty_title_and_content(self):
        valid = {
            "context_type": "user_note",
            "title": "Valid title",
            "content": "Valid content",
        }
        for field_name, invalid_value in (("title", " "), ("content", "")):
            arguments = {**valid, field_name: invalid_value}
            with self.subTest(field=field_name):
                with self.assertRaises(ValueError):
                    CREATE_MODULE.create_context_item(**arguments)

    def test_create_rejects_invalid_context_type(self):
        with self.assertRaises(ValueError):
            CREATE_MODULE.create_context_item(
                context_type="random_memory",
                title="Invalid type",
                content="This item must not be stored.",
            )


@unittest.skipUnless(
    READ_MODULE,
    "Fellow 2: add local_first_ai.storage.read_context to activate these tests",
)
class TestReadContext(TemporaryContextDatabaseTestCase):
    def test_empty_database_is_clear_and_missing_id_does_not_crash(self):
        self.assertEqual(READ_MODULE.list_context_items(), [])
        self.assertIsNone(READ_MODULE.get_context_item(999_999))
        self.assertEqual(READ_MODULE.list_context_by_type("user_note"), [])
        self.assertEqual(READ_MODULE.list_recent_context(), [])

    def test_list_and_get_return_complete_items(self):
        first_id = self.insert_context(title="First item")
        second_id = self.insert_context(title="Second item")

        items = READ_MODULE.list_context_items()
        self.assertIsInstance(items, list)
        self.assertEqual({item["id"] for item in items}, {first_id, second_id})
        self.assert_context_mapping(READ_MODULE.get_context_item(first_id))

    def test_filter_by_context_type(self):
        user_note_id = self.insert_context(
            context_type="user_note",
            title="User preference",
        )
        self.insert_context(
            context_type="device_log",
            title="Device event",
        )

        items = READ_MODULE.list_context_by_type("user_note")
        self.assertEqual([item["id"] for item in items], [user_note_id])

    def test_recent_context_respects_limit_and_newest_first(self):
        self.insert_context(
            title="Old",
            created_at="2026-01-01T00:00:00+00:00",
        )
        middle_id = self.insert_context(
            title="Middle",
            created_at="2026-01-02T00:00:00+00:00",
        )
        newest_id = self.insert_context(
            title="Newest",
            created_at="2026-01-03T00:00:00+00:00",
        )

        items = READ_MODULE.list_recent_context(limit=2)
        self.assertEqual([item["id"] for item in items], [newest_id, middle_id])


@unittest.skipUnless(
    SEARCH_MODULE,
    "Fellow 3: add local_first_ai.storage.search_context to activate these tests",
)
class TestSearchContext(TemporaryContextDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.decision_id = self.insert_context(
            context_type="config_decision",
            title="Database choice",
            content="We chose SQLite because it is local and works offline.",
            importance=5,
        )
        self.project_id = self.insert_context(
            context_type="project_note",
            title="SQLite integration goal",
            content="Week 2 builds the first local memory layer.",
            importance=4,
        )
        self.insert_context(
            context_type="device_log",
            title="Battery report",
            content="The laptop battery is healthy.",
            importance=1,
        )

    def test_search_matches_title_and_content_case_insensitively(self):
        matches = SEARCH_MODULE.search_context_items("sqlite")
        self.assertEqual(
            {item["id"] for item in matches},
            {self.decision_id, self.project_id},
        )

        content_matches = SEARCH_MODULE.search_context_items("OFFLINE")
        self.assertEqual(
            [item["id"] for item in content_matches],
            [self.decision_id],
        )

    def test_search_by_type_limits_results(self):
        matches = SEARCH_MODULE.search_context_by_type(
            "config_decision",
            "sqlite",
        )
        self.assertEqual([item["id"] for item in matches], [self.decision_id])

    def test_search_returns_empty_list_for_no_match(self):
        self.assertEqual(SEARCH_MODULE.search_context_items("no-such-keyword"), [])

    def test_top_context_prioritizes_importance(self):
        matches = SEARCH_MODULE.get_top_context_for_prompt("sqlite", limit=1)
        self.assertEqual([item["id"] for item in matches], [self.decision_id])

    def test_prepare_context_returns_inference_ready_text(self):
        prepared = SEARCH_MODULE.prepare_context_for_inference("sqlite", limit=5)
        self.assertIsInstance(prepared, str)
        self.assertIn("Relevant Local Context", prepared)
        self.assertIn("Database choice", prepared)
        self.assertIn("We chose SQLite", prepared)

    def test_small_local_search_completes_promptly(self):
        started = time.perf_counter()
        SEARCH_MODULE.search_context_items("sqlite")
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 1.0)


@unittest.skipUnless(
    MANAGE_MODULE,
    "Fellow 4: add local_first_ai.storage.manage_context to activate these tests",
)
class TestManageContext(TemporaryContextDatabaseTestCase):
    def test_update_changes_only_requested_fields_and_timestamp(self):
        original_timestamp = "2026-01-01T00:00:00+00:00"
        item_id = self.insert_context(
            title="Original title",
            content="Original content",
            tags="old",
            importance=1,
            created_at=original_timestamp,
            updated_at=original_timestamp,
        )

        result = MANAGE_MODULE.update_context_item(
            item_id,
            title="Updated title",
            tags="updated,local",
            importance=5,
        )
        self.assertTrue(result)

        stored = self.fetch_context(item_id)
        self.assertEqual(stored["title"], "Updated title")
        self.assertEqual(stored["content"], "Original content")
        self.assertEqual(stored["tags"], "updated,local")
        self.assertEqual(stored["importance"], 5)
        self.assertEqual(stored["created_at"], original_timestamp)
        self.assertNotEqual(stored["updated_at"], original_timestamp)

    def test_update_and_delete_missing_id_do_not_crash(self):
        self.assertFalse(
            MANAGE_MODULE.update_context_item(
                999_999,
                title="Missing",
            )
        )
        self.assertFalse(MANAGE_MODULE.delete_context_item(999_999))

    def test_delete_removes_existing_item(self):
        item_id = self.insert_context()
        self.assertTrue(MANAGE_MODULE.delete_context_item(item_id))
        self.assertIsNone(self.fetch_context(item_id))

    def test_prove_persistence_reopens_the_database(self):
        self.insert_context(title="Persistent item")
        self.assertTrue(MANAGE_MODULE.prove_persistence())

    def test_write_back_creates_inference_output(self):
        item_id = MANAGE_MODULE.write_back_context(
            context_type="conversation_context",
            title="Week 2 database explanation",
            content="The answer explained why SQLite was selected.",
        )
        self.assertIsInstance(item_id, int)
        self.assertGreater(item_id, 0)

        stored = self.fetch_context(item_id)
        self.assertEqual(stored["context_type"], "conversation_context")
        self.assertEqual(stored["source"], "inference_output")


@unittest.skipUnless(
    all((CREATE_MODULE, READ_MODULE, SEARCH_MODULE, MANAGE_MODULE)),
    "The full demo activates after all four fellow modules are present",
)
class TestWeek02Demo(TemporaryContextDatabaseTestCase):
    def test_integrated_demo_completes(self):
        output: list[str] = []
        week_02_demo.run_demo(self.database_path, output.append)
        rendered_output = "\n".join(output)
        self.assertIn("Week 2 Local Context Store Demo", rendered_output)
        self.assertIn(
            "Local Context Store demo completed successfully.",
            rendered_output,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
