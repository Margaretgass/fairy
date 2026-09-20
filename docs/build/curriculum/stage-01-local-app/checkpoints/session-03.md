# Stage 1 · Session 3 recovery checkpoint

[← Back to Stage 1 instructions](../README.md)

> **Use only if stuck.** This is a recovery reference, not another lesson to complete.

Session 3 changes several existing files, including two larger browser files. To keep each
fallback directly copyable, the complete expected files are stored as source snapshots
rather than abbreviated snippets.

Every link below opens the entire file from its first line to its last line:

| Repository destination | Complete expected file |
|---|---|
| `src/fairy/prompts.py` | [Complete prompts.py](final/complete-code/src/fairy/prompts.py) |
| `src/fairy/web_app.py` | [Complete web_app.py](final/complete-code/src/fairy/web_app.py) |
| `.env.example` | [Complete .env.example](final/complete-code/.env.example) |
| `uiux/ui/index.html` | [Complete index.html](final/complete-code/uiux/ui/index.html) |
| `uiux/ui/app.js` | [Complete app.js](final/complete-code/uiux/ui/app.js) |
| `README.md` | [Complete root README](final/complete-code/ROOT_README.md) |

When using a recovery file, copy its full contents to the repository destination shown in
the left column. `ROOT_README.md` is deliberately named differently inside the checkpoint
so it cannot be confused with the curriculum README.

### Preview without copying files

Open [the self-contained Stage 1 prototype](final/complete-code/uiux/ui/index.html) for a visual
check. Its neighboring styles, scripts, fonts, and images are unchanged support copies that
allow the checkpoint to render when opened directly. Only the files in the table above are
Stage 1 recovery destinations.

The direct-file preview cannot call the relative `POST /api/chat` endpoint. Run Uvicorn and
open `http://127.0.0.1:8000` when you want to verify live local-AI chat.

## Expected commands and output

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Representative result:

```text
All checks passed!
22 files already formatted
============================== 13 passed in ... ==============================
```

The formatted-file count and duration can vary if unrelated files have been added.

Then run:

```bash
ollama list
uv run python -m fairy.test_local_model
uv run uvicorn fairy.web_app:app --reload
```

Expected live result:

- `qwen2.5:3b` appears in the installed model list.
- The direct model check returns a short useful next action; wording varies.
- Uvicorn serves `http://127.0.0.1:8000`.
- The browser banner still identifies sample prototype data but no longer claims chat is
  simulated or scripted.
- Talk displays `Local AI · Ollama` and renders a real `/api/chat` reply.
