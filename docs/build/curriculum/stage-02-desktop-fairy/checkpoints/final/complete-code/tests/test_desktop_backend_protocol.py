import pytest

from fairy.desktop.backend_protocol import (
    BackendHandshakeError,
    BackendSession,
    BackendState,
    decode_backend_handshake,
)

TOKEN = "0123456789abcdef0123456789abcdef"


def test_owned_child_handshake_returns_bound_port():
    line = (
        b'FAIRY_BACKEND_READY {"port":53123,'
        b'"proof":"f1d4f6595616abfdc1ac6d9cc346a63d146ae3a5f03d33df91aaaac0a9d36de8"}'
    )

    assert decode_backend_handshake(line, TOKEN) == 53123


def test_public_or_forged_handshake_is_rejected():
    forged = (
        b'FAIRY_BACKEND_READY {"port":53123,'
        b'"proof":"0000000000000000000000000000000000000000000000000000000000000000"}'
    )

    with pytest.raises(BackendHandshakeError):
        decode_backend_handshake(forged, TOKEN)


@pytest.mark.parametrize("port", [0, 65_536, "53123"])
def test_handshake_rejects_invalid_ports(port):
    line = f'FAIRY_BACKEND_READY {{"port":{port!r},"proof":"unused"}}'.encode()

    with pytest.raises(BackendHandshakeError):
        decode_backend_handshake(line, TOKEN)


def test_owned_session_disables_chat_after_child_failure():
    session = BackendSession()

    session.begin_owned_start()
    assert session.state is BackendState.STARTING
    assert session.owns_process is True

    session.mark_ready(53123)
    assert session.state is BackendState.READY
    assert session.api_base_url == "http://127.0.0.1:53123"

    session.mark_failed()
    assert session.state is BackendState.FAILED
    assert session.api_base_url is None
    assert session.can_send_chat is False


def test_startup_timeout_disables_chat_before_handshake():
    session = BackendSession()
    session.begin_owned_start()

    session.mark_failed()

    assert session.state is BackendState.FAILED
    assert session.api_base_url is None
    assert session.can_send_chat is False


def test_shutdown_only_terminates_a_running_owned_child():
    session = BackendSession()
    assert session.should_terminate_child(child_running=True) is False

    session.begin_owned_start()
    assert session.should_terminate_child(child_running=True) is True
    assert session.should_terminate_child(child_running=False) is False
