# ✅ ABNAHMETEST – Micks Musikkiste V2
**Datum:** 31. März 2026  
**Scope:** Lokaler Release (Mock & Real/MusicGen)

## Testmatrix
1) Startskript (start_app.bat) → ✅ Backend gestartet, Frontend unter / verfügbar  
2) /health → ✅ status=ok, engine_mode=mock|real, engine_name korrekt  
3) Mock Track → ✅ Job completed, WAV/MP3 im Player, Export ok  
4) Mock Beat → ✅ Job completed, Export ok  
5) Real Track (MusicGen) → ✅ WAV in data/outputs, Player lädt, Export ok  
6) Presets → ✅ Werte/Regler werden gesetzt (Track & Beat)  
7) Projekt speichern → ✅ Eintrag in data/projects, Export-Historie leer initial  
8) Projekt öffnen → ✅ Titel/Genre/Mood/Dauer/Regler/Preset/Lyrics zurückgeladen  
9) Export aus Projekt → ✅ Datei in data/exports, last_export_at aktualisiert  
10) Suche/Filter/Sortierung Projekte → ✅ Typ/Genre/Preset-Filter, Sortierung inkl. „Zuletzt exportiert“  
11) Fehlerfall Real ohne deps → ✅ Job failed, verständliche Meldung, kein Mock-Fallback  
12) Status-UI → ✅ Topbar-Badge + Status-Seite zeigen Mode/Engine

## Ergebnis
Alle release-kritischen Flows grün. MusicGen erzeugt echte WAV, Mock weiter nutzbar. Keine Blocker offen.
