"""Command-line entry point: `freeflow run`, `freeflow transcribe`, and friends."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime

from freeflow import __version__, config
from freeflow.config import IS_MAC, Config

log = logging.getLogger("freeflow")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in ("httpx", "httpx2", "httpcore", "anthropic", "urllib3", "faster_whisper"):
        logging.getLogger(noisy).setLevel(logging.DEBUG if verbose else logging.WARNING)


def _load() -> Config:
    path = config.config_path()
    cfg = config.load(path)
    log.debug("config: %s (%s)", path, "found" if path.exists() else "defaults")
    return cfg


def _polisher(cfg: Config):
    from freeflow.cleanup import Polisher, create_backend

    return Polisher(cfg, create_backend(cfg.cleanup))


def _pipeline(cfg: Config):
    from freeflow import transcribe
    from freeflow.app import Pipeline

    return Pipeline(cfg, transcribe.create(cfg.transcription), _polisher(cfg))


def _history(cfg: Config):
    from freeflow.history import History

    return History(config.app_dir() / "history.db") if cfg.history.enabled else None


# Commands --------------------------------------------------------------------


def cmd_run(args) -> int:
    from freeflow import tray
    from freeflow.app import App
    from freeflow.audio import Recorder
    from freeflow.output import Output

    cfg = _load()
    pipeline = _pipeline(cfg)
    app = App(cfg, pipeline, Recorder(cfg.audio), Output(cfg.output), _history(cfg))

    if not args.no_tray and tray.available():
        icon = tray.Tray(on_paste_last=app._on_paste_last, on_quit=app.stop)

        def status(state: str, message: str) -> None:
            log.info("%-10s %s", state, message)
            icon.update(state, message)

        app.status = status
        icon.run(setup=app.start)
        return 0

    app.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()
    return 0


def cmd_init(args) -> int:
    try:
        path = config.write_default(overwrite=args.force)
    except FileExistsError as e:
        print(f"{e} already exists (use --force to overwrite)")
        return 1
    print(f"Wrote {path}")
    return 0


def cmd_devices(args) -> int:
    from freeflow.audio import list_devices

    print(list_devices())
    return 0


def cmd_transcribe(args) -> int:
    from freeflow.audio import Recording
    from freeflow.context import AppContext

    cfg = _load()
    pipeline = _pipeline(cfg)
    rec = Recording.from_file(args.file, cfg.audio.sample_rate)
    if skip := pipeline.check_audio(rec):
        print(f"Skipped: {skip}", file=sys.stderr)
        return 1
    if args.raw:
        raw, ms = pipeline.transcribe(rec)
        print(raw)
        print(f"[{ms} ms]", file=sys.stderr)
        return 0
    mode = "command" if args.command else "dictate"
    out = pipeline.run(rec, mode, AppContext(app=args.app), selection=args.selection)
    print(out.text.rstrip())
    print(f"[raw: {out.raw!r}] [style: {out.style or '-'}] [stt {out.stt_ms} ms, "
          f"cleanup {out.llm_ms} ms]{' [' + out.note + ']' if out.note else ''}",
          file=sys.stderr)
    return 0


def cmd_clean(args) -> int:
    from freeflow.context import AppContext

    cfg = _load()
    polisher = _polisher(cfg)
    t0 = time.perf_counter()
    result = polisher.dictation(args.text, AppContext(app=args.app))
    print(result.text)
    print(f"[style: {result.style or '-'}] [{(time.perf_counter() - t0) * 1000:.0f} ms]"
          f"{' [' + result.note + ']' if result.note else ''}", file=sys.stderr)
    return 0


def cmd_history(args) -> int:
    history = _history(_load())
    if history is None:
        print("History is disabled in config.")
        return 1
    entries = history.recent(args.n, args.search)
    if not entries:
        print("No dictations yet." if not args.search else "No matches.")
    for e in reversed(entries):
        when = datetime.fromtimestamp(e.created_at).strftime("%Y-%m-%d %H:%M")
        print(f"#{e.id} {when} [{e.mode}] {e.app or '-'}")
        print(f"  {e.final_text.strip()}")
        if args.raw:
            print(f"  raw: {e.raw_text}")
    return 0


def cmd_stats(args) -> int:
    history = _history(_load())
    if history is None:
        print("History is disabled in config.")
        return 1
    s = history.stats()
    print(f"Dictations:    {s.sessions}")
    print(f"Words:         {s.words} ({s.words_today} today)")
    print(f"Speaking pace: {s.wpm:.0f} words/min")
    print(f"Time saved:    {s.minutes_saved:.0f} min vs typing at 40 wpm")
    return 0


def cmd_clear_history(args) -> int:
    history = _history(_load())
    if history:
        history.clear()
        print("History cleared.")
    return 0


def cmd_doctor(args) -> int:
    from freeflow.hotkeys import Combo

    ok = True

    def report(good: bool, label: str, detail: str = "") -> None:
        nonlocal ok
        ok &= good
        print(f"  [{'ok' if good else '!!'}] {label}{': ' + detail if detail else ''}")

    path = config.config_path()
    print(f"FreeFlow {__version__}")
    print(f"Config: {path} ({'found' if path.exists() else 'not found, using defaults; run `freeflow init`'})")
    try:
        cfg = config.load(path)
        report(True, "config parses")
    except Exception as e:
        report(False, "config parses", str(e))
        return 1

    h = cfg.hotkeys
    report(bool(Combo(h.dictate)), "dictate hotkey", h.dictate)
    report(True, "command hotkey", h.command or "(disabled)")

    try:
        import sounddevice as sd

        dev = sd.query_devices(kind="input")
        report(True, "microphone", str(dev["name"]))
    except Exception as e:
        report(False, "microphone", str(e))

    try:
        from freeflow import transcribe

        t0 = time.perf_counter()
        stt = transcribe.create(cfg.transcription)
        report(True, f"transcription ({cfg.transcription.provider})",
               f"{getattr(stt, 'model_name', '')} ready in {time.perf_counter() - t0:.1f}s")
    except Exception as e:
        report(False, f"transcription ({cfg.transcription.provider})", str(e))

    try:
        from freeflow.cleanup import create_backend
        from freeflow.context import AppContext

        backend = create_backend(cfg.cleanup)
        if backend is None:
            report(True, "cleanup", "rules only (provider = none)")
        else:
            from freeflow.cleanup import Polisher

            t0 = time.perf_counter()
            result = Polisher(cfg, backend).dictation(
                "um so I think we should uh meet on tuesday no wait wednesday", AppContext()
            )
            ms = (time.perf_counter() - t0) * 1000
            report(result.used_llm, f"cleanup ({backend.name} {getattr(backend, 'model', '')})",
                   f"{result.text!r} in {ms:.0f} ms" if result.used_llm else result.note)
    except Exception as e:
        report(False, "cleanup", str(e))

    if IS_MAC:
        print("\nmacOS permissions (System Settings > Privacy & Security), for the app you")
        print("launch freeflow from (Terminal, iTerm, ...): Microphone, Accessibility,")
        print("Input Monitoring. For the fn key: Keyboard > 'Press fn key to' > Do Nothing.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="freeflow",
        description="Hold a key, speak, and polished text appears at your cursor.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("run", help="start dictation (default)")
    p.add_argument("--no-tray", action="store_true", help="don't show a tray icon")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("init", help="write a starter config file")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    sub.add_parser("doctor", help="check config, mic, and providers").set_defaults(func=cmd_doctor)
    sub.add_parser("devices", help="list audio input devices").set_defaults(func=cmd_devices)

    p = sub.add_parser("transcribe", help="run the full pipeline on an audio file")
    p.add_argument("file")
    p.add_argument("--app", default="", help="pretend this app is focused, e.g. Slack")
    p.add_argument("--raw", action="store_true", help="speech-to-text only, no cleanup")
    p.add_argument("--command", action="store_true", help="treat the audio as a command")
    p.add_argument("--selection", default="", help="selected text for --command")
    p.set_defaults(func=cmd_transcribe)

    p = sub.add_parser("clean", help="run AI cleanup on typed text")
    p.add_argument("text")
    p.add_argument("--app", default="")
    p.set_defaults(func=cmd_clean)

    p = sub.add_parser("history", help="show recent dictations")
    p.add_argument("-n", type=int, default=20)
    p.add_argument("--search", default="")
    p.add_argument("--raw", action="store_true", help="also show the raw transcript")
    p.set_defaults(func=cmd_history)

    sub.add_parser("stats", help="words dictated, pace, time saved").set_defaults(func=cmd_stats)
    sub.add_parser("clear-history", help="delete all history").set_defaults(func=cmd_clear_history)

    argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(argv)
    if args.cmd is None:
        args = parser.parse_args([*argv, "run"])
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
