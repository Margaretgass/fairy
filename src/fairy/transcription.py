from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


class TranscriptionUnavailable(RuntimeError):
    """Raised when tspt tool not available"""


class TranscriptionFailed(RuntimeError):
    """when local transcription cannot produce usable text"""


@dataclass(frozen=True)
class WhisperCppConfig:
    """paths and options run local whisper.cpp tscption"""

    cli_path: Path
    model_path: Path
    ffmpeg_path: str = "ffmpeg"
    language: str = "en"

    @classmethod
    def from_env(cls) -> "WhisperCppConfig":
        """build config from env defaults and optional overrides"""
        cli_default = Path.home() / ".fairy/whisper.cpp/build/bin/whisper-cli"
        model_default = Path.home() / ".fairy/whisper.cpp/models/ggml-base.en.bin"
        return cls(
            cli_path=Path(os.environ.get("FAIRY_WHISPER_CLI", cli_default)),
            model_path=Path(os.environ.get("FAIRY_WHISPER_MODEL", model_default)),
            ffmpeg_path=os.environ.get("FAIRY_FFMPEG", "ffmpeg"),
        )

    ProcessRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def clean_transcript(text: str) -> str:
    """Collapse repeated whitespace while preserving punctuation."""
    return " ".join(text.split())


def transcribe_audio(
    source_path: Path,
    config: WhisperCppConfig | None = None,
    *,
    runner: ProcessRunner = subprocess.run,
) -> str:
    """Convert local audio to WAV, transcribe it locally, and return clean text."""
    source_path = Path(source_path)

    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    config = config or WhisperCppConfig.from_env()

    if not config.cli_path.is_file():
        raise TranscriptionUnavailable("whisper-cli is not installed")

    if not config.model_path.is_file():
        raise TranscriptionUnavailable("model is not installed")

    try:
        with tempfile.TemporaryDirectory(prefix="fairy-transcription-") as temp_dir:
            temp_path = Path(temp_dir)
            wav_path = temp_path / "audio.wav"
            output_prefix = temp_path / "transcript"
            transcript_path = output_prefix.with_suffix(".txt")

            runner(
                [
                    config.ffmpeg_path,
                    "-y",
                    "-i",
                    str(source_path),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(wav_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            runner(
                [
                    str(config.cli_path),
                    "-m",
                    str(config.model_path),
                    "-f",
                    str(wav_path),
                    "-l",
                    config.language,
                    "-nt",
                    "-np",
                    "-otxt",
                    "-of",
                    str(output_prefix),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            if not transcript_path.is_file():
                raise TranscriptionFailed("Transcript was not produced.")

            cleaned = clean_transcript(transcript_path.read_text(encoding="utf-8"))

            if not cleaned:
                raise TranscriptionFailed("No speech was detected.")

            return cleaned
    except FileNotFoundError as exc:
        raise TranscriptionUnavailable(f"ffmpeg is not installed: {config.ffmpeg_path}") from exc
    except subprocess.CalledProcessError as exc:
        raise TranscriptionFailed("Local transcription failed.") from exc
