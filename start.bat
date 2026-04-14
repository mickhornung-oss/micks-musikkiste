@echo off
REM Micks Musikkiste - Start Script (Windows)

echo.
echo =====================================
echo   Micks Musikkiste - Lokaler Start
echo =====================================
echo.

REM Check if venv exists
if not exist ".venv" (
    echo [!] Virtual Environment nicht gefunden
    echo [*] Erstelle .venv...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install requirements if needed
if not exist ".venv\Lib\site-packages\fastapi" (
    echo [*] Installiere Requirements...
    pip install -r backend\requirements.txt
)
if not exist ".venv\Lib\site-packages\sqlalchemy" (
    echo [*] Installiere DB-Requirements...
    pip install -r backend\requirements.txt
)

REM Start backend
echo.
echo [*] Starte Backend-Server...
echo [*] Frontend: http://localhost:8000
echo [*] API Docs: http://localhost:8000/docs
echo [*] Diagnostics: http://localhost:8000/api/diagnostics
echo [*] Logs: logs\app.log / logs\error.log
echo.

python backend\run.py
