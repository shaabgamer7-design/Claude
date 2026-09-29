"""Paths and user-tunable settings for Avatar Studio."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("AVATAR_STUDIO_DATA", ROOT / "data"))
MODELS_DIR = Path(os.environ.get("AVATAR_STUDIO_MODELS", ROOT / "models"))
AVATARS_DIR = DATA_DIR / "avatars"
VIDEOS_DIR = DATA_DIR / "videos"
TMP_DIR = DATA_DIR / "tmp"
SETTINGS_FILE = DATA_DIR / "settings.json"

for _d in (DATA_DIR, MODELS_DIR, AVATARS_DIR, VIDEOS_DIR, TMP_DIR):
    _d.mkdir(parents=True, exist_ok=True)

FPS = 25
# Base clips are normalised so their short side is at most this many pixels.
BASE_SHORT_SIDE = 720
# Longest base clip kept per avatar (seconds). Longer uploads are trimmed.
BASE_MAX_SECONDS = 20

DEFAULT_SETTINGS = {
    # Hard cap on the length of a rendered video, in seconds.
    "max_video_seconds": 15,
    # Local LLM (optional, free) used to write scripts: https://ollama.com
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:3b",
    # Threads for ONNX Runtime. 0 = use every CPU thread.
    "cpu_threads": 0,
}


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            settings.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    return settings


def save_settings(values: dict) -> dict:
    settings = load_settings()
    for key in DEFAULT_SETTINGS:
        if key in values:
            settings[key] = values[key]
    settings["max_video_seconds"] = max(3, min(int(settings["max_video_seconds"]), 60))
    settings["cpu_threads"] = max(0, int(settings["cpu_threads"]))
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings
