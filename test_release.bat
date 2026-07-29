@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe scripts\validate_release_v103.py
) else (
  py scripts\validate_release_v103.py
)
pause
