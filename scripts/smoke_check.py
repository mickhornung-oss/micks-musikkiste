"""Simple deployment smoke check for local/staging environments."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=8) as response:
        return json.load(response)


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    health_url = f"{base_url.rstrip('/')}/health"
    diagnostics_url = f"{base_url.rstrip('/')}/api/diagnostics"

    try:
        health = _fetch_json(health_url)
        diagnostics = _fetch_json(diagnostics_url)
    except urllib.error.URLError as exc:
        print(f"SMOKE_CHECK_FAILED: connection_error={exc}")
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE_CHECK_FAILED: unexpected_error={exc}")
        return 3

    if health.get("status") not in {"ok", "degraded"}:
        print(f"SMOKE_CHECK_FAILED: invalid_health_status={health.get('status')}")
        return 4

    db_ok = diagnostics.get("database", {}).get("ok")
    engine_mode = diagnostics.get("engine_type")
    release = diagnostics.get("release", {})
    runtime = diagnostics.get("runtime", {})

    print(
        "SMOKE_CHECK_OK",
        f"health_status={health.get('status')}",
        f"db_ok={db_ok}",
        f"engine_mode={engine_mode}",
        f"release_version={release.get('version')}",
        f"release_sha={release.get('sha')}",
        f"uptime_seconds={runtime.get('uptime_seconds')}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
