# 🎜 MICKS MUSIKKISTE V2 – CHANGE LOG

**Status:** ✅ IN ARBEIT  
**Datum:** 30. März 2026  
**Version:** 2.0.0-beta  

---

## 🚀 Phase 1: Presets-System ✅ DONE

### Implementiert:
- ✅ PresetValues Model (Pydantic)
- ✅ TrackPreset Model mit Specs
- ✅ BeatPreset Model mit Specs
- ✅ PresetsManager Service mit JSON-Speicherung
- ✅ 8 Track-Presets:
  - Dark Techno ← hypnotic, minimal
  - Melodic Techno ← emotional, structured
  - Driving Club Techno ← dance-floor ready
  - Hard Underground Techno ← aggressive, raw
  - Boom Bap ← soul samples, classic hip-hop
  - Modern Trap ← 808s, hi-hats, contemporary
  - LoFi Hip-Hop ← chill, vinyl, study vibes
  - Dark Urban Hip-Hop ← street sound, aggressive
- ✅ 4 Beat-Presets (Techno Dark, Club, Boom Bap, Trap)
- ✅ Preset-Loader und Auto-Default-Creation
- ✅ 4 neue API-Endpoints:
  - GET /api/presets/track - alle Track-Presets
  - GET /api/presets/beat - alle Beat-Presets
  - GET /api/presets/track/{id} - spezifisches Track-Preset
  - GET /api/presets/beat/{id} - spezifisches Beat-Preset
- ✅ Preset-Anwendung in generate Endpoints (auto-apply values)
- ✅ Generierungs-Service erweitert mit Preset-Support
- ✅ Modelle erweitert: preset_used, lyrics, notes, exports-Tracking

### API Response Beispiel:
```json
{
  "success": true,
  "data": {
    "total": 8,
    "presets": [
      {
        "id": "techno_dark",
        "name": "Dark Techno",
        "category": "techno",
        "description": "...",
        "values": {
          "energy": 6,
          "tempo": 125,
          ...
        }
      }
    ]
  }
}
```

**Verifiziert:** ✅ Alle Endpoints funktionieren, Presets von API verfügbar

---

## 📝 Phase 2: Frontend Preset-UI & Guided Flows (IN ARBEIT)

### Geplant:
- [ ] Preset-Dropdown in Track/Beat-Forms
- [ ] Guided Creation Flow mit Hilfetexten
- [ ] Bessere Preset-Beschreibungen in UI
- [ ] Ergebnisbereich komplett redesign
- [ ] Projekt-Filtration (Track/Beat, Genre, Alphabetisch)
- [ ] Export-Statusanzeige
- [ ] Bessere Fehlerbehandlung

### Dateien zu ändern:
- frontend/index.html - erweiterte Forms
- frontend/js/app.js - Preset-Logik + Flows
- frontend/styles/main.css - UI-Polishing

---

## 🎯 Phase 3: Models & Backend-Erweiterung ✅ DONE

### Implementiert:
- ✅ GenerationJob um "cancelled" + "preset_used" erweitert
- ✅ Project um "preset_used", "lyrics", "negative_prompts", "notes", "exports" erweitert
- ✅ TrackGenerationRequest um "preset_id" erweitert
- ✅ BeatGenerationRequest um "preset_id" erweitert
- ✅ Imports in routes angepasst

---

## 🛠️ Phase 3b: Engine-Adapter & Job-Pipeline ✅ DONE

### Implementiert:
- ✅ Engine-Adapter-Schicht mit Factory (`mock`/`real`)
- ✅ Mock-Adapter ausgelagert (sauberer Testlauf)
- ✅ Real-Adapter vorbereitet (externes CLI über `ENGINE_REAL_COMMAND`, Timeout)
- ✅ MusicGenerationService: queued → running → completed/failed/cancelled, Engine-Metadaten
- ✅ Output-Validierung (Datei muss existieren, sonst failed)
- ✅ Export-Logging + last_export_at im ProjectService
- ✅ Health-Endpoint meldet aktiven Engine-Mode

### Neue Settings:
- `ENGINE_MODE` = mock | real
- `ENGINE_REAL_COMMAND` = Pfad/Command zur echten Engine
- `ENGINE_TIMEOUT` = Sekunden

### Hinweise:
- Default bleibt mock; Real-Adapter wirft klaren Fehler ohne konfigurierten Command.
- Endpoints/Frontend unverändert, nutzen weiterhin die Service-Schicht.

---

## 🎛️ Phase 4: Konkrete Real-Engine ✅ DONE

### Implementiert:
- ✅ Real-Adapter nutzt externes CLI (Default: internes `backend/engine_cli.py`)
- ✅ Mapping von title/genre/mood/duration/tempo/energy/preset/lyrics/negative -> CLI-Args
- ✅ Output-Erzeugung als WAV in `data/outputs`, Validierung auf Existenz/Size
- ✅ Timeout-Handling & Exitcode-Fehler mit nutzerfreundlicher Meldung
- ✅ Beispiel-Engine erzeugt echten Audio-Output (Sine-Layer) für End-to-End-Tests

### Nutzung:
- Mock: `ENGINE_MODE=mock` (Default)
- Real: `ENGINE_MODE=real` und optional `ENGINE_REAL_COMMAND="python backend/engine_cli.py"`
- `ENGINE_TIMEOUT` setzt Max-Laufzeit (Default 180s)

### Grenzen:
- Fortschrittswerte sind aktuell konservativ (queued/running/completed/failed), kein Live-Progress aus externer Engine.
- Beispiel-Engine generiert synthetische WAVs; für echte Modelle `ENGINE_REAL_COMMAND` auf eigenes CLI zeigen.

---

## 🎶 Phase 5: Echtes Musikmodell (MusicGen) ✅ DONE

### Implementiert:
- ✅ Real-Adapter defaultet jetzt auf internes `engine_musicgen.py` (Meta MusicGen)
- ✅ CLI `backend/engine_musicgen.py` mappt title/genre/mood/preset/lyrics/tempo/energy/duration -> MusicGen Prompt
- ✅ Output als WAV in `data/outputs`, validiert in Job-Pipeline
- ✅ Fehler bei fehlenden Abhängigkeiten klar (torch/torchaudio/audiocraft)

### Nutzung:
- `.env` Beispiel:
  - `ENGINE_MODE=real`
  - `ENGINE_REAL_COMMAND="python backend/engine_musicgen.py"`
  - optional `ENGINE_TIMEOUT=300`
- Dependencies (optional, nur für Real): `pip install torch torchaudio audiocraft soundfile`

### Grenzen:
- MusicGen Download/Inference benötigt CPU/GPU und Netz für ersten Download.
- Dauer aktuell auf 60s begrenzt, kein Live-Progress von MusicGen.
- Wenn Dependencies fehlen, Real-Run schlägt mit klarer Fehlermeldung fehl; Mock weiter nutzbar.

---

## 💾 Phase 4: Datenstruktur

### Created:
- ✅ data/presets/track_presets.json (8 Presets)
- ✅ data/presets/beat_presets.json (4 Presets)

---

## 📊 Features-Übersicht V2

### Was NEU in V2:
1. **Presets-System** - Genre-spezifische Starter-Templates
2. **Guided Creation Flow** - bessere Nutzerführung
3. **Ergebnisbereich** - aufgewertet mit mehr Info/Aktionen
4. **Projekt-Verwaltung** - Suche + Filter
5. **Export-Management** - Track-Export-Statusanzeige
6. **Settings** - Standard-Defaults
7. **UI-Polish** - Konsistenz, Eleganz, Usability

### Was V2 NICHT ist:
- ❌ Keine Voll-DAW
- ❌ Keine Timeline/Mehrspur
- ❌ Keine MIDI-Bearbeitung
- ❌ Keine Node-Editor-Sicht
- ❌ Keine komplexe Engine-Einstellungen im UI

---

## 🔧 Backend-Changes (nur API/Models):

### Neue Routes:
```
GET  /api/presets/track              → Track-Presets auflisten
GET  /api/presets/beat               → Beat-Presets auflisten
GET  /api/presets/track/{id}         → Spezifisches Track-Preset
GET  /api/presets/beat/{id}          → Spezifisches Beat-Preset
POST /api/track/generate (updated)   → mit Preset-Support
POST /api/beat/generate (updated)    → mit Preset-Support
```

### Neue Models:
- PresetValues
- TrackPreset
- BeatPreset

### Updated Routes:
- GenerationJob: +preset_used, +cancelled, +queued status
- Project: +preset_used, +lyrics, +negative_prompts, +notes, +exports[]

### Services:
- MusicGenerationService ← updated mit preset_used tracking
- PresetsManager ← neu mit JSON persistence

---

## 📈 V1 → V2 Regressions-Check

- ✅ V1 Generierungs-Flows bleiben funktional
- ✅ V1 Projekte bleiben kompatibel
- ✅ V1 API-Endpoints bleiben erhalten
- ✅ V1 UI-Layout bleibt Basis (erweitert, nicht zerstört)
- ✅ Lokale Speicherung unbeeinträchtigt
- ✅ Mock-Engine läuf weiter

---

## 🧪 Tests durchgeführt

### Backend:
- ✅ Track-Presets API → 8 Presets geladen
- ✅ Beat-Presets API → 4 Presets geladen
- ✅ Preset-spezifisches Abrufen → OK
- ✅ Kategoriefilter → OK
- ✅ Preset-Anwendung auf Requests → OK
- ✅ Server startet ohne Fehler → OK

### Frontend:
- ⏳ noch zu testen nach UI-Update

---

##  Nächste Schritte

1. ✅ Presets-System (DONE)
2. → Frontend Preset-UI
3. → Guided Flows + Hilfetexte
4. → Ergebnisbereich Redesign
5. → Projekt-Filtration
6. → Export-System
7. → Settings
8. → Final Testing & Dokumentation

---

**Aktualisiert:** 30. März 2026 21:30 UTC
