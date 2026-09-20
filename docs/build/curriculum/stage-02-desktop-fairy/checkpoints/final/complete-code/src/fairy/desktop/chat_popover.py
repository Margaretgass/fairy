"""Keyboard-accessible chat popover for the desktop Fairy."""

from __future__ import annotations

import html

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from fairy.desktop.api_client import ApiClient

POPOVER_WIDTH = 360
POPOVER_HEIGHT = 420
POPOVER_GAP = 12


class ChatPopover(QWidget):
    thinking_changed = Signal(bool)

    def __init__(self, api: ApiClient) -> None:
        super().__init__()
        self._api = api
        self.setWindowTitle("Chat with NeuroFairy")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(POPOVER_WIDTH, POPOVER_HEIGHT)
        self.setAccessibleName("NeuroFairy chat")

        self._transcript = QTextBrowser()
        self._transcript.setAccessibleName("Conversation")
        self._input = QPlainTextEdit()
        self._input.setAccessibleName("Message")
        self._input.setPlaceholderText("What would help right now?")
        self._input.setMaximumHeight(90)
        self._status = QLabel("")
        self._status.setAccessibleName("Chat status")
        self._send = QPushButton("Send")
        self._send.setAccessibleName("Send message")

        layout = QVBoxLayout(self)
        layout.addWidget(self._transcript)
        layout.addWidget(self._input)
        layout.addWidget(self._status)
        layout.addWidget(self._send)

        self._send.clicked.connect(self._submit)
        self._api.chat_succeeded.connect(self._show_reply)
        self._api.chat_failed.connect(self._show_error)

    def open_near(self, anchor: QRect) -> None:
        screen = QApplication.screenAt(anchor.center()) or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            right_x = anchor.right() + POPOVER_GAP
            left_x = anchor.left() - self.width() - POPOVER_GAP
            x = right_x if right_x + self.width() <= area.right() else left_x
            x = min(max(x, area.left()), area.right() - self.width() + 1)
            y = min(max(anchor.top(), area.top()), area.bottom() - self.height() + 1)
            self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus(Qt.FocusReason.MouseFocusReason)

    def _submit(self) -> None:
        message = self._input.toPlainText().strip()
        if not message or not self._send.isEnabled():
            return
        self._transcript.append(f"<b>You:</b> {html.escape(message)}")
        self._input.clear()
        self._set_busy(True)
        self._api.send_chat(message)

    def _show_reply(self, message: str) -> None:
        self._transcript.append(f"<b>Fairy:</b> {html.escape(message)}")
        self._set_busy(False)

    def _show_error(self, message: str) -> None:
        self._status.setText(message)
        self._set_busy(False, clear_status=False)

    def _set_busy(self, busy: bool, *, clear_status: bool = True) -> None:
        self._send.setEnabled(not busy)
        self._input.setEnabled(not busy)
        if clear_status:
            self._status.setText("Thinking locally…" if busy else "")
        self.thinking_changed.emit(busy)
        if not busy:
            self._input.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)
