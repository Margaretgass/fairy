from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Neurofairy")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UIUX_DIR = PROJECT_ROOT / "uiux"
UI_DIR = UIUX_DIR / "ui"

app.mount("/assets", StaticFiles(directory=UIUX_DIR / "assets"), name="assets")
app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

