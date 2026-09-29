"""FFmpeg helpers. Uses a system ffmpeg when it can burn subtitles, else the
binary bundled with the imageio-ffmpeg package (no separate install needed)."""
import functools
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _filters(exe: str) -> str:
    try:
        out = subprocess.run([exe, "-hide_banner", "-filters"], capture_output=True,
                             text=True, timeout=20, creationflags=_NO_WINDOW)
        return out.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


@functools.lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    candidates = []
    system = shutil.which("ffmpeg")
    if system:
        candidates.append(system)
    try:
        import imageio_ffmpeg
        candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    if not candidates:
        raise RuntimeError("FFmpeg not found. Run the setup script again.")
    for exe in candidates:
        if " subtitles " in _filters(exe):
            return exe
    return candidates[0]


@functools.lru_cache(maxsize=1)
def can_burn_subtitles() -> bool:
    return " subtitles " in _filters(ffmpeg_exe())


def run(args, cwd=None, stdin=None):
    """Run ffmpeg with the given arguments; raise with its log on failure."""
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    proc = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True,
                          creationflags=_NO_WINDOW)
    if proc.returncode != 0:
        log = proc.stderr.decode("utf-8", "replace")[-2000:]
        raise RuntimeError(f"FFmpeg failed: {log}")
    return proc


def probe_duration(path) -> float:
    cmd = [ffmpeg_exe(), "-hide_banner", "-i", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          creationflags=_NO_WINDOW)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        return 0.0
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def has_video_stream(path) -> bool:
    cmd = [ffmpeg_exe(), "-hide_banner", "-i", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          creationflags=_NO_WINDOW)
    return bool(re.search(r"Stream #.*Video:", proc.stderr))


# Voice "mastering" chain: remove rumble and hiss, even out the level and hit
# the -14 LUFS loudness that Instagram, TikTok and YouTube normalise to.
STUDIO_VOICE = ("highpass=f=75,lowpass=f=15000,"
                "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
                "loudnorm=I=-14:TP=-1.5:LRA=9")


def prepare_voice(src, dst, max_seconds: float, studio: bool = True, denoise: bool = False,
                  trim_start: bool = True):
    """Convert any audio/video file to a 48 kHz mono WAV, trimmed and polished."""
    chain = []
    if trim_start:
        chain.append("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08")
    if denoise:
        chain.append("afftdn=nf=-28")
    if studio:
        chain.append(STUDIO_VOICE)
    # Short tail so the last word is not clipped, then a hard cap on length.
    chain.append("apad=pad_dur=0.35")
    run(["-i", src, "-vn", "-ac", "1", "-ar", 48000, "-af", ",".join(chain),
         "-t", f"{max_seconds:.2f}", "-c:a", "pcm_s16le", dst])


def load_audio_16k(path) -> np.ndarray:
    """Decode audio to a float32 mono 16 kHz array (what Wav2Lip expects)."""
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path),
           "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
    proc = subprocess.run(cmd, capture_output=True, creationflags=_NO_WINDOW)
    if proc.returncode != 0:
        raise RuntimeError("Could not decode audio: "
                           + proc.stderr.decode("utf-8", "replace")[-500:])
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def normalise_video(src, dst, fps: int, short_side: int, max_seconds: float):
    """Constant frame rate, short side <= short_side, no audio, near-lossless."""
    scale = (f"scale=w='if(gte(iw,ih),-2,min({short_side},iw))'"
             f":h='if(gte(iw,ih),min({short_side},ih),-2)':flags=lanczos")
    run(["-i", src, "-t", f"{max_seconds:.2f}", "-an",
         "-vf", f"fps={fps},{scale},format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", 12, dst])


def video_size(path):
    cmd = [ffmpeg_exe(), "-hide_banner", "-i", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          creationflags=_NO_WINDOW)
    m = re.search(r"Stream #.*Video:.*?\b(\d{2,5})x(\d{2,5})\b", proc.stderr)
    if not m:
        raise RuntimeError(f"Could not read video size of {Path(path).name}")
    return int(m.group(1)), int(m.group(2))


def read_frames(path):
    """Decode every frame as BGR uint8 arrays (via ffmpeg: safe with any path)."""
    w, h = video_size(path)
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path),
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    proc = subprocess.run(cmd, capture_output=True, creationflags=_NO_WINDOW)
    if proc.returncode != 0:
        raise RuntimeError("Could not decode video: "
                           + proc.stderr.decode("utf-8", "replace")[-500:])
    size = w * h * 3
    n = len(proc.stdout) // size
    # Read-only views into one buffer (no second copy); callers copy before editing.
    return list(np.frombuffer(proc.stdout, np.uint8)[: n * size].reshape(n, h, w, 3))


def imread(path):
    import cv2
    img = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read the image. Use a JPG, PNG or WEBP file.")
    return img


def imwrite(path, img, quality=90):
    import cv2
    ext = Path(path).suffix or ".jpg"
    ok, buf = cv2.imencode(ext, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError(f"Could not encode {path}")
    buf.tofile(str(path))


def write_frames(frames, dst, fps: int, crf: int = 12):
    h, w = frames[0].shape[:2]
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", str(dst)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=_NO_WINDOW)
    try:
        for f in frames:
            proc.stdin.write(np.ascontiguousarray(f).tobytes())
    finally:
        proc.stdin.close()
        err = proc.stderr.read()
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("FFmpeg failed: " + err.decode("utf-8", "replace")[-1000:])


class VideoWriter:
    """Streams BGR frames into ffmpeg and muxes the final audio + captions."""

    def __init__(self, dst, size, fps, audio, workdir, subtitles=None, finish=True):
        w, h = size
        vf = []
        if subtitles:
            # Relative names keep the filter graph free of Windows drive-letter escaping.
            vf.append(f"subtitles={Path(subtitles).name}:fontsdir=fonts")
        if finish:
            # Gentle sharpening plus fine temporal grain: unifies the restored mouth
            # texture with the rest of the frame and hides compression banding.
            vf.append("unsharp=5:5:0.45:5:5:0.0")
            vf.append("noise=alls=3:allf=t")
        vf.append("format=yuv420p")
        cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps),
               "-i", "-", "-i", str(audio),
               "-vf", ",".join(vf),
               "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
               "-shortest", "-movflags", "+faststart", str(dst)]
        self.proc = subprocess.Popen(cmd, cwd=str(workdir), stdin=subprocess.PIPE,
                                     stderr=subprocess.PIPE, creationflags=_NO_WINDOW)

    def write(self, frame):
        self.proc.stdin.write(np.ascontiguousarray(frame).tobytes())

    def close(self):
        self.proc.stdin.close()
        err = self.proc.stderr.read()
        self.proc.wait()
        if self.proc.returncode != 0:
            raise RuntimeError("FFmpeg failed: " + err.decode("utf-8", "replace")[-1500:])
