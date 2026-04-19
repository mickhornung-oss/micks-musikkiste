"""Consolidated API routes with database-backed persistence."""

import re
import shutil
from pathlib import Path
from typing import Optional

from app.config import settings
from app.database import async_session_factory, check_db_connection, get_db_session
from app.errors import InvalidStateError, NotFoundError
from app.logging_config import logger
from app.models import (
    BeatGenerationRequest,
    DiagnosticsResponse,
    SaveProjectRequest,
    SystemStatus,
    TrackGenerationRequest,
)
from app.observability import runtime_stats
from app.repositories.job_repository import JobRepository
from app.services.engines import get_engine_diagnostics
from app.services.music_service import MusicGenerationService
from app.services.presets import presets_manager
from app.services.project_service import ProjectService
from app.services.queue_worker import get_worker
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_music_service(
    session: AsyncSession = Depends(get_db_session),
) -> MusicGenerationService:
    return MusicGenerationService(session)


async def get_project_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectService:
    return ProjectService(session)


def _count_output_files() -> int:
    return len(list(settings.OUTPUTS_DIR.glob("*.mp3"))) + len(
        list(settings.OUTPUTS_DIR.glob("*.wav"))
    )


def _release_info() -> dict:
    return {
        "environment": settings.APP_ENV,
        "version": settings.RELEASE_VERSION,
        "sha": settings.RELEASE_SHA,
    }


@router.get("/health")
async def health_check() -> SystemStatus:
    database = {"ok": False, "error": "unknown"}
    total_projects = 0
    try:
        database = await check_db_connection()
    except Exception as exc:
        database = {"ok": False, "error": str(exc)}

    if database.get("ok"):
        try:
            async with async_session_factory() as session:
                project_service = ProjectService(session)
                total_projects = await project_service.count_projects()
        except Exception as exc:
            logger.warning("health_project_count_failed", error=str(exc))

    diag = get_engine_diagnostics()
    return SystemStatus(
        status="ok" if database["ok"] else "degraded",
        engine_type=settings.ENGINE_MODE,
        engine_name=settings.ENGINE_MODE,
        engine_ready=bool(diag.get("ready", False)),
        version=settings.API_VERSION,
        data_dir_ok=True,
        total_projects=total_projects,
        total_outputs=_count_output_files(),
        release=_release_info(),
    )


@router.get("/api/worker/status")
async def get_worker_status():
    """Get the current worker status."""
    worker = get_worker()
    if worker is None:
        return {"running": False, "worker_id": None}
    return worker.get_status()


@router.get("/api/version")
async def get_version() -> dict:
    """Expose release metadata for deploy validation."""
    return {
        "success": True,
        "data": {
            "api_version": settings.API_VERSION,
            "release": _release_info(),
        },
    }


@router.get("/api/diagnostics")
async def get_diagnostics() -> DiagnosticsResponse:
    database = {"ok": False, "error": "unknown"}
    job_counts = {}
    try:
        database = await check_db_connection()
    except Exception as exc:
        database = {"ok": False, "error": str(exc)}

    if database.get("ok"):
        try:
            async with async_session_factory() as session:
                job_repo = JobRepository(session)
                job_counts = await job_repo.get_status_counts()
        except Exception as exc:
            logger.warning("diagnostics_job_counts_failed", error=str(exc))
            job_counts = {"error": str(exc)}

    worker = get_worker()
    return DiagnosticsResponse(
        status="ok" if database["ok"] else "degraded",
        version=settings.API_VERSION,
        engine_type=settings.ENGINE_MODE,
        engine=get_engine_diagnostics(),
        database=database,
        jobs=job_counts,
        worker=worker.get_status() if worker else {"running": False, "worker_id": None},
        runtime=runtime_stats.snapshot(),
        release=_release_info(),
        storage={
            "outputs_dir": str(settings.OUTPUTS_DIR),
            "outputs_total": _count_output_files(),
            "exports_dir": str(settings.EXPORTS_DIR),
            "exports_total": len(list(settings.EXPORTS_DIR.glob("*"))),
        },
        logs={
            "directory": str(settings.LOGS_DIR),
            "app_log": str(settings.LOGS_DIR / "app.log"),
            "error_log": str(settings.LOGS_DIR / "error.log"),
        },
    )


# ---------------------------------------------------------------------------
# Engine status & mode switching
# ---------------------------------------------------------------------------

class EngineModeRequest(BaseModel):
    mode: str  # "mock" | "ace"


@router.get("/api/engine/status")
async def get_engine_status() -> dict:
    """Current engine mode with readiness details for the UI."""
    diag = get_engine_diagnostics()
    return {
        "success": True,
        "data": {
            "current_mode": settings.ENGINE_MODE,
            "ready": diag.get("ready", False),
            "details": diag.get("details", {}),
        },
    }


@router.post("/api/engine/mode")
async def set_engine_mode(body: EngineModeRequest) -> dict:
    """Switch ENGINE_MODE immediately (hot-swap) and persist to .env."""
    allowed = {"mock", "ace"}
    if body.mode not in allowed:
        raise HTTPException(status_code=400, detail=f"Ungültiger Modus. Erlaubt: {allowed}")

    # Hot-swap in memory first – get_engine_adapter() reads settings.ENGINE_MODE
    # dynamically so this takes effect for all subsequent requests immediately.
    settings.ENGINE_MODE = body.mode

    # Persist to .env so the change survives a restart.
    env_path = settings.PROJECT_ROOT / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        content = re.sub(r"(?m)^ENGINE_MODE=.*$", f"ENGINE_MODE={body.mode}", content)
        content = re.sub(r"(?m)^ENGINE_TYPE=.*$", f"ENGINE_TYPE={body.mode}", content)
        env_path.write_text(content, encoding="utf-8")

    mode_label = "ACE-Step (Lokal)" if body.mode == "ace" else "Mock (Test-Modus)"
    return {
        "success": True,
        "data": {
            "mode": body.mode,
            "requires_restart": False,
            "message": f"Engine sofort auf '{mode_label}' umgeschaltet.",
        },
    }


# ---------------------------------------------------------------------------
# Engine profiles
# ---------------------------------------------------------------------------

def _load_profiles() -> list[dict]:
    profiles_dir = settings.PROJECT_ROOT / "data" / "profiles"
    profiles = []
    if profiles_dir.exists():
        for p in sorted(profiles_dir.glob("*.json")):
            try:
                import json
                profiles.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                pass
    return profiles


@router.get("/api/engine/profiles")
async def get_engine_profiles() -> dict:
    """Return all configured engine profiles."""
    profiles = _load_profiles()
    return {
        "success": True,
        "data": {
            "active_profile": settings.ENGINE_PROFILE,
            "profiles": profiles,
        },
    }


class EngineProfileRequest(BaseModel):
    profile_id: str


@router.post("/api/engine/profile")
async def set_engine_profile(body: EngineProfileRequest) -> dict:
    """Switch ENGINE_PROFILE in .env. Requires backend restart."""
    profiles = _load_profiles()
    valid_ids = {p["id"] for p in profiles}
    if body.profile_id not in valid_ids:
        raise HTTPException(status_code=400, detail=f"Unbekanntes Profil '{body.profile_id}'. Verfügbar: {sorted(valid_ids)}")

    profile = next(p for p in profiles if p["id"] == body.profile_id)
    if not profile.get("available", False):
        raise HTTPException(status_code=400, detail=f"Profil '{body.profile_id}' ist noch nicht verfügbar.")

    env_path = settings.PROJECT_ROOT / ".env"
    if not env_path.exists():
        raise HTTPException(status_code=500, detail=".env nicht gefunden")

    content = env_path.read_text(encoding="utf-8")
    if re.search(r"(?m)^ENGINE_PROFILE=", content):
        content = re.sub(r"(?m)^ENGINE_PROFILE=.*$", f"ENGINE_PROFILE={body.profile_id}", content)
    else:
        content += f"\nENGINE_PROFILE={body.profile_id}\n"
    env_path.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "data": {
            "profile_id": body.profile_id,
            "requires_restart": True,
            "message": f"Profil auf '{body.profile_id}' gesetzt. Backend neu starten um die Änderung zu aktivieren.",
        },
    }


@router.get("/api/presets/track")
async def get_track_presets(category: Optional[str] = Query(None)) -> dict:
    presets = presets_manager.get_track_presets(category=category)
    return {"success": True, "data": {"total": len(presets), "presets": presets}}


@router.get("/api/presets/beat")
async def get_beat_presets(category: Optional[str] = Query(None)) -> dict:
    presets = presets_manager.get_beat_presets(category=category)
    return {"success": True, "data": {"total": len(presets), "presets": presets}}


@router.get("/api/presets/track/{preset_id}")
async def get_track_preset(preset_id: str) -> dict:
    preset = presets_manager.get_track_preset(preset_id)
    if not preset:
        raise NotFoundError(
            "Preset nicht gefunden",
            code="track_preset_not_found",
            details={"preset_id": preset_id},
        )
    return {"success": True, "data": preset}


@router.get("/api/presets/beat/{preset_id}")
async def get_beat_preset(preset_id: str) -> dict:
    preset = presets_manager.get_beat_preset(preset_id)
    if not preset:
        raise NotFoundError(
            "Preset nicht gefunden",
            code="beat_preset_not_found",
            details={"preset_id": preset_id},
        )
    return {"success": True, "data": preset}


@router.post("/api/track/generate")
async def generate_track(
    request: TrackGenerationRequest,
    music_service: MusicGenerationService = Depends(get_music_service),
) -> dict:
    request_data = request.model_dump()
    if request_data.get("preset_id"):
        request_data = presets_manager.apply_track_preset(
            request_data["preset_id"], request_data
        )
    job_id = await music_service.generate_track(request_data)
    return {
        "success": True,
        "message": "Track-Generierung gestartet",
        "data": {
            "job_id": job_id,
            "status": "queued",
            "title": request.title,
            "preset_used": request_data.get("preset_id"),
        },
    }


@router.post("/api/beat/generate")
async def generate_beat(
    request: BeatGenerationRequest,
    music_service: MusicGenerationService = Depends(get_music_service),
) -> dict:
    request_data = request.model_dump()
    if request_data.get("preset_id"):
        request_data = presets_manager.apply_beat_preset(
            request_data["preset_id"], request_data
        )
    job_id = await music_service.generate_beat(request_data)
    return {
        "success": True,
        "message": "Beat-Generierung gestartet",
        "data": {
            "job_id": job_id,
            "status": "queued",
            "title": request.title,
            "preset_used": request_data.get("preset_id"),
        },
    }


@router.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    music_service: MusicGenerationService = Depends(get_music_service),
) -> dict:
    job = await music_service.get_job_status(job_id)
    if not job:
        raise NotFoundError(
            "Job nicht gefunden", code="job_not_found", details={"job_id": job_id}
        )
    return {"success": True, "data": job}


@router.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = Query(None),
    music_service: MusicGenerationService = Depends(get_music_service),
) -> dict:
    jobs = await (
        music_service.get_jobs_by_status(status)
        if status
        else music_service.list_jobs()
    )
    return {"success": True, "data": {"total": len(jobs), "jobs": jobs}}


@router.post("/api/projects")
async def save_project(
    request: SaveProjectRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    project = await project_service.create_project(
        name=request.name,
        project_type=request.project_type,
        genre=request.genre,
        mood=request.mood,
        duration=request.duration,
        parameters=request.parameters or request.metadata or {},
        output_file=request.output_file,
        metadata=request.metadata,
        preset_used=request.preset_used,
        lyrics=request.lyrics,
        negative_prompts=request.negative_prompts,
        last_job_id=(request.metadata or {}).get("source_job_id"),
    )
    return {"success": True, "message": "Projekt gespeichert", "data": project}


@router.get("/api/projects")
async def list_projects(
    project_type: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    projects = await project_service.list_projects(
        project_type=project_type, genre=genre
    )
    return {"success": True, "data": {"total": len(projects), "projects": projects}}


@router.get("/api/projects/search")
async def search_projects(
    q: Optional[str] = Query(None, description="Suchbegriff"),
    project_type: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    projects = await project_service.search_projects(
        search_term=q,
        project_type=project_type,
        genre=genre,
    )
    return {"success": True, "data": {"total": len(projects), "projects": projects}}


@router.get("/api/projects/{project_id}")
async def get_project(
    project_id: str, project_service: ProjectService = Depends(get_project_service)
) -> dict:
    project = await project_service.get_project(project_id)
    if not project:
        raise NotFoundError(
            "Projekt nicht gefunden",
            code="project_not_found",
            details={"project_id": project_id},
        )
    return {"success": True, "data": project}


@router.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    success = await project_service.delete_project(project_id)
    if not success:
        raise NotFoundError(
            "Projekt nicht gefunden",
            code="project_not_found",
            details={"project_id": project_id},
        )
    return {"success": True, "message": "Projekt gelöscht"}


@router.post("/api/export/{job_id}")
async def export_audio(
    job_id: str,
    export_name: str,
    project_id: Optional[str] = None,
    music_service: MusicGenerationService = Depends(get_music_service),
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    job = await music_service.get_job_status(job_id)
    if not job or job.get("status") != "completed":
        raise InvalidStateError(
            "Job nicht abgeschlossen",
            code="job_not_completed",
            details={"job_id": job_id},
        )

    source_file = Path(job.get("result_file") or "")
    if not source_file.exists():
        raise NotFoundError(
            "Audiodatei nicht gefunden",
            code="job_audio_not_found",
            details={"job_id": job_id},
        )

    export_filename = f"{export_name}_{source_file.name}"
    export_path = settings.EXPORTS_DIR / export_filename
    shutil.copy2(source_file, export_path)

    if project_id:
        await project_service.add_export(project_id, export_filename, str(export_path))

    logger.info(
        "job_export_completed",
        job_id=job_id,
        export_filename=export_filename,
        project_id=project_id,
    )
    return {
        "success": True,
        "message": "Export abgeschlossen",
        "data": {
            "filename": export_filename,
            "path": str(export_path),
            "public_url": f"/exports/{export_filename}",
        },
    }


@router.post("/api/projects/{project_id}/export")
async def export_project_audio(
    project_id: str,
    export_name: Optional[str] = None,
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    project = await project_service.get_project(project_id)
    if not project:
        raise NotFoundError(
            "Projekt nicht gefunden",
            code="project_not_found",
            details={"project_id": project_id},
        )

    source_path = Path(project.get("output_file") or "")
    if not source_path.exists():
        raise NotFoundError(
            "Audiodatei nicht gefunden",
            code="project_audio_not_found",
            details={"project_id": project_id},
        )

    safe_name = (export_name or project.get("name", "export")).replace(" ", "_")
    export_filename = f"{safe_name}_{source_path.name}"
    export_path = settings.EXPORTS_DIR / export_filename
    shutil.copy2(source_path, export_path)
    await project_service.add_export(project_id, export_filename, str(export_path))
    logger.info(
        "project_export_completed",
        project_id=project_id,
        export_filename=export_filename,
    )

    return {
        "success": True,
        "message": "Export abgeschlossen",
        "data": {
            "filename": export_filename,
            "path": str(export_path),
            "public_url": f"/exports/{export_filename}",
        },
    }


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    return await get_output(filename)


@router.get("/exports/{filename}")
async def get_export(filename: str):
    file_path = settings.EXPORTS_DIR / filename
    if not file_path.exists():
        raise NotFoundError(
            "Export nicht gefunden",
            code="export_not_found",
            details={"filename": filename},
        )
    media_type = "audio/wav" if filename.lower().endswith(".wav") else "audio/mpeg"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)


@router.get("/outputs/{filename}")
async def get_output(filename: str):
    file_path = settings.OUTPUTS_DIR / filename
    if not file_path.exists():
        raise NotFoundError(
            "Output nicht gefunden",
            code="output_not_found",
            details={"filename": filename},
        )
    media_type = "audio/wav" if filename.lower().endswith(".wav") else "audio/mpeg"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)
