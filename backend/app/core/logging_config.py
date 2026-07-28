"""Logging configuration for Sanskriti AI Studio backend."""

import logging
from pathlib import Path

LOG_LEVEL = "INFO"  # noqa: F401
def setup_logging() -> None:
    """Configure logging with file and console handlers."""
    
    # Get log directory from config or default to storage/logs
    log_dir = Path("storage/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


# Apply configuration at module import time
setup_logging()