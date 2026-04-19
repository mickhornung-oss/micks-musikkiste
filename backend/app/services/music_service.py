"""Music generation service with database integration."""

import uuid
from pathlib import Path
from typing import Optional

from app.config import settings
from app.errors import InvalidStateError
from app.logging_config import logger
from app.models.db_models import Job, JobStatus
from app.observability import runtime_stats
from app.repositories import JobRepository
from app.services.engines import get_engine_adapter
from sqlalchemy.ext.asyncio import AsyncSession


class MusicGenerationService:
    """Handle job lifecycle with database persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = JobRepository(session)
        self.engine = get_engine_adapter()

    async def generate_track(self, request_data: dict) -> str:
        job_id = str(uuid.uuid4())
        clean = self._normalize_request(request_data)
        logger.info(
            "job_generation_queued",
            job_id=job_id,
            kind="track",
            title=clean.get("title"),
        )
        job = Job(
            id=job_id,
            type="track",
            title=clean.get("title", "Track"),
            status=JobStatus.QUEUED,
            progress=0,
            metadata_json=clean,
            preset_used=clean.get("preset_id"),
            engine=self.engine.name,
            max_attempts=settings.WORKER_MAX_RETRIES,
        )
        await self.job_repo.create(job)
        await self.session.commit()
        runtime_stats.record_job_started()
        return job_id

    async def generate_beat(self, request_data: dict) -> str:
        job_id = str(uuid.uuid4())
        clean = self._normalize_request(request_data)
        logger.info(
            "job_generation_queued",
            job_id=job_id,
            kind="beat",
            title=clean.get("title"),
        )
        job = Job(
            id=job_id,
            type="beat",
            title=clean.get("title", "Beat"),
            status=JobStatus.QUEUED,
            progress=0,
            metadata_json=clean,
            preset_used=clean.get("preset_id"),
            engine=self.engine.name,
            max_attempts=settings.WORKER_MAX_RETRIES,
        )
        await self.job_repo.create(job)
        await self.session.commit()
        runtime_stats.record_job_started()
        return job_id

    @staticmethod
    def _normalize_request(data: dict) -> dict:
        normalized = dict(data or {})
        try:
            duration = int(normalized.get("duration", 30))
        except Exception:
            duration = 30
        # Respect the engine's configured max duration (default 300 s / 5 min).
        # Do NOT hardcap at 60 – that silently discards the user's choice.
        max_dur = settings.ACE_STEP_MAX_DURATION  # default 300
        duration = max(5, min(duration, max_dur))
        normalized["duration"] = duration
        normalized["duration_effective"] = duration
        normalized["duration_requested"] = (
            data.get("duration") if isinstance(data, dict) else duration
        )
        return normalized

    async def get_job_status(self, job_id: str) -> Optional[dict]:
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return None
        if job.status == JobStatus.COMPLETED.value:
            result = job.result_file
            if not result or not Path(result).exists():
                logger.warning(
                    "job_result_file_missing", job_id=job_id, result_file=result
                )
                await self.job_repo.update_status(
                    job_id, JobStatus.FAILED, error="Ergebnisdatei nicht vorhanden"
                )
                await self.session.commit()
                job = await self.job_repo.get_by_id(job_id)
        return job.to_dict() if job else None

    async def list_jobs(self, limit: Optional[int] = None) -> list:
        jobs = await self.job_repo.get_all(limit=limit)
        return [job.to_dict() for job in jobs]

    async def get_jobs_by_status(self, status: str) -> list:
        try:
            job_status = JobStatus(status) if isinstance(status, str) else status
        except ValueError as exc:
            raise InvalidStateError(
                "Unbekannter Job-Status",
                code="invalid_job_status",
                details={"status": status},
            ) from exc
        jobs = await self.job_repo.get_by_status(job_status)
        return [job.to_dict() for job in jobs]
