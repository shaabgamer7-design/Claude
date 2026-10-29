"""Runs the dictation app in the background and reports its state to the UI."""

from __future__ import annotations

import copy
import logging
import os
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from freeflow import apikeys, transcribe
from freeflow.app import App, Pipeline
from freeflow.audio import Recorder
from freeflow.cleanup import Polisher, create_backend
from freeflow.config import Config, app_dir
from freeflow.history import History
from freeflow.output import Output

log = logging.getLogger(__name__)


class Engine(QObject):
    """Owns the running App. Building it (loading the speech model) happens on a
    background thread; settings changes rebuild it, reusing the speech model when
    its settings are unchanged."""

    # (state, message). States: loading, ready, idle, recording, processing,
    # paused, error. Emitted from worker threads; Qt delivers them on the UI thread.
    status = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.app: App | None = None
        self.cfg: Config | None = None
        self.state, self.message = "stopped", ""
        self._stt = None
        self._stt_cfg = None
        self._detail = ""
        self._notice = ""
        self._threads: list[threading.Thread] = []
        self._generation = 0
        self._lock = threading.Lock()
        self._stt_lock = threading.Lock()

    def _emit(self, state: str, message: str) -> None:
        log.info("%-10s %s", state, message)
        self.state, self.message = state, message
        self.status.emit(state, message)

    def start(self, cfg: Config) -> None:
        with self._lock:
            self._generation += 1
            generation = self._generation
            old, self.app = self.app, None
            self.cfg = cfg
            self.state = "loading"
        if old is not None:
            old.stop()
        self._spawn(self._build, cfg, generation)

    def _spawn(self, target, *args) -> None:
        thread = threading.Thread(target=target, args=args, daemon=True, name="freeflow-engine")
        self._threads = [t for t in self._threads if t.is_alive()] + [thread]
        thread.start()

    def join(self, timeout: float = 5.0) -> None:
        """Wait for background work to finish (tests; and before dropping an Engine)."""
        for thread in list(self._threads):
            thread.join(timeout)

    def _build(self, cfg: Config, generation: int) -> None:
        apikeys.load_into_environ()
        try:
            with self._stt_lock:  # reuse the speech model if its settings are unchanged
                if self._stt is None or self._stt_cfg != cfg.transcription:
                    tcfg = copy.deepcopy(cfg.transcription)
                    # Load in the background: hotkeys work at once, and anything
                    # said during a first-run model download is kept until it's ready.
                    self._stt = transcribe.BackgroundTranscriber(lambda: transcribe.create(tcfg))
                    self._stt_cfg = tcfg
                    self._spawn(self._watch_model, self._stt, tcfg)
                stt = self._stt
            notice = ""
            try:
                backend = create_backend(cfg.cleanup)
            except Exception as e:
                backend, notice = None, f"AI editing is off: {e}"
            if (cfg.cleanup.provider == "claude" and not os.environ.get("ANTHROPIC_API_KEY")
                    and not os.environ.get("ANTHROPIC_AUTH_TOKEN")):
                notice = "Add your Anthropic API key in Settings to turn on AI editing"
            self._notice = notice
            history = History(app_dir() / "history.db") if cfg.history.enabled else None
            app = App(cfg, Pipeline(cfg, stt, Polisher(cfg, backend)),
                      Recorder(cfg.audio), Output(cfg.output), history, status=self._emit)
            with self._lock:
                if generation != self._generation:
                    return  # settings changed again while we were loading
                self.app = app
            app.start()
            # While the model is still loading, _watch_model reports progress and
            # announces when it's ready (including this notice).
            if notice and stt.ready:
                self._emit("ready", notice)
        except Exception as e:
            log.exception("engine failed to start")
            with self._lock:
                if generation == self._generation:
                    self.app = None
            self._emit("error", str(e))

    def _watch_model(self, stt, tcfg) -> None:
        """Report download progress until the speech model is ready."""
        waited = False
        while not stt.wait(1.0):
            if self._stt is not stt:
                return
            waited = True
            self._detail = _download_message(tcfg)
            if self.state not in ("recording", "processing"):
                self._emit("loading", self._detail)
        self._detail = ""
        if self._stt is not stt:
            return
        if stt.error is not None:
            self._stt = None  # try again on the next start
            self._emit("error", f"The speech model couldn't load: {stt.error}")
        elif waited:
            hint = self.app.how_to() if self.app else ""
            message = "Speech model ready." + (f" {hint[:1].upper()}{hint[1:]}." if hint else "")
            self._emit("ready", f"{message} {self._notice}".strip())

    def loading_detail(self) -> str:
        """What the speech model is doing, while it isn't ready yet."""
        stt = self._stt
        if stt is None or getattr(stt, "ready", True):
            return ""
        return self._detail or "Loading the speech model..."

    def stop(self) -> None:
        with self._lock:
            self._generation += 1
            old, self.app = self.app, None
        if old is not None:
            old.stop()
        self.state = "stopped"

    @property
    def paused(self) -> bool:
        return bool(self.app and self.app.paused)

    def set_paused(self, paused: bool) -> None:
        if self.app:
            self.app.paused = paused

    def paste_last(self) -> None:
        if self.app:
            self.app.paste_last()

    def level(self) -> float:
        return self.app.level() if self.app else 0.0

    def session(self):
        return self.app.session if self.app else None


def _download_message(tcfg) -> str:
    """'Downloading the speech model: 230 MB so far', from the download cache size."""
    if tcfg.provider != "local":
        return "Connecting to the speech service..."
    try:
        from faster_whisper.utils import _MODELS
        from huggingface_hub import constants
    except Exception:
        return "Loading the speech model..."
    name = tcfg.model or transcribe.LocalWhisper.DEFAULT_MODEL
    repo = _MODELS.get(name, name if "/" in name else "")
    folders = [Path(constants.HF_HUB_CACHE) / ("models--" + repo.replace("/", "--"))]
    folders.append(Path(constants.HF_HOME) / "xet")  # hf_xet stages chunks here
    total = 0
    for folder in folders:
        if folder.is_dir():
            total += sum(f.stat().st_size for f in folder.rglob("*")
                         if f.is_file() and not f.is_symlink())
    if total < 1_000_000:
        return "Loading the speech model..."
    return f"Downloading the speech model (first run only): {total / 1e6:.0f} MB so far"
