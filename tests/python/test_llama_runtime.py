"""Offline tests for llama.cpp/Qwen discovery and lifecycle."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src" / "python"))

from local_first_ai.assistant import llama_runtime  # noqa: E402


class TestLlamaRuntime(unittest.TestCase):
    def test_find_server_prefers_path(self):
        with patch.object(llama_runtime.shutil, "which", return_value="/usr/bin/llama-server"):
            self.assertEqual(
                llama_runtime.find_llama_server(Path("/unused")),
                Path("/usr/bin/llama-server"),
            )

    def test_ensure_model_reuses_nonempty_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "models" / llama_runtime.QWEN_MODEL
            model.parent.mkdir()
            model.write_bytes(b"gguf")
            with patch.object(llama_runtime, "_download") as download:
                self.assertEqual(llama_runtime.ensure_model(root), model)
                download.assert_not_called()

    def test_prepare_starts_fixed_qwen_model_and_endpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server = root / "llama-server"
            model = root / llama_runtime.QWEN_MODEL
            model.write_bytes(b"gguf")
            process = MagicMock()
            process.poll.return_value = None
            with (
                patch.object(llama_runtime, "find_llama_server", return_value=server),
                patch.object(llama_runtime, "ensure_model", return_value=model),
                patch.object(llama_runtime.subprocess, "Popen", return_value=process) as popen,
                patch.object(llama_runtime, "_ready", return_value=True),
                patch.object(llama_runtime.atexit, "register"),
            ):
                runtime = llama_runtime.prepare_llama_runtime(root, port=8123)

            self.assertEqual(runtime.base_url, "http://127.0.0.1:8123/v1")
            self.assertEqual(runtime.model, llama_runtime.MODEL_ALIAS)
            command = popen.call_args.args[0]
            self.assertEqual(command[command.index("--model") + 1], str(model))
            self.assertEqual(command[command.index("--alias") + 1], llama_runtime.MODEL_ALIAS)

    def test_runtime_dir_honors_environment(self):
        with patch.dict(os.environ, {"LOCAL_FIRST_AI_RUNTIME_DIR": "/tmp/custom-runtime"}):
            self.assertEqual(
                llama_runtime.default_runtime_dir(), Path("/tmp/custom-runtime")
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
