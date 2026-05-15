"""
Custom exceptions and global exception handlers.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("knowledge_os.exceptions")


# ── Custom Exception Classes ─────────────────────────────────
class KnowledgeOSException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class EntityNotFoundError(KnowledgeOSException):
    """Raised when a requested entity is not found."""

    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            message=f"{entity} with id '{entity_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class DuplicateEntityError(KnowledgeOSException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            message=f"{entity} with {field} '{value}' already exists",
            status_code=status.HTTP_409_CONFLICT,
        )


class PermissionDeniedError(KnowledgeOSException):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class FileProcessingError(KnowledgeOSException):
    """Raised when file processing fails."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to process file '{filename}': {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class LLMServiceError(KnowledgeOSException):
    """Raised when LLM service communication fails."""

    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ── Register Global Handlers ────────────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(KnowledgeOSException)
    async def knowledge_os_exception_handler(
        request: Request, exc: KnowledgeOSException
    ) -> JSONResponse:
        logger.error(
            "KnowledgeOSException: %s [%d] — %s %s",
            exc.message,
            exc.status_code,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": type(exc).__name__},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred. Please try again later.",
                "type": "InternalServerError",
            },
        )
