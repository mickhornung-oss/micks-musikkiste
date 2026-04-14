@echo off
REM Micks Musikkiste - Quick Start Batch

title Micks Musikkiste V1 - WebUI

cls
echo.
echo ╔════════════════════════════════════════╗
echo ║  🎵 Micks Musikkiste V1 - Go Live!    ║
echo ╚════════════════════════════════════════╝
echo.
echo [1/4] Verzeichnis wechseln...
cd /d C:\Users\mickh\Desktop\MicksMusikkiste

echo [2/4] Virtual Environment aktivieren...
call .venv\Scripts\Activate.bat

echo [3/4] Backend Server starten...
echo.
echo ╔════════════════════════════════════════╗
echo ║  Server lädt...                        ║
echo ║  Öffnen Sie den Browser und gehen sie zu:
echo ║  http://localhost:8000                 ║
echo ║                                        ║
echo ║  Swagger API-Dokumentation:            ║
echo ║  http://localhost:8000/docs            ║
echo ║                                        ║
echo ║  Drücken Sie CTRL+C zum Beenden        ║
echo ╚════════════════════════════════════════╝
echo.

python backend/run.py

pause
