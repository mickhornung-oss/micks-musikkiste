# 🚀 Schnelle Installation - Windows

## Schritt 1: Projekt öffnen

```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste
```

## Schritt 2: Virtual Environment aktivieren

```powershell
.venv\Scripts\Activate.ps1
```

**Erfolgreich wenn:** `(.venv)` am Anfang der Zeile steht

## Schritt 3: Dependencies installieren

```powershell
pip install -r backend/requirements.txt
```

## Schritt 4: Server starten

```powershell
python backend/run.py
```

**Erfolgreich wenn:**
```
╔════════════════════════════════════════╗
║     Micks Musikkiste - Backend V1      ║
╚════════════════════════════════════════╝

🎜 Server wird gestartet...

Frontend:  http://localhost:8000
API Docs:  http://localhost:8000/docs

INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Schritt 5: Browser öffnen

**Öffne:** http://localhost:8000

Fertig! 🎉

---

## Schnellbefehle (Copy & Paste)

### Kompletten Setup machen (one-liner)
```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste; .venv\Scripts\Activate.ps1; pip install -r backend/requirements.txt; python backend/run.py
```

### Nur Server starten (wenn schon installiert)
```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste; .venv\Scripts\Activate.ps1; python backend/run.py
```

### Windows Batch-Datei verwenden
```powershell
cd C:\Users\mickh\Desktop\MicksMusikkiste
start.bat
```

---

## Links

- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **API Root:** http://localhost:8000/api

---

## Troubleshooting

**"Python nicht gefunden"**
```powershell
# Nutzer Python 3.8+
python --version

# Falls nicht: Installiere von python.org
```

**"Module nicht gefunden"**
```powershell
# Stell sicher venv ist aktiviert
.venv\Scripts\Activate.ps1

# Dann reinstallieren
pip install -r backend/requirements.txt
```

**"Port 8000 schon in Benutzung"**
```powershell
# Nutzer einen anderen Port
python backend/run.py --port 8001
# Dann: http://localhost:8001
```

**"Access Denied bei Datei"**
```powershell
# Starte PowerShell als Admin
# Oder change file permissions
```

---

**Viel Spaß! 🎜**
