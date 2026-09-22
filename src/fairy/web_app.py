import asyncio
import tempfile
import threading
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from fairy.neurofairy_chat import reply_to_user
from fairy.transcription import TranscriptionUnavailable, transcribe_audio

app = FastAPI(title="Neurofairy")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UIUX_DIR = PROJECT_ROOT / "uiux"
UI_DIR = UIUX_DIR / "ui"
MAX_TRANSCRIPTION_BYTES = 20 * 1024 * 1024
TRANSCRIPTION_TEMP_DIR: Path | None = None
TRANSCRIPTION_SLOT = threading.BoundedSemaphore(1)
ALLOWED_AUDIO_TYPES = {
    "audio/aac",
    "audio/flac",
    "audio/m4a",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-wav",
}


class ChatRequest(BaseModel):
    message: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/transcriptions")
async def create_transcription(
    audio: Annotated[UploadFile, File(...)],
) -> dict[str, str]:
    content_type = (audio.content_type or "").split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio type.",
        )
    contents = await audio.read(MAX_TRANSCRIPTION_BYTES + 1)  # Read one extra byte to check size

    if len(contents) > MAX_TRANSCRIPTION_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large")

    if not contents:
        raise HTTPException(status_code=400, detail="No audio file uploaded")

    if not TRANSCRIPTION_SLOT.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="A transcription is already in progress.",
        )

    with tempfile.NamedTemporaryFile(
        dir=TRANSCRIPTION_TEMP_DIR,
        suffix=".audio",
        delete=False,
    ) as temporary_file:
        temporary_file.write(contents)
        temporary_path = Path(temporary_file.name)

    try:
        transcript = await asyncio.to_thread(
            transcribe_audio, temporary_path
        )  # Run the blocking transcribe_audio in a separate thread
        return {"transcript": transcript}
    except TranscriptionUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Local transcription is unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not transcribe the audio.",
        ) from exc
    finally:
        temporary_path.unlink(missing_ok=True)
        TRANSCRIPTION_SLOT.release()


@app.post("/api/chat")
def chat_with_neurofairy(request: ChatRequest) -> dict[str, str]:
    message = request.message.strip()

    if not message:
        return {"reply": "Here when you are ready."}

    try:
        return {"reply": reply_to_user(message)}
    except Exception:
        return {
            "reply": (
                "I'm having trouble thinking clearly. Try again later. In the meantime, take a deep"
                "breath and choose one action."
            )
        }


app.mount("/assets", StaticFiles(directory=UIUX_DIR / "assets"), name="assets")
app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")
