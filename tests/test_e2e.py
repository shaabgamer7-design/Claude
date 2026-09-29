"""End-to-end test with stand-in models (no internet needed).

    python tests/make_test_models.py /tmp/as-models
    AVATAR_STUDIO_MODELS=/tmp/as-models AVATAR_STUDIO_DATA=/tmp/as-data python tests/test_e2e.py
"""
import io
import json
import math
import os
import sys
import time
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import media  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def wait(job, timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = client.get(f"/api/jobs/{job['id']}").json()
        if j["status"] in ("done", "error"):
            assert j["status"] == "done", j["error"]
            return j
        time.sleep(0.5)
    raise TimeoutError(job)


def face_png():
    from skimage import data
    import cv2
    img = cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def speech_like_wav(seconds=4.0, sr=16000):
    t = np.arange(int(seconds * sr)) / sr
    env = (np.sin(2 * math.pi * 3 * t) > -0.2).astype(np.float32)  # syllable-ish bursts
    sig = 0.3 * env * np.sin(2 * math.pi * 180 * t) * (1 + 0.5 * np.sin(2 * math.pi * 5 * t))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())
    return buf.getvalue()


def test_full_flow():
    st = client.get("/api/status").json()
    assert st["models"]["wav2lip"]["ready"], "run tests/make_test_models.py first"

    persona = {"name": "Test Nova", "tone": "Energetic", "niche": "AI tools",
               "language": "English", "cta": "Follow for more"}
    r = client.post("/api/avatars", data={"data": json.dumps(persona)},
                    files={"face": ("face.png", face_png(), "image/png"),
                           "voice_sample": ("v.wav", speech_like_wav(3), "audio/wav")})
    assert r.status_code == 200, r.text
    wait(r.json()["job"])
    avatar = client.get(f"/api/avatars/{r.json()['avatar']['id']}").json()
    assert avatar["status"] == "ready" and avatar["base"]["frames"] == 250
    assert avatar["has_voice_sample"]

    prompt = client.post("/api/script/prompt", json={"avatar_id": avatar["id"],
                                                     "topic": "3 free AI tools"}).json()
    assert "Energetic" in prompt["prompt"]

    for quality, aspect, style in [("studio", "9:16", "pop"), ("fast", "16:9", "clean")]:
        params = {"avatar_id": avatar["id"], "voice_mode": "upload", "quality": quality,
                  "aspect": aspect, "caption_style": style,
                  "script": "This is a quick test of the avatar studio captions."}
        t0 = time.time()
        r = client.post("/api/render", data={"data": json.dumps(params)},
                        files={"audio": ("a.wav", speech_like_wav(4), "audio/wav")})
        assert r.status_code == 200, r.text
        meta = wait(r.json())["result"]
        print(quality, aspect, "rendered in", round(time.time() - t0, 1), "s", meta)
        vid = Path(os.environ["AVATAR_STUDIO_DATA"]) / "videos" / meta["id"] / "video.mp4"
        assert vid.exists()
        w, h = media.video_size(vid)
        assert (w, h) == {"9:16": (720, 1280), "16:9": (1280, 720)}[aspect]
        assert 3.5 < media.probe_duration(vid) < 5.0

    # A video avatar, using the photo avatar's base clip as the upload.
    base = Path(os.environ["AVATAR_STUDIO_DATA"]) / "avatars" / avatar["id"] / "base.mp4"
    r = client.post("/api/avatars", data={"data": json.dumps({"name": "Video twin"})},
                    files={"face": ("me.mp4", base.read_bytes(), "video/mp4")})
    wait(r.json()["job"])
    v_avatar = client.get(f"/api/avatars/{r.json()['avatar']['id']}").json()
    assert v_avatar["base"]["kind"] == "video", v_avatar
    assert len(client.get("/api/videos").json()) == 2


if __name__ == "__main__":
    test_full_flow()
    print("E2E OK")
