@echo off
setlocal
cd /d "%~dp0"
title Avatar Studio - Setup
echo.
echo  =====================================
echo    Avatar Studio - one-time setup
echo  =====================================
echo.

set "PY="
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (py -3.12 --version >nul 2>&1 && set "PY=py -3.12")
if not defined PY (py -3.10 --version >nul 2>&1 && set "PY=py -3.10")
if not defined PY (python --version >nul 2>&1 && set "PY=python")
if not defined PY (
  echo  Python was not found.
  echo  Install Python 3.11 from https://www.python.org/downloads/
  echo  IMPORTANT: tick "Add python.exe to PATH" in the installer, then run this file again.
  echo.
  pause
  exit /b 1
)
echo  Using: %PY%
%PY% --version

if not exist "venv\Scripts\python.exe" (
  echo.
  echo  [1/3] Creating a private Python environment...
  %PY% -m venv venv
  if errorlevel 1 (
    echo  Could not create the environment.
    pause
    exit /b 1
  )
)

echo.
echo  [2/3] Installing packages (a few minutes, about 250 MB)...
"venv\Scripts\python.exe" -m pip install --upgrade pip
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo  Package installation failed. Check your internet connection and run setup again.
  pause
  exit /b 1
)

echo.
echo  [3/3] Downloading the AI models (one time, about 480 MB)...
"venv\Scripts\python.exe" -m app.models_dl
if errorlevel 1 (
  echo.
  echo  The lip-sync model did not download. You can retry later from Settings in the app,
  echo  or download it by hand - see README.md, section "Manual model download".
)

echo.
echo  =====================================
echo    Setup complete!
echo    Double-click start_windows.bat to open Avatar Studio.
echo  =====================================
echo.
pause
