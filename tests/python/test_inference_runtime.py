"""Offline tests for inference-engine and model selection."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src" / "python"))

from local_first_ai.assistant import inference_runtime as runtime  # noqa: E402


def answers(*values: str):
    iterator = iter(values)
    return lambda _prompt: next(iterator)


class TestInferenceSelection(unittest.TestCase):
    def test_engine_menu_dispatches_custom_endpoint(self):
        selected = runtime.prepare_inference_runtime(
            input_fn=answers("3", "http://localhost:9999/v1", "remote-model", "secret")
        )
        self.assertEqual(selected.engine, "custom")
        self.assertEqual(selected.base_url, "http://localhost:9999/v1")
        self.assertEqual(selected.model, "remote-model")
        self.assertEqual(selected.api_key, "secret")

    def test_llama_menu_lists_existing_gguf(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "models" / "local.gguf"
            model.parent.mkdir()
            model.write_bytes(b"gguf")
            selected = runtime.select_llama_model(root, input_fn=answers("1"))
            self.assertEqual(selected, model)

    def test_llama_custom_download_accepts_default_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(
                runtime.llama_runtime, "ensure_model", return_value=root / "other.gguf"
            ) as ensure:
                selected = runtime.select_llama_model(
                    root,
                    input_fn=answers("3", "https://models.test/other.gguf", ""),
                )
            self.assertEqual(selected, root / "other.gguf")
            ensure.assert_called_once_with(
                root, url="https://models.test/other.gguf", filename="other.gguf"
            )

    def test_ollama_reuses_installed_model(self):
        executable = Path("/usr/bin/ollama")
        with (
            patch.object(runtime, "ollama_models", return_value=["qwen:local"]),
            patch.object(runtime.subprocess, "run") as run,
        ):
            model = runtime.select_ollama_model(executable, input_fn=answers("1"))
        self.assertEqual(model, "qwen:local")
        run.assert_not_called()

    def test_ollama_pulls_requested_missing_model(self):
        executable = Path("/usr/bin/ollama")
        completed = MagicMock(returncode=0)
        with (
            patch.object(runtime, "ollama_models", return_value=[]),
            patch.object(runtime.subprocess, "run", return_value=completed) as run,
        ):
            model = runtime.select_ollama_model(
                executable, requested_model="gemma3:1b"
            )
        self.assertEqual(model, "gemma3:1b")
        run.assert_called_once_with(
            [str(executable), "pull", "gemma3:1b"], check=False
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
