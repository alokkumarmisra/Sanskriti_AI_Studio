"""Configuration loader for Sanskriti AI Studio backend."""

from app.core.settings import Settings, from_env  # noqa: F401

# Load configuration at module import time
config = from_env()