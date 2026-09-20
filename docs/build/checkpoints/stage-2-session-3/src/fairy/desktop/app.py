"""Application entry point for the desktop Fairy before the menu-bar session."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from fairy.desktop.api_client import ApiClient
from fairy.desktop.backend import BackendController
from fairy.desktop.chat_popover import ChatPopover
from fairy.desktop.status_popover import StatusPopover
from fairy.desktop.window import FairyWindow

HOVER_DELAY_MS = 650


def become_accessory_app() -> None:
    if sys.platform != "darwin":
        return
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)


def activate_for_chat() -> None:
    if sys.platform != "darwin":
        return
    from AppKit import NSApplication

    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)


def main() -> None:
    app = QApplication(sys.argv)
    become_accessory_app()

    api = ApiClient(app)
    backend = BackendController(api, app)
    fairy = FairyWindow()
    status = StatusPopover()
    chat = ChatPopover(api)
    hover_timer = QTimer(app)
    hover_timer.setSingleShot(True)
    hover_timer.setInterval(HOVER_DELAY_MS)

    def current_status() -> str:
        if backend.is_ready:
            return "Ready to help"
        if backend.state == "starting":
            return "Starting local service…"
        if backend.state == "failed":
            return "Local service unavailable"
        return "Checking local service…"

    def show_status() -> None:
        status.set_message(current_status())
        status.show_near(fairy.frameGeometry())

    def hide_status() -> None:
        hover_timer.stop()
        status.hide()

    def refresh_status(_value=None) -> None:
        if status.isVisible():
            status.set_message(current_status())

    def show_backend_error(message: str) -> None:
        if status.isVisible():
            status.set_message(message)

    def open_chat() -> None:
        activate_for_chat()
        chat.open_near(fairy.frameGeometry())

    def update_thinking(thinking: bool) -> None:
        if thinking and status.isVisible():
            status.set_message("Thinking locally…")
        elif status.isVisible():
            status.set_message(current_status())

    hover_timer.timeout.connect(show_status)
    fairy.hover_started.connect(hover_timer.start)
    fairy.hover_ended.connect(hide_status)
    fairy.clicked.connect(open_chat)
    backend.ready_changed.connect(refresh_status)
    backend.state_changed.connect(refresh_status)
    backend.error_changed.connect(show_backend_error)
    chat.thinking_changed.connect(update_thinking)
    app.aboutToQuit.connect(backend.shutdown)

    fairy.show()
    QTimer.singleShot(0, backend.start)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
