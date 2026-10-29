import threading

import pytest

from freeflow.hotkeys import HotkeyStateMachine
from freeflow.mouse import MouseTrigger
from freeflow.transcribe import BackgroundTranscriber, TranscriberError
from tests.test_hotkeys import FakeScheduler


def make_trigger(text_cursor=True, caret=False):
    events = []
    sched = FakeScheduler()
    machine = HotkeyStateMachine(lambda a, **kw: events.append(a), schedule=FakeScheduler())
    trigger = MouseTrigger(machine, hold_seconds=0.4, schedule=sched,
                           pointer_over_text=lambda: text_cursor, caret_in_focus=lambda: caret)
    return trigger, machine, events, sched


def test_hold_records_until_release():
    trigger, machine, events, sched = make_trigger()
    trigger.press(100, 100)
    assert events == []  # nothing until the hold time passes
    sched.fire()
    assert events == ["start"] and machine.recording
    trigger.move(103, 102)  # a little jitter is fine
    trigger.release()
    assert events == ["start", "stop"]
    assert machine.state == machine.IDLE


def test_short_click_is_just_a_click():
    trigger, machine, events, sched = make_trigger()
    trigger.press(100, 100)
    trigger.release()
    sched.fire()  # the stale timer must not start anything
    assert events == []


def test_dragging_never_starts_and_cancels_a_recording():
    trigger, machine, events, sched = make_trigger()
    trigger.press(100, 100)
    trigger.move(130, 100)  # selecting text
    sched.fire()
    assert events == []
    trigger.release()

    trigger.press(100, 100)
    sched.fire()
    trigger.move(200, 100)  # started, then dragged away
    assert events == ["start", "cancel"]
    trigger.release()
    assert events == ["start", "cancel"]


def test_only_in_text_boxes():
    trigger, _, events, sched = make_trigger(text_cursor=False, caret=False)
    trigger.press(5, 5)  # e.g. a window title bar
    sched.fire()
    trigger.release()
    assert events == []

    trigger, _, events, sched = make_trigger(text_cursor=False, caret=True)
    trigger.press(5, 5)  # custom pointer, but the click focused a text box
    sched.fire()
    assert events == ["start"]


def test_paused_trigger_ignores_presses():
    trigger, _, events, sched = make_trigger()
    trigger.enabled = False
    trigger.press(1, 1)
    sched.fire()
    trigger.release()
    assert events == []


def test_keyboard_does_not_interfere_with_mouse_dictation():
    trigger, machine, events, sched = make_trigger()
    trigger.press(1, 1)
    sched.fire()
    machine.interrupt()  # typing while holding the mouse button
    machine.update(1.0, True, False)
    machine.update(1.2, False, False)
    assert events == ["start"]
    trigger.release()
    assert events == ["start", "stop"]


def test_background_transcriber_waits_for_model():
    gate = threading.Event()

    class Slow:
        name = "slow"

        def __init__(self):
            gate.wait(5)

        def transcribe(self, audio, prompt=""):
            return "hello"

    stt = BackgroundTranscriber(Slow)
    assert not stt.ready and stt.name == "loading"
    result = []
    worker = threading.Thread(target=lambda: result.append(stt.transcribe(None)))
    worker.start()
    worker.join(0.2)
    assert result == []  # still waiting for the model
    gate.set()
    worker.join(5)
    assert result == ["hello"] and stt.name == "slow"


def test_background_transcriber_reports_load_errors():
    def boom():
        raise RuntimeError("no internet")

    stt = BackgroundTranscriber(boom)
    assert stt.wait(5)
    with pytest.raises(TranscriberError, match="no internet"):
        stt.transcribe(None)
