"""The running dictation app: hotkeys -> recording -> transcription -> cleanup -> paste."""

from __future__ import annotations

import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from freeflow import audio
from freeflow.audio import Recorder, Recording
from freeflow.cleanup import CleanupError, Polisher
from freeflow.config import Config, app_dir
from freeflow.context import AppContext, active_app
from freeflow.history import History
from freeflow.hotkeys import HotkeyListener, HotkeyStateMachine
from freeflow.output import Output
from freeflow.transcribe import Transcriber, vocabulary_prompt

log = logging.getLogger(__name__)

_MODIFIERS = {
    "ctrl", "ctrl_l", "ctrl_r", "shift", "shift_l", "shift_r", "alt", "alt_l", "alt_r",
    "alt_gr", "cmd", "cmd_l", "cmd_r", "fn",
}

StatusFn = Callable[[str, str], None]


@dataclass
class Session:
    id: int
    mode: str  # "dictate" | "command"
    started: float
    context: AppContext = field(default_factory=AppContext)
    hands_free: bool = False


@dataclass
class Outcome:
    raw: str
    text: str
    style: str = ""
    stt_ms: int = 0
    llm_ms: int = 0
    note: str = ""


class Pipeline:
    """Recording -> finished text. Separate from the hotkey app so it can be
    driven from the CLI (`freeflow transcribe file.wav`) and from tests."""

    def __init__(self, cfg: Config, transcriber: Transcriber, polisher: Polisher):
        self.cfg = cfg
        self.transcriber = transcriber
        self.polisher = polisher
        self.prompt = vocabulary_prompt(cfg.dictionary)

    def check_audio(self, rec: Recording) -> str:
        """Why this recording should be skipped, or "" to process it."""
        if rec.duration < self.cfg.audio.min_seconds:
            return "too short"
        if rec.rms_db() < self.cfg.audio.silence_threshold_db:
            return "no speech detected (check your microphone)"
        return ""

    def transcribe(self, rec: Recording) -> tuple[str, int]:
        if self.cfg.audio.normalize:
            rec = rec.normalized()
        t0 = time.perf_counter()
        raw = self.transcriber.transcribe(rec, prompt=self.prompt)
        return raw, int((time.perf_counter() - t0) * 1000)

    def run(self, rec: Recording, mode: str, ctx: AppContext, selection: str = "") -> Outcome:
        raw, stt_ms = self.transcribe(rec)
        if not raw.strip():
            return Outcome(raw="", text="", stt_ms=stt_ms, note="no speech recognized")
        t0 = time.perf_counter()
        if mode == "command":
            result = self.polisher.command(raw, selection, ctx)
        else:
            result = self.polisher.dictation(raw, ctx)
        llm_ms = int((time.perf_counter() - t0) * 1000) if result.used_llm else 0
        text = result.text
        if (mode == "dictate" and text and self.cfg.output.trailing_space
                and not text.endswith((" ", "\n"))):
            text += " "
        return Outcome(raw, text, result.style, stt_ms, llm_ms, result.note)


def _console_status(state: str, message: str) -> None:
    log.info("%-10s %s", state, message)


class App:
    def __init__(
        self,
        cfg: Config,
        pipeline: Pipeline,
        recorder: Recorder,
        output: Output,
        history: History | None,
        status: StatusFn = _console_status,
    ):
        self.cfg = cfg
        self.pipeline = pipeline
        self.recorder = recorder
        self.output = output
        self.history = history
        self.status = status
        self.machine = HotkeyStateMachine(
            self._on_action, cfg.hotkeys.tap_max_seconds, cfg.hotkeys.double_tap_window
        )
        self.listener = HotkeyListener(cfg.hotkeys, self.machine, self._on_paste_last)
        self._actions: queue.Queue = queue.Queue()
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="freeflow-process")
        self._control = threading.Thread(target=self._control_loop, daemon=True,
                                         name="freeflow-control")
        self._session: Session | None = None
        self._session_ids = 0
        self._max_timer: threading.Timer | None = None
        self.last_text = ""

    # Lifecycle ------------------------------------------------------------

    def start(self) -> None:
        self.recorder.warm_up()
        self._control.start()
        self.listener.start()
        h = self.cfg.hotkeys
        self.status("ready", f"hold [{h.dictate}] to dictate, double-tap for hands-free, "
                             f"[{h.command}] for commands")

    def stop(self) -> None:
        self.listener.stop()
        self._actions.put((None, {}))
        self._worker.shutdown(wait=False, cancel_futures=True)
        self.recorder.close()

    # Hotkey actions (state machine -> control thread) ----------------------

    def _on_action(self, action: str, **kwargs) -> None:
        # Called from the keyboard hook; never block here.
        self._actions.put((action, kwargs))

    def _control_loop(self) -> None:
        while True:
            action, kwargs = self._actions.get()
            if action is None:
                return
            try:
                getattr(self, f"_do_{action}")(**kwargs)
            except Exception:
                log.exception("error handling %s", action)
                self._sound("error")

    def _sound(self, name: str) -> None:
        if self.cfg.audio.sounds:
            audio.play(name)

    def _do_start(self, command: bool) -> None:
        try:
            self.recorder.start()
        except Exception as e:
            self.machine.cancel()
            self.status("error", f"could not open microphone: {e}")
            self._sound("error")
            return
        self._sound("start")
        self._session_ids += 1
        session = Session(self._session_ids, "command" if command else "dictate", time.monotonic())
        self._session = session
        session.context = active_app()
        self._max_timer = threading.Timer(self.cfg.audio.max_seconds, self.machine.finish)
        self._max_timer.daemon = True
        self._max_timer.start()
        self.status("recording", f"{session.mode} -> {session.context.app or 'unknown app'}")

    def _do_command(self) -> None:
        if self._session:
            self._session.mode = "command"
            self.status("recording", "command mode")

    def _do_hands_free(self) -> None:
        if self._session:
            self._session.hands_free = True
            self.status("recording", "hands-free: press the hotkey again to finish, Esc to cancel")

    def _end_session(self) -> tuple[Session | None, Recording]:
        if self._max_timer:
            self._max_timer.cancel()
            self._max_timer = None
        session, self._session = self._session, None
        return session, self.recorder.stop()

    def _do_cancel(self) -> None:
        session, _ = self._end_session()
        if session:
            self._sound("cancel")
            self.status("idle", "cancelled")

    def _do_stop(self) -> None:
        session, rec = self._end_session()
        if session is None:
            return
        self._sound("stop")
        self._worker.submit(self._process, session, rec)

    # Processing (worker thread) --------------------------------------------

    def _wait_for_modifiers_released(self, timeout: float = 2.0) -> None:
        """Synthetic Cmd/Ctrl+V must not mix with keys the user still holds."""
        deadline = time.monotonic() + timeout
        while self.listener.held() & _MODIFIERS and time.monotonic() < deadline:
            time.sleep(0.02)

    def _process(self, session: Session, rec: Recording) -> None:
        if skip := self.pipeline.check_audio(rec):
            self.status("idle", skip)
            return
        self.status("processing", f"{rec.duration:.1f}s of audio")
        selection = ""
        try:
            if session.mode == "command":
                self._wait_for_modifiers_released()
                selection = self.output.copy_selection()
            outcome = self.pipeline.run(rec, session.mode, session.context, selection)
        except CleanupError as e:
            self.status("error", str(e))
            self._sound("error")
            return
        except Exception as e:
            saved = self._save_failed_audio(rec)
            self.status("error", f"{e} (audio saved to {saved}; retry with "
                                 f"`freeflow transcribe {saved}`)")
            self._sound("error")
            return
        if not outcome.text.strip():
            self.status("idle", outcome.note or "nothing to insert")
            return
        self._wait_for_modifiers_released()
        self.output.insert(outcome.text, app=session.context.app)
        self.last_text = outcome.text
        if self.history:
            self.history.add(session.mode, outcome.raw, outcome.text, app=session.context.app,
                             style=outcome.style, audio_seconds=rec.duration,
                             stt_ms=outcome.stt_ms, llm_ms=outcome.llm_ms)
        timing = f"stt {outcome.stt_ms} ms"
        if outcome.llm_ms:
            timing += f", cleanup {outcome.llm_ms} ms"
        note = f" ({outcome.note})" if outcome.note else ""
        self.status("idle", f"inserted {len(outcome.text.split())} words, {timing}{note}")

    def _save_failed_audio(self, rec: Recording) -> str:
        folder = app_dir() / "failed"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / time.strftime("%Y%m%d-%H%M%S.wav")
        path.write_bytes(rec.to_wav())
        return str(path)

    def _on_paste_last(self) -> None:
        self._worker.submit(self._paste_last)

    def _paste_last(self) -> None:
        text = self.last_text
        if not text and self.history and (entry := self.history.last()):
            text = entry.final_text
        if not text:
            self.status("idle", "nothing to paste yet")
            return
        self._wait_for_modifiers_released()
        self.output.insert(text, app=active_app().app)
        self.status("idle", "pasted last result")
