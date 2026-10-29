"""Render the app icon to packaging/build/icon.{png,ico,icns}."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from freeflow.gui.icons import app_pixmap  # noqa: E402

out = ROOT / "packaging" / "build"
out.mkdir(parents=True, exist_ok=True)
app = QGuiApplication([])
png = out / "icon.png"
app_pixmap(1024).save(str(png))
img = Image.open(png)
img.save(out / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save(out / "icon.icns")
print(f"wrote icons to {out}")
