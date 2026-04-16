"""Engine factory that selects mock or real adapter."""

from app.config import settings

from .ace import AceEngineAdapter
from .mock import MockEngineAdapter
from .real import RealEngineAdapter


def get_engine_adapter():
    mode = (settings.ENGINE_MODE or "mock").lower()
    if mode == "real":
        return RealEngineAdapter()
    if mode in {"ace", "ace-step", "acestep"}:
        return AceEngineAdapter()
    return MockEngineAdapter()


def get_engine_diagnostics() -> dict:
    return get_engine_adapter().diagnostics()


__all__ = [
    "get_engine_adapter",
    "get_engine_diagnostics",
    "MockEngineAdapter",
    "RealEngineAdapter",
]
