"""Desktop app entry point: menu-bar/tray icon, recording bar, setup, settings."""

from __future__ import annotations

import argparse
import getpass
import logging
import logging.handlers
import os
import sys

from freeflow import config, permissions
from freeflow.config import IS_MAC, Config

log = logging.getLogger("freeflow")


def _fix_stdio() -> None:
    # Windowed builds have no console; libraries that print would crash.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


def _setup_logging(verbose: bool) -> None:
    folder = config.app_dir()
    folder.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.handlers.RotatingFileHandler(
        folder / "freeflow.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")]
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpx2", "httpcore", "anthropic", "urllib3", "faster_whisper"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class Controller:
    """Wires the engine to the tray icon, recording bar and windows."""

    def __init__(self, qapp, cfg: Config):
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu, QSystemTrayIcon

        from freeflow.gui.engine import Engine
        from freeflow.gui.icons import tray_icon
        from freeflow.gui.overlay import FlowBar

        self.qapp = qapp
        self.cfg = cfg
        self.engine = Engine()
        self.overlay = FlowBar(self.engine.level, self.engine.session, self.engine.loading_detail)
        self.overlay.enabled = cfg.ui.overlay
        self.settings = None
        self.wizard = None
        self._tray_icon = tray_icon

        self.tray = QSystemTrayIcon(tray_icon("loading"))
        self.tray.setToolTip("FreeFlow")
        menu = QMenu()
        self.status_action = QAction("Starting...", menu, enabled=False)
        self.key_action = QAction("", menu, enabled=False)
        self.pause_action = QAction("Pause dictation", menu, checkable=True)
        self.pause_action.toggled.connect(self.engine.set_paused)
        paste = QAction("Paste last result", menu)
        paste.triggered.connect(self.engine.paste_last)
        settings = QAction("Settings...", menu)
        settings.triggered.connect(lambda: self.show_settings())
        history = QAction("History...", menu)
        history.triggered.connect(lambda: self.show_settings("History"))
        quit_action = QAction("Quit FreeFlow", menu)
        quit_action.triggered.connect(self.quit)
        for item in (self.status_action, self.key_action, None, self.pause_action, paste, None,
                     settings, history, None, quit_action):
            menu.addSeparator() if item is None else menu.addAction(item)
        self.menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_clicked)
        self.tray.show()
        self._update_key_hint()

        self.engine.status.connect(self._on_status)
        self.engine.status.connect(self.overlay.on_status)

    # Startup --------------------------------------------------------------

    def start(self, open_settings: bool = False) -> None:
        if not self.cfg.ui.onboarded:
            self.show_wizard()
            return
        self.engine.start(self.cfg)
        if IS_MAC and permissions.missing():
            self.show_wizard(start_at_permissions=True)
        elif open_settings:
            self.show_settings()

    def _update_key_hint(self) -> None:
        from freeflow.gui import choices

        key = choices.label_for(choices.DICTATE_KEYS, self.cfg.hotkeys.dictate)
        if self.cfg.hotkeys.mouse_hold:
            self.key_action.setText(f"Hold the left mouse button in a text box, or {key}")
        else:
            self.key_action.setText(f"Hold {key} to dictate")

    # Status -----------------------------------------------------------------

    def _on_status(self, state: str, message: str) -> None:
        icon_state = state
        if state in ("idle", "ready"):
            icon_state = "paused" if self.engine.paused else "idle"
        if state == "recording" and (s := self.engine.session()) and s.mode == "command":
            icon_state = "command"
        self.tray.setIcon(self._tray_icon(icon_state))
        label = {"loading": "Starting", "ready": "Ready", "idle": "Ready",
                 "recording": "Listening", "processing": "Working", "paused": "Paused",
                 "error": "Problem"}.get(state, state.title())
        if state in ("loading", "error") or (state == "ready" and "key" in message):
            label += f": {message}"
        self.status_action.setText(label[:80])
        self.tray.setToolTip(f"FreeFlow - {label}"[:120])
        if state == "error" and message and not (self.wizard and self.wizard.isVisible()):
            self.tray.showMessage("FreeFlow", message[:200], self._tray_icon("error"), 5000)
        if state == "ready" and message.startswith("Speech model ready"):
            self.tray.showMessage("FreeFlow is ready", message[:200], self._tray_icon("idle"), 6000)
        if self.wizard is not None:
            self.wizard.try_page.on_status(state, message)

    def _tray_clicked(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon

        if not IS_MAC and reason == QSystemTrayIcon.Trigger:
            self.show_settings()

    # Windows --------------------------------------------------------------

    def _history(self):
        from freeflow.history import History

        return History(config.app_dir() / "history.db") if self.cfg.history.enabled else None

    def show_settings(self, page: str = "General") -> None:
        from freeflow.gui.settings import SettingsWindow

        if self.settings is None:
            self.settings = SettingsWindow(self.cfg, history_factory=self._history)
            self.settings.saved.connect(self.apply_config)
            self.settings.rerun_setup.connect(lambda: self.show_wizard())
        self.settings.show_page(page)

    def show_wizard(self, start_at_permissions: bool = False) -> None:
        from freeflow.gui.onboarding import SetupWizard
        from freeflow.gui.settings import bring_to_front

        if self.wizard is not None:
            self.wizard.deleteLater()  # delete the old one here, on the UI thread
        self.wizard = SetupWizard(self.cfg, permissions_only=start_at_permissions)
        self.wizard.apply_requested.connect(lambda cfg: self.engine.start(cfg))
        self.wizard.finished_setup.connect(self._wizard_done)
        self.wizard.restart_requested.connect(self.relaunch)
        self.wizard.rejected.connect(self._wizard_closed)
        bring_to_front(self.wizard)

    def _wizard_closed(self) -> None:
        # Closed before finishing: run with the current settings anyway (the
        # wizard shows again next launch until it's completed).
        if self.engine.app is None and self.engine.state in ("stopped", "error"):
            self.engine.start(self.cfg)

    def _wizard_done(self, cfg: Config) -> None:
        self.apply_config(cfg)
        self.tray.showMessage("FreeFlow is running", self.key_action.text(),
                              self._tray_icon("idle"), 4000)

    def relaunch(self) -> None:
        """Start a fresh copy once this one has exited (it holds the single-instance lock)."""
        import shlex

        from PySide6.QtCore import QProcess

        from freeflow import autostart

        if self.wizard is not None and self.wizard.isVisible():
            cfg = self.wizard.result_config()
            cfg.ui.onboarded = True
            config.save(cfg)
        if sys.platform.startswith("win"):
            QProcess.startDetached("cmd", ["/c", "timeout /t 2 >nul & start \"\" "
                                           + " ".join(f'"{c}"' for c in autostart.command())])
        else:
            QProcess.startDetached("/bin/sh", ["-c", f"sleep 1.5; {shlex.join(autostart.command())}"])
        self.quit()

    def apply_config(self, cfg: Config) -> None:
        config.save(cfg)
        self.cfg = cfg
        self.overlay.enabled = cfg.ui.overlay
        self._update_key_hint()
        if self.settings is not None:
            self.settings.cfg = cfg
        self.pause_action.setChecked(False)
        self.engine.start(cfg)

    def quit(self) -> None:
        self.engine.stop()
        self.tray.hide()
        self.qapp.quit()


def _collect_garbage_on_ui_thread(qapp) -> None:
    """Python's cycle collector runs on whichever thread happens to allocate,
    and PySide crashes deleting Qt objects it frees off the UI thread (seen with
    PySide6 6.12). Reference counting still frees almost everything at once;
    only reference cycles wait for this timer."""
    import gc

    from PySide6.QtCore import QTimer

    gc.disable()
    timer = QTimer(qapp, interval=15_000)
    timer.timeout.connect(gc.collect)
    timer.start()


def _single_instance(qapp, on_message):
    """Return False if FreeFlow is already running (and ask it to show itself)."""
    from PySide6.QtNetwork import QLocalServer, QLocalSocket

    name = f"freeflow-{getpass.getuser()}"
    sock = QLocalSocket()
    sock.connectToServer(name)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(300)
        return None
    QLocalServer.removeServer(name)
    server = QLocalServer(qapp)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), on_message()))
    server.listen(name)
    return server


def main(argv: list[str] | None = None) -> int:
    _fix_stdio()
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    parser = argparse.ArgumentParser(prog="FreeFlow")
    parser.add_argument("--selftest", metavar="REPORT", help="check the bundle and exit")
    parser.add_argument("--settings", action="store_true", help="open settings on start")
    parser.add_argument("-v", "--verbose", action="store_true")
    args, _qt_args = parser.parse_known_args(argv)

    if args.selftest:
        from freeflow.gui.selftest import run

        return run(args.selftest)

    _setup_logging(args.verbose)
    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

    from freeflow.gui.icons import app_icon

    qapp = QApplication(sys.argv[:1])
    qapp.setApplicationName("FreeFlow")
    qapp.setOrganizationName("FreeFlow")
    qapp.setWindowIcon(app_icon())
    qapp.setQuitOnLastWindowClosed(False)
    _collect_garbage_on_ui_thread(qapp)

    holder: dict = {}
    server = _single_instance(qapp, lambda: holder["c"].show_settings())
    if server is None:
        return 0
    if not QSystemTrayIcon.isSystemTrayAvailable():
        log.warning("no system tray; opening settings instead")

    try:
        cfg = config.load()
    except Exception as e:
        QMessageBox.warning(None, "FreeFlow", f"Your settings file has a problem:\n{e}\n\n"
                            "Starting with default settings.")
        cfg = Config()
    controller = Controller(qapp, cfg)
    holder["c"] = controller
    controller.start(open_settings=args.settings or not QSystemTrayIcon.isSystemTrayAvailable())
    log.info("FreeFlow started")
    return qapp.exec()


if __name__ == "__main__":
    raise SystemExit(main())
