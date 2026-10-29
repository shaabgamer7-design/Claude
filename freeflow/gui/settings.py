"""The settings window."""

from __future__ import annotations

import copy
import logging
import os
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from freeflow import __version__, apikeys, autostart, config
from freeflow.config import IS_MAC, Config, StyleRule
from freeflow.context import STYLE_PROMPTS, AppContext
from freeflow.gui import choices
from freeflow.gui.icons import app_icon
from freeflow.gui.widgets import ChoiceCombo, PairTable, SecretField, heading, hint

log = logging.getLogger(__name__)


def input_devices() -> list[tuple[str, str]]:
    out = [("", "System default")]
    try:
        import sounddevice as sd

        seen = set()
        for dev in sd.query_devices():
            name = str(dev["name"])
            if dev["max_input_channels"] > 0 and name not in seen:
                seen.add(name)
                out.append((name, name))
    except Exception as e:  # PortAudio missing, no devices
        log.debug("could not list microphones: %s", e)
    return out


def bring_to_front(widget: QWidget) -> None:
    widget.show()
    widget.raise_()
    widget.activateWindow()
    if IS_MAC:
        try:
            from AppKit import NSApplication

            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
            pass


class _Relay(QObject):
    """Carries results from worker threads back to the UI thread."""

    done = Signal(str)


def _page(title: str, subtitle: str = "") -> tuple[QWidget, QVBoxLayout]:
    inner = QWidget()
    layout = QVBoxLayout(inner)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    layout.addWidget(heading(title))
    if subtitle:
        layout.addWidget(hint(subtitle))
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setWidget(inner)
    return scroll, layout


class SettingsWindow(QWidget):
    saved = Signal(object)  # Config
    rerun_setup = Signal()

    PAGES = ["General", "Speech", "AI editing", "Dictionary", "Styles", "History", "About"]

    def __init__(self, cfg: Config, history_factory=None):
        super().__init__()
        self.setWindowTitle("FreeFlow Settings")
        self.setWindowIcon(app_icon())
        self.resize(820, 600)
        self.cfg = copy.deepcopy(cfg)
        self._history_factory = history_factory
        self._loaded_keys: dict[str, str] = {}
        self._relay = _Relay()
        self._relay.done.connect(self._show_test_result)

        self.sidebar = QListWidget()
        self.sidebar.addItems(self.PAGES)
        self.sidebar.setFixedWidth(170)
        self.sidebar.setStyleSheet(
            "QListWidget { border: none; padding: 8px 6px; font-size: 14px; }"
            "QListWidget::item { padding: 7px 10px; border-radius: 6px; }"
        )
        self.stack = QStackedWidget()
        for build in (self._general, self._speech, self._ai, self._dictionary, self._styles,
                      self._history, self._about):
            self.stack.addWidget(build())
        self.sidebar.currentRowChanged.connect(self._switch)
        self.sidebar.setCurrentRow(0)

        self.saved_label = QLabel("")
        save = QPushButton("Save")
        save.setDefault(True)
        save.clicked.connect(self.save)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        footer = QHBoxLayout()
        footer.addWidget(self.saved_label)
        footer.addStretch()
        footer.addWidget(close)
        footer.addWidget(save)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self.sidebar)
        body.addWidget(self.stack, 1)
        root = QVBoxLayout(self)
        root.addLayout(body, 1)
        root.addLayout(footer)
        self.load(self.cfg)

    def _switch(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        if self.PAGES[row] == "History":
            self.refresh_history()

    def show_page(self, name: str) -> None:
        self.sidebar.setCurrentRow(self.PAGES.index(name))
        bring_to_front(self)

    # Pages ----------------------------------------------------------------

    def _general(self) -> QWidget:
        page, layout = _page("General", "Hold the dictation key in any app and speak. "
                             "Double-tap it for hands-free mode; tap again to finish. "
                             "Press Esc to cancel.")
        form = QFormLayout()
        self.dictate_key = ChoiceCombo(choices.DICTATE_KEYS, editable=True)
        self.command_key = ChoiceCombo(choices.COMMAND_KEYS, editable=True)
        self.paste_key = ChoiceCombo(choices.PASTE_LAST_KEYS, editable=True)
        form.addRow("Dictation key", self.dictate_key)
        form.addRow("Command mode key", self.command_key)
        form.addRow("Paste last result", self.paste_key)
        layout.addLayout(form)
        layout.addWidget(hint(
            "Command mode: select text, hold the command key and say what to change "
            "(\"make this friendlier\", \"translate to Spanish\"). With nothing selected "
            "it writes what you ask for. Custom keys: type names joined with +, e.g. "
            "ctrl_r+shift, alt_r, f8."
        ))
        form2 = QFormLayout()
        self.microphone = ChoiceCombo(input_devices())
        self.output_method = ChoiceCombo(choices.OUTPUT_METHODS)
        form2.addRow("Microphone", self.microphone)
        form2.addRow("Insert text by", self.output_method)
        layout.addLayout(form2)
        self.overlay = QCheckBox("Show the recording bar while dictating")
        self.sounds = QCheckBox("Play start and stop sounds")
        self.trailing_space = QCheckBox("Add a space after each dictation")
        self.launch_at_login = QCheckBox("Open FreeFlow when I log in")
        self.keep_mic = QCheckBox("Keep the microphone ready (never clips your first word; "
                                  "the mic indicator stays on)")
        self.save_history = QCheckBox("Save dictation history on this computer")
        for box in (self.overlay, self.sounds, self.trailing_space, self.launch_at_login,
                    self.keep_mic, self.save_history):
            layout.addWidget(box)
        layout.addStretch()
        return page

    def _speech(self) -> QWidget:
        page, layout = _page("Speech recognition",
                             "Turns your voice into words. Running it on this computer is "
                             "free and private; cloud options are faster on older machines.")
        form = QFormLayout()
        self.stt_provider = ChoiceCombo(choices.speech_providers())
        self.stt_model = ChoiceCombo([], editable=True)
        self.stt_language = ChoiceCombo(choices.LANGUAGES)
        self.stt_url = QLineEdit()
        self.stt_url.setPlaceholderText("http://localhost:8000/v1")
        self.stt_key = SecretField("API key")
        self.stt_key_link = hint("")
        form.addRow("Run speech recognition", self.stt_provider)
        form.addRow("Model", self.stt_model)
        form.addRow("Language", self.stt_language)
        self._stt_url_row = ("Server URL", self.stt_url)
        form.addRow(*self._stt_url_row)
        form.addRow("API key", self.stt_key)
        form.addRow("", self.stt_key_link)
        self._stt_form = form
        layout.addLayout(form)
        self.stt_note = hint("")
        layout.addWidget(self.stt_note)
        layout.addStretch()
        self.stt_provider.currentIndexChanged.connect(self._update_speech)
        return page

    def _update_speech(self) -> None:
        provider = self.stt_provider.value()
        current = self.stt_model.value()
        models = choices.SPEECH_MODELS.get(provider, [])
        self.stt_model.set_choices(models)
        if current not in [m for m, _ in models]:
            self.stt_model.set_value(choices.default_speech_model(provider))
        key_name = choices.SPEECH_KEY.get(provider)
        self._stt_form.setRowVisible(self.stt_key, key_name is not None)
        self._stt_form.setRowVisible(self.stt_key_link, key_name in choices.KEY_LINKS)
        self._stt_form.setRowVisible(self.stt_url, provider == "custom")
        if key_name:
            self.stt_key.setText(self._loaded_keys.setdefault(key_name, apikeys.read(key_name)))
            if link := choices.KEY_LINKS.get(key_name):
                self.stt_key_link.setText(f'<a href="{link}">Get a {provider.title()} API key</a>')
        self.stt_note.setText({
            "local": "Runs offline. The model downloads once the first time it's used.",
            "mlx": "Runs offline on the Apple Silicon GPU.",
            "groq": "Audio is sent to Groq for transcription.",
            "openai": "Audio is sent to OpenAI for transcription.",
            "custom": "Audio is sent to your server's /audio/transcriptions endpoint.",
        }.get(provider, ""))

    def _ai(self) -> QWidget:
        page, layout = _page("AI editing",
                             "Removes filler words, applies your corrections (\"no wait, "
                             "I mean...\"), fixes punctuation and matches the app's tone.")
        form = QFormLayout()
        self.ai_provider = ChoiceCombo(choices.CLEANUP_PROVIDERS)
        self.output_language = ChoiceCombo(choices.OUTPUT_LANGUAGES, editable=True)
        form.addRow("Edit with", self.ai_provider)
        form.addRow("Write in", self.output_language)
        layout.addLayout(form)

        self.claude_box = QGroupBox("Claude")
        cform = QFormLayout(self.claude_box)
        self.claude_model = ChoiceCombo(choices.CLAUDE_MODELS, editable=True)
        self.effort = ChoiceCombo(choices.EFFORTS)
        self.command_effort = ChoiceCombo(choices.EFFORTS)
        self.anthropic_key = SecretField("sk-ant-...")
        cform.addRow("Model", self.claude_model)
        cform.addRow("Dictation effort", self.effort)
        cform.addRow("Command effort", self.command_effort)
        cform.addRow("API key", self.anthropic_key)
        cform.addRow("", hint(f'<a href="{choices.KEY_LINKS["ANTHROPIC_API_KEY"]}">'
                              "Get an Anthropic API key</a>. You pay Anthropic per use; "
                              "costs shown are rough estimates for a short dictation."))
        layout.addWidget(self.claude_box)

        self.ollama_box = QGroupBox("Ollama")
        oform = QFormLayout(self.ollama_box)
        self.ollama_url = QLineEdit()
        self.ollama_model = QLineEdit()
        oform.addRow("Server", self.ollama_url)
        oform.addRow("Model", self.ollama_model)
        oform.addRow("", hint('Install from <a href="https://ollama.com">ollama.com</a>, '
                              "then run: ollama pull llama3.2"))
        layout.addWidget(self.ollama_box)

        test_box = QGroupBox("Try it")
        tlayout = QVBoxLayout(test_box)
        self.test_input = QLineEdit("um so I think we should uh meet on tuesday no wait wednesday")
        self.test_button = QPushButton("Run test")
        self.test_button.clicked.connect(self._run_test)
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        self.test_result.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row = QHBoxLayout()
        row.addWidget(self.test_input, 1)
        row.addWidget(self.test_button)
        tlayout.addLayout(row)
        tlayout.addWidget(self.test_result)
        layout.addWidget(test_box)
        layout.addStretch()
        self.ai_provider.currentIndexChanged.connect(self._update_ai)
        return page

    def _update_ai(self) -> None:
        provider = self.ai_provider.value()
        self.claude_box.setVisible(provider == "claude")
        self.ollama_box.setVisible(provider == "ollama")

    def _run_test(self) -> None:
        from freeflow.cleanup import Polisher, create_backend

        cfg = self.collect()
        if key := self.anthropic_key.text():
            os.environ["ANTHROPIC_API_KEY"] = key  # in memory until saved
        text = self.test_input.text()
        self.test_button.setEnabled(False)
        self.test_result.setText("Working...")

        def work():
            try:
                result = Polisher(cfg, create_backend(cfg.cleanup)).dictation(text, AppContext())
                msg = result.text if result.used_llm else f"{result.text}\n\n(basic cleanup: {result.note})"
            except Exception as e:
                msg = f"Error: {e}"
            self._relay.done.emit(msg)

        threading.Thread(target=work, daemon=True).start()

    def _show_test_result(self, text: str) -> None:
        self.test_button.setEnabled(True)
        self.test_result.setText(text)

    def _dictionary(self) -> QWidget:
        page, layout = _page("Dictionary", "Teach FreeFlow names, jargon and shortcuts.")
        layout.addWidget(QLabel("<b>Words to spell exactly</b> (one per line)"))
        self.words = QPlainTextEdit()
        self.words.setPlaceholderText("Anthropic\nKubernetes\nSiobhan")
        self.words.setMaximumHeight(130)
        layout.addWidget(self.words)
        layout.addWidget(QLabel("<b>Replacements</b> (always applied)"))
        self.replacements = PairTable("When it writes", "Change it to")
        layout.addWidget(self.replacements)
        layout.addWidget(QLabel("<b>Snippets</b> - say the phrase, get the text"))
        self.snippets = PairTable("Say", "Insert")
        layout.addWidget(self.snippets)
        layout.addWidget(hint("Snippet text is inserted on this computer and never sent "
                              "to an AI service."))
        return page

    def _styles(self) -> QWidget:
        page, layout = _page("Styles", "FreeFlow picks a writing style from the app you're "
                             "dictating into. Built in: chat apps are casual, mail apps "
                             "are email, document apps are formal, editors are code.")
        layout.addWidget(QLabel("<b>Your rules</b> (checked first)"))
        self.style_rules = PairTable("App or window title contains (comma-separated)",
                                     "Style: natural, casual, email, formal or code")
        layout.addWidget(self.style_rules)
        layout.addWidget(QLabel("<b>Style instructions</b> (leave blank for the default)"))
        self.style_edits: dict[str, QPlainTextEdit] = {}
        form = QFormLayout()
        for value, label in choices.STYLES:
            edit = QPlainTextEdit()
            edit.setPlaceholderText(STYLE_PROMPTS[value])
            edit.setMaximumHeight(64)
            self.style_edits[value] = edit
            form.addRow(label, edit)
        layout.addLayout(form)
        return page

    def _history(self) -> QWidget:
        page, layout = _page("History")
        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search")
        self.history_search.textChanged.connect(self.refresh_history)
        layout.addWidget(self.history_search)
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["When", "App", "Text"])
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setWordWrap(True)
        layout.addWidget(self.history_table, 1)
        copy_btn = QPushButton("Copy selected")
        copy_btn.clicked.connect(self._copy_history)
        clear_btn = QPushButton("Delete all history")
        clear_btn.clicked.connect(self._clear_history)
        row = QHBoxLayout()
        row.addWidget(copy_btn)
        row.addStretch()
        row.addWidget(clear_btn)
        layout.addLayout(row)
        return page

    def refresh_history(self) -> None:
        history = self._history_factory() if self._history_factory else None
        if history is None:
            self.stats_label.setText("History is turned off.")
            self.history_table.setRowCount(0)
            return
        s = history.stats()
        self.stats_label.setText(
            f"<b>{s.words:,}</b> words dictated ({s.words_today:,} today) · "
            f"<b>{s.wpm:.0f}</b> words per minute · about <b>{s.minutes_saved:.0f} min</b> "
            "saved vs. typing"
        )
        entries = history.recent(200, self.history_search.text().strip())
        self.history_table.setRowCount(len(entries))
        for row, e in enumerate(entries):
            when = datetime.fromtimestamp(e.created_at).strftime("%b %d, %H:%M")
            app = (e.app.split(" com.")[0] if e.app else "") + (" · command" if e.mode == "command" else "")
            for col, text in enumerate((when, app, e.final_text.strip())):
                item = QTableWidgetItem(text)
                item.setToolTip(e.raw_text if col == 2 else text)
                self.history_table.setItem(row, col, item)
        self.history_table.resizeColumnToContents(0)
        self.history_table.resizeColumnToContents(1)

    def _copy_history(self) -> None:
        rows = sorted({i.row() for i in self.history_table.selectedIndexes()})
        text = "\n".join(self.history_table.item(r, 2).text() for r in rows)
        if text:
            QGuiApplication.clipboard().setText(text)

    def _clear_history(self) -> None:
        history = self._history_factory() if self._history_factory else None
        if history and QMessageBox.question(
            self, "Delete history", "Delete all saved dictations? This can't be undone."
        ) == QMessageBox.Yes:
            history.clear()
            self.refresh_history()

    def _about(self) -> QWidget:
        page, layout = _page(f"FreeFlow {__version__}",
                             "Voice dictation that runs on your terms: no word limits, "
                             "your choice of providers, history kept on this computer.")
        folder = QPushButton("Open settings folder")
        folder.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(config.app_dir()))))
        log_btn = QPushButton("Open log")
        log_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(config.app_dir() / "freeflow.log"))))
        setup = QPushButton("Run setup again")
        setup.clicked.connect(self.rerun_setup.emit)
        for b in (folder, log_btn, setup):
            row = QHBoxLayout()
            row.addWidget(b)
            row.addStretch()
            layout.addLayout(row)
        layout.addWidget(hint(
            "Privacy: with on-device speech recognition and Ollama, nothing leaves this "
            "computer. With cloud providers, audio goes to the speech provider and the "
            "transcript (plus the app name and window title, for style) goes to the AI "
            "provider. API keys are stored in your system keychain."
        ))
        layout.addStretch()
        return page

    # Load / collect / save --------------------------------------------------

    def load(self, cfg: Config) -> None:
        h = cfg.hotkeys
        self.dictate_key.set_value(h.dictate)
        self.command_key.set_value(h.command)
        self.paste_key.set_value(h.paste_last)
        self.microphone.set_value(cfg.audio.device)
        self.output_method.set_value(cfg.output.method)
        self.overlay.setChecked(cfg.ui.overlay)
        self.sounds.setChecked(cfg.audio.sounds)
        self.trailing_space.setChecked(cfg.output.trailing_space)
        self.launch_at_login.setChecked(cfg.ui.launch_at_login)
        self.keep_mic.setChecked(cfg.audio.keep_mic_open)
        self.save_history.setChecked(cfg.history.enabled)

        t = cfg.transcription
        self.stt_provider.set_value(t.provider)
        self._update_speech()
        self.stt_model.set_value(t.model or choices.default_speech_model(t.provider))
        self.stt_language.set_value(t.language)
        self.stt_url.setText(t.base_url)

        c = cfg.cleanup
        self.ai_provider.set_value(c.provider)
        self.claude_model.set_value(c.model if c.provider == "claude" and c.model else "claude-opus-5-5")
        self.effort.set_value(c.effort)
        self.command_effort.set_value(c.command_effort)
        self.anthropic_key.setText(self._loaded_keys.setdefault(
            "ANTHROPIC_API_KEY", apikeys.read("ANTHROPIC_API_KEY")))
        self.ollama_url.setText(c.ollama_url)
        self.ollama_model.setText(c.model if c.provider == "ollama" and c.model else "llama3.2")
        self.output_language.set_value(c.translate_to)
        self._update_ai()

        self.words.setPlainText("\n".join(cfg.dictionary))
        self.replacements.set_pairs(cfg.replacements)
        self.snippets.set_pairs(cfg.snippets)
        self.style_rules.set_pairs({", ".join(r.match): _style_label(r.style) for r in cfg.styles})
        for name, edit in self.style_edits.items():
            edit.setPlainText(cfg.style_prompts.get(name, ""))

    def collect(self) -> Config:
        cfg = copy.deepcopy(self.cfg)
        cfg.hotkeys.dictate = self.dictate_key.value() or cfg.hotkeys.dictate
        cfg.hotkeys.command = self.command_key.value()
        cfg.hotkeys.paste_last = self.paste_key.value()
        cfg.audio.device = self.microphone.value()
        cfg.output.method = self.output_method.value()
        cfg.ui.overlay = self.overlay.isChecked()
        cfg.audio.sounds = self.sounds.isChecked()
        cfg.output.trailing_space = self.trailing_space.isChecked()
        cfg.ui.launch_at_login = self.launch_at_login.isChecked()
        cfg.audio.keep_mic_open = self.keep_mic.isChecked()
        cfg.history.enabled = self.save_history.isChecked()

        t = cfg.transcription
        t.provider = self.stt_provider.value()
        t.model = self.stt_model.value()
        if t.model == choices.default_speech_model(t.provider):
            t.model = ""  # keep following the provider default
        t.language = self.stt_language.value() or "auto"
        t.base_url = self.stt_url.text().strip()

        c = cfg.cleanup
        c.provider = self.ai_provider.value()
        c.model = {"claude": self.claude_model.value(),
                   "ollama": self.ollama_model.text().strip()}.get(c.provider, "")
        c.effort = self.effort.value()
        c.command_effort = self.command_effort.value()
        c.ollama_url = self.ollama_url.text().strip() or "http://localhost:11434"
        c.translate_to = self.output_language.value()

        cfg.dictionary = [w.strip() for w in self.words.toPlainText().splitlines() if w.strip()]
        cfg.replacements = self.replacements.pairs()
        cfg.snippets = self.snippets.pairs()
        cfg.styles = [
            StyleRule([m.strip() for m in k.split(",") if m.strip()], _style_value(v))
            for k, v in self.style_rules.pairs().items()
        ]
        cfg.style_prompts = {
            name: edit.toPlainText().strip()
            for name, edit in self.style_edits.items() if edit.toPlainText().strip()
        }
        # Keep custom styles defined in the config file but not shown here.
        for name, text in self.cfg.style_prompts.items():
            if name not in self.style_edits:
                cfg.style_prompts[name] = text
        return cfg

    def save(self) -> None:
        cfg = self.collect()
        keys = {"ANTHROPIC_API_KEY": self.anthropic_key.text()}
        if key_name := choices.SPEECH_KEY.get(cfg.transcription.provider):
            keys[key_name] = self.stt_key.text()
        try:
            for name, value in keys.items():
                # Only touch keys the user edited, so a key exported in the
                # shell isn't removed just because the field was blank.
                if value != self._loaded_keys.get(name, ""):
                    apikeys.store(name, value)
                    self._loaded_keys[name] = value
            if cfg.ui.launch_at_login != autostart.is_enabled():
                autostart.set_enabled(cfg.ui.launch_at_login)
            config.save(cfg)
        except Exception as e:
            log.exception("saving settings failed")
            QMessageBox.warning(self, "FreeFlow", f"Could not save settings: {e}")
            return
        self.cfg = cfg
        self.saved_label.setText("Saved. Your changes are active.")
        self.saved.emit(copy.deepcopy(cfg))


def _style_label(style: str) -> str:
    return "natural" if style == "default" else style


def _style_value(text: str) -> str:
    text = text.strip().lower()
    return "default" if text in ("", "natural", "default") else text
