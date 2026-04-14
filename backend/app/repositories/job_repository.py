"""Repository for job database operations."""

from datetime import UTC, datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import logger
from app.models.db_models import Job, JobStatus


class JobRepository:
    """Persist and query generation jobs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _utc_now() -> datetime:
        """Return UTC timestamps compatible with the current naive DB schema."""
        return datetime.now(UTC).replace(tzinfo=None)

    async def create(self, job: Job) -> Job:
        try:
            self.session.add(job)
            await self.session.flush()
            await self.session.refresh(job)
            logger.info("job_repo_created", job_id=job.id, job_type=job.type, status=job.status)
            return job
        except Exception:
            logger.exception("job_repo_create_failed", job_id=job.id, job_type=job.type)
            raise

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        try:
            result = await self.session.execute(select(Job).where(Job.id == job_id))
            return result.scalar_one_or_none()
        except Exception:
            logger.exception("job_repo_get_failed", job_id=job_id)
            return None

    async def get_all(self, limit: Optional[int] = None) -> List[Job]:
        try:
            query = select(Job).order_by(Job.created_at.desc())
            if limit:
                query = query.limit(limit)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception:
            logger.exception("job_repo_list_failed", limit=limit)
            return []

    async def get_by_status(self, status: JobStatus) -> List[Job]:
        try:
            result = await self.session.execute(
                select(Job).where(Job.status == status.value).order_by(Job.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception:
            logger.exception("job_repo_status_list_failed", status=status.value)
            return []

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: Optional[int] = None,
        error: Optional[str] = None,
        result_file: Optional[str] = None,
    ) -> Optional[Job]:
        try:
            status_value = status.value if isinstance(status, JobStatus) else status
            values = {"status": status_value}
            if status_value in {JobStatus.RUNNING.value, JobStatus.COMPLETED.value}:
                values["error"] = None
            if progress is not None:
                values["progress"] = progress
            if error is not None:
                values["error"] = error
            if result_file is not None:
                values["result_file"] = result_file

            result = await self.session.execute(
                update(Job).where(Job.id == job_id).values(**values).returning(Job)
            )
            job = result.scalar_one_or_none()
            if job:
                logger.info(
                    "job_repo_status_updated",
                    job_id=job_id,
                    status=status_value,
                    progress=progress,
                    has_result_file=bool(result_file),
                    has_error=bool(error),
                )
            return job
        except Exception:
            logger.exception("job_repo_status_update_failed", job_id=job_id, status=status_value)
            return None

    async def delete(self, job_id: str) -> bool:
        try:
            job = await self.get_by_id(job_id)
            if not job:
                return False
            await self.session.delete(job)
            logger.info("job_repo_deleted", job_id=job_id)
            return True
        except Exception:
            logger.exception("job_repo_delete_failed", job_id=job_id)
            return False

    async def count_by_status(self, status: JobStatus) -> int:
        try:
            result = await self.session.execute(select(func.count(Job.id)).where(Job.status == status.value))
            return result.scalar() or 0
        except Exception:
            logger.exception("job_repo_count_failed", status=status.value)
            return 0

    async def get_status_counts(self) -> dict[str, int]:
        """Count jobs by status for diagnostics."""
        try:
            result = await self.session.execute(select(Job.status, func.count(Job.id)).group_by(Job.status))
            counts = {status: count for status, count in result.all()}
            return {job_status.value: counts.get(job_status.value, 0) for job_status in JobStatus}
        except Exception:
            logger.exception("job_repo_status_counts_failed")
            return {job_status.value: 0 for job_status in JobStatus}

    async def claim_next_job(self, worker_id: str) -> Optional[Job]:
        """Claim the next queued job using SELECT FOR UPDATE SKIP LOCKED."""
        try:
            now = self._utc_now()
            result = await self.session.execute(
                select(Job)
                .where(
                    Job.status == JobStatus.QUEUED.value,
                    (Job.scheduled_at.is_(None) | (Job.scheduled_at <= now))
                )
                .order_by(Job.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            job = result.scalar_one_or_none()
            if job:
                job.status = JobStatus.CLAIMED.value
                job.worker_id = worker_id
                job.claimed_at = now
                job.heartbeat_at = now
                job.attempt_count += 1
                await self.session.flush()
                logger.info(
                    "job_repo_claimed",
                    job_id=job.id,
                    worker_id=worker_id,
                    attempt_count=job.attempt_count
                )
            return job
        except Exception:
            logger.exception("job_repo_claim_failed", worker_id=worker_id)
            return None

    async def update_heartbeat(self, job_id: str, worker_id: str) -> bool:
        """Update heartbeat timestamp for a claimed job."""
        try:
            result = await self.session.execute(
                update(Job)
                .where(
                    Job.id == job_id,
                    Job.worker_id == worker_id,
                    Job.status.in_([JobStatus.CLAIMED.value, JobStatus.RUNNING.value])
                )
                .values(heartbeat_at=self._utc_now())
                .returning(Job)
            )
            job = result.scalar_one_or_none()
            if job:
                logger.debug("job_repo_heartbeat_updated", job_id=job_id, worker_id=worker_id)
                return True
            return False
        except Exception:
            logger.exception("job_repo_heartbeat_failed", job_id=job_id, worker_id=worker_id)
            return False

    async def release_stale_jobs(self, timeout_seconds: float, current_job_id: str = None) -> int:
        """Release jobs that have been claimed too long without heartbeat.

        Args:
            timeout_seconds: Timeout in seconds before a job is considered stale
            current_job_id: ID of the job currently being processed (will not be released)
        """
        try:
            timeout_threshold = self._utc_now() - timedelta(seconds=timeout_seconds)

            # Get stale jobs
            result = await self.session.execute(
                select(Job).where(
                    Job.status.in_([JobStatus.CLAIMED.value, JobStatus.RUNNING.value]),
                    (
                        Job.heartbeat_at.is_(None)
                        | (Job.heartbeat_at < timeout_threshold)
                    )
                )
            )
            stale_jobs = list(result.scalars().all())

            released_count = 0
            for job in stale_jobs:
                # Skip the job currently being processed
                if current_job_id and job.id == current_job_id:
                    continue
                if job.should_retry():
                    # Retry the job
                    job.status = JobStatus.QUEUED
                    job.scheduled_at = self._utc_now() + job.calculate_retry_delay()
                    job.worker_id = None
                    job.claimed_at = None
                    job.heartbeat_at = None
                    released_count += 1
                    logger.info(
                        "job_repo_stale_released",
                        job_id=job.id,
                        attempt_count=job.attempt_count,
                        scheduled_at=job.scheduled_at
                    )
                else:
                    # Mark as failed after max retries
                    job.status = JobStatus.FAILED
                    job.finished_at = self._utc_now()
                    job.scheduled_at = None
                    job.claimed_at = None
                    job.heartbeat_at = None
                    job.worker_id = None
                    job.last_error = f"Job failed after {job.attempt_count} attempts (stale worker)"
                    logger.warning(
                        "job_repo_stale_failed",
                        job_id=job.id,
                        attempt_count=job.attempt_count
                    )

            await self.session.flush()
            return released_count
        except Exception:
            logger.exception("job_repo_release_stale_failed")
            return 0

    async def recover_stuck_jobs(self) -> dict[str, int]:
        """Recover jobs stuck in CLAIMED status on startup."""
        try:
            # Jobs stuck in CLAIMED for more than stale timeout
            timeout_threshold = self._utc_now() - timedelta(seconds=600)  # 10 minutes

            result = await self.session.execute(
                select(Job).where(
                    Job.status.in_([JobStatus.CLAIMED.value, JobStatus.RUNNING.value]),
                    (
                        Job.heartbeat_at.is_(None)
                        | (Job.heartbeat_at < timeout_threshold)
                    )
                )
            )
            stuck_jobs = list(result.scalars().all())

            recovered = 0
            failed = 0

            for job in stuck_jobs:
                if job.should_retry():
                    job.status = JobStatus.QUEUED
                    job.scheduled_at = self._utc_now() + job.calculate_retry_delay()
                    job.worker_id = None
                    job.claimed_at = None
                    job.heartbeat_at = None
                    recovered += 1
                    logger.info(
                        "job_repo_stuck_recovered",
                        job_id=job.id,
                        attempt_count=job.attempt_count
                    )
                else:
                    job.status = JobStatus.FAILED
                    job.finished_at = self._utc_now()
                    job.scheduled_at = None
                    job.claimed_at = None
                    job.heartbeat_at = None
                    job.worker_id = None
                    job.last_error = f"Job recovered as failed after {job.attempt_count} attempts (stuck worker)"
                    failed += 1
                    logger.warning(
                        "job_repo_stuck_failed",
                        job_id=job.id,
                        attempt_count=job.attempt_count
                    )

            await self.session.flush()
            logger.info(
                "job_repo_recovery_complete",
                total=len(stuck_jobs),
                recovered=recovered,
                failed=failed
            )
            return {"recovered": recovered, "failed": failed, "total": len(stuck_jobs)}
        except Exception:
            logger.exception("job_repo_recovery_failed")
            return {"recovered": 0, "failed": 0, "total": 0}
