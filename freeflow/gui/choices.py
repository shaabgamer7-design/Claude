"""Option lists shown in the settings window and setup wizard: (value, label)."""

from __future__ import annotations

import importlib.util

from freeflow.config import IS_MAC

if IS_MAC:
    DICTATE_KEYS = [
        ("fn", "fn (Globe) key"),
        ("alt_r", "Right Option"),
        ("cmd_r", "Right Command"),
        ("ctrl+alt", "Control + Option"),
    ]
    COMMAND_KEYS = [
        ("fn+ctrl", "fn + Control"),
        ("alt_r+shift", "Right Option + Shift"),
        ("cmd_r+shift", "Right Command + Shift"),
        ("", "Off"),
    ]
    PASTE_LAST_KEYS = [("ctrl+cmd+v", "Control + Command + V"), ("", "Off")]
else:
    DICTATE_KEYS = [
        ("ctrl_r", "Right Ctrl"),
        ("ctrl+cmd", "Ctrl + Windows"),
        ("alt_r", "Right Alt"),
        ("f9", "F9"),
    ]
    COMMAND_KEYS = [
        ("ctrl_r+shift", "Right Ctrl + Shift"),
        ("ctrl+cmd+alt", "Ctrl + Windows + Alt"),
        ("alt_r+shift", "Right Alt + Shift"),
        ("", "Off"),
    ]
    PASTE_LAST_KEYS = [("alt+shift+z", "Alt + Shift + Z"), ("", "Off")]


def speech_providers() -> list[tuple[str, str]]:
    out = [("local", "On this computer (free, private)")]
    if IS_MAC and importlib.util.find_spec("mlx_whisper") is not None:
        out.append(("mlx", "On this Mac's GPU (free, private, fast)"))
    out += [
        ("groq", "Groq cloud (fastest, very cheap)"),
        ("openai", "OpenAI cloud"),
        ("custom", "My own server (OpenAI-compatible)"),
    ]
    return out


SPEECH_MODELS = {
    "local": [
        ("base", "Base - fastest, ~150 MB"),
        ("small", "Small - balanced, ~500 MB"),
        ("large-v3-turbo", "Large v3 Turbo - most accurate, ~1.6 GB"),
        ("distil-large-v3", "Distil Large v3 - English only, fast and accurate"),
        ("medium", "Medium - ~1.5 GB"),
    ],
    "mlx": [
        ("mlx-community/whisper-large-v3-turbo", "Large v3 Turbo"),
        ("mlx-community/whisper-small-mlx", "Small"),
    ],
    "groq": [
        ("whisper-large-v3-turbo", "Whisper Large v3 Turbo"),
        ("whisper-large-v3", "Whisper Large v3"),
    ],
    "openai": [
        ("gpt-4o-transcribe", "GPT-4o Transcribe"),
        ("gpt-4o-mini-transcribe", "GPT-4o mini Transcribe"),
        ("whisper-1", "Whisper"),
    ],
    "custom": [("whisper-1", "whisper-1")],
}

def default_speech_model(provider: str) -> str:
    """The model a provider uses when the config leaves `model` empty."""
    from freeflow.transcribe import HTTPTranscriber, LocalWhisper, MLXWhisper

    if provider == "local":
        return LocalWhisper.DEFAULT_MODEL
    if provider == "mlx":
        return MLXWhisper.DEFAULT_MODEL
    return HTTPTranscriber.PRESETS.get(provider, ("", "", ""))[1]


SPEECH_KEY = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY", "custom": "FREEFLOW_CUSTOM_STT_KEY"}
KEY_LINKS = {
    "ANTHROPIC_API_KEY": "https://console.anthropic.com/settings/keys",
    "GROQ_API_KEY": "https://console.groq.com/keys",
    "OPENAI_API_KEY": "https://platform.openai.com/api-keys",
}

CLEANUP_PROVIDERS = [
    ("claude", "Claude (best quality)"),
    ("ollama", "Ollama on this computer (free, private)"),
    ("none", "Off - basic cleanup only"),
]

# Costs: ~750 input + ~200 output tokens for a short dictation at list prices.
CLAUDE_MODELS = [
    ("claude-opus-5-5", "Claude Opus 5.5 - best quality (about 0.7¢ per dictation)"),
    ("claude-sonnet-5-5", "Claude Sonnet 5.5 - balanced (about 0.35¢)"),
    ("claude-haiku-5-5", "Claude Haiku 5.5 - fastest (about 0.02¢)"),
]

EFFORTS = [("low", "Low - fastest"), ("medium", "Medium"), ("high", "High - most careful")]

LANGUAGES = [
    ("auto", "Detect automatically"),
    ("en", "English"), ("ar", "Arabic"), ("bn", "Bengali"), ("zh", "Chinese"),
    ("nl", "Dutch"), ("fr", "French"), ("de", "German"), ("hi", "Hindi"),
    ("id", "Indonesian"), ("it", "Italian"), ("ja", "Japanese"), ("ko", "Korean"),
    ("fa", "Persian"), ("pl", "Polish"), ("pt", "Portuguese"), ("ru", "Russian"),
    ("es", "Spanish"), ("sv", "Swedish"), ("tl", "Tagalog"), ("tr", "Turkish"),
    ("uk", "Ukrainian"), ("ur", "Urdu"), ("vi", "Vietnamese"),
]

OUTPUT_LANGUAGES = [("", "Same as spoken")] + [
    (label, label) for value, label in LANGUAGES if value != "auto"
]

OUTPUT_METHODS = [
    ("paste", "Paste (fastest)"),
    ("type", "Type it out (for apps that block pasting)"),
    ("clipboard", "Copy to clipboard only"),
]

STYLES = [
    ("default", "Natural"),
    ("casual", "Casual (chat)"),
    ("email", "Email"),
    ("formal", "Formal (documents)"),
    ("code", "Code / technical"),
]


def label_for(choices: list[tuple[str, str]], value: str) -> str:
    return next((label for v, label in choices if v == value), value)
