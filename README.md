# Micks Musikkiste

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-09a031.svg)](https://fastapi.tiangolo.com/)

Lokales AI-Musikstudio für Techno und Hip-Hop mit konsolidiertem FastAPI-Backend, PostgreSQL für Jobs und Projekte, statischem Frontend und lokalen Audio-/Export-Dateien unter `data/`.

## Architektur

- Backend: FastAPI + SQLAlchemy Async + PostgreSQL
- Frontend: statische HTML/CSS/JS-App, ausgeliefert direkt vom Backend
- Persistenz: PostgreSQL für Jobs, Projekte und Export-Metadaten
- Dateien: lokale Outputs unter `data/outputs`, Exporte unter `data/exports`
- Logging: strukturierte Konsole plus lokale Logdateien unter `logs/`
- Modi: `mock`, `ace`, `real`

## ⚡ Quick Start

```powershell
# 1. Dependencies installieren
pip install -r backend/requirements.txt

# 2. Datenbank initialisieren (beim ersten Mal)
python backend/scripts/migrate.py

# 3. App starten
python backend/run.py
# oder: start.bat (Windows)
```

✅ **App live unter:**
- 🎵 UI: http://localhost:8000
- 📚 API-Docs: http://localhost:8000/docs
- 🔍 Diagnostics: http://localhost:8000/api/diagnostics
- 💓 Health-Check: http://localhost:8000/health

## Datenbank

Standardmäßig erwartet das Projekt eine lokale PostgreSQL-Instanz.

```env
DATABASE_URL=postgresql+asyncpg://postgres:Passwort@localhost:5432/postgres
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
LOG_LEVEL=info
DEBUG=false
```

Setup:

```powershell
pip install -r backend/requirements.txt
python backend/scripts/migrate.py
python backend/scripts/import_projects.py
```

## Mock / ACE / ComfyUI

- `ENGINE_MODE=mock`
  Empfohlener Standard für lokale Entwicklung, Smokes und E2E.
- `ENGINE_MODE=ace`
  Erwartet eine laufende lokale ComfyUI-Instanz und einen gültigen ACE-Workflow.
- `ENGINE_MODE=real`
  Nutzt den vorhandenen Real-Engine-Pfad; nur sinnvoll, wenn die lokale Runtime wirklich vorhanden ist.

Beispiel aus `.env.example`:

```env
ENGINE_MODE=mock
ENGINE_TYPE=mock
ENGINE_MOCK_DELAY=2
ENGINE_TIMEOUT=180
ACE_STEP_COMMAND=python ../scripts/ace_comfy_wrapper.py --workflow "C:/path/to/workflow.json" --comfy-url http://127.0.0.1:8188
```

Wichtige Grenze:

- Wenn ComfyUI lokal nicht läuft, bleibt der ACE-Pfad absichtlich bei sauberer Diagnose und wird nicht künstlich hochgezogen.
- Der Fehlerpfad liefert dann eine klare lokale Meldung statt eines rohen Python-Tracebacks.

## Diagnostics / Logs

- `GET /health`
  Kurzstatus für API, Engine und Zähler.
- `GET /api/diagnostics`
  Detaillierter Laufzeitstatus für Datenbank, Engine-Readiness, Jobs, Storage und Logs.
- Response-Header:
  - `X-Request-ID`
  - `X-Process-Time-Ms`
- Logdateien:
  - `logs/app.log`
  - `logs/error.log`

## Tests / E2E

Backend-Tests:

```powershell
.\.venv\Scripts\python -m pytest backend/tests -q
```

Browsernahe E2E-Smokes:

```powershell
cd e2e
npm install
npx playwright install chromium
npm test
```

Die E2E-Suite startet das Backend isoliert im `mock`-Modus auf `http://127.0.0.1:8011`.

Aktuell abgesichert:

- App-Start
- Statusseite
- Mock-Track erzeugen
- Ergebnis anzeigen
- Projekt speichern
- Export aus der Ergebnisansicht
- Projektliste prüfen
- Projektkarten-Export als UI-Schnellaktion

## Bekannte Restgrenzen

- ACE/ComfyUI ist weiterhin eine echte externe Laufzeitabhängigkeit.
- Der Projektkarten-Export ist als One-Click-Schnellaktion ausgelegt und nutzt automatisch einen sauberen Dateinamen aus dem Projektnamen.
- Außerhalb des aktiven Kernpfads können noch kleinere Alttexte oder Stilunterschiede bestehen, aber keine bekannte zentrale Laufpfad-Baustelle.

## Sinnvoller Nächster Ausbaupfad

- ACE nur dann kontrolliert end-to-end absichern, wenn ComfyUI lokal real läuft.
- Danach optional gezielte Produktverbesserungen statt weiterer Grundumbauten, zum Beispiel echte Variationen, feinere Projektverwaltung oder zusätzliche Engine-spezifische Smokes.
