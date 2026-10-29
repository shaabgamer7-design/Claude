"""The floating recording bar: a small pill near the bottom of the screen.

It must never take keyboard focus, or the dictated text would be pasted into
the bar instead of the user's app.
"""

from __future__ import annotations

import collections
import logging
import math
import time

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from freeflow.config import IS_MAC
from freeflow.gui.icons import COMMAND, PROCESSING, RECORDING

log = logging.getLogger(__name__)

BARS = 14
HEIGHT = 38


class FlowBar(QWidget):
    def __init__(self, level_source, session_source):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.NoFocus)
        self._level = level_source
        self._session = session_source
        self.mode = "hidden"  # hidden | recording | processing | message
        self.text = ""
        self.enabled = True
        self._levels = collections.deque([0.0] * BARS, maxlen=BARS)
        self._t0 = time.monotonic()
        self._font = QFont()
        self._font.setPointSizeF(11.5)
        self._font.setWeight(QFont.DemiBold)
        self._tick = QTimer(self, interval=33, timeout=self._animate)
        self._hide_timer = QTimer(self, singleShot=True, timeout=self._hide)
        self._mac_configured = False

    # State ----------------------------------------------------------------

    def on_status(self, state: str, message: str) -> None:
        if not self.enabled:
            return
        if state == "recording":
            self._show("recording")
        elif state == "processing":
            self._show("processing")
        elif state == "error":
            self._show("message", message or "Something went wrong")
        elif state == "idle" and self.mode in ("recording", "processing"):
            if message.startswith("inserted") or message in ("cancelled", "too short"):
                self._hide()
            elif message:
                self._show("message", _short(message))
            else:
                self._hide()

    def _show(self, mode: str, text: str = "") -> None:
        self.mode, self.text = mode, text
        self._hide_timer.stop()
        if mode == "recording":
            self._levels.extend([0.0] * BARS)
        if mode == "message":
            self._hide_timer.start(2600)
        self._place()
        if not self.isVisible():
            self.show()
            self._configure_mac_window()
        self._tick.start()
        self.update()

    def _hide(self) -> None:
        self.mode = "hidden"
        self._tick.stop()
        self.hide()

    # Geometry ---------------------------------------------------------------

    def _width(self) -> int:
        if self.mode == "message":
            return min(520, QFontMetrics(self._font).horizontalAdvance(self.text) + 40)
        session = self._session()
        label = self._label(session)
        extra = QFontMetrics(self._font).horizontalAdvance(label) + 12 if label else 0
        return 150 + extra if self.mode == "recording" else 92

    def _label(self, session) -> str:
        if self.mode != "recording" or session is None:
            return ""
        if session.mode == "command":
            return "Command"
        return "Hands-free" if session.hands_free else ""

    def _place(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        w = self._width()
        self.setGeometry(area.center().x() - w // 2, area.bottom() - HEIGHT - 28, w, HEIGHT)

    def _configure_mac_window(self) -> None:
        """Float over full-screen apps and every Space, and never become key."""
        if not IS_MAC or self._mac_configured:
            return
        self._mac_configured = True
        try:
            import AppKit
            import objc

            view = objc.objc_object(c_void_p=int(self.winId()))
            window = view.window()
            window.setCollectionBehavior_(
                AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                | AppKit.NSWindowCollectionBehaviorStationary
            )
            window.setLevel_(AppKit.NSStatusWindowLevel)
            window.setIgnoresMouseEvents_(True)
            window.setHidesOnDeactivate_(False)
        except Exception as e:
            log.debug("could not configure overlay window: %s", e)

    # Painting ---------------------------------------------------------------

    def _animate(self) -> None:
        if self.mode == "recording":
            level = self._level()
            # Speech RMS is roughly 0.01-0.2; map it onto 0..1 perceptually.
            self._levels.append(min(1.0, math.sqrt(level * 12)))
            if self.width() != self._width():
                self._place()
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        p.fillPath(path, QColor(18, 18, 22, 235))
        p.setPen(QColor(255, 255, 255, 40))
        p.drawPath(path)
        p.setFont(self._font)
        if self.mode == "recording":
            self._paint_recording(p, rect)
        elif self.mode == "processing":
            self._paint_processing(p, rect)
        elif self.mode == "message":
            p.setPen(QColor("white"))
            p.drawText(rect, Qt.AlignCenter, self.text)
        p.end()

    def _paint_recording(self, p: QPainter, rect: QRectF) -> None:
        session = self._session()
        command = session is not None and session.mode == "command"
        dot = COMMAND if command else RECORDING
        pulse = 0.75 + 0.25 * math.sin((time.monotonic() - self._t0) * 6)
        p.setPen(Qt.NoPen)
        c = QColor(dot)
        c.setAlphaF(pulse)
        p.setBrush(c)
        cy = rect.center().y()
        p.drawEllipse(QRectF(rect.left() + 14, cy - 5, 10, 10))
        x = rect.left() + 34
        bar_w, gap = 4.0, 3.5
        p.setBrush(QColor(255, 255, 255, 230))
        for v in self._levels:
            h = 4 + v * (rect.height() - 16)
            p.drawRoundedRect(QRectF(x, cy - h / 2, bar_w, h), 2, 2)
            x += bar_w + gap
        label = self._label(session)
        if label:
            p.setPen(QColor(COMMAND if command else "white"))
            p.drawText(QRectF(x + 6, rect.top(), rect.right() - x - 14, rect.height()),
                       Qt.AlignVCenter | Qt.AlignLeft, label)

    def _paint_processing(self, p: QPainter, rect: QRectF) -> None:
        t = time.monotonic() - self._t0
        p.setPen(Qt.NoPen)
        cy = rect.center().y()
        for i in range(3):
            phase = (math.sin(t * 7 - i * 0.9) + 1) / 2
            c = QColor(PROCESSING)
            c.setAlphaF(0.35 + 0.65 * phase)
            p.setBrush(c)
            r = 3.5 + 1.5 * phase
            p.drawEllipse(QRectF(rect.center().x() - 18 + i * 18 - r, cy - r, 2 * r, 2 * r))


def _short(message: str) -> str:
    return message if len(message) <= 60 else message[:57] + "..."
