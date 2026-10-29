import os
import plistlib
import time

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from freeflow import apikeys, autostart, config  # noqa: E402
from freeflow.app import Session  # noqa: E402
from freeflow.config import Config, StyleRule  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEFLOW_HOME", str(tmp_path))
    monkeypatch.setattr(apikeys, "_keyring", lambda: None)  # use the private-file fallback
    for name in apikeys.KEY_LABELS:
        monkeypatch.delenv(name, raising=False)
    return tmp_path


def _wait(qapp, predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_api_keys_fallback_file(home):
    apikeys.store("ANTHROPIC_API_KEY", " sk-ant-test ")
    assert apikeys.read("ANTHROPIC_API_KEY") == "sk-ant-test"
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
    if os.name == "posix":
        assert oct((home / "keys.json").stat().st_mode & 0o777) == "0o600"
    apikeys.store("ANTHROPIC_API_KEY", "")
    assert apikeys.read("ANTHROPIC_API_KEY") == ""
    assert "ANTHROPIC_API_KEY" not in os.environ


def test_settings_round_trip_and_save(qapp, home):
    from freeflow.gui.settings import SettingsWindow

    cfg = Config(dictionary=["Anthropic"], replacements={"chat gpt": "ChatGPT"},
                 snippets={"my email": "me@example.com"},
                 styles=[StyleRule(["linear", "jira"], "formal")],
                 style_prompts={"casual": "lowercase", "pirate": "Talk like a pirate."})
    cfg.cleanup.model = "claude-haiku-5-5"
    cfg.transcription.language = "ar"
    window = SettingsWindow(cfg)
    assert window.collect() == cfg

    window.dictate_key.set_value("alt_r")
    window.stt_provider.set_value("groq")
    window.stt_key.setText("gsk_test")
    window.anthropic_key.setText("sk-ant-test")
    saved = []
    window.saved.connect(saved.append)
    window.save()
    assert saved and saved[0].hotkeys.dictate == "alt_r"
    assert saved[0].transcription.provider == "groq"
    assert saved[0].transcription.model == ""  # provider default (whisper-large-v3-turbo)
    assert window.stt_model.value() == "whisper-large-v3-turbo"
    assert config.load(home / "config.toml") == saved[0]
    assert apikeys.read("GROQ_API_KEY") == "gsk_test"
    assert apikeys.read("ANTHROPIC_API_KEY") == "sk-ant-test"


def test_settings_does_not_clear_shell_key(qapp, home, monkeypatch):
    from freeflow.gui.settings import SettingsWindow

    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-shell")
    window = SettingsWindow(Config())
    window.save()
    assert os.environ["ANTHROPIC_API_KEY"] == "from-shell"


def test_history_page(qapp, home):
    from freeflow.gui.settings import SettingsWindow
    from freeflow.history import History

    history = History(home / "history.db")
    history.add("dictate", "um hi", "Hi.", app="Slack", audio_seconds=1)
    window = SettingsWindow(Config(), history_factory=lambda: history)
    window.show_page("History")
    assert window.history_table.rowCount() == 1
    assert window.history_table.item(0, 2).text() == "Hi."


def test_wizard_setups(qapp, home):
    from freeflow.gui.onboarding import SetupWizard, apply_setup

    cloud = apply_setup(Config(), "cloud", "small", False, "claude-haiku-5-5")
    assert (cloud.transcription.provider, cloud.cleanup.provider) == ("groq", "claude")
    assert cloud.cleanup.model == "claude-haiku-5-5"
    private = apply_setup(Config(), "private", "base", has_ollama=True)
    assert (private.transcription.model, private.cleanup.provider) == ("base", "ollama")
    assert apply_setup(Config(), "private", "base", has_ollama=False).cleanup.provider == "none"

    wizard = SetupWizard(Config())
    done = []
    wizard.finished_setup.connect(done.append)
    wizard.show()
    wizard.next()  # setup choice
    assert wizard.currentPage() is wizard.setup_page
    wizard.accept()
    assert done and done[0].ui.onboarded and done[0].transcription.provider == "local"

    perms_only = SetupWizard(Config(), permissions_only=True)
    assert perms_only.result_config() == Config()


def test_flow_bar_states(qapp):
    from freeflow.gui.overlay import FlowBar

    session = Session(1, "dictate", 0.0)
    bar = FlowBar(lambda: 0.05, lambda: session)
    bar.on_status("recording", "dictate")
    assert bar.isVisible() and bar.mode == "recording"
    bar._animate()
    session.hands_free = True
    assert bar._label(session) == "Hands-free"
    bar.on_status("processing", "")
    assert bar.mode == "processing"
    bar.on_status("idle", "inserted 4 words, stt 300 ms")
    assert not bar.isVisible()
    bar.on_status("recording", "")
    bar.on_status("idle", "no speech detected")
    assert bar.mode == "message" and bar.text == "no speech detected"
    bar.enabled = False
    bar.on_status("recording", "")
    assert bar.mode == "message"


def test_engine_boots_and_restarts(qapp, home, monkeypatch):
    from freeflow.gui.engine import Engine
    from freeflow.hotkeys import HotkeyListener

    monkeypatch.setattr(HotkeyListener, "start", lambda self: None)  # no display here
    monkeypatch.setattr(HotkeyListener, "stop", lambda self: None)
    cfg = Config()
    cfg.transcription.provider = "custom"
    cfg.transcription.base_url = "http://127.0.0.1:9/v1"
    cfg.cleanup.provider = "none"
    engine = Engine()
    states = []
    engine.status.connect(lambda s, m: states.append(s))
    engine.start(cfg)
    assert _wait(qapp, lambda: engine.app is not None and "ready" in states)
    first_stt = engine.app.pipeline.transcriber
    engine.set_paused(True)
    assert engine.paused
    cfg2 = Config(**{**cfg.__dict__})
    cfg2.dictionary = ["FreeFlow"]
    engine.start(cfg2)
    assert _wait(qapp, lambda: engine.app is not None and engine.app.cfg is cfg2)
    assert engine.app.pipeline.transcriber is first_stt  # speech model reused
    engine.stop()
    assert engine.app is None


def test_engine_reports_errors(qapp, home):
    from freeflow.gui.engine import Engine

    cfg = Config()
    cfg.transcription.provider = "groq"  # no key set
    engine = Engine()
    errors = []
    engine.status.connect(lambda s, m: errors.append(m) if s == "error" else None)
    engine.start(cfg)
    assert _wait(qapp, lambda: bool(errors))
    assert "groq" in errors[0].lower()


def test_controller_tray_and_settings(qapp, home, monkeypatch):
    from freeflow.gui.main import Controller
    from freeflow.hotkeys import HotkeyListener

    monkeypatch.setattr(HotkeyListener, "start", lambda self: None)
    monkeypatch.setattr(HotkeyListener, "stop", lambda self: None)
    cfg = Config()
    cfg.ui.onboarded = True
    cfg.transcription.provider = "custom"
    cfg.transcription.base_url = "http://127.0.0.1:9/v1"
    cfg.cleanup.provider = "none"
    controller = Controller(qapp, cfg)
    controller.start()
    assert _wait(qapp, lambda: controller.engine.app is not None)
    assert controller.status_action.text().startswith("Ready")
    controller.pause_action.setChecked(True)
    assert controller.engine.paused
    assert _wait(qapp, lambda: controller.status_action.text() == "Paused")

    controller.show_settings("Dictionary")
    controller.settings.words.setPlainText("FreeFlow")
    controller.settings.save()
    assert _wait(qapp, lambda: controller.engine.app is not None
                 and controller.engine.app.cfg.dictionary == ["FreeFlow"])
    assert not controller.engine.paused  # a settings change resumes dictation
    assert config.load().dictionary == ["FreeFlow"]
    controller.engine.stop()


def test_autostart_files(home, monkeypatch, tmp_path):
    monkeypatch.setattr(autostart.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(autostart, "IS_MAC", True)
    monkeypatch.setattr(autostart, "IS_WINDOWS", False)
    autostart.set_enabled(True)
    plist = plistlib.loads((tmp_path / "Library/LaunchAgents/com.freeflow.app.plist").read_bytes())
    assert plist["RunAtLoad"] and plist["ProgramArguments"][-2:] == ["-m", "freeflow.gui"]
    assert autostart.is_enabled()
    autostart.set_enabled(False)
    assert not autostart.is_enabled()
