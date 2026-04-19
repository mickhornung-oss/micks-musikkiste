# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Release-Dokumentation auf ehrlichen V2-Stand gebracht (README, Installation, Quick Reference, Architektur)
- Startskripte auf V2-Begriffe und realen Startpfad vereinheitlicht
- Konfigurationsbeispiele auf `ENGINE_MODE` und lokalen Mock-Start ausgerichtet

### Fixed
- Irrefuehrende V1-Texte in Root-Doku entfernt
- Falsche Aussagen zu vollstaendig produktionsbereiten Engines entfernt

### Notes
- Aktueller realistischer Engine-Status:
	- `mock` nutzbar
	- `ace` nur mit erfuellten lokalen Voraussetzungen
	- `musicgen` vorbereitet, aktuell nicht voll implementiert/verfuegbar

## [2.0.0] - 2026-04-20

### Added
- V2 API unter `/api/v2/*` fuer Beat/Track/Jobs/Projects/Status
- V2 Frontend-Flow fuer Beat und Full Track mit Prompt, Negative Prompt und Textidee
- V2 Projektfluss inkl. Save/List und Output-URL Mapping
- V2 Testabdeckung fuer End-to-End-Flows im Mock-Modus

### Changed
- Produktlogik auf V2 Request/Response-Vertraege ausgerichtet
- Frontend von alten Preset-orientierten V1-Pfaden auf V2-Formlogik umgestellt
- Dokumentation und Startpfade auf den tatsaechlichen V2-Stand gebracht

### Fixed
- `output_url` in Job-Antworten fuer direkte Audio-Auslieferung
- Feldmapping zwischen V1-Projektdaten und V2-Projektansicht (`name/title`, `audio_url/output_url`)
- Integrationstests auf reale V2-Endpunkte aktualisiert

### Notes
- Kein Claim auf voll produktionsbereite ACE/MusicGen-Ausfuehrung im Standard-Setup

## [1.0.1] - 2026-04-16

### Added
- Operational runbook (`docs/RUNBOOK.md`) and release checklist (`docs/RELEASE_CHECKLIST.md`)
- Deployment smoke check script (`scripts/smoke_check.py`)
- Release and runtime metadata in `/health` and `/api/diagnostics`
- Container health checks in Dockerfile and docker-compose

## [1.0.0] - 2026-04-15

### Added
- MIT License for open-source distribution
- Initial release: FastAPI backend with async PostgreSQL, queue-based job processing
- MockMusicEngine for local demo/testing without external dependencies
- Track and Beat generation endpoints with Pydantic validation
- Preset system with JSON-based track and beat presets
- Project persistence with SQLAlchemy ORM
- Frontend SPA (HTML/CSS/JS) with dark theme, Lila/Grün palette
- Structured observability: `/health`, `/api/diagnostics`, request tracing
- Queue worker with heartbeat, stale-job recovery, and retry logic
- Database migrations via Alembic
- Deployment configs: Dockerfile, docker-compose, Railway, Render
