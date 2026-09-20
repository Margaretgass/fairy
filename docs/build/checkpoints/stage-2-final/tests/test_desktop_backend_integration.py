"""Regression tests for the real desktop controller/client trust boundary.

Small Qt fakes keep these lifecycle tests deterministic and runnable without opening a
window. The application modules themselves are loaded unchanged.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


class FakeBoundSignal:
    def __init__(self) -> None:
        self.callbacks = []
        self.values = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self, *args) -> None:
        self.values.append(args)
        for callback in list(self.callbacks):
            callback(*args)


class FakeSignal:
    def __init__(self, *_types) -> None:
        self.name = ""

    def __set_name__(self, _owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, _owner):
        if instance is None:
            return self
        key = f"_signal_{self.name}"
        return instance.__dict__.setdefault(key, FakeBoundSignal())


class FakeQObject:
    def __init__(self, parent=None) -> None:
        self.parent = parent


class FakeElapsedTimer:
    def start(self) -> None:
        pass

    def hasExpired(self, _milliseconds: int) -> bool:
        return False


class FakeTimer:
    callbacks = []

    @classmethod
    def singleShot(cls, milliseconds: int, callback) -> None:
        cls.callbacks.append((milliseconds, callback))


class FakeProcess:
    class ProcessChannelMode:
        SeparateChannels = 1

    class ProcessState:
        NotRunning = 0
        Running = 1

    instances = []

    def __init__(self, _parent=None) -> None:
        self.started = FakeBoundSignal()
        self.readyReadStandardOutput = FakeBoundSignal()
        self.readyReadStandardError = FakeBoundSignal()
        self.errorOccurred = FakeBoundSignal()
        self.finished = FakeBoundSignal()
        self.program = None
        self.arguments = []
        self.writes = []
        self.terminate_calls = 0
        self.kill_calls = 0
        self.process_state = self.ProcessState.NotRunning
        self.instances.append(self)

    def setProcessChannelMode(self, _mode) -> None:
        pass

    def setProgram(self, program: str) -> None:
        self.program = program

    def setArguments(self, arguments: list[str]) -> None:
        self.arguments = arguments

    def start(self) -> None:
        self.process_state = self.ProcessState.Running
        self.started.emit()

    def state(self):
        return self.process_state

    def write(self, payload: bytes) -> None:
        self.writes.append(bytes(payload))

    def closeWriteChannel(self) -> None:
        pass

    def readAllStandardOutput(self) -> bytes:
        return b""

    def readAllStandardError(self) -> bytes:
        return b""

    def terminate(self) -> None:
        self.terminate_calls += 1
        self.process_state = self.ProcessState.NotRunning

    def waitForFinished(self, _milliseconds: int) -> bool:
        return True

    def kill(self) -> None:
        self.kill_calls += 1
        self.process_state = self.ProcessState.NotRunning


class FakeRequest:
    class KnownHeaders:
        ContentTypeHeader = 1

    def __init__(self, url: str) -> None:
        self.url = str(url)
        self.raw_headers = {}
        self.headers = {}
        self.timeout = None

    def setRawHeader(self, name: bytes, value: bytes) -> None:
        self.raw_headers[name] = value

    def setHeader(self, name, value) -> None:
        self.headers[name] = value

    def setTransferTimeout(self, milliseconds: int) -> None:
        self.timeout = milliseconds


class FakeReply:
    class NetworkError:
        NoError = 0

    def __init__(self, payload: bytes = b"", error: int = 0) -> None:
        self.finished = FakeBoundSignal()
        self.payload = payload
        self.error_value = error
        self.deleted = False
        self.abort_calls = 0

    def error(self) -> int:
        return self.error_value

    def readAll(self) -> bytes:
        return self.payload

    def deleteLater(self) -> None:
        self.deleted = True

    def abort(self) -> None:
        self.abort_calls += 1
        self.finished.emit()


class FakeNetworkManager:
    instances = []

    def __init__(self, _parent=None) -> None:
        self.get_calls = []
        self.post_calls = []
        self.instances.append(self)

    def get(self, request: FakeRequest) -> FakeReply:
        reply = FakeReply()
        self.get_calls.append((request, reply))
        return reply

    def post(self, request: FakeRequest, payload: bytes) -> FakeReply:
        reply = FakeReply()
        self.post_calls.append((request, bytes(payload), reply))
        return reply


@pytest.fixture
def desktop_modules(monkeypatch):
    FakeProcess.instances = []
    FakeNetworkManager.instances = []
    FakeTimer.callbacks = []

    core = ModuleType("PySide6.QtCore")
    core.QByteArray = bytes
    core.QElapsedTimer = FakeElapsedTimer
    core.QObject = FakeQObject
    core.QProcess = FakeProcess
    core.QTimer = FakeTimer
    core.QUrl = str
    core.Signal = FakeSignal

    network = ModuleType("PySide6.QtNetwork")
    network.QNetworkAccessManager = FakeNetworkManager
    network.QNetworkReply = FakeReply
    network.QNetworkRequest = FakeRequest

    pyside = ModuleType("PySide6")
    pyside.QtCore = core
    pyside.QtNetwork = network

    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", core)
    monkeypatch.setitem(sys.modules, "PySide6.QtNetwork", network)
    monkeypatch.delitem(sys.modules, "fairy.desktop.api_client", raising=False)
    monkeypatch.delitem(sys.modules, "fairy.desktop.backend", raising=False)

    api_client = importlib.import_module("fairy.desktop.api_client")
    backend = importlib.import_module("fairy.desktop.backend")
    protocol = importlib.import_module("fairy.desktop.backend_protocol")
    return SimpleNamespace(api_client=api_client, backend=backend, protocol=protocol)


def make_controller(modules):
    api = modules.api_client.ApiClient()
    controller = modules.backend.BackendController(api)
    return api, controller


def test_controller_launch_has_no_fixed_port_and_chat_starts_disabled(desktop_modules):
    api, controller = make_controller(desktop_modules)

    controller.start()
    api.send_chat("private thought")

    assert controller._process.arguments == ["-m", "fairy.desktop.backend_server"]
    assert "8000" not in " ".join(controller._process.arguments)
    assert FakeNetworkManager.instances[0].post_calls == []


def test_forged_handshake_never_configures_client_and_stops_owned_child(desktop_modules):
    api, controller = make_controller(desktop_modules)
    controller.start()

    forged = (
        b'FAIRY_BACKEND_READY {"port":8000,'
        b'"proof":"0000000000000000000000000000000000000000000000000000000000000000"}'
    )
    controller._handle_handshake(forged)
    api.send_chat("do not leak this")

    assert controller.state == "failed"
    assert controller._process.terminate_calls == 1
    assert FakeNetworkManager.instances[0].post_calls == []
    assert FakeNetworkManager.instances[1].get_calls == []


def test_child_failure_aborts_inflight_chat_and_disables_later_sends(desktop_modules):
    api, controller = make_controller(desktop_modules)
    controller.start()
    handshake = desktop_modules.protocol.encode_backend_handshake(53_123, controller._token)

    controller._handle_handshake(handshake)
    health_request, health_reply = FakeNetworkManager.instances[1].get_calls[0]
    health_reply.payload = b'{"service":"neurofairy","status":"ok"}'
    health_reply.finished.emit()

    assert health_request.url == "http://127.0.0.1:53123/api/health"
    assert health_request.raw_headers[b"X-Fairy-Token"] == controller._token.encode()

    api.send_chat("safe after authentication")
    _, _, chat_reply = FakeNetworkManager.instances[0].post_calls[0]

    controller._process.finished.emit()

    assert controller.state == "failed"
    assert chat_reply.abort_calls == 1
    assert api.chat_succeeded.values == []
    assert api.chat_failed.values == [("Local service unavailable. Try again.",)]

    api.send_chat("must not send after failure")

    assert api.chat_failed.values == [
        ("Local service unavailable. Try again.",),
        ("Local service unavailable. Try again.",),
    ]
    assert len(FakeNetworkManager.instances[0].post_calls) == 1


def test_shutdown_aborts_probe_and_stale_health_cannot_restore_configuration(
    desktop_modules,
):
    api, controller = make_controller(desktop_modules)
    controller.start()
    handshake = desktop_modules.protocol.encode_backend_handshake(53_123, controller._token)
    controller._handle_handshake(handshake)
    _, health_reply = FakeNetworkManager.instances[1].get_calls[0]

    controller.shutdown()
    health_reply.payload = b'{"service":"neurofairy","status":"ok"}'
    health_reply.finished.emit()
    api.send_chat("must remain disabled")

    assert health_reply.abort_calls == 1
    assert controller.state == "failed"
    assert api._base_url is None
    assert FakeNetworkManager.instances[0].post_calls == []


def test_shutdown_terminates_only_the_controller_owned_process(desktop_modules):
    unrelated_process = FakeProcess()
    api, controller = make_controller(desktop_modules)
    controller.start()

    controller.shutdown()
    api.send_chat("must not send during shutdown")

    assert controller._process.terminate_calls == 1
    assert unrelated_process.terminate_calls == 0
    assert FakeNetworkManager.instances[0].post_calls == []
