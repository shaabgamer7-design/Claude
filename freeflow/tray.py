"""Optional menu-bar / system-tray icon showing the current state."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Callable

from freeflow.config import config_path

log = logging.getLogger(__name__)

_COLORS = {
    "ready": (120, 120, 120),
    "idle": (120, 120, 120),
    "recording": (220, 50, 47),
    "processing": (240, 160, 30),
    "error": (150, 0, 150),
}


def available() -> bool:
    try:
        import PIL  # noqa: F401
        import pystray  # noqa: F401
    except ImportError:
        return False
    return True


def _image(color):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((22, 8, 42, 40), radius=10, fill=color)  # mic capsule
    draw.arc((14, 20, 50, 50), start=0, end=180, fill=color, width=4)
    draw.line((32, 50, 32, 58), fill=color, width=4)
    return img


def _open(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    elif sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", "start", "", path])
    else:
        subprocess.Popen(["xdg-open", path])


class Tray:
    def __init__(self, on_paste_last: Callable[[], None], on_quit: Callable[[], None]):
        import pystray

        self.state, self.message = "ready", ""
        self._on_quit = on_quit
        self.icon = pystray.Icon(
            "freeflow",
            _image(_COLORS["ready"]),
            "FreeFlow",
            menu=pystray.Menu(
                pystray.MenuItem(lambda _item: f"{self.state}: {self.message}"[:60], None,
                                 enabled=False),
                pystray.MenuItem("Paste last result", lambda: on_paste_last()),
                pystray.MenuItem("Open config", lambda: _open(str(config_path()))),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def update(self, state: str, message: str) -> None:
        self.state, self.message = state, message
        self.icon.icon = _image(_COLORS.get(state, _COLORS["idle"]))
        self.icon.title = f"FreeFlow - {state}"
        try:
            self.icon.update_menu()
        except Exception:  # not supported by every backend
            pass

    def _quit(self) -> None:
        self._on_quit()
        self.icon.stop()

    def run(self, setup: Callable[[], None]) -> None:
        """Blocks on the main thread (required on macOS)."""

        def _setup(icon):
            icon.visible = True
            setup()

        self.icon.run(setup=_setup)
