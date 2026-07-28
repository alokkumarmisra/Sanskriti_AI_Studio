"""Dependency injection structure for Sanskriti AI Studio backend."""

from fastapi import Depends


class ConfigDep:
    """Config dependency that provides application configuration."""

    def __call__(self) -> dict[str, str]:
        from app.core.config import config  # noqa: F401

        return {k: v for k, v in config.__dict__.items() if not k.startswith("_")}


class LoggingDep:
    """Logging dependency that provides logging configuration."""

    def __call__(self) -> dict[str, str]:
        from app.core.logging_config import LOG_LEVEL  # noqa: F401

        return {"LOG_LEVEL": LOG_LEVEL}


class ExceptionHandlersDep:
    """Exception handlers dependency for FastAPI."""

    def __call__(self) -> dict[str, type[Exception]]:
        from app.core.exceptions import (  # noqa: F401
            BadRequest,
            Forbidden,
            HTTPException,
            InternalError,
            NotFound,
            Unauthorized,
        )

        return {
            "BadRequest": BadRequest,
            "Forbidden": Forbidden,
            "HTTPException": HTTPException,
            "InternalError": InternalError,
            "NotFound": NotFound,
            "Unauthorized": Unauthorized,
        }


class CORSDep:
    """CORS middleware dependency."""

    def __call__(self) -> dict[str, str]:
        from app.middleware.cors_middleware import cors_middleware  # noqa: F401

        return {"cors_middleware": cors_middleware}


class DatabaseDep:
    """Database connection placeholder dependency."""

    def __call__(self) -> None:
        pass


# Export all dependencies for use in FastAPI routes
__all__ = [
    "ConfigDep",
    "LoggingDep",
    "ExceptionHandlersDep",
    "CORSDep",
    "DatabaseDep",
]