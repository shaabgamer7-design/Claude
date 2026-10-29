"""API keys kept in the OS keychain (macOS Keychain, Windows Credential Manager).

Providers read keys from environment variables, so the desktop app copies the
stored keys into the environment at startup. If no keychain is available, keys
fall back to a file only the current user can read.
"""

from __future__ import annotations

import json
import logging
import os

from freeflow.config import app_dir

log = logging.getLogger(__name__)

SERVICE = "FreeFlow"

KEY_LABELS = {
    "ANTHROPIC_API_KEY": "Anthropic (Claude)",
    "GROQ_API_KEY": "Groq",
    "OPENAI_API_KEY": "OpenAI",
    "FREEFLOW_CUSTOM_STT_KEY": "Custom speech server",
}


def _fallback_path():
    return app_dir() / "keys.json"


def _read_fallback() -> dict[str, str]:
    try:
        return json.loads(_fallback_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_fallback(data: dict[str, str]) -> None:
    path = _fallback_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _keyring():
    if os.environ.get("FREEFLOW_NO_KEYCHAIN"):
        return None
    try:
        import keyring
        from keyring.backends import fail

        if isinstance(keyring.get_keyring(), fail.Keyring):
            return None
        return keyring
    except Exception:  # not installed, or no usable backend
        return None


def read(name: str) -> str:
    if (kr := _keyring()) is not None:
        try:
            if value := kr.get_password(SERVICE, name):
                return value
        except Exception as e:
            log.debug("keychain read failed for %s: %s", name, e)
    return _read_fallback().get(name, "")


def store(name: str, value: str) -> None:
    """Store a key (empty value deletes it) and update this process's environment."""
    value = value.strip()
    stored = False
    if (kr := _keyring()) is not None:
        try:
            if value:
                kr.set_password(SERVICE, name, value)
            else:
                try:
                    kr.delete_password(SERVICE, name)
                except Exception:
                    pass  # wasn't stored
            stored = True
        except Exception as e:
            log.warning("keychain unavailable, storing %s in a private file: %s", name, e)
    data = _read_fallback()
    if stored or not value:
        data.pop(name, None)
    else:
        data[name] = value
    if data or _fallback_path().exists():
        _write_fallback(data)
    if value:
        os.environ[name] = value
    else:
        os.environ.pop(name, None)


def load_into_environ() -> None:
    """Make stored keys visible to providers, without overriding the shell's."""
    for name in KEY_LABELS:
        if not os.environ.get(name) and (value := read(name)):
            os.environ[name] = value
