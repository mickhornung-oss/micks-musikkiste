# Micks Musikkiste V2 - Architektur

## Zielbild

Micks Musikkiste V2 ist ein lokales Musikstudio mit zwei Hauptablaeufen:
- Beat erstellen
- Full Track erstellen

Die App besteht aus einem statischen Frontend und einem FastAPI-Backend mit Job-Queue.

## Komponenten

### Frontend

- Pfad: `frontend/`
- Technologie: HTML/CSS/Vanilla JavaScript
- Seiten: Dashboard, Beat, Track, Result, Projects, Status
- Kommunikation: REST ueber `/api/v2/*`

### Backend

- Pfad: `backend/app/`
- Technologie: FastAPI, SQLAlchemy Async
- Verantwortung:
  - V2 Request-Validierung
  - Job-Erstellung und Statusabfrage
  - Projekt speichern/listen
  - Export aus Projekten

### Persistenz

- Primar ueber Datenbanktabellen fuer Jobs/Projekte
- Dateibasierte Artefakte:
  - `data/outputs/` generierte Audios
  - `data/exports/` exportierte Audios

### Queue Worker

- Worker verarbeitet gequeue-te Jobs asynchron
- Statuspfad: queued -> running/claimed -> completed/failed/cancelled
- Heartbeat und Recovery-Mechanismen sind integriert

## V2 API-Schnittstellen

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

Projekt-Export:
- `POST /api/projects/{project_id}/export`

## Feldlogik in V2

Track/Beat nutzen eine klare Semantik:
- `prompt`: primare Musikbeschreibung
- `negative_prompt`: Ausschluesse
- `text_idea` (nur Track): Themenidee, nicht als direkte Lyrics an Engine

Diese Trennung ist Teil der V2-Produktlogik und wird in den Endpunkten explizit umgesetzt.

## Engine-Ebene (ehrlicher Stand)

- `mock`:
  - fuer lokalen Flow nutzbar
  - erzeugt Test-Audio fuer E2E
- `ace`:
  - nur nutzbar bei funktionierender lokaler ComfyUI-Bridge und passendem Workflow
- `musicgen`:
  - Adapter vorhanden
  - derzeit nicht als voll produktionsbereit zu werten

## Observability

- `GET /health`
- `GET /api/diagnostics`
- Logausgaben in `logs/`
- Worker/Engine-Details ueber Status-Endpunkte

## Nicht-Ziele dieser Version

- Keine Aussage "alle Engines voll produktionsbereit"
- Keine DAW-Features wie Multi-Track-Timeline oder MIDI-Editing
- Kein Cloud-Zwang im lokalen Basisbetrieb
