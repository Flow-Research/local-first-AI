"""Unit tests for Fellow 1's create_context_item.

Run with the module runner from the repository root (inside the venv):

    python3 -m unittest tests.python.storage.test_create_context

The venv's `local_first_ai.pth` puts `src/python` on the import path, so no
`sys.path` hack is needed.

Each test gets a fresh isolated SQLite database through LOCAL_CONTEXT_DB_PATH,
so no data leaks into data/local_context_store.db.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from local_first_ai.storage import create_context
from local_first_ai.storage import db_contract


class CreateContextTestCase(unittest.TestCase):
    def setUp(self):
        # Fresh database per test, pointed at by LOCAL_CONTEXT_DB_PATH so the
        # module under test writes to the temp file instead of the real store.
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

    def fetch_context(self, item_id: int) -> dict | None:
        with db_contract.database_connection() as connection:
            row = connection.execute(
                "SELECT * FROM context_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        return db_contract.row_to_dict(row)


class TestCreateContextItem(CreateContextTestCase):
    def test_create_stores_valid_item_and_returns_its_id(self):
        item_id = create_context.create_context_item(
            context_type="config_decision",
            title="Database choice",
            content="SQLite is local, lightweight, and works offline.",
            source="week-02-discussion",
            tags="sqlite,database,local-first",
            importance=5,
        )

        self.assertIsInstance(item_id, int)
        self.assertGreater(item_id, 0)

        stored = self.fetch_context(item_id)
        self.assertIsNotNone(stored)
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

    def test_invalid_context_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            create_context.create_context_item(
                context_type="random_memory",
                title="Invalid type",
                content="This item must not be stored.",
            )

    def test_empty_title_raises_value_error(self):
        with self.assertRaises(ValueError):
            create_context.create_context_item(
                context_type="user_note",
                title="   ",
                content="Content is fine.",
            )

    def test_empty_content_raises_value_error(self):
        with self.assertRaises(ValueError):
            create_context.create_context_item(
                context_type="user_note",
                title="Valid title",
                content="",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
