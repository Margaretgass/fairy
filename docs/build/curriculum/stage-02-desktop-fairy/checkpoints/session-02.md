# Stage 2 · Session 2 recovery checkpoint

[← Back to Stage 2 instructions](../README.md)

> **Use only if stuck.** This is a recovery reference, not another lesson to complete.

These are the complete files created or changed by Session 2. Files not listed remain as
shown in the Session 1 checkpoint.

## `src/fairy/desktop/geometry.py`

```python
"""Pure geometry rules for the desktop Fairy."""

from __future__ import annotations

from dataclasses import dataclass


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


def clamp_position(position: Point, window: Rect, available: Rect) -> Point:
    """Return a top-left position that keeps the window in the available area."""
    max_x = max(available.x, available.x + available.width - window.width)
    max_y = max(available.y, available.y + available.height - window.height)
    return Point(
        x=min(max(position.x, available.x), max_x),
        y=min(max(position.y, available.y), max_y),
    )


def snap_to_nearest_side(position: Point, window: Rect, available: Rect) -> Point:
    """Clamp a position, then move it to the nearer horizontal screen edge."""
    clamped = clamp_position(position, window, available)
    left_x = available.x
    right_x = max(available.x, available.x + available.width - window.width)
    distance_to_left = abs(clamped.x - left_x)
    distance_to_right = abs(right_x - clamped.x)
    snapped_x = left_x if distance_to_left <= distance_to_right else right_x
    return Point(snapped_x, clamped.y)
```

## `src/fairy/desktop/window.py`

```python
"""The neutral floating Fairy window."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from fairy.desktop.geometry import Point, Rect, clamp_position, snap_to_nearest_side

PLACEHOLDER_SIZE = 72
PLACEHOLDER_BACKGROUND = "#343A40"
PLACEHOLDER_FOREGROUND = "#FFFFFF"
SCREEN_MARGIN = 24


def _rect_value(rect) -> Rect:
    return Rect(rect.x(), rect.y(), rect.width(), rect.height())


class FairyWindow(QWidget):
    """Small non-activating desktop entry point."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("NeuroFairy", "Desktop")
        self._press_global: QPoint | None = None
        self._window_origin: QPoint | None = None
        self._dragging = False

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
        self._restore_position()

    def _window_rect(self) -> Rect:
        return Rect(0, 0, self.width(), self.height())

    def _restore_position(self) -> None:
        screens = {screen.name(): screen for screen in QApplication.screens()}
        saved_name = self._settings.value("screen", "", type=str)
        screen = screens.get(saved_name) or QApplication.primaryScreen()
        if screen is None:
            return

        available = _rect_value(screen.availableGeometry())
        default = Point(
            available.x + available.width - self.width() - SCREEN_MARGIN,
            available.y + available.height - self.height() - SCREEN_MARGIN,
        )
        saved = Point(
            self._settings.value("x", default.x, type=int),
            self._settings.value("y", default.y, type=int),
        )
        restored = clamp_position(saved, self._window_rect(), available)
        self.move(restored.x, restored.y)

    def _save_position(self, screen_name: str) -> None:
        self._settings.setValue("x", self.x())
        self._settings.setValue("y", self.y())
        self._settings.setValue("screen", screen_name)

    def _snap_and_save(self) -> None:
        screen = QApplication.screenAt(self.frameGeometry().center())
        screen = screen or QApplication.primaryScreen()
        if screen is None:
            return

        snapped = snap_to_nearest_side(
            Point(self.x(), self.y()),
            self._window_rect(),
            _rect_value(screen.availableGeometry()),
        )
        self.move(snapped.x, snapped.y)
        self._save_position(screen.name())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        self._press_global = event.globalPosition().toPoint()
        self._window_origin = self.pos()
        self._dragging = False
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._press_global is None or self._window_origin is None:
            return super().mouseMoveEvent(event)
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return

        delta = event.globalPosition().toPoint() - self._press_global
        if delta.manhattanLength() >= QApplication.startDragDistance():
            self._dragging = True
        if self._dragging:
            self.move(self._window_origin + delta)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mouseReleaseEvent(event)
        if self._dragging:
            self._snap_and_save()
        self._press_global = None
        self._window_origin = None
        self._dragging = False
        event.accept()
```

## `tests/test_desktop_geometry.py`

```python
from fairy.desktop.geometry import Point, Rect, clamp_position, snap_to_nearest_side

WINDOW = Rect(0, 0, 72, 72)
SCREEN = Rect(0, 0, 1440, 900)


def test_clamp_keeps_visible_position_unchanged():
    assert clamp_position(Point(100, 200), WINDOW, SCREEN) == Point(100, 200)


def test_clamp_moves_position_inside_right_and_bottom_edges():
    assert clamp_position(Point(2000, 1000), WINDOW, SCREEN) == Point(1368, 828)


def test_clamp_moves_negative_position_inside_top_left():
    assert clamp_position(Point(-20, -50), WINDOW, SCREEN) == Point(0, 0)


def test_clamp_handles_window_larger_than_available_area():
    window = Rect(0, 0, 500, 500)
    available = Rect(100, 200, 300, 250)
    assert clamp_position(Point(900, 900), window, available) == Point(100, 200)


def test_snap_chooses_left_edge_when_left_is_nearer():
    assert snap_to_nearest_side(Point(200, 300), WINDOW, SCREEN) == Point(0, 300)


def test_snap_chooses_right_edge_when_right_is_nearer():
    assert snap_to_nearest_side(Point(1200, 300), WINDOW, SCREEN) == Point(1368, 300)


def test_snap_tie_is_stable_on_left_edge():
    midpoint = (SCREEN.width - WINDOW.width) // 2
    assert snap_to_nearest_side(Point(midpoint, 300), WINDOW, SCREEN) == Point(0, 300)
```

## Expected commands and output

First, before creating `geometry.py`:

```bash
uv run pytest tests/test_desktop_geometry.py
```

Expected red result:

```text
E   ModuleNotFoundError: No module named 'fairy.desktop.geometry'
=========================== 1 error in ... ====================================
```

After adding the complete files above:

```bash
uv run pytest tests/test_desktop_geometry.py
uv run pytest
uv run fairy-desktop
```

Expected result:

```text
============================== 7 passed in ... ===============================
============================== 20 passed in ... ==============================
```

Durations can vary. The GUI command normally remains quiet.

Expected visible result:

- Movement smaller than the system drag threshold behaves like a click and does not move
  the Fairy.
- A real drag follows the pointer and snaps to the nearer horizontal screen edge.
- Relaunch restores a visible position.
- If the saved display is unavailable, the Fairy returns to the primary screen.
