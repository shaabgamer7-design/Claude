"""macOS privacy permissions the app needs. Other platforms need none."""

from __future__ import annotations

import ctypes
import logging
import subprocess

from freeflow.config import IS_MAC

log = logging.getLogger(__name__)

_PANES = {
    "accessibility": "Privacy_Accessibility",
    "input_monitoring": "Privacy_ListenEvent",
    "microphone": "Privacy_Microphone",
}


def _services():
    lib = ctypes.CDLL(
        "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
    )
    for fn in ("AXIsProcessTrusted", "CGPreflightListenEventAccess",
               "CGRequestListenEventAccess", "CGPreflightPostEventAccess",
               "CGRequestPostEventAccess"):
        getattr(lib, fn).restype = ctypes.c_bool
        getattr(lib, fn).argtypes = []
    return lib


def _call(fn: str) -> bool:
    if not IS_MAC:
        return True
    try:
        return bool(getattr(_services(), fn)())
    except (OSError, AttributeError) as e:
        log.debug("%s unavailable: %s", fn, e)
        return True  # older macOS without this check


def accessibility_granted() -> bool:
    """Needed to paste text (send Cmd+V) and read the focused window."""
    return _call("AXIsProcessTrusted")


def input_monitoring_granted() -> bool:
    """Needed to see the dictation hotkey from other apps."""
    return _call("CGPreflightListenEventAccess")


def request_accessibility() -> None:
    _call("CGRequestPostEventAccess")


def request_input_monitoring() -> None:
    _call("CGRequestListenEventAccess")


def open_settings(permission: str) -> None:
    if IS_MAC:
        url = f"x-apple.systempreferences:com.apple.preference.security?{_PANES[permission]}"
        subprocess.Popen(["open", url])


def missing() -> list[str]:
    out = []
    if not accessibility_granted():
        out.append("accessibility")
    if not input_monitoring_granted():
        out.append("input_monitoring")
    return out
