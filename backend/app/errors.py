"""Application-level exceptions with HTTP mapping."""

from typing import Any, Optional


class AppError(Exception):
    """Base application error with stable API metadata."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "internal_error",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str, *, code: str = "not_found", details: Optional[dict[str, Any]] = None):
        super().__init__(message, status_code=404, code=code, details=details)


class InvalidStateError(AppError):
    def __init__(self, message: str, *, code: str = "invalid_state", details: Optional[dict[str, Any]] = None):
        super().__init__(message, status_code=400, code=code, details=details)


class ConfigurationError(AppError):
    def __init__(self, message: str, *, code: str = "configuration_error", details: Optional[dict[str, Any]] = None):
        super().__init__(message, status_code=500, code=code, details=details)
