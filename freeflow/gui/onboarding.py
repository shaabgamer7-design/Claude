"""First-run setup wizard."""

from __future__ import annotations

import copy
import threading

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from freeflow import apikeys, permissions
from freeflow.config import IS_MAC, Config
from freeflow.gui import choices
from freeflow.gui.icons import app_icon, app_pixmap
from freeflow.gui.widgets import ChoiceCombo, SecretField, heading, hint

SETUPS = {
    "hybrid": ("Recommended: free speech recognition + Claude editing",
               "Your voice is transcribed on this computer for free. Claude polishes the "
               "text; you pay Anthropic per use with your own API key."),
    "private": ("Private and free: everything on this computer",
                "Nothing leaves your computer. AI editing uses Ollama if it's installed, "
                "otherwise basic cleanup."),
    "cloud": ("Fastest: cloud speech + Claude editing",
              "Best on older computers. Groq transcribes your voice in a blink; Claude "
              "polishes the text. Needs Groq and Anthropic API keys."),
}


def ollama_running(url: str = "http://localhost:11434") -> bool:
    try:
        import requests

        return requests.get(url + "/api/tags", timeout=0.5).status_code == 200
    except Exception:
        return False


def apply_setup(cfg: Config, setup: str, speech_model: str, has_ollama: bool,
                claude_model: str = "") -> Config:
    cfg = copy.deepcopy(cfg)
    if setup == "cloud":
        cfg.transcription.provider, cfg.transcription.model = "groq", ""
    else:
        cfg.transcription.provider, cfg.transcription.model = "local", speech_model
    if setup == "private":
        cfg.cleanup.provider = "ollama" if has_ollama else "none"
        cfg.cleanup.model = ""
    else:
        cfg.cleanup.provider = "claude"
        cfg.cleanup.model = claude_model
    return cfg


class _Signals(QObject):
    mic_result = Signal(str)


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        logo = QLabel()
        logo.setPixmap(app_pixmap(96))
        layout.addWidget(logo, alignment=Qt.AlignHCenter)
        layout.addWidget(heading("Welcome to FreeFlow"), alignment=Qt.AlignHCenter)
        body = QLabel(
            "Speak instead of type, in any app.<br><br>"
            "&bull; Hold a key, talk, let go: polished text appears at your cursor.<br>"
            "&bull; Filler words and false starts disappear; \"no wait, I mean...\" "
            "corrections are applied.<br>"
            "&bull; The tone fits the app: casual in chat, proper in email.<br>"
            "&bull; No word limits, no subscription.<br><br>"
            "Setup takes about a minute."
        )
        body.setWordWrap(True)
        layout.addWidget(body)
        layout.addStretch()


class SetupPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("How should FreeFlow work?")
        self.setSubTitle("You can change this any time in Settings.")
        layout = QVBoxLayout(self)
        self.group = QButtonGroup(self)
        for key, (title, desc) in SETUPS.items():
            radio = QRadioButton(title)
            radio.setProperty("setup", key)
            font = radio.font()
            font.setBold(True)
            radio.setFont(font)
            self.group.addButton(radio)
            layout.addWidget(radio)
            d = hint(desc)
            d.setContentsMargins(24, 0, 0, 8)
            layout.addWidget(d)
            if key == "hybrid":
                radio.setChecked(True)
        form = QFormLayout()
        self.model = ChoiceCombo(choices.SPEECH_MODELS["local"][:3])
        self.model.set_value("small")
        form.addRow("On-device speech model", self.model)
        layout.addLayout(form)
        layout.addWidget(hint("Small works well on most computers. Large is more accurate "
                              "on fast machines. The model downloads once (a few hundred MB)."))
        self.ollama_note = hint("")
        layout.addWidget(self.ollama_note)
        layout.addStretch()
        self.has_ollama = False
        self.group.buttonToggled.connect(self._update)

    def initializePage(self) -> None:
        self.has_ollama = ollama_running()
        self._update()

    def setup(self) -> str:
        button = self.group.checkedButton()
        return button.property("setup") if button else "hybrid"

    def _update(self, *_args) -> None:
        setup = self.setup()
        self.model.setEnabled(setup != "cloud")
        if setup == "private":
            self.ollama_note.setText(
                "Ollama found: it will do the AI editing." if self.has_ollama else
                'Ollama isn\'t running, so you\'ll get basic cleanup. For AI editing, install '
                '<a href="https://ollama.com">Ollama</a>, run "ollama pull llama3.2", then '
                "pick it in Settings > AI editing."
            )
        else:
            self.ollama_note.setText("")


class KeysPage(QWizardPage):
    def __init__(self, setup_page: SetupPage):
        super().__init__()
        self.setup_page = setup_page
        self.setTitle("Add your API keys")
        self.setSubTitle("Keys are stored in your system keychain and only sent to their "
                         "own service.")
        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.anthropic = SecretField("sk-ant-...")
        self.groq = SecretField("gsk_...")
        self.model = ChoiceCombo(choices.CLAUDE_MODELS)
        self.form.addRow("Claude model", self.model)
        self.form.addRow("", hint("Costs are rough estimates for a short dictation, paid to "
                                  "Anthropic. Haiku is plenty for everyday dictation."))
        self.form.addRow("Anthropic API key", self.anthropic)
        self.form.addRow("", hint(f'<a href="{choices.KEY_LINKS["ANTHROPIC_API_KEY"]}">'
                                  "Create an Anthropic key</a>"))
        self.form.addRow("Groq API key", self.groq)
        self._groq_link = hint(f'<a href="{choices.KEY_LINKS["GROQ_API_KEY"]}">'
                               "Create a free Groq key</a>")
        self.form.addRow("", self._groq_link)
        layout.addLayout(self.form)
        layout.addWidget(hint("No key yet? You can skip this and add it later in Settings; "
                              "until then FreeFlow uses basic cleanup."))
        layout.addStretch()

    def initializePage(self) -> None:
        cloud = self.setup_page.setup() == "cloud"
        self.form.setRowVisible(self.groq, cloud)
        self.form.setRowVisible(self._groq_link, cloud)
        self.anthropic.setText(apikeys.read("ANTHROPIC_API_KEY"))
        self.groq.setText(apikeys.read("GROQ_API_KEY"))

    def store(self) -> None:
        if self.anthropic.text():
            apikeys.store("ANTHROPIC_API_KEY", self.anthropic.text())
        if self.setup_page.setup() == "cloud" and self.groq.text():
            apikeys.store("GROQ_API_KEY", self.groq.text())


class PermissionsPage(QWizardPage):
    restart_requested = Signal()

    def __init__(self, device_getter):
        super().__init__()
        self.setTitle("Permissions")
        self.setSubTitle("FreeFlow needs to hear you and to type into other apps.")
        self._device = device_getter
        self._signals = _Signals()
        self._signals.mic_result.connect(self._mic_done)
        layout = QVBoxLayout(self)
        self.rows: dict[str, QLabel] = {}
        if IS_MAC:
            for key, title, desc in (
                ("input_monitoring", "Input Monitoring", "to notice when you hold the dictation key"),
                ("accessibility", "Accessibility", "to paste text where your cursor is"),
            ):
                layout.addLayout(self._row(key, title, desc))
            restart_row = QHBoxLayout()
            restart_row.addWidget(hint("After switching FreeFlow on in System Settings, "
                                       "restart it so macOS applies the change."), 1)
            restart = QPushButton("Restart FreeFlow")
            restart.clicked.connect(self.restart_requested.emit)
            restart_row.addWidget(restart)
            layout.addLayout(restart_row)
        mic_row = QHBoxLayout()
        self.mic_status = QLabel("Microphone: not tested yet")
        mic_btn = QPushButton("Test microphone")
        mic_btn.clicked.connect(self._test_mic)
        self.mic_btn = mic_btn
        mic_row.addWidget(self.mic_status, 1)
        mic_row.addWidget(mic_btn)
        layout.addLayout(mic_row)
        layout.addWidget(hint("Press Test and say a few words."))
        layout.addStretch()
        self._timer = QTimer(self, interval=1000, timeout=self._refresh)

    def _row(self, key: str, title: str, desc: str) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel()
        self.rows[key] = label
        button = QPushButton("Open Settings")

        def grant():
            (permissions.request_input_monitoring if key == "input_monitoring"
             else permissions.request_accessibility)()
            permissions.open_settings(key)

        button.clicked.connect(grant)
        label.setProperty("title", f"<b>{title}</b> - {desc}")
        row.addWidget(label, 1)
        row.addWidget(button)
        return row

    def initializePage(self) -> None:
        self._refresh()
        self._timer.start()

    def cleanupPage(self) -> None:
        self._timer.stop()

    def _refresh(self) -> None:
        granted = {
            "input_monitoring": permissions.input_monitoring_granted(),
            "accessibility": permissions.accessibility_granted(),
        }
        for key, label in self.rows.items():
            mark = "&#10003; allowed" if granted[key] else "needs permission"
            label.setText(f"{label.property('title')}: {mark}")

    def _test_mic(self) -> None:
        self.mic_btn.setEnabled(False)
        self.mic_status.setText("Microphone: listening for 2 seconds... say something")
        device = self._device()

        def work():
            try:
                import numpy as np
                import sounddevice as sd

                from freeflow.audio import _resolve_device

                data = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype="float32",
                              device=_resolve_device(device), blocking=True)
                rms = float(np.sqrt(np.mean(np.square(data))))
                if rms > 0.003:
                    msg = "Microphone: works, heard you"
                elif rms > 0:
                    msg = "Microphone: very quiet, check the input device in Settings"
                else:
                    msg = ("Microphone: silent. Allow FreeFlow in System Settings > "
                           "Privacy & Security > Microphone" if IS_MAC else
                           "Microphone: silent. Check Windows Settings > Privacy > Microphone")
            except Exception as e:
                msg = f"Microphone: couldn't open it ({e})"
            self._signals.mic_result.emit(msg)

        threading.Thread(target=work, daemon=True).start()

    def _mic_done(self, msg: str) -> None:
        self.mic_btn.setEnabled(True)
        self.mic_status.setText(msg)


class TryPage(QWizardPage):
    def __init__(self, wizard: "SetupWizard"):
        super().__init__()
        self._wizard = wizard
        self.setTitle("Try it")
        layout = QVBoxLayout(self)
        self.instructions = QLabel()
        self.instructions.setWordWrap(True)
        layout.addWidget(self.instructions)
        self.status = hint("Starting...")
        layout.addWidget(self.status)
        self.box = QPlainTextEdit()
        self.box.setPlaceholderText("Hold the mouse button here and say: \"Hi team, um, the "
                                    "meeting is at three, no wait, four o'clock.\"")
        layout.addWidget(self.box)

    def initializePage(self) -> None:
        cfg = self._wizard.result_config()
        key = choices.label_for(choices.DICTATE_KEYS, cfg.hotkeys.dictate)
        self.instructions.setText(
            "<b>Press and hold the left mouse button</b> in the box below, wait for the "
            "beep, speak, and let go. The text is written where you clicked.<br>"
            f"You can also hold <b>{key}</b> instead of the mouse button."
        )
        self._wizard.apply(cfg)

    def on_status(self, state: str, message: str) -> None:
        text = {"loading": message + " You can already try it; the text appears when it's done.",
                "ready": message if message.startswith("Speech model ready") else "Ready! Try it.",
                "error": f"Problem: {message}"}.get(state, message)
        if text:
            self.status.setText(text)


class SetupWizard(QWizard):
    finished_setup = Signal(object)  # Config
    apply_requested = Signal(object)  # Config: start the engine with it

    restart_requested = Signal()  # macOS: new permissions apply after a relaunch

    def __init__(self, cfg: Config, permissions_only: bool = False):
        super().__init__()
        self.setWindowTitle("Set up FreeFlow")
        self.setWindowIcon(app_icon())
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(640, 520)
        self.base = copy.deepcopy(cfg)
        self.permissions_only = permissions_only
        self.welcome = WelcomePage()
        self.setup_page = SetupPage()
        self.keys = KeysPage(self.setup_page)
        self.perms = PermissionsPage(lambda: self.base.audio.device)
        self.perms.restart_requested.connect(self.restart_requested.emit)
        self.try_page = TryPage(self)
        for page in (self.welcome, self.setup_page, self.keys, self.perms, self.try_page):
            self.addPage(page)
        if permissions_only:
            self.setStartId(self.pageIds()[3])
        self.setButtonText(QWizard.FinishButton, "Start using FreeFlow")
        self.currentIdChanged.connect(self._page_changed)
        self.accepted.connect(self._finish)

    def nextId(self) -> int:
        current = self.currentId()
        ids = self.pageIds()
        if self.page(current) is self.setup_page and self.setup_page.setup() == "private":
            return ids[ids.index(current) + 2]
        return super().nextId()

    def _page_changed(self, _id: int) -> None:
        if self.currentPage() is self.perms and not self.permissions_only:
            self.keys.store()

    def result_config(self) -> Config:
        if self.permissions_only:
            return copy.deepcopy(self.base)
        return apply_setup(self.base, self.setup_page.setup(), self.setup_page.model.value(),
                           self.setup_page.has_ollama, self.keys.model.value())

    def apply(self, cfg: Config) -> None:
        if not self.permissions_only:
            self.keys.store()
        self.apply_requested.emit(cfg)

    def _finish(self) -> None:
        cfg = self.result_config()
        cfg.ui.onboarded = True
        self.finished_setup.emit(cfg)

