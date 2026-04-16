"""Mock engine implementation used for local demo/testing."""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict

from app.config import settings

from .base import EngineAdapter


class MockEngineAdapter(EngineAdapter):
    name = "mock"

    def diagnostics(self) -> dict:
        return {
            "name": self.name,
            "mode": "mock",
            "ready": True,
            "details": {
                "mock_delay_seconds": settings.ENGINE_MOCK_DELAY,
                "outputs_dir": str(settings.OUTPUTS_DIR),
            },
        }

    async def generate_track_audio(self, payload: Dict[str, Any]) -> str:
        await asyncio.sleep(settings.ENGINE_MOCK_DELAY)
        output_filename = f"track_{uuid.uuid4().hex[:8]}.mp3"
        output_path = settings.OUTPUTS_DIR / output_filename
        output_path.write_bytes(
            b"MOCK_AUDIO_TRACK_" + payload.get("title", "track").encode()
        )
        return str(output_path)

    async def generate_beat_audio(self, payload: Dict[str, Any]) -> str:
        await asyncio.sleep(settings.ENGINE_MOCK_DELAY)
        output_filename = f"beat_{uuid.uuid4().hex[:8]}.mp3"
        output_path = settings.OUTPUTS_DIR / output_filename
        output_path.write_bytes(
            b"MOCK_AUDIO_BEAT_" + payload.get("title", "beat").encode()
        )
        return str(output_path)
