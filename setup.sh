#!/usr/bin/env bash
# Avatar Studio setup for Linux / macOS
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-$(command -v python3.11 || command -v python3.12 || command -v python3.10 || command -v python3)}
echo "Using $($PY --version)"
[ -x venv/bin/python ] || "$PY" -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m app.models_dl || echo "Some models failed - retry from Settings in the app."
echo "Setup complete. Run ./start.sh"
