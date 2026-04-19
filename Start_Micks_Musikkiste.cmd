@echo off
setlocal

set "PROJECT_ROOT=C:\Users\mickh\Desktop\MicksMusikkiste"
set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "BACKEND_RUN=%PROJECT_ROOT%\backend\run.py"
set "BACKEND_URL=http://127.0.0.1:8000"
set "BACKEND_HEALTH=http://127.0.0.1:8000/health"
set "LOG_FILE=%PROJECT_ROOT%\logs\backend_startup.log"
set "ERR_FILE=%PROJECT_ROOT%\logs\backend_startup_err.log"
set "OPEN_BROWSER_ON_START=1"

echo.
echo [Micks Musikkiste] Start wird vorbereitet...

call :is_port_listening 8000
if %errorlevel%==0 (
    echo [OK] Backend laeuft bereits auf Port 8000.
    call :wait_for_http %BACKEND_HEALTH% 10
    goto :open_browser
)

if not exist "%PYTHON_EXE%" (
    echo [FEHLER] Python venv nicht gefunden: %PYTHON_EXE%
    echo [HINWEIS] Bitte zuerst: python -m venv .venv und pip install -r backend\requirements.txt
    pause
    exit /b 2
)

if not exist "%BACKEND_RUN%" (
    echo [FEHLER] Backend-Startdatei nicht gefunden: %BACKEND_RUN%
    pause
    exit /b 3
)

if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

echo [START] Starte Backend (Logs: %LOG_FILE%)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'backend\run.py' -WorkingDirectory '%PROJECT_ROOT%' -RedirectStandardOutput '%LOG_FILE%' -RedirectStandardError '%ERR_FILE%' -WindowStyle Hidden"

echo [INFO] Warte auf Backend (bis zu 60 Sek.)...
call :wait_for_port 8000 60
if errorlevel 1 (
    echo.
    echo [FEHLER] Backend wurde nicht rechtzeitig erreichbar.
    echo [HINWEIS] Startup-Log:  %LOG_FILE%
    echo [HINWEIS] Fehler-Log:   %ERR_FILE%
    echo.
    if exist "%ERR_FILE%" (
        echo --- Fehler-Ausgabe ---
        type "%ERR_FILE%"
        echo --- Ende ---
    )
    pause
    exit /b 4
)

echo [INFO] Port 8000 erreichbar. Pruefe HTTP-Gesundheit...
call :wait_for_http %BACKEND_HEALTH% 15
if errorlevel 1 (
    echo [WARNUNG] HTTP-Healthcheck nicht bestaetigt - oeffne App trotzdem.
)

:open_browser
if "%OPEN_BROWSER_ON_START%"=="1" (
    echo [OK] Oeffne Browser: %BACKEND_URL%
    start "" "%BACKEND_URL%"
)

echo [FERTIG] Backend laeuft. Logs: %LOG_FILE%
exit /b 0


:is_port_listening
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort %~1 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>&1
exit /b %errorlevel%

:wait_for_port
setlocal
set "PORT=%~1"
set "TRIES=%~2"
:wfp_loop
call :is_port_listening %PORT%
if %errorlevel%==0 (
    endlocal & exit /b 0
)
set /a TRIES-=1
if %TRIES% LEQ 0 (
    endlocal & exit /b 1
)
timeout /t 1 /nobreak >nul
goto wfp_loop

:wait_for_http
setlocal
set "HURL=%~1"
set "TRIES=%~2"
:wfh_loop
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri '%HURL%' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    endlocal & exit /b 0
)
set /a TRIES-=1
if %TRIES% LEQ 0 (
    endlocal & exit /b 1
)
timeout /t 1 /nobreak >nul
goto wfh_loop