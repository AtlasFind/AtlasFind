@echo off
setlocal
cd /d "%~dp0"

echo [AtlasFind] Proje klasoru: %CD%

if not exist ".venv\Scripts\python.exe" (
    echo [AtlasFind] Sanal ortam olusturuluyor...
    py -m venv .venv
    if errorlevel 1 goto :error
)

echo [AtlasFind] Bagimliliklar kontrol ediliyor...
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [AtlasFind] v1.0.2 dogrulamasi calistiriliyor...
call ".venv\Scripts\python.exe" scripts\validate_release_v102.py
if errorlevel 1 goto :error

echo [AtlasFind] Sunucu baslatiliyor: http://127.0.0.1:5000/tr/
call ".venv\Scripts\python.exe" app.py
goto :eof

:error
echo.
echo [AtlasFind] Islem basarisiz. Yukaridaki hata metnini kopyalayin.
pause
exit /b 1
