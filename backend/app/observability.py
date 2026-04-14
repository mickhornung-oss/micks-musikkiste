"""Lightweight local observability helpers."""

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RuntimeStats:
    requests_total: int = 0
    requests_failed: int = 0
    jobs_started: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    last_error_code: str | None = None
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_request(self, *, failed: bool = False, error_code: str | None = None):
        with self._lock:
            self.requests_total += 1
            if failed:
                self.requests_failed += 1
            if error_code:
                self.last_error_code = error_code

    def record_job_started(self):
        with self._lock:
            self.jobs_started += 1

    def record_job_completed(self):
        with self._lock:
            self.jobs_completed += 1

    def record_job_failed(self):
        with self._lock:
            self.jobs_failed += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "requests_total": self.requests_total,
                "requests_failed": self.requests_failed,
                "jobs_started": self.jobs_started,
                "jobs_completed": self.jobs_completed,
                "jobs_failed": self.jobs_failed,
                "last_error_code": self.last_error_code,
            }


runtime_stats = RuntimeStats()
