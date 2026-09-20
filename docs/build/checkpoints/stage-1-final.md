# Stage 1 final recovery snapshot

This map contains every hand-maintained source, test, configuration, and documentation file
created or changed by Stage 1. Each linked file is complete and contains no ellipses.

## Final changed files

| Repository destination | Complete final file |
|---|---|
| `pyproject.toml` | [Complete project configuration](stage-1-final/pyproject.toml) |
| `tests/test_web_app.py` | [Complete route tests](stage-1-final/tests/test_web_app.py) |
| `src/fairy/prompts.py` | [Complete system prompt](stage-1-final/src/fairy/prompts.py) |
| `src/fairy/web_app.py` | [Complete FastAPI app](stage-1-final/src/fairy/web_app.py) |
| `.env.example` | [Complete environment example](stage-1-final/.env.example) |
| `uiux/ui/index.html` | [Complete browser shell](stage-1-final/uiux/ui/index.html) |
| `uiux/ui/app.js` | [Complete browser behavior](stage-1-final/uiux/ui/app.js) |
| `README.md` | [Complete root README](stage-1-final/ROOT_README.md) |

The `ROOT_README.md` checkpoint content belongs at repository path `README.md`. Its plain
`docs/build/README.md` path is the destination-relative curriculum location; the adjacent
checkpoint link remains clickable while you inspect the recovery copy in place.

`uv.lock` is generated from `pyproject.toml` by `uv sync`; do not copy or edit it by hand.

## Open the visual checkpoint

Open [the checkpoint prototype](stage-1-final/uiux/ui/index.html) to inspect the Stage 1
interface without changing your working files. The checkpoint includes copies of the
unchanged styles, helper scripts, fonts, and image assets that the two edited UI files need,
so the prototype also renders when this HTML file is opened directly.

Direct-file preview is for visual and interaction recovery only. To test real chat, run the
application and open `http://127.0.0.1:8000` so `POST /api/chat` reaches FastAPI.

The support copies under `stage-1-final/uiux/assets/`, `stage-1-final/uiux/references/`, and
the other files in `stage-1-final/uiux/ui/` were not changed by Stage 1. Do not copy them
over newer repository files during recovery unless those original files are missing.

## Final expected verification

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
git diff --check
```

Representative result:

```text
All checks passed!
22 files already formatted
============================== 13 passed in ... ==============================
```

## Final expected product behavior

- Fairy Home loads from FastAPI.
- The standalone checkpoint link renders the styled prototype instead of bare HTML.
- Talk sends real requests to `POST /api/chat` and renders local-model replies.
- Whitespace requests, missing fields, service success, service failure, and static serving
  have deterministic route coverage.
- The UI no longer labels working chat as simulated or scripted.
- The README and `.env.example` identify the actual local model `qwen2.5:3b`.
- The task/MCP path remains separate, and no connector or model tool use is implied.
- Ruff lint, formatting, and all 13 Stage 1 tests pass before Stage 2 begins.
