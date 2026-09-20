# Stage 2 · Session 1 recovery checkpoint

[← Back to Stage 2 instructions](../README.md)

> **Use only if stuck.** This is a recovery reference, not another lesson to complete.

Use this only after attempting Session 1 in the main lesson. These are the complete files
created or changed by the session.

`uv add` may record newer minimum dependency versions than the version-neutral entries
shown below. Keep the compatible constraints written by `uv`; the package names, marker,
script, and remaining file content should match.

## `pyproject.toml`

```toml
[project]
name = "fairy"
version = "0.1.0"
description = "A local-first ADHD companion: MCP tools, a focus timer, and a desktop fairy."
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.141.1",
    "fastmcp>=4.0.5",
    "langchain>=1.4.2",
    "langchain-ollama>=1.1.0",
    "PySide6",
    "pyobjc-framework-Cocoa; sys_platform == 'darwin'",
    "uvicorn[standard]>=0.53.0",
]

[project.scripts]
fairy-tasks = "fairy.servers.tasks_server:main"
fairy-desktop = "fairy.desktop.app:main"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.16",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/fairy"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]
# Tutorial code blocks are illustrative: aligned comments aid reading, and some
# snippets are deliberately incomplete. Don't reformat them.
extend-exclude = ["docs"]

[tool.ruff.lint]
# E/W pycodestyle, F pyflakes, I import sorting, UP modern syntax, B common bugs
select = ["E", "W", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"
```

## `src/fairy/desktop/__init__.py`

```python
"""Desktop companion surfaces for NeuroFairy."""
```

## `src/fairy/desktop/window.py`

```python
"""The neutral floating Fairy window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

PLACEHOLDER_SIZE = 72
PLACEHOLDER_BACKGROUND = "#343A40"
PLACEHOLDER_FOREGROUND = "#FFFFFF"
SCREEN_MARGIN = 24


class FairyWindow(QWidget):
    """Small non-activating desktop entry point."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NeuroFairy")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(PLACEHOLDER_SIZE, PLACEHOLDER_SIZE)
        self.setAccessibleName("Open NeuroFairy")
        self.setToolTip("Open NeuroFairy chat")

        label = QLabel("F")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAccessibleName("Open NeuroFairy")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label.setStyleSheet(
            f"background: {PLACEHOLDER_BACKGROUND};"
            f"color: {PLACEHOLDER_FOREGROUND};"
            f"border-radius: {PLACEHOLDER_SIZE // 2}px;"
            "font-size: 22px; font-weight: 600;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)

        screen = QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(
                area.x() + area.width() - self.width() - SCREEN_MARGIN,
                area.y() + area.height() - self.height() - SCREEN_MARGIN,
            )
```

## `src/fairy/desktop/app.py`

```python
"""Application entry point for the desktop Fairy."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from fairy.desktop.window import FairyWindow


def become_accessory_app() -> None:
    """Use macOS accessory behavior without affecting other platforms."""
    if sys.platform != "darwin":
        return

    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)


def main() -> None:
    app = QApplication(sys.argv)
    become_accessory_app()

    fairy = FairyWindow()
    fairy.show()

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
```

## Expected commands and output

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest
uv run fairy-desktop
```

Representative terminal result before the GUI command:

```text
25 files left unchanged
All checks passed!
============================== 13 passed in ... ==============================
```

The file count and duration can vary. `uv run fairy-desktop` normally stays quiet and does
not return until the app exits.

Expected visible result:

- A neutral circular `F` appears near the lower-right usable edge of the primary screen.
- The surrounding window is transparent.
- The Fairy remains above normal windows.
- It does not appear in `Cmd+Tab` and does not interrupt typing in another app.
- VoiceOver announces `Open NeuroFairy`.
