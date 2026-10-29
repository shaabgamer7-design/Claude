"""Configuration: defaults, on-disk TOML, and per-OS paths."""

from __future__ import annotations

import dataclasses
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

log = logging.getLogger(__name__)

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")


def app_dir() -> Path:
    """Directory holding config.toml and history.db."""
    if env := os.environ.get("FREEFLOW_HOME"):
        return Path(env).expanduser()
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "FreeFlow"
    if IS_WINDOWS:
        return Path(os.environ.get("APPDATA", Path.home())) / "FreeFlow"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "freeflow"


def config_path() -> Path:
    return app_dir() / "config.toml"


@dataclass
class HotkeyConfig:
    # Hold to dictate; double-tap to start hands-free mode, tap again to stop.
    dictate: str = "fn" if IS_MAC else "ctrl_r"
    # Hold with text selected to edit it by voice ("make this friendlier").
    # With nothing selected, the spoken request is answered and inserted.
    command: str = "fn+ctrl" if IS_MAC else "ctrl_r+shift"
    # Re-paste the most recent result. Empty disables it.
    paste_last: str = "ctrl+cmd+v" if IS_MAC else "alt+shift+z"
    cancel: str = "esc"
    # A press shorter than this counts as a tap (for double-tap detection).
    tap_max_seconds: float = 0.3
    double_tap_window: float = 0.4
    # Hold the left mouse button in a text box to dictate; release to insert.
    mouse_hold: bool = True
    mouse_hold_seconds: float = 0.4  # shorter presses are ordinary clicks
    mouse_text_only: bool = True  # only where the pointer is a text cursor (Windows)


@dataclass
class AudioConfig:
    device: str = ""  # input device name or index; empty = system default
    sample_rate: int = 16000
    min_seconds: float = 0.3
    # Recordings quieter than this (RMS, dBFS) are treated as silence.
    silence_threshold_db: float = -55.0
    # Boost quiet or whispered speech before transcription.
    normalize: bool = True
    # Keep the microphone stream open so the first syllable is never clipped.
    keep_mic_open: bool = False
    sounds: bool = True
    max_seconds: float = 600.0


@dataclass
class TranscriptionConfig:
    provider: str = "local"  # local | mlx | groq | openai | custom
    model: str = ""  # empty = provider default
    language: str = "auto"  # "auto" or an ISO code such as "en", "de", "ar"
    base_url: str = ""  # custom provider only
    api_key_env: str = ""  # env var holding the key; empty = provider default
    device: str = "auto"  # local provider: auto | cpu | cuda
    compute_type: str = "auto"  # local provider: auto | int8 | float16 | ...
    timeout_seconds: float = 30.0


@dataclass
class CleanupConfig:
    provider: str = "claude"  # claude | ollama | none
    model: str = ""  # empty = provider default
    effort: str = "low"  # claude: low | medium | high | xhigh | max
    command_effort: str = "medium"
    ollama_url: str = "http://localhost:11434"
    # Output language for dictation, e.g. "English". Empty keeps the spoken language.
    translate_to: str = ""
    timeout_seconds: float = 30.0


@dataclass
class OutputConfig:
    method: str = "paste"  # paste | type | clipboard
    restore_clipboard: bool = True
    restore_delay_seconds: float = 0.4
    trailing_space: bool = True


@dataclass
class HistoryConfig:
    enabled: bool = True


@dataclass
class UIConfig:
    overlay: bool = True  # floating recording bar near the bottom of the screen
    launch_at_login: bool = False
    onboarded: bool = False  # first-run setup completed


@dataclass
class StyleRule:
    match: list[str]
    style: str


@dataclass
class Config:
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    cleanup: CleanupConfig = field(default_factory=CleanupConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    # Words the speech model and the cleanup model should spell exactly.
    dictionary: list[str] = field(default_factory=list)
    # Case-insensitive find -> replace applied to every result.
    replacements: dict[str, str] = field(default_factory=dict)
    # Spoken cue -> text inserted verbatim.
    snippets: dict[str, str] = field(default_factory=dict)
    # Checked before the built-in app -> style rules.
    styles: list[StyleRule] = field(default_factory=list)
    # Override or add style instructions by name.
    style_prompts: dict[str, str] = field(default_factory=dict)


_SECTIONS = {
    "hotkeys": HotkeyConfig,
    "audio": AudioConfig,
    "transcription": TranscriptionConfig,
    "cleanup": CleanupConfig,
    "output": OutputConfig,
    "history": HistoryConfig,
    "ui": UIConfig,
}


def _build_section(cls: type, name: str, values: dict[str, Any]) -> Any:
    known = {f.name: f for f in dataclasses.fields(cls)}
    kwargs = {}
    for key, value in values.items():
        if key not in known:
            log.warning("Ignoring unknown setting [%s] %s", name, key)
            continue
        default = getattr(cls(), key)
        if isinstance(default, float) and isinstance(value, int):
            value = float(value)
        if type(default) is not type(value):
            raise ValueError(
                f"[{name}] {key} should be {type(default).__name__}, got {value!r}"
            )
        kwargs[key] = value
    return cls(**kwargs)


def from_dict(data: dict[str, Any]) -> Config:
    cfg = Config()
    for name, cls in _SECTIONS.items():
        if name in data:
            setattr(cfg, name, _build_section(cls, name, data[name]))
    cfg.dictionary = [str(w) for w in data.get("dictionary", {}).get("words", [])]
    cfg.replacements = {str(k): str(v) for k, v in data.get("replacements", {}).items()}
    cfg.snippets = {str(k): str(v) for k, v in data.get("snippets", {}).items()}
    cfg.style_prompts = {str(k): str(v) for k, v in data.get("style_prompts", {}).items()}
    for rule in data.get("styles", []):
        match = rule.get("match", [])
        if isinstance(match, str):
            match = [match]
        cfg.styles.append(StyleRule(match=[str(m) for m in match], style=str(rule["style"])))
    unknown = set(data) - set(_SECTIONS) - {
        "dictionary", "replacements", "snippets", "styles", "style_prompts"
    }
    for name in sorted(unknown):
        log.warning("Ignoring unknown config section [%s]", name)
    return cfg


def load(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        return Config()
    with open(path, "rb") as f:
        return from_dict(tomllib.load(f))


def to_dict(cfg: Config) -> dict[str, Any]:
    data: dict[str, Any] = {name: dataclasses.asdict(getattr(cfg, name)) for name in _SECTIONS}
    data["dictionary"] = {"words": list(cfg.dictionary)}
    data["replacements"] = dict(cfg.replacements)
    data["snippets"] = dict(cfg.snippets)
    data["style_prompts"] = dict(cfg.style_prompts)
    if cfg.styles:
        data["styles"] = [{"match": list(r.match), "style": r.style} for r in cfg.styles]
    return data


def save(cfg: Config, path: Path | None = None) -> Path:
    """Write the config (used by the settings window; comments are not kept)."""
    import tomli_w

    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("# FreeFlow settings (written by the app)\n\n" + tomli_w.dumps(to_dict(cfg)),
                   encoding="utf-8")
    tmp.replace(path)
    return path


def default_toml() -> str:
    h = HotkeyConfig()
    return DEFAULT_TEMPLATE.format(
        dictate=h.dictate, command=h.command, paste_last=h.paste_last
    )


def write_default(path: Path | None = None, overwrite: bool = False) -> Path:
    path = path or config_path()
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(default_toml(), encoding="utf-8")
    return path


DEFAULT_TEMPLATE = """\
# FreeFlow configuration. Run `freeflow doctor` after editing.

[hotkeys]
# Key names: fn (macOS), ctrl, ctrl_l, ctrl_r, alt, alt_l, alt_r, shift, shift_r,
# cmd, cmd_r, space, esc, f1..f20, single characters, or vkNN for a raw key code.
# Combine with "+".
dictate = "{dictate}"        # hold to talk; double-tap for hands-free
command = "{command}"     # hold with text selected to edit it by voice
paste_last = "{paste_last}"  # re-paste the last result ("" disables)
cancel = "esc"
tap_max_seconds = 0.3
double_tap_window = 0.4
mouse_hold = true            # hold the left mouse button in a text box to dictate
mouse_hold_seconds = 0.4     # shorter presses are ordinary clicks
mouse_text_only = true       # only over text boxes (Windows)

[audio]
device = ""                 # see `freeflow devices`; empty = system default
sample_rate = 16000
min_seconds = 0.3
silence_threshold_db = -55.0
normalize = true            # boosts whispered / quiet speech
keep_mic_open = false       # true = no clipped first word, mic stays live
sounds = true
max_seconds = 600.0

[transcription]
# local  = faster-whisper on this machine (free, offline; pip install 'freeflow[local]')
# mlx    = Whisper on Apple Silicon GPU (free, offline; pip install 'freeflow[mlx]')
# groq   = Groq Whisper API, fastest (GROQ_API_KEY)
# openai = OpenAI transcription API (OPENAI_API_KEY)
# custom = any OpenAI-compatible /audio/transcriptions server (set base_url)
provider = "local"
model = ""                  # empty = provider default
language = "auto"
base_url = ""
api_key_env = ""
device = "auto"
compute_type = "auto"
timeout_seconds = 30.0

[cleanup]
# claude = Claude API (ANTHROPIC_API_KEY); ollama = local model; none = rules only
provider = "claude"
model = ""                  # empty = provider default
effort = "low"
command_effort = "medium"
ollama_url = "http://localhost:11434"
translate_to = ""           # e.g. "English" to always output English
timeout_seconds = 30.0

[output]
method = "paste"            # paste | type | clipboard
restore_clipboard = true
restore_delay_seconds = 0.4
trailing_space = true

[history]
enabled = true

[ui]
overlay = true              # floating recording bar (desktop app)
launch_at_login = false
onboarded = false

[dictionary]
# Names, jargon and product terms to spell exactly.
words = []

[replacements]
# "chat gpt" = "ChatGPT"

[snippets]
# Say the cue, get the text. Expansions never leave your machine.
# "my email" = "me@example.com"
# "my calendar link" = "https://cal.com/me"

# App-specific writing styles, checked before the built-in rules.
# Matched against the active app name and window title (case-insensitive).
# Built-in styles: default, casual, email, formal, code.
# [[styles]]
# match = ["linear", "jira"]
# style = "formal"

[style_prompts]
# casual = "Lowercase is fine. No period at the end of a single sentence."
"""
