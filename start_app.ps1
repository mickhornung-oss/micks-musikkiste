#!/usr/bin/env pwsh
<#
    .SYNOPSIS
    Micks Musikkiste V2 - Quick Start PowerShell Script
    
    .DESCRIPTION
    Startet die komplette AI-Musik-Studio-Anwendung
    
    .USAGE
    .\start_app.ps1
#>

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   Micks Musikkiste V2 - Local Start  ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

Write-Host "[1/3] Verzeichnis wechseln..." -ForegroundColor Cyan
Push-Location $PSScriptRoot

Write-Host "[2/3] Python-Umgebung pruefen..." -ForegroundColor Cyan
$PythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $PythonExe)) {
    Write-Host "[FEHLER] Venv nicht gefunden: $PythonExe" -ForegroundColor Red
    Write-Host "[HINWEIS] Bitte zuerst: python -m venv .venv && pip install -r backend\requirements.txt" -ForegroundColor Yellow
    Pop-Location
    exit 1
}

# Port-Vorpruefung: laeuft bereits eine Instanz?
$portBelegt = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($portBelegt) {
    Write-Host "[INFO] Port 8000 ist bereits belegt - Backend laeuft schon." -ForegroundColor Yellow
    Write-Host "[INFO] Oeffne Browser: http://localhost:8000" -ForegroundColor Cyan
    Start-Process "http://localhost:8000"
    Pop-Location
    exit 0
}

Write-Host "[3/3] Backend Server starten..." -ForegroundColor Cyan
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Server wird gestartet...           ║" -ForegroundColor Green
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  🌐 Frontend:                        ║" -ForegroundColor Green
Write-Host "║     http://localhost:8000             ║" -ForegroundColor Cyan
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  📖 API Dokumentation:               ║" -ForegroundColor Green
Write-Host "║     http://localhost:8000/docs        ║" -ForegroundColor Cyan
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  Hinweis: ENGINE_MODE=mock empfohlen  ║" -ForegroundColor Yellow
Write-Host "║  fuer lokalen V2-Flow                 ║" -ForegroundColor Yellow
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  ⏸️  Beenden: CTRL+C                 ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

& $PythonExe backend/run.py
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Host "" 
    Write-Host "[FEHLER] Backend mit Exit-Code $exitCode beendet." -ForegroundColor Red
    Write-Host "[HINWEIS] Pruefe Logs unter: $PSScriptRoot\logs\" -ForegroundColor Yellow
}

Pop-Location
