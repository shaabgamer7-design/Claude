"""Launch the desktop app at login (macOS LaunchAgent, Windows Run key, XDG autostart)."""

from __future__ import annotations

import plistlib
import shlex
import sys
from pathlib import Path

from freeflow.config import IS_MAC, IS_WINDOWS

LABEL = "com.freeflow.app"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def command() -> list[str]:
    """How to start the app: the installed executable, or this Python."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        if IS_MAC and exe.parent.name == "MacOS" and exe.parents[2].suffix == ".app":
            return ["/usr/bin/open", "-a", str(exe.parents[2])]
        return [str(exe)]
    return [sys.executable, "-m", "freeflow.gui"]


def _mac_plist() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _linux_desktop() -> Path:
    return Path.home() / ".config" / "autostart" / "freeflow.desktop"


def is_enabled() -> bool:
    if IS_MAC:
        return _mac_plist().exists()
    if IS_WINDOWS:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, "FreeFlow")
            return True
        except OSError:
            return False
    return _linux_desktop().exists()


def set_enabled(enabled: bool) -> None:
    cmd = command()
    if IS_MAC:
        path = _mac_plist()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(plistlib.dumps(
                {"Label": LABEL, "ProgramArguments": cmd, "RunAtLoad": True,
                 "ProcessType": "Interactive"}
            ))
        else:
            path.unlink(missing_ok=True)
    elif IS_WINDOWS:
        import subprocess
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, "FreeFlow", 0, winreg.REG_SZ, subprocess.list2cmdline(cmd))
            else:
                try:
                    winreg.DeleteValue(key, "FreeFlow")
                except OSError:
                    pass
    else:
        path = _linux_desktop()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "[Desktop Entry]\nType=Application\nName=FreeFlow\n"
                f"Exec={shlex.join(cmd)}\nX-GNOME-Autostart-enabled=true\n",
                encoding="utf-8",
            )
        else:
            path.unlink(missing_ok=True)
