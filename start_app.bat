@echo off
REM Micks Musikkiste - Quick Start Batch

title Micks Musikkiste V2 - WebUI

cls
echo.
echo ╔════════════════════════════════════════╗
echo ║   Micks Musikkiste V2 - Local Start   ║
echo ╚════════════════════════════════════════╝
echo.
echo [1/4] Verzeichnis wechseln...
cd /d "%~dp0"

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
echo ║  Hinweis: ENGINE_MODE=mock empfohlen   ║
echo ║  fuer lokalen V2-Flow                  ║
echo ║                                        ║
echo ║  Drücken Sie CTRL+C zum Beenden        ║
echo ╚════════════════════════════════════════╝
echo.

python backend/run.py

pause
