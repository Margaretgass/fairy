"""The neutral floating Fairy window."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSettings, Qt, Signal
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
    clicked = Signal()
    hover_started = Signal()
    hover_ended = Signal()

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

    def enterEvent(self, event) -> None:
        self.hover_started.emit()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.hover_ended.emit()
        super().leaveEvent(event)

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
        else:
            self.clicked.emit()
        self._press_global = None
        self._window_origin = None
        self._dragging = False
        event.accept()
