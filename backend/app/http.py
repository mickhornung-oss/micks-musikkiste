"""HTTP middleware and exception handlers."""

import time
import uuid

import structlog
from app.errors import AppError
from app.observability import runtime_stats
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        request.state.request_id = request_id
        request.state.error_code = None

        try:
            response = await call_next(request)
        except Exception:
            runtime_stats.record_request(failed=True, error_code="unhandled_exception")
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        runtime_stats.record_request(
            failed=response.status_code >= 400,
            error_code=request.state.error_code,
        )
        structlog.get_logger().info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


def _error_payload(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    request.state.error_code = code
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": request_id,
            },
        },
        headers={"X-Request-ID": request_id} if request_id else None,
    )


def install_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        structlog.get_logger().warning(
            "app_error",
            error_code=exc.code,
            status_code=exc.status_code,
            details=exc.details,
        )
        return _error_payload(
            request=request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP-Fehler"
        code = {
            400: "bad_request",
            404: "not_found",
            422: "validation_error",
        }.get(exc.status_code, "http_error")
        structlog.get_logger().warning(
            "http_error", status_code=exc.status_code, detail=detail
        )
        return _error_payload(
            request=request,
            status_code=exc.status_code,
            code=code,
            message=detail,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        structlog.get_logger().warning("request_validation_failed", errors=exc.errors())
        return _error_payload(
            request=request,
            status_code=422,
            code="validation_error",
            message="Ungültige Anfrage",
            details={"fields": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        structlog.get_logger().exception("unhandled_exception")
        return _error_payload(
            request=request,
            status_code=500,
            code="internal_error",
            message="Interner Fehler",
        )
