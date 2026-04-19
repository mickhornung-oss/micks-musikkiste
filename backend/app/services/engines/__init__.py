"""Engine factory – V2: mock | ace | musicgen.

ACE:     Haupt-Engine. Läuft via ComfyUI-Bridge (ace_comfy_wrapper.py).
         Direkte ace-step CLI erfordert: pip install ace-step torch.
MusicGen: Zweite Engine-Schiene. Vorbereitet, requires: pip install audiocraft
         ODER pip install transformers torch accelerate.
Mock:    Dev/Fallback. Erzeugt echten 440-Hz-Testton-WAV.
"""

from app.config import settings

from .ace import AceEngineAdapter
from .mock import MockEngineAdapter
from .musicgen import MusicGenAdapter


def get_engine_adapter():
    mode = (settings.ENGINE_MODE or "mock").lower()
    if mode in {"ace", "ace-step", "acestep"}:
        return AceEngineAdapter()
    if mode == "musicgen":
        return MusicGenAdapter()
    return MockEngineAdapter()


def get_engine_diagnostics() -> dict:
    return get_engine_adapter().diagnostics()


__all__ = [
    "get_engine_adapter",
    "get_engine_diagnostics",
    "MockEngineAdapter",
    "AceEngineAdapter",
    "MusicGenAdapter",
]
