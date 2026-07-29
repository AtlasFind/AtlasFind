@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1
.venv\Scripts\python.exe scripts\sync_ratings_v103_to_sqlite.py
if errorlevel 1 pause & exit /b 1
.venv\Scripts\python.exe scripts\validate_release_v103.py
if errorlevel 1 pause & exit /b 1
.venv\Scripts\python.exe app.py
pause
