"""Pure protocol and ownership rules for the desktop-owned backend."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from enum import StrEnum

HANDSHAKE_PREFIX = b"FAIRY_BACKEND_READY "


class BackendHandshakeError(ValueError):
    """The child backend did not provide a valid authenticated handshake."""


class BackendState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"


@dataclass
class BackendSession:
    state: BackendState = BackendState.STOPPED
    owns_process: bool = False
    api_base_url: str | None = None

    @property
    def can_send_chat(self) -> bool:
        return self.state is BackendState.READY and self.api_base_url is not None

    def begin_owned_start(self) -> None:
        if self.state is not BackendState.STOPPED:
            raise RuntimeError("backend session has already started")
        self.state = BackendState.STARTING
        self.owns_process = True
        self.api_base_url = None

    def mark_ready(self, port: int) -> None:
        if self.state is not BackendState.STARTING or not self.owns_process:
            raise RuntimeError("only a starting owned backend can become ready")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65_535:
            raise ValueError("backend port is invalid")
        self.state = BackendState.READY
        self.api_base_url = f"http://127.0.0.1:{port}"

    def mark_failed(self) -> None:
        self.state = BackendState.FAILED
        self.api_base_url = None

    def should_terminate_child(self, *, child_running: bool) -> bool:
        return self.owns_process and child_running


def _proof(port: int, token: str) -> str:
    message = f"neurofairy-backend:{port}".encode()
    return hmac.new(token.encode(), message, hashlib.sha256).hexdigest()


def encode_backend_handshake(port: int, token: str) -> bytes:
    payload = json.dumps({"port": port, "proof": _proof(port, token)}, separators=(",", ":"))
    return HANDSHAKE_PREFIX + payload.encode()


def decode_backend_handshake(line: bytes, token: str) -> int:
    if not line.startswith(HANDSHAKE_PREFIX):
        raise BackendHandshakeError("backend handshake prefix is missing")
    try:
        payload = json.loads(line[len(HANDSHAKE_PREFIX) :].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackendHandshakeError("backend handshake is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise BackendHandshakeError("backend handshake must be an object")
    port = payload.get("port")
    proof = payload.get("proof")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65_535:
        raise BackendHandshakeError("backend handshake port is invalid")
    if not isinstance(proof, str) or not hmac.compare_digest(proof, _proof(port, token)):
        raise BackendHandshakeError("backend handshake proof is invalid")
    return port
