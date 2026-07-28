@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=py"
)

%PYTHON% scripts\validate_release_v102.py
if errorlevel 1 (
    echo.
    echo v1.0.2 dogrulamasi BASARISIZ.
    pause
    exit /b 1
)

echo.
echo v1.0.2 dogrulamasi BASARILI.
pause
