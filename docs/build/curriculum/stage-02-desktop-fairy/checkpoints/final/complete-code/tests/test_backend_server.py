import socket
from io import StringIO

import pytest

from fairy.desktop.backend_server import bind_loopback_socket, read_session_token


def test_session_token_is_read_from_stdin_without_whitespace():
    token = "0123456789abcdef0123456789abcdef"

    assert read_session_token(StringIO(f"  {token}\n")) == token


@pytest.mark.parametrize("value", ["", "short-token"])
def test_missing_or_short_session_token_is_rejected(value):
    with pytest.raises(ValueError, match="session token"):
        read_session_token(StringIO(value))


def test_backend_socket_uses_os_assigned_loopback_port(monkeypatch):
    calls: list[tuple[str, tuple | None]] = []

    class FakeSocket:
        def bind(self, address):
            calls.append(("bind", address))

        def listen(self):
            calls.append(("listen", None))

        def close(self):
            calls.append(("close", None))

    fake_socket = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *_args: fake_socket)

    server_socket = bind_loopback_socket()

    assert server_socket is fake_socket
    assert calls == [("bind", ("127.0.0.1", 0)), ("listen", None)]
