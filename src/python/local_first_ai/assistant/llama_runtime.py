"""Install and run a llama.cpp local inference stack.

Downloads happen only when the executable or selected model is absent.
"""

from __future__ import annotations

import atexit
import json
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LLAMA_RELEASE_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
QWEN_MODEL = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
QWEN_MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/"
    + QWEN_MODEL
    + "?download=true"
)
MODEL_ALIAS = "qwen2.5-1.5b-instruct"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8004


class RuntimeSetupError(RuntimeError):
    """Raised when llama.cpp or Qwen cannot be prepared or started."""


@dataclass
class LlamaRuntime:
    base_url: str
    model: str
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


def default_runtime_dir() -> Path:
    override = os.getenv("LOCAL_FIRST_AI_RUNTIME_DIR")
    if override:
        return Path(override).expanduser()
    cache_root = os.getenv("XDG_CACHE_HOME")
    root = Path(cache_root).expanduser() if cache_root else Path.home() / ".cache"
    return root / "local-first-ai"


def find_llama_server(runtime_dir: Path) -> Path | None:
    """Prefer an existing system install, then the managed installation."""

    for command in ("llama-server", "llama-server.exe"):
        found = shutil.which(command)
        if found:
            return Path(found)
    names = ("llama-server.exe",) if os.name == "nt" else ("llama-server",)
    for name in names:
        matches = sorted((runtime_dir / "llama.cpp").rglob(name))
        if matches:
            return matches[0]
    return None


def _asset_tokens() -> tuple[str, str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "arm64" if machine in {"arm64", "aarch64"} else "x64"
    if system == "linux":
        return "ubuntu", arch, ".tar.gz"
    if system == "darwin":
        return "macos", arch, ".tar.gz"
    if system == "windows":
        return "win", arch, ".zip"
    raise RuntimeSetupError(f"No llama.cpp prebuilt release is supported for {system}/{machine}.")


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": "local-first-ai-assistant"})


def _download(url: str, destination: Path, label: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    print(f"Downloading {label}...")
    try:
        with urllib.request.urlopen(_request(url), timeout=60) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out)
        partial.replace(destination)
    except (OSError, urllib.error.URLError) as exc:
        partial.unlink(missing_ok=True)
        raise RuntimeSetupError(f"Could not download {label}: {exc}") from exc


def _safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                if not (root / member.filename).resolve().is_relative_to(root):
                    raise RuntimeSetupError("Unsafe path in llama.cpp release archive.")
            bundle.extractall(destination)
    else:
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle.getmembers():
                if not (root / member.name).resolve().is_relative_to(root):
                    raise RuntimeSetupError("Unsafe path in llama.cpp release archive.")
            bundle.extractall(destination, filter="data")


def install_llama_server(runtime_dir: Path) -> Path:
    """Download the latest official CPU release and return llama-server."""

    os_token, arch, suffix = _asset_tokens()
    try:
        with urllib.request.urlopen(_request(LLAMA_RELEASE_API), timeout=30) as response:
            release: dict[str, Any] = json.load(response)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        raise RuntimeSetupError(f"Could not check the latest llama.cpp release: {exc}") from exc

    assets = release.get("assets", [])
    candidates = []
    for asset in assets:
        name = str(asset.get("name", "")).lower()
        if (
            "bin" in name
            and os_token in name
            and arch in name
            and name.endswith(suffix)
            and not any(extra in name for extra in ("vulkan", "rocm", "sycl", "openvino", "cuda"))
        ):
            candidates.append(asset)
    if not candidates:
        raise RuntimeSetupError(f"The latest llama.cpp release has no CPU binary for {os_token}/{arch}.")

    asset = candidates[0]
    install_dir = runtime_dir / "llama.cpp"
    with tempfile.TemporaryDirectory(dir=runtime_dir) as temp_dir:
        archive = Path(temp_dir) / str(asset["name"])
        _download(str(asset["browser_download_url"]), archive, "llama.cpp")
        _safe_extract(archive, install_dir)

    server = find_llama_server(runtime_dir)
    if server is None:
        raise RuntimeSetupError("llama.cpp installed, but llama-server was not found.")
    server.chmod(server.stat().st_mode | stat.S_IXUSR)
    return server


def available_models(runtime_dir: Path) -> list[Path]:
    """Return managed GGUF files that can be selected without a download."""

    model_dir = runtime_dir / "models"
    if not model_dir.is_dir():
        return []
    return sorted(path for path in model_dir.rglob("*.gguf") if path.is_file())


def ensure_model(
    runtime_dir: Path,
    *,
    url: str = QWEN_MODEL_URL,
    filename: str = QWEN_MODEL,
) -> Path:
    model_path = runtime_dir / "models" / filename
    if not model_path.is_file() or model_path.stat().st_size == 0:
        _download(url, model_path, filename)
    return model_path


def _ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(_request(url + "/health"), timeout=2) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def prepare_llama_runtime(
    runtime_dir: Path | None = None,
    *,
    model_path: Path | None = None,
    model_alias: str | None = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = 120.0,
) -> LlamaRuntime:
    """Ensure llama.cpp exists, then serve the selected GGUF model."""

    root = (runtime_dir or default_runtime_dir()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    server = find_llama_server(root) or install_llama_server(root)
    model = model_path or ensure_model(root)
    if not model.is_file():
        raise RuntimeSetupError(f"Selected GGUF model does not exist: {model}")
    alias = model_alias or (MODEL_ALIAS if model.name == QWEN_MODEL else model.stem)
    endpoint = f"http://{host}:{port}"
    command = [
        str(server), "--model", str(model), "--alias", alias,
        "--host", host, "--port", str(port), "--ctx-size", "4096",
        "--parallel", "1", "--jinja",
    ]
    print(f"Starting llama.cpp with {alias}...")
    process = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    runtime = LlamaRuntime(base_url=endpoint + "/v1", model=alias, process=process)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeSetupError(
                f"llama-server exited with status {process.returncode} during startup."
            )
        if _ready(endpoint):
            atexit.register(runtime.stop)
            return runtime
        time.sleep(0.25)
    runtime.stop()
    raise RuntimeSetupError(f"llama-server did not become ready within {timeout:g} seconds.")
