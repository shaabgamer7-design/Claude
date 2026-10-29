"""Icons drawn in code, so the app ships no image assets."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap

ACCENT = QColor("#6C5CE7")
ACCENT_2 = QColor("#00B4D8")
RECORDING = QColor("#FF3B30")
PROCESSING = QColor("#FF9F0A")
COMMAND = QColor("#AF52DE")


def _mic(p: QPainter, rect: QRectF, color: QColor) -> None:
    """A microphone glyph filling `rect`."""
    w, h = rect.width(), rect.height()
    x, y = rect.x(), rect.y()
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    cap_w, cap_h = w * 0.36, h * 0.56
    p.drawRoundedRect(QRectF(x + (w - cap_w) / 2, y + h * 0.06, cap_w, cap_h), cap_w / 2, cap_w / 2)
    pen = QPen(color, max(1.5, w * 0.08), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    arc = QRectF(x + w * 0.2, y + h * 0.22, w * 0.6, h * 0.52)
    p.drawArc(arc, 200 * 16, 140 * 16)
    p.drawLine(QPointF(x + w / 2, y + h * 0.75), QPointF(x + w / 2, y + h * 0.9))


def tray_icon(state: str = "idle") -> QIcon:
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    color = {
        "recording": RECORDING,
        "processing": PROCESSING,
        "command": COMMAND,
        "error": QColor("#8E8E93"),
    }.get(state, QColor("black"))
    _mic(p, QRectF(8, 4, 48, 56), color)
    if state == "paused":
        p.setPen(QPen(QColor("black"), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(10, 54), QPointF(54, 10))
    p.end()
    icon = QIcon(pm)
    # A mask icon adapts to the light/dark macOS menu bar.
    icon.setIsMask(state in ("idle", "ready", "loading", "paused"))
    return icon


def app_pixmap(size: int = 512) -> QPixmap:
    """The app icon: a gradient rounded square with a white microphone."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    margin = size * 0.08
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0, ACCENT)
    grad.setColorAt(1, ACCENT_2)
    path = QPainterPath()
    path.addRoundedRect(rect, size * 0.2, size * 0.2)
    p.fillPath(path, grad)
    inner = size * 0.24
    _mic(p, QRectF(inner, inner * 0.95, size - 2 * inner, size - 2 * inner), QColor("white"))
    p.end()
    return pm


def app_icon() -> QIcon:
    icon = QIcon()
    for s in (16, 32, 64, 128, 256, 512):
        icon.addPixmap(app_pixmap(s))
    return icon
