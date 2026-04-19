"""Mock engine implementation used for local demo/testing."""

import array
import asyncio
import math
import uuid
import wave
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from app.config import settings

from .base import EngineAdapter


def _test_tone_wav(duration_seconds: float = 1.0, sample_rate: int = 8000, frequency: float = 440.0) -> bytes:
    """Return a WAV file with an audible 440 Hz sine-wave test tone.

    Using a real tone makes it immediately obvious that audio was generated
    and that playback works correctly, unlike silence which is indistinguishable
    from a broken player or missing file.
    """
    num_frames = int(sample_rate * duration_seconds)
    amplitude = 10000  # comfortable listening level, well below 16-bit clip
    fade = min(int(sample_rate * 0.15), max(num_frames // 4, 1))
    two_pi_f_over_sr = 2.0 * math.pi * frequency / sample_rate

    samples = array.array("h", [0] * num_frames)
    for i in range(num_frames):
        s = math.sin(two_pi_f_over_sr * i) * amplitude
        if i < fade:
            s *= i / fade
        elif i > num_frames - fade:
            s *= (num_frames - i) / fade
        samples[i] = int(s)

    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


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
                "note": "Demo mode – produces audible 440 Hz test-tone WAV files, no real AI audio",
            },
        }

    async def generate_track_audio(self, payload: Dict[str, Any]) -> str:
        await asyncio.sleep(settings.ENGINE_MOCK_DELAY)
        duration = max(1, min(int(payload.get("duration", 5) or 5), 300))
        output_filename = f"track_{uuid.uuid4().hex[:8]}.wav"
        output_path = settings.OUTPUTS_DIR / output_filename
        output_path.write_bytes(_test_tone_wav(duration_seconds=duration))
        return str(output_path)

    async def generate_beat_audio(self, payload: Dict[str, Any]) -> str:
        await asyncio.sleep(settings.ENGINE_MOCK_DELAY)
        duration = max(1, min(int(payload.get("duration", 5) or 5), 300))
        output_filename = f"beat_{uuid.uuid4().hex[:8]}.wav"
        output_path = settings.OUTPUTS_DIR / output_filename
        output_path.write_bytes(_test_tone_wav(duration_seconds=duration))
        return str(output_path)
