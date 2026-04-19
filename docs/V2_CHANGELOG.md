# V2 Entwicklungsverlauf (konsolidiert)

Dieses Dokument ist eine bereinigte V2-Historie.
Es ersetzt alte Zwischenstaende mit ueberholten Aussagen.

## Stand 2026-04-20

V2 ist als Produktlinie aktiv und integriert:
- Frontend-Flow fuer Beat und Full Track
- V2-Endpunkte unter `/api/v2/*`
- Job-Polling inkl. Ausgabe-URLs
- Projekt speichern/listen in V2-Form
- Export aus gespeicherten Projekten
- Testabdeckung fuer die zentralen V2-Flows

## Wichtige V2-Entscheidungen

- Keine Preset-zentrierte V1-Interaktion als Hauptpfad
- Klare Feldsemantik:
  - `prompt` = Musikbeschreibung
  - `negative_prompt` = Ausschluesse
  - `text_idea` = Themenhinweis, keine direkte Lyrics-Uebergabe
- Ehrliche Engine-Kommunikation statt "alles ready"

## Realer Engine-Status

- `mock`: nutzbar
- `ace`: nur mit erfuellten lokalen Voraussetzungen (ComfyUI + Workflow + Erreichbarkeit)
- `musicgen`: vorbereitet, derzeit nicht voll implementiert/verfuegbar

## Release-Reife fuer V2

V2 ist fuer lokale End-to-End-Flows im Mock-Modus releasefaehig:
- Generate -> Poll -> Audio abrufen
- Projekt speichern/listen
- Projekt exportieren

Nicht Teil dieses Stands:
- voll produktionsreife ACE- oder MusicGen-Laufzeit ohne weitere Infrastrukturarbeit
