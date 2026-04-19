"""MusicGen engine adapter für Micks Musikkiste V2.

STATUS: Vorbereitet, aber noch nicht aktivierbar ohne zusätzliche Dependencies.

Für die Aktivierung wird benötigt:
  pip install audiocraft  (Meta's MusicGen: torch + transformers + encodec)
  ODER
  pip install transformers accelerate  (HuggingFace MusicGen pipeline)

Das ist eine ~5 GB schwere Dependency (PyTorch + CUDA-Support).
Sie ist bewusst NICHT in requirements.txt, um das Basis-Setup leichtgewichtig zu halten.

Zur Aktivierung:
  1. pip install audiocraft
  2. ENGINE_MODE=musicgen in .env setzen
  3. MUSICGEN_MODEL in .env setzen (z.B. facebook/musicgen-medium)

Dieser Adapter wirft KEINE NotImplementedError-Attrappe.
Er prüft die Abhängigkeiten und gibt einen klaren, hilfreichen Fehlerstatus zurück.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from app.config import settings

from .base import EngineAdapter

logger = logging.getLogger(__name__)

# Wird beim ersten Import geprüft, nicht bei jedem Aufruf
_AUDIOCRAFT_AVAILABLE: bool | None = None
_TRANSFORMERS_AVAILABLE: bool | None = None


def _check_audiocraft() -> bool:
    global _AUDIOCRAFT_AVAILABLE
    if _AUDIOCRAFT_AVAILABLE is None:
        try:
            import audiocraft  # noqa: F401
            _AUDIOCRAFT_AVAILABLE = True
        except ImportError:
            _AUDIOCRAFT_AVAILABLE = False
    return _AUDIOCRAFT_AVAILABLE


def _check_transformers_musicgen() -> bool:
    """Prüft ob transformers + torch für MusicGen verfügbar sind."""
    global _TRANSFORMERS_AVAILABLE
    if _TRANSFORMERS_AVAILABLE is None:
        try:
            from transformers import AutoProcessor, MusicgenForConditionalGeneration  # noqa: F401
            import torch  # noqa: F401
            _TRANSFORMERS_AVAILABLE = True
        except ImportError:
            _TRANSFORMERS_AVAILABLE = False
    return _TRANSFORMERS_AVAILABLE


def _is_available() -> bool:
    return _check_audiocraft() or _check_transformers_musicgen()


class MusicGenAdapter(EngineAdapter):
    """MusicGen engine adapter.

    Nutzt Meta's MusicGen via audiocraft oder HuggingFace transformers.
    Beide Backends folgen derselben Adapter-Schnittstelle.

    Aktueller Status: vorbereitet, Dependencies noch nicht installiert.
    Aktivierung: siehe Modul-Docstring.
    """

    name = "musicgen"

    def __init__(self):
        self.model_id: str = getattr(settings, "MUSICGEN_MODEL", "facebook/musicgen-medium")
        self._model = None  # lazy-loaded beim ersten Generate

    def diagnostics(self) -> dict:
        audiocraft_ok = _check_audiocraft()
        transformers_ok = _check_transformers_musicgen()
        available = audiocraft_ok or transformers_ok

        backend = None
        if audiocraft_ok:
            backend = "audiocraft"
        elif transformers_ok:
            backend = "transformers"

        return {
            "name": self.name,
            "mode": "musicgen",
            "ready": available,
            "details": {
                "available": available,
                "backend": backend,
                "model_id": self.model_id,
                "audiocraft_installed": audiocraft_ok,
                "transformers_installed": transformers_ok,
                "activation_instructions": (
                    "Nicht verfügbar. Installation erforderlich: "
                    "pip install audiocraft  ODER  pip install transformers torch accelerate. "
                    "Danach ENGINE_MODE=musicgen in .env setzen."
                ) if not available else "Bereit",
            },
        }

    async def generate_track_audio(self, payload: Dict[str, Any]) -> str:
        return await self._generate(payload, kind="track")

    async def generate_beat_audio(self, payload: Dict[str, Any]) -> str:
        return await self._generate(payload, kind="beat")

    async def _generate(self, payload: Dict[str, Any], kind: str) -> str:
        if not _is_available():
            raise RuntimeError(
                "MusicGen-Engine ist nicht verfügbar. "
                "Bitte audiocraft oder transformers+torch installieren "
                "(siehe backend/app/services/engines/musicgen.py für Details). "
                "Alternativ: ENGINE_MODE=mock oder ENGINE_MODE=ace in .env setzen."
            )

        output_filename = f"{kind}_{uuid.uuid4().hex[:8]}.wav"
        output_path = settings.OUTPUTS_DIR / output_filename

        # Prompt aus V2-Feldern zusammenbauen
        prompt_parts = []
        if payload.get("prompt"):
            prompt_parts.append(str(payload["prompt"]))
        if payload.get("genre"):
            prompt_parts.append(str(payload["genre"]))
        if payload.get("substyle"):
            prompt_parts.append(str(payload["substyle"]))
        music_prompt = ", ".join(filter(None, prompt_parts)) or "music"

        duration = int(payload.get("duration", 30))
        duration = max(5, min(duration, 300))

        if _check_audiocraft():
            return await self._generate_via_audiocraft(music_prompt, output_path, duration)
        elif _check_transformers_musicgen():
            return await self._generate_via_transformers(music_prompt, output_path, duration)

        raise RuntimeError("MusicGen: Keine passende Backend-Library gefunden.")

    async def _generate_via_audiocraft(
        self, prompt: str, output_path: Path, duration: int
    ) -> str:
        import asyncio
        import numpy as np

        def _run():
            from audiocraft.models import MusicGen
            import soundfile as sf
            import torch

            if self._model is None:
                logger.info("musicgen_loading_model", model=self.model_id)
                self._model = MusicGen.get_pretrained(self.model_id)
                self._model.set_generation_params(duration=duration)

            self._model.set_generation_params(duration=duration)
            with torch.no_grad():
                wav = self._model.generate([prompt])

            audio_data = wav[0].squeeze().cpu().numpy()
            sf.write(str(output_path), audio_data, samplerate=32000)
            return str(output_path)

        return await asyncio.to_thread(_run)

    async def _generate_via_transformers(
        self, prompt: str, output_path: Path, duration: int
    ) -> str:
        import asyncio

        def _run():
            from transformers import AutoProcessor, MusicgenForConditionalGeneration
            import torch
            import scipy.io.wavfile as wavfile
            import numpy as np

            logger.info("musicgen_loading_hf_model", model=self.model_id)
            processor = AutoProcessor.from_pretrained(self.model_id)
            model = MusicgenForConditionalGeneration.from_pretrained(self.model_id)

            inputs = processor(
                text=[prompt],
                padding=True,
                return_tensors="pt",
            )
            # max_new_tokens approx: 50 tokens/sec for musicgen-medium
            max_tokens = min(duration * 50, 1500)
            with torch.no_grad():
                audio_values = model.generate(**inputs, max_new_tokens=max_tokens)

            sampling_rate = model.config.audio_encoder.sampling_rate
            audio_data = audio_values[0, 0].numpy()
            wavfile.write(str(output_path), rate=sampling_rate, data=audio_data)
            return str(output_path)

        return await asyncio.to_thread(_run)
