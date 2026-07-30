# Week 3 assistant

Chat CLI: local SQLite context + local OpenAI-compatible model.
Model picks chat or tools (list / search / read / create / update / delete).
Writes need confirmation.

## 1. Setup (repo root)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp src/python/local_first_ai/assistant/.env.example \
   src/python/local_first_ai/assistant/.env
```

Edit `.env` and set:

- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `OPENAI_API_KEY`

No hard-coded defaults. Missing any of those three → error and exit.

Each new shell:

```bash
source .venv/bin/activate
export PYTHONPATH=src/python
```

## 2. Run

Start local model server first. App auto-loads `.env` next to this README.

```bash
python -m local_first_ai.assistant
```

Without activate:

```bash
PYTHONPATH=src/python .venv/bin/python -m local_first_ai.assistant
```

Optional flags (override `.env`):

```bash
python -m local_first_ai.assistant \
  --base-url http://localhost:8004/v1 \
  --model your-model \
  --api-key not-needed
```

Optional env: `ASSISTANT_STREAM=false`, `LOCAL_CONTEXT_DB_PATH=...`

## 3. Test

```bash
source .venv/bin/activate
export PYTHONPATH=src/python
python -m unittest tests.python.test_assistant -v
```

No live server needed.
