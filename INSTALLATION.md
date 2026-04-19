# Installation und Start (V2, Windows)

Diese Anleitung beschreibt den real getesteten lokalen Standardpfad.
Empfohlen fuer den Einstieg: `ENGINE_MODE=mock`.

## 1. In den Projektordner wechseln

```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste
```

## 2. Virtuelle Umgebung anlegen und aktivieren

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Erwartung: Prompt startet mit `(.venv)`.

## 3. Abhaengigkeiten installieren

```powershell
pip install -r backend\requirements.txt
```

## 4. Konfiguration anlegen

```powershell
copy backend\.env.example backend\.env
```

Fuer lokalen Start in `backend/.env` mindestens setzen/pruefen:

```env
ENGINE_MODE=mock
DATABASE_URL=sqlite+aiosqlite:///./data/micks_musikkiste.db
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

## 5. Datenbank-Migration ausfuehren

```powershell
python backend\scripts\migrate.py
```

## 6. Server starten

```powershell
python backend\run.py
```

Erwartung im Terminal:
- "Micks Musikkiste backend is starting..."
- URL-Hinweise fuer Frontend und Docs
- Uvicorn auf `http://127.0.0.1:8000`

## 7. Im Browser pruefen

- UI: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## Startskripte (optional)

- `start.bat`
- `start_app.bat`
- `start_app.ps1`
- `start.sh`
- `Start_Micks_Musikkiste.cmd`

Alle starten denselben Backend-Entry-Point: `python backend/run.py`.

## Engine-Hinweise (wichtig)

- Mock:
	- sofort nutzbar
	- fuer lokalen Funktionstest und E2E empfohlen
- ACE:
	- nur nutzbar, wenn ComfyUI/Workflow lokal erreichbar sind
	- ohne laufende ComfyUI ist `ready=false`
- MusicGen:
	- noch nicht voll implementiert/verfuegbar

## Troubleshooting

"Python nicht gefunden"
```powershell
python --version
```

"Port 8000 bereits belegt"
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

"Module fehlen"
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

"Health nicht ok"
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/diagnostics
```
