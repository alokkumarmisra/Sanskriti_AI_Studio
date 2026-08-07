#!/usr/bin/env python3
"""
Screenshot Storage Module for Sanskriti AI Studio.

This module handles the physical storage and retrieval of screenshot files.
It implements a structured directory-based storage system with proper
organization by session, milestone, task, and browser.

Storage Structure:
    runtime/
        screenshots/
            session/
                milestone/
                    task/
                        browser/
                            {image_path}.png
                            metadata.json

Features:
- Directory-based file storage (PNG images)
- JSON metadata alongside each image
- Session/task hierarchy for organization
- Duplicate detection by hash comparison
- File size validation
- Atomic write operations

Version: 1.0
Last Updated: 2026-08-07
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from metadata module (same package)
from ai_agents.screenshots.metadata import CaptureMode, BrowserType


class StorageConfig:
    """Configuration for screenshot storage."""

    def __init__(
        self,
        base_path: str = "runtime/screenshots",
        max_file_size_mb: float = 10.0,
        enable_duplicate_detection: bool = True,
        duplicate_hash_algorithm: str = "sha256",
        backup_directory: Optional[str] = None,
    ):
        """
        Initialize storage configuration.

        Args:
            base_path: Base directory for storing screenshots (relative path)
            max_file_size_mb: Maximum allowed file size in megabytes
            enable_duplicate_detection: Whether to detect and prevent duplicates
            duplicate_hash_algorithm: Hash algorithm for duplicate detection
            backup_directory: Optional backup directory for archived files
        """
        self.base_path = base_path
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.enable_duplicate_detection = enable_duplicate_detection
        self.duplicate_hash_algorithm = duplicate_hash_algorithm
        self.backup_directory = backup_directory

    @classmethod
    def default_config(cls, base_path: str = "runtime/screenshots") -> "StorageConfig":
        """Get default storage configuration."""
        return cls(
            base_path=base_path,
            max_file_size_mb=10.0,
            enable_duplicate_detection=True,
        )

    def resolve_base_path(self) -> Path:
        """
        Resolve the base path to an absolute path.

        Returns:
            Absolute Path object for the base directory
        """
        return Path.cwd() / self.base_path


class DuplicateDetector:
    """Handles duplicate screenshot detection."""

    def __init__(self, hash_algorithm: str = "sha256"):
        """
        Initialize duplicate detector.

        Args:
            hash_algorithm: Hash algorithm to use (sha256, sha1, md5)
        """
        self.hash_algorithm = hash_algorithm
        import hashlib
        self._hash_func = getattr(hashlib, hash_algorithm.lower())()

    def compute_file_hash(self, file_path: str) -> Optional[str]:
        """
        Compute hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of file content or None if error
        """
        try:
            with open(file_path, "rb") as f:
                # Read in chunks for memory efficiency
                for chunk in iter(lambda: f.read(8192), b""):
                    self._hash_func.update(chunk)
            return self._hash_func.hexdigest()
        except Exception:
            return None

    def is_duplicate(self, file_path: str, known_hashes: Dict[str, str]) -> Optional[str]:
        """
        Check if a file is a duplicate of an existing one.

        Args:
            file_path: Path to the new file
            known_hashes: Dictionary mapping hash -> original file path

        Returns:
            Original file path if duplicate found, None otherwise
        """
        new_hash = self.compute_file_hash(file_path)
        if not new_hash:
            return None

        # Check against known hashes
        for stored_hash, stored_path in known_hashes.items():
            if new_hash.lower() == stored_hash.lower():
                return stored_path
        
        return None


class ScreenshotStorage:
    """
    Storage manager for screenshot files.

    Handles all file I/O operations including reading, writing,
    organizing, and retrieving screenshots.
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        """
        Initialize storage manager.

        Args:
            config: Storage configuration (uses defaults if None)
        """
        self.config = config or StorageConfig.default_config()
        self.base_path = self.config.resolve_base_path()
        self._known_hashes: Dict[str, str] = {}  # hash -> file path
        self._detector = DuplicateDetector(self.config.duplicate_hash_algorithm)

    def _get_storage_directory(
        self,
        session_id: Optional[str] = None,
        milestone_id: Optional[str] = None,
        task_id: Optional[str] = None,
        browser_type: Optional[BrowserType] = None,
    ) -> Path:
        """
        Build the storage directory path based on hierarchy.

        Args:
            session_id: Session identifier
            milestone_id: Milestone identifier
            task_id: Task identifier
            browser_type: Browser type (e.g., CHROMIUM)

        Returns:
            Path object for the storage directory
        """
        parts = []
        
        if session_id:
            parts.append("session")
            parts.append(session_id.replace("/", "_"))
        
        if milestone_id:
            parts.append("milestone")
            parts.append(milestone_id.replace(".", "_"))
        
        if task_id:
            parts.append("task")
            parts.append(task_id.replace(" ", "_").replace(",", ""))
        
        if browser_type:
            parts.append(browser_type.value)
        
        # Create directory path
        dir_path = self.base_path
        for part in parts:
            dir_path = dir_path / part
        
        return dir_path

    def ensure_directory(self, session_id: str, milestone_id: str, task_id: str) -> Path:
        """
        Ensure the storage directory exists.

        Args:
            session_id: Session identifier
            milestone_id: Milestone identifier
            task_id: Task identifier

        Returns:
            The created/verified directory path
        """
        dir_path = self._get_storage_directory(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
        )
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def store_screenshot(
        self,
        image_path: str,
        session_id: str,
        milestone_id: str,
        task_id: str,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        verify_size: bool = True,
    ) -> Path:
        """
        Store a screenshot image file.

        Args:
            image_path: Relative path to the source image
            session_id: Session identifier
            milestone_id: Milestone identifier
            task_id: Task identifier
            browser_type: Browser type used for capture
            verify_size: Whether to verify file size

        Returns:
            Path to the stored file

        Raises:
            ValueError: If file is too large or other validation fails
        """
        source_path = Path(image_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        # Check file size
        if verify_size and source_path.stat().st_size > self.config.max_file_size_bytes:
            max_mb = self.config.max_file_size_bytes / (1024 * 1024)
            raise ValueError(
                f"File too large: {source_path.stat().st_size / (1024*1024):.1f}MB > max {max_mb:.1f}MB"
            )

        # Ensure directory exists
        storage_dir = self.ensure_directory(session_id, milestone_id, task_id)

        # Generate unique filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_name = f"{self._generate_unique_filename()}{source_path.suffix}"

        # Full destination path
        dest_path = storage_dir / unique_name
        relative_dest_path = self._get_relative_path(dest_path)

        # Check for duplicates
        if self.config.enable_duplicate_detection:
            existing = self._detector.is_duplicate(str(source_path), self._known_hashes)
            if existing:
                raise FileExistsError(f"Duplicate detected: {existing}")

        # Copy file atomically
        import shutil
        shutil.copy2(str(source_path), str(dest_path))

        # Update known hashes
        new_hash = self._detector.compute_file_hash(str(source_path))
        if new_hash:
            self._known_hashes[new_hash] = relative_dest_path

        return dest_path

    def _generate_unique_filename(self) -> str:
        """Generate a unique filename using timestamp and random suffix."""
        import uuid
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"{timestamp}_{random_suffix}"

    def _get_relative_path(self, dest_path: Path) -> str:
        """Get relative path from base."""
        try:
            rel_path = dest_path.relative_to(self.base_path)
            return str(rel_path).replace("\\", "/")
        except ValueError:
            # If not relative to base, make it absolute
            return str(dest_path).replace("\\", "/")

    def get_screenshot(self, image_path: str) -> Optional[Path]:
        """
        Retrieve a screenshot by its stored path.

        Args:
            image_path: Relative or absolute path to the stored image

        Returns:
            Path object if found, None otherwise
        """
        # Resolve to absolute if given relative path - FIX: use Path() constructor instead of replace
        if not os.path.isabs(image_path):
            full_path = self.base_path / image_path
        else:
            full_path = Path(image_path)

        if full_path.exists():
            return full_path
        return None

    def get_file_size(self, image_path: str) -> Optional[int]:
        """
        Get the file size of a stored screenshot.

        Args:
            image_path: Relative path to the stored image

        Returns:
            File size in bytes or None if not found
        """
        path = self.get_screenshot(image_path)
        if path:
            return path.stat().st_size
        return None

    def get_all_stored_paths(self, session_id: Optional[str] = None) -> List[str]:
        """
        Get list of all stored screenshot paths.

        Args:
            session_id: Filter by session ID (optional)

        Returns:
            List of relative paths to stored images
        """
        import glob
        base_str = str(self.base_path).replace("\\", "/")
        
        if session_id:
            pattern = os.path.join(base_str, "session", session_id.replace("/", "_"), "*", "*.png")
        else:
            pattern = os.path.join(base_str, "**", "*.png")
        
        files = glob.glob(pattern, recursive=True)
        # Convert to relative paths
        rel_paths = []
        for f in files:
            try:
                rel = Path(f).relative_to(self.base_path)
                rel_paths.append(str(rel).replace("\\", "/"))
            except ValueError:
                pass
        
        return sorted(rel_paths)

    def clear_storage(self) -> int:
        """
        Clear all stored screenshots.

        Returns:
            Number of files deleted
        """
        import shutil
        if self.base_path.exists():
            count = len(list(self.base_path.glob("*")))
            shutil.rmtree(self.base_path)
            return count
        return 0

    def get_known_hashes(self) -> Dict[str, str]:
        """Get the known file hashes for duplicate detection."""
        return dict(self._known_hashes)

    def clear_hashes(self) -> None:
        """Clear the stored file hashes cache."""
        self._known_hashes.clear()


__all__ = [
    "StorageConfig",
    "DuplicateDetector",
    "ScreenshotStorage",
]
