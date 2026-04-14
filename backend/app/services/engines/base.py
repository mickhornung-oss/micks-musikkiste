"""Engine Adapter Interfaces for Micks Musikkiste"""

import abc
from typing import Any, Dict


class EngineAdapter(abc.ABC):
    """Abstract base for any music engine (mock or real)."""

    name: str = "base"

    @abc.abstractmethod
    async def generate_track_audio(self, payload: Dict[str, Any]) -> str:
        """Generate a full track. Returns absolute path to output file."""

    @abc.abstractmethod
    async def generate_beat_audio(self, payload: Dict[str, Any]) -> str:
        """Generate a beat. Returns absolute path to output file."""

    def diagnostics(self) -> dict:
        """Return lightweight local readiness information."""
        return {"name": self.name, "ready": True}
