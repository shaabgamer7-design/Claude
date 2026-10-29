"""Put text where the user's cursor is, and read the current selection."""

from __future__ import annotations

import logging
import sys
import threading
import time
import uuid

from freeflow.config import IS_MAC, OutputConfig

log = logging.getLogger(__name__)

_LINUX_TERMINALS = ("terminal", "konsole", "alacritty", "kitty", "wezterm", "xterm",
                    "tilix", "terminator", "ghostty", "foot")


class Output:
    def __init__(self, cfg: OutputConfig):
        self.cfg = cfg
        self._keyboard = None
        self._lock = threading.Lock()

    @property
    def keyboard(self):
        if self._keyboard is None:
            from pynput.keyboard import Controller

            self._keyboard = Controller()
        return self._keyboard

    def _chord(self, *keys) -> None:
        kb = self.keyboard
        for k in keys[:-1]:
            kb.press(k)
        kb.tap(keys[-1])
        for k in reversed(keys[:-1]):
            kb.release(k)

    def _paste_keys(self, app: str):
        from pynput.keyboard import Key

        if IS_MAC:
            return (Key.cmd, "v")
        if sys.platform.startswith("linux") and any(t in app.lower() for t in _LINUX_TERMINALS):
            return (Key.ctrl, Key.shift, "v")
        return (Key.ctrl, "v")

    def insert(self, text: str, app: str = "") -> None:
        """Insert text at the cursor using the configured method."""
        if not text:
            return
        import pyperclip

        with self._lock:
            if self.cfg.method == "type":
                self.keyboard.type(text)
                return
            if self.cfg.method == "clipboard":
                pyperclip.copy(text)
                return
            previous = _safe_paste()
            pyperclip.copy(text)
            time.sleep(0.05)  # let the clipboard owner settle before pasting
            self._chord(*self._paste_keys(app))
            if self.cfg.restore_clipboard and previous is not None:
                # Give the target app time to read the clipboard first.
                time.sleep(self.cfg.restore_delay_seconds)
                if _safe_paste() == text:
                    pyperclip.copy(previous)

    def copy_selection(self, timeout: float = 0.5) -> str:
        """Return the currently selected text ("" if nothing is selected).

        Sends the copy shortcut, then restores the user's clipboard.
        """
        import pyperclip
        from pynput.keyboard import Key

        with self._lock:
            previous = _safe_paste()
            sentinel = f"freeflow-{uuid.uuid4()}"
            pyperclip.copy(sentinel)
            self._chord(Key.cmd if IS_MAC else Key.ctrl, "c")
            selected = ""
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                time.sleep(0.03)
                current = _safe_paste()
                if current is not None and current != sentinel:
                    selected = current
                    break
            if previous is not None:
                pyperclip.copy(previous)
            return selected


def _safe_paste() -> str | None:
    import pyperclip

    try:
        return pyperclip.paste()
    except Exception as e:  # e.g. clipboard holds an image, or no clipboard tool
        log.debug("clipboard read failed: %s", e)
        return None
