# Micks Musikkiste

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-09a031.svg)](https://fastapi.tiangolo.com/)
[![codecov](https://codecov.io/gh/mickhornung-oss/micks-musikkiste/branch/main/graph/badge.svg)](https://codecov.io/gh/mickhornung-oss/micks-musikkiste)
[![Tests](https://github.com/mickhornung-oss/micks-musikkiste/actions/workflows/python-tests.yml/badge.svg)](https://github.com/mickhornung-oss/micks-musikkiste/actions)

AI music production studio — FastAPI backend with async PostgreSQL, queue-based job processing, multi-engine abstraction, and structured observability.

> **Deutsch:** Lokales KI-Musikstudio mit FastAPI-Backend, async PostgreSQL, Job-Queue und strukturiertem Observability-Layer.

## Architecture

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLAlchemy Async + asyncpg |
| Database | PostgreSQL (jobs, projects, export metadata) |
| Job Queue | Background worker with status tracking |
| Frontend | Static HTML/CSS/JS served by FastAPI |
| Observability | Structured logging, `/health`, `/api/diagnostics` |
| Engine Modes | `mock` / `ace` (ComfyUI) / `real` |

## Quick Start

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Set environment variables (copy .env.example → .env)
cp .env.example .env

# 3. Initialize database
python backend/scripts/migrate.py

# 4. Start the app
python backend/run.py
```

Live endpoints:
- UI: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Diagnostics: `http://localhost:8000/api/diagnostics`

## Configuration

Set via environment variables or `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
ENGINE_MODE=mock
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
LOG_LEVEL=info
DEBUG=false
```

## Engine Modes

| Mode | Description |
|---|---|
| `mock` | Recommended for local dev — no external dependencies |
| `ace` | Requires a running ComfyUI instance with ACE-Step workflow |
| `real` | Uses the real engine runtime if available locally |

## Observability

- `GET /health` — API status, engine state, counters
- `GET /api/diagnostics` — DB pool info, engine readiness, storage, recent jobs
- Response headers: `X-Request-ID`, `X-Process-Time-Ms`
- Log files: `logs/app.log`, `logs/error.log`

## Tests

```bash
# Unit + Integration tests (requires PostgreSQL)
.\.venv\Scripts\python -m pytest backend/tests -q

# Browser-level E2E smoke tests
cd e2e && npm install && npx playwright install chromium && npm test
```

The test suite starts the backend in `mock` mode on port `8011` and covers:
app startup, status page, mock track creation, result display, project save, export, project list.

## Known Limitations

- `ace` / `real` modes require a local ComfyUI instance with specific workflows installed
- The E2E suite runs against `mock` mode only — ComfyUI integration is tested manually
