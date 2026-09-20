"""Asynchronous client for the local NeuroFairy API."""

from __future__ import annotations

import json

from PySide6.QtCore import QByteArray, QObject, QUrl, Signal
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)

REQUEST_TIMEOUT_MS = 15_000
TOKEN_HEADER = b"X-Fairy-Token"


class ApiResponseError(ValueError):
    """The local API returned a response the desktop client cannot use."""


def decode_chat_reply(payload: bytes) -> str:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiResponseError("invalid chat response") from exc
    if not isinstance(data, dict):
        raise ApiResponseError("chat response must be an object")
    reply = data.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise ApiResponseError("chat response is missing a reply")
    return reply.strip()


def decode_health(payload: bytes) -> bool:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return data == {"service": "neurofairy", "status": "ok"}


class ApiClient(QObject):
    chat_succeeded = Signal(str)
    chat_failed = Signal(str)
    health_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._chat_pending = False
        self._chat_reply: QNetworkReply | None = None
        self._health_reply: QNetworkReply | None = None
        self._base_url: str | None = None
        self._token: str | None = None

    def configure(self, base_url: str, token: str) -> None:
        self._base_url = base_url
        self._token = token

    def clear_configuration(self) -> None:
        chat_was_pending = self._chat_pending or self._chat_reply is not None
        self._base_url = None
        self._token = None
        self._chat_pending = False
        replies = (self._chat_reply, self._health_reply)
        self._chat_reply = None
        self._health_reply = None
        for reply in replies:
            if reply is not None:
                reply.abort()
        if chat_was_pending:
            self.chat_failed.emit("Local service unavailable. Try again.")

    def _request(self, path: str) -> QNetworkRequest | None:
        if self._base_url is None or self._token is None:
            return None
        request = QNetworkRequest(QUrl(f"{self._base_url}{path}"))
        request.setRawHeader(TOKEN_HEADER, self._token.encode())
        return request

    def send_chat(self, message: str) -> None:
        clean_message = message.strip()
        if not clean_message or self._chat_pending:
            return

        request = self._request("/api/chat")
        if request is None:
            self.chat_failed.emit("Local service unavailable. Try again.")
            return
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/json",
        )
        request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        payload = json.dumps({"message": clean_message}).encode("utf-8")

        self._chat_pending = True
        reply = self._network.post(request, QByteArray(payload))
        self._chat_reply = reply
        reply.finished.connect(lambda: self._finish_chat(reply))

    def check_health(self) -> None:
        if self._health_reply is not None:
            return
        request = self._request("/api/health")
        if request is None:
            self.health_changed.emit(False)
            return
        request.setTransferTimeout(3_000)
        reply = self._network.get(request)
        self._health_reply = reply
        reply.finished.connect(lambda: self._finish_health(reply))

    def _finish_chat(self, reply: QNetworkReply) -> None:
        if reply is not self._chat_reply:
            reply.deleteLater()
            return
        self._chat_reply = None
        self._chat_pending = False
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.chat_failed.emit("Local service unavailable. Try again.")
                return
            try:
                message = decode_chat_reply(bytes(reply.readAll()))
            except ApiResponseError:
                self.chat_failed.emit("The local reply was not usable. Try again.")
                return
            self.chat_succeeded.emit(message)
        finally:
            reply.deleteLater()

    def _finish_health(self, reply: QNetworkReply) -> None:
        if reply is not self._health_reply:
            reply.deleteLater()
            return
        self._health_reply = None
        try:
            healthy = reply.error() == QNetworkReply.NetworkError.NoError and decode_health(
                bytes(reply.readAll())
            )
            self.health_changed.emit(healthy)
        finally:
            reply.deleteLater()
