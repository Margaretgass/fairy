"""Run the authenticated backend owned by the desktop Fairy process."""

from __future__ import annotations

import socket
import sys
from typing import TextIO

import uvicorn

from fairy.desktop.backend_protocol import encode_backend_handshake
from fairy.web_app import create_app

MINIMUM_TOKEN_LENGTH = 32


def read_session_token(stream: TextIO) -> str:
    """Read the one-time desktop credential without putting it in process arguments."""
    token = stream.readline().strip()
    if len(token) < MINIMUM_TOKEN_LENGTH:
        raise ValueError("desktop session token is missing or too short")
    return token


def bind_loopback_socket() -> socket.socket:
    """Reserve an OS-assigned loopback port for this child process."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(("127.0.0.1", 0))
        server_socket.listen()
        return server_socket
    except Exception:
        server_socket.close()
        raise


def main() -> None:
    token = read_session_token(sys.stdin)
    server_socket = bind_loopback_socket()
    port = server_socket.getsockname()[1]
    print(encode_backend_handshake(port, token).decode(), flush=True)

    config = uvicorn.Config(
        create_app(api_token=token),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    try:
        uvicorn.Server(config).run(sockets=[server_socket])
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
