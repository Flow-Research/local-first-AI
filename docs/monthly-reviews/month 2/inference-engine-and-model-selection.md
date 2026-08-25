# Month 2 Review: Inference Engine and Model Selection

## Summary

The assistant was changed from a client that depended on manually configured
`OPENAI_BASE_URL`, `OPENAI_MODEL`, and `OPENAI_API_KEY` values into a startup
flow that can select and prepare an inference backend. A user can now choose:

1. **llama.cpp** for a locally managed GGUF model.
2. **Ollama** for a model managed through the Ollama service.
3. **Other** for a user-managed OpenAI-compatible endpoint.

After the engine is selected, the application discovers available models,
offers an existing model when possible, and provides an appropriate download
path when a new model is needed. Every engine produces the same small runtime
contract—base URL, model name, API key, and optional child process—so the
existing assistant and tool-calling code does not need to know which engine is
serving the model.

This work was introduced in commit
`34240deb37fb4b07eb2d7bfcf82ffad839fd3662` on
`feature/month-02-week-03-llama-cpp-qwen-endpoint`.

## Motivation

Previously, users had to start a compatible model server themselves and place
all three connection values in `.env`. That design kept the assistant client
simple, but setup differed between machines and the project could not help when
an engine or model was missing.

The new design keeps the assistant protocol stable while moving environment
discovery, installation, model selection, server startup, and cleanup into
dedicated runtime modules.

## Architecture

The implementation is divided into three layers:

```text
Command-line entry point (app.py)
        |
        | engine/model/endpoint options
        v
Runtime selector (inference_runtime.py)
        |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
  llama.cpp path       Ollama path        Custom endpoint
        |                   |                   |
        v                   v                   |
llama_runtime.py      Ollama CLI/API             |
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
                  InferenceRuntime contract
             base_url + model + api_key + process
                            |
                            v
                    Config -> OpenAI client
                            |
                            v
                  Existing ChatSession/tool loop
```

The important boundary is the `InferenceRuntime` object. Everything below it
is engine-specific; everything above it continues to use the common
OpenAI-compatible Chat Completions interface.

## Files Added and Changed

### `inference_runtime.py`

[`inference_runtime.py`](../../../src/python/local_first_ai/assistant/inference_runtime.py)
coordinates interactive selection and contains the Ollama and custom-endpoint
implementations.

Its `InferenceRuntime` dataclass contains:

- `engine`: the selected engine identifier.
- `base_url`: the OpenAI-compatible endpoint used by the client.
- `model`: the model identifier sent with completion requests.
- `api_key`: a real key for authenticated custom endpoints or `not-needed` for
  local engines.
- `process`: an optional server process started by this application.

The `stop()` method terminates only a process owned by the application. An
already-running Ollama service or a custom endpoint is not stopped.

Reference: [`InferenceRuntime`](../../../src/python/local_first_ai/assistant/inference_runtime.py#L29)

### `llama_runtime.py`

[`llama_runtime.py`](../../../src/python/local_first_ai/assistant/llama_runtime.py)
owns llama.cpp-specific discovery, installation, GGUF downloads, extraction,
server startup, readiness checks, and shutdown.

### `app.py`

[`app.py`](../../../src/python/local_first_ai/assistant/app.py) now exposes the
selection inputs as command-line flags and passes them to the runtime selector.
It converts the returned runtime into the existing `Config` object before
creating the OpenAI client and `ChatSession`.

### Configuration and documentation

The [environment example](../../../src/python/local_first_ai/assistant/.env.example)
documents optional non-interactive values. The assistant
[README](../../../src/python/local_first_ai/assistant/README.md) explains the
interactive and scripted startup paths.

## Startup Selection Flow

`prepare_inference_runtime()` is the public dispatcher. If `--engine` or
`LOCAL_FIRST_AI_ENGINE` supplied a value, it uses that value directly. If not,
it prints an interactive menu for llama.cpp, Ollama, or another endpoint.

The dispatcher then forwards only the settings relevant to the selected
engine:

- llama.cpp receives the runtime directory, model path/name, and optional
  model URL.
- Ollama receives the optional model name.
- A custom endpoint receives its URL, model name, and API key.

Reference: [`prepare_inference_runtime()`](../../../src/python/local_first_ai/assistant/inference_runtime.py#L306)

The `_choose()` and `_required()` helpers keep interactive input validation in
one place. Invalid menu numbers are rejected and required values cannot be
blank.

Reference: [interactive helpers](../../../src/python/local_first_ai/assistant/inference_runtime.py#L48)

## llama.cpp Connection

### Engine discovery and installation

`find_llama_server()` first checks the operating system `PATH` for an existing
`llama-server`. It then searches the managed runtime directory. This ordering
allows a user’s existing installation to take priority while still supporting
the project-managed copy.

Reference: [`find_llama_server()`](../../../src/python/local_first_ai/assistant/llama_runtime.py#L68)

If no executable exists, `install_llama_server()` queries the latest official
llama.cpp GitHub release. It identifies the CPU archive matching Linux, macOS,
or Windows and the current x64 or ARM64 architecture. GPU-specific Vulkan,
ROCm, SYCL, OpenVINO, and CUDA packages are excluded from this initial
implementation so there is one predictable managed engine variant.

The archive is downloaded into a temporary directory and extracted into the
runtime cache. `_safe_extract()` rejects archive paths that would escape the
destination directory.

References:

- [Platform-to-asset mapping](../../../src/python/local_first_ai/assistant/llama_runtime.py#L83)
- [Safe archive extraction](../../../src/python/local_first_ai/assistant/llama_runtime.py#L113)
- [llama.cpp installation](../../../src/python/local_first_ai/assistant/llama_runtime.py#L130)

### Model discovery and download

`available_models()` recursively lists `.gguf` files in the managed
model directory. The model menu offers:

- A cached GGUF model.
- An existing GGUF at another filesystem path.
- The recommended Qwen2.5 1.5B Instruct Q4_K_M model.
- A different GGUF supplied by URL.

`ensure_model()` downloads only when the target does not already exist or is
empty. Downloads first use a `.part` file and are renamed only after completion,
which avoids treating an interrupted transfer as a usable model.

References:

- [Model menu](../../../src/python/local_first_ai/assistant/inference_runtime.py#L80)
- [Managed model discovery](../../../src/python/local_first_ai/assistant/llama_runtime.py#L169)
- [Model download/reuse](../../../src/python/local_first_ai/assistant/llama_runtime.py#L178)

### Starting the endpoint

`prepare_llama_runtime()` starts `llama-server` with the selected GGUF, assigns
the filename stem as the model alias, and binds to `127.0.0.1:8004`. It uses a
4096-token context, one parallel sequence, and Jinja chat templates.

The function polls `/health` until the server becomes ready. If the process
exits early or does not become ready before the timeout, setup fails with a
`RuntimeSetupError`. On success, it returns the OpenAI-compatible `/v1` base
URL and registers process cleanup.

Reference: [`prepare_llama_runtime()`](../../../src/python/local_first_ai/assistant/llama_runtime.py#L198)

## Ollama Connection

### Discovery and installation

`find_ollama()` checks `PATH` for the Ollama executable. When it is missing,
`install_ollama()` downloads and runs Ollama’s official platform installer:

- `install.sh` on Linux and macOS.
- `install.ps1` on Windows.

The temporary installer file is removed after execution. Setup fails with a
clear error if the installer returns a non-zero status or the executable still
cannot be found.

References:

- [Ollama discovery](../../../src/python/local_first_ai/assistant/inference_runtime.py#L151)
- [Ollama installation](../../../src/python/local_first_ai/assistant/inference_runtime.py#L156)

### Starting or reusing the service

The application checks `http://127.0.0.1:11434/api/tags`. If that request
succeeds, an existing Ollama service is reused. Otherwise, `_start_ollama()`
runs `ollama serve` and polls the same endpoint until it is ready.

The returned process is recorded only when this application started it. This
distinction prevents application shutdown from terminating an independently
managed Ollama service.

References:

- [Ollama readiness check](../../../src/python/local_first_ai/assistant/inference_runtime.py#L194)
- [Ollama service startup](../../../src/python/local_first_ai/assistant/inference_runtime.py#L202)

### Model selection

`ollama_models()` reads the `/api/tags` response and extracts installed model
names. The user can select one of those models, download the recommended
`qwen2.5:1.5b`, or enter another Ollama model name.

When the requested name is not already installed, the application runs:

```text
ollama pull <model-name>
```

The assistant then connects through Ollama’s OpenAI-compatible endpoint at
`http://127.0.0.1:11434/v1`.

References:

- [Installed-model query](../../../src/python/local_first_ai/assistant/inference_runtime.py#L221)
- [Ollama model selection and pull](../../../src/python/local_first_ai/assistant/inference_runtime.py#L232)
- [Complete Ollama preparation](../../../src/python/local_first_ai/assistant/inference_runtime.py#L267)

## Custom OpenAI-Compatible Endpoint

The custom path does not install or start an unknown third-party engine. It
asks the user for:

- An OpenAI-compatible base URL.
- The model name expected by that endpoint.
- An optional API key, defaulting to `not-needed` for unauthenticated local
  servers.

Trailing slashes are removed from the URL so it can be passed consistently to
the OpenAI client. Because there is no locally owned process, `stop()` has no
external service to terminate.

Reference: [`prepare_custom()`](../../../src/python/local_first_ai/assistant/inference_runtime.py#L289)

## Connection to the Assistant

The CLI parser exposes the following runtime settings:

| Flag | Environment variable | Purpose |
|---|---|---|
| `--engine` | `LOCAL_FIRST_AI_ENGINE` | Select `llama`, `ollama`, or `custom`. |
| `--model` | `OPENAI_MODEL` | Select a GGUF path/filename or engine model name. |
| `--model-url` | `LOCAL_FIRST_AI_MODEL_URL` | Download a missing llama.cpp GGUF. |
| `--base-url` | `OPENAI_BASE_URL` | Supply a custom OpenAI-compatible endpoint. |
| `--api-key` | `OPENAI_API_KEY` | Authenticate to a custom endpoint. |
| `--runtime-dir` | `LOCAL_FIRST_AI_RUNTIME_DIR` | Change the llama.cpp/model cache directory. |

Reference: [`build_parser()`](../../../src/python/local_first_ai/assistant/app.py#L1052)

In `main()`, these parsed values are passed to `prepare_inference_runtime()`.
The returned values are translated into the existing `Config` dataclass:

```text
runtime.base_url -> Config.base_url
runtime.model    -> Config.model
runtime.api_key  -> Config.api_key
```

`make_client()` then constructs the same OpenAI client used by the original
assistant. `ChatSession`, the system prompt, context tools, SQLite operations,
confirmation checks, and streaming loop remain independent of the selected
engine.

References:

- [Runtime selection in `main()`](../../../src/python/local_first_ai/assistant/app.py#L1146)
- [`Config` construction and client connection](../../../src/python/local_first_ai/assistant/app.py#L1170)
- [OpenAI client creation](../../../src/python/local_first_ai/assistant/app.py#L885)

The chat loop is enclosed in `try/finally`, so `runtime.stop()` runs on normal
exit, `quit`, or end-of-file.

Reference: [Runtime cleanup](../../../src/python/local_first_ai/assistant/app.py#L1189)

## Example Flows

### Interactive llama.cpp

```text
Select an inference engine:
  1. llama.cpp
  2. Ollama
  3. Other OpenAI-compatible endpoint

Choose: 1
Select a llama.cpp model:
  1. Use local model: existing-model.gguf
  2. Download recommended Qwen2.5 1.5B Q4_K_M
  3. Use an existing GGUF file by path
  4. Download another GGUF model from a URL
```

### Non-interactive Ollama

```bash
python -m local_first_ai.assistant \
  --engine ollama \
  --model qwen2.5:1.5b
```

### Custom endpoint

```bash
python -m local_first_ai.assistant \
  --engine custom \
  --base-url http://localhost:9000/v1 \
  --model my-model \
  --api-key not-needed
```

## Testing

The runtime tests are offline and deterministic. They mock downloads,
subprocesses, readiness checks, and external services rather than installing an
engine or downloading a large model during the test suite.

[`test_inference_runtime.py`](../../../tests/python/test_inference_runtime.py)
verifies:

- Interactive engine dispatch to a custom endpoint.
- Discovery and selection of an existing local GGUF.
- Custom GGUF URL handling and filename selection.
- Reuse of an installed Ollama model.
- Pulling a requested Ollama model when it is absent.

[`test_llama_runtime.py`](../../../tests/python/test_llama_runtime.py) verifies:

- Preference for a system `llama-server` on `PATH`.
- Reuse of an existing non-empty GGUF.
- Correct llama.cpp command construction, model alias, and endpoint.
- Runtime cache override through `LOCAL_FIRST_AI_RUNTIME_DIR`.

The existing assistant tests continue using an injected fake OpenAI-compatible
client. This confirms that engine preparation remains outside the chat and
SQLite behavior.

## Limitations and Future Work

- The managed llama.cpp installation currently selects a CPU build. GPU build
  selection can be added later without changing the `InferenceRuntime`
  contract.
- llama.cpp currently uses a fixed host, port, context size, and parallelism.
  These can become explicit runtime options in a future iteration.
- Only GGUF files inside the managed model directory are automatically listed;
  models elsewhere are selected by explicit path.
- Ollama installation can request operating-system permissions because it uses
  the official installer.
- A custom endpoint is trusted as user-provided and is not installed,
  health-checked, or lifecycle-managed by the project.
- A downloaded model URL is user-controlled. Future work could add expected
  checksums and display download size before transfer.
- Engine/model compatibility with structured tool calling still depends on the
  selected server and model.

## Outcome

The assistant now supports both guided local setup and advanced external
configuration without coupling its conversation and storage logic to one
inference engine. llama.cpp and Ollama can be discovered, installed, started,
and supplied with a selected model, while other OpenAI-compatible engines can
connect through an endpoint. All three paths converge on the same runtime
contract and reuse the existing client, chat session, tools, and SQLite store.
