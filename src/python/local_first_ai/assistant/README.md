# Week 3 assistant

Chat CLI: local SQLite context + a selectable inference endpoint.
Model picks chat or tools (list / search / read / create / update / delete).
Writes need confirmation.

## 1. Setup (repo root)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No endpoint configuration is required. At startup the assistant asks you to
select:

1. `llama.cpp` — uses an existing `llama-server`, or installs the latest
   official CPU build. It lists cached GGUF models, accepts another local GGUF
   path, and can download the recommended Qwen model or another GGUF URL.
2. `Ollama` — uses an existing installation, or runs Ollama's official
   installer. It lists installed models and can pull Qwen or another model.
3. `Other` — asks for an OpenAI-compatible endpoint, model name, and optional
   API key. The external server is not installed or managed by this project.

llama.cpp files are cached in `~/.cache/local-first-ai`, so later runs reuse
them. Set `LOCAL_FIRST_AI_RUNTIME_DIR` or pass `--runtime-dir` to change this.

Each new shell:

```bash
source .venv/bin/activate
export PYTHONPATH=src/python
```

## 2. Run

```bash
python -m local_first_ai.assistant
```

Without activate:

```bash
PYTHONPATH=src/python .venv/bin/python -m local_first_ai.assistant
```

Optional env: `ASSISTANT_STREAM=false`, `LOCAL_CONTEXT_DB_PATH=...`

For scripts, bypass the menus with flags:

```bash
# Existing or automatically downloaded Ollama model
python -m local_first_ai.assistant --engine ollama --model qwen2.5:1.5b

# Existing llama.cpp GGUF
python -m local_first_ai.assistant --engine llama --model /models/model.gguf

# Download a llama.cpp GGUF into the managed model directory
python -m local_first_ai.assistant --engine llama \
  --model model.gguf --model-url https://host.example/model.gguf

# User-managed OpenAI-compatible server
python -m local_first_ai.assistant --engine custom \
  --base-url http://localhost:9000/v1 --model my-model --api-key not-needed
```

An internet connection is required only when a selected engine or model must
be downloaded. Installation tools may request the operating system permissions
required by their official installer.

## 3. Test

```bash
source .venv/bin/activate
export PYTHONPATH=src/python
python -m unittest discover -s tests/python -p 'test*.py' -v
```

No live server needed.
