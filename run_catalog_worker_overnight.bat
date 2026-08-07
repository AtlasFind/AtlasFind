@echo off
cd /d "%~dp0"
echo AtlasFind katalog paneli baslatiliyor...
echo Tarayicinizda canli kontrol paneli acilacak.
echo Isci siz durdurana kadar calisir ve adaylari otomatik yayinlamaz.
python scripts\atlas_catalog_dashboard.py
echo.
echo Calisma tamamlandi. Pencereyi kapatmak icin bir tusa basin.
pause >nul
