# Stage 3 — The desktop fairy

> **By the end of this stage** a fairy floats on your desktop showing your real focus
> timer, and she never steals your cursor while you type.

**Sessions:** 4 · **Time:** ~3 weeks

### What you'll learn

| Concept | Where |
|---|---|
| GUI event loops — how a desktop app actually runs | Session 1 |
| Window flags, transparency, and macOS activation policy | Session 1 |
| Mouse events and gesture thresholds | Session 2 |
| `QTimer` — doing things on a schedule | Session 3 |
| Sharing state between two processes through a database | Session 3 |
| System tray applications | Session 4 |

### Install what you need

```bash
cd ~/code/fairy && uv add PySide6 "pyobjc-framework-Cocoa; sys_platform == 'darwin'"
```

**What that second string means.** `"pyobjc-framework-Cocoa; sys_platform == 'darwin'"` is
a *conditional dependency* — install it only on macOS. Someone running your project on
Linux skips it entirely, and the code guards the import so nothing breaks.

Copy the artwork across:

```bash
mkdir -p ~/code/fairy/assets && cp ~/Desktop/adhdfairy/ADHD_Fairy_Final_Handoff/assets/*.png ~/code/fairy/assets/ && ls ~/code/fairy/assets/
```

---

## Session 1 — Get her on screen

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** a transparent, always-on-top fairy that doesn't steal focus.

**This code is verified working** on macOS 26.5 with PySide6 6.11.2 — it was run with your
actual `fairy-full.png` before this guide was written.

### The thing that isn't in any documentation

Qt's documented flags are **not enough** on macOS.

- Every forum post recommends `FramelessWindowHint | WindowStaysOnTopHint |
  WindowDoesNotAcceptFocus | Qt.Tool` plus `WA_ShowWithoutActivating`
- Tested on your machine: the window **still stole keyboard focus**

The fix isn't a Qt setting at all. You have to tell macOS the process is an *accessory*
app, which is what `LSUIElement` does for a bundled app:

```python
if sys.platform == "darwin":
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )
```

With that line: focus is never stolen, there's no Dock icon, and she doesn't appear in
`Cmd+Tab`. Without it, none of those are true.

Create the folder and file:

```bash
mkdir -p ~/code/fairy/fairy_desktop && touch ~/code/fairy/fairy_desktop/__init__.py
```

`fairy_desktop/fairy.py`:

```python
"""The floating desktop fairy."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

ASSETS = Path(__file__).parent.parent / "assets"
FAIRY_HEIGHT = 140


def _become_accessory_app() -> None:
    """macOS: never activate, no Dock icon, no Cmd-Tab entry."""
    if sys.platform != "darwin":
        return
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )


class Fairy(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        pixmap = QPixmap(str(ASSETS / "fairy-full.png"))
        if pixmap.isNull():
            raise SystemExit(f"could not load fairy art from {ASSETS}")
        pixmap = pixmap.scaledToHeight(FAIRY_HEIGHT, Qt.SmoothTransformation)

        label = QLabel()
        label.setPixmap(pixmap)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)


def main() -> None:
    app = QApplication(sys.argv)
    _become_accessory_app()

    fairy = Fairy()
    screen = app.primaryScreen().availableGeometry()
    fairy.move(screen.right() - 200, screen.bottom() - 260)
    fairy.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

### Understanding a GUI application

Everything you've written so far runs top to bottom and exits. A GUI app is different:

```python
app = QApplication(sys.argv)   # 1. create the application
fairy = Fairy()                # 2. build your windows
fairy.show()                   # 3. show them
sys.exit(app.exec())           # 4. hand control to the event loop
```

`app.exec()` **does not return** until the app quits.

- It's a loop waiting for events — clicks, mouse moves, timers
- When one arrives, it calls your code
- This is why GUI code is *methods that get called*, not a script that runs top to bottom

### Understanding the window flags

| Flag | Effect |
|---|---|
| `FramelessWindowHint` | No title bar, no border, no close button |
| `WindowStaysOnTopHint` | Floats above other windows |
| `WindowDoesNotAcceptFocus` | Clicking her doesn't move keyboard focus |
| `Qt.Tool` | A utility window — not a main app window |
| `WA_TranslucentBackground` | Transparent where the PNG's alpha is transparent |
| `WA_ShowWithoutActivating` | Showing her doesn't bring the app forward |

They're combined with `|` (bitwise OR) because each is a single bit in a number. That's a
very common pattern in GUI and systems code.

### Understanding `__init__` and `super()`

```python
class Fairy(QWidget):
    def __init__(self) -> None:
        super().__init__()
```

- `__init__` runs when you create the object
- `super().__init__()` runs the parent's setup first — here, all of `QWidget`'s machinery
- Forget it and you get confusing crashes: you'd be configuring a widget that was never built

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -m fairy_desktop.fairy
```

Check all four, deliberately:

1. **Transparent** — no white box around her
2. **On top** — she stays above VS Code
3. **Doesn't steal focus** — click VS Code, type, keep typing while she's visible
4. **Not in `Cmd+Tab`** — hold `Cmd`, press `Tab`, she's absent

`Ctrl-C` in the terminal to quit (there's no close button yet — that's Session 4).

### ⚠ If it breaks

| Error | Fix |
|---|---|
| `could not load fairy art from ...` | The asset copy didn't work. `ls ~/code/fairy/assets/` |
| White box around the fairy | `WA_TranslucentBackground` missing, or the PNG has no alpha |
| She steals focus | `_become_accessory_app()` is missing or called **after** `QApplication` was created — order matters |
| `ModuleNotFoundError: AppKit` | `uv add "pyobjc-framework-Cocoa; sys_platform == 'darwin'"` |
| Nothing appears at all | She may be off-screen. Try `fairy.move(400, 400)` |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: floating desktop fairy" && git push
```


---

## Session 2 — Drag, snap, remember

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** make her feel like a real desktop object.

Three behaviours, ported from the original Swift `FairyWindowController`.

### Drag with a threshold

```python
def mousePressEvent(self, event):
    self._press_pos = event.globalPosition().toPoint()
    self._origin = self.pos()
    self._moved = False

def mouseMoveEvent(self, event):
    delta = event.globalPosition().toPoint() - self._press_pos
    if delta.manhattanLength() > 5:
        self._moved = True
    if self._moved:
        self.move(self._origin + delta)

def mouseReleaseEvent(self, event):
    if self._moved:
        self._snap_to_edge()
        self._save_position()
    else:
        self._on_click()
```

**Why the 5-pixel threshold:** a human click always includes a pixel or two of movement.
Without it, every click nudges her sideways. Under 5px = click, over = drag.

`manhattanLength()` is `abs(dx) + abs(dy)` — cheaper than real distance and fine here.

**You never call these yourself.** Qt's event loop calls them when the mouse moves.
Overriding methods the framework calls is the core pattern of GUI programming.

### Snap to the nearest edge

On release, find which screen she's on and move her to the nearer side:

```python
screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
area = screen.availableGeometry()
```

`availableGeometry()` excludes the menu bar and Dock, so she won't hide underneath them.
Use `screenAt()` rather than assuming the primary screen — people have monitors.

### Remember where she was

Save to `~/.fairy/desktop.json`: x, y, and the screen name.

On launch, **clamp the saved position back onto a screen that still exists.** Monitors get
unplugged, and a fairy restored to coordinates on a screen that's gone is invisible with no
way to get her back. Always validate restored geometry.

### ✔ Check yourself

```bash
cd ~/code/fairy && uv run python -m fairy_desktop.fairy
```

1. **Click her without moving** — she should not shift position
2. **Drag her to the left edge** — on release she snaps flush to the side
3. **Quit (`Ctrl-C`) and relaunch** — she reappears where you left her

```bash
cat ~/.fairy/desktop.json
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| She jumps on every click | Threshold missing, or you moved her before `_moved` was set |
| She snaps off-screen | Using `geometry()` instead of `availableGeometry()` |
| Position not remembered | `_save_position` never called, or the JSON write failed silently |
| She vanishes after unplugging a monitor | You didn't clamp the restored position onto a current screen |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: fairy drag, edge snapping, and saved position" && git push
```


---

## Session 3 — Show the real timer

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** connect her to Stage 2's engine. This is where the architecture pays off.

She reads the **same SQLite database** the MCP server writes to. No HTTP, no ports, no
server, no authentication — that's the benefit of choosing shared storage as the
integration point.

### The naive approach, and why not to use it

You could read the database every second. That's 86,400 queries a day and makes your logs
useless.

You don't need to, because **your timer engine is pure**:

```python
# Sync with the database every 30 seconds...
self._sync_timer = QTimer(self)
self._sync_timer.timeout.connect(self._reload_from_db)
self._sync_timer.start(30_000)

# ...but tick locally every second for a smooth countdown.
self._tick_timer = QTimer(self)
self._tick_timer.timeout.connect(self._tick)
self._tick_timer.start(1_000)

def _tick(self) -> None:
    now_ms = int(time.time() * 1000)
    self._state = bloom.tick(self._state, now_ms)
    self._label.setText(self._format_remaining())
```

**Why this works:** `bloom.tick(state, now_ms)` takes time as a parameter, so the fairy runs
the same engine locally between syncs.

- Smooth display
- ~2,900 database reads a day instead of 86,400
- Keeps counting even if the MCP server isn't running

That is the concrete payoff of the purity rule from Stage 2. The same function runs in your
tests, in the MCP server, and in the GUI — with no modification.

### Understanding signals and slots

```python
self._tick_timer.timeout.connect(self._tick)
```

`timeout` is a **signal** — something Qt emits when the timer fires. `connect` says "when
that happens, call this function." It's how everything in Qt communicates: buttons emit
`clicked`, timers emit `timeout`, and you connect them to your own methods.

Display the time remaining and the growth stage underneath her.

### ✔ Check yourself

With the fairy running, ask Claude Desktop: *"start a 25 minute focus session"*.

Within 30 seconds her label should start counting down — and then tick every second.

```bash
sqlite3 ~/.fairy/fairy.db "SELECT phase, remaining_ms FROM focus_state;"
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| `database is locked` | `PRAGMA journal_mode=WAL` missing from `connect()` |
| Label never updates | `timeout.connect(...)` not wired, or `start()` never called on the QTimer |
| Countdown jumps around | You're re-reading the database every tick instead of ticking locally |
| Time is wrong after sleep | You're storing elapsed time instead of `anchor_ms` — let `bloom.tick` do the maths |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: fairy shows live focus timer from shared database" && git push
```


---

## Session 4 — Peek, menu bar, and quick capture

### ▶ Start this session

```bash
cd ~/code/fairy && git pull && uv sync
```

**Goal:** finish her, and give yourself a way to quit.

### Hover peek

After a 650 ms delay (matching the original design), show a small panel with the current
task and time left:

```python
self._hover_timer = QTimer(self)
self._hover_timer.setSingleShot(True)
self._hover_timer.timeout.connect(self._show_peek)

def enterEvent(self, event):
    self._hover_timer.start(650)

def leaveEvent(self, event):
    self._hover_timer.stop()
    self._hide_peek()
```

**Why delay, then cancel:**
- Without a delay, the peek flashes whenever your cursor crosses her
- `setSingleShot(True)` fires once instead of repeating
- `leaveEvent` cancels it if you move away first

Delay-then-cancel is the standard pattern for any hover UI.

### Menu bar icon

`QSystemTrayIcon` with a menu: Show/Hide Fairy · Start Focus · Pause · Quit.

**This is how you quit her.** An accessory app has no Dock icon to right-click, so without
a tray menu your only option is `Ctrl-C` in a terminal. Build this before you get annoyed.

### Click to capture

Clicking opens a small always-on-top input. Type a thought, press Enter, it goes straight
into your `tasks` table via `tasks.add_task`.

**This is the feature you will use most.** It's the entire reason the fairy exists — a
thought arrives, you get it out of your head in two seconds without changing windows.

Register the command in `pyproject.toml`:

```toml
[project.scripts]
fairy-tasks = "fairy.servers.tasks_server:main"
fairy-timer = "fairy.servers.timer_server:main"
fairy-desktop = "fairy_desktop.fairy:main"
```

```bash
cd ~/code/fairy && uv sync && uv run fairy-desktop
```

### ✔ Check yourself

1. **Hover** over her for a second — the peek appears; move away quickly and it doesn't
2. **Menu bar icon** — the menu opens and Quit actually quits
3. **Click her**, type "test thought", press Enter

```bash
sqlite3 ~/.fairy/fairy.db "SELECT id, title FROM tasks ORDER BY id DESC LIMIT 1;"
```

### ⚠ If it breaks

| Symptom | Cause |
|---|---|
| Peek flashes constantly | `leaveEvent` isn't stopping the timer |
| Peek never appears | `setSingleShot(True)` missing, or the timer is restarted every mouse-move |
| No menu bar icon | `QSystemTrayIcon` needs an icon set before `show()` |
| Capture window steals focus | It *should* take focus — it's a text field. Only the fairy herself must not |

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "feat: hover peek, menu bar, and quick capture" && git push
```


---

## ✅ Stage 3 complete

**You built:** a native desktop companion in pure Python, sharing state with your MCP
servers through SQLite.

**You learned:**

- GUI **event loops** and why GUI code is callback-shaped
- Window flags, transparency, and macOS **activation policy**
- Gesture **thresholds** — the difference between a click and a drag
- `QTimer`, **signals and slots**
- Running pure domain logic in two processes at once

### 📹 Record a GIF here

Ten seconds: fairy floating, timer ticking, quick capture catching a thought. **Put it at
the top of your README.** Most portfolio projects are a REST API and a dashboard. Yours has
a pixel fairy on the desktop — that is what people will remember.

```bash
cd ~/code/fairy && open -a "QuickTime Player"
```

File → New Screen Recording → record a region around her → export → drag into your repo as
`docs/fairy.gif`.

### 📝 Write your first decision note

`docs/decisions/001-pyside6-over-swift.md`. Cover: the options (Swift, PyObjC, Tkinter,
PySide6), what you chose, and **the accessory-policy experiment** — the documented flags
failed, and here's what actually fixed it.

A decision record with a real experiment behind it is worth more than three opinionated
ones, and interviewers ask about exactly this kind of thing.

### ■ Finish this session

Verify everything is clean:

```bash
cd ~/code/fairy && uv run ruff check . && uv run ruff format . && uv run pytest
```

Then commit and push:

```bash
cd ~/code/fairy && git add -A && git commit -m "docs: add decision note on PySide6 and record demo GIF" && git push
```


---

Next: [Stage 4 — Real integrations](stage-4-connectors.md)
