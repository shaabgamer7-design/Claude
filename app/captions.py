"""Short-form style captions (burned in with libass through FFmpeg).

Styles:
  * "pop"   - 1-3 words at a time, the spoken word highlighted and popped in.
  * "clean" - short phrases in white, no highlight.
  * "none"
Works with right-to-left scripts (Urdu, Arabic): libass shapes them correctly.
"""
import os
import shutil
import sys
from pathlib import Path

ARABIC = [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]
DEVANAGARI = [(0x0900, 0x097F)]


def script_of(text):
    for ch in text:
        cp = ord(ch)
        if any(a <= cp <= b for a, b in ARABIC):
            return "arabic"
        if any(a <= cp <= b for a, b in DEVANAGARI):
            return "devanagari"
    return "latin"


def _font_dirs():
    if os.name == "nt":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        return [Path(windir) / "Fonts",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"]
    if sys.platform == "darwin":
        return [Path("/System/Library/Fonts/Supplemental"), Path("/Library/Fonts"),
                Path.home() / "Library/Fonts"]
    return [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"]


FONT_CANDIDATES = {
    "latin": ["Montserrat-ExtraBold.ttf", "Montserrat-Bold.ttf", "ariblk.ttf", "arialbd.ttf",
              "Arial Black.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
              "LiberationSans-Bold.ttf"],
    "arabic": ["NotoNastaliqUrdu-Bold.ttf", "NotoNastaliqUrdu-Regular.ttf", "UrdTypeb.ttf",
               "UrdType.ttf", "segoeuib.ttf", "tahomabd.ttf", "NotoSansArabic-Bold.ttf",
               "GeezaPro.ttc", "DejaVuSans-Bold.ttf"],
    "devanagari": ["NirmalaB.ttf", "Nirmala.ttf", "NotoSansDevanagari-Bold.ttf",
                   "Kohinoor.ttc", "DejaVuSans-Bold.ttf"],
}


def find_font(script):
    """Return (family_name, path) of the best installed font for a script."""
    for name in FONT_CANDIDATES[script]:
        for d in _font_dirs():
            if not d.exists():
                continue
            direct = d / name
            hits = [direct] if direct.exists() else list(d.rglob(name))[:1]
            for path in hits:
                try:
                    from PIL import ImageFont
                    family = ImageFont.truetype(str(path), 20).getname()[0]
                except Exception:
                    family = Path(name).stem.split("-")[0]
                return family, path
    return "Arial", None


def _ts(t):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _esc(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def _group(words, max_words, max_chars):
    groups, cur = [], []
    for w in words:
        text_len = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
        if cur and (len(cur) >= max_words or text_len > max_chars):
            groups.append(cur)
            cur = []
        cur.append(w)
        if w["text"][-1:] in ".!?,;:\u06d4\u061f\u060c":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def build(words, style, width, height, workdir, duration):
    """Write captions.ass (+ the font it needs) into workdir. Returns its path or None."""
    if style == "none" or not words:
        return None
    text_all = " ".join(w["text"] for w in words)
    script = script_of(text_all)
    family, font_path = find_font(script)
    fonts = Path(workdir) / "fonts"
    fonts.mkdir(exist_ok=True)
    if font_path:
        shutil.copy(font_path, fonts / Path(font_path).name)

    portrait = height > width
    size = int(min(width, height) * (0.085 if portrait else 0.075))
    if script == "arabic":
        size = int(size * 1.1)
    margin_v = int(height * (0.20 if portrait else 0.10))
    outline = max(3, size // 12)
    upper = script == "latin" and style == "pop"
    # ASS colours are &HAABBGGRR
    white, yellow, black = "&H00FFFFFF", "&H0000E6FF", "&H00000000"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{family},{size},{white},{white},{black},&H80000000,-1,0,0,0,100,100,0,0,1,{outline},{max(1, outline // 2)},2,{int(width * 0.08)},{int(width * 0.08)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    # Inline colour tags split a line into separately-shaped runs, which scrambles
    # right-to-left word order. RTL "pop" therefore pops whole 2-word phrases.
    rtl_pop = style == "pop" and script == "arabic"
    if rtl_pop:
        groups = _group(words, 2, 14)
    else:
        groups = _group(words, 3 if style == "pop" else 5, 16 if style == "pop" else 30)
    for gi, group in enumerate(groups):
        g_start = group[0]["start"]
        next_start = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else duration
        g_end = min(max(group[-1]["end"] + 0.25, g_start + 0.4), next_start, duration)
        texts = [_esc(w["text"].upper() if upper else w["text"]) for w in group]
        if style == "clean":
            lines.append(f"Dialogue: 0,{_ts(g_start)},{_ts(g_end)},Main,,0,0,0,,"
                         f"{{\\fad(80,60)}}{' '.join(texts)}")
            continue
        if rtl_pop:
            lines.append(f"Dialogue: 0,{_ts(g_start)},{_ts(g_end)},Main,,0,0,0,,"
                         f"{{\\c{yellow}\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}}"
                         + " ".join(texts))
            continue
        for wi, w in enumerate(group):
            w_start = g_start if wi == 0 else w["start"]
            w_end = group[wi + 1]["start"] if wi + 1 < len(group) else g_end
            if w_end <= w_start:
                continue
            parts = []
            for j, t in enumerate(texts):
                if j == wi:
                    parts.append(f"{{\\c{yellow}\\fscx112\\fscy112}}{t}{{\\c{white}\\fscx100\\fscy100}}")
                else:
                    parts.append(t)
            pop = "{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}" if wi == 0 else ""
            lines.append(f"Dialogue: 0,{_ts(w_start)},{_ts(w_end)},Main,,0,0,0,,{pop}"
                         + " ".join(parts))
    path = Path(workdir) / "captions.ass"
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8-sig")
    return path
