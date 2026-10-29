"""Speech-to-text providers: local Whisper, Apple Silicon MLX, or HTTP APIs."""

from __future__ import annotations

import logging
import os
from typing import Protocol

from freeflow.audio import Recording
from freeflow.config import TranscriptionConfig

log = logging.getLogger(__name__)


class TranscriberError(RuntimeError):
    pass


class Transcriber(Protocol):
    name: str

    def transcribe(self, audio: Recording, prompt: str = "") -> str: ...


def vocabulary_prompt(words: list[str]) -> str:
    """Whisper-style prompt that biases recognition toward these spellings."""
    return ", ".join(words[:100]) + "." if words else ""


def _language(cfg: TranscriptionConfig) -> str | None:
    lang = cfg.language.strip().lower()
    return None if lang in ("", "auto") else lang


class LocalWhisper:
    """faster-whisper (CTranslate2). Runs on CPU or NVIDIA GPU, fully offline."""

    name = "local"
    DEFAULT_MODEL = "small"

    def __init__(self, cfg: TranscriptionConfig):
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise TranscriberError(
                "faster-whisper is not installed. Run: pip install 'freeflow[local]' "
                "or choose another [transcription] provider."
            ) from e
        device = cfg.device
        if device == "auto":
            device = "cuda" if _cuda_available() else "cpu"
        compute = cfg.compute_type
        if compute == "auto":
            compute = "float16" if device == "cuda" else "int8"
        self.model_name = cfg.model or self.DEFAULT_MODEL
        log.info("Loading Whisper model %s on %s (%s)...", self.model_name, device, compute)
        self.model = WhisperModel(self.model_name, device=device, compute_type=compute)
        self.language = _language(cfg)

    def transcribe(self, audio: Recording, prompt: str = "") -> str:
        segments, _info = self.model.transcribe(
            audio.samples,
            language=self.language,
            initial_prompt=prompt or None,
            vad_filter=True,
            beam_size=5,
            condition_on_previous_text=False,
        )
        return " ".join(s.text.strip() for s in segments).strip()


def _cuda_available() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


class MLXWhisper:
    """mlx-whisper on the Apple Silicon GPU, fully offline."""

    name = "mlx"
    DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"

    def __init__(self, cfg: TranscriptionConfig):
        try:
            import mlx_whisper
        except ImportError as e:
            raise TranscriberError(
                "mlx-whisper is not installed. Run: pip install 'freeflow[mlx]'"
            ) from e
        self._mlx_whisper = mlx_whisper
        self.model_name = cfg.model or self.DEFAULT_MODEL
        self.language = _language(cfg)

    def transcribe(self, audio: Recording, prompt: str = "") -> str:
        result = self._mlx_whisper.transcribe(
            audio.samples,
            path_or_hf_repo=self.model_name,
            initial_prompt=prompt or None,
            language=self.language,
            condition_on_previous_text=False,
        )
        return str(result.get("text", "")).strip()


class HTTPTranscriber:
    """Any OpenAI-compatible POST /audio/transcriptions endpoint."""

    PRESETS = {
        "groq": ("https://api.groq.com/openai/v1", "whisper-large-v3-turbo", "GROQ_API_KEY"),
        "openai": ("https://api.openai.com/v1", "gpt-4o-transcribe", "OPENAI_API_KEY"),
        "custom": ("", "whisper-1", ""),
    }

    def __init__(self, cfg: TranscriptionConfig):
        import requests

        base_url, model, key_env = self.PRESETS[cfg.provider]
        self.name = cfg.provider
        self.base_url = (cfg.base_url or base_url).rstrip("/")
        if not self.base_url:
            raise TranscriberError("[transcription] base_url is required for provider 'custom'")
        self.model_name = cfg.model or model
        key_env = cfg.api_key_env or key_env
        self.api_key = os.environ.get(key_env, "") if key_env else ""
        if key_env and not self.api_key:
            raise TranscriberError(f"Set the {key_env} environment variable for {self.name}")
        self.language = _language(cfg)
        self.timeout = cfg.timeout_seconds
        self.session = requests.Session()

    def transcribe(self, audio: Recording, prompt: str = "") -> str:
        import requests

        data = {"model": self.model_name, "response_format": "json", "temperature": "0"}
        if prompt:
            data["prompt"] = prompt
        if self.language:
            data["language"] = self.language
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            resp = self.session.post(
                f"{self.base_url}/audio/transcriptions",
                headers=headers,
                data=data,
                files={"file": ("audio.wav", audio.to_wav(), "audio/wav")},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise TranscriberError(f"{self.name} request failed: {e}") from e
        if resp.status_code != 200:
            raise TranscriberError(f"{self.name} returned {resp.status_code}: {resp.text[:300]}")
        return str(resp.json().get("text", "")).strip()


def create(cfg: TranscriptionConfig) -> Transcriber:
    if cfg.provider == "local":
        return LocalWhisper(cfg)
    if cfg.provider == "mlx":
        return MLXWhisper(cfg)
    if cfg.provider in HTTPTranscriber.PRESETS:
        return HTTPTranscriber(cfg)
    raise TranscriberError(f"Unknown transcription provider: {cfg.provider!r}")
