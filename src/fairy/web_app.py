from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Neurofairy")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UIUX_DIR = PROJECT_ROOT / "uiux"
UI_DIR = UIUX_DIR / "ui"


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat_with_neurofairy(request: ChatRequest) -> dict[str, str]:
    message = request.message.strip()

    if not message:
        return {"reply": "I’m here. Whenever you’re ready."}

    return {
        "reply": (
            "Choose one small, visible "
            "next step, and we can make it smaller if it still feels like too much."
        )
    }


app.mount("/assets", StaticFiles(directory=UIUX_DIR / "assets"), name="assets")
app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")
