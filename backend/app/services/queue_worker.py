"""Queue worker for processing jobs from the database."""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

UTC = timezone.utc

from app.config import settings
from app.database import async_session_factory
from app.logging_config import logger
from app.models.db_models import Job, JobStatus
from app.repositories import JobRepository
from app.services.engines import get_engine_adapter
from sqlalchemy.ext.asyncio import AsyncSession


class QueueWorker:
    """Internal async worker for processing jobs from the database queue."""

    def __init__(self):
        self.worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        self.engine = get_engine_adapter()
        self._running = False
        self._heartbeat_task = None
        self._stale_job_task = None
        self._worker_task = None
        self._current_job = None
        self._current_job_id: Optional[str] = None
        self._shutdown_event = asyncio.Event()

    @staticmethod
    def _utc_now() -> datetime:
        """Return UTC timestamps compatible with the current naive DB schema."""
        return datetime.now(UTC).replace(tzinfo=None)

    async def start(self):
        """Start the worker loop."""
        if self._running:
            logger.warning("worker_already_running", worker_id=self.worker_id)
            return

        self._running = True
        self._shutdown_event.clear()
        logger.info(
            "worker_starting", worker_id=self.worker_id, mode=settings.ENGINE_MODE
        )

        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._stale_job_task = asyncio.create_task(self._stale_job_loop())
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self, timeout: float = 30.0):
        """Stop the worker gracefully."""
        if not self._running:
            return

        logger.info("worker_stopping", worker_id=self.worker_id)
        self._running = False
        self._shutdown_event.set()

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._stale_job_task:
            self._stale_job_task.cancel()

        # Wait for current job to finish or timeout
        if self._current_job:
            try:
                await asyncio.wait_for(self._current_job, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("worker_shutdown_timeout", worker_id=self.worker_id)

        # Wait for worker/background tasks to finish
        tasks = [
            t
            for t in [self._worker_task, self._heartbeat_task, self._stale_job_task]
            if t and not t.done()
        ]
        if tasks:
            await asyncio.wait(tasks, timeout=5.0)

        logger.info("worker_stopped", worker_id=self.worker_id)

    async def _worker_loop(self):
        """Main worker loop for claiming and processing jobs."""
        logger.info("worker_loop_started", worker_id=self.worker_id)

        while self._running:
            try:
                async with async_session_factory() as session:
                    job_repo = JobRepository(session)

                    # Claim next job
                    job = await job_repo.claim_next_job(self.worker_id)

                    if job:
                        self._current_job = asyncio.create_task(
                            self._process_job(job, job_repo, session)
                        )
                        try:
                            await self._current_job
                        finally:
                            self._current_job = None
                    else:
                        # No job available, wait before next poll
                        await asyncio.sleep(settings.WORKER_POLL_INTERVAL)

            except asyncio.CancelledError:
                logger.info("worker_loop_cancelled", worker_id=self.worker_id)
                break
            except Exception:
                logger.exception("worker_loop_error", worker_id=self.worker_id)
                await asyncio.sleep(1.0)  # Brief pause before retry

        logger.info("worker_loop_stopped", worker_id=self.worker_id)

    async def _process_job(
        self, job: Job, job_repo: JobRepository, session: AsyncSession
    ):
        """Process a single job."""
        job_id = job.id
        self._current_job_id = job_id
        logger.info(
            "job_processing_start",
            job_id=job_id,
            kind=job.type,
            attempt=job.attempt_count,
            worker_id=self.worker_id,
        )

        try:
            # Update progress
            job.progress = 10
            await job_repo.update_status(job_id, JobStatus.RUNNING, progress=10)
            await session.commit()

            # Generate audio
            if job.type == "track":
                result_file = await self.engine.generate_track_audio(job.metadata_json)
            else:
                result_file = await self.engine.generate_beat_audio(job.metadata_json)

            # Validate result
            result_path = Path(result_file)
            if not result_path.exists() or result_path.stat().st_size == 0:
                raise RuntimeError("Engine produzierte keine gültige Audiodatei")

            # Mark as completed
            await job_repo.update_status(
                job_id, JobStatus.COMPLETED, progress=100, result_file=str(result_path)
            )
            job.finished_at = self._utc_now()
            job.last_error = None
            await session.commit()

            logger.info(
                "job_processing_completed",
                job_id=job_id,
                kind=job.type,
                worker_id=self.worker_id,
            )

        except asyncio.CancelledError:
            logger.warning("job_processing_cancelled", job_id=job_id)
            # Job will be recovered on next startup

        except Exception as exc:
            logger.exception("job_processing_failed", job_id=job_id)

            # Check if job should be retried
            if job.should_retry():
                # Schedule for retry
                retry_delay = job.calculate_retry_delay()
                scheduled_at = self._utc_now() + retry_delay

                await job_repo.update_status(job_id, JobStatus.QUEUED, error=str(exc))
                # Update scheduled_at directly
                job.status = JobStatus.QUEUED
                job.progress = 0
                job.scheduled_at = scheduled_at
                job.claimed_at = None
                job.heartbeat_at = None
                job.worker_id = None
                job.last_error = str(exc)
                await session.commit()

                logger.info(
                    "job_scheduled_for_retry",
                    job_id=job_id,
                    attempt=job.attempt_count,
                    scheduled_at=scheduled_at.isoformat(),
                )
            else:
                # Mark as permanently failed
                await job_repo.update_status(job_id, JobStatus.FAILED, error=str(exc))
                job.scheduled_at = None
                job.claimed_at = None
                job.heartbeat_at = None
                job.worker_id = None
                job.last_error = str(exc)
                job.finished_at = self._utc_now()
                await session.commit()

                logger.warning(
                    "job_failed_permanently",
                    job_id=job_id,
                    attempt=job.attempt_count,
                    error=str(exc),
                )
        finally:
            self._current_job_id = None

    async def _heartbeat_loop(self):
        """Background loop for updating heartbeats."""
        logger.info("heartbeat_loop_started", worker_id=self.worker_id)

        while self._running:
            try:
                await asyncio.sleep(settings.WORKER_HEARTBEAT_INTERVAL)

                if self._current_job_id:
                    async with async_session_factory() as session:
                        job_repo = JobRepository(session)
                        await job_repo.update_heartbeat(
                            self._current_job_id, self.worker_id
                        )

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("heartbeat_loop_error", worker_id=self.worker_id)

        logger.info("heartbeat_loop_stopped", worker_id=self.worker_id)

    async def _stale_job_loop(self):
        """Background loop for releasing stale jobs."""
        logger.info("stale_job_loop_started", worker_id=self.worker_id)

        while self._running:
            try:
                await asyncio.sleep(
                    settings.WORKER_STALE_TIMEOUT / 2
                )  # Check twice per timeout period

                async with async_session_factory() as session:
                    job_repo = JobRepository(session)
                    released = await job_repo.release_stale_jobs(
                        settings.WORKER_STALE_TIMEOUT, self._current_job_id
                    )
                    await session.commit()

                    if released > 0:
                        logger.info(
                            "stale_jobs_released",
                            worker_id=self.worker_id,
                            count=released,
                        )

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("stale_job_loop_error", worker_id=self.worker_id)

        logger.info("stale_job_loop_stopped", worker_id=self.worker_id)

    def get_status(self) -> dict:
        """Get worker status for diagnostics."""
        return {
            "worker_id": self.worker_id,
            "running": self._running,
            "engine": self.engine.name,
            "current_job_id": self._current_job_id,
            "has_current_job": self._current_job is not None,
            "current_job_processing": (
                self._current_job is not None and not self._current_job.done()
                if self._current_job
                else False
            ),
        }


# Global worker instance
_worker: Optional[QueueWorker] = None


def get_worker() -> Optional[QueueWorker]:
    """Get the global worker instance."""
    return _worker


async def start_worker() -> Optional[QueueWorker]:
    """Start the global worker instance."""
    global _worker

    if not settings.WORKER_ENABLED:
        logger.info("worker_disabled_in_config")
        return None

    if _worker is None:
        _worker = QueueWorker()
        await _worker.start()

    return _worker


async def stop_worker():
    """Stop the global worker instance."""
    global _worker

    if _worker is not None:
        await _worker.stop()
        _worker = None
