#!/usr/bin/env bash
# Optional: offline voice cloning (Chatterbox) in its own environment.
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-$(command -v python3.11 || command -v python3.10 || command -v python3)}
[ -x venv-voice/bin/python ] || "$PY" -m venv venv-voice
venv-voice/bin/python -m pip install --upgrade pip
venv-voice/bin/python -m pip install chatterbox-tts soundfile
venv-voice/bin/python tools/voice_worker.py download
echo "Done. Restart Avatar Studio."
