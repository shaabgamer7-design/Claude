"""Hold the left mouse button in a text box to dictate; release to insert.

A short press stays an ordinary click, and dragging (selecting text, moving a
window) never starts or keeps a recording.
"""

from __future__ import annotations

import logging
import math
import threading
from typing import Callable

from freeflow.config import IS_WINDOWS, HotkeyConfig
from freeflow.hotkeys import HotkeyStateMachine, Schedule, _thread_schedule

log = logging.getLogger(__name__)

START_SLOP_PX = 8  # movement allowed before the recording starts
DRAG_CANCEL_PX = 40  # movement that cancels a recording in progress


class MouseTrigger:
    def __init__(
        self,
        machine: HotkeyStateMachine,
        hold_seconds: float = 0.4,
        text_only: bool = True,
        schedule: Schedule = _thread_schedule,
        pointer_over_text: Callable[[], bool] | None = None,
        caret_in_focus: Callable[[], bool] | None = None,
    ):
        self.machine = machine
        self.hold_seconds = hold_seconds
        self.text_only = text_only
        self._schedule = schedule
        self._pointer_over_text = pointer_over_text or _pointer_over_text
        self._caret_in_focus = caret_in_focus or _caret_in_focus
        self._down: tuple[float, float] | None = None
        self._pointer_was_text = False
        self._active = False
        self._token = 0
        self._cancel_timer: Callable[[], None] | None = None
        self._lock = threading.Lock()
        self._listener = None
        self.enabled = True

    # Events (called from the mouse hook; must stay fast) ------------------

    def press(self, x: float, y: float) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._down = (x, y)
            self._pointer_was_text = self._pointer_over_text() if self.text_only else True
            self._token += 1
            token = self._token
            self._cancel_timer = self._schedule(self.hold_seconds, lambda: self._held(token))

    def _held(self, token: int) -> None:
        with self._lock:
            if self._down is None or token != self._token:
                return
            self._cancel_timer = None
            # By now the press has focused whatever was clicked, so a text box
            # shows a caret even if it uses a custom pointer.
            if self.text_only and not (self._pointer_was_text or self._caret_in_focus()):
                return
            self._active = self.machine.begin()

    def move(self, x: float, y: float) -> None:
        down = self._down
        if down is None:
            return
        distance = math.hypot(x - down[0], y - down[1])
        with self._lock:
            if self._active and distance > DRAG_CANCEL_PX:
                self._active = False
                self._down = None
                self.machine.cancel()
            elif not self._active and distance > START_SLOP_PX:
                self._clear()

    def release(self) -> None:
        with self._lock:
            active = self._active
            self._clear()
            if active:
                self.machine.finish()

    def _clear(self) -> None:
        self._down = None
        self._active = False
        self._token += 1
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None

    # pynput glue ----------------------------------------------------------

    def start(self) -> None:
        from pynput import mouse

        def on_click(x, y, button, pressed, injected=False):
            if injected or button != mouse.Button.left:
                return
            (self.press(x, y) if pressed else self.release())

        def on_move(x, y, injected=False):
            if not injected:
                self.move(x, y)

        self._listener = mouse.Listener(on_click=on_click, on_move=on_move)
        self._listener.start()
        self._listener.wait()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()


def from_config(cfg: HotkeyConfig, machine: HotkeyStateMachine) -> MouseTrigger | None:
    if not cfg.mouse_hold:
        return None
    return MouseTrigger(machine, cfg.mouse_hold_seconds, cfg.mouse_text_only)


# "Is this a place you can type?" -------------------------------------------
# Windows only; elsewhere every press counts. Both checks are cheap Win32 calls.


def _pointer_over_text() -> bool:
    """The pointer is the system text cursor (I-beam), as over any text box."""
    if not IS_WINDOWS:
        return True
    try:
        import ctypes
        from ctypes import wintypes

        class CURSORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                        ("hCursor", ctypes.c_void_p), ("ptScreenPos", wintypes.POINT)]

        user32 = ctypes.WinDLL("user32")
        user32.GetCursorInfo.argtypes = [ctypes.POINTER(CURSORINFO)]
        user32.LoadCursorW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        user32.LoadCursorW.restype = ctypes.c_void_p
        info = CURSORINFO(cbSize=ctypes.sizeof(CURSORINFO))
        if not user32.GetCursorInfo(ctypes.byref(info)):
            return True
        ibeam = user32.LoadCursorW(None, ctypes.c_void_p(32513))  # IDC_IBEAM
        return info.hCursor == ibeam
    except Exception as e:
        log.debug("pointer check failed: %s", e)
        return True


def _caret_in_focus() -> bool:
    """The focused window has a text caret (Word, Notepad, most browsers)."""
    if not IS_WINDOWS:
        return True
    try:
        import ctypes
        from ctypes import wintypes

        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                        ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
                        ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                        ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
                        ("rcCaret", wintypes.RECT)]

        user32 = ctypes.WinDLL("user32")
        user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
        info = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
        if not user32.GetGUIThreadInfo(0, ctypes.byref(info)):  # 0 = foreground thread
            return False
        return bool(info.hwndCaret)
    except Exception as e:
        log.debug("caret check failed: %s", e)
        return False
