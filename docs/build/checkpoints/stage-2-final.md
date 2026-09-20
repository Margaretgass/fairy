# Stage 2 final recovery snapshot

This is the complete Stage 2 checkpoint. Every hand-maintained file is stored below in
copy-ready form from its first line to its last line. No code is replaced with ellipses.

Use this map only after attempting the incremental lesson. If a final file differs, replace
that file with the linked complete version, run formatting, and rerun the narrowest relevant
test before continuing.

## Final source tree

```text
pyproject.toml
src/fairy/
├── web_app.py
└── desktop/
    ├── __init__.py
    ├── api_client.py
    ├── app.py
    ├── backend.py
    ├── backend_protocol.py
    ├── backend_server.py
    ├── chat_popover.py
    ├── geometry.py
    ├── status_popover.py
    └── window.py
tests/
├── test_backend_server.py
├── test_desktop_backend_integration.py
├── test_desktop_backend_protocol.py
├── test_desktop_geometry.py
├── test_desktop_protocol.py
└── test_web_app.py
```

## Complete final files

| Final path | Full-file checkpoint |
|---|---|
| `pyproject.toml` | [Complete pyproject](stage-2-final/pyproject.toml) |
| `src/fairy/web_app.py` | [Complete web application](stage-2-final/src/fairy/web_app.py) |
| `src/fairy/desktop/__init__.py` | [Complete package marker](stage-2-final/src/fairy/desktop/__init__.py) |
| `src/fairy/desktop/api_client.py` | [Complete authenticated API client](stage-2-final/src/fairy/desktop/api_client.py) |
| `src/fairy/desktop/app.py` | [Complete final application entry point](stage-2-final/src/fairy/desktop/app.py) |
| `src/fairy/desktop/backend.py` | [Complete backend controller](stage-2-final/src/fairy/desktop/backend.py) |
| `src/fairy/desktop/backend_protocol.py` | [Complete handshake protocol](stage-2-final/src/fairy/desktop/backend_protocol.py) |
| `src/fairy/desktop/backend_server.py` | [Complete owned backend entry point](stage-2-final/src/fairy/desktop/backend_server.py) |
| `src/fairy/desktop/chat_popover.py` | [Complete chat popover](stage-2-final/src/fairy/desktop/chat_popover.py) |
| `src/fairy/desktop/geometry.py` | [Complete geometry module](stage-2-final/src/fairy/desktop/geometry.py) |
| `src/fairy/desktop/status_popover.py` | [Complete status popover](stage-2-final/src/fairy/desktop/status_popover.py) |
| `src/fairy/desktop/window.py` | [Complete floating window](stage-2-final/src/fairy/desktop/window.py) |
| `tests/test_backend_server.py` | [Complete backend-server tests](stage-2-final/tests/test_backend_server.py) |
| `tests/test_desktop_backend_integration.py` | [Complete controller/client security regression tests](stage-2-final/tests/test_desktop_backend_integration.py) |
| `tests/test_desktop_backend_protocol.py` | [Complete handshake and lifecycle tests](stage-2-final/tests/test_desktop_backend_protocol.py) |
| `tests/test_desktop_geometry.py` | [Complete geometry tests](stage-2-final/tests/test_desktop_geometry.py) |
| `tests/test_desktop_protocol.py` | [Complete response-decoder tests](stage-2-final/tests/test_desktop_protocol.py) |
| `tests/test_web_app.py` | [Complete web-route and authentication tests](stage-2-final/tests/test_web_app.py) |

If an anchor does not jump in your Markdown viewer, open the linked checkpoint and search
for the exact path shown in the left column.

`uv.lock` is intentionally not pasted. It is generated from `pyproject.toml` by `uv sync`
and should be committed after dependency resolution.

## Final expected verification

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest
git diff --check
uv run fairy-desktop
```

Representative automated result:

```text
All checks passed!
============================== 47 passed in ... ==============================
```

The precise formatted-file count, test duration, Uvicorn process ID, local client port,
and model wording can vary.

## Final expected product behavior

- One neutral placeholder Fairy stays above normal macOS windows.
- Idle and hover surfaces do not interrupt typing.
- Dragging snaps and saves; disconnected displays cannot strand the Fairy.
- Hover gives only an honest local-service status.
- Click opens an accessible chat popover that sends through `POST /api/chat`.
- Network errors are retryable and never freeze the GUI.
- The desktop app starts one backend child it explicitly owns on an OS-assigned loopback
  port and enables chat only after an authenticated handshake and health check.
- It never reuses or sends a private chat body to an arbitrary process on port 8000.
- Child failure aborts any in-flight authenticated request before clearing the client.
- A late health callback after shutdown cannot restore the client configuration.
- Quit stops only an owned child backend.
- The menu-bar item remains available when the Fairy is hidden.
- No final art, task synchronization, focus engine, tools, or connectors are implied.
