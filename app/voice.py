"""Voice generation.

Engines (all free):
  * "tts"    - Microsoft Edge neural voices via the `edge-tts` package. No API key,
               needs an internet connection. Includes Urdu, Hindi, Arabic, English.
               Gives exact word timings for captions.
  * "clone"  - Chatterbox (MIT licence) zero-shot voice cloning from the avatar's
               voice sample, fully offline on CPU. Optional add-on, installed into
               its own environment by `install_voice_clone` so its heavy
               dependencies never clash with the main app.
  * "upload" - your own recording (best for Urdu: nothing beats your real voice).

Any of them can then be passed through Chatterbox voice conversion to make it
sound like the avatar's voice sample ("convert" option).
"""
import asyncio
import os
import re
import subprocess
import sys
import time

import numpy as np

from .config import ROOT

CURATED_VOICES = [
    ("en-US-AndrewMultilingualNeural", "English (US) - Andrew, warm male"),
    ("en-US-BrianMultilingualNeural", "English (US) - Brian, casual male"),
    ("en-US-AvaMultilingualNeural", "English (US) - Ava, bright female"),
    ("en-US-EmmaMultilingualNeural", "English (US) - Emma, friendly female"),
    ("en-US-GuyNeural", "English (US) - Guy, newscaster male"),
    ("en-US-JennyNeural", "English (US) - Jenny, female"),
    ("en-GB-RyanNeural", "English (UK) - Ryan, male"),
    ("en-GB-SoniaNeural", "English (UK) - Sonia, female"),
    ("en-IN-PrabhatNeural", "English (India) - Prabhat, male"),
    ("en-IN-NeerjaNeural", "English (India) - Neerja, female"),
    ("ur-PK-AsadNeural", "Urdu (Pakistan) - Asad, male"),
    ("ur-PK-UzmaNeural", "Urdu (Pakistan) - Uzma, female"),
    ("ur-IN-SalmanNeural", "Urdu (India) - Salman, male"),
    ("ur-IN-GulNeural", "Urdu (India) - Gul, female"),
    ("hi-IN-MadhurNeural", "Hindi - Madhur, male"),
    ("hi-IN-SwaraNeural", "Hindi - Swara, female"),
    ("ar-SA-HamedNeural", "Arabic (Saudi) - Hamed, male"),
    ("ar-SA-ZariyahNeural", "Arabic (Saudi) - Zariyah, female"),
    ("ar-AE-HamdanNeural", "Arabic (UAE) - Hamdan, male"),
]

_voice_cache = None
_voice_fail_time = 0.0


def list_tts_voices():
    """All Edge voices when online (cached), else the curated list."""
    global _voice_cache, _voice_fail_time
    if _voice_cache:
        return _voice_cache
    voices = [{"id": v, "label": label, "featured": True} for v, label in CURATED_VOICES]
    if time.time() - _voice_fail_time < 300:  # offline recently: don't wait again
        return voices
    try:
        import edge_tts
        live = asyncio.run(asyncio.wait_for(edge_tts.list_voices(), timeout=6))
        featured = {v for v, _ in CURATED_VOICES}
        for v in sorted(live, key=lambda x: x["ShortName"]):
            if v["ShortName"] not in featured:
                voices.append({"id": v["ShortName"],
                               "label": f"{v['Locale']} - {v['ShortName'].split('-')[-1]}"
                                        f" ({v.get('Gender', '').lower()})",
                               "featured": False})
        _voice_cache = voices
    except Exception:
        _voice_fail_time = time.time()
    return voices


def _signed(value, unit):
    value = int(value)
    return f"{'+' if value >= 0 else ''}{value}{unit}"


async def _edge(text, voice, rate, pitch, out_path):
    import edge_tts
    try:
        comm = edge_tts.Communicate(text, voice, rate=_signed(rate, "%"),
                                    pitch=_signed(pitch, "Hz"), boundary="WordBoundary")
    except TypeError:  # older edge-tts: word boundaries are the default
        comm = edge_tts.Communicate(text, voice, rate=_signed(rate, "%"),
                                    pitch=_signed(pitch, "Hz"))
    words = []
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append({"start": start, "end": start + chunk["duration"] / 1e7,
                              "text": chunk["text"]})
    return words


def tts(text, voice, out_path, rate=0, pitch=0):
    """Synthesize speech; returns word timings [{start, end, text}]."""
    try:
        return asyncio.run(_edge(text, voice, rate, pitch, out_path))
    except Exception as exc:
        raise RuntimeError(f"Neural TTS failed ({exc}). It needs an internet connection; "
                           "or record your own voice and use 'My recording'.") from exc


# ---- Chatterbox (optional, offline voice cloning) ---------------------------

def _voice_python():
    base = ROOT / "venv-voice"
    exe = base / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return exe if exe.exists() else None


def clone_available():
    return _voice_python() is not None


def _run_worker(args, timeout=3600):
    py = _voice_python()
    if not py:
        raise RuntimeError("Voice cloning is not installed. Run install_voice_clone "
                           "(see README) to add it.")
    cmd = [str(py), str(ROOT / "tools" / "voice_worker.py"), *map(str, args)]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if proc.returncode != 0:
        raise RuntimeError("Voice cloning failed: " + (proc.stderr or proc.stdout)[-1500:])


def clone_tts(text, reference_wav, out_path, language="en", expressiveness=0.5):
    # "--text=..." so a script starting with "-" is not mistaken for an option.
    _run_worker(["tts", f"--text={text}", "--ref", reference_wav, "--out", out_path,
                 "--lang", language, "--exaggeration", expressiveness])


def convert_voice(src_wav, reference_wav, out_path):
    _run_worker(["vc", "--src", src_wav, "--ref", reference_wav, "--out", out_path])


# ---- word timing estimate (for captions on non-TTS audio) -------------------

def split_words(text):
    return [w for w in re.split(r"\s+", text.strip()) if w]


def estimate_word_timings(text, wav16: np.ndarray, sr=16000):
    """Spread the script's words over the detected speech, weighted by length,
    and snapped to pauses so captions stay in step with the voice."""
    words = split_words(text)
    if not words or len(wav16) == 0:
        return []
    hop = int(0.02 * sr)
    frames = len(wav16) // hop
    if frames < 2:
        return []
    rms = np.sqrt(np.mean(wav16[: frames * hop].reshape(frames, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms / (rms.max() + 1e-9) + 1e-9)
    voiced = db > -32
    if not voiced.any():
        return []
    # Speech segments separated by >= 180 ms of silence.
    segments, start, gap = [], None, 0
    for i, v in enumerate(voiced):
        if v:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= 9:
                segments.append((start, i - gap + 1))
                start, gap = None, 0
    if start is not None:
        segments.append((start, frames - gap))
    seg_time = [((a * hop) / sr, (b * hop) / sr) for a, b in segments]
    total_speech = sum(b - a for a, b in seg_time) or 1e-6
    weights = np.array([len(w) + 2 for w in words], np.float32)
    per_word = weights / weights.sum() * total_speech

    timings, seg_i = [], 0
    t = seg_time[0][0]
    for w, dur in zip(words, per_word):
        while seg_i < len(seg_time) - 1 and t >= seg_time[seg_i][1] - 0.02:
            seg_i += 1
            t = max(t, seg_time[seg_i][0])
        timings.append({"start": float(t), "end": float(t + dur), "text": w})
        t += dur
    return timings


def main():  # quick manual test: python -m app.voice "Hello" en-US-AndrewMultilingualNeural
    text = sys.argv[1] if len(sys.argv) > 1 else "Hello from Avatar Studio."
    voice = sys.argv[2] if len(sys.argv) > 2 else CURATED_VOICES[0][0]
    print(tts(text, voice, "voice_test.mp3"))


if __name__ == "__main__":
    main()
