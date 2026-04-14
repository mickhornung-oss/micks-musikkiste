@echo off
setlocal

set "PROJECT_ROOT=C:\Users\mickh\Desktop\MicksMusikkiste"
set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "BACKEND_RUN=%PROJECT_ROOT%\backend\run.py"
set "BACKEND_URL=http://127.0.0.1:8000"
set "OPEN_BROWSER_ON_START=1"

echo.
echo [Micks Musikkiste] Start wird vorbereitet...

call :is_port_listening 8000
if %errorlevel%==0 (
    echo [OK] Backend laeuft bereits auf Port 8000.
    set "BACKEND_STARTED=0"
) else (
    if not exist "%PYTHON_EXE%" (
        echo [FEHLER] Python aus der Venv nicht gefunden: "%PYTHON_EXE%"
        exit /b 2
    )

    if not exist "%BACKEND_RUN%" (
        echo [FEHLER] Backend-Startdatei nicht gefunden: "%BACKEND_RUN%"
        exit /b 3
    )

    echo [START] Starte Backend im Hintergrundfenster...
    start "Micks Musikkiste Backend" /MIN /D "%PROJECT_ROOT%" "%PYTHON_EXE%" "backend\run.py"
    set "BACKEND_STARTED=1"
)

echo [INFO] Warte auf Backend...
call :wait_for_port 8000 30
if errorlevel 1 (
    echo [FEHLER] Backend wurde nicht rechtzeitig erreichbar.
    echo [HINWEIS] Siehe App-Logs im Ordner: "%PROJECT_ROOT%\logs"
    exit /b 4
)

if "%BACKEND_STARTED%"=="1" (
    if "%OPEN_BROWSER_ON_START%"=="1" (
        echo [START] Oeffne Browser: %BACKEND_URL%
        start "" "%BACKEND_URL%"
    ) else (
        echo [INFO] Browser bleibt geschlossen. URL: %BACKEND_URL%
    )
) else (
    echo [INFO] Browser wird nicht erneut geoeffnet. URL: %BACKEND_URL%
)

echo [FERTIG] Starter abgeschlossen.
exit /b 0

:is_port_listening
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort %~1 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>&1
exit /b %errorlevel%

:wait_for_port
setlocal
set "PORT=%~1"
set "TRIES=%~2"
:wait_loop
call :is_port_listening %PORT%
if %errorlevel%==0 (
    endlocal & exit /b 0
)
set /a TRIES-=1
if %TRIES% LEQ 0 (
    endlocal & exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait_loop
