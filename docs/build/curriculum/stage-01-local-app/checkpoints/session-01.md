# Stage 1 · Session 1 recovery checkpoint

[← Back to Stage 1 instructions](../README.md)

> **Use only if stuck.** This is a recovery reference, not another lesson to complete.

Session 1 is an observation step. It intentionally changes no files, so there is no code
file to replace. The recovery checkpoint is the verified baseline output below.

## Expected commands

```bash
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run python -m fairy.test_local_model
uv run uvicorn fairy.web_app:app --reload
```

## Expected deterministic output

```text
============================== 8 passed in ... ===============================
21 files already formatted
E501 Line too long (...) in src/fairy/prompts.py
E501 Line too long (...) in src/fairy/web_app.py
Found 2 errors.
```

The duration and exact Ruff columns may vary slightly. At this baseline, the two named
`E501` failures are expected observations, not passing lint.

## Expected live output

The model test prints a short response recommending one visible first action. Its exact
wording varies. Uvicorn should report a local address equivalent to:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000
```

In the browser, one Talk message should produce one `POST /api/chat` request with HTTP 200
and a non-empty `reply`. If any of those facts differ, stop at the responsible boundary
instead of editing files during this observation session.
