@echo off
cd /d "%~dp0"
echo AtlasFind gece katalog iscisi baslatiliyor...
echo Adaylar otomatik yayinlanmaz; data\research kuyruğuna kaydedilir.
python scripts\atlas_catalog_worker.py --hours 8 --max-candidates 300 --min-stars 500
echo.
echo Calisma tamamlandi. Pencereyi kapatmak icin bir tusa basin.
pause >nul
