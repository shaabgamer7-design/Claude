"""`FreeFlow --selftest report.txt`: checks that a packaged build has everything.

CI runs this on the built .app / .exe, so a missing library shows up as a red
build instead of a crash on someone's computer. Each check has a time limit and
the report is written as it goes, so a hang names the check that hung.
"""

from __future__ import annotations

import os
import platform
import sys
import tempfile
import threading
import traceback


def run(report_path: str) -> int:
    os.environ["FREEFLOW_HOME"] = tempfile.mkdtemp(prefix="freeflow-selftest-")
    report = open(report_path, "w", encoding="utf-8")
    failed = 0
    total = 0

    def emit(line: str) -> None:
        report.write(line + "\n")
        report.flush()
        try:
            print(line, flush=True)
        except Exception:  # windowed build without a console
            pass

    def record(status: str, name: str, detail: str) -> None:
        nonlocal failed, total
        total += 1
        failed += status == "FAIL"
        emit(f"[{status}] {name}: {detail}")

    def check(name, fn, timeout: float = 60, required: bool = True, thread: bool = True):
        emit(f"... {name}")
        if not thread:  # Qt widgets must be created on the main thread
            def give_up():
                record("FAIL", name, f"timed out after {timeout:.0f}s")
                report.close()
                os._exit(1)

            watchdog = threading.Timer(timeout, give_up)
            watchdog.daemon = True
            watchdog.start()
            try:
                record("ok", name, str(fn() or ""))
            except BaseException as e:  # noqa: BLE001 - report everything
                record("FAIL", name, f"{e!r}\n{traceback.format_exc()}")
            watchdog.cancel()
            return
        result: dict = {}

        def target():
            try:
                result["detail"] = str(fn() or "")
            except BaseException as e:  # noqa: BLE001
                result["error"] = f"{e!r}\n{traceback.format_exc()}"

        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            record("FAIL" if required else "warn", name, f"timed out after {timeout:.0f}s")
        elif "error" in result:
            record("FAIL" if required else "warn", name, result["error"])
        else:
            record("ok", name, result["detail"])

    def numpy_check():
        import numpy

        return numpy.__version__

    def portaudio():
        import sounddevice

        return sounddevice.get_portaudio_version()[1]

    def keyboard():
        from pynput import keyboard as kb

        kb.Controller()
        return kb.Listener.__module__

    def clipboard():
        import pyperclip

        return pyperclip.__version__

    def claude():
        import anthropic

        anthropic.Anthropic(api_key="selftest")
        from freeflow.cleanup import ClaudeBackend
        from freeflow.config import CleanupConfig

        ClaudeBackend(CleanupConfig())
        return anthropic.__version__

    def tls():
        import certifi
        import requests

        return f"requests {requests.__version__}, {os.path.basename(certifi.where())}"

    def keychain_backend():
        import keyring

        backend = type(keyring.get_keyring())
        name = f"{backend.__module__}.{backend.__name__}"
        if sys.platform in ("darwin", "win32") and backend.__module__.endswith(".fail"):
            raise RuntimeError(f"no system keychain backend found ({name})")
        return name

    def keychain_read():
        from freeflow import apikeys

        return f"read ok ({'empty' if not apikeys.read('FREEFLOW_SELFTEST') else 'value'})"

    def whisper():
        import ctranslate2
        import faster_whisper
        import onnxruntime

        return (f"faster-whisper {faster_whisper.__version__}, ctranslate2 "
                f"{ctranslate2.__version__}, onnxruntime {onnxruntime.__version__}")

    def transcribe_tiny():
        import numpy as np

        from freeflow.audio import Recording
        from freeflow.config import TranscriptionConfig
        from freeflow.transcribe import LocalWhisper

        stt = LocalWhisper(TranscriptionConfig(model="tiny", device="cpu"))
        t = np.arange(16000 * 2) / 16000
        audio = Recording((0.05 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), 16000)
        return repr(stt.transcribe(audio))

    def settings_io():
        from freeflow import config

        path = config.save(config.Config())
        return f"round trip ok: {config.load(path) == config.Config()}"

    def qt():
        from PySide6.QtWidgets import QApplication

        from freeflow.config import Config
        from freeflow.gui.onboarding import SetupWizard
        from freeflow.gui.overlay import FlowBar
        from freeflow.gui.settings import SettingsWindow

        app = QApplication.instance() or QApplication([])
        windows = [SettingsWindow(Config()), SetupWizard(Config()),
                   FlowBar(lambda: 0.0, lambda: None)]
        sizes = [w.grab().size() for w in windows]
        return f"{app.platformName()}: " + ", ".join(f"{s.width()}x{s.height()}" for s in sizes)

    emit(f"FreeFlow selftest on {platform.platform()} (Python {sys.version.split()[0]})")
    check("numpy", numpy_check)
    check("audio (PortAudio)", portaudio)
    check("keyboard hooks (pynput)", keyboard)
    check("clipboard", clipboard)
    check("Claude client", claude)
    check("HTTPS", tls)
    check("keychain backend", keychain_backend)
    # A CI machine's keychain can be locked and wait for a password forever;
    # on a logged-in computer this returns immediately.
    check("keychain read", keychain_read, timeout=20, required=False)
    check("on-device speech libraries", whisper)
    if os.environ.get("FREEFLOW_SELFTEST_TRANSCRIBE"):
        check("on-device transcription (tiny model)", transcribe_tiny, timeout=300)
    check("settings file", settings_io)
    os.environ["FREEFLOW_NO_KEYCHAIN"] = "1"  # the windows below read API keys
    check("windows render", qt, thread=False)
    emit(f"{total - failed}/{total} passed")
    report.close()
    sys.stdout.flush()
    # A check that timed out may still be stuck in native code; don't wait for it.
    os._exit(1 if failed else 0)
