# Micks Musikkiste

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-09a031.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://github.com/mickhornung-oss/micks-musikkiste/actions/workflows/python-tests.yml/badge.svg)](https://github.com/mickhornung-oss/micks-musikkiste/actions)

AI music production studio backend with FastAPI, async PostgreSQL, queue-based jobs, and structured observability.

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

# 2. Set environment variables (copy .env.example to .env)
cp .env.example .env

# 3. Initialize database
python backend/scripts/migrate.py

# 4. Start the app
python backend/run.py
```

Live endpoints:
- UI: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
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
APP_ENV=local
RELEASE_VERSION=0.2.0
RELEASE_SHA=local
```

## Engine Modes

| Mode | Description |
|---|---|
| `mock` | Recommended for local dev, no external dependencies |
| `ace` | Requires a running ComfyUI instance with ACE-Step workflow |
| `real` | Uses the real engine runtime if available locally |

## Observability

- `GET /health`: API status and release metadata
- `GET /api/diagnostics`: database, engine, jobs, runtime, storage, logs
- `release` block: `environment`, `version`, `sha`
- `runtime` block: `started_at_utc`, `uptime_seconds`
- Response headers: `X-Request-ID`, `X-Process-Time-Ms`
- Log files: `logs/app.log`, `logs/error.log`

## Operations

- Runbook: [`docs/RUNBOOK.md`](docs/RUNBOOK.md)
- Release checklist: [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md)
- Deployment smoke check:

```bash
python scripts/smoke_check.py http://127.0.0.1:8000
```

## Tests

```bash
# Unit + integration tests (requires PostgreSQL)
.\.venv\Scripts\python -m pytest backend/tests -q

# Browser-level E2E smoke tests
cd e2e && npm install && npx playwright install chromium && npm test
```

## Known Limitations

- `ace` and `real` modes require a local ComfyUI installation
- E2E suite runs against `mock` mode only
