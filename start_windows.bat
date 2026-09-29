@echo off
cd /d "%~dp0"
title Avatar Studio
if not exist "venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
"venv\Scripts\python.exe" -m app %*
pause
