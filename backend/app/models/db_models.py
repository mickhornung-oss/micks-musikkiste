"""SQLAlchemy ORM models for Micks Musikkiste."""

import enum
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now_naive() -> datetime:
    """Return a UTC timestamp compatible with the current naive DB schema."""
    return datetime.now(UTC).replace(tzinfo=None)


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectType(str, enum.Enum):
    TRACK = "track"
    BEAT = "beat"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING.value)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_file: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    preset_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    engine: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # Queue-specific fields
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "progress": self.progress,
            "error": self.error,
            "result_file": self.result_file,
            "metadata": self.metadata_json,
            "preset_used": self.preset_used,
            "engine": self.engine,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "heartbeat_at": self.heartbeat_at.isoformat() if self.heartbeat_at else None,
            "worker_id": self.worker_id,
            "last_error": self.last_error,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

    def calculate_retry_delay(self) -> timedelta:
        """Calculate exponential backoff delay for retries."""
        base_delay = 5  # seconds
        max_delay = 300  # seconds (5 minutes)
        delay = min(base_delay * (2 ** self.attempt_count), max_delay)
        return timedelta(seconds=delay)

    def should_retry(self) -> bool:
        """Check if job should be retried."""
        return self.attempt_count < self.max_attempts


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), nullable=False)
    mood: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    output_file: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preset_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lyrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    negative_prompts: Mapped[list[Any]] = mapped_column(JSON, default=list)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exports: Mapped[list[Any]] = mapped_column(JSON, default=list)
    last_export_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_job_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    last_job: Mapped[Optional["Job"]] = relationship("Job", foreign_keys=[last_job_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, ProjectType) else self.type,
            "genre": self.genre,
            "mood": self.mood,
            "duration": self.duration,
            "output_file": self.output_file,
            "preset_used": self.preset_used,
            "lyrics": self.lyrics,
            "negative_prompts": self.negative_prompts,
            "parameters": self.parameters,
            "metadata": self.metadata_json,
            "notes": self.notes,
            "exports": self.exports,
            "last_export_at": self.last_export_at.isoformat() if self.last_export_at else None,
            "last_job_id": self.last_job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
