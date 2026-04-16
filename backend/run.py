#!/usr/bin/env python3
"""Start the consolidated backend server."""

import os
from pathlib import Path

project_root = Path(__file__).parent
os.chdir(project_root)


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    reload_enabled = os.getenv("MICKS_BACKEND_RELOAD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    print("Micks Musikkiste backend is starting...")
    print(f"Frontend: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"API Docs: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/docs")
    print(
        f"Diagnostics: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/api/diagnostics"
    )
    print(f"Logs: {settings.LOGS_DIR}")
    print(f"Reload mode: {'on' if reload_enabled else 'off'}")

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=reload_enabled,
        log_level=settings.LOG_LEVEL.lower(),
    )
