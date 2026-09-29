@echo off
setlocal
cd /d "%~dp0"
title Avatar Studio - Voice cloning add-on
echo.
echo  Optional add-on: offline voice cloning with Chatterbox (MIT licence).
echo  Needs about 5 GB of disk (PyTorch + voice models). Uses Python 3.11 or 3.10.
echo.

set "PY="
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (py -3.10 --version >nul 2>&1 && set "PY=py -3.10")
if not defined PY (
  echo  Python 3.11 was not found. Install it from https://www.python.org/downloads/release/python-3119/
  pause
  exit /b 1
)

if not exist "venv-voice\Scripts\python.exe" (
  %PY% -m venv venv-voice
  if errorlevel 1 (
    echo  Could not create the environment.
    pause
    exit /b 1
  )
)
"venv-voice\Scripts\python.exe" -m pip install --upgrade pip
"venv-voice\Scripts\python.exe" -m pip install chatterbox-tts soundfile
if errorlevel 1 (
  echo  Installation failed. Check your internet connection and try again.
  pause
  exit /b 1
)
echo.
echo  Downloading the voice models (one time, about 3 GB)...
"venv-voice\Scripts\python.exe" tools\voice_worker.py download
echo.
echo  Done. Restart Avatar Studio: "Cloned voice" is now enabled.
pause
