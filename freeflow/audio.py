"""Microphone capture, level checks, WAV encoding, and feedback sounds."""

from __future__ import annotations

import collections
import io
import logging
import threading
import wave
from dataclasses import dataclass

import numpy as np

from freeflow.config import AudioConfig

log = logging.getLogger(__name__)

PREROLL_SECONDS = 0.3


@dataclass
class Recording:
    samples: np.ndarray  # float32 mono in [-1, 1]
    sample_rate: int

    @property
    def duration(self) -> float:
        return len(self.samples) / self.sample_rate if self.sample_rate else 0.0

    def rms_db(self) -> float:
        if not len(self.samples):
            return -120.0
        rms = float(np.sqrt(np.mean(np.square(self.samples, dtype=np.float64))))
        return 20 * np.log10(max(rms, 1e-6))

    def normalized(self, target_peak: float = 0.9, max_gain: float = 20.0) -> "Recording":
        """Scale up quiet audio (whispering, distant mic) without clipping."""
        peak = float(np.max(np.abs(self.samples))) if len(self.samples) else 0.0
        if peak <= 0:
            return self
        gain = min(target_peak / peak, max_gain)
        if gain <= 1.0:
            return self
        return Recording((self.samples * gain).astype(np.float32), self.sample_rate)

    def to_wav(self) -> bytes:
        pcm = (np.clip(self.samples, -1, 1) * 32767).astype("<i2")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sample_rate)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()

    @classmethod
    def from_file(cls, path: str, sample_rate: int = 16000) -> "Recording":
        """Load any audio file (WAV natively; other formats via ffmpeg)."""
        try:
            with wave.open(path, "rb") as w:
                rate, width, channels = w.getframerate(), w.getsampwidth(), w.getnchannels()
                raw = w.readframes(w.getnframes())
            if width != 2:
                raise wave.Error("not 16-bit")
            data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            if channels > 1:
                data = data.reshape(-1, channels).mean(axis=1)
            if rate != sample_rate:
                data = _resample(data, rate, sample_rate)
            return cls(data.astype(np.float32), sample_rate)
        except (wave.Error, EOFError):
            return cls._from_ffmpeg(path, sample_rate)

    @classmethod
    def _from_ffmpeg(cls, path: str, sample_rate: int) -> "Recording":
        import subprocess

        out = subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path,
             "-f", "s16le", "-ac", "1", "-ar", str(sample_rate), "-"],
            check=True, capture_output=True,
        ).stdout
        data = np.frombuffer(out, dtype="<i2").astype(np.float32) / 32768.0
        return cls(data, sample_rate)


def _resample(data: np.ndarray, src: int, dst: int) -> np.ndarray:
    if not len(data):
        return data
    n = int(round(len(data) * dst / src))
    return np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data)


def _resolve_device(device: str):
    if not device:
        return None
    return int(device) if device.isdigit() else device


class Recorder:
    """Captures mono float32 audio between start() and stop()."""

    def __init__(self, cfg: AudioConfig):
        self.cfg = cfg
        self._frames: list[np.ndarray] = []
        self._preroll: collections.deque[np.ndarray] = collections.deque()
        self._preroll_len = 0
        self._recording = False
        self._stream = None
        self._lock = threading.Lock()
        self.level = 0.0  # RMS of the latest chunk while recording, for meters

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            log.debug("audio status: %s", status)
        chunk = indata[:, 0].copy()
        with self._lock:
            if self._recording:
                self._frames.append(chunk)
                self.level = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
            elif self.cfg.keep_mic_open:
                self._preroll.append(chunk)
                self._preroll_len += len(chunk)
                limit = int(PREROLL_SECONDS * self.cfg.sample_rate)
                while self._preroll and self._preroll_len - len(self._preroll[0]) >= limit:
                    self._preroll_len -= len(self._preroll.popleft())

    def _open(self) -> None:
        import sounddevice as sd

        self._stream = sd.InputStream(
            samplerate=self.cfg.sample_rate,
            channels=1,
            dtype="float32",
            device=_resolve_device(self.cfg.device),
            callback=self._callback,
        )
        self._stream.start()

    def warm_up(self) -> None:
        """Open the stream up front when keep_mic_open is set."""
        if self.cfg.keep_mic_open and self._stream is None:
            self._open()

    def start(self) -> None:
        with self._lock:
            self._frames = list(self._preroll)
            self._preroll.clear()
            self._preroll_len = 0
            self._recording = True
        if self._stream is None:
            self._open()

    def stop(self) -> Recording:
        with self._lock:
            self._recording = False
            self.level = 0.0
            frames, self._frames = self._frames, []
        if not self.cfg.keep_mic_open and self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        samples = np.concatenate(frames) if frames else np.zeros(0, dtype=np.float32)
        return Recording(samples.astype(np.float32), self.cfg.sample_rate)

    def close(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None


def list_devices() -> str:
    import sounddevice as sd

    return str(sd.query_devices())


def _tone(freqs: list[float], seconds: float = 0.06, rate: int = 44100) -> np.ndarray:
    parts = []
    for f in freqs:
        t = np.arange(int(rate * seconds)) / rate
        envelope = np.minimum(1, np.minimum(t, t[::-1]) / 0.01)
        parts.append(0.12 * np.sin(2 * np.pi * f * t) * envelope)
    return np.concatenate(parts).astype(np.float32)


_SOUNDS = {
    "start": [660, 880],
    "stop": [880, 660],
    "cancel": [440, 330],
    "error": [300, 200, 300],
}


def play(name: str) -> None:
    """Play a short cue without blocking. Failures are ignored."""
    try:
        import sounddevice as sd

        sd.play(_tone(_SOUNDS[name]), 44100, blocking=False)
    except Exception as e:  # no output device, etc.
        log.debug("sound %s failed: %s", name, e)
