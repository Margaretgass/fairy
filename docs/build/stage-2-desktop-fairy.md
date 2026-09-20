# Stage 2 — Desktop Fairy companion

> **Status:** Planned next. Start only after Stage 1 has a clean test, format, and lint
> baseline.

**Stage outcome:** a small neutral-placeholder Fairy floats above normal macOS windows,
does not interrupt typing, can be dragged and recovered after monitor changes, shows a
short honest hover status, and opens a chat popover that reuses the existing local
`POST /api/chat` connection.

**Estimated sessions:** 4 small sessions. Stop after each session, verify the result, and
report what happened before continuing.

This is the earliest new product feature in the revised curriculum. It makes the working
local AI reachable from the desktop without creating a second chat service.

See the [architecture map](ARCHITECTURE.md) for the current browser path and target desktop
runtime.

---

## Product slice built in this stage

```text
Person
  │
  ├─ hover ──> short status that does not take keyboard focus
  │
  └─ click ──> chat popover that intentionally accepts text input
                    │
                    │ POST /api/chat
                    ▼
               existing FastAPI app
                    │
                    ▼
             existing local AI service
                    │
                    ▼
                local Ollama
```

The desktop Fairy is a client of the local API. It does not call Ollama directly and does
not read or write the task database directly.

---

## Current starting point

### Already implemented

- FastAPI serves the existing Fairy Home browser UI.
- `POST /api/chat` accepts `{"message": "..."}`.
- The route calls the local LangChain `ChatOllama` service.
- Ollama runs `qwen2.5:3b` locally.
- The Talk UI already sends real messages and renders real replies.

### Not implemented yet

- PySide6 or PyObjC dependencies
- Desktop application package or command
- Floating macOS window
- Desktop API client
- Hover status or chat popover
- Desktop position persistence
- Desktop-owned backend lifecycle, authenticated startup protocol, or health route

Do not describe the old desktop lesson's example code as working repository behavior. It
was a useful design reference, but none of those files exist in the current source tree.

---

## Build now

- One neutral, accessible placeholder instead of final Fairy artwork
- A transparent, always-reachable desktop window
- No focus theft while the Fairy is idle or showing hover status
- Dragging with a native movement threshold
- Edge snapping and safe position restoration across monitor changes
- A brief, honest hover status
- A click-to-chat popover using the existing `/api/chat` contract
- Calm loading, unavailable, and retry states
- A menu-bar path to show, hide, open chat, and quit
- Explicit ownership of any backend process started by the desktop app
- An OS-assigned loopback port, per-launch credential, authenticated child handshake, and
  credential-protected desktop health/chat requests

## Not yet

- Final Fairy art, animation, colors, or typography
- Task capture or task recommendations
- Shared task state between browser and desktop
- Focus timer status
- Brain-dump planning
- LangChain tools
- OAuth or external integrations
- Notifications, launch at login, signing, notarization, or distribution packaging

Those behaviors belong to later stages. In particular, the hover panel must not invent a
task or focus status before those services exist.

---

## Learning goals

By the end of this stage, you should be able to explain:

- How a GUI event loop differs from a command-line program
- Why the idle Fairy and text-entry popover need different focus behavior
- Why macOS accessory behavior needs a small PyObjC bridge
- How drag thresholds distinguish clicking from dragging
- Why saved window coordinates must be validated against current screens
- How Qt signals and slots support timers and network replies
- Why network work must not block the GUI thread
- Why the desktop app calls FastAPI instead of Ollama or SQLite directly
- How to start and stop only a backend process the desktop app owns
- Why loopback binding alone does not authenticate a local process

---

## Architecture decisions for this stage

The old Swift/SwiftUI/Xcode prototype is out of scope. Do not port it, embed it, or keep a
second desktop implementation beside this one. Stage 2 extends the current Python
application with PySide6 and a narrow PyObjC bridge only where macOS window behavior needs
it.

| Decision | Choice | Reason |
|---|---|---|
| Desktop toolkit | PySide6 | Keeps the application in Python and provides mature macOS window/network APIs |
| macOS bridge | `pyobjc-framework-Cocoa` | Applies accessory-app behavior Qt flags alone do not guarantee |
| Desktop-to-backend boundary | Loopback HTTP | Reuses the working FastAPI contract and keeps one product-logic boundary |
| Desktop backend identity | Owned child + authenticated startup handshake | Prevents an unrelated local process from impersonating Fairy's API |
| Desktop API credential | Random per-launch token sent through child stdin | Keeps private chat disabled until the exact child proves its identity |
| Chat networking | Qt network APIs | Keeps requests asynchronous on the GUI event loop |
| Window preferences | `QSettings` | Stores only visual desktop preferences, not product/domain state |
| Product state | Application services and SQLite later | Prevents a second source of truth in the desktop UI |
| Visuals | Replaceable neutral tokens | Final visual direction and artwork will be supplied separately |

`QSettings` may store the Fairy's screen and position. It must not become storage for
tasks, plans, focus sessions, consent, or chat truth.

---

## Files created or changed

| Path | Responsibility |
|---|---|
| `pyproject.toml` | PySide6/PyObjC dependencies and `fairy-desktop` command |
| `src/fairy/desktop/__init__.py` | Desktop package marker |
| `src/fairy/desktop/app.py` | QApplication lifecycle and top-level composition |
| `src/fairy/desktop/window.py` | Floating Fairy window and pointer events |
| `src/fairy/desktop/geometry.py` | Pure clamp and edge-snap calculations |
| `src/fairy/desktop/status_popover.py` | Non-activating hover status |
| `src/fairy/desktop/chat_popover.py` | Activating text conversation surface |
| `src/fairy/desktop/api_client.py` | Asynchronous `/api/chat` and health requests |
| `src/fairy/desktop/backend.py` | Owned local-backend process lifecycle |
| `src/fairy/desktop/backend_protocol.py` | Pure authenticated-handshake and ownership rules |
| `src/fairy/desktop/backend_server.py` | Authenticated child entry point on an OS-assigned loopback port |
| `src/fairy/web_app.py` | App factory plus protected desktop health/chat routes |
| `tests/test_backend_server.py` | Child token and loopback-binding tests |
| `tests/test_desktop_backend_integration.py` | Real controller/client trust-boundary regression tests with small Qt fakes |
| `tests/test_desktop_backend_protocol.py` | Forged-proof and lifecycle regression tests |
| `tests/test_desktop_geometry.py` | Deterministic position and monitor tests |
| `tests/test_desktop_protocol.py` | Desktop response-validation tests |
| `tests/test_web_app.py` | Existing route tests plus health-route coverage |

Keep desktop code under `src/fairy/desktop/`. Do not create a second top-level Python
package when the existing `fairy` package already owns the application.

---

## Prerequisites

```bash
cd ~/code/fairy
git status --short --branch
uv sync
uv run pytest
uv run ruff format --check .
uv run ruff check .
```

Expected before Stage 2:

- Stage 1 route tests are committed and passing.
- Formatting and linting are clean.
- The working tree does not contain changes you do not understand.
- The browser can still send a message through `/api/chat`.

If the two Stage 1 line-length failures remain, finish Stage 1 first. Do not bury an old
failure under a new dependency and several desktop files.

---

## Session 1 — Put the neutral Fairy on screen

### Practical goal

Show a small always-on-top placeholder that remains visible without stealing keyboard
focus from the application the user is already using.

### Concept

`QApplication.exec()` starts an event loop. The application waits for pointer, window,
timer, and network events; Qt calls your event handlers when those events occur.

The idle Fairy is an accessory surface, not a normal document window. It should not appear
in the Dock or `Cmd+Tab`, and merely showing or clicking the idle surface must not interrupt
typing elsewhere.

### Step 1: add only the approved desktop dependencies

```bash
cd ~/code/fairy
uv add PySide6 'pyobjc-framework-Cocoa; sys_platform == "darwin"'
```

The environment marker keeps the Cocoa bridge macOS-specific. Do not add a web framework,
hosted AI SDK, or second HTTP server.

### Step 2: create the desktop package

Create:

```text
src/fairy/desktop/
├── __init__.py
├── app.py
└── window.py
```

In `app.py`, keep macOS-specific behavior behind one function:

```python
def become_accessory_app() -> None:
    if sys.platform != "darwin":
        return

    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )
```

Create `QApplication` first, apply the accessory policy before showing the window, then
enter the event loop:

```python
def main() -> None:
    app = QApplication(sys.argv)
    become_accessory_app()

    fairy = FairyWindow()
    fairy.show()

    raise SystemExit(app.exec())
```

### Step 3: create a replaceable placeholder window

`FairyWindow` should:

- inherit from `QWidget`;
- combine `FramelessWindowHint`, `WindowStaysOnTopHint`,
  `WindowDoesNotAcceptFocus`, and `Tool`;
- enable `WA_TranslucentBackground` and `WA_ShowWithoutActivating`;
- have a fixed 72 × 72 logical-pixel hit area;
- expose an accessible name such as `Open NeuroFairy`;
- show a neutral high-contrast circle containing the word `Fairy` or the letter `F`.

Define placeholder dimensions and colors as named constants at the top of `window.py`.
Do not copy artwork from another directory or encode final visual decisions in this stage.

### Step 4: register the command

Add to `[project.scripts]` in `pyproject.toml`:

```toml
fairy-desktop = "fairy.desktop.app:main"
```

Then run:

```bash
uv sync
uv run fairy-desktop
```

### Manual verification

1. The placeholder has no rectangular opaque background.
2. It stays above a normal window.
3. It does not appear in `Cmd+Tab`.
4. Typing continues in another app while the idle Fairy is visible.
5. VoiceOver identifies it as `Open NeuroFairy`.
6. `Ctrl-C` in the launching terminal exits during this first session.

### Likely errors

| Symptom | First check |
|---|---|
| `ModuleNotFoundError: PySide6` | Confirm `uv add` and `uv sync` completed |
| `ModuleNotFoundError: AppKit` | Confirm the quoted macOS dependency appears in `pyproject.toml` |
| Placeholder has an opaque square | Check `WA_TranslucentBackground` and child background radius |
| Idle Fairy steals focus | Check the window flags, `WA_ShowWithoutActivating`, and accessory policy timing |
| Fairy is invisible | Temporarily place it at `(400, 400)` and verify the fixed size |

### Stop checkpoint

Run:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

Suggested commit message after all checks and the manual checklist pass:

```text
feat: add neutral floating desktop fairy
```

Stop and report which macOS checks passed. Do not add dragging or chat yet.

### Full-file recovery checkpoint

If any incremental edit is unclear, compare against the
[Session 1 complete files and expected output](checkpoints/stage-2-session-1.md). It contains
the entire `pyproject.toml`, `__init__.py`, `window.py`, and `app.py` with no omitted code.

---

## Session 2 — Drag, snap, and recover safely

### Practical goal

Make the Fairy behave like a reliable desktop object across clicks, drags, relaunches, and
monitor changes.

### Concept

A click always contains tiny pointer movement. Use `QApplication.startDragDistance()` as
the threshold so macOS accessibility and pointer preferences influence the behavior.

Window geometry is deterministic logic. Put calculations in `geometry.py` so they can be
tested without showing a real window.

### Step 1: write the failing geometry tests

Create `tests/test_desktop_geometry.py` with cases for:

- a point already inside the available screen rectangle;
- a saved point beyond the right or bottom edge;
- a negative/off-screen point;
- a window larger than the remaining visible area;
- snapping to the nearer left edge;
- snapping to the nearer right edge;
- stable behavior when both edges are equally distant.

Use simple integer inputs. Do not require a running `QApplication` for these tests.

Run the new file and confirm it fails because the functions do not exist yet:

```bash
uv run pytest tests/test_desktop_geometry.py
```

### Step 2: implement pure geometry helpers

Create `src/fairy/desktop/geometry.py` with small typed values and functions equivalent to:

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


def clamp_position(position: Point, window: Rect, available: Rect) -> Point: ...


def snap_to_nearest_side(position: Point, window: Rect, available: Rect) -> Point: ...
```

Keep Qt types at the edge: translate `QPoint`/`QRect` into these values in `window.py`, call
the pure function, then translate the returned point back.

### Step 3: add pointer behavior

In `FairyWindow`:

1. Record the global press position and window origin in `mousePressEvent`.
2. In `mouseMoveEvent`, calculate Manhattan distance from the press point.
3. Mark the gesture as dragging only after the native threshold is exceeded.
4. Move relative to the original position while dragging.
5. On release, snap to the nearest horizontal screen edge only if a drag occurred.
6. Treat a release below the threshold as a click; leave the click action empty until
   Session 3.

Use `QApplication.screenAt()` and each screen's `availableGeometry()`. Available geometry
excludes the menu bar and Dock.

### Step 4: persist only presentation preferences

Use `QSettings("NeuroFairy", "Desktop")` to store:

- x position;
- y position;
- screen name.

On launch:

1. Find the saved screen by name.
2. Fall back to the primary screen if it is no longer connected.
3. Clamp the saved position to that screen's current available geometry.
4. Show the window only after a valid visible position is chosen.

Do not store tasks, chat history, plans, or focus state in `QSettings`.

### Verification

```bash
uv run pytest tests/test_desktop_geometry.py
uv run ruff format .
uv run ruff check .
uv run pytest
uv run fairy-desktop
```

Manual checks:

1. A click does not move the Fairy.
2. A drag follows the pointer and snaps to the nearer side.
3. Quit and relaunch restores a visible position.
4. Move it to a secondary display, quit, disconnect that display, and relaunch.
5. The Fairy returns to a visible area on a remaining screen.

Suggested commit message:

```text
feat: add safe fairy dragging and position restore
```

Stop before adding hover or network behavior.

### Full-file recovery checkpoint

Use the [Session 2 complete files and expected output](checkpoints/stage-2-session-2.md) if
you get stuck. It contains the entire geometry module, updated window, and geometry test
file, plus the expected failing and passing pytest results.

---

## Session 3 — Hover, click, and authenticated real chat

### Practical goal

Make hover and click do two intentionally different jobs, then connect chat only after the
desktop has proved that it is talking to the backend child it started:

- Hover gives a short status without activating the app.
- Click opens a keyboard-accessible chat popover.
- The desktop starts one owned backend on an OS-assigned loopback port.
- Private chat stays disabled until an authenticated startup handshake and health check pass.

### Concept

Loopback means “this computer,” not “this exact process.” A public health response on a
fixed port can be copied by an unrelated local process. Because chat can contain private
user text, the desktop must authenticate the destination before it sends a message.

The UI must also avoid blocking HTTP work on the GUI thread. `QNetworkAccessManager`
returns immediately and emits a signal when the reply arrives.

### Step 1: write the security boundary tests first

Add these pure or route-level tests before implementation:

- a valid child handshake proves knowledge of a per-launch secret;
- a forged proof is rejected;
- invalid ports are rejected;
- chat is disabled after an owned child fails;
- shutdown targets only a running owned child;
- the protected health and chat routes reject missing or incorrect credentials;
- a matching credential still permits a normal chat request;
- the child reads its credential from standard input and binds an OS-assigned loopback port.

Run them and confirm they fail because the new modules and `create_app` factory do not yet
exist. This is the expected red test phase—not a finished checkpoint.

### Step 2: add the authenticated web-app factory

Refactor `src/fairy/web_app.py` to expose:

```python
def create_app(*, api_token: str | None = None) -> FastAPI:
    ...


app = create_app()
```

The default `app` keeps manual browser development working on port 8000. When
`api_token` is supplied by the desktop-owned child, both `/api/health` and `/api/chat`
require the matching `X-Fairy-Token` header. Compare credentials with
`hmac.compare_digest` and return HTTP 401 for missing or incorrect values.

This separation is deliberate:

- `uv run uvicorn fairy.web_app:app --reload` is the browser-development path;
- `uv run fairy-desktop` creates a separate authenticated child for desktop chat;
- the desktop never discovers or reuses an arbitrary process on port 8000.

### Step 3: implement and test the startup protocol

Keep the cryptographic and ownership rules in the pure
`desktop/backend_protocol.py` module. The child emits one line containing its selected
port and an HMAC-SHA256 proof derived from the per-launch secret. The parent accepts the
port only when the proof matches.

Create `desktop/backend_server.py` to:

1. read a high-entropy secret from standard input, not command-line arguments;
2. bind `127.0.0.1` with port `0` so the operating system selects an available port;
3. print the authenticated handshake;
4. run `create_app(api_token=token)` on the already-bound socket.

Do not place the token in logs, UI state, SQLite, or the process argument list.

### Step 4: create the asynchronous authenticated client and controller

`api_client.py` should have no fixed base URL. It receives the verified base URL and token
from `BackendController`, places the credential in `X-Fairy-Token`, applies finite
timeouts, allows one in-flight chat send, and clears its configuration when the child is
no longer ready. Clearing configuration must also abort any in-flight chat or health reply
so a dead child's port cannot be rebound while an authenticated request is still queued.

`backend.py` should use `QProcess` and this lifecycle:

```text
stopped → starting → authenticated health check → ready
                  └────────────────────────────→ failed
ready ── child exits ──────────────────────────→ failed
```

On failure, clear the client configuration and abort its active replies before another chat
can be sent. On shutdown, terminate only the stored owned child. Do not use `shell=True`,
broad process-name killing, or `pkill`.

### Step 5: create hover and chat popovers

Use a non-activating tool window for the delayed hover status and an activating popover for
text entry. Honest statuses in this stage are limited to:

- `Starting local service…` while the owned child starts;
- `Ready to help` only after authenticated health succeeds;
- `Local service unavailable` after failure;
- `Thinking locally…` only while a chat request is pending.

When thinking ends, always restore the current backend status. Never leave the hover panel
stuck on `Thinking locally…`.

The chat popover should provide a readable transcript, labeled multiline input, Send
button, visible sending state, retryable connection error, Escape-to-close behavior,
useful tab order, and accessible names. Escape user and assistant strings before adding
them to rich-text transcript HTML.

### Step 6: connect and verify the real desktop path

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

Manual checks:

1. The desktop starts without requiring a separate Uvicorn terminal.
2. Passing over the Fairy quickly does not flash a status.
3. Hovering for the delay shows a short status without moving keyboard focus.
4. Clicking without dragging opens the chat popover.
5. Sending a message creates one authenticated `POST /api/chat` request and shows a reply.
6. Stopping the owned child aborts an unfinished request, changes the UI to unavailable,
   and disables later chat sends.
7. A manually started service on port 8000 is neither contacted nor stopped.

Suggested commit message:

```text
feat: connect desktop fairy to authenticated local backend
```

### Full-file recovery checkpoint

Use the [Session 3 complete files and expected output](checkpoints/stage-2-session-3.md) if
you get stuck. It links every complete runtime and test file created or changed in this
session, including the pre-menu application entry point.

---

## Session 4 — Add the menu-bar escape hatch and verify safe exit

### Practical goal

Keep the Fairy recoverable when hidden and make Quit stop exactly the child process owned
by this desktop launch.

### Step 1: add the menu-bar controls

Add `QSystemTrayIcon` with:

- Show Fairy
- Hide Fairy
- Open Chat
- Quit NeuroFairy

The menu must remain usable while the Fairy is hidden. Quit closes both popovers and the
Fairy, then exits the event loop. `aboutToQuit` invokes `backend.shutdown()`; the ownership
rule remains inside the backend controller.

### Step 2: verify normal and hostile paths

1. Run `uv run fairy-desktop`, wait for `Ready to help`, send a chat, and quit from the
   menu. Confirm the owned child exits.
2. Start `uv run uvicorn fairy.web_app:app --reload` separately on port 8000, then start
   the desktop app. Confirm both work independently and desktop Quit leaves manual Uvicorn
   running.
3. Confirm a missing or forged handshake never reaches ready state.
4. Confirm requests without the per-launch token receive HTTP 401 and do not call the AI
   service.
5. Stop the desktop child while a chat request is pending; confirm that request is aborted,
   later chat attempts are disabled, and the app shows an unavailable state.
6. Quit while the authenticated health probe is pending; confirm a late reply cannot return
   the controller to ready or restore the client URL and token.

### Full verification

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest
git diff --check
uv run fairy-desktop
```

Suggested commit message:

```text
feat: add desktop fairy menu and safe shutdown
```

Stop and report the automated results and manual lifecycle checks.

### Full-file recovery checkpoint

Use the [Session 4 complete files and expected output](checkpoints/stage-2-session-4.md) if
you get stuck. It links every final Stage 2 file and the expected terminal and visible
output.

---

## Stage acceptance criteria

Stage 2 is complete only when:

- The Fairy runs from `uv run fairy-desktop`.
- The placeholder stays on top and remains visible.
- Idle and hover states do not steal keyboard focus.
- The chat popover intentionally accepts focus and is keyboard navigable.
- Clicking and dragging are reliably distinguished.
- Position restoration cannot strand the Fairy on a disconnected display.
- Hover status is delayed, short, and honest.
- Desktop chat uses the existing `/api/chat` route.
- Network failure does not freeze or crash the GUI.
- The desktop app enables chat only after its owned child proves knowledge of the
  per-launch credential and passes an authenticated health check.
- A missing or forged proof never enables chat, and missing or incorrect API credentials
  never reach the AI service.
- The desktop does not reuse an arbitrary service on port 8000.
- It stops only a backend process it started.
- A menu-bar path can show, hide, open chat, and quit.
- Deterministic geometry, protocol, health, and existing repository tests pass.
- Ruff lint and formatting pass.
- No final art or later-stage product behavior was inferred.

---

## Complete Stage 2 recovery snapshot

The [Stage 2 final recovery snapshot](checkpoints/stage-2-final.md) maps every final source,
test, and configuration path to a complete copy-ready file and lists the final expected
terminal and product output. Use it to recover from a missed edit; do not skip the smaller
session explanations unless you are debugging.

---

## Common errors and debugging

| Symptom | Responsible boundary | Smallest inspection step |
|---|---|---|
| Fairy steals focus while idle | Window/accessory policy | Inspect Qt flags and when the Cocoa policy is applied |
| Chat input cannot receive focus | Popover window flags | Confirm chat does not inherit `WindowDoesNotAcceptFocus` |
| Click moves the Fairy | Pointer threshold | Log movement versus `startDragDistance()` |
| Fairy vanishes after monitor change | Position restoration | Test clamp function with the current available geometry |
| Hover flashes while passing over | Hover timer | Confirm single-shot delay is cancelled on leave |
| UI freezes while sending | Network boundary | Confirm Qt async network APIs are used on the GUI thread |
| HTTP 422 | Request schema | Inspect JSON for the `message` field |
| Calm fallback appears for every chat | API/model boundary | Inspect Uvicorn output, then run `ollama list` |
| Port 8000 is occupied | Browser-development runtime | Leave it alone; desktop uses its own OS-assigned port |
| Desktop never becomes ready | Authenticated startup | Run the handshake tests, then inspect only child stderr for a startup error |
| HTTP 401 from desktop child | Per-launch credential | Confirm the client was configured only from the verified ready signal |
| Backend remains after app-owned quit | Process ownership | Confirm the saved `QProcess` is terminated on app exit |
| Manual Uvicorn stops on quit | Process ownership bug | The desktop must terminate only its stored child process |

Debug one boundary at a time: window behavior, gesture handling, API transport, backend
process, or model availability.

---

## Portfolio evidence

After this stage, you can truthfully demonstrate:

- A Mac-first Python desktop companion built with PySide6 and a narrow PyObjC bridge
- Careful focus behavior for an always-reachable assistive interface
- Tested multi-monitor geometry and preference restoration
- Asynchronous desktop-to-FastAPI communication
- Reuse of one FastAPI/AI application boundary across browser and desktop surfaces
- Authenticated local-process ownership and recovery behavior
- Accessible neutral placeholders that keep final visual design replaceable

Record a short demo only after the stage acceptance checklist passes. Show drag, hover,
click-to-chat, a local reply, hide/show, and quit. Describe the placeholder as temporary.

---

## Reflection

Write short answers in your own notes:

1. Why must the idle Fairy and chat popover use different focus rules?
2. Why does the desktop app call FastAPI instead of importing the model service?
3. What makes position restoration a correctness problem rather than a cosmetic detail?
4. Why is `QNetworkAccessManager` safer for this UI than a blocking request?
5. How does the app know whether it may stop the backend process?
6. Which hover statuses would be dishonest before Stages 3 and 5 exist?
7. Why is binding to `127.0.0.1` not enough to prove which local process receives chat?

---

Next after Stage 2: **Stage 3 — Internal tasks and next actions**, where the browser,
desktop Fairy, FastAPI routes, and optional MCP clients begin using one shared task service.
