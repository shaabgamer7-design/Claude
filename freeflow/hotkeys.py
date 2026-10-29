"""Global hotkeys: push-to-talk, double-tap hands-free, and command mode.

`HotkeyStateMachine` holds all the timing logic and is independent of the
keyboard library so it can be tested; `HotkeyListener` feeds it from pynput.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from freeflow.config import IS_MAC, HotkeyConfig

log = logging.getLogger(__name__)

_ALIASES = {
    "control": "ctrl",
    "option": "alt",
    "opt": "alt",
    "command": "cmd",
    "win": "cmd",
    "super": "cmd",
    "meta": "cmd",
    "escape": "esc",
    "return": "enter",
    "globe": "fn",
}

# Names pynput may report for each modifier, including left/right variants.
_MODIFIER_FAMILIES = {
    "ctrl": {"ctrl", "ctrl_l", "ctrl_r"},
    "shift": {"shift", "shift_l", "shift_r"},
    "alt": {"alt", "alt_l", "alt_r", "alt_gr"},
    "cmd": {"cmd", "cmd_l", "cmd_r"},
    # pynput reports the left key as the bare name on some platforms.
    "ctrl_l": {"ctrl", "ctrl_l"},
    "shift_l": {"shift", "shift_l"},
    "alt_l": {"alt", "alt_l"},
    "cmd_l": {"cmd", "cmd_l"},
}


class Combo:
    """A set of keys that must all be held, e.g. ``ctrl_r+shift``."""

    def __init__(self, spec: str):
        self.spec = spec.strip().lower()
        self.parts: list[set[str]] = []
        for token in filter(None, (t.strip() for t in self.spec.split("+"))):
            token = _ALIASES.get(token, token)
            self.parts.append(_MODIFIER_FAMILIES.get(token, {token}))

    def __bool__(self) -> bool:
        return bool(self.parts)

    def names(self) -> set[str]:
        return set().union(*self.parts) if self.parts else set()

    def active(self, pressed: set[str]) -> bool:
        return bool(self.parts) and all(part & pressed for part in self.parts)

    def __repr__(self) -> str:
        return f"Combo({self.spec!r})"


Emit = Callable[..., None]
Schedule = Callable[[float, Callable[[], None]], Callable[[], None]]


def _thread_schedule(delay: float, fn: Callable[[], None]) -> Callable[[], None]:
    timer = threading.Timer(delay, fn)
    timer.daemon = True
    timer.start()
    return timer.cancel


class HotkeyStateMachine:
    """Turns "which hotkeys are held right now" into recording actions.

    Emits:
      start(command: bool) - begin recording
      command()            - a dictation became a command (command combo joined)
      hands_free()         - recording continues after the key is released
      stop()               - finish recording and process it
      cancel()             - discard the recording
    """

    IDLE = "idle"
    HOLDING = "holding"  # push-to-talk, key down
    TAP_PENDING = "tap_pending"  # short tap released; waiting for a second tap
    HANDS_FREE_ARMING = "hands_free_arming"  # second tap still held
    HANDS_FREE = "hands_free"
    WAIT_RELEASE = "wait_release"  # finished; ignore keys until released

    def __init__(
        self,
        emit: Emit,
        tap_max_seconds: float = 0.3,
        double_tap_window: float = 0.4,
        schedule: Schedule = _thread_schedule,
    ):
        self._emit = emit
        self._schedule = schedule
        self.tap_max = tap_max_seconds
        self.double_tap_window = double_tap_window
        self.state = self.IDLE
        self.command = False
        self._held = False
        self._pressed_at = 0.0
        self._cancel_timer: Callable[[], None] | None = None
        self._timer_token = 0
        self._lock = threading.RLock()

    @property
    def recording(self) -> bool:
        return self.state in (
            self.HOLDING, self.TAP_PENDING, self.HANDS_FREE_ARMING, self.HANDS_FREE
        )

    def update(self, now: float, dictate_active: bool, command_active: bool) -> None:
        with self._lock:
            held = dictate_active or command_active
            pressed, released = held and not self._held, self._held and not held
            self._held = held
            if command_active and self.state == self.HOLDING and not self.command:
                self.command = True
                self._emit("command")
            if pressed:
                self._on_press(now, command_active)
            elif released:
                self._on_release(now)

    def _on_press(self, now: float, command_active: bool) -> None:
        if self.state == self.IDLE:
            self.state = self.HOLDING
            self.command = command_active
            self._pressed_at = now
            self._emit("start", command=command_active)
        elif self.state == self.TAP_PENDING:
            self._clear_timer()
            self.state = self.HANDS_FREE_ARMING
            self._emit("hands_free")
        elif self.state == self.HANDS_FREE:
            self.state = self.WAIT_RELEASE
            self._emit("stop")

    def _on_release(self, now: float) -> None:
        if self.state == self.HOLDING:
            if self.command or now - self._pressed_at >= self.tap_max:
                self.state = self.IDLE
                self._emit("stop")
            else:
                self.state = self.TAP_PENDING
                self._timer_token += 1
                token = self._timer_token
                self._cancel_timer = self._schedule(
                    self.double_tap_window, lambda: self._tap_timeout(token)
                )
        elif self.state == self.HANDS_FREE_ARMING:
            self.state = self.HANDS_FREE
        elif self.state == self.WAIT_RELEASE:
            self.state = self.IDLE

    def _tap_timeout(self, token: int) -> None:
        with self._lock:
            if self.state == self.TAP_PENDING and token == self._timer_token:
                self._cancel_timer = None
                self.state = self.IDLE
                self._emit("cancel")

    def _clear_timer(self) -> None:
        self._timer_token += 1
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None

    def cancel(self) -> None:
        """Discard the current recording (Esc, or another key chorded in)."""
        with self._lock:
            if not self.recording:
                return
            self._clear_timer()
            self.state = self.WAIT_RELEASE if self._held else self.IDLE
            self._emit("cancel")

    def interrupt(self) -> None:
        """A non-hotkey key was pressed: the user meant a shortcut, not dictation."""
        with self._lock:
            if self.state in (self.HOLDING, self.TAP_PENDING):
                self.cancel()

    def finish(self) -> None:
        """Stop from outside the keyboard (e.g. the max recording length)."""
        with self._lock:
            if not self.recording:
                return
            self._clear_timer()
            self.state = self.WAIT_RELEASE if self._held else self.IDLE
            self._emit("stop")


def key_name(key, canonical=None) -> str | None:
    """Normalize a pynput key to the names used in config strings."""
    from pynput import keyboard

    if isinstance(key, keyboard.Key):
        return key.name
    if isinstance(key, keyboard.KeyCode):
        if canonical is not None:
            try:
                key = canonical(key)
            except Exception:  # canonical() can fail on exotic keys
                pass
        char = getattr(key, "char", None)
        if char and char.isprintable():
            return char.lower()
        if key.vk is not None:
            return f"vk{key.vk}"
    return None


class HotkeyListener:
    """Watches the global keyboard and drives a HotkeyStateMachine."""

    _MAC_FN_KEYCODE = 63

    def __init__(
        self,
        cfg: HotkeyConfig,
        machine: HotkeyStateMachine,
        on_paste_last: Callable[[], None] | None = None,
    ):
        self.machine = machine
        self.dictate = Combo(cfg.dictate)
        self.command = Combo(cfg.command)
        self.paste_last = Combo(cfg.paste_last)
        self.cancel = Combo(cfg.cancel)
        if not self.dictate:
            raise ValueError("hotkeys.dictate must not be empty")
        self.trigger_keys = self.dictate.names() | self.command.names()
        self.on_paste_last = on_paste_last
        self.pressed: set[str] = set()
        self._paste_latched = False
        self._fn_down = False
        self._lock = threading.Lock()
        self._listener = None

    # Key events -----------------------------------------------------------

    def held(self) -> set[str]:
        with self._lock:
            return set(self.pressed)

    def key_down(self, name: str) -> None:
        with self._lock:
            if name in self.pressed:
                return  # auto-repeat
            self.pressed.add(name)
            self._evaluate(name, is_press=True)

    def key_up(self, name: str) -> None:
        with self._lock:
            self.pressed.discard(name)
            self._evaluate(name, is_press=False)

    def _evaluate(self, name: str, is_press: bool) -> None:
        if is_press and self.cancel.active(self.pressed) and self.machine.recording:
            self.machine.cancel()
        if self.paste_last.active(self.pressed):
            if not self._paste_latched:
                self._paste_latched = True
                self.machine.interrupt()
                if self.on_paste_last:
                    self.on_paste_last()
        else:
            self._paste_latched = False
        if is_press and name not in self.trigger_keys:
            self.machine.interrupt()
        self.machine.update(
            time.monotonic(),
            self.dictate.active(self.pressed),
            self.command.active(self.pressed),
        )

    # pynput glue ----------------------------------------------------------

    def start(self) -> None:
        from pynput import keyboard

        kwargs = {}
        if IS_MAC and "fn" in self.trigger_keys | self.paste_last.names():
            kwargs["darwin_intercept"] = self._darwin_intercept

        def on_press(key, injected=False):
            if injected:
                return
            name = key_name(key, self._listener.canonical if self._listener else None)
            if name and not self._is_mac_fn_echo(name):
                self.key_down(name)

        def on_release(key, injected=False):
            if injected:
                return
            name = key_name(key, self._listener.canonical if self._listener else None)
            if name and not self._is_mac_fn_echo(name):
                self.key_up(name)

        self._listener = keyboard.Listener(
            on_press=on_press, on_release=on_release, **kwargs
        )
        self._listener.start()
        self._listener.wait()

    def _is_mac_fn_echo(self, name: str) -> bool:
        # pynput reports Fn as a release of an unknown key on every change;
        # the intercept below handles Fn instead.
        return IS_MAC and name == f"vk{self._MAC_FN_KEYCODE}"

    def _darwin_intercept(self, event_type, event):
        import Quartz

        if event_type == Quartz.kCGEventFlagsChanged:
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )
            if keycode == self._MAC_FN_KEYCODE:
                down = bool(
                    Quartz.CGEventGetFlags(event) & Quartz.kCGEventFlagMaskSecondaryFn
                )
                if down != self._fn_down:
                    self._fn_down = down
                    (self.key_down if down else self.key_up)("fn")
        return event

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()

    def join(self) -> None:
        if self._listener:
            self._listener.join()
