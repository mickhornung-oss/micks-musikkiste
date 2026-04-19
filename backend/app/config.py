import os
from pathlib import Path
from typing import Any, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        case_sensitive=False,
        extra="ignore",
    )

    # API
    API_TITLE: str = "Micks Musikkiste API"
    API_VERSION: str = "1.0.1"
    API_DESCRIPTION: str = "Lokales AI-Musikstudio Backend"
    APP_ENV: str = "local"
    RELEASE_VERSION: str = "1.0.1"
    RELEASE_SHA: str = "local"

    # Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    PROJECTS_DIR: Path = DATA_DIR / "projects"
    OUTPUTS_DIR: Path = DATA_DIR / "outputs"
    EXPORTS_DIR: Path = DATA_DIR / "exports"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres@localhost:5432/postgres"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Logging
    LOG_LEVEL: str = "info"
    DEBUG: bool = False

    # Engine
    ENGINE_MODE: str = "mock"
    ENGINE_MOCK_DELAY: int = 2
    ENGINE_REAL_COMMAND: str = ""
    ENGINE_TIMEOUT: int = 600
    ENGINE_PROFILE: str = "ace_turbo"
    ACE_STEP_COMMAND: str = "ace-step"
    ACE_STEP_MAX_DURATION: int = 300
    COMFYUI_URL: str = "http://127.0.0.1:8188"
    COMFYUI_AUTOSTART: bool = True
    COMFYUI_START_TIMEOUT: int = 45
    COMFYUI_EXE: str = str(
        Path.home() / "AppData" / "Local" / "Programs" / "ComfyUI" / "ComfyUI.exe"
    )
    COMFYUI_SERVER_ROOT: str = str(
        Path.home()
        / "AppData"
        / "Local"
        / "Programs"
        / "ComfyUI"
        / "resources"
        / "ComfyUI"
    )
    COMFYUI_SERVER_PYTHON: str = str(
        Path.home()
        / "AppData"
        / "Local"
        / "Programs"
        / "ComfyUI"
        / "resources"
        / "ComfyUI"
        / ".venv"
        / "Scripts"
        / "python.exe"
    )

    # Worker
    WORKER_ENABLED: bool = True
    WORKER_POLL_INTERVAL: float = 2.0
    WORKER_HEARTBEAT_INTERVAL: float = 30.0
    WORKER_STALE_TIMEOUT: float = 600.0  # 10 minutes
    WORKER_MAX_RETRIES: int = 3

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        """Accept noisy shell env values like DEBUG=release."""
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        normalized = str(value).strip().lower()
        return normalized in {"1", "true", "yes", "on", "debug", "dev"}

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: Any) -> str:
        """Support Railway-style postgres URLs with async SQLAlchemy driver."""
        if value is None:
            return "postgresql+asyncpg://postgres@localhost:5432/postgres"
        raw = str(value).strip()
        if raw.startswith("postgres://"):
            return "postgresql+asyncpg://" + raw[len("postgres://") :]
        if raw.startswith("postgresql://") and not raw.startswith(
            "postgresql+asyncpg://"
        ):
            return "postgresql+asyncpg://" + raw[len("postgresql://") :]
        return raw


settings = Settings()

# Backwards compatibility: honor ENGINE_TYPE when ENGINE_MODE is not set.
legacy_engine = os.getenv("ENGINE_TYPE")
if legacy_engine and not os.getenv("ENGINE_MODE"):
    settings.ENGINE_MODE = legacy_engine

for dir_path in (
    settings.PROJECTS_DIR,
    settings.OUTPUTS_DIR,
    settings.EXPORTS_DIR,
    settings.LOGS_DIR,
):
    dir_path.mkdir(parents=True, exist_ok=True)
