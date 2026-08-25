"""Offline, deterministic tests for the Week 3 chat assistant.

Run from the repository root:

    python -m unittest tests.python.test_assistant -v

No live vmlx server, no installed ``openai`` package, and no network are
required. The suite uses the real Week 2 SQLite storage functions wired through
the assistant's injectable ``StorageBackend``, pointed at an isolated temporary
database via ``LOCAL_CONTEXT_DB_PATH``. The model is replaced by a fake
OpenAI-compatible client that scripted responses, so every flow -- model-first
routing where each non-help/exit message reaches the model with tools, grounded
answers, full CRUD, confirmation allow/deny, malformed or unknown tool calls,
and the model-unavailable fallback -- is exercised through the assistant's
public interface. The model -- not deterministic keyword matching -- decides
whether to read, write, list, search, or simply converse.

The assistant package is never modified; only its exported, injectable functions
and the ``ChatSession`` class are driven here. Implementation lives at
``local_first_ai.assistant.app``.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# Make the local source importable regardless of an active venv.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PYTHON_SOURCE_ROOT = REPOSITORY_ROOT / "src" / "python"
import sys  # noqa: E402

sys.path.insert(0, str(PYTHON_SOURCE_ROOT))

from local_first_ai.storage import db_contract  # noqa: E402
from local_first_ai.assistant import app as assistant  # noqa: E402
from local_first_ai.assistant.app import (  # noqa: E402
    MODEL_UNAVAILABLE_MESSAGE,
    ChatSession,
    Config,
    StorageBackend,
    execute_tool,
)


# --------------------------------------------------------------------------- #
# Fake OpenAI-compatible client
# --------------------------------------------------------------------------- #
def _tool_call(call_id: str, name: str, arguments: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _response(
    content: str | None = None,
    tool_calls: list | None = None,
    finish_reason: str | None = None,
):
    """Build a minimal chat.completions response object."""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice])


class FakeClient:
    """OpenAI-compatible client returning scripted responses.

    Records every ``create`` call so tests can assert whether (and with what
    payload) the model was invoked. If ``raise_with`` is set, the next call
    raises that exception to simulate an unavailable endpoint.
    """

    def __init__(self, responses: list | None = None, raise_with=None):
        self._responses = list(responses or [])
        self._raise_with = raise_with
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._raise_with is not None:
            raise self._raise_with
        if not self._responses:
            raise AssertionError("model was called more times than scripted")
        return self._responses.pop(0)


# --------------------------------------------------------------------------- #
# Shared base: isolated temp database + real storage backend
# --------------------------------------------------------------------------- #
class AssistantTestCase(unittest.TestCase):
    def setUp(self):
        # Mirror the Week 2 test convention: a fresh database per test, pointed
        # at by LOCAL_CONTEXT_DB_PATH so real storage writes land in temp only.
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

        # Real Week 2 storage functions, injected exactly as the CLI defaults do.
        from local_first_ai.storage import (  # local import keeps setup order clean
            create_context,
            manage_context,
            read_context,
            search_context,
        )

        self.storage = StorageBackend(
            create_context_item=create_context.create_context_item,
            search_context_items=search_context.search_context_items,
            get_context_item=read_context.get_context_item,
            list_context_items=read_context.list_context_items,
            update_context_item=manage_context.update_context_item,
            delete_context_item=manage_context.delete_context_item,
        )
        self.allow = lambda name, args: True
        self.deny = lambda name, args: False

    def tearDown(self):
        self.environment.stop()
        self.temporary_directory.cleanup()

    def seed(self, **fields) -> int:
        """Insert a row directly so tests stay independent of tool dispatch."""
        defaults = dict(
            context_type="user_note",
            title="Seeded note",
            content="We chose SQLite because it is local and works offline.",
            source="test",
            tags="sqlite,local",
            importance=3,
        )
        defaults.update(fields)
        with db_contract.database_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO context_items (
                    context_type, title, content, source, tags, importance,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    defaults["context_type"],
                    defaults["title"],
                    defaults["content"],
                    defaults["source"],
                    defaults["tags"],
                    defaults["importance"],
                    db_contract.utc_now(),
                    db_contract.utc_now(),
                ),
            )
            return int(cursor.lastrowid)

    def fetch(self, item_id: int) -> dict | None:
        with db_contract.database_connection() as connection:
            row = connection.execute(
                "SELECT * FROM context_items WHERE id = ?", (item_id,)
            ).fetchone()
        return db_contract.row_to_dict(row)

    def new_session(self, client=None, confirm=None, stream=None) -> ChatSession:
        config = Config(
            base_url="http://test.local/v1",
            model="test-model",
            api_key="test-key",
        )
        config.storage = self.storage
        if stream is not None:
            config.stream = stream
        return ChatSession(
            config,
            client=client,
            confirm=confirm if confirm is not None else self.allow,
            init_db=False,
        )


# --------------------------------------------------------------------------- #
# Model-first routing: every non-help/exit message reaches the model with
# tools; the model decides whether to call a read/write tool or just converse.
# --------------------------------------------------------------------------- #
class TestModelFirstRouting(AssistantTestCase):
    def test_greeting_reaches_model_without_calling_tools(self):
        client = FakeClient(responses=[_response(content="Hello! How can I help?")])
        session = self.new_session(client=client)

        answer = session.handle("Hi there, how are you?")

        self.assertEqual(answer, "Hello! How can I help?")
        # Small talk must reach the model but never invoke a tool.
        self.assertEqual(len(client.calls), 1)
        self.assertIsNone(client.calls[0]["messages"][-1].get("tool_calls"))
        self.assertEqual(len(self.storage.list_context_items()), 0)

    def test_listing_request_calls_list_tool(self):
        self.seed(title="One")
        self.seed(title="Two")
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[_tool_call("call_1", "list_context_items", "{}")]
                ),
                _response(content="You have 2 items stored."),
            ]
        )
        session = self.new_session(client=client)

        answer = session.handle("What items do I have stored?")

        self.assertEqual(answer, "You have 2 items stored.")
        self.assertEqual(len(client.calls), 2)
        # The model actually read the store before answering.
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        self.assertIn("Two", tool_messages[0]["content"])
        self.assertEqual(len(self.storage.list_context_items()), 2)

    def test_search_request_calls_search_tool(self):
        self.seed(content="SQLite is the local database we selected.")
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "search_context_items",
                            json.dumps({"keyword": "sqlite"}),
                        )
                    ]
                ),
                _response(content="You have a note about SQLite."),
            ]
        )
        session = self.new_session(client=client)

        answer = session.handle("Find notes about SQLite.")

        self.assertEqual(answer, "You have a note about SQLite.")
        # Model-first: the raw request reaches the model, not deterministic
        # evidence prepended by handle. (calls record a live message reference,
        # so find the user turn by role rather than by position.)
        user_turns = [
            m["content"]
            for m in client.calls[0]["messages"]
            if m.get("role") == "user"
        ]
        self.assertEqual(user_turns[-1], "Find notes about SQLite.")
        self.assertEqual(len(client.calls), 2)
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        self.assertIn("SQLite is the local database", tool_messages[0]["content"])

    def test_grounded_question_lets_model_search_then_answer(self):
        self.seed(
            context_type="config_decision",
            title="Database choice",
            content="We chose SQLite because it is local and works offline.",
        )
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "search_context_items",
                            json.dumps({"keyword": "sqlite"}),
                        )
                    ]
                ),
                _response(content="We picked SQLite for local-first use."),
            ]
        )
        session = self.new_session(client=client)

        answer = session.handle("What did we decide about SQLite?")

        self.assertEqual(answer, "We picked SQLite for local-first use.")
        # Model-first: the raw request reaches the model, not deterministic
        # evidence prepended by handle. (calls record a live message reference,
        # so find the user turn by role rather than by position.)
        user_turns = [
            m["content"]
            for m in client.calls[0]["messages"]
            if m.get("role") == "user"
        ]
        self.assertEqual(user_turns[-1], "What did we decide about SQLite?")
        # The model decided to read before answering, so two calls happen.
        self.assertEqual(len(client.calls), 2)
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertTrue(tool_messages)
        self.assertIn("We chose SQLite", tool_messages[0]["content"])
        # A grounded question must not mutate the store.
        self.assertEqual(len(self.storage.list_context_items()), 1)

    def test_empty_search_yields_no_relevant_context_from_model(self):
        self.seed(content="Unrelated note about the weather being sunny.")
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "search_context_items",
                            json.dumps({"keyword": "france"}),
                        )
                    ]
                ),
                _response(
                    content="I have no relevant local context about France."
                ),
            ]
        )
        session = self.new_session(client=client)

        result = session.handle("What is the capital of France?")

        self.assertIn("no relevant local context", result)
        # The model was reached (not short-circuited) and used a read tool.
        self.assertEqual(len(client.calls), 2)
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        # An empty search result carries no row content.
        self.assertIn('"count": 0', tool_messages[0]["content"])

    def test_required_read_is_repaired_once_when_auto_omits_tool(self):
        self.seed(title="Stored item")
        client = FakeClient(
            responses=[
                _response(content="I cannot access that."),
                _response(
                    tool_calls=[_tool_call("repair", "list_context_items", "{}")]
                ),
                _response(content="You have one stored item."),
            ]
        )
        session = self.new_session(client=client, stream=False)

        answer = session.handle("What is stored?")

        self.assertEqual(answer, "You have one stored item.")
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(client.calls[0]["tool_choice"], "auto")
        self.assertEqual(client.calls[1]["tool_choice"], "required")
        self.assertEqual(client.calls[2]["tool_choice"], "auto")
        self.assertEqual(len(self.storage.list_context_items()), 1)

    def test_required_write_is_repaired_once_without_duplicate_mutation(self):
        client = FakeClient(
            responses=[
                _response(content="I will remember that."),
                _response(
                    tool_calls=[
                        _tool_call(
                            "repair",
                            "create_context_item",
                            json.dumps(
                                {
                                    "context_type": "user_note",
                                    "title": "Offline choice",
                                    "content": "Use SQLite.",
                                }
                            ),
                        )
                    ]
                ),
                _response(content="Remembered."),
            ]
        )
        session = self.new_session(client=client, confirm=self.allow, stream=False)

        answer = session.handle("Remember that we use SQLite.")

        self.assertEqual(answer, "Remembered.")
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(client.calls[1]["tool_choice"], "required")
        self.assertEqual(len(self.storage.list_context_items()), 1)

    def test_required_tool_repair_fails_closed_for_missing_or_wrong_family(self):
        for response in (
            _response(content="No tool."),
            _response(
                tool_calls=[
                    _tool_call(
                        "wrong",
                        "create_context_item",
                        json.dumps(
                            {
                                "context_type": "user_note",
                                "title": "Wrong",
                                "content": "Must not persist.",
                            }
                        ),
                    )
                ]
            ),
        ):
            with self.subTest(response=response):
                client = FakeClient(
                    responses=[_response(content="Skipped."), response]
                )
                messages = [
                    {"role": "system", "content": assistant.SYSTEM_PROMPT},
                    {"role": "user", "content": "What is stored?"},
                ]

                final, error = assistant.run_assistant_turn(
                    client,
                    "test-model",
                    messages,
                    self.storage,
                    self.allow,
                    stream=False,
                )

                self.assertIsNone(final)
                self.assertIsInstance(error, RuntimeError)
                self.assertEqual(len(client.calls), 2)
                self.assertEqual(len(self.storage.list_context_items()), 0)

    def test_final_answer_after_tool_execution_is_not_repaired(self):
        self.seed(title="Stored item")
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[_tool_call("read", "list_context_items", "{}")]
                ),
                _response(content="There is one item."),
            ]
        )
        session = self.new_session(client=client, stream=False)

        answer = session.handle("List stored items.")

        self.assertEqual(answer, "There is one item.")
        self.assertEqual(len(client.calls), 2)
        self.assertTrue(all(call["tool_choice"] == "auto" for call in client.calls))

    def test_greeting_and_unrelated_save_phrase_remain_auto_only(self):
        for prompt in ("Hello there.", "Save me a seat for tomorrow."):
            with self.subTest(prompt=prompt):
                client = FakeClient(responses=[_response(content="Okay.")])
                session = self.new_session(client=client, stream=False)

                self.assertEqual(session.handle(prompt), "Okay.")
                self.assertEqual(len(client.calls), 1)
                self.assertEqual(client.calls[0]["tool_choice"], "auto")

    def test_explicit_local_note_queries_repair_read_once(self):
        prompts = (
            "Find notes about SQLite.",
            "What do you know locally about SQLite?",
            "What did we decide about SQLite?",
            "What local context do we have about SQLite?",
        )
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                client = FakeClient(
                    responses=[
                        _response(content="I do not know."),
                        _response(
                            tool_calls=[
                                _tool_call("repair", "search_context_items", '{"keyword":"sqlite"}')
                            ]
                        ),
                        _response(content="SQLite is in local context."),
                    ]
                )
                session = self.new_session(client=client, stream=False)

                self.assertEqual(
                    session.handle(prompt), "SQLite is in local context."
                )
                self.assertEqual(len(client.calls), 3)
                self.assertEqual(client.calls[1]["tool_choice"], "required")

    def test_retail_store_question_remains_auto_only(self):
        client = FakeClient(responses=[_response(content="A retail answer.")])
        session = self.new_session(client=client, stream=False)

        self.assertEqual(session.handle("What store sells shoes?"), "A retail answer.")
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["tool_choice"], "auto")


# --------------------------------------------------------------------------- #
# 3. CRUD through the public execute_tool entry point
# --------------------------------------------------------------------------- #
class TestCrudThroughExecuteTool(AssistantTestCase):
    def test_create_persists_row_and_returns_id(self):
        payload = json.dumps(
            {
                "context_type": "project_note",
                "title": "Roadmap",
                "content": "Ship offline mode first.",
                "tags": "plan",
                "importance": 4,
            }
        )
        result = json.loads(execute_tool("create_context_item", payload, self.storage, self.allow))

        self.assertEqual(result["status"], "created")
        self.assertIsInstance(result["id"], int)
        stored = self.fetch(result["id"])
        self.assertIsNotNone(stored)
        self.assertEqual(stored["title"], "Roadmap")
        self.assertEqual(stored["importance"], 4)

    def test_search_returns_matching_rows(self):
        self.seed(content="SQLite is the local database we selected.")
        self.seed(content="The weather is rainy today.", title="Weather")
        result = json.loads(
            execute_tool(
                "search_context_items",
                json.dumps({"keyword": "sqlite"}),
                self.storage,
                self.allow,
            )
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["content"], "SQLite is the local database we selected.")

    def test_read_returns_item_by_id_and_none_for_missing(self):
        item_id = self.seed(title="Readable")
        found = json.loads(
            execute_tool(
                "get_context_item",
                json.dumps({"item_id": item_id}),
                self.storage,
                self.allow,
            )
        )
        missing = json.loads(
            execute_tool(
                "get_context_item",
                json.dumps({"item_id": 999999}),
                self.storage,
                self.allow,
            )
        )
        self.assertTrue(found["found"])
        self.assertEqual(found["item"]["id"], item_id)
        self.assertFalse(missing["found"])

    def test_list_returns_all_items(self):
        self.seed(title="One")
        self.seed(title="Two")
        result = json.loads(
            execute_tool("list_context_items", "{}", self.storage, self.allow)
        )
        self.assertEqual(result["count"], 2)

    def test_update_changes_only_requested_fields(self):
        item_id = self.seed(title="Old title", content="Old content", importance=1)
        result = json.loads(
            execute_tool(
                "update_context_item",
                json.dumps({"item_id": item_id, "title": "New title", "importance": 5}),
                self.storage,
                self.allow,
            )
        )
        self.assertEqual(result["status"], "updated")
        stored = self.fetch(item_id)
        self.assertEqual(stored["title"], "New title")
        self.assertEqual(stored["content"], "Old content")
        self.assertEqual(stored["importance"], 5)

    def test_delete_removes_row(self):
        item_id = self.seed(title="Doomed")
        result = json.loads(
            execute_tool(
                "delete_context_item",
                json.dumps({"item_id": item_id}),
                self.storage,
                self.allow,
            )
        )
        self.assertEqual(result["status"], "deleted")
        self.assertIsNone(self.fetch(item_id))


# --------------------------------------------------------------------------- #
# 4. Confirmation allow / deny for mutating tools
# --------------------------------------------------------------------------- #
class TestConfirmation(AssistantTestCase):
    def test_write_tool_denied_never_mutates_store(self):
        for name, payload, changed_check in (
            (
                "create_context_item",
                json.dumps(
                    {
                        "context_type": "user_note",
                        "title": "Should not exist",
                        "content": "blocked",
                    }
                ),
                lambda: len(self.storage.list_context_items()) == 0,
            ),
            (
                "update_context_item",
                json.dumps({"item_id": 1, "title": "Hacked"}),
                lambda: True,  # no row exists yet; nothing to change
            ),
            (
                "delete_context_item",
                json.dumps({"item_id": 1}),
                lambda: True,
            ),
        ):
            with self.subTest(tool=name):
                result = json.loads(
                    execute_tool(name, payload, self.storage, self.deny)
                                )
                self.assertEqual(result["status"], "cancelled")
                self.assertEqual(
                    result["reason"], "user declined confirmation"
                )
                self.assertTrue(changed_check())
        self.assertEqual(len(self.storage.list_context_items()), 0)

    def test_write_tool_allowed_mutates_store(self):
        payload = json.dumps(
            {
                "context_type": "user_note",
                "title": "Allowed",
                "content": "confirmed",
            }
        )
        result = json.loads(
            execute_tool("create_context_item", payload, self.storage, self.allow)
        )
        self.assertEqual(result["status"], "created")
        self.assertIsNotNone(self.fetch(result["id"]))

    def test_session_create_allowed_via_model_writes_row(self):
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "create_context_item",
                            json.dumps(
                                {
                                    "context_type": "user_note",
                                    "title": "From model",
                                    "content": "created through the loop",
                                }
                            ),
                        )
                    ]
                ),
                _response(content="Created it for you."),
            ]
        )
        session = self.new_session(client=client, confirm=self.allow)

        answer = session.handle("Create a user_note titled From model about stuff.")

        self.assertEqual(answer, "Created it for you.")
        items = self.storage.list_context_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "From model")

    def test_session_create_denied_via_model_does_not_write(self):
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "create_context_item",
                            json.dumps(
                                {
                                    "context_type": "user_note",
                                    "title": "Blocked",
                                    "content": "should not persist",
                                }
                            ),
                        )
                    ]
                ),
                _response(content="Understood, I will not create it."),
            ]
        )
        session = self.new_session(client=client, confirm=self.deny)

        answer = session.handle("Create a user_note titled Blocked about stuff.")

        self.assertEqual(answer, "Understood, I will not create it.")
        self.assertEqual(len(self.storage.list_context_items()), 0)

    def test_remember_request_reaches_model_and_creates_note(self):
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "create_context_item",
                            json.dumps(
                                {
                                    "context_type": "user_note",
                                    "title": "Local model server",
                                    "content": (
                                        "My local model server uses vmlx on port 8080."
                                    ),
                                }
                            ),
                        )
                    ]
                ),
                _response(content="Saved it."),
            ]
        )
        session = self.new_session(client=client, confirm=self.allow)

        answer = session.handle(
            "Remember that my local model server uses vmlx on port 8080."
        )

        self.assertEqual(answer, "Saved it.")
        self.assertEqual(len(client.calls), 2)
        items = self.storage.list_context_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Local model server")


# --------------------------------------------------------------------------- #
# 5. Malformed / unknown tool calls
# --------------------------------------------------------------------------- #
class TestMalformedAndUnknownTools(AssistantTestCase):
    def test_unknown_tool_returns_error(self):
        result = json.loads(
            execute_tool("frobnicate", "{}", self.storage, self.allow)
        )
        self.assertIn("error", result)
        self.assertIn("Unknown tool", result["error"])

    def test_malformed_json_arguments_returns_error(self):
        result = json.loads(
            execute_tool("get_context_item", "{not valid json", self.storage, self.allow)
        )
        self.assertIn("error", result)
        self.assertIn("Invalid JSON", result["error"])

    def test_arguments_not_an_object_returns_error(self):
        result = json.loads(
            execute_tool("list_context_items", "[1,2,3]", self.storage, self.allow)
        )
        self.assertIn("error", result)
        self.assertIn("JSON object", result["error"])

    def test_invalid_args_returns_validation_error(self):
        result = json.loads(
            execute_tool(
                "create_context_item",
                json.dumps({"context_type": "bogus", "title": "x", "content": "y"}),
                self.storage,
                self.allow,
            )
        )
        self.assertIn("error", result)
        self.assertIn("Invalid arguments", result["error"])

    def test_fractional_importance_is_rejected_instead_of_truncated(self):
        result = json.loads(
            execute_tool(
                "create_context_item",
                json.dumps(
                    {
                        "context_type": "user_note",
                        "title": "Fractional",
                        "content": "Must not be stored.",
                        "importance": 3.9,
                    }
                ),
                self.storage,
                self.allow,
            )
        )
        self.assertIn("error", result)
        self.assertEqual(len(self.storage.list_context_items()), 0)


# --------------------------------------------------------------------------- #
# 6. Model-unavailable fallback
# --------------------------------------------------------------------------- #
class TestModelUnavailable(AssistantTestCase):
    def test_no_client_with_operation_intent_reports_unavailable(self):
        session = self.new_session(client=None)
        result = session.handle("List all context items.")
        self.assertEqual(result, MODEL_UNAVAILABLE_MESSAGE)

    def test_model_error_during_turn_reports_unavailable_and_no_write(self):
        client = FakeClient(raise_with=RuntimeError("endpoint down"))
        session = self.new_session(client=client, confirm=self.allow)
        result = session.handle("Create a user_note titled Lost about nothing.")
        self.assertEqual(result, MODEL_UNAVAILABLE_MESSAGE)
        # The failing model call must not leave a partial write behind.
        self.assertEqual(len(self.storage.list_context_items()), 0)

    def test_empty_model_choices_reports_unavailable(self):
        client = FakeClient(responses=[SimpleNamespace(choices=[])])
        session = self.new_session(client=client)
        result = session.handle("List all context items.")
        self.assertEqual(result, MODEL_UNAVAILABLE_MESSAGE)


class TestToolLoop(AssistantTestCase):
    def test_multiple_tool_iterations_reach_final_answer(self):
        item_id = self.seed(title="Loop note")
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "get_context_item",
                            json.dumps({"item_id": item_id}),
                        )
                    ]
                ),
                _response(
                    tool_calls=[
                        _tool_call("call_2", "list_context_items", "{}")
                    ]
                ),
                _response(content="Read one item and listed the store."),
            ]
        )
        session = self.new_session(client=client)

        answer = session.handle(f"Read item id {item_id}, then list all items.")

        self.assertEqual(answer, "Read one item and listed the store.")
        self.assertEqual(len(client.calls), 3)

    def test_parallel_read_tool_calls_are_all_returned(self):
        first_id = self.seed(title="First")
        second_id = self.seed(title="Second")
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call(
                            "call_1",
                            "get_context_item",
                            json.dumps({"item_id": first_id}),
                        ),
                        _tool_call(
                            "call_2",
                            "get_context_item",
                            json.dumps({"item_id": second_id}),
                        ),
                    ]
                ),
                _response(content="Read both items."),
            ]
        )
        session = self.new_session(client=client)

        answer = session.handle("Read id 1 and id 2.")

        self.assertEqual(answer, "Read both items.")
        second_request_messages = client.calls[1]["messages"]
        tool_messages = [
            message for message in second_request_messages if message["role"] == "tool"
        ]
        self.assertEqual(
            [message["tool_call_id"] for message in tool_messages],
            ["call_1", "call_2"],
        )

    def test_repeated_identical_write_is_confirmed_and_executed_once(self):
        arguments = json.dumps(
            {
                "context_type": "config_decision",
                "title": "Local Model Server Configuration",
                "content": "Local model server uses vmlx on port 8080.",
                "importance": 4,
            }
        )
        client = FakeClient(
            responses=[
                _response(
                    tool_calls=[
                        _tool_call("call_1", "create_context_item", arguments)
                    ]
                ),
                _response(
                    tool_calls=[
                        _tool_call("call_2", "create_context_item", arguments),
                        _tool_call("call_3", "list_context_items", "{}"),
                    ]
                ),
                _response(content="Saved it."),
            ]
        )
        confirmations: list[tuple[str, dict]] = []

        session = self.new_session(
            client=client,
            confirm=lambda name, args: confirmations.append((name, args)) or True,
        )
        answer = session.handle(
            "Remember that my local model server uses vmlx on port 8080."
        )

        self.assertEqual(answer, "Write already handled; duplicate request ignored.")
        self.assertEqual(len(confirmations), 1)
        self.assertEqual(len(self.storage.list_context_items()), 1)
        tool_call_ids = [
            message["tool_call_id"]
            for message in session.messages
            if message["role"] == "tool"
        ]
        self.assertEqual(tool_call_ids, ["call_1", "call_2", "call_3"])


# --------------------------------------------------------------------------- #
# 7. Default-on streaming: OpenAI Chat Completions stream accumulator + flow
# --------------------------------------------------------------------------- #
def _stream_chunk(content=None, tool_calls=None, finish_reason=None):
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(delta=delta, finish_reason=finish_reason, index=0)
    return SimpleNamespace(choices=[choice])


def _stream_tool_call(index, id=None, name=None, arguments=None, type=None):
    return SimpleNamespace(
        index=index,
        id=id,
        type=type,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _empty_choices_chunk():
    return SimpleNamespace(choices=[])


class FakeStreamClient:
    """OpenAI-compatible client that returns iterable chunk lists for stream=True
    and non-iterable responses for stream=False (the retry path)."""

    def __init__(
        self,
        stream_responses=None,
        non_stream_responses=None,
        raise_with=None,
        raise_stream_with=None,
    ):
        self._stream_responses = list(stream_responses or [])
        self._non_stream_responses = list(non_stream_responses or [])
        self._raise_with = raise_with
        self._raise_stream_with = raise_stream_with
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream") and self._raise_stream_with is not None:
            raise self._raise_stream_with
        if not kwargs.get("stream") and self._raise_with is not None:
            raise self._raise_with
        if kwargs.get("stream"):
            if not self._stream_responses:
                raise AssertionError("no stream response scripted")
            return self._stream_responses.pop(0)
        if not self._non_stream_responses:
            raise AssertionError("no non-stream response scripted")
        return self._non_stream_responses.pop(0)


class TestStreamConfig(AssistantTestCase):
    def test_config_stream_defaults_true(self):
        config = Config(
            base_url="http://test.local/v1",
            model="test-model",
            api_key="test-key",
        )
        self.assertTrue(config.stream)

    def test_stream_from_env_respects_disable_values(self):
        for disabled in ("false", "0", "no", "off", "FALSE", "No"):
            with self.subTest(value=disabled):
                with patch.dict(os.environ, {"ASSISTANT_STREAM": disabled}):
                    self.assertFalse(assistant._stream_from_env())
        with patch.dict(os.environ):
            os.environ.pop("ASSISTANT_STREAM", None)
            self.assertTrue(assistant._stream_from_env())


class TestStreamAccumulator(unittest.TestCase):
    def test_skips_empty_choices_and_collects_content(self):
        chunks = [
            _empty_choices_chunk(),
            _stream_chunk(content="Hello "),
            _stream_chunk(content="world"),
            _stream_chunk(content=None, finish_reason="stop"),
        ]
        parts, calls, fr, err, leaked, emitted = assistant._accumulate_stream(chunks)
        self.assertEqual(parts, "Hello world")
        self.assertEqual(fr, "stop")
        self.assertEqual(calls, [])
        self.assertFalse(leaked)
        self.assertFalse(emitted)

    def test_fragments_tool_args_by_index(self):
        chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(0, id="call_1", name="get_context_item")
                ]
            ),
            _stream_chunk(tool_calls=[_stream_tool_call(0, arguments='{"item_id": ')]),
            _stream_chunk(tool_calls=[_stream_tool_call(0, arguments="1}")]),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        parts, calls, fr, err, leaked, emitted = assistant._accumulate_stream(chunks)
        self.assertEqual(fr, "tool_calls")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["id"], "call_1")
        self.assertEqual(calls[0]["function"]["name"], "get_context_item")
        self.assertEqual(calls[0]["function"]["arguments"], '{"item_id": 1}')

    def test_multiple_indexed_calls_preserved_in_order(self):
        chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(0, id="c1", name="search_context_items",
                                      arguments='{"keyword":"a"}'),
                    _stream_tool_call(1, id="c2", name="list_context_items",
                                      arguments="{}"),
                ]
            ),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        parts, calls, fr, err, leaked, emitted = assistant._accumulate_stream(chunks)
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            [c["function"]["name"] for c in calls],
            ["search_context_items", "list_context_items"],
        )
        self.assertEqual(calls[0]["function"]["arguments"], '{"keyword":"a"}')

    def test_whole_tool_call_delivered_at_finish(self):
        arguments = json.dumps(
            {"context_type": "user_note", "title": "X", "content": "Y"}
        )
        chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(0, id="c1", name="create_context_item",
                                      arguments=arguments)
                ]
            ),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        parts, calls, fr, err, leaked, emitted = assistant._accumulate_stream(chunks)
        self.assertEqual(fr, "tool_calls")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["function"]["arguments"], arguments)

    def test_incomplete_stream_has_no_finish_reason(self):
        chunks = [
            _stream_chunk(tool_calls=[_stream_tool_call(0, name="list_context_items",
                                                        arguments="{}")]),
        ]
        parts, calls, fr, err, leaked, emitted = assistant._accumulate_stream(chunks)
        self.assertIsNone(fr)
        self.assertEqual(len(calls), 1)

    def test_fragmented_marker_bytes_are_never_emitted(self):
        # A marker split across two chunks must be held back in full; the
        # preceding normal text may stream but the marker itself must not.
        chunks = [
            _stream_chunk(content="before <tool"),
            _stream_chunk(content="_call> leaked"),
            _stream_chunk(finish_reason="stop"),
        ]
        emitted: list[str] = []
        parts, calls, fr, err, leaked, was_emitted = assistant._accumulate_stream(
            chunks, on_token=emitted.append
        )
        self.assertTrue(leaked)
        joined = "".join(emitted)
        self.assertNotIn("<tool_call>", joined)
        self.assertTrue(joined.startswith("before "))
        self.assertTrue(was_emitted)


class TestStreamingTurns(AssistantTestCase):
    def test_required_stream_recovery_discards_ungrounded_first_text(self):
        self.seed(title="Stored item")
        first_chunks = [
            _stream_chunk(content="Ungrounded first answer."),
            _stream_chunk(finish_reason="stop"),
        ]
        repaired = _response(
            tool_calls=[_tool_call("repair", "list_context_items", "{}")]
        )
        final_chunks = [
            _stream_chunk(content="Grounded answer."),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(
            stream_responses=[first_chunks, final_chunks],
            non_stream_responses=[repaired],
        )
        session = self.new_session(client=client, stream=True)
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            answer = session.handle("What is stored?")

        self.assertEqual(answer, "Grounded answer.")
        self.assertEqual(output.getvalue(), "assistant> Grounded answer.\n")
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(client.calls[0]["tool_choice"], "auto")
        self.assertEqual(client.calls[1]["tool_choice"], "required")
        self.assertEqual(client.calls[1]["stream"], False)
        self.assertEqual(client.calls[2]["tool_choice"], "auto")

    def test_visible_answer_with_stop_finish_tool_is_returned_once(self):
        chunks = [
            _stream_chunk(content="The store has one item."),
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(
                        0,
                        id="call_1",
                        name="list_context_items",
                        arguments="{}",
                    )
                ]
            ),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[chunks])
        session = self.new_session(client=client, stream=True)
        buf = io.StringIO()

        with contextlib.redirect_stdout(buf):
            answer = session.handle("List items.")

        self.assertEqual(answer, "The store has one item.")
        self.assertEqual(buf.getvalue(), "assistant> The store has one item.\n")
        self.assertEqual(len(client.calls), 1)

    def test_non_stream_visible_answer_with_stop_finish_tool_is_returned_once(self):
        client = FakeStreamClient(
            non_stream_responses=[
                _response(
                    content="The store has one item.",
                    tool_calls=[_tool_call("call_1", "list_context_items", "{}")],
                    finish_reason="stop",
                )
            ]
        )
        session = self.new_session(client=client, stream=False)

        answer = session.handle("List items.")

        self.assertEqual(answer, "The store has one item.")
        self.assertEqual(len(client.calls), 1)

    def test_streamed_tool_call_with_stop_finish_executes_once(self):
        arguments = json.dumps(
            {
                "context_type": "user_note",
                "title": "Stop finish call",
                "content": "Tool calls are authoritative.",
            }
        )
        tool_chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(
                        0,
                        id="call_1",
                        name="create_context_item",
                        arguments=arguments,
                    )
                ]
            ),
            _stream_chunk(finish_reason="stop"),
        ]
        answer_chunks = [
            _stream_chunk(content="Created."),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[tool_chunks, answer_chunks])
        session = self.new_session(client=client, confirm=self.allow, stream=True)

        answer = session.handle("Remember this.")

        self.assertEqual(answer, "Created.")
        items = self.storage.list_context_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Stop finish call")
        self.assertEqual(len(client.calls), 2)
        self.assertTrue(all(call["stream"] for call in client.calls))

    def test_non_stream_tool_call_with_stop_finish_executes_once(self):
        arguments = json.dumps(
            {
                "context_type": "user_note",
                "title": "Non-stream stop finish call",
                "content": "Non-stream matches stream behavior.",
            }
        )
        client = FakeStreamClient(
            non_stream_responses=[
                _response(
                    tool_calls=[
                        _tool_call("call_1", "create_context_item", arguments)
                    ],
                    finish_reason="stop",
                ),
                _response(content="Created.", finish_reason="stop"),
            ]
        )
        session = self.new_session(client=client, confirm=self.allow, stream=False)

        answer = session.handle("Remember this.")

        self.assertEqual(answer, "Created.")
        items = self.storage.list_context_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Non-stream stop finish call")
        self.assertEqual(len(client.calls), 2)

    def test_streamed_text_printed_incrementally_and_final_matches(self):
        chunks = [
            _stream_chunk(content="Hello "),
            _stream_chunk(content="there"),
            _stream_chunk(content="!"),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[chunks])
        session = self.new_session(client=client, stream=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            answer = session.handle("Hi there.")
        out = buf.getvalue()
        self.assertEqual(answer, "Hello there!")
        # Prefix printed exactly once; tokens flushed; single trailing newline.
        self.assertEqual(out.count("assistant> "), 1)
        self.assertEqual(out, "assistant> Hello there!\n")
        # Only one model call for a plain chat turn.
        self.assertEqual(len(client.calls), 1)
        self.assertTrue(client.calls[0]["stream"])

    def test_streamed_tool_call_executes_after_completion(self):
        self.seed(title="One")
        tool_chunks = [
            _stream_chunk(
                tool_calls=[_stream_tool_call(0, id="call_1",
                                              name="list_context_items",
                                              arguments="{}")]
            ),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        answer_chunks = [
            _stream_chunk(content="You have 1 item."),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[tool_chunks, answer_chunks])
        session = self.new_session(client=client, stream=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            answer = session.handle("List items.")
        out = buf.getvalue()
        self.assertEqual(answer, "You have 1 item.")
        # Tool-call turn must not print prefix until the final content.
        self.assertEqual(out.count("assistant> "), 1)
        self.assertEqual(out, "assistant> You have 1 item.\n")
        self.assertEqual(len(client.calls), 2)
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        self.assertIn("One", tool_messages[0]["content"])

    def test_streamed_fragmented_write_executes_once_confirmed(self):
        arguments = json.dumps(
            {
                "context_type": "user_note",
                "title": "Streamed",
                "content": "from fragments",
            }
        )
        chunks = [
            _stream_chunk(
                tool_calls=[_stream_tool_call(0, id="call_1",
                                              name="create_context_item")]
            ),
            _stream_chunk(tool_calls=[_stream_tool_call(0, arguments=arguments[:12])]),
            _stream_chunk(tool_calls=[_stream_tool_call(0, arguments=arguments[12:])]),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        answer_chunks = [
            _stream_chunk(content="Created."),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[chunks, answer_chunks])
        session = self.new_session(client=client, confirm=self.allow, stream=True)
        answer = session.handle("Remember a streamed note.")
        self.assertEqual(answer, "Created.")
        items = self.storage.list_context_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Streamed")

    def test_streamed_multiple_indexed_calls_all_executed(self):
        first_id = self.seed(title="A")
        second_id = self.seed(title="B")
        chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(0, id="c1", name="get_context_item",
                                      arguments=json.dumps({"item_id": first_id})),
                    _stream_tool_call(1, id="c2", name="get_context_item",
                                      arguments=json.dumps({"item_id": second_id})),
                ]
            ),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        answer_chunks = [
            _stream_chunk(content="Read both."),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[chunks, answer_chunks])
        session = self.new_session(client=client, stream=True)
        answer = session.handle("Read both items.")
        self.assertEqual(answer, "Read both.")
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertEqual(
            [m["tool_call_id"] for m in tool_messages], ["c1", "c2"]
        )

    def test_incomplete_stream_retries_non_stream_before_any_write(self):
        # First stream shows a create tool call but never reaches finish_reason.
        incomplete_chunks = [
            _stream_chunk(
                tool_calls=[_stream_tool_call(0, id="call_1",
                                              name="create_context_item")]
            ),
            _stream_chunk(
                tool_calls=[_stream_tool_call(
                    0, arguments=json.dumps(
                        {"context_type": "user_note", "title": "X", "content": "Y"}
                    ))]
            ),
            # No finish_reason chunk -> incomplete.
        ]
        retry_response = _response(
            content="Sorry, the stream ended early; no write was performed."
        )
        client = FakeStreamClient(
            stream_responses=[incomplete_chunks],
            non_stream_responses=[retry_response],
        )
        session = self.new_session(client=client, confirm=self.allow, stream=True)
        answer = session.handle("Create X.")
        self.assertEqual(
            answer, "Sorry, the stream ended early; no write was performed."
        )
        # Safety: the partial tool call was never executed.
        self.assertEqual(len(self.storage.list_context_items()), 0)
        # Two model calls: the incomplete stream plus the non-stream retry.
        self.assertEqual(len(client.calls), 2)
        self.assertFalse(client.calls[1]["stream"])

    def test_leaked_tool_markup_retries_non_stream_without_printing(self):
        leak_chunks = [
            _stream_chunk(
                content='<tool_call> search_context_items {"keyword":"x"} </tool_call>'
            ),
            _stream_chunk(finish_reason="stop"),
        ]
        clean_response = _response(content="I have no relevant local context.")
        client = FakeStreamClient(
            stream_responses=[leak_chunks],
            non_stream_responses=[clean_response],
        )
        session = self.new_session(client=client, stream=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            answer = session.handle("What about x?")
        out = buf.getvalue()
        self.assertEqual(answer, "I have no relevant local context.")
        # The leaked raw markup must never reach the user.
        self.assertNotIn("<tool_call>", out)
        self.assertNotIn("search_context_items", out)
        self.assertEqual(out, "assistant> I have no relevant local context.\n")
        self.assertEqual(len(client.calls), 2)
        self.assertFalse(client.calls[1]["stream"])

    def test_streamed_malformed_tool_arguments_do_not_execute_write(self):
        chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(
                        0,
                        id="call_1",
                        name="create_context_item",
                        arguments='{ "context_type": "user_note", "title": ',
                    )
                ]
            ),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        answer_chunks = [
            _stream_chunk(content="No write happened."),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(stream_responses=[chunks, answer_chunks])
        session = self.new_session(client=client, confirm=self.allow, stream=True)

        answer = session.handle("Remember malformed payload.")

        self.assertEqual(answer, "No write happened.")
        self.assertEqual(len(self.storage.list_context_items()), 0)
        tool_messages = [
            m for m in client.calls[1]["messages"] if m.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        self.assertIn("Invalid JSON", tool_messages[0]["content"])

    def test_streamed_tool_call_without_id_returns_unavailable_without_write(self):
        chunks = [
            _stream_chunk(
                tool_calls=[
                    _stream_tool_call(
                        0,
                        name="create_context_item",
                        arguments=json.dumps(
                            {
                                "context_type": "user_note",
                                "title": "Missing id",
                                "content": "Must not write.",
                            }
                        ),
                    )
                ]
            ),
            _stream_chunk(finish_reason="tool_calls"),
        ]
        client = FakeStreamClient(stream_responses=[chunks])
        session = self.new_session(client=client, confirm=self.allow, stream=True)

        answer = session.handle("Remember missing id.")

        self.assertEqual(answer, MODEL_UNAVAILABLE_MESSAGE)
        self.assertEqual(len(self.storage.list_context_items()), 0)

    def test_midstream_exception_with_tool_call_does_not_execute_write(self):
        def broken_stream():
            yield _stream_chunk(
                tool_calls=[
                    _stream_tool_call(
                        0,
                        id="call_1",
                        name="create_context_item",
                        arguments=json.dumps(
                            {
                                "context_type": "user_note",
                                "title": "Partial",
                                "content": "Must not write.",
                            }
                        ),
                    )
                ]
            )
            raise RuntimeError("stream broke")

        client = FakeStreamClient(stream_responses=[broken_stream()])
        session = self.new_session(client=client, confirm=self.allow, stream=True)

        answer = session.handle("Remember partial stream.")

        self.assertEqual(answer, MODEL_UNAVAILABLE_MESSAGE)
        self.assertEqual(len(self.storage.list_context_items()), 0)
        self.assertEqual(len(client.calls), 1)


class TestStreamTimingAndFallback(AssistantTestCase):
    def test_on_token_fires_during_iteration_not_after(self):
        # A generator asserts the first token was emitted before the second
        # chunk is yielded, proving genuinely incremental streaming.
        events: list[tuple] = []

        def on_token(token):
            events.append(("token", token))

        def chunk_gen():
            yield _stream_chunk(content="A")
            # First token must have been emitted before this second chunk.
            self.assertIn(("token", "A"), events)
            events.append(("yielded_second", None))
            yield _stream_chunk(content="B")
            yield _stream_chunk(finish_reason="stop")

        client = FakeStreamClient(stream_responses=[chunk_gen()])
        final, error = assistant.run_assistant_turn(
            client,
            "m",
            [{"role": "user", "content": "hi"}],
            self.storage,
            self.allow,
            stream=True,
            on_token=on_token,
        )
        self.assertEqual(final, "AB")
        self.assertIsNone(error)
        self.assertEqual(events[0], ("token", "A"))
        self.assertEqual(events[1], ("yielded_second", None))
        self.assertEqual(events[2], ("token", "B"))

    def test_stream_request_error_retries_non_stream_once(self):
        client = FakeStreamClient(
            raise_stream_with=RuntimeError("stream endpoint down"),
            non_stream_responses=[_response(content="Recovered via non-stream.")],
        )
        session = self.new_session(client=client, stream=True)
        answer = session.handle("Hi.")
        self.assertEqual(answer, "Recovered via non-stream.")
        self.assertEqual(len(client.calls), 2)
        self.assertTrue(client.calls[0]["stream"])
        self.assertFalse(client.calls[1]["stream"])

    def test_incomplete_text_stream_does_not_duplicate_output(self):
        chunks = [
            _stream_chunk(content="Partial "),
            _stream_chunk(content="answer"),
            # No finish_reason chunk -> incomplete.
        ]
        client = FakeStreamClient(stream_responses=[chunks])
        session = self.new_session(client=client, stream=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            answer = session.handle("Tell me something.")
        out = buf.getvalue()
        # Error returned; the already-streamed text must not be duplicated.
        self.assertEqual(answer, MODEL_UNAVAILABLE_MESSAGE)
        self.assertEqual(out.count("Partial answer"), 1)
        self.assertIn(MODEL_UNAVAILABLE_MESSAGE, out)
        # No non-stream retry happened (visible text was already emitted).
        self.assertEqual(len(client.calls), 1)


class TestStreamDisable(AssistantTestCase):
    def test_non_stream_does_not_invoke_on_token(self):
        client = FakeClient(responses=[_response(content="Plain answer.")])
        emitted: list[str] = []
        final, error = assistant.run_assistant_turn(
            client,
            "m",
            [{"role": "user", "content": "hi"}],
            self.storage,
            self.allow,
            stream=False,
            on_token=emitted.append,
        )
        self.assertEqual(final, "Plain answer.")
        self.assertEqual(emitted, [])  # on_token unused in non-stream mode

    def test_no_stream_flag_disables_streaming(self):
        chunks = [
            _stream_chunk(content="streamed"),
            _stream_chunk(finish_reason="stop"),
        ]
        client = FakeStreamClient(
            stream_responses=[chunks],
            non_stream_responses=[_response(content="non-streamed")],
        )
        session = self.new_session(client=client, stream=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            answer = session.handle("Hi.")
        self.assertEqual(answer, "non-streamed")
        self.assertEqual(buf.getvalue(), "assistant> non-streamed\n")
        self.assertFalse(client.calls[0]["stream"])

    def test_parser_exposes_no_stream_and_help_reflects_default(self):
        parser = assistant.build_parser()
        args = parser.parse_args(["--no-stream"])
        self.assertTrue(args.no_stream)
        self.assertIn("streaming", parser.format_help())


class TestDotenvAndRuntimeConfig(unittest.TestCase):
    def test_load_dotenv_sets_missing_only_and_strips_quotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "OPENAI_BASE_URL=http://from-file/v1",
                        'OPENAI_MODEL="quoted-model"',
                        "OPENAI_API_KEY=file-key",
                        "EMPTY_SKIP=",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ):
                os.environ.pop("OPENAI_BASE_URL", None)
                os.environ.pop("OPENAI_API_KEY", None)
                os.environ.pop("EMPTY_SKIP", None)
                os.environ["OPENAI_MODEL"] = "shell-wins"
                loaded = assistant._load_dotenv(path)
                self.assertEqual(loaded, path)
                self.assertEqual(os.environ["OPENAI_BASE_URL"], "http://from-file/v1")
                self.assertEqual(os.environ["OPENAI_MODEL"], "shell-wins")
                self.assertEqual(os.environ["OPENAI_API_KEY"], "file-key")
                self.assertNotIn("EMPTY_SKIP", os.environ)

    def test_load_dotenv_missing_file_returns_none(self):
        missing = Path(tempfile.gettempdir()) / "no-such-assistant-env-file.env"
        self.assertIsNone(assistant._load_dotenv(missing))

    def test_resolve_runtime_config_requires_all_three(self):
        ns = SimpleNamespace(base_url=None, model="m", api_key="k")
        with self.assertRaises(SystemExit) as ctx:
            assistant.resolve_runtime_config(ns)
        message = str(ctx.exception)
        self.assertIn("OPENAI_BASE_URL", message)
        self.assertNotIn("OPENAI_MODEL (or --model)", message)

    def test_resolve_runtime_config_rejects_blank_strings(self):
        ns = SimpleNamespace(base_url="  ", model="", api_key="k")
        with self.assertRaises(SystemExit) as ctx:
            assistant.resolve_runtime_config(ns)
        message = str(ctx.exception)
        self.assertIn("OPENAI_BASE_URL", message)
        self.assertIn("OPENAI_MODEL", message)

    def test_resolve_runtime_config_builds_config(self):
        ns = SimpleNamespace(
            base_url=" http://test.local/v1 ",
            model=" test-model ",
            api_key=" test-key ",
        )
        config = assistant.resolve_runtime_config(ns, stream=False)
        self.assertEqual(config.base_url, "http://test.local/v1")
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.api_key, "test-key")
        self.assertFalse(config.stream)


if __name__ == "__main__":
    unittest.main(verbosity=2)
