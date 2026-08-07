@echo off
cd /d "%~dp0"
echo AtlasFind katalog paneli baslatiliyor...
echo Tarayicinizda canli kontrol paneli acilacak.
echo Isci kaldigi yerden devam eder ve adaylari otomatik yayinlamaz.
echo Durdur dugmesi masaustune JSON, SQLite ve ZIP paketi hazirlar.
where python >nul 2>nul
if errorlevel 1 (
  echo Python bulunamadi. Once Python 3.11 veya daha yenisini kurun.
  pause
  exit /b 1
)
python -c "import flask, PIL" >nul 2>nul
if errorlevel 1 (
  echo Gerekli kutuphaneler eksik. Bir kez su komutu calistirin:
  echo python -m pip install -r requirements.txt
  pause
  exit /b 1
)
python scripts\atlas_catalog_dashboard.py --start-worker
echo.
echo Calisma tamamlandi. Pencereyi kapatmak icin bir tusa basin.
pause >nul
