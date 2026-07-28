"""Pydantic Settings model for Sanskriti AI Studio backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables with fallbacks to defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "sanskriti_ai_studio"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = "/api"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Storage paths (relative to backend root)
    STORAGE_PROJECTS: str = "projects"
    STORAGE_ASSETS: str = "assets"
    STORAGE_EXPORTS: str = "exports"
    STORAGE_TEMP: str = "temp"
    STORAGE_LOGS: str = "logs"

    # Feature flags
    ENABLE_CORS: bool = True


def from_env() -> Settings:
    """Load settings from environment variables with fallbacks to defaults."""
    return Settings()