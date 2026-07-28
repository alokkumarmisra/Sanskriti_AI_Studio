"""Exception handlers for Sanskriti AI Studio backend."""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class HTTPException(Exception):
    """Base exception class with standardized response data."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return standardized JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "errors": [],
        },
    )


class NotFound(HTTPException):
    """Resource not found exception (404)."""

    def __init__(self, message: str = "Not Found") -> None:
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class BadRequest(HTTPException):
    """Bad request validation error (400)."""

    def __init__(self, message: str = "Bad Request", errors: list[str] | None = None) -> None:
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class Unauthorized(HTTPException):
    """Authentication required (401)."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class Forbidden(HTTPException):
    """Access denied (403)."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class InternalError(HTTPException):
    """Internal server error (500)."""

    def __init__(self, message: str = "Internal Error") -> None:
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)