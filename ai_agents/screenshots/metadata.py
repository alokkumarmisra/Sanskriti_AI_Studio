#!/usr/bin/env python3
"""
Screenshot Metadata Module for Sanskriti AI Studio.

This module handles metadata generation, validation, and serialization
for all captured screenshots.

Metadata includes:
- Screenshot ID (unique identifier)
- Session ID
- Milestone ID
- Task ID
- Timestamp (ISO-8601 UTC)
- URL
- Browser info
- Viewport dimensions
- Capture mode
- Page title
- Image dimensions (width x height in pixels)
- File size
- Optimization level
- Duplicate status

Version: 1.0
Last Updated: 2026-08-07
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class CaptureMode(str, Enum):
    """Enumeration of capture modes supported by the Screenshot Service."""

    FULL_PAGE = "full_page"  # Entire scrollable page
    VIEWPORT = "viewport"     # Visible viewport only
    ELEMENT = "element"      # Specific DOM element
    REGION = "region"        # Cropped region of viewport


class BrowserType(str, Enum):
    """Supported browser types."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class OptimizationLevel(str, Enum):
    """Image optimization levels."""

    NONE = 0       # No compression
    LOW = 1        # ~60% quality
    MEDIUM = 2     # ~75% quality
    HIGH = 3       # ~90% quality
    MAXIMAL = 4    # ~98% quality (best quality, largest size)


@dataclass
class ScreenshotMetadata:
    """
    Complete metadata structure for a captured screenshot.
    
    This metadata is stored alongside each PNG file in JSON format.
    """

    # Core identifiers
    screenshot_id: str  # Unique UUID or generated ID
    image_path: str     # Relative path to the stored PNG file
    
    # Context information
    session_id: str = ""      # Session identifier
    milestone_id: str = ""    # Current milestone (e.g., "STEP-23.4")
    task_id: str = ""         # Task identifier
    correlation_id: str = ""  # Correlation ID for tracking
    
    # Timestamps
    captured_at: str = ""     # ISO-8601 UTC timestamp when captured
    
    # Capture details
    capture_mode: CaptureMode = CaptureMode.VIEWPORT
    url: str = ""             # Page URL (if applicable)
    browser_type: BrowserType = BrowserType.CHROMIUM
    viewport_width: int = 0   # Viewport width in pixels
    viewport_height: int = 0  # Viewport height in pixels
    page_title: str = ""      # Page title from DOM
    
    # Image dimensions
    image_width: int = 0         # Actual captured image width
    image_height: int = 0        # Actual captured image height
    
    # File information
    file_size_bytes: int = 0    # Size of PNG file in bytes
    
    # Optimization details
    optimization_level: OptimizationLevel = OptimizationLevel.MEDIUM
    compression_method: str = "png"  # Compression algorithm used
    
    # Quality control
    is_duplicate: bool = False   # Whether this is a duplicate
    duplicate_of: str = ""       # Screenshot ID of original if duplicate
    quality_score: float = 1.0   # Image quality assessment (0-1)
    
    # Status and lifecycle
    status: str = "active"      # active, archived, deleted
    captured_by: str = ""       # Agent or service that captured it
    
    # Additional notes
    notes: str = ""             # Any additional notes about the capture
    
    # Raw data (for future extensibility)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if not self.screenshot_id or len(self.screenshot_id) == 0:
            raise ValueError("screenshot_id cannot be empty")
        
        if not self.image_path:
            raise ValueError("image_path cannot be empty")

    @property
    def file_size_kb(self) -> float:
        """Get file size in kilobytes."""
        return self.file_size_bytes / 1024.0

    @property
    def resolution_megapixels(self) -> float:
        """Get image resolution in megapixels."""
        if not self.image_width or not self.image_height:
            return 0.0
        return (self.image_width * self.image_height) / 1_000_000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        result = {}
        for field_name in [
            "screenshot_id", "image_path", "session_id", "milestone_id",
            "task_id", "correlation_id", "captured_at", "capture_mode", "url",
            "browser_type", "viewport_width", "viewport_height", "page_title",
            "image_width", "image_height", "file_size_bytes", "optimization_level",
            "compression_method", "is_duplicate", "duplicate_of", "quality_score",
            "status", "captured_by", "notes"
        ]:
            if field_name in self.__dict__:
                value = getattr(self, field_name)
                # Convert enum to string for JSON serialization
                if isinstance(value, Enum):
                    result[field_name] = value.value
                else:
                    result[field_name] = value
        
        # Include raw_data if present
        if self.raw_data:
            result["raw_data"] = self.raw_data
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScreenshotMetadata":
        """Create metadata from dictionary (for deserialization)."""
        # Convert string enum values back to Enum instances
        enum_map = {
            "capture_mode": CaptureMode,
            "browser_type": BrowserType,
            "optimization_level": OptimizationLevel,
        }
        
        for field_name, enum_type in enum_map.items():
            if field_name in data and isinstance(data[field_name], str):
                # Handle enum value conversion using member access
                try:
                    # Use getattr to safely get enum member by value
                    member = enum_type.__members__[data[field_name]]
                    data[field_name] = member
                except (KeyError, TypeError, AttributeError):
                    pass
        
        return cls(**data)

    def generate_filename(self, prefix: str = "screenshot") -> str:
        """
        Generate a filename from the metadata.
        
        Example output: screenshot_abc123_full_page_chromium_20260807_113000.png
        
        Args:
            prefix: Filename prefix (default: "screenshot")
            
        Returns:
            Generated filename string
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        mode_str = self.capture_mode.replace("_", "-")
        browser_str = self.browser_type
        
        return f"{prefix}_{self.screenshot_id[:8]}_{mode_str}_{browser_str}_{timestamp}.png"

    def validate_checksum(self, checksum: str) -> bool:
        """Validate the metadata against a checksum."""
        # Simple validation - in production, use proper hashing
        import hashlib
        expected_hash = hashlib.md5(
            f"{self.screenshot_id}{self.image_path}".encode()
        ).hexdigest()
        return self.capture_mode in checksum or checksum == expected_hash

    def is_expired(self, hours: int = 24) -> bool:
        """Check if the screenshot has expired based on timestamp."""
        try:
            captured_time = datetime.fromisoformat(self.captured_at.replace('Z', '+00:00'))
            expiry_time = captured_time.timestamp() + (hours * 3600)
            return datetime.now(timezone.utc).timestamp() > expiry_time
        except Exception:
            return False


class MetadataGenerator:
    """
    Factory for generating and managing screenshot metadata.
    
    This class provides methods to generate metadata for new captures,
    retrieve existing metadata, and manage metadata operations.
    """

    def __init__(self, screenshot_service=None):
        """
        Initialize the metadata generator.
        
        Args:
            screenshot_service: Optional reference to ScreenshotCaptureService
        """
        self.screenshot_service = screenshot_service
        self._metadata_cache: Dict[str, ScreenshotMetadata] = {}

    def generate_new_metadata(
        self,
        session_id: str,
        milestone_id: str,
        task_id: str,
        image_path: str,
        capture_mode: CaptureMode = CaptureMode.VIEWPORT,
        url: Optional[str] = None,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        optimization_level: OptimizationLevel = OptimizationLevel.MEDIUM,
    ) -> ScreenshotMetadata:
        """
        Generate metadata for a new screenshot capture.
        
        Args:
            session_id: Session identifier
            milestone_id: Milestone identifier (e.g., "STEP-23.4")
            task_id: Task identifier
            image_path: Relative path to the stored PNG
            capture_mode: Capture mode used
            url: Page URL (optional)
            browser_type: Browser type used for capture
            viewport_width: Viewport width in pixels
            viewport_height: Viewport height in pixels
            optimization_level: Image optimization level
            
        Returns:
            ScreenshotMetadata instance
        """
        screenshot_id = self._generate_unique_id(milestone_id, task_id)
        captured_at = datetime.now(timezone.utc).isoformat()
        
        # Generate page title from URL if available
        page_title = ""
        if url:
            try:
                page_title = url.split("/")[-1] or url.split("?")[0].split("#")[0][:100]
            except Exception:
                pass
        
        metadata = ScreenshotMetadata(
            screenshot_id=screenshot_id,
            image_path=image_path,
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
            captured_at=captured_at,
            capture_mode=capture_mode,
            url=url or "",
            browser_type=browser_type,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            page_title=page_title,
            optimization_level=optimization_level,
        )
        
        return metadata

    def _generate_unique_id(self, milestone: str, task: str) -> str:
        """
        Generate a unique screenshot ID based on milestone and task.
        
        Format: {milestone}_{task}_uuid_8chars
        
        Args:
            milestone: Milestone identifier
            task: Task identifier
            
        Returns:
            Unique string identifier
        """
        import uuid
        base_id = f"{milestone.replace('.', '_')}_{task.replace(' ', '_')}"
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{base_id}_{unique_suffix}"

    def get_metadata(self, screenshot_id: str) -> Optional[ScreenshotMetadata]:
        """
        Retrieve metadata for a specific screenshot.
        
        Args:
            screenshot_id: The screenshot ID to look up
            
        Returns:
            ScreenshotMetadata or None if not found
        """
        if screenshot_id in self._metadata_cache:
            return self._metadata_cache[screenshot_id]
        
        # Try to load from file if service is available
        if self.screenshot_service:
            metadata = self.screenshot_service.get_metadata(screenshot_id)
            if metadata:
                self._metadata_cache[screenshot_id] = metadata
                return metadata
        
        return None

    def update_metadata(self, screenshot_id: str, updates: Dict[str, Any]) -> Optional[ScreenshotMetadata]:
        """
        Update metadata for an existing screenshot.
        
        Args:
            screenshot_id: The screenshot ID to update
            updates: Dictionary of field names to new values
            
        Returns:
            Updated metadata or None if not found
        """
        metadata = self.get_metadata(screenshot_id)
        if not metadata:
            return None
        
        for field, value in updates.items():
            setattr(metadata, field, value)
        
        self._metadata_cache[screenshot_id] = metadata
        return metadata

    def mark_as_duplicate(
        self, 
        screenshot_id: str, 
        original_id: str
    ) -> Optional[ScreenshotMetadata]:
        """
        Mark a screenshot as a duplicate of another.
        
        Args:
            screenshot_id: ID of the duplicate screenshot
            original_id: ID of the original screenshot
            
        Returns:
            Updated metadata or None if not found
        """
        return self.update_metadata(
            screenshot_id, 
            {"is_duplicate": True, "duplicate_of": original_id}
        )

    def cache_metadata(self, metadata: ScreenshotMetadata) -> None:
        """Cache metadata for quick retrieval."""
        self._metadata_cache[metadata.screenshot_id] = metadata

    def clear_cache(self) -> None:
        """Clear the metadata cache."""
        self._metadata_cache.clear()


__all__ = [
    "ScreenshotMetadata",
    "CaptureMode",
    "BrowserType", 
    "OptimizationLevel",
    "MetadataGenerator",
]
