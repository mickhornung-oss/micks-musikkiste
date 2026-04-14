# 🏗️ Micks Musikkiste - Architektur Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (Browser)                        │
│  HTML/CSS/JS SPA (Dark Theme, Lila/Grün)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
┌────────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Python)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Routes Layer (API Endpoints)                         │   │
│  │  - /api/track/generate                              │   │
│  │  - /api/beat/generate                               │   │
│  │  - /api/projects                                    │   │
│  │  - /api/jobs/{id}                                   │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │ Services Layer (Business Logic)                      │   │
│  │  - MusicGenerationService                           │   │
│  │  - ProjectService                                   │   │
│  │  - Job Management                                   │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │ Engine Adapter Layer (Austauschbar!)                │   │
│  │  - MockMusicEngine (V1)                             │   │
│  │  - [ComfyUI Engine - später]                        │   │
│  │  - [ACE-Steps Engine - später]                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │ File I/O
┌────────────────────────▼────────────────────────────────────┐
│                   Local Storage                             │
│  - data/projects/     (Projekte als JSON)                   │
│  - data/outputs/      (Generierte Audios)                   │
│  - data/exports/      (Exportierte Dateien)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (HTML/CSS/JS)

**Datei:** `frontend/`

#### HTML (`index.html`)
- Single Page Application (SPA)
- Navigation zwischen Seiten
- Formulare für Track/Beat-Erstellung
- Audio-Player
- Projektliste

#### CSS (`styles/main.css`)
- **Farben:** Lila (#8B5CF6) + Grün (#10B981)
- **Theme:** Dunkel (Hintergrund: #0F172A)
- **Design:** Modern, clean, studio-like
- Responsive Grid-Layout
- Smooth Transitions & Animations

#### JavaScript (`js/app.js`)
- **SPA Logic:** Navigation zwischen Seiten
- **API Communication:** Fetch-basierte REST-Calls
- **State Management:** currentJob, currentJobId
- **Job Monitoring:** Polling (500ms) für Job-Status
- **Error Handling:** Visual Alerts & Messages

---

### 2. Backend (FastAPI)

#### Routes (`app/routes/__init__.py`)

```
GET    /                       → Root Info
GET    /health                 → System Status
GET    /api                    → API Info

POST   /api/track/generate     → Track-Generierung starten
POST   /api/beat/generate      → Beat-Generierung starten

GET    /api/jobs               → Alle Jobs
GET    /api/jobs/{job_id}      → Job-Status abfragen

GET    /api/projects           → Alle Projekte auflisten
POST   /api/projects           → Projekt speichern
GET    /api/projects/{id}      → Ein Projekt laden
DELETE /api/projects/{id}      → Projekt löschen

POST   /api/export/{job_id}    → Audio exportieren
GET    /audio/{filename}       → Audio streamen
```

#### Models (`app/models/__init__.py`)

```python
TrackGenerationRequest
  └─ title, genre, mood, language, duration
    └─ lyrics, negative_prompts
    └─ energy, tempo, creativity, catchiness, vocal_strength

BeatGenerationRequest
  └─ title, genre, mood, duration
    └─ tempo, heaviness, melody_amount, energy

GenerationJob
  └─ id, type, status, progress, result_file, error, metadata

Project
  └─ id, name, type, genre, mood, duration
    └─ created_at, updated_at, data_file, output_file
    └─ parameters, metadata

SystemStatus
  └─ status, engine_type, version, data_dir_ok
    └─ total_projects, total_outputs
```

#### Services (`app/services/`)

**MusicGenerationService** (`__init__.py`)
- Verwaltet aktive Generierungs-Jobs
- Abstrahiert Engine-Calls
- Bietet API: `generate_track()`, `generate_beat()`, `get_job_status()`
- Async Job-Execution

**ProjectService** (`projects.py`)
- Lokale JSON-basierte Projekte
- CRUD-Operationen
- Sortierung nach Erstellungszeit

**MusicEngine** (Adapter Pattern)
```python
MockMusicEngine  (V1)
  ├─ generate_track_audio()
  ├─ generate_beat_audio()
  └─ vary_audio()

# Später:
ComfyUIEngine
ACEStepsEngine
```

---

## Data Flow

### Track Generation Flow

```
1. Frontend: User füllt Track-Form
   └─ Klick "Track generieren"

2. Frontend: POST /api/track/generate
   └─ Request mit allen Parametern

3. Backend: Route /api/track/generate
   └─ Validiere mit Pydantic

4. Backend: MusicGenerationService.generate_track()
   └─ Erstelle Job-Objekt
   └─ Starte async Task
   └─ Returne job_id

5. Frontend: Erhalte job_id
   └─ Starte Polling-Loop (500ms)

6. Backend: Async Task läuft
   └─ MusicEngine.generate_track_audio()
   └─ Update Job-Status: generating → progress: 50%
   └─ Speichere output_file
   └─ Update Job-Status: completed, progress: 100%

7. Frontend: Polling erkennt "completed"
   └─ Lade Audio-Datei
   └─ Zeige Ergebnisbereich
   └─ Stop Polling-Loop

8. User kann jetzt:
   └─ Abspielen
   └─ Variieren (Repeat Flow)
   └─ Speichern (→ Project Service)
   └─ Exportieren
```

---

## Job Management

### Job Lifecycle

```
Created
   ↓
Pending (queued)
   ↓
Generating (progress: 0-100%)
   ↓
├─ Completed ✓
│
├─ Failed ✗ (error message)
│
└─ Cancelled (optional V2)
```

### Job Storage

**In-Memory Dictionary** (V1)
```python
{
  "job_id_1": {
    "id": "uuid",
    "type": "track",
    "status": "completed",
    "progress": 100,
    "result_file": "/path/to/audio.mp3",
    "metadata": {...},
    "created_at": datetime
  },
  ...
}
```

**Later (V2):** Database (SQLite/PostgreSQL)

---

## Configuration

### Settings (`app/config.py`)

```python
# Engine
ENGINE_TYPE = "mock"  # oder "comfyui", "aces"
ENGINE_MOCK_DELAY = 2  # Sekunden für Demo

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROJECTS_DIR = DATA_DIR / "projects"
OUTPUTS_DIR = DATA_DIR / "outputs"
EXPORTS_DIR = DATA_DIR / "exports"

# CORS
ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000", ...]
```

### Environment Variables (`.env`)
```
ENGINE_TYPE=mock
SERVER_PORT=8000
LOG_LEVEL=info
```

---

## File Organization

### Projects (JSON)

```json
// data/projects/abc12345.json
{
  "id": "abc12345",
  "name": "Midnight Vibes",
  "type": "track",
  "genre": "Techno",
  "mood": "dark",
  "duration": 120,
  "created_at": "2026-03-30T22:30:00",
  "updated_at": "2026-03-30T22:30:00",
  "output_file": "data/outputs/track_abc12345.mp3",
  "parameters": {
    "energy": 7,
    "tempo": 130,
    "creativity": 6,
    "catchiness": 5,
    "vocal_strength": 4
  },
  "metadata": {
    "lyrics": "Optional lyrics...",
    "tags": ["dark", "minimal"]
  }
}
```

### Audio Files

```
data/outputs/
  ├── track_a1b2c3d4.mp3    (generierte Tracks)
  ├── beat_e5f6g7h8.mp3     (generierte Beats)
  └── variation_i9j0k1l2.mp3 (Variationen)

data/exports/
  ├── My Track Final_track_a1b2c3d4.mp3
  └── Dark Beat_beat_e5f6g7h8.mp3
```

---

## Extension Points

### 1. Neue Engine-Integration

**Pattern:**
```python
# app/services/__init__.py
class MyCustomEngine:
    async def generate_track_audio(self, **kwargs) -> str:
        # Mache echte API-Calls hier
        # Return Pfad zu Audiodatei
        pass

# app/config.py
if settings.ENGINE_TYPE == "myengine":
    engine = MyCustomEngine()
```

**Kein UI-Change erforderlich!**

### 2. Neue Features

- **Status-Updates:** MusicGenerationService → Backend → Frontend
- **Batch-Processing:** Routes → BatchService
- **Plugins:** Services-basierte Architektur
- **Database:** Ersetze JSON durch SQLAlchemy

### 3. Frontend Extensions

- Neue Seiten: `<section id="page-NEW">...</section>`
- Neue Navigation: `<button class="nav-btn" data-page="NEW">`
- Neue API-Calls: `addEventListener + fetch()`

---

## Development Tips

### Debug-Modus

```bash
# Backend mit Debug-Output
LOG_LEVEL=debug python backend/run.py

# Frontend Browser-Console
F12 → Console
```

### Mock-Engine testen

Keine echte Engine nötig! Einfach:
1. Formulare ausfüllen
2. Generierung starten
3. Fortschritt beobachten
4. Dummy-Audio abspielen

### API Docs

Interaktive Swagger-UI:
```
http://localhost:8000/docs
```

### Daten inspizieren

```bash
# Projekte auflisten
ls data/projects/*.json

# Outputs auflisten
ls data/outputs/

# Project-Datei lesen
type data/projects/abc12345.json
```

---

## Known Limitations (V1)

- ✗ Keine echte Musik-Generierung (Mock)
- ✗ Jobs nur im RAM (verloren bei Server-Restart)
- ✗ Kein User-Management
- ✗ Keine Authentifizierung
- ✗ Single-Threaded (ein Job nach dem anderen)
- ✗ Keine Error-Recovery

**V2 wird diese Aufzählung adressieren.**

---

## Performance Considerations

### Current (V1)
- Mock-Generierung: 2 Sekunden
- Job-Polling: 500ms Intervall
- In-Memory Jobs: ~100 gleichzeitige Jobs möglich
- File I/O: JSON-Serialisierung (schnell)

### Optimizations (V2)
- WebSocket statt Polling
- Echte Musik-Engine (variable Zeiten)
- Database statt JSON
- Job Queue (ThreadPool/Celery)
- Audio-Streaming (Chunks statt ganz laden)

---

## Testing Strategy

### Manual Testing
- [ ] Frontend Navigation
- [ ] Track-Form Validierung
- [ ] Beat-Form Validierung
- [ ] Job Monitoring
- [ ] Project Save/Load
- [ ] Export-Funktion

### Automated Testing (später)
- Unit Tests (Services)
- Integration Tests (Routes)
- UI Tests (Selenium/Playwright)

---

## Deployment (zukünftig)

### Local Development
```bash
python backend/run.py
# Frontend: http://localhost:8000
```

### Production (V2)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (V2)
```dockerfile
FROM python:3.11
COPY backend /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app"]
```

---

## 🎯 Design Principles

1. **Simplicity:** Wenig ist mehr
2. **Modularity:** Services sind austauschbar
3. **User-Focused:** Keine technischen Details in der UI
4. **Extensible:** Neue Features leicht zu ergänzen
5. **Beautiful:** Lila/Grün, Dark Theme, Studio-Feel

---

**Last Updated:** 2026-03-30  
**Version:** 1.0.0-alpha  
**Status:** ✅ Foundation Complete, Ready for Engine Integration
