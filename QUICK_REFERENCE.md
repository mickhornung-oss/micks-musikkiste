# Micks Musikkiste V2 - Quick Reference

## 1-Minute Start

```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste
.\.venv\Scripts\Activate.ps1
python backend\run.py
```

Danach:
- UI: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs

## V2 Kernlogik

- Zwei Hauptmodi:
  - Beat erstellen
  - Full Track erstellen
- Feldbedeutung:
  - `prompt`: musikalische Hauptanweisung
  - `negative_prompt`: Ausschluesse
  - `text_idea` (nur Track): Themenidee, keine direkte Lyrics-Uebergabe

## Wichtige Endpunkte

- `POST /api/v2/beat/generate`
- `POST /api/v2/track/generate`
- `GET /api/v2/jobs/{job_id}`
- `GET /api/v2/projects`
- `POST /api/v2/projects`
- `GET /api/v2/engine/status`

## Engine-Realitaet

- `mock`: laeuft lokal direkt
- `ace`: nur bei funktionierender lokaler ComfyUI-Bridge
- `musicgen`: vorbereitet, derzeit nicht voll implementiert/verfuegbar

## Wichtige Ordner

- `backend/` FastAPI + Queue + Services
- `frontend/` SPA
- `data/outputs/` generierte Audios
- `data/exports/` exportierte Audios
- `data/projects/` Projektdateien
- `docs/` technische Doku

## Schnelltests

```powershell
.\.venv\Scripts\python -m pytest backend\tests -q
```

## Haeufige Probleme

Server startet nicht:
- Port pruefen: `Get-NetTCPConnection -LocalPort 8000 -State Listen`
- Health pruefen: `Invoke-RestMethod http://127.0.0.1:8000/health`

Falscher Engine-Modus:
- `backend/.env` pruefen: `ENGINE_MODE=mock`

## Release-Hinweis

Dieses Projekt ist V2-faehig fuer lokale End-to-End-Flows im Mock-Modus.
ACE und MusicGen sind bewusst nicht als "voll produktionsbereit" dargestellt.
