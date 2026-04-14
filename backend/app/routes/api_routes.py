"""Consolidated API routes with database-backed persistence."""

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import check_db_connection, get_db_session
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

router = APIRouter()


async def get_music_service(session: AsyncSession = Depends(get_db_session)) -> MusicGenerationService:
    return MusicGenerationService(session)


async def get_project_service(session: AsyncSession = Depends(get_db_session)) -> ProjectService:
    return ProjectService(session)


def _count_output_files() -> int:
    return len(list(settings.OUTPUTS_DIR.glob("*.mp3"))) + len(list(settings.OUTPUTS_DIR.glob("*.wav")))


@router.get("/health")
async def health_check(project_service: ProjectService = Depends(get_project_service)) -> SystemStatus:
    database = await check_db_connection()
    return SystemStatus(
        status="ok" if database["ok"] else "degraded",
        engine_type=settings.ENGINE_MODE,
        engine_name=settings.ENGINE_MODE,
        version=settings.API_VERSION,
        data_dir_ok=True,
        total_projects=await project_service.count_projects(),
        total_outputs=_count_output_files(),
    )


@router.get("/api/worker/status")
async def get_worker_status():
    """Get the current worker status."""
    worker = get_worker()
    if worker is None:
        return {"running": False, "worker_id": None}
    return worker.get_status()


@router.get("/api/diagnostics")
async def get_diagnostics(session: AsyncSession = Depends(get_db_session)) -> DiagnosticsResponse:
    job_repo = JobRepository(session)
    database = await check_db_connection()
    job_counts = await job_repo.get_status_counts()
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
        raise NotFoundError("Preset nicht gefunden", code="track_preset_not_found", details={"preset_id": preset_id})
    return {"success": True, "data": preset}


@router.get("/api/presets/beat/{preset_id}")
async def get_beat_preset(preset_id: str) -> dict:
    preset = presets_manager.get_beat_preset(preset_id)
    if not preset:
        raise NotFoundError("Preset nicht gefunden", code="beat_preset_not_found", details={"preset_id": preset_id})
    return {"success": True, "data": preset}


@router.post("/api/track/generate")
async def generate_track(
    request: TrackGenerationRequest,
    music_service: MusicGenerationService = Depends(get_music_service),
) -> dict:
    request_data = request.model_dump()
    if request_data.get("preset_id"):
        request_data = presets_manager.apply_track_preset(request_data["preset_id"], request_data)
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
        request_data = presets_manager.apply_beat_preset(request_data["preset_id"], request_data)
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
        raise NotFoundError("Job nicht gefunden", code="job_not_found", details={"job_id": job_id})
    return {"success": True, "data": job}


@router.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = Query(None),
    music_service: MusicGenerationService = Depends(get_music_service),
) -> dict:
    jobs = await (music_service.get_jobs_by_status(status) if status else music_service.list_jobs())
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
    projects = await project_service.list_projects(project_type=project_type, genre=genre)
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
async def get_project(project_id: str, project_service: ProjectService = Depends(get_project_service)) -> dict:
    project = await project_service.get_project(project_id)
    if not project:
        raise NotFoundError("Projekt nicht gefunden", code="project_not_found", details={"project_id": project_id})
    return {"success": True, "data": project}


@router.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> dict:
    success = await project_service.delete_project(project_id)
    if not success:
        raise NotFoundError("Projekt nicht gefunden", code="project_not_found", details={"project_id": project_id})
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
        raise InvalidStateError("Job nicht abgeschlossen", code="job_not_completed", details={"job_id": job_id})

    source_file = Path(job.get("result_file") or "")
    if not source_file.exists():
        raise NotFoundError("Audiodatei nicht gefunden", code="job_audio_not_found", details={"job_id": job_id})

    export_filename = f"{export_name}_{source_file.name}"
    export_path = settings.EXPORTS_DIR / export_filename
    shutil.copy2(source_file, export_path)

    if project_id:
        await project_service.add_export(project_id, export_filename, str(export_path))

    logger.info("job_export_completed", job_id=job_id, export_filename=export_filename, project_id=project_id)
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
        raise NotFoundError("Projekt nicht gefunden", code="project_not_found", details={"project_id": project_id})

    source_path = Path(project.get("output_file") or "")
    if not source_path.exists():
        raise NotFoundError("Audiodatei nicht gefunden", code="project_audio_not_found", details={"project_id": project_id})

    safe_name = (export_name or project.get("name", "export")).replace(" ", "_")
    export_filename = f"{safe_name}_{source_path.name}"
    export_path = settings.EXPORTS_DIR / export_filename
    shutil.copy2(source_path, export_path)
    await project_service.add_export(project_id, export_filename, str(export_path))
    logger.info("project_export_completed", project_id=project_id, export_filename=export_filename)

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
        raise NotFoundError("Export nicht gefunden", code="export_not_found", details={"filename": filename})
    media_type = "audio/wav" if filename.lower().endswith(".wav") else "audio/mpeg"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)


@router.get("/outputs/{filename}")
async def get_output(filename: str):
    file_path = settings.OUTPUTS_DIR / filename
    if not file_path.exists():
        raise NotFoundError("Output nicht gefunden", code="output_not_found", details={"filename": filename})
    media_type = "audio/wav" if filename.lower().endswith(".wav") else "audio/mpeg"
    return FileResponse(path=file_path, media_type=media_type, filename=filename)
