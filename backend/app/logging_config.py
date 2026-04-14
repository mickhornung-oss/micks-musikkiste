"""Structured logging configuration for Micks Musikkiste."""

import logging
from logging.handlers import RotatingFileHandler

import structlog

from app.config import settings


class SafeRotatingFileHandler(RotatingFileHandler):
    """Keep startup alive even if Windows log rotation hits a locked file."""

    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            # Another process still holds the rotated file. Keep app startup alive and
            # continue writing to the current file instead of crashing the startup path.
            if self.stream is None:
                self.stream = self._open()


def configure_logging():
    """Configure console and file logging with shared structured context."""
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=shared_processors,
    )
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    app_file_handler = SafeRotatingFileHandler(
        settings.LOGS_DIR / "app.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(json_formatter)

    error_file_handler = SafeRotatingFileHandler(
        settings.LOGS_DIR / "error.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(json_formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger("micks")
