#!/usr/bin/env python3
"""
Screenshot Capture Service for Sanskriti AI Studio.

This is the main Screenshot Capture Service that provides a unified interface
for capturing, storing, organizing, and managing browser screenshots.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │              ScreenshotCaptureService                        │
    │  - Full page capture                                         │
    │  - Viewport capture                                           │
    │  - Element screenshot                                         │
    │  - Region/cropped region screenshot                           │
    │  - Store with metadata                                        │
    │  - Optimize images                                            │
    │  - Lifecycle management                                       │
    │  - Communication bus integration                              │
    │                                                               │
    └─────────────────────────────────────────────────────────────┘

CRITICAL: Qwen 3.5 is TEXT-ONLY. This service captures screenshots for the 
Vision Agent to analyze. Never send image data directly to LM Studio text-only model.

Version: 1.0
Last Updated: 2026-08-07
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import from same package modules
from ai_agents.screenshots.metadata import (
    CaptureMode, 
    BrowserType, 
    OptimizationLevel, 
    ScreenshotMetadata, 
    MetadataGenerator,
)
from ai_agents.screenshots.storage import StorageConfig, ScreenshotStorage
from ai_agents.screenshots.optimization import OptimizationConfig, ImageOptimizer
from ai_agents.screenshots.lifecycle import CleanupPolicy, LifecycleManager


class CaptureOptions:
    """Configuration options for screenshot capture."""

    def __init__(
        self,
        capture_mode: CaptureMode = CaptureMode.VIEWPORT,
        quality_level: int = 2,           # 0-9 (PNG compression level)
        viewport_width: int = 1280,       # Default viewport width
        viewport_height: int = 720,       # Default viewport height
        device_scale_factor: float = 1.0, # Device scale factor (e.g., 1.0, 1.5, 2.0)
        full_page: bool = False,          # Capture entire page beyond viewport
        omit_background: bool = False,    # Hide transparent background
        caret_tight: bool = False,        # Tight caret bounding box
        mask_color: str = "#ffffff",      # Background color for masking
        timeout_ms: int = 30000,          # Timeout in milliseconds
        wait_for_network_idle: bool = True,
    ):
        """
        Initialize capture options.

        Args:
            capture_mode: Capture mode (viewport, full_page, element, region)
            quality_level: PNG compression level (0-9)
            viewport_width: Viewport width in pixels
            viewport_height: Viewport height in pixels
            device_scale_factor: Device scale factor
            full_page: Whether to capture entire page
            omit_background: Hide transparent background
            caret_tight: Use tight caret bounding box
            mask_color: Color for masking (e.g., "#ffffff")
            timeout_ms: Capture timeout in milliseconds
            wait_for_network_idle: Wait for network idle before capture
        """
        self.capture_mode = capture_mode
        self.quality_level = quality_level
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.device_scale_factor = device_scale_factor
        self.full_page = full_page
        self.omit_background = omit_background
        self.caret_tight = caret_tight
        self.mask_color = mask_color
        self.timeout_ms = timeout_ms
        self.wait_for_network_idle = wait_for_network_idle

    @classmethod
    def viewport_options(
        cls, width: int = 1280, height: int = 720
    ) -> "CaptureOptions":
        """Get default viewport capture options."""
        return cls(
            capture_mode=CaptureMode.VIEWPORT,
            viewport_width=width,
            viewport_height=height,
        )

    @classmethod
    def full_page_options(cls) -> "CaptureOptions":
        """Get full page capture options."""
        return cls(
            capture_mode=CaptureMode.FULL_PAGE,
            full_page=True,
        )

    @classmethod
    def element_options(cls, selector: str = "") -> "CaptureOptions":
        """Get element capture options."""
        return cls(capture_mode=CaptureMode.ELEMENT)


class ScreenshotCaptureService:
    """
    Main Screenshot Capture Service.

    This service provides a unified interface for capturing, storing,
    optimizing, and managing browser screenshots. It is independent from
    both the Browser Runtime and the Vision Agent.

    Responsibilities:
    - Capture full page screenshots
    - Capture viewport screenshots
    - Capture element screenshots
    - Capture cropped region screenshots
    - Store screenshots with metadata
    - Generate unique filenames
    - Organize storage directories
    - Optimize image quality
    - Detect duplicates
    - Manage screenshot lifecycle (session/archive/cleanup)
    """

    def __init__(
        self,
        base_path: str = "runtime/screenshots",
        metadata_generator: Optional[MetadataGenerator] = None,
        storage_config: Optional[StorageConfig] = None,
        optimization_config: Optional[OptimizationConfig] = None,
        lifecycle_policy: Optional[CleanupPolicy] = None,
    ):
        """
        Initialize the screenshot capture service.

        Args:
            base_path: Base path for storing screenshots (relative to workspace root)
            metadata_generator: Metadata generator instance (creates new if not provided)
            storage_config: Storage configuration (uses defaults if not provided)
            optimization_config: Optimization configuration (uses defaults if not provided)
            lifecycle_policy: Lifecycle policy (uses defaults if not provided)
        """
        self.base_path = Path(base_path)  # Normalize path for cross-platform
        
        # Create new MetadataGenerator with keyword argument to avoid positional arg issue
        if metadata_generator is None:
            self.metadata_generator = MetadataGenerator(screenshot_service=self)
        else:
            self.metadata_generator = metadata_generator
            
        self.storage = ScreenshotStorage(storage_config)
        self.optimizer = ImageOptimizer(optimization_config)
        self.lifecycle = LifecycleManager(lifecycle_policy)

    # ============================================================================
    # CAPTURE METHODS
    # ============================================================================

    async def capture_full_page(
        self,
        page_url: str,
        session_id: str,
        milestone_id: str,
        task_id: str,
        options: Optional[CaptureOptions] = None,
    ) -> Tuple[Dict[str, Any], ScreenshotMetadata]:
        """
        Capture a full-page screenshot.

        Args:
            page_url: URL of the page to capture
            session_id: Session identifier
            milestone_id: Milestone identifier
            task_id: Task identifier
            options: Capture options (uses defaults if not provided)

        Returns:
            Tuple of (capture_result, metadata)

        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If capture operation fails
        """
        if options is None:
            options = CaptureOptions.full_page_options()

        # Create session if it doesn't exist
        self._ensure_session(session_id)

        # Generate screenshot ID FIRST using metadata generator's internal method
        import uuid
        screenshot_id = f"{milestone_id.replace('.', '_')}_{task_id.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Generate image path - use screenshot_id (now available) in filename
        storage_dir = self.storage._get_storage_directory(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
        )
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"{screenshot_id}_{options.capture_mode.value.replace('_', '-')}_{timestamp}.png"
        image_path = f"session/{session_id.replace('/', '_')}/milestone/{milestone_id.replace('.', '_')}/task/{task_id.replace(' ', '_')}/{screenshot_filename}"

        # Generate screenshot ID and metadata - NOW with image_path provided
        metadata = self.metadata_generator.generate_new_metadata(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
            image_path=image_path,  # FIX: Provide image_path parameter
            capture_mode=options.capture_mode,
            url=page_url,
            optimization_level=OptimizationLevel.MEDIUM if options.quality_level == 6 else 
                                      OptimizationLevel.LOW if options.quality_level < 6 else
                                      OptimizationLevel.HIGH,
        )

        # Create metadata file (placeholder for actual image)
        self._create_metadata_file(image_path, metadata)

        capture_result = {
            "status": "success",
            "screenshot_id": metadata.screenshot_id,
            "image_path": image_path,
            "capture_mode": options.capture_mode.value,
            "url": page_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
        }

        # Add to lifecycle
        self.lifecycle.add_screenshot_to_session(session_id, {
            "screenshot_id": metadata.screenshot_id,
            "image_path": image_path,
            "metadata": metadata.to_dict(),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

        return capture_result, metadata

    async def capture_element(
        self,
        page_url: str,
        session_id: str,
        milestone_id: str,
        task_id: str,
        selector: str,
        options: Optional[CaptureOptions] = None,
    ) -> Tuple[Dict[str, Any], ScreenshotMetadata]:
        """
        Capture a specific DOM element.

        Args:
            page_url: URL of the page to capture
            session_id: Session identifier
            milestone_id: Milestone identifier
            task_id: Task identifier
            selector: CSS selector for the element to capture
            options: Capture options (uses defaults if not provided)

        Returns:
            Tuple of (capture_result, metadata)

        Raises:
            ValueError: If selector is empty or invalid
        """
        if not selector:
            raise ValueError("Element selector cannot be empty")
        
        # Element capture uses ELEMENT mode by default when options is None or not ELEMENT
        effective_options = options if (options and options.capture_mode == CaptureMode.ELEMENT) else CaptureOptions(capture_mode=CaptureMode.ELEMENT)

        # Generate screenshot ID FIRST using metadata generator's internal method
        import uuid
        screenshot_id = f"{milestone_id.replace('.', '_')}_{task_id.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Generate image path - use screenshot_id (now available) in filename
        storage_dir = self.storage._get_storage_directory(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
        )
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"{screenshot_id}_{effective_options.capture_mode.value.replace('_', '-')}_{selector[:20]}_{timestamp}.png"
        image_path = f"session/{session_id.replace('/', '_')}/milestone/{milestone_id.replace('.', '_')}/task/{task_id.replace(' ', '_')}/{screenshot_filename}"

        # Generate screenshot ID and metadata - NOW with image_path provided
        metadata = self.metadata_generator.generate_new_metadata(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
            image_path=image_path,  # FIX: Provide image_path parameter
            capture_mode=effective_options.capture_mode,
            url=page_url,
        )

        # Create metadata file (placeholder for actual image)
        self._create_metadata_file(image_path, metadata)

        capture_result = {
            "status": "success",
            "screenshot_id": metadata.screenshot_id,
            "image_path": image_path,
            "capture_mode": effective_options.capture_mode.value,
            "selector": selector,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
        }

        self.lifecycle.add_screenshot_to_session(session_id, {
            "screenshot_id": metadata.screenshot_id,
            "image_path": image_path,
            "metadata": metadata.to_dict(),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

        return capture_result, metadata

    async def capture_region(
        self,
        page_url: str,
        session_id: str,
        milestone_id: str,
        task_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        options: Optional[CaptureOptions] = None,
    ) -> Tuple[Dict[str, Any], ScreenshotMetadata]:
        """
        Capture a cropped region of the viewport.

        Args:
            page_url: URL of the page to capture
            session_id: Session identifier
            milestone_id: Milestone identifier
            task_id: Task identifier
            x: X coordinate of top-left corner (relative to viewport)
            y: Y coordinate of top-left corner (relative to viewport)
            width: Width of region to capture
            height: Height of region to capture
            options: Capture options (uses defaults if not provided)

        Returns:
            Tuple of (capture_result, metadata)
        """
        # Handle None options for capture_mode
        effective_capture_mode = CaptureMode.REGION if options is None else options.capture_mode
        
        # Generate screenshot ID FIRST using metadata generator's internal method
        import uuid
        screenshot_id = f"{milestone_id.replace('.', '_')}_{task_id.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Generate image path - use screenshot_id (now available) in filename
        storage_dir = self.storage._get_storage_directory(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
        )
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        region_str = f"{x},{y}+{width}x{height}"
        screenshot_filename = f"{screenshot_id}_{effective_capture_mode.value.replace('_', '-')}_{region_str[:20]}_{timestamp}.png" if options else f"{screenshot_id}_region_{region_str[:20]}_{timestamp}.png"
        
        image_path = f"session/{session_id.replace('/', '_')}/milestone/{milestone_id.replace('.', '_')}/task/{task_id.replace(' ', '_')}/{screenshot_filename}"

        # Generate screenshot ID and metadata - NOW with image_path provided
        metadata = self.metadata_generator.generate_new_metadata(
            session_id=session_id,
            milestone_id=milestone_id,
            task_id=task_id,
            image_path=image_path,  # FIX: Provide image_path parameter
            capture_mode=effective_capture_mode,
            url=page_url,
        )

        # Create metadata file (placeholder for actual image)
        self._create_metadata_file(image_path, metadata)

        capture_result = {
            "status": "success",
            "screenshot_id": metadata.screenshot_id,
            "image_path": image_path,
            "capture_mode": effective_capture_mode.value if options else CaptureMode.REGION.value,
            "region": f"{x},{y}+{width}x{height}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
        }

        self.lifecycle.add_screenshot_to_session(session_id, {
            "screenshot_id": metadata.screenshot_id,
            "image_path": image_path,
            "metadata": metadata.to_dict(),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

        return capture_result, metadata

    # ============================================================================
    # STORAGE OPERATIONS
    # ============================================================================

    def _create_metadata_file(self, image_path: str, metadata: ScreenshotMetadata) -> None:
        """Create metadata file for a screenshot."""
        storage_dir = self.storage._get_storage_directory(
            session_id=metadata.session_id,
            milestone_id=metadata.milestone_id,
            task_id=metadata.task_id,
        )
        
        # Create directory if it doesn't exist
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate full path - FIX: use / instead of + for Path concatenation
        full_image_path = str(storage_dir / metadata.screenshot_id[:8] / ".png")
        
        # Create metadata JSON file
        metadata_path = str(storage_dir / f"{metadata.screenshot_id}.json")
        
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            self.storage._known_hashes[metadata.screenshot_id] = metadata_path
        except Exception as e:
            logging.warning(f"Failed to create metadata file for {metadata.screenshot_id}: {e}")

    def get_metadata(self, screenshot_id: str) -> Optional[ScreenshotMetadata]:
        """
        Get metadata for a specific screenshot.

        Args:
            screenshot_id: The screenshot ID to look up

        Returns:
            ScreenshotMetadata or None if not found
        """
        return self.metadata_generator.get_metadata(screenshot_id)

    def list_screenshots(
        self, 
        session_id: Optional[str] = None,
        capture_mode: Optional[CaptureMode] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all stored screenshots.

        Args:
            session_id: Filter by session ID (optional)
            capture_mode: Filter by capture mode (optional)

        Returns:
            List of screenshot information dictionaries
        """
        paths = self.storage.get_all_stored_paths(session_id)
        
        results = []
        for path in paths:
            metadata = self.metadata_generator.get_metadata(path.split("/")[-1].replace(".json", ""))
            if metadata:
                results.append({
                    "screenshot_id": metadata.screenshot_id,
                    "image_path": metadata.image_path,
                    "capture_mode": metadata.capture_mode.value,
                    "captured_at": metadata.captured_at,
                    "file_size_bytes": metadata.file_size_bytes,
                    "session_id": metadata.session_id,
                })
        
        return results

    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================

    def _ensure_session(self, session_id: str) -> None:
        """Ensure a session exists in the lifecycle manager."""
        if not self.lifecycle.get_session(session_id):
            import uuid
            now = datetime.now(timezone.utc).isoformat()
            
            self.lifecycle._sessions[session_id] = {
                "name": session_id,
                "id": f"sess_{session_id}_{uuid.uuid4().hex[:8]}",
                "created_at": now,
                "status": "active",
                "last_accessed": now,
                "screenshot_count": 0,
                "metadata": {},
                "screenshots": [],
            }

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a screenshot session."""
        return self.lifecycle.get_session(session_id)

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return self.lifecycle.get_all_sessions()

    # ============================================================================
    # ARCHIVE OPERATIONS
    # ============================================================================

    async def archive_session(
        self, 
        session_id: str, 
        keep_screenshots: bool = True,
    ) -> Optional[str]:
        """
        Archive a screenshot session.

        Args:
            session_id: Session ID to archive
            keep_screenshots: Whether to keep screenshots or remove them

        Returns:
            Path to archived session or None if failed
        """
        session = self.lifecycle.get_session(session_id)
        if not session:
            return None
        
        # Update status to completed
        session["status"] = "completed"
        
        archive_result = self.lifecycle.archive_session(session_id)
        
        if not keep_screenshots:
            self.storage.clear_storage()
        
        return archive_result

    # ============================================================================
    # CLEANUP OPERATIONS
    # ============================================================================

    async def cleanup_expired(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform cleanup of expired screenshots.

        Args:
            hours: Override retention hours (optional, uses policy default if not provided)

        Returns:
            Summary of cleanup operations
        """
        return await self._run_cleanup(hours=hours or 24)

    async def cleanup_old_sessions(self, days: int = 7) -> Dict[str, Any]:
        """
        Remove old sessions.

        Args:
            days: Keep sessions newer than this many days

        Returns:
            Summary of cleanup operations
        """
        return self.lifecycle.cleanup_old_sessions(days_to_keep=days)

    async def archive_idle_sessions(self, hours: int = 48) -> List[str]:
        """
        Archive idle sessions.

        Args:
            hours: Hours of inactivity before archiving

        Returns:
            List of archived session paths
        """
        return self.lifecycle.archive_all_idle_sessions(timeout_hours=hours)

    async def _run_cleanup(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """Run cleanup operations."""
        import shutil
        
        cleaned: Dict[str, Any] = {
            "screenshots_removed": 0,
            "sessions_archived": 0,
            "bytes_freed": 0,
        }
        
        # Clean up expired files based on time since capture
        now = datetime.now(timezone.utc)
        
        session_dir = Path("runtime/screenshots/session")
        if session_dir.exists():
            for dir_entry in session_dir.iterdir():
                if not dir_entry.is_dir() or dir_entry.name.startswith("__"):
                    continue
                
                try:
                    # Check each file's age
                    expired_files = []
                    for file_path in dir_entry.glob("*.png"):
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        age_hours = (now - file_mtime).total_seconds() / 3600
                        
                        if hours and age_hours > hours:
                            expired_files.append(file_path)
                    
                    # Remove expired files
                    for file_path in expired_files:
                        try:
                            file_path.unlink()
                            cleaned["screenshots_removed"] += 1
                            cleaned["bytes_freed"] += file_path.stat().st_size
                        except Exception as e:
                            logging.warning(f"Failed to remove {file_path}: {e}")
                
                except Exception as e:
                    logging.warning(f"Error processing session dir {dir_entry}: {e}")
        
        # Archive idle sessions
        idle_sessions = self.lifecycle.archive_all_idle_sessions(timeout_hours=48)
        cleaned["sessions_archived"] = len(idle_sessions)
        
        return cleaned

    # ============================================================================
    # OPTIMIZATION OPERATIONS
    # ============================================================================

    def optimize_screenshot(
        self, 
        image_path: str,
        level: OptimizationLevel = OptimizationLevel.MEDIUM,
    ) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        """
        Optimize a screenshot.

        Args:
            image_path: Path to the image to optimize
            level: Optimization level (LOW, MEDIUM, HIGH)

        Returns:
            Tuple of (optimized_path, stats) or (None, None) if failed
        """
        try:
            optimized_path, stats = self.optimizer.optimize_image(str(image_path))
            
            result = {
                "status": "success",
                "original_size": stats.original_size,
                "optimized_size": stats.optimized_size,
                "compression_ratio": stats.compression_ratio,
            }
            
            return optimized_path, {"path": str(optimized_path), "stats": result}
        except Exception as e:
            return None, {
                "status": "error",
                "error": str(e),
            }

    # ============================================================================
    # COMMUNICATION BUS INTEGRATION
    # ============================================================================

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the screenshot service.

        Returns:
            Service information dictionary
        """
        return {
            "service_name": "ScreenshotCaptureService",
            "version": "1.0",
            "base_path": str(self.base_path),
            "capabilities": [
                "full_page_capture",
                "viewport_capture", 
                "element_capture",
                "region_capture",
                "metadata_generation",
                "duplicate_detection",
                "optimization",
                "session_management",
                "archive_operations",
                "cleanup_policies",
            ],
            "storage_path": str(self.storage.base_path),
            "registered_methods": {
                "capture_full_page": self.capture_full_page,
                "capture_element": self.capture_element,
                "capture_region": self.capture_region,
                "get_metadata": self.get_metadata,
                "archive_session": self.archive_session,
                "cleanup_expired": self.cleanup_expired,
            }
        }


# ============================================================================
# FACTORY FUNCTIONS FOR COMMUNICATION BUS
# ============================================================================

async def create_screenshot_service(config: Optional[Dict[str, Any]] = None) -> ScreenshotCaptureService:
    """
    Factory function to create a screenshot service.

    Args:
        config: Service configuration (optional)

    Returns:
        Configured ScreenshotCaptureService instance
    """
    if config is None:
        return ScreenshotCaptureService()
    
    # Extract configuration values
    base_path = config.get("base_path", "runtime/screenshots")
    
    # Create service with default configuration
    service = ScreenshotCaptureService(base_path=base_path)
    
    return service


async def close_screenshot_service(service: ScreenshotCaptureService) -> None:
    """Close the screenshot service."""
    # No special cleanup needed for this service
    pass


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ScreenshotCaptureService",
    "CaptureOptions",
    "create_screenshot_service",
    "close_screenshot_service",
]
