#!/usr/bin/env python3
"""
Blackheads explainer - a 30 second animated video, generated entirely in code.

Pillow draws every frame (supersampled 2x for smooth edges), the frames are piped
into ffmpeg, and a soft synthesized ambient pad is mixed in as background audio.

Usage:
    python3 blackheads_video.py render blackheads_explainer.mp4
    python3 blackheads_video.py frames OUT_DIR 1.0 6.5 12.0     # preview PNGs at given seconds
"""
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1280, 720, 30, 30
S = 2  # supersampling factor

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

TEAL = (63, 208, 201)
YELLOW = (255, 209, 102)
PINK = (255, 122, 144)
BLUE = (110, 180, 255)
CREAM = (246, 226, 160)
INK = (10, 25, 38)
WHITE = (244, 248, 251)
MUTED = (178, 205, 218)


# ----------------------------------------------------------------- helpers
_fc = {}


def font(sz, bold=True):
    k = (sz, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_B if bold else FONT_R, int(sz * S))
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def eo(x):
    return 1 - (1 - x) ** 3


def eio(x):
    return 3 * x * x - 2 * x ** 3


def eob(x):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def A(c, a):
    return (*c, int(255 * clamp(a)))


def sc(pts):
    return [(x * S, y * S) for x, y in pts]


def ell(d, cx, cy, rx, ry=None, fill=None, outline=None, width=1):
    ry = rx if ry is None else ry
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S],
              fill=fill, outline=outline, width=max(1, int(width * S)))


def rrect(d, x0, y0, x1, y1, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S,
                        fill=fill, outline=outline, width=max(1, int(width * S)))


def line(d, pts, fill, width):
    d.line(sc(pts), fill=fill, width=max(1, int(width * S)), joint="curve")


def poly(d, pts, fill):
    d.polygon(sc(pts), fill=fill)


def txt(d, x, y, s, size, fill, bold=True, anchor="la"):
    if len(fill) == 4 and fill[3] <= 0:  # Pillow draws alpha-0 text fully opaque, so skip it
        return
    d.text((x * S, y * S), s, font=font(size, bold), fill=fill, anchor=anchor)


def tw(s, size, bold=True):
    return font(size, bold).getlength(s) / S


def wrap(s, size, bold, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(trial, size, bold) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


_bg = {}


def gradient(top, bot, name):
    if name not in _bg:
        t = np.linspace(0, 1, H * S)[:, None, None]
        a = np.array(top, dtype=float)[None, None, :]
        b = np.array(bot, dtype=float)[None, None, :]
        arr = np.repeat((a + (b - a) * t).astype(np.uint8), W * S, axis=1)
        _bg[name] = Image.fromarray(arr, "RGB")
    return _bg[name].copy()


def new_canvas():
    im = gradient((8, 22, 34), (16, 66, 80), "main")
    return im, ImageDraw.Draw(im, "RGBA")


def fadein(t, start, dur=0.5):
    p = eo(prog(t, start, start + dur))
    return p, (1 - p) * 16


def pill(d, x, y, s, size=20, alpha=1.0, accent=TEAL):
    w = tw(s, size) + 28
    rrect(d, x, y - 19, x + w, y + 19, 19, fill=A((10, 25, 38), 0.82 * alpha),
          outline=A(accent, alpha), width=1.5)
    txt(d, x + 14, y, s, size, A(WHITE, alpha), anchor="lm")
    return w


BUB = []
_r = random.Random(7)
for _ in range(26):
    BUB.append((_r.uniform(0, W), _r.uniform(0, H + 200), _r.uniform(8, 46),
                _r.uniform(8, 26), _r.uniform(0, 6.28)))


def bubbles(d, t, a=1.0):
    for x, y0, r, sp, ph in BUB:
        y = (y0 - sp * t) % (H + 200) - 100
        xx = x + 14 * math.sin(t * 0.8 + ph)
        ell(d, xx, y, r, fill=A(TEAL, 0.09 * a), outline=A((120, 230, 225), 0.32 * a), width=1.5)
        ell(d, xx - r * 0.3, y - r * 0.3, r * 0.18, fill=A(WHITE, 0.25 * a))


# ------------------------------------------------------------ scene: title
def scene_title(t):
    im, d = new_canvas()
    bubbles(d, t)
    for k in range(3):
        ph = (t * 0.45 + k / 3) % 1
        r = lerp(60, 430, ph)
        ell(d, W / 2, 330, r, outline=A(TEAL, 0.28 * (1 - ph)), width=2.5)

    # badge
    pa = eo(prog(t, 0.2, 0.8))
    label = "SKIN SCIENCE  -  30 SEC EXPLAINER"
    bw = tw(label, 20) + 40
    rrect(d, W / 2 - bw / 2, 175 - 20 + (1 - pa) * 14, W / 2 + bw / 2, 175 + 20 + (1 - pa) * 14, 20,
          fill=A(TEAL, 0.16 * pa), outline=A(TEAL, pa), width=1.5)
    txt(d, W / 2, 175 + (1 - pa) * 14, label, 20, A(TEAL, pa), anchor="mm")

    # letters
    word, size, gap = "BLACKHEADS", 138, 8
    widths = [tw(c, size) for c in word]
    total = sum(widths) + gap * (len(word) - 1)
    x = (W - total) / 2
    for i, c in enumerate(word):
        s0 = 0.45 + i * 0.09
        p = eob(prog(t, s0, s0 + 0.55))
        a = clamp(prog(t, s0, s0 + 0.3))
        col = WHITE if i < 5 else TEAL
        txt(d, x, 310 + (1 - p) * 70, c, size, A(col, a), anchor="lm")
        x += widths[i] + gap

    # underline + subtitle
    up = eio(prog(t, 1.5, 2.4))
    line(d, [(W / 2 - 230 * up, 405), (W / 2 + 230 * up, 405)], A(YELLOW, 1), 5)
    sa, soff = fadein(t, 1.9, 0.7)
    txt(d, W / 2, 462 + soff, "What are they - and why do they happen?", 36, A(MUTED, sa), bold=False, anchor="mm")
    return im


# ------------------------------------------------------- scene: skin close-up
CX, SURF = 360, 300
CAV_BOT = 545
EPI, DERM, EPI_LINE = (241, 195, 165), (229, 154, 138), (214, 140, 120)
CAV, CAV_EDGE = (122, 64, 60), (88, 40, 38)
SEBUM = (247, 222, 120)
CELLS = [(-22, 4), (6, 8), (22, 2), (-8, 26), (14, 34), (-20, 44), (2, 52), (22, 58)]


def hw(y):
    if y <= 420:
        return 36 + 8 * clamp((y - SURF) / 120)
    if y <= 490:
        return 44 + 51 * eio((y - 420) / 70)
    return 95 * math.sqrt(max(0.0, 1 - ((y - 490) / 55) ** 2))


def cav_side(y0, y1, step=3):
    ys = list(range(int(y0), int(y1) + 1, step))
    if ys[-1] != int(y1):
        ys.append(int(y1))
    left = [(CX - hw(y), y) for y in ys]
    right = [(CX + hw(y), y) for y in reversed(ys)]
    return left, right


def cav_poly(y0, y1):
    l, r = cav_side(y0, y1)
    return l + r


def bullets(d, x, y0, items, u, gate):
    y = y0
    for text, start, style in items:
        bold = style == "accent"
        size = 34 if bold else 28
        lines = wrap(text, size, bold, 474)
        p, off = fadein(u, start)
        al = p * gate
        col = YELLOW if bold else WHITE
        ell(d, x + 6, y + 18 + off, 6, fill=A(TEAL, al))
        for i, ln in enumerate(lines):
            txt(d, x + 28, y + i * 40 + off, ln, size, A(col, al), bold=bold)
        y += 40 * len(lines) + 24


def scene_skin(t):
    u = t - 4
    im, d = new_canvas()

    # ---- skin block
    rrect(d, 40, SURF, 680, 780, 26, fill=DERM)
    rrect(d, 40, SURF, 680, 352, 26, fill=EPI)
    d.rectangle([40 * S, 330 * S, 680 * S, 352 * S], fill=EPI)
    line(d, [(40, 352), (680, 352)], EPI_LINE, 2)
    for (x, y, r) in [(110, 600, 20), (230, 660, 14), (560, 640, 24), (620, 560, 12), (150, 520, 10)]:
        ell(d, x, y, r, fill=(200, 110, 105, 130))
    line(d, [(66, SURF + 1.5), (CX - 36, SURF + 1.5)], (255, 232, 210), 3)
    line(d, [(CX + 36, SURF + 1.5), (654, SURF + 1.5)], (255, 232, 210), 3)

    # ---- pore cavity
    poly(d, cav_poly(SURF, CAV_BOT), CAV)
    l, r = cav_side(SURF, CAV_BOT)
    line(d, l, CAV_EDGE, 3)
    line(d, r, CAV_EDGE, 3)

    # ---- oil gland + duct
    gp = 1 + 0.03 * math.sin(u * 4)
    line(d, [(512, 478), (452, 488)], (240, 205, 110), 14)
    ell(d, 556, 470, 48 * gp, 34 * gp, fill=(243, 213, 107), outline=(205, 160, 60), width=2.5)
    if 0.7 < u < 4.4:
        for i in range(4):
            k = (u * 1.7 + i / 4) % 1
            ell(d, lerp(525, 458, k), lerp(478, 488, k), 5, fill=A((250, 232, 140), math.sin(math.pi * k)))

    # ---- sebum fill (rises from the bottom)
    f = eio(prog(u, 0.8, 4.0))
    if f > 0.001:
        level = lerp(CAV_BOT, SURF + 3, f)
        poly(d, cav_poly(level, CAV_BOT), SEBUM)

    # ---- dead skin cells fall in
    for i, (dx, dy) in enumerate(CELLS):
        s0 = 1.4 + i * 0.38
        p = prog(u, s0, s0 + 1.1)
        if p <= 0:
            continue
        pe = p * p
        y = lerp(150, SURF + 8 + dy, pe)
        x = CX + dx + (1 - pe) * 10 * math.sin(i * 1.7 + u * 2)
        a = clamp(p * 4)
        ell(d, x, y, 11, 7, fill=A((255, 243, 220), a), outline=A((190, 150, 120), a), width=1.5)

    # ---- oxidation: plug darkens from the top down
    ox = eio(prog(u, 7.4, 11.2))
    if ox > 0.001:
        depth = 22 + 55 * ox
        poly(d, cav_poly(SURF, SURF + depth), A((22, 16, 14), clamp(ox * 1.6) * 0.98))

    # ---- the visible dome of the blackhead
    grow = eo(prog(u, 3.6, 4.8))
    if grow > 0:
        ry = 11 * grow
        col = mix(CREAM, (24, 18, 16), clamp(ox * 1.4))
        d.pieslice([(CX - 40) * S, (SURF - ry) * S, (CX + 40) * S, (SURF + ry) * S], 180, 360, fill=col)

    # ---- oxygen particles
    if 7.3 < u < 11.6:
        for i in range(8):
            ph = ((u - 7.3) * 0.5 + i / 8) % 1
            px = CX + (i - 3.5) * 46 * (1 - ph)
            py = lerp(150, SURF - 14, ph)
            a = math.sin(math.pi * ph) * clamp(prog(u, 7.3, 8.0)) * (1 - prog(u, 11.0, 11.6))
            ell(d, px, py, 13, fill=A((80, 170, 255), 0.85 * a))
            txt(d, px, py, "O₂", 13, A(WHITE, a), anchor="mm")

    # ---- callout labels (phase 1)
    la = prog(u, 3.6, 4.2) * (1 - prog(u, 6.4, 6.9))
    if la > 0:
        for (px, py, s, tx, ty) in [
            (90, 225, "Pore opening", CX - 30, SURF - 2),
            (70, 345, "Dead skin cells", CX - 24, 333),
            (70, 440, "Sebum (oil)", CX - 60, 452),
            (470, 575, "Oil gland", 556, 506),
        ]:
            w = pill(d, px, py, s, 20, la)
            sx = px + w if px < CX else px + w / 2
            sy = py if px < CX else py - 19
            line(d, [(sx, sy), (tx, ty)], A(TEAL, la), 2)
            ell(d, tx, ty, 5, fill=A(TEAL, la))

    # ---- callout (phase 2)
    ba = eo(prog(u, 11.4, 12.0))
    if ba > 0:
        w = pill(d, CX + 70, 235, "Blackhead!", 22, ba, accent=YELLOW)
        line(d, [(CX + 70, 235), (CX + 10, SURF - 14)], A(YELLOW, ba), 2)
        ell(d, CX + 10, SURF - 14, 5, fill=A(YELLOW, ba))

    # ---- right-hand text
    g1 = 1 - prog(u, 6.5, 7.0)
    if g1 > 0:
        p, off = fadein(u, 0.25)
        for i, ln in enumerate(["What is a", "blackhead?"]):
            txt(d, 730, 170 + i * 64 + off, ln, 54, A(WHITE, p * g1))
        bullets(d, 730, 340, [("A small bump called an open comedone.", 1.0, "n"),
                              ("Oil (sebum) and dead skin cells clog the pore.", 3.0, "n")], u, g1)
    if u > 7.0:
        p, off = fadein(u, 7.2)
        for i, ln in enumerate(["Why is it", "black?"]):
            txt(d, 730, 170 + i * 64 + off, ln, 54, A(WHITE, p))
        bullets(d, 730, 340, [("Not dirt!", 7.9, "accent"),
                              ("The plug is open to the air, so the oil oxidizes and darkens.", 9.2, "n")], u, 1.0)
    return im


# ------------------------------------------------------------ scene: causes
def glyph(d, kind, ix, iy, v):
    c = INK
    if kind == "drop":
        poly(d, [(ix - 15, iy), (ix + 15, iy), (ix, iy - 27)], c)
        ell(d, ix, iy + 6, 17, fill=c)
    elif kind == "cells":
        for dx, dy, rx, ry in [(-12, -8, 12, 8), (11, -10, 11, 7), (0, 4, 13, 8), (-14, 14, 10, 7), (14, 14, 11, 7)]:
            ell(d, ix + dx, iy + dy, rx, ry, fill=c)
    elif kind == "wave":
        pts = [(ix - 28 + i, iy + 12 * math.sin((i / 56) * 4 * math.pi + v * 4)) for i in range(0, 57, 3)]
        line(d, pts, c, 5)
    elif kind == "cloud":
        for dx, dy, rx, ry in [(-13, 4, 13, 11), (4, -6, 15, 14), (17, 5, 11, 10)]:
            ell(d, ix + dx, iy + dy, rx, ry, fill=c)
        d.rectangle([(ix - 13) * S, (iy + 4) * S, (ix + 17) * S, (iy + 15) * S], fill=c)


def scene_causes(t):
    v = t - 17
    im, d = new_canvas()
    bubbles(d, t, 0.5)
    p, off = fadein(v, 0.0)
    txt(d, W / 2, 105 + off, "What causes them?", 54, A(WHITE, p), anchor="mm")

    cards = [
        ("Excess oil", "Pores make too much sebum", YELLOW, "drop"),
        ("Dead skin cells", "Build up and block pores", CREAM, "cells"),
        ("Hormones", "Puberty, periods, stress", PINK, "wave"),
        ("Sweat & makeup", "Heavy products clog pores", BLUE, "cloud"),
    ]
    for i, (title, sub, col, kind) in enumerate(cards):
        x0 = 70 + (i % 2) * 600
        y0 = 190 + (i // 2) * 190
        s0 = 0.5 + i * 0.7
        pp = eob(prog(v, s0, s0 + 0.6))
        a = clamp(pp)
        yo = (1 - clamp(pp, 0, 1)) * 40
        rrect(d, x0, y0 + yo, x0 + 540, y0 + 150 + yo, 22, fill=A(WHITE, 0.09 * a), outline=A(WHITE, 0.25 * a), width=1.5)
        ix, iy = x0 + 80, y0 + 75 + yo
        ell(d, ix, iy, 44 + 2 * math.sin(v * 3 + i), fill=A(col, a))
        if a > 0.05:
            glyph(d, kind, ix, iy, v)
        txt(d, x0 + 148, iy - 20, title, 30, A(WHITE, a), anchor="lm")
        txt(d, x0 + 148, iy + 22, sub, 21, A(MUTED, a), bold=False, anchor="lm")

    fa, fo = fadein(v, 4.3, 0.7)
    txt(d, W / 2, 610 + fo, "Hormones + oil + dead cells  =  clogged pores", 30, A(YELLOW, fa), anchor="mm")
    return im


# -------------------------------------------------------------- scene: tips
def scene_tips(t):
    w = t - 23
    im, d = new_canvas()
    bubbles(d, t, 0.5)
    p, off = fadein(w, 0.0)
    txt(d, W / 2, 105 + off, "How to manage them", 54, A(WHITE, p), anchor="mm")

    rows = [
        ("Wash gently, twice a day", True),
        ("Use salicylic acid (BHA) or a retinoid", True),
        ("Choose \"non-comedogenic\" products", True),
        ("Never squeeze or pick at them", False),
    ]
    for i, (text, ok) in enumerate(rows):
        s0 = 0.5 + i * 0.75
        pp = eo(prog(w, s0, s0 + 0.5))
        xo = (1 - pp) * -60
        cy = 215 + i * 100
        col = (80, 220, 150) if ok else (255, 100, 110)
        rrect(d, 120 + xo, cy - 38, 1160 + xo, cy + 38, 20, fill=A(WHITE, 0.08 * pp), outline=A(WHITE, 0.22 * pp), width=1.5)
        ix = 180 + xo
        ell(d, ix, cy, 26, fill=A(col, pp), outline=None)
        cp = eio(prog(w, s0 + 0.35, s0 + 0.85))
        if ok:
            pts = [(-11, 1), (-3, 10), (13, -9)]
            seg = cp * 2
            path = [(ix + pts[0][0], cy + pts[0][1])]
            for k in range(2):
                f = clamp(seg - k)
                if f <= 0:
                    break
                a_, b_ = pts[k], pts[k + 1]
                path.append((ix + lerp(a_[0], b_[0], f), cy + lerp(a_[1], b_[1], f)))
            if len(path) > 1:
                line(d, path, A(INK, 1), 5)
        else:
            m = 10 * cp
            line(d, [(ix - m, cy - m), (ix + m, cy + m)], A(INK, 1), 5)
            line(d, [(ix + m, cy - m), (ix - m, cy + m)], A(INK, 1), 5)
        txt(d, 235 + xo, cy, text, 29, A(WHITE, pp), anchor="lm")

    fa, fo = fadein(w, 3.7, 0.7)
    txt(d, W / 2, 635 + fo, "Be patient - results take 6 to 8 weeks.", 28, A(YELLOW, fa), anchor="mm")
    return im


# --------------------------------------------------------------- scene: end
def scene_end(t):
    x = t - 28
    im, d = new_canvas()
    bubbles(d, t)
    for k in range(2):
        ph = (t * 0.45 + k / 2) % 1
        ell(d, W / 2, 330, lerp(60, 380, ph), outline=A(TEAL, 0.25 * (1 - ph)), width=2.5)
    a1, o1 = fadein(x, 0.1, 0.5)
    a2, o2 = fadein(x, 0.5, 0.5)
    a3, o3 = fadein(x, 0.9, 0.5)
    txt(d, W / 2, 255 + o1, "Blackhead", 44, A(MUTED, a1), bold=False, anchor="mm")
    txt(d, W / 2, 330 + o2, "clogged pore  +  air", 66, A(WHITE, a2), anchor="mm")
    txt(d, W / 2, 410 + o2, "Harmless, common and treatable.", 34, A(YELLOW, a2), bold=False, anchor="mm")
    txt(d, W / 2, 520 + o3, "Persistent or painful? Ask a dermatologist.", 24, A(MUTED, a3), bold=False, anchor="mm")
    return im


# ------------------------------------------------------------------ driver
SCENES = [(0, scene_title), (4, scene_skin), (17, scene_causes), (23, scene_tips), (28, scene_end)]
XFADE = 0.5


def frame_image(t):
    idx = max(i for i, (s, _) in enumerate(SCENES) if t >= s)
    start, fn = SCENES[idx]
    im = fn(t)
    if idx > 0 and t < start + XFADE:
        prev = SCENES[idx - 1][1](t)
        im = Image.blend(prev, im, eio((t - start) / XFADE))
    d = ImageDraw.Draw(im, "RGBA")
    # persistent chrome: progress bar + small header chip after the title scene
    d.rectangle([0, (H - 6) * S, W * S, H * S], fill=(255, 255, 255, 30))
    d.rectangle([0, (H - 6) * S, W * S * t / DUR, H * S], fill=A(TEAL, 1))
    ca = prog(t, 4.0, 4.6) * (1 - prog(t, 27.6, 28.1))
    if ca > 0:
        pill(d, 36, 40, "BLACKHEADS 101", 18, ca)
    return im.resize((W, H), Image.LANCZOS)


def frame_bytes(i):
    return frame_image(i / FPS).tobytes()


def render(out):
    total = DUR * FPS
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        # soft ambient pad (A major chord) so the video is not silent
        "-f", "lavfi", "-i", f"sine=f=110:d={DUR}",
        "-f", "lavfi", "-i", f"sine=f=220:d={DUR}",
        "-f", "lavfi", "-i", f"sine=f=277.18:d={DUR}",
        "-f", "lavfi", "-i", f"sine=f=329.63:d={DUR}",
        "-filter_complex",
        f"[1:a][2:a][3:a][4:a]amix=inputs=4:normalize=0,volume=0.16,tremolo=f=0.3:d=0.35,"
        f"lowpass=f=900,aecho=0.8:0.5:600:0.3,afade=t=in:d=2,afade=t=out:st={DUR - 3}:d=3[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", str(DUR), out,
    ]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count() or 2) as pool:
        for n, b in enumerate(pool.imap(frame_bytes, range(total), chunksize=4)):
            ff.stdin.write(b)
            if n % 90 == 0:
                print(f"frame {n}/{total}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done:", out)


if __name__ == "__main__":
    if sys.argv[1] == "render":
        render(sys.argv[2])
    elif sys.argv[1] == "frames":
        os.makedirs(sys.argv[2], exist_ok=True)
        for ts in sys.argv[3:]:
            frame_image(float(ts)).save(os.path.join(sys.argv[2], f"t{float(ts):05.2f}.png"))
