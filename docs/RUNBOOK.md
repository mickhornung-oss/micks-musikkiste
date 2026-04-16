# Operations Runbook

## Scope
- Service: `micks-musikkiste` backend (`FastAPI`)
- Critical endpoints: `/health`, `/api/diagnostics`, `/api/jobs`, `/api/projects`
- Main risks: database connectivity, stuck queue jobs, engine runtime readiness

## Environments
- `APP_ENV`: `local`, `staging`, `production`
- `RELEASE_VERSION`: semantic release string (for example `0.2.1`)
- `RELEASE_SHA`: short git sha deployed

## Pre-Deploy Checklist
1. CI green on `main`.
2. `docker build` succeeds locally.
3. Smoke check passes against target:
   - `python scripts/smoke_check.py http://<host>:8000`
4. `/api/diagnostics` shows:
   - `database.ok=true`
   - `worker.running=true` (if worker enabled)
   - expected `release.version` and `release.sha`

## Incident Triage

### 1) Service unavailable
1. Check container/process health.
2. Call `/health` and `/api/diagnostics`.
3. If no response:
   - inspect container logs (`logs/app.log`, `logs/error.log`)
   - verify DB reachability and credentials.

### 2) Jobs stuck in `running`/`queued`
1. Inspect `/api/worker/status`.
2. Verify DB health (`diagnostics.database`).
3. Restart worker process/container.
4. Recheck `jobs` counters in diagnostics.

### 3) Engine issues (`ace`/`real`)
1. Confirm `ENGINE_MODE`.
2. In diagnostics, inspect:
   - `engine.ready`
   - `engine.details.workflow_ok`
   - `engine.details.comfy_reachable`
3. Fallback to `ENGINE_MODE=mock` for partial availability.

## Recovery Actions
- Restart API service.
- Restart worker (if split deployment).
- Run migrations:
  - `cd backend && alembic upgrade head`
- Re-run smoke check:
  - `python scripts/smoke_check.py http://127.0.0.1:8000`

## Rollback Rule
- If smoke check fails after deploy and error is not fixed within 15 minutes:
  1. Roll back to previous image/tag.
  2. Confirm health + diagnostics on rolled-back version.
  3. Open incident note with root-cause and follow-up tasks.
