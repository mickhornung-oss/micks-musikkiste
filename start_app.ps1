#!/usr/bin/env pwsh
<#
    .SYNOPSIS
    Micks Musikkiste V1 - Quick Start PowerShell Script
    
    .DESCRIPTION
    Startet die komplette AI-Musik-Studio-Anwendung
    
    .USAGE
    .\start_app.ps1
#>

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  🎵 Micks Musikkiste V1 - Go Live!   ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

Write-Host "[1/4] Verzeichnis wechseln..." -ForegroundColor Cyan
Push-Location "C:\Users\mickh\Desktop\MicksMusikkiste"

Write-Host "[2/4] Virtual Environment aktivieren..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

Write-Host "[3/4] Backend Server starten..." -ForegroundColor Cyan
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ Server lädt...                    ║" -ForegroundColor Green
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  🌐 Frontend:                        ║" -ForegroundColor Green
Write-Host "║     http://localhost:8000             ║" -ForegroundColor Cyan
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  📖 API Dokumentation:               ║" -ForegroundColor Green
Write-Host "║     http://localhost:8000/docs        ║" -ForegroundColor Cyan
Write-Host "║                                       ║" -ForegroundColor Green
Write-Host "║  ⏸️  Beenden: CTRL+C                 ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

python backend/run.py

Pop-Location
