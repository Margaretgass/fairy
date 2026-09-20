"""Lifecycle manager for the authenticated, desktop-owned FastAPI process."""

from __future__ import annotations

import secrets
import sys

from PySide6.QtCore import QByteArray, QElapsedTimer, QObject, QProcess, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from fairy.desktop.api_client import TOKEN_HEADER, ApiClient, decode_health
from fairy.desktop.backend_protocol import (
    BackendHandshakeError,
    BackendSession,
    BackendState,
    decode_backend_handshake,
)

STARTUP_TIMEOUT_MS = 10_000
POLL_INTERVAL_MS = 100


class BackendController(QObject):
    ready_changed = Signal(bool)
    state_changed = Signal(str)
    error_changed = Signal(str)

    def __init__(self, api: ApiClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._api = api
        self._network = QNetworkAccessManager(self)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self._process.started.connect(self._send_session_token)
        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._drain_stderr)
        self._process.errorOccurred.connect(self._process_error)
        self._process.finished.connect(self._process_finished)
        self._deadline = QElapsedTimer()
        self._session = BackendSession()
        self._token: str | None = None
        self._handshake_buffer = b""
        self._pending_port: int | None = None
        self._probe_reply: QNetworkReply | None = None
        self._shutting_down = False

    @property
    def is_ready(self) -> bool:
        return self._session.can_send_chat

    @property
    def state(self) -> str:
        return self._session.state.value

    def start(self) -> None:
        if self._session.state is not BackendState.STOPPED:
            return
        self._api.clear_configuration()
        self._session.begin_owned_start()
        self._token = secrets.token_urlsafe(32)
        self._deadline.start()
        self._set_state()
        self._process.setProgram(sys.executable)
        self._process.setArguments(["-m", "fairy.desktop.backend_server"])
        self._process.start()
        QTimer.singleShot(STARTUP_TIMEOUT_MS, self._check_startup_timeout)

    def shutdown(self) -> None:
        self._shutting_down = True
        self._api.clear_configuration()
        self._cancel_probe()
        self._token = None
        self._pending_port = None
        if self._session.state in {BackendState.STARTING, BackendState.READY}:
            self._session.mark_failed()
            self._set_state()
            self.ready_changed.emit(False)
        if not self._session.should_terminate_child(child_running=self._child_running()):
            return
        self._process.terminate()
        if not self._process.waitForFinished(2_000):
            self._process.kill()
            self._process.waitForFinished(1_000)

    def _child_running(self) -> bool:
        return self._process.state() != QProcess.ProcessState.NotRunning

    def _send_session_token(self) -> None:
        if self._token is None:
            self._fail("The local NeuroFairy service has no session credential.")
            return
        self._process.write(QByteArray(f"{self._token}\n".encode()))
        self._process.closeWriteChannel()

    def _read_stdout(self) -> None:
        self._handshake_buffer += bytes(self._process.readAllStandardOutput())
        while b"\n" in self._handshake_buffer:
            line, self._handshake_buffer = self._handshake_buffer.split(b"\n", 1)
            if line:
                self._handle_handshake(line)

    def _handle_handshake(self, line: bytes) -> None:
        if self._token is None or self._pending_port is not None:
            self._fail("The local NeuroFairy service returned an unexpected handshake.")
            return
        try:
            self._pending_port = decode_backend_handshake(line, self._token)
        except BackendHandshakeError:
            self._fail("The local NeuroFairy service could not prove its identity.")
            return
        self._probe_authenticated_health()

    def _probe_authenticated_health(self) -> None:
        if (
            self._shutting_down
            or self._session.state is not BackendState.STARTING
            or self._pending_port is None
            or self._token is None
            or self._probe_reply is not None
        ):
            return
        request = QNetworkRequest(QUrl(f"http://127.0.0.1:{self._pending_port}/api/health"))
        request.setRawHeader(TOKEN_HEADER, self._token.encode())
        request.setTransferTimeout(2_000)
        reply = self._network.get(request)
        self._probe_reply = reply
        reply.finished.connect(lambda: self._handle_probe(reply))

    def _handle_probe(self, reply: QNetworkReply) -> None:
        if reply is not self._probe_reply:
            reply.deleteLater()
            return
        self._probe_reply = None
        try:
            healthy = reply.error() == QNetworkReply.NetworkError.NoError and decode_health(
                bytes(reply.readAll())
            )
            if (
                healthy
                and not self._shutting_down
                and self._session.state is BackendState.STARTING
                and self._child_running()
                and self._pending_port is not None
                and self._token is not None
            ):
                self._session.mark_ready(self._pending_port)
                self._api.configure(self._session.api_base_url or "", self._token)
                self._set_state()
                self.ready_changed.emit(True)
                return
            if self._shutting_down or self._session.state is not BackendState.STARTING:
                return
            if self._deadline.hasExpired(STARTUP_TIMEOUT_MS):
                self._fail("The local NeuroFairy service did not start in time.")
                return
            QTimer.singleShot(POLL_INTERVAL_MS, self._probe_authenticated_health)
        finally:
            reply.deleteLater()

    def _check_startup_timeout(self) -> None:
        if self._session.state is BackendState.STARTING:
            self._fail("The local NeuroFairy service did not start in time.")

    def _drain_stderr(self) -> None:
        output = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        if output:
            sys.stderr.write(output)

    def _process_error(self, _error) -> None:
        if not self._shutting_down:
            self._fail("The local NeuroFairy service could not be started.")

    def _process_finished(self, *_args) -> None:
        if not self._shutting_down and self._session.state is not BackendState.FAILED:
            self._fail("The local NeuroFairy service stopped unexpectedly.")

    def _fail(self, message: str) -> None:
        self._api.clear_configuration()
        self._cancel_probe()
        self._session.mark_failed()
        self._token = None
        self._pending_port = None
        self._set_state()
        self.ready_changed.emit(False)
        self.error_changed.emit(message)
        if self._session.should_terminate_child(child_running=self._child_running()):
            self._process.terminate()
            if not self._process.waitForFinished(1_000):
                self._process.kill()

    def _set_state(self) -> None:
        self.state_changed.emit(self._session.state.value)

    def _cancel_probe(self) -> None:
        reply = self._probe_reply
        self._probe_reply = None
        if reply is not None:
            reply.abort()
