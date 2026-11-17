"""Generate all SFX and the music bed procedurally (no third-party samples).

Everything here is synthesized from sine waves and seeded noise, so the
output is original and free of licensing restrictions.
Run: python3 scripts/gen_audio.py  (writes into public/audio/)
"""
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
OUT = os.path.join(os.path.dirname(__file__), "..", "public", "audio")
rng = np.random.default_rng(7)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def write(name, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    wavfile.write(os.path.join(OUT, name), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    print("wrote", name, f"{len(x)/SR:.2f}s")


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def reverb(x, sec=1.8, mix=0.25, seed=3):
    r = np.random.default_rng(seed)
    t = t_axis(sec)
    ir_l = r.standard_normal(len(t)) * np.exp(-t * 3.2)
    ir_r = r.standard_normal(len(t)) * np.exp(-t * 3.2)
    ir_l, ir_r = lp(ir_l, 6000), lp(ir_r, 6000)
    mono = x if x.ndim == 1 else x.mean(axis=1)
    wl = fftconvolve(mono, ir_l)[: len(mono)]
    wr = fftconvolve(mono, ir_r)[: len(mono)]
    wet = np.stack([wl, wr], 1)
    wet = wet / (np.max(np.abs(wet)) or 1) * np.max(np.abs(mono))
    dry = np.stack([mono, mono], 1) if x.ndim == 1 else x
    return dry * (1 - mix) + wet * mix


# ---------- whoosh: band-passed noise with a rising/falling centre ----------
def whoosh(sec=0.7):
    t = t_axis(sec)
    n = rng.standard_normal(len(t))
    env = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 2.2
    # sweep a resonant band-pass by processing in short blocks
    out = np.zeros_like(n)
    blk = 512
    for i in range(0, len(n), blk):
        p = i / len(n)
        fc = 300 + 2600 * np.sin(np.pi * p) ** 1.5
        seg = n[max(0, i - 2048): i + blk]
        y = bp(seg, fc * 0.6, min(fc * 1.6, 20000))
        out[i:i + blk] = y[-len(n[i:i + blk]):]
    x = out * env
    st = np.stack([x * (1 - 0.4 * t / sec), x * (0.6 + 0.4 * t / sec)], 1)  # slight L->R pan
    return norm(reverb(st, 0.9, 0.18), 0.7)


# ---------- soft click: tiny filtered transient + woody body ----------
def click():
    t = t_axis(0.12)
    tick = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 900)
    body = np.sin(2 * np.pi * 1850 * t) * np.exp(-t * 140) * 0.5
    thump = np.sin(2 * np.pi * 420 * t) * np.exp(-t * 60) * 0.35
    return norm(tick * 0.6 + body + thump, 0.55)


# ---------- sparkle chime: bright bell partials, quick arpeggio ----------
def chime(seed=0):
    r = np.random.default_rng(11 + seed)
    t = t_axis(1.4)
    x = np.zeros_like(t)
    notes = [2093.0, 2637.0, 3136.0, 3951.0]  # C7 E7 G7 B7
    r.shuffle(notes)
    for k, f in enumerate(notes):
        d = int((0.035 * k) * SR)
        tt = t[: len(t) - d]
        bell = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt)
                + 0.15 * np.sin(2 * np.pi * f * 5.4 * tt)) * np.exp(-tt * (5 + k))
        x[d:] += bell * (0.9 - 0.12 * k)
    shimmer = hp(r.standard_normal(len(t)), 7000) * np.exp(-t * 9) * 0.08
    return norm(reverb(x + shimmer, 1.4, 0.35), 0.5)


# ---------- low boom: sub sine drop + soft noise thump + long tail ----------
def boom():
    t = t_axis(2.6)
    f = 62 * np.exp(-t * 1.3) + 34
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t * 1.6)
    thump = lp(rng.standard_normal(len(t)), 220) * np.exp(-t * 14) * 2.0
    air = bp(rng.standard_normal(len(t)), 300, 1400) * np.exp(-t * 6) * 0.15
    x = sub + thump + air
    x = np.tanh(x * 1.4)
    return norm(reverb(x, 2.2, 0.3), 0.85)


# ---------- music bed: warm pad + soft pluck arpeggio, 30.5 s ----------
def music(sec=30.5, bpm=84):
    t = t_axis(sec)
    beat = 60 / bpm
    bar = beat * 4
    # Dmaj9 -> Bm9 -> Gmaj9 -> A6/9 (A section repeats)
    chords = [
        [146.83, 220.0, 277.18, 329.63, 369.99],
        [123.47, 185.0, 220.0, 277.18, 293.66],
        [98.0, 146.83, 196.0, 246.94, 293.66],
        [110.0, 164.81, 220.0, 277.18, 246.94],
    ]
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    nbars = int(np.ceil(sec / bar))
    for b in range(nbars):
        ch = chords[b % 4]
        s0 = b * bar
        i0, i1 = int(s0 * SR), min(int((s0 + bar + 1.2) * SR), len(t))
        tt = t[i0:i1] - s0
        env = np.clip(tt / 0.9, 0, 1) * np.clip((bar + 1.2 - tt) / 1.2, 0, 1)
        for j, f in enumerate(ch):
            det = 1 + 0.0025 * (j - 2)
            v = (np.sin(2 * np.pi * f * det * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt + j)) * env
            L[i0:i1] += v * (0.55 + 0.1 * (j % 2))
            R[i0:i1] += v * (0.65 - 0.1 * (j % 2))
        # pluck arpeggio, 8th notes
        for k in range(8):
            f = ch[[1, 2, 3, 4, 3, 2, 4, 3][k]] * 2
            ps = s0 + k * beat / 2
            p0 = int(ps * SR)
            if p0 >= len(t):
                break
            p1 = min(p0 + int(0.9 * SR), len(t))
            tp = t[p0:p1] - ps
            pl = (np.sin(2 * np.pi * f * tp) + 0.2 * np.sin(2 * np.pi * f * 3 * tp)) * np.exp(-tp * 5.5) * 0.32
            pan = 0.5 + 0.3 * np.sin(k)
            L[p0:p1] += pl * (1 - pan)
            R[p0:p1] += pl * pan
    # soft "heartbeat" low pulse on beats 1 & 3, very quiet
    for b in range(int(sec / beat)):
        if b % 2:
            continue
        p0 = int(b * beat * SR)
        p1 = min(p0 + int(0.4 * SR), len(t))
        tp = t[p0:p1] - b * beat
        k = np.sin(2 * np.pi * (55 + 30 * np.exp(-tp * 30)) * tp) * np.exp(-tp * 9) * 0.5
        L[p0:p1] += k
        R[p0:p1] += k
    st = np.stack([lp(L, 5200), lp(R, 5200)], 1)
    st = reverb(st, 2.4, 0.3)
    fade_in = np.clip(t / 1.0, 0, 1)
    fade_out = np.clip((sec - t) / 2.0, 0, 1)
    st *= (fade_in * fade_out)[:, None]
    return norm(st, 0.8)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write("sfx_whoosh.wav", whoosh())
    write("sfx_click.wav", click())
    for i in range(3):
        write(f"sfx_chime{i}.wav", chime(i))
    write("sfx_boom.wav", boom())
    write("music_bed.wav", music())
