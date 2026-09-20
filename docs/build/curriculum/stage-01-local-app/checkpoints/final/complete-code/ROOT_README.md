# NeuroFairy

NeuroFairy is a calm, local-first executive-function companion that helps someone choose
and begin one realistic next action.

## Current status

The repository has a working local chat slice:

```text
Fairy Home browser UI
    → POST /api/chat
    → FastAPI
    → LangChain ChatOllama
    → local Ollama qwen2.5:3b
    → JSON reply rendered in Talk
```

SQLite task operations and FastMCP task tools also exist, but they are not yet connected
to Fairy Home or the chat model. Most non-chat browser state remains a `localStorage`
prototype.

## Prerequisites

- Python 3.13 or newer
- [`uv`](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/)
- Local model `qwen2.5:3b`

```bash
ollama pull qwen2.5:3b
uv sync
```

## Run the checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Test the local model directly

```bash
ollama list
uv run python -m fairy.test_local_model
```

## Run Fairy Home

```bash
uv run uvicorn fairy.web_app:app --reload
```

Open `http://127.0.0.1:8000`, select **Talk**, and send a message.

## Implemented

- Existing browser UI served by FastAPI
- Browser-to-FastAPI chat request
- Local LangChain/ChatOllama service using `qwen2.5:3b`
- SQLite task operations with deterministic tests
- FastMCP task tools

## Planned

- Floating desktop Fairy
- Shared internal tasks and next actions
- Brain-dump planning
- Gentle focus/body-doubling support
- Safe LangChain tools
- Read-only calendar context and connector privacy
- Pilot evaluation and optional non-punitive charms

No third-party account is connected, and V1 integrations will not modify external data.

## Follow-along curriculum

Start with `docs/build/curriculum/README.md`. While viewing this recovery snapshot, use the
[current curriculum link](../../../../README.md). The curriculum distinguishes implemented,
prototype, planned, and future-optional behavior.

## License

MIT
