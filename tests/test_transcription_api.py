from pathlib import Path

from fastapi.testclient import TestClient

from fairy import web_app
from fairy.transcription import TranscriptionUnavailable

client = TestClient(web_app.app)


def test_valid_upload_returns_transcript(monkeypatch) -> None:
    def fake_transcribe(path: Path) -> str:
        assert path.is_file()
        return "This is a test"

    monkeypatch.setattr(web_app, "transcribe_audio", fake_transcribe)

    response = client.post(
        "/api/transcriptions",
        files={"audio": ("brain-dump.webm", b"fake audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {"transcript": "This is a test"}


def test_empty_upload_returns_bad_request() -> None:
    response = client.post(
        "/api/transcriptions",
        files={"audio": ("empty.webm", b"", "audio/webm")},
    )

    assert response.status_code == 400


def test_large_upload_returns_payload_too_large() -> None:
    large_audio = b"x" * (20 * 1024 * 1024 + 1)

    response = client.post(
        "/api/transcriptions",
        files={"audio": ("large.webm", large_audio, "audio/webm")},
    )

    assert response.status_code == 413


def test_unavailable_transcriber_returns_service_unavailable(monkeypatch) -> None:
    def fake_transcribe(path: Path) -> str:
        raise TranscriptionUnavailable("private setup detail")

    monkeypatch.setattr(web_app, "transcribe_audio", fake_transcribe)

    response = client.post(
        "/api/transcriptions",
        files={"audio": ("brain-dump.webm", b"fake audio", "audio/webm")},
    )

    assert response.status_code == 503
    assert "private setup detail" not in response.text


def test_temporary_upload_is_deleted_after_success(monkeypatch, tmp_path: Path) -> None:
    uploaded_path: Path | None = None

    def fake_transcribe(path: Path) -> str:
        nonlocal uploaded_path
        uploaded_path = path
        return "A thought."

    monkeypatch.setattr(web_app, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(web_app, "TRANSCRIPTION_TEMP_DIR", tmp_path)

    response = client.post(
        "/api/transcriptions",
        files={"audio": ("brain-dump.webm", b"fake audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert uploaded_path is not None
    assert not uploaded_path.exists()


def test_temporary_upload_is_deleted_after_failure(monkeypatch, tmp_path: Path) -> None:
    uploaded_path: Path | None = None

    def fake_transcribe(path: Path) -> str:
        nonlocal uploaded_path
        uploaded_path = path
        raise RuntimeError("private failure detail")

    monkeypatch.setattr(web_app, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(web_app, "TRANSCRIPTION_TEMP_DIR", tmp_path)

    response = client.post(
        "/api/transcriptions",
        files={"audio": ("brain-dump.webm", b"fake audio", "audio/webm")},
    )

    assert response.status_code == 500
    assert uploaded_path is not None
    assert not uploaded_path.exists()
    assert "private failure detail" not in response.text


def test_unsupported_audio_type_returns_bad_request() -> None:
    response = client.post(
        "/api/transcriptions",
        files={"audio": ("notes.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400


def test_audio_codec_parameter_is_accepted(monkeypatch) -> None:
    monkeypatch.setattr(web_app, "transcribe_audio", lambda path: "A thought.")

    response = client.post(
        "/api/transcriptions",
        files={
            "audio": (
                "brain-dump.webm",
                b"fake audio",
                "audio/webm;codecs=opus",
            )
        },
    )

    assert response.status_code == 200


def test_second_transcription_is_rejected_while_one_is_running() -> None:
    assert web_app.TRANSCRIPTION_SLOT.acquire(blocking=False)

    try:
        response = client.post(
            "/api/transcriptions",
            files={"audio": ("brain-dump.webm", b"fake audio", "audio/webm")},
        )
    finally:
        web_app.TRANSCRIPTION_SLOT.release()

    assert response.status_code == 429
