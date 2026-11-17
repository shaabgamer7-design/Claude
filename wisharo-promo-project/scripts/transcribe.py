"""Word-level transcription of public/audio/narration.wav with faster-whisper.

Writes src/data/words.json (for burned-in captions) and out/captions.srt.
Whisper's spelling of brand words is corrected against the known script
(timings always come from Whisper).
"""
import json, os, re
from faster_whisper import WhisperModel
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

ROOT = os.path.join(os.path.dirname(__file__), "..")
WAV = os.path.join(ROOT, "public", "audio", "narration.wav")
SCRIPT = open(os.path.join(ROOT, "public", "audio", "script.txt")).read().split()

model = WhisperModel("small.en", device="cpu", compute_type="int8")
sr, pcm = wavfile.read(WAV)
audio16 = resample_poly(pcm.astype(np.float32) / 32768.0, 1, sr // 16000).astype(np.float32)
segs, _ = model.transcribe(audio16, word_timestamps=True, beam_size=5, vad_filter=False,
                           initial_prompt="Wisharo Studio. Make card. wisharo dot com.")
words = []
for s in segs:
    for w in s.words:
        words.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
print("whisper:", " ".join(w["text"] for w in words))
# Greedy alignment: merge whisper tokens until they spell the next script word
# (handles "sign up" -> "sign-up"); display text comes from the script.
aligned, i = [], 0
for ref in SCRIPT:
    if i >= len(words):
        break
    j, acc = i, ""
    while j < len(words) and len(acc) < len(norm(ref)):
        acc += norm(words[j]["text"]); j += 1
    if acc != norm(ref):
        print(f"  mismatch near '{ref}' ('{acc}')")
    aligned.append({"text": ref, "start": words[i]["start"], "end": words[j - 1]["end"]})
    i = j
if len(aligned) == len(SCRIPT):
    words = aligned
else:
    print("WARNING: alignment failed; keeping whisper text")

json.dump(words, open(os.path.join(ROOT, "src", "data", "words.json"), "w"), indent=1)


# SRT: one cue per sentence-ish phrase (split on . , ? !), max 5 words
def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02}:{int(m):02}:{int(s):02},{int(round((s % 1) * 1000)):03}"

cues, cur = [], []
for w in words:
    cur.append(w)
    if re.search(r"[.,?!]$", w["text"]) or len(cur) >= 7:
        cues.append(cur); cur = []
if cur:
    cues.append(cur)
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with open(os.path.join(ROOT, "out", "captions.srt"), "w") as f:
    for i, c in enumerate(cues, 1):
        f.write(f"{i}\n{ts(c[0]['start'])} --> {ts(c[-1]['end'])}\n{' '.join(x['text'] for x in c)}\n\n")
print(len(words), "words,", len(cues), "cues")
