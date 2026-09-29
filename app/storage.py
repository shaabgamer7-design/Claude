"""Avatars and videos live as plain folders + JSON under data/. Easy to back up."""
import json
import shutil
import time
import uuid
from pathlib import Path

from .config import AVATARS_DIR, VIDEOS_DIR

PERSONA_FIELDS = {
    "name": "",
    "tagline": "",        # e.g. "Your daily dose of tech in 15 seconds"
    "niche": "",          # e.g. "AI tools, productivity"
    "tone": "",           # e.g. "Energetic, witty, confident"
    "personality": "",    # behaviour, how they talk, what they never do
    "audience": "",
    "language": "English",
    "catchphrases": "",
    "cta": "",            # call to action, e.g. "Follow for part 2"
    # voice defaults
    "voice_mode": "tts",  # tts | clone | upload
    "tts_voice": "en-US-AndrewMultilingualNeural",
    "tts_rate": 0,
    "tts_pitch": 0,
    "clone_language": "en",
    # look defaults
    "aspect": "9:16",
    "caption_style": "pop",
}


def _new_id():
    return time.strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6]


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write(path: Path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


# ---- avatars ----------------------------------------------------------------

def avatar_dir(avatar_id: str) -> Path:
    d = (AVATARS_DIR / avatar_id).resolve()
    if d.parent != AVATARS_DIR.resolve():
        raise ValueError("Bad avatar id")
    return d


def create_avatar(fields: dict) -> dict:
    avatar_id = _new_id()
    d = avatar_dir(avatar_id)
    d.mkdir(parents=True)
    data = dict(PERSONA_FIELDS)
    data.update({k: v for k, v in fields.items() if k in PERSONA_FIELDS})
    data.update({"id": avatar_id, "created": time.time(), "status": "preparing",
                 "has_voice_sample": False})
    _write(d / "avatar.json", data)
    return data


def get_avatar(avatar_id: str):
    data = _read(avatar_dir(avatar_id) / "avatar.json")
    if data is None:
        return None
    base = _read(avatar_dir(avatar_id) / "base.json")
    data["base"] = base
    return data


def update_avatar(avatar_id: str, fields: dict) -> dict:
    d = avatar_dir(avatar_id)
    data = _read(d / "avatar.json")
    if data is None:
        raise KeyError(avatar_id)
    for k, v in fields.items():
        if k in PERSONA_FIELDS or k in ("status", "error", "has_voice_sample"):
            data[k] = v
    _write(d / "avatar.json", data)
    return data


def list_avatars():
    out = []
    for d in AVATARS_DIR.iterdir():
        if d.is_dir():
            a = get_avatar(d.name)
            if a:
                out.append(a)
    return sorted(out, key=lambda a: a.get("created", 0), reverse=True)


def delete_avatar(avatar_id: str):
    shutil.rmtree(avatar_dir(avatar_id), ignore_errors=True)


# ---- videos -----------------------------------------------------------------

def video_dir(video_id: str) -> Path:
    d = (VIDEOS_DIR / video_id).resolve()
    if d.parent != VIDEOS_DIR.resolve():
        raise ValueError("Bad video id")
    return d


def new_video_dir():
    video_id = _new_id()
    d = video_dir(video_id)
    d.mkdir(parents=True)
    return video_id, d


def save_video_meta(video_id: str, meta: dict):
    _write(video_dir(video_id) / "meta.json", meta)


def list_videos():
    out = []
    for d in VIDEOS_DIR.iterdir():
        meta = _read(d / "meta.json") if d.is_dir() else None
        if meta and (d / "video.mp4").exists():
            out.append(meta)
    return sorted(out, key=lambda m: m.get("created", 0), reverse=True)


def delete_video(video_id: str):
    shutil.rmtree(video_dir(video_id), ignore_errors=True)
