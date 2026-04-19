"""Micks Musikkiste - consolidated backend entrypoint."""

from contextlib import asynccontextmanager

from app.config import settings
from app.database import async_session_factory, close_db, init_db
from app.http import RequestContextMiddleware, install_error_handlers
from app.logging_config import logger
from app.repositories.job_repository import JobRepository
from app.routes import router
from app.routes.v2_routes import v2_router
from app.services.comfy_service import ensure_comfy_available
from app.services.queue_worker import start_worker, stop_worker
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and close shared resources."""
    logger.info("starting_backend", engine_mode=settings.ENGINE_MODE)
    db_ready = True
    try:
        await init_db()
    except Exception as exc:
        db_ready = False
        logger.exception("database_init_failed_starting_degraded", error=str(exc))
    app.state.db_ready = db_ready

    # Recovery of stuck jobs
    if db_ready:
        try:
            async with async_session_factory() as session:
                job_repo = JobRepository(session)
                recovery_result = await job_repo.recover_stuck_jobs()
                logger.info(
                    "recovery_complete",
                    recovered=recovery_result["recovered"],
                    failed=recovery_result["failed"],
                    total=recovery_result["total"],
                )
        except Exception as exc:
            logger.error("recovery_failed", error=str(exc))
            db_ready = False
            app.state.db_ready = False

    if (settings.ENGINE_MODE or "").lower() in {"ace", "ace-step", "acestep"}:
        comfy_state = await ensure_comfy_available()
        logger.info(
            "comfy_startup_status",
            reachable=comfy_state["reachable"],
            autostart_attempted=comfy_state["autostart_attempted"],
            autostart_started=comfy_state["autostart_started"],
            error=comfy_state["last_error"],
            url=comfy_state["url"],
        )

    # Start queue worker if enabled
    worker = None
    if settings.WORKER_ENABLED and db_ready:
        worker = await start_worker()
        if worker:
            logger.info("worker_started", worker_id=worker.worker_id)

    yield

    # Stop worker gracefully
    if worker:
        await stop_worker()

    await close_db()
    logger.info("backend_stopped")


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
install_error_handlers(app)

app.include_router(router)
app.include_router(v2_router)

frontend_path = settings.PROJECT_ROOT / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Serve frontend HTML when available."""
    index_file = settings.PROJECT_ROOT / "frontend" / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")

    return {
        "app": "Micks Musikkiste",
        "version": settings.API_VERSION,
        "status": "running",
        "frontend": "not found - check frontend/index.html",
        "docs": "/docs",
    }


@app.get("/api")
async def api_root():
    """Expose a minimal API index."""
    return {
        "version": settings.API_VERSION,
        "v2_endpoints": {
            "beat_generate": "/api/v2/beat/generate",
            "track_generate": "/api/v2/track/generate",
            "engine_status": "/api/v2/engine/status",
            "genres": "/api/v2/genres",
            "config": "/api/v2/config",
            "job_status": "/api/v2/jobs/{job_id}",
        },
        "v1_endpoints": {
            "health": "/health",
            "track": "/api/track/generate",
            "beat": "/api/beat/generate",
            "projects": "/api/projects",
            "jobs": "/api/jobs",
        },
    }
