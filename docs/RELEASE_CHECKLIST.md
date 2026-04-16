# Release Checklist

## Before Tagging
1. Merge only after CI is green.
2. Update `CHANGELOG.md` with user-visible changes.
3. Set release metadata for target env:
   - `RELEASE_VERSION`
   - `RELEASE_SHA`
   - `APP_ENV`

## Build & Verify
1. Build image:
   - `docker build -t micks-musikkiste:<version> .`
2. Start stack:
   - `docker compose up -d`
3. Run smoke test:
   - `python scripts/smoke_check.py http://127.0.0.1:8000`

## Deploy
1. Deploy image to target environment.
2. Validate:
   - `/health` returns `ok` or `degraded`
   - `/api/diagnostics` `database.ok=true`
   - `release.version` and `release.sha` match target release

## After Deploy
1. Watch logs for 10 minutes.
2. Confirm no growth in `requests_failed`.
3. Create git tag and release notes.
