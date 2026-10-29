from freeflow.config import HotkeyConfig
from freeflow.hotkeys import Combo, HotkeyListener, HotkeyStateMachine


class FakeScheduler:
    def __init__(self):
        self.pending = []

    def __call__(self, delay, fn):
        entry = {"fn": fn, "live": True}
        self.pending.append(entry)

        def cancel():
            entry["live"] = False

        return cancel

    def fire(self):
        pending, self.pending = self.pending, []
        for entry in pending:
            if entry["live"]:
                entry["fn"]()


def make_machine():
    events = []
    sched = FakeScheduler()

    def emit(action, **kw):
        events.append((action, kw) if kw else action)

    m = HotkeyStateMachine(emit, tap_max_seconds=0.3, double_tap_window=0.4, schedule=sched)
    return m, events, sched


def test_hold_to_talk():
    m, events, _ = make_machine()
    m.update(0.0, True, False)
    m.update(1.5, False, False)
    assert events == [("start", {"command": False}), "stop"]
    assert m.state == m.IDLE


def test_single_short_tap_is_discarded_after_window():
    m, events, sched = make_machine()
    m.update(0.0, True, False)
    m.update(0.1, False, False)
    assert m.state == m.TAP_PENDING and m.recording
    sched.fire()
    assert events == [("start", {"command": False}), "cancel"]
    assert m.state == m.IDLE


def test_double_tap_enters_hands_free_until_next_press():
    m, events, sched = make_machine()
    m.update(0.0, True, False)
    m.update(0.1, False, False)
    m.update(0.2, True, False)  # second tap
    m.update(0.3, False, False)
    sched.fire()  # stale timer must not cancel hands-free
    assert m.state == m.HANDS_FREE
    m.update(9.0, True, False)
    assert events[-1] == "stop"
    m.update(9.1, False, False)
    assert m.state == m.IDLE
    assert events == [("start", {"command": False}), "hands_free", "stop"]


def test_command_combo_joining_a_dictation_upgrades_it():
    m, events, _ = make_machine()
    m.update(0.0, True, False)  # fn
    m.update(0.1, True, True)  # fn+ctrl
    m.update(0.2, True, False)  # ctrl released first
    m.update(0.25, False, False)
    assert events == [("start", {"command": False}), "command", "stop"]


def test_command_combo_pressed_directly():
    m, events, _ = make_machine()
    m.update(0.0, True, True)
    m.update(2.0, False, False)
    assert events == [("start", {"command": True}), "stop"]


def test_interrupt_cancels_push_to_talk_and_waits_for_release():
    m, events, _ = make_machine()
    m.update(0.0, True, False)
    m.interrupt()
    assert events[-1] == "cancel"
    assert m.state == m.WAIT_RELEASE
    m.update(0.5, False, False)
    assert m.state == m.IDLE
    m.update(1.0, True, False)
    assert events[-1] == ("start", {"command": False})


def test_interrupt_is_ignored_in_hands_free():
    m, events, _ = make_machine()
    m.update(0.0, True, False)
    m.update(0.1, False, False)
    m.update(0.2, True, False)
    m.update(0.3, False, False)
    m.interrupt()
    assert m.state == m.HANDS_FREE
    m.cancel()
    assert events[-1] == "cancel" and m.state == m.IDLE


def test_finish_stops_an_active_recording():
    m, events, _ = make_machine()
    m.update(0.0, True, False)
    m.finish()
    assert events[-1] == "stop"
    m.update(5.0, False, False)
    assert m.state == m.IDLE
    m.finish()
    assert events.count("stop") == 1


def test_combo_matching_and_aliases():
    assert Combo("ctrl_r").active({"ctrl_r"})
    assert not Combo("ctrl_r").active({"ctrl_l"})
    assert Combo("ctrl+shift").active({"ctrl_l", "shift_r"})
    assert Combo("Control+Option").active({"ctrl", "alt_r"})
    assert Combo("ctrl_l").active({"ctrl"})
    assert not Combo("").active({"ctrl"})
    assert not Combo("ctrl+shift").active({"ctrl"})


def _listener(**overrides):
    cfg = HotkeyConfig(dictate="ctrl_r", command="ctrl_r+shift", paste_last="alt+shift+z",
                       cancel="esc", **overrides)
    events, pasted = [], []
    machine = HotkeyStateMachine(lambda a, **kw: events.append(a), schedule=FakeScheduler())
    return HotkeyListener(cfg, machine, on_paste_last=lambda: pasted.append(1)), events, pasted


def test_listener_chorded_key_cancels_dictation():
    listener, events, _ = _listener()
    listener.key_down("ctrl_r")
    listener.key_down("c")  # ctrl+c: a shortcut, not dictation
    assert events == ["start", "cancel"]


def test_listener_shift_upgrades_to_command_mode():
    listener, events, _ = _listener()
    listener.key_down("ctrl_r")
    listener.key_down("shift")
    assert events == ["start", "command"]


def test_listener_escape_cancels_and_paste_last_fires_once():
    listener, events, pasted = _listener()
    listener.key_down("ctrl_r")
    listener.key_down("esc")
    assert events == ["start", "cancel"]
    listener.key_up("esc")
    listener.key_up("ctrl_r")
    for key in ("alt", "shift", "z"):
        listener.key_down(key)
    listener.key_down("z")  # auto-repeat
    assert pasted == [1]
    assert listener.held() == {"alt", "shift", "z"}
