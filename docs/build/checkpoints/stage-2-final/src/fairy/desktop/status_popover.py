"""Non-activating hover status for the desktop Fairy."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

POPOVER_WIDTH = 220
POPOVER_GAP = 10


class StatusPopover(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAccessibleName("NeuroFairy status")
        self.setFixedWidth(POPOVER_WIDTH)

        self._label = QLabel("Checking local service…")
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            "background: #343A40; color: #FFFFFF; border-radius: 8px; padding: 10px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

    def set_message(self, message: str) -> None:
        self._label.setText(message)
        self.adjustSize()

    def show_near(self, anchor: QRect) -> None:
        self.adjustSize()
        screen = QApplication.screenAt(anchor.center()) or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        right_x = anchor.right() + POPOVER_GAP
        left_x = anchor.left() - self.width() - POPOVER_GAP
        x = right_x if right_x + self.width() <= area.right() else left_x
        x = min(max(x, area.left()), area.right() - self.width() + 1)
        y = min(max(anchor.top(), area.top()), area.bottom() - self.height() + 1)
        self.move(x, y)
        self.show()
