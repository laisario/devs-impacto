"""
Custom exceptions and error handlers for the PNAE API.
Provides consistent error response format across the application.
"""

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    detail: str | None = None
    code: str | None = None


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str | None = None,
        detail: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
        )


class UnauthorizedError(AppException):
    """Authentication error."""

    def __init__(self, message: str = "Not authenticated"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
        )


class ForbiddenError(AppException):
    """Authorization error."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
        )


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, detail: str | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            detail=detail,
        )


class ConflictError(AppException):
    """Conflict error (e.g., duplicate resource)."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException and return consistent error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.message,
            detail=exc.detail,
            code=exc.code,
        ).model_dump(exclude_none=True),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException and return consistent error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            code="HTTP_ERROR",
        ).model_dump(exclude_none=True),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]

