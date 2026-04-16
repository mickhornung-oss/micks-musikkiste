# INC-2026-04-16 CI Stability Regression

## Header
- Incident ID: INC-2026-04-16
- Date/Time (UTC): 2026-04-16
- Environment: CI (`main` branch)
- Release version / SHA: pre-`v1.0.1`
- Severity: SEV-3
- Status: Resolved

## Impact
- User impact: no direct user downtime
- Technical impact: blocked merges due to failing CI pipelines
- Start time: ~00:30 UTC
- End time: ~06:30 UTC
- Total duration: ~6 hours

## Detection
- Detected by failed GitHub Actions runs and red status badges
- First signal: failing `tests` jobs and unstable security checks

## Timeline (UTC)
1. CI jobs failed with multiple root causes (dependency audit, pytest plugin mismatch, platform libs).
2. Security gates were hardened (`pip-audit` enforced), exposing hidden dependency issues.
3. Dependencies and workflows were patched; diagnostics annotations were added.
4. `minan-csv-analyse` Linux dependency (`libegl1`) added; Codecov failure path removed.
5. All critical repos returned to green CI.

## Root Cause
- Primary cause: pipeline fragility from inconsistent dependency/tool versions and environment assumptions.
- Contributing factors:
  - security checks previously non-blocking (`|| true`)
  - test/runtime dependencies mixed in single requirement sets
  - missing Linux GUI dependency for Qt tests

## Mitigation and Recovery
- Enforced deterministic CI tooling and security scans.
- Updated vulnerable dependencies.
- Added targeted ignore for a known transitive CVE where no compatible fix path was available in current stack.
- Added test-failure annotations to improve diagnosis speed.

## Corrective Actions
1. Separate runtime and test dependency concerns in CI.
   - Owner: Maintainer
   - Due date: completed
2. Keep workflow diagnostics for faster future triage.
   - Owner: Maintainer
   - Due date: completed

## Preventive Actions
1. Keep `pip-audit` as a hard gate with documented exceptions only.
2. Keep smoke check and runbook mandatory for release prep.
3. Record future CI incidents in `docs/incidents/`.

## Closure
- Final verification: all main pipelines green
- Lessons learned: fast iteration is fine, but deterministic CI and explicit diagnostics are mandatory
