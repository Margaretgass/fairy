from __future__ import annotations

import subprocess
from pathlib import Path
from typing import get_type_hints

import pytest

from fairy.transcription import (
    TranscriptionFailed,
    TranscriptionUnavailable,
    WhisperCppConfig,
    transcribe_audio,
)


def test_transcribe_audio_type_hints_resolve() -> None:
    annotations = get_type_hints(transcribe_audio)

    assert annotations["return"] is str


def test_config_uses_documented_default_model_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("FAIRY_WHISPER_MODEL", raising=False)

    config = WhisperCppConfig.from_env()

    assert config.model_path == tmp_path / ".fairy/models/ggml-base.en.bin"


def make_fake_config(tmp_path: Path) -> WhisperCppConfig:
    cli_path = tmp_path / "whisper-cli"
    model_path = tmp_path / "ggml-base.en.bin"

    cli_path.write_text("fake whisper cli", encoding="utf-8")
    model_path.write_text("fake model", encoding="utf-8")

    return WhisperCppConfig(
        cli_path=cli_path,
        model_path=model_path,
    )


def make_fake_runner(transcript: str = "  Call   the dentist.  "):
    """Return a fake subprocess runner and the commands it receives."""
    calls: list[list[str]] = []

    def fake_runner(command: list[str], **kwargs: object):
        calls.append(command)

        if command[0].endswith("ffmpeg"):
            wav_path = Path(command[-1])
            wav_path.write_bytes(b"fake wav data")
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        output_prefix = Path(command[command.index("-of") + 1])
        output_prefix.with_suffix(".txt").write_text(
            transcript,
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    return fake_runner, calls


def test_converter_receives_expected_ffmpeg_args(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    runner, calls = make_fake_runner()
    config = make_fake_config(tmp_path)

    transcribe_audio(source_path, config, runner=runner)

    ffmpeg_command = calls[0]
    assert ffmpeg_command[0] == "ffmpeg"
    assert ffmpeg_command[ffmpeg_command.index("-ar") + 1] == "16000"
    assert ffmpeg_command[ffmpeg_command.index("-ac") + 1] == "1"
    assert ffmpeg_command[ffmpeg_command.index("-c:a") + 1] == "pcm_s16le"


def test_whisper_command_uses_separate_arguments_no_shell(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    seen_kwargs: list[dict[str, object]] = []

    def fake_runner(command: list[str], **kwargs: object):
        seen_kwargs.append(kwargs)
        if command[0].endswith("ffmpeg"):
            Path(command[-1]).write_bytes(b"fake wav data")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        output_prefix = Path(command[command.index("-of") + 1])
        output_prefix.with_suffix(".txt").write_text("hello world", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    transcribe_audio(
        source_path,
        make_fake_config(tmp_path),
        runner=fake_runner,
    )

    assert len(seen_kwargs) == 2
    assert all("shell" not in kwargs or kwargs.get("shell") is not True for kwargs in seen_kwargs)


def test_whitespace_is_cleaned(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    runner, _ = make_fake_runner("   Call   the   dentist.   ")
    config = make_fake_config(tmp_path)

    result = transcribe_audio(source_path, config, runner=runner)

    assert result == "Call the dentist."


def test_missing_audio_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        transcribe_audio(tmp_path / "missing.wav", make_fake_config(tmp_path))


def test_missing_cli_raises_transcription_unavailable(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    config = WhisperCppConfig(
        cli_path=tmp_path / "missing-whisper-cli",
        model_path=tmp_path / "model.bin",
    )
    config.model_path.write_text("fake model", encoding="utf-8")

    with pytest.raises(TranscriptionUnavailable, match="whisper-cli is not installed"):
        transcribe_audio(source_path, config)


def test_missing_model_raises_transcription_unavailable(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    config = WhisperCppConfig(
        cli_path=tmp_path / "whisper-cli",
        model_path=tmp_path / "missing-model.bin",
    )
    config.cli_path.write_text("fake cli", encoding="utf-8")

    with pytest.raises(TranscriptionUnavailable, match="model is not installed"):
        transcribe_audio(source_path, config)


def test_empty_transcript_raises_transcription_failed(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    runner, _ = make_fake_runner("   \n\t  ")
    config = make_fake_config(tmp_path)

    with pytest.raises(TranscriptionFailed, match="No speech was detected"):
        transcribe_audio(source_path, config, runner=runner)


def test_fake_runner_test_does_not_require_real_whisper_or_microphone(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    runner, _ = make_fake_runner("hello there")
    config = make_fake_config(tmp_path)

    result = transcribe_audio(source_path, config, runner=runner)
    assert result == "hello there"


def test_subprocess_failure_becomes_transcription_failed(tmp_path: Path) -> None:
    source_path = tmp_path / "audio.wav"
    source_path.write_bytes(b"fake audio")

    def failing_runner(command: list[str], **kwargs: object):
        if command[0].endswith("ffmpeg"):
            Path(command[-1]).write_bytes(b"fake wav data")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise subprocess.CalledProcessError(
            1,
            command,
            stderr="private whisper stderr",
        )

    config = make_fake_config(tmp_path)

    with pytest.raises(TranscriptionFailed, match="Local transcription failed"):
        transcribe_audio(source_path, config, runner=failing_runner)
