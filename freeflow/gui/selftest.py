"""`FreeFlow --selftest report.txt`: checks that a packaged build has everything.

CI runs this on the built .app / .exe, so a missing library shows up as a red
build instead of a crash on someone's computer.
"""

from __future__ import annotations

import os
import platform
import sys
import tempfile
import traceback


def run(report_path: str) -> int:
    os.environ["FREEFLOW_HOME"] = tempfile.mkdtemp(prefix="freeflow-selftest-")
    results: list[tuple[str, str, str]] = []

    def check(name, fn):
        try:
            detail = fn()
            results.append(("ok", name, str(detail or "")))
        except BaseException as e:  # noqa: BLE001 - report everything, including SystemExit
            results.append(("FAIL", name, f"{e!r}\n{traceback.format_exc()}"))

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

    def keychain():
        import keyring

        backend = type(keyring.get_keyring())
        name = f"{backend.__module__}.{backend.__name__}"
        if sys.platform in ("darwin", "win32") and backend.__module__.endswith(".fail"):
            raise RuntimeError(f"no system keychain backend found ({name})")
        return name

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

    check("numpy", numpy_check)
    check("audio (PortAudio)", portaudio)
    check("keyboard hooks (pynput)", keyboard)
    check("clipboard", clipboard)
    check("Claude client", claude)
    check("HTTPS", tls)
    check("keychain", keychain)
    check("on-device speech libraries", whisper)
    if os.environ.get("FREEFLOW_SELFTEST_TRANSCRIBE"):
        check("on-device transcription (tiny model)", transcribe_tiny)
    check("settings file", settings_io)
    check("windows render", qt)

    failed = [r for r in results if r[0] != "ok"]
    lines = [f"FreeFlow selftest on {platform.platform()} (Python {sys.version.split()[0]})"]
    lines += [f"[{status}] {name}: {detail}" for status, name, detail in results]
    lines.append(f"{len(results) - len(failed)}/{len(results)} passed")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return 1 if failed else 0
