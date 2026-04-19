# Micks Musikkiste V2

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-09a031.svg)](https://fastapi.tiangolo.com/)

Lokales Musikstudio mit FastAPI-Backend und V2-Frontend fuer zwei Kernablaeufe:
- Beat erstellen
- Full Track erstellen

Wichtiger Release-Hinweis: Dieses Repo ist auf ehrliche lokale Nutzung ausgelegt. Es gibt aktuell keine Aussage "alle Engines produktionsbereit".

## Was V2 konkret ist

V2 trennt die Produktlogik klar von alten V1-Mustern:
- V2-Endpunkte laufen unter `/api/v2/*`
- Prompt ist das primaere Steuerfeld fuer Musik-Generierung
- `negative_prompt` wird als Ausschlussliste verarbeitet
- `text_idea` wird nur als Themen-Metadaten genutzt und nicht als direkte Lyrics uebergeben
- Ergebnisse landen als Audio-Dateien in `data/outputs` und koennen als Projekte gespeichert/exportiert werden

## Engine-Status (ehrlich)

- `mock`: nutzbar, lokale Testtoene fuer durchgehende Flows
- `ace`: nur nutzbar, wenn lokale Voraussetzungen vorhanden sind (ComfyUI + Workflow + Erreichbarkeit)
- `musicgen`: Adapter vorbereitet, aktuell nicht voll implementiert/verfuegbar

Wenn du sofort loslegen willst, nutze `ENGINE_MODE=mock`.

## Quick Start (Windows PowerShell)

```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
python backend\scripts\migrate.py
python backend\run.py
```

Danach:
- UI: `http://127.0.0.1:8000`
- API Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- Diagnostics: `http://127.0.0.1:8000/api/diagnostics`

## Voraussetzungen

- Python 3.9+
- Virtuelle Umgebung (`.venv`)
- Fuer Standardbetrieb: keine externe Engine noetig (`mock`)
- Datenbank:
	- lokal einfach: SQLite
	- produktionsnaeher: PostgreSQL

## Konfiguration

Die App liest Umgebungsvariablen aus `backend/.env`.

Minimal sinnvoll fuer lokalen V2-Start:

```env
ENGINE_MODE=mock
DATABASE_URL=sqlite+aiosqlite:///./data/micks_musikkiste.db
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
LOG_LEVEL=info
```

Hinweis:
- `ENGINE_TYPE` ist nur Legacy-Fallback. Verwende `ENGINE_MODE`.

## V2 API Ueberblick

Kernendpunkte:
- `POST /api/v2/beat/generate`
- `POST /api/v2/track/generate`
- `GET /api/v2/jobs/{job_id}`
- `GET /api/v2/engine/status`
- `GET /api/v2/genres`
- `GET /api/v2/profiles`
- `GET /api/v2/config`
- `POST /api/v2/projects`
- `GET /api/v2/projects`

Export bleibt ueber den bestehenden Projekt-Exportpfad verfuegbar:
- `POST /api/projects/{project_id}/export`

## Architektur in kurz

- Frontend: statisches SPA (`frontend/index.html`, `frontend/js/app.js`)
- Backend: FastAPI (`backend/app/main.py`)
- Queue/Jobs: DB-basiert mit Worker
- Storage:
	- generierte Audios: `data/outputs`
	- exportierte Audios: `data/exports`
	- Projektdaten: `data/projects`

## Tests

```powershell
# Backend Tests
.\.venv\Scripts\python -m pytest backend\tests -v

# Browser Smoke (optional)
cd e2e
npm install
npx playwright install chromium
npm test
```

## Bekannte Grenzen

- V2 ist funktional fuer lokale Flows, aber nicht als "alle Engines ready" zu verstehen.
- `ace` ist von externer lokaler Runtime abhaengig.
- `musicgen` ist noch kein vollstaendiger produktiver Pfad.
- E2E Browser-Tests laufen sinnvoll mit `ENGINE_MODE=mock`.

## Weitere Doku

- Installation: `INSTALLATION.md`
- Quick Reference: `QUICK_REFERENCE.md`
- Architektur: `docs/ARCHITECTURE.md`
- Release Checklist: `docs/RELEASE_CHECKLIST.md`
