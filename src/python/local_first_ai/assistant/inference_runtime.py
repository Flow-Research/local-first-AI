"""Interactive selection and preparation of local inference backends."""

from __future__ import annotations

import atexit
import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from local_first_ai.assistant import llama_runtime
from local_first_ai.assistant.llama_runtime import LlamaRuntime, RuntimeSetupError


OLLAMA_BASE_URL = "http://127.0.0.1:11434"
RECOMMENDED_OLLAMA_MODEL = "qwen2.5:1.5b"
Input = Callable[[str], str]


@dataclass
class InferenceRuntime:
    engine: str
    base_url: str
    model: str
    api_key: str = "not-needed"
    process: subprocess.Popen[bytes] | None = None

    def stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


def _choose(title: str, choices: list[str], input_fn: Input) -> int:
    print(title)
    for index, choice in enumerate(choices, 1):
        print(f"  {index}. {choice}")
    while True:
        try:
            value = input_fn("Choose a number: ").strip()
        except EOFError as exc:
            raise RuntimeSetupError("Interactive selection requires terminal input.") from exc
        if value.isdigit() and 1 <= int(value) <= len(choices):
            return int(value) - 1
        print(f"Enter a number from 1 to {len(choices)}.")


def _required(prompt: str, input_fn: Input) -> str:
    while True:
        try:
            value = input_fn(prompt).strip()
        except EOFError as exc:
            raise RuntimeSetupError("A required runtime setting was not provided.") from exc
        if value:
            return value
        print("A value is required.")


def _defaulted(prompt: str, default: str, input_fn: Input) -> str:
    try:
        return input_fn(f"{prompt} [{default}]: ").strip() or default
    except EOFError as exc:
        raise RuntimeSetupError("Interactive selection requires terminal input.") from exc


def select_llama_model(
    root: Path,
    *,
    requested_model: str | None = None,
    model_url: str | None = None,
    input_fn: Input = input,
) -> Path:
    if requested_model:
        candidate = Path(requested_model).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        managed = root / "models" / requested_model
        if managed.is_file():
            return managed
        if not model_url:
            raise RuntimeSetupError(
                "A llama.cpp model must be an existing GGUF path or include --model-url."
            )
        return llama_runtime.ensure_model(root, url=model_url, filename=requested_model)

    models = llama_runtime.available_models(root)
    choices = [f"Use local model: {path.name}" for path in models]
    choices.extend(
        [
            "Download recommended Qwen2.5 1.5B Q4_K_M",
            "Use an existing GGUF file by path",
            "Download another GGUF model from a URL",
        ]
    )
    selected = _choose("Select a llama.cpp model:", choices, input_fn)
    if selected < len(models):
        return models[selected]
    if selected == len(models):
        return llama_runtime.ensure_model(root)
    if selected == len(models) + 1:
        path = Path(_required("GGUF file path: ", input_fn)).expanduser().resolve()
        if not path.is_file():
            raise RuntimeSetupError(f"Selected GGUF model does not exist: {path}")
        return path
    url = _required("GGUF download URL: ", input_fn)
    parsed_name = Path(urllib.parse.urlparse(url).path).name
    filename = _defaulted("Local filename", parsed_name or "model.gguf", input_fn)
    if not filename.lower().endswith(".gguf"):
        filename += ".gguf"
    return llama_runtime.ensure_model(root, url=url, filename=filename)


def prepare_llama(
    runtime_dir: Path | None,
    *,
    requested_model: str | None,
    model_url: str | None,
    input_fn: Input,
) -> InferenceRuntime:
    root = (runtime_dir or llama_runtime.default_runtime_dir()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    # Installation is intentionally completed before presenting model choices.
    if llama_runtime.find_llama_server(root) is None:
        llama_runtime.install_llama_server(root)
    model_path = select_llama_model(
        root, requested_model=requested_model, model_url=model_url, input_fn=input_fn
    )
    runtime: LlamaRuntime = llama_runtime.prepare_llama_runtime(
        root, model_path=model_path, model_alias=model_path.stem
    )
    return InferenceRuntime(
        engine="llama", base_url=runtime.base_url, model=runtime.model,
        process=runtime.process,
    )


def find_ollama() -> Path | None:
    found = shutil.which("ollama") or shutil.which("ollama.exe")
    return Path(found) if found else None


def install_ollama() -> Path:
    """Run Ollama's official installer for the current operating system."""

    system = platform.system().lower()
    if system in {"linux", "darwin"}:
        url = "https://ollama.com/install.sh"
        suffix = ".sh"
        command_prefix = ["sh"]
    elif system == "windows":
        url = "https://ollama.com/install.ps1"
        suffix = ".ps1"
        command_prefix = ["powershell", "-ExecutionPolicy", "Bypass", "-File"]
    else:
        raise RuntimeSetupError(f"Automatic Ollama installation is unsupported on {system}.")

    print("Ollama was not found. Running the official Ollama installer...")
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as script:
            script_path = Path(script.name)
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "local-first-ai-assistant"}),
                timeout=60,
            ) as response:
                shutil.copyfileobj(response, script)
        result = subprocess.run(command_prefix + [str(script_path)], check=False)
    except (OSError, urllib.error.URLError) as exc:
        raise RuntimeSetupError(f"Could not install Ollama: {exc}") from exc
    finally:
        if "script_path" in locals():
            script_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeSetupError(f"The Ollama installer exited with status {result.returncode}.")
    executable = find_ollama()
    if executable is None:
        raise RuntimeSetupError("Ollama installed, but its executable is not on PATH.")
    return executable


def _ollama_ready() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_BASE_URL + "/api/tags", timeout=2) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def _start_ollama(executable: Path, timeout: float = 60.0) -> subprocess.Popen[bytes] | None:
    if _ollama_ready():
        return None
    process = subprocess.Popen(
        [str(executable), "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeSetupError(
                f"Ollama exited with status {process.returncode} during startup."
            )
        if _ollama_ready():
            return process
        time.sleep(0.25)
    process.terminate()
    raise RuntimeSetupError("Ollama did not become ready before the timeout.")


def ollama_models() -> list[str]:
    try:
        with urllib.request.urlopen(OLLAMA_BASE_URL + "/api/tags", timeout=5) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise RuntimeSetupError(f"Could not list Ollama models: {exc}") from exc
    return sorted(
        str(item["name"]) for item in payload.get("models", []) if item.get("name")
    )


def select_ollama_model(
    executable: Path,
    *,
    requested_model: str | None = None,
    input_fn: Input = input,
) -> str:
    installed = ollama_models()
    if requested_model:
        selected = requested_model
    else:
        choices = [f"Use installed model: {name}" for name in installed]
        choices.extend(
            [
                f"Download recommended model: {RECOMMENDED_OLLAMA_MODEL}",
                "Download another model by name",
            ]
        )
        index = _choose("Select an Ollama model:", choices, input_fn)
        if index < len(installed):
            return installed[index]
        selected = (
            RECOMMENDED_OLLAMA_MODEL
            if index == len(installed)
            else _required("Ollama model name: ", input_fn)
        )
    if selected not in installed:
        print(f"Downloading Ollama model {selected}...")
        result = subprocess.run([str(executable), "pull", selected], check=False)
        if result.returncode != 0:
            raise RuntimeSetupError(
                f"Ollama could not download {selected} (status {result.returncode})."
            )
    return selected


def prepare_ollama(
    *, requested_model: str | None, input_fn: Input
) -> InferenceRuntime:
    executable = find_ollama() or install_ollama()
    process = _start_ollama(executable)
    try:
        model = select_ollama_model(
            executable, requested_model=requested_model, input_fn=input_fn
        )
    except Exception:
        if process is not None:
            process.terminate()
        raise
    runtime = InferenceRuntime(
        engine="ollama", base_url=OLLAMA_BASE_URL + "/v1", model=model,
        process=process,
    )
    if process is not None:
        atexit.register(runtime.stop)
    return runtime


def prepare_custom(
    *, base_url: str | None, model: str | None, api_key: str | None,
    input_fn: Input,
) -> InferenceRuntime:
    endpoint = (base_url or _required("OpenAI-compatible base URL: ", input_fn)).rstrip("/")
    selected_model = model or _required("Model name: ", input_fn)
    key = api_key
    if key is None:
        try:
            key = input_fn("API key [not-needed]: ").strip() or "not-needed"
        except EOFError:
            key = "not-needed"
    return InferenceRuntime(
        engine="custom", base_url=endpoint, model=selected_model, api_key=key
    )


def prepare_inference_runtime(
    *,
    engine: str | None = None,
    runtime_dir: Path | None = None,
    model: str | None = None,
    model_url: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    input_fn: Input = input,
) -> InferenceRuntime:
    selected = engine
    if selected is None:
        selected = ("llama", "ollama", "custom")[_choose(
            "Select an inference engine:",
            ["llama.cpp", "Ollama", "Other OpenAI-compatible endpoint"],
            input_fn,
        )]
    if selected == "llama":
        return prepare_llama(
            runtime_dir, requested_model=model, model_url=model_url,
            input_fn=input_fn,
        )
    if selected == "ollama":
        return prepare_ollama(requested_model=model, input_fn=input_fn)
    if selected == "custom":
        return prepare_custom(
            base_url=base_url, model=model, api_key=api_key, input_fn=input_fn
        )
    raise RuntimeSetupError(f"Unknown inference engine: {selected}")
