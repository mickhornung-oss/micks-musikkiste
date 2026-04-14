# 📋 Micks Musikkiste - Quick Reference

## 🎮 First Time Here?

1. **Öffne Terminal/PowerShell**
2. **Navigiere:** `cd C:\Users\mickh\Desktop\MicksMusikkiste`
3. **Aktiviere venv:** `.venv\Scripts\Activate.ps1`
4. **Starte Server:** `python backend/run.py`
5. **Öffne Browser:** http://localhost:8000

**Fertig!** UI sollte sichtbar sein. ✅

---

## 🎨 UI Einstieg

### Startseite
- 3 große Karten: Track erstellen | Beat starten | Projekte
- Darunter: Kürzliche Projekte

### Track erstellen
1. Titel eingeben (z.B. "Midnight Vibes")
2. Genre wählen (Techno, Hip-Hop, House, ...)
3. Stimmung wählen (energetic, dark, melancholic, ...)
4. Optional: Lyrics, Sprache, Dauer einstellen
5. Sliders anpassen (Energie, Tempo, Kreativität, ...)
6. **"Track generieren"** klicken
7. Warte auf Generierung (Mock: ~2 Sekunden)
8. Ergebnis speichern oder exportieren

### Beat starten
Ähnlich wie Track, aber:
- Kein Lyrics
- Fokus auf Drums/Percussion
- Regler: Tempo, Druck, Melodie-Anteil, Energie

### Projekte
- Liste aller gespeicherten Tracks/Beats
- Mit Buttons: Abspielen, Löschen

### Status
- System-Informationen
- Engine-Typ
- Projekt-/Output-Zähler

---

## 🔧 Backend URLs

```
GET    http://localhost:8000/              (App Info)
GET    http://localhost:8000/health        (System Status)
GET    http://localhost:8000/docs          (API Docs - Swagger)

POST   http://localhost:8000/api/track/generate
POST   http://localhost:8000/api/beat/generate
GET    http://localhost:8000/api/projects
GET    http://localhost:8000/api/jobs/{id}
```

---

## 📁 Wichtige Ordner

```
C:\Users\mickh\Desktop\MicksMusikkiste\

backend/           ← FastAPI App
frontend/          ← HTML/CSS/JS UI
data/
  ├─ projects/    ← Gespeicherte Projekte (JSON)
  ├─ outputs/     ← Generierte Audio-Dateien
  └─ exports/     ← Exportierte Sound-Dateien
docs/              ← Dokumentation
```

---

## 🎯 Design Merksätze

**Farben:**
- 🟣 Lila (#8B5CF6) - Primary Actions
- 🟢 Grün (#10B981) - Success/Export
- 🟤 Dunkelblau (#0F172A) - Background
- 🔴 Rosa (#EC4899) - Highlight

**Gefühl:** Studio, modern, urban, clean, dark

---

## ✨ Das funktioniert JETZT

- ✅ Schöne Oberfläche
- ✅ Track/Beat-Forms
- ✅ Mock-Generierung
- ✅ Audio-Player
- ✅ Projekte speichern/laden
- ✅ Export-Funktion
- ✅ Status-Seite
- ✅ API Dokumentation

---

## 🚧 Das kommt SPÄTER (V2+)

- 🔜 Echte Musik-Engine
- 🔜 Datenbank statt JSON
- 🔜 WebSockets (statt Polling)
- 🔜 User-Accounts
- 🔜 Cloud-Sync
- 🔜 Batch-Processing
- 🔜 Advanced Editing

---

## 🐛 Falls Problem auftritt...

**Server startet nicht?**
- Ist Port 8000 frei? `netstat -ano | findstr :8000`
- Python 3.8+? `python --version`
- Alle Dependencies installiert? `pip install -r backend/requirements.txt`

**UI lädt nicht?**
- Browser: http://localhost:8000
- Refresh: Ctrl+F5
- Console: F12 → Console (errors?)

**API antwortet nicht?**
- Server läuft? Terminal sollte "Uvicorn running" zeigen
- Swagger UI: http://localhost:8000/docs
- Test Health: http://localhost:8000/health

---

## 📞 File Guide

| Datei | Warum wichtig |
|-------|---|
| `backend/app/main.py` | FastAPI App-Kern |
| `backend/app/config.py` | Settings (ENGINE_TYPE, etc) |
| `frontend/index.html` | UI-Struktur |
| `frontend/styles/main.css` | Lila/Grün Design |
| `frontend/js/app.js` | Frontend-Logik |
| `.env` | Umgebungsvariablen |
| `README.md` | Vollständige Docs |
| `ARCHITECTURE.md` | Technische Details |

---

## 🎪 Demo-Flow

1. **Start:** http://localhost:8000
2. **Click:** "Track erstellen"
3. **Fill:** Titel = "My First Track", Genre = "Techno", Stimmung = "dark"
4. **Click:** "Track generieren"
5. **Wait:** Progress Bar läuft
6. **Result:** Audio-Player mit Dummy-Audio
7. **Click:** "Als Projekt speichern"
8. **Go:** "Projekte" → Dein Projekt ist da!

---

## 🎵 Pro-Tipps

- **Slider anpassen** before generating für unterschiedliche Sounds
- **Lyrics eingeben** für personalisierte Tracks
- **Mehrere generieren** und compare
- **Projects verwalten** - Backups empfohlen
- **API Docs nutzen** zum experimentieren

---

## 📊 Technologie Stack

**Backend:** FastAPI (Python)  
**Frontend:** HTML5 + CSS3 + Vanilla JS  
**Storage:** JSON-Files (lokal)  
**Engine:** Mock (V1), später: ComfyUI/ACE-Steps  
**Threading:** Async Python (asyncio)  

---

✅ **Du bist startklar!**

**Nächster Schritt:** `python backend/run.py` dann http://localhost:8000

Happy Music Making! 🎜🟣🟢
