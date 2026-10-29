"""Which app is the user dictating into, and what writing style fits it."""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from dataclasses import dataclass

from freeflow.config import IS_MAC, IS_WINDOWS, StyleRule

log = logging.getLogger(__name__)


@dataclass
class AppContext:
    app: str = ""
    title: str = ""

    def haystack(self) -> str:
        return f"{self.app} {self.title}".lower()


# Checked in order; the first rule whose keyword appears in the app name or
# window title wins. Browser tabs are covered by the window title.
BUILTIN_RULES = [
    StyleRule(["terminal", "iterm", "warp", "ghostty", "alacritty", "kitty", "wezterm",
               "powershell", "cmd.exe", "windowsterminal", "konsole", "gnome-terminal"], "code"),
    StyleRule(["visual studio code", "code.exe", "cursor", "windsurf", "xcode", "pycharm",
               "intellij", "webstorm", "goland", "android studio", "sublime", "zed",
               "neovim", "nvim", "vim", "emacs", "github"], "code"),
    StyleRule(["mail", "outlook", "gmail", "superhuman", "spark", "thunderbird",
               "proton mail", "hey.com", "airmail"], "email"),
    StyleRule(["slack", "discord", "messages", "whatsapp", "telegram", "signal",
               "messenger", "teams", "imessage", "wechat", "line", "x.com", "twitter"], "casual"),
    StyleRule(["word", "pages", "google docs", "notion", "obsidian", "bear", "craft",
               "confluence", "linear", "jira", "quip", "dropbox paper"], "formal"),
]

STYLE_PROMPTS = {
    "default": "Write clean, natural prose that sounds like the speaker.",
    "casual": (
        "This is a chat message. Keep it conversational and brief, as the speaker "
        "would type it. Light punctuation; no greeting or sign-off unless spoken."
    ),
    "email": (
        "This is an email. Use complete sentences and proper paragraphs. If the "
        "speaker dictates a greeting or sign-off, put each on its own line."
    ),
    "formal": (
        "This is a document. Use polished, well-structured prose. Use headings or "
        "lists only when the speaker clearly enumerates items or sections."
    ),
    "code": (
        "The speaker is in a code editor or terminal, often writing prompts, commit "
        "messages, comments or commands. Preserve technical terms, identifiers, file "
        "names, flags and casing exactly (camelCase, snake_case, CLI flags). Format "
        "code identifiers as plain text, not Markdown, unless the speaker asks for it."
    ),
}


def _mentions(haystack: str, keyword: str) -> bool:
    # Whole-word match so "line" doesn't hit "Linear" and "word" doesn't hit "password".
    pattern = r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, haystack) is not None


def pick_style(ctx: AppContext, user_rules: list[StyleRule]) -> str:
    hay = ctx.haystack()
    for rule in [*user_rules, *BUILTIN_RULES]:
        if any(_mentions(hay, m) for m in rule.match if m):
            return rule.style
    return "default"


def style_prompt(style: str, overrides: dict[str, str]) -> str:
    return overrides.get(style) or STYLE_PROMPTS.get(style) or STYLE_PROMPTS["default"]


def active_app() -> AppContext:
    """Best-effort name and window title of the frontmost app."""
    try:
        if IS_MAC:
            return _mac()
        if IS_WINDOWS:
            return _windows()
        if sys.platform.startswith("linux"):
            return _linux()
    except Exception as e:
        log.debug("active app detection failed: %s", e)
    return AppContext()


def _mac() -> AppContext:
    try:
        from AppKit import NSWorkspace

        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        name = str(app.localizedName() or "")
        bundle = str(app.bundleIdentifier() or "")
    except ImportError:
        name = _run(["osascript", "-e",
                     'tell application "System Events" to get name of first '
                     'application process whose frontmost is true'])
        bundle = ""
    # Window titles need Screen Recording permission on recent macOS; the
    # Accessibility API gives us the focused window title without it.
    title = _mac_window_title()
    return AppContext(app=" ".join(filter(None, [name, bundle])), title=title)


def _mac_window_title() -> str:
    try:
        from ApplicationServices import (
            AXUIElementCopyAttributeValue,
            AXUIElementCreateSystemWide,
            kAXFocusedApplicationAttribute,
            kAXFocusedWindowAttribute,
            kAXTitleAttribute,
        )
    except ImportError:
        return ""
    system = AXUIElementCreateSystemWide()
    err, app = AXUIElementCopyAttributeValue(system, kAXFocusedApplicationAttribute, None)
    if err or app is None:
        return ""
    err, window = AXUIElementCopyAttributeValue(app, kAXFocusedWindowAttribute, None)
    if err or window is None:
        return ""
    err, title = AXUIElementCopyAttributeValue(window, kAXTitleAttribute, None)
    return "" if err or title is None else str(title)


def _windows() -> AppContext:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    handle = kernel32.OpenProcess(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
    if handle:
        try:
            size = wintypes.DWORD(1024)
            path = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                exe = path.value.rsplit("\\", 1)[-1]
        finally:
            kernel32.CloseHandle(handle)
    return AppContext(app=exe, title=title)


def _linux() -> AppContext:
    title = _run(["xdotool", "getactivewindow", "getwindowname"])
    app = _run(["xdotool", "getactivewindow", "getwindowclassname"])
    return AppContext(app=app, title=title)


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.0)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
