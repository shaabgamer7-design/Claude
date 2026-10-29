"""Runs the dictation app in the background and reports its state to the UI."""

from __future__ import annotations

import copy
import logging
import os
import threading

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
        threading.Thread(target=self._build, args=(cfg, generation), daemon=True,
                         name="freeflow-engine").start()

    def _build(self, cfg: Config, generation: int) -> None:
        apikeys.load_into_environ()
        try:
            with self._stt_lock:  # one model load at a time; reuse it if unchanged
                if self._stt is None or self._stt_cfg != cfg.transcription:
                    self._stt = None
                    if cfg.transcription.provider in ("local", "mlx"):
                        self._emit("loading", "Loading speech model (the first run downloads it)...")
                    else:
                        self._emit("loading", "Connecting...")
                    self._stt = transcribe.create(cfg.transcription)
                    self._stt_cfg = copy.deepcopy(cfg.transcription)
                stt = self._stt
            notice = ""
            try:
                backend = create_backend(cfg.cleanup)
            except Exception as e:
                backend, notice = None, f"AI editing is off: {e}"
            if (cfg.cleanup.provider == "claude" and not os.environ.get("ANTHROPIC_API_KEY")
                    and not os.environ.get("ANTHROPIC_AUTH_TOKEN")):
                notice = "Add your Anthropic API key in Settings to turn on AI editing"
            history = History(app_dir() / "history.db") if cfg.history.enabled else None
            app = App(cfg, Pipeline(cfg, stt, Polisher(cfg, backend)),
                      Recorder(cfg.audio), Output(cfg.output), history, status=self._emit)
            with self._lock:
                if generation != self._generation:
                    return  # settings changed again while we were loading
                self.app = app
            app.start()
            if notice:
                self._emit("ready", notice)
        except Exception as e:
            log.exception("engine failed to start")
            with self._lock:
                if generation == self._generation:
                    self.app = None
            self._emit("error", str(e))

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
