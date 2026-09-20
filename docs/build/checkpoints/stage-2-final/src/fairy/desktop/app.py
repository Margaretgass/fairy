"""Application entry point for the desktop Fairy."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

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


def make_placeholder_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#343A40"))
    painter.setPen(QColor("#FFFFFF"))
    painter.drawEllipse(1, 1, 30, 30)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "F")
    painter.end()
    return QIcon(pixmap)


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    become_accessory_app()

    api = ApiClient(app)
    backend = BackendController(api, app)
    fairy = FairyWindow()
    status = StatusPopover()
    chat = ChatPopover(api)
    hover_timer = QTimer(app)
    hover_timer.setSingleShot(True)
    hover_timer.setInterval(HOVER_DELAY_MS)

    tray = QSystemTrayIcon(make_placeholder_icon(), app)
    tray.setToolTip("NeuroFairy")
    menu = QMenu()
    show_action = QAction("Show Fairy", menu)
    hide_action = QAction("Hide Fairy", menu)
    chat_action = QAction("Open Chat", menu)
    quit_action = QAction("Quit NeuroFairy", menu)
    menu.addActions([show_action, hide_action, chat_action])
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

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

    def open_chat(_checked: bool = False) -> None:
        activate_for_chat()
        chat.open_near(fairy.frameGeometry())

    def update_thinking(thinking: bool) -> None:
        if thinking and status.isVisible():
            status.set_message("Thinking locally…")
        elif status.isVisible():
            status.set_message(current_status())

    def quit_app(_checked: bool = False) -> None:
        chat.close()
        status.close()
        fairy.close()
        app.quit()

    hover_timer.timeout.connect(show_status)
    fairy.hover_started.connect(hover_timer.start)
    fairy.hover_ended.connect(hide_status)
    fairy.clicked.connect(open_chat)
    backend.ready_changed.connect(refresh_status)
    backend.state_changed.connect(refresh_status)
    backend.error_changed.connect(show_backend_error)
    chat.thinking_changed.connect(update_thinking)
    show_action.triggered.connect(lambda _checked=False: fairy.show())
    hide_action.triggered.connect(lambda _checked=False: fairy.hide())
    chat_action.triggered.connect(open_chat)
    quit_action.triggered.connect(quit_app)
    app.aboutToQuit.connect(backend.shutdown)

    tray.show()
    fairy.show()
    QTimer.singleShot(0, backend.start)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
