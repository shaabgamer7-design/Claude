import numpy as np
import pytest

from freeflow.app import App, Pipeline, Session
from freeflow.audio import Recording
from freeflow.cleanup import Polisher
from freeflow.config import AudioConfig, Config
from freeflow.context import AppContext
from freeflow.history import History


class FakeTranscriber:
    name = "fake"

    def __init__(self, text="", error=None):
        self.text, self.error, self.prompts = text, error, []

    def transcribe(self, audio, prompt=""):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.text


class FakeBackend:
    name = "fake"

    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, user, effort):
        return self.reply


class FakeOutput:
    def __init__(self, selection=""):
        self.inserted, self.selection = [], selection

    def insert(self, text, app=""):
        self.inserted.append(text)

    def copy_selection(self):
        return self.selection


class FakeRecorder:
    def warm_up(self): ...
    def close(self): ...


def speech(seconds=1.0, rate=16000, amplitude=0.1):
    t = np.arange(int(seconds * rate)) / rate
    return Recording((amplitude * np.sin(2 * np.pi * 220 * t)).astype(np.float32), rate)


def make_pipeline(text="um hello world", reply=None, cfg=None, error=None):
    cfg = cfg or Config(dictionary=["FreeFlow"])
    backend = FakeBackend(reply) if reply is not None else None
    return Pipeline(cfg, FakeTranscriber(text, error), Polisher(cfg, backend))


def test_check_audio():
    p = make_pipeline()
    assert p.check_audio(speech(0.1)) == "too short"
    assert "no speech" in p.check_audio(Recording(np.zeros(16000, np.float32), 16000))
    assert p.check_audio(speech()) == ""


def test_dictation_rules_only_adds_trailing_space():
    p = make_pipeline()
    out = p.run(speech(), "dictate", AppContext())
    assert out.text == "Hello world "
    assert out.raw == "um hello world"
    assert p.transcriber.prompts == ["FreeFlow."]


def test_command_mode_passes_selection():
    p = make_pipeline(text="make it shout", reply="HELLO")
    out = p.run(speech(), "command", AppContext(), selection="hello")
    assert out.text == "HELLO"  # no trailing space when replacing a selection


def test_empty_transcript():
    out = make_pipeline(text="  ").run(speech(), "dictate", AppContext())
    assert out.text == "" and out.note == "no speech recognized"


def make_app(tmp_path, pipeline, output):
    cfg = pipeline.cfg
    cfg.audio = AudioConfig(sounds=False)
    statuses = []
    app = App(cfg, pipeline, FakeRecorder(), output, History(tmp_path / "h.db"),
              status=lambda state, msg: statuses.append((state, msg)))
    return app, statuses


def test_app_process_inserts_and_records_history(tmp_path):
    output = FakeOutput()
    app, statuses = make_app(tmp_path, make_pipeline(reply="Hello, world."), output)
    session = Session(1, "dictate", 0.0, AppContext(app="Slack"))
    app._process(session, speech())
    assert output.inserted == ["Hello, world. "]
    assert app.last_text == "Hello, world. "
    entry = app.history.last()
    assert entry.app == "Slack" and entry.style == "casual" and entry.raw_text == "um hello world"
    assert statuses[-1][0] == "idle" and "inserted 2 words" in statuses[-1][1]


def test_app_command_mode_copies_selection_first(tmp_path):
    output = FakeOutput(selection="hi")
    app, _ = make_app(tmp_path, make_pipeline(text="capitalize", reply="HI"), output)
    app._process(Session(1, "command", 0.0), speech())
    assert output.inserted == ["HI"]


def test_app_saves_audio_when_transcription_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("FREEFLOW_HOME", str(tmp_path))
    output = FakeOutput()
    app, statuses = make_app(tmp_path, make_pipeline(error=RuntimeError("boom")), output)
    app._process(Session(1, "dictate", 0.0), speech())
    assert output.inserted == []
    assert statuses[-1][0] == "error"
    saved = list((tmp_path / "failed").glob("*.wav"))
    assert len(saved) == 1
    assert Recording.from_file(str(saved[0])).duration == pytest.approx(1.0, abs=0.01)


def test_recording_wav_roundtrip_and_normalize():
    rec = speech(0.5, amplitude=0.01)
    louder = rec.normalized()
    assert np.max(np.abs(louder.samples)) == pytest.approx(0.2, rel=0.01)  # capped at 20x
    assert louder.rms_db() > rec.rms_db()
    assert speech(amplitude=0.95).normalized().samples.max() <= 0.95
