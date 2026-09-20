# Stage 2 · Session 3 recovery checkpoint

These are the complete files created or changed by Session 3. Open a link to view or copy
the whole file from its first line through its last line. The application entry point has
its own Session 3 snapshot because Session 4 adds the menu-bar escape hatch; the remaining
files are already in their final Stage 2 form.

## Complete files

| Repository path | Complete checkpoint file |
|---|---|
| `src/fairy/desktop/api_client.py` | [Complete API client](stage-2-final/src/fairy/desktop/api_client.py) |
| `src/fairy/desktop/backend_protocol.py` | [Complete authenticated-handshake protocol](stage-2-final/src/fairy/desktop/backend_protocol.py) |
| `src/fairy/desktop/backend_server.py` | [Complete owned backend entry point](stage-2-final/src/fairy/desktop/backend_server.py) |
| `src/fairy/desktop/backend.py` | [Complete backend controller](stage-2-final/src/fairy/desktop/backend.py) |
| `src/fairy/desktop/status_popover.py` | [Complete status popover](stage-2-final/src/fairy/desktop/status_popover.py) |
| `src/fairy/desktop/chat_popover.py` | [Complete chat popover](stage-2-final/src/fairy/desktop/chat_popover.py) |
| `src/fairy/desktop/window.py` | [Complete floating window](stage-2-final/src/fairy/desktop/window.py) |
| `src/fairy/desktop/app.py` | [Complete Session 3 application entry point](stage-2-session-3/src/fairy/desktop/app.py) |
| `src/fairy/web_app.py` | [Complete authenticated-capable web app](stage-2-final/src/fairy/web_app.py) |
| `tests/test_backend_server.py` | [Complete backend-server tests](stage-2-final/tests/test_backend_server.py) |
| `tests/test_desktop_backend_integration.py` | [Complete controller/client security regression tests](stage-2-final/tests/test_desktop_backend_integration.py) |
| `tests/test_desktop_backend_protocol.py` | [Complete handshake and lifecycle tests](stage-2-final/tests/test_desktop_backend_protocol.py) |
| `tests/test_desktop_protocol.py` | [Complete response-decoder tests](stage-2-final/tests/test_desktop_protocol.py) |
| `tests/test_web_app.py` | [Complete web-route and authentication tests](stage-2-final/tests/test_web_app.py) |

`geometry.py`, `tests/test_desktop_geometry.py`, and `pyproject.toml` remain exactly as
shown in the Session 2 and Session 1 checkpoints.

## Expected commands and output

```bash
uv run pytest tests/test_backend_server.py \
  tests/test_desktop_backend_integration.py \
  tests/test_desktop_backend_protocol.py \
  tests/test_desktop_protocol.py \
  tests/test_web_app.py
uv run ruff format .
uv run ruff check .
uv run pytest
uv run fairy-desktop
```

Representative automated result after all Stage 2 tests are present:

```text
============================== 32 passed in ... ==============================
All checks passed!
============================== 47 passed in ... ==============================
```

Expected visible result:

- The desktop command starts its own backend on an OS-assigned loopback port.
- The desktop does not reuse or send chat to an arbitrary service already using port 8000.
- A valid authenticated health response enables chat; an invalid handshake never does.
- A 650 ms hover shows an honest status without taking focus.
- Clicking without dragging opens a focused chat popover.
- Sending a message shows `Thinking locally…`, then restores the current status and shows
  a real local-model reply.
- Child failure aborts an in-flight authenticated request and disables later sends.
- A stale health reply after shutdown cannot return the controller to ready.
- Closing the Fairy exits this pre-menu session and stops only its owned child process.
