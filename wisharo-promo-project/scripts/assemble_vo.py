"""Place each narration line at its scene start and write public/audio/narration.wav.

Line start times (seconds) are the single source of truth for scene timing;
src/data/timeline.json is written from the same table so Remotion and the
audio never drift apart.
"""
import json, os
import numpy as np
from scipy.io import wavfile

ROOT = os.path.join(os.path.dirname(__file__), "..")
LINES = os.path.join(ROOT, "public", "audio", "lines")
SR = 48000
TOTAL = 30.0

# (scene id, line file, when the speech should START in the video, seconds)
# Each line file has ~0.24 s of leading silence, which we trim.
PLAN = [
    ("problem",    "l1.wav", 0.35),
    ("reveal",     "l2.wav", 5.75),
    ("pick",       "l3.wav", 10.75),
    ("background", "l4.wav", 15.35),
    ("stickers",   "l5.wav", 18.75),
    ("language",   "l6.wav", 23.15),
    ("cta",        "l7.wav", 26.55),
]


def speech_bounds(x, thr=10 ** (-45 / 20)):
    idx = np.where(np.abs(x) > thr)[0]
    return idx[0], idx[-1]


out = np.zeros(int(TOTAL * SR), dtype=np.float64)
timeline = []
for sid, f, start in PLAN:
    sr, x = wavfile.read(os.path.join(LINES, f))
    assert sr == SR
    x = x.astype(np.float64) / 32768.0
    a, b = speech_bounds(x)
    a = max(0, a - int(0.03 * SR))
    b = min(len(x), b + int(0.12 * SR))
    seg = x[a:b]
    i0 = int(start * SR)
    out[i0:i0 + len(seg)] += seg
    timeline.append({"id": sid, "voStart": round(start, 3), "voEnd": round(start + len(seg) / SR, 3)})

peak = np.max(np.abs(out))
out = out / peak * 0.89  # about -1 dBFS peak
wavfile.write(os.path.join(ROOT, "public", "audio", "narration.wav"), SR, (out * 32767).astype(np.int16))
os.makedirs(os.path.join(ROOT, "src", "data"), exist_ok=True)
json.dump(timeline, open(os.path.join(ROOT, "src", "data", "vo_timeline.json"), "w"), indent=1)
for t in timeline:
    print(t)
