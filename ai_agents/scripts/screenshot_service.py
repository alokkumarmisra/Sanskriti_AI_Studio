#!/usr/bin/env python3
"""
Screenshot Service Runtime for Sanskriti AI Studio.

This runtime provides the Screenshot Capture Service that is independent from both
the Browser Runtime and the Vision Agent. It captures, stores, organizes, and manages
browser screenshots.

CRITICAL: Qwen 3.5 is TEXT-ONLY. This service captures screenshots for the 
Vision Agent to analyze. Never send image data directly to LM Studio text-only model.

Version: 1.0
Last Updated: 2026-08-07
"""

import argparse
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING


# Add ai_agents to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("screenshot_service")


# ============================================================================
# Screenshot Service Module Import and Integration
# ============================================================================

def _import_screenshots():
    """Import the screenshots module from ai_agents.screenshots."""
    import sys
    
    if AI_AGENTS_ROOT not in sys.path:
        sys.path.insert(0, AI_AGENTS_ROOT)
    
    # Add current dir to path for relative imports
    sys.path.insert(0, SCRIPT_DIR)
    
    try:
        from ai_agents.screenshots.service import ScreenshotCaptureService, CaptureOptions
        from ai_agents.screenshots.metadata import CaptureMode, BrowserType, OptimizationLevel
        from ai_agents.screenshots.storage import StorageConfig
        from ai_agents.screenshots.lifecycle import CleanupPolicy
        
        return {
            "ScreenshotCaptureService": ScreenshotCaptureService,
            "CaptureOptions": CaptureOptions,
            "CaptureMode": CaptureMode,
            "BrowserType": BrowserType,
            "OptimizationLevel": OptimizationLevel,
            "StorageConfig": StorageConfig,
            "CleanupPolicy": CleanupPolicy,
        }
    except Exception as e:
        logger.error(f"[IMPORT-ERROR] Failed to import screenshots module: {e}")
        return {}


# ============================================================================
# Screenshot Service Factory Function for Communication Bus
# ============================================================================

if TYPE_CHECKING:
    # Import for type checking only (not executed at runtime)
    from ai_agents.screenshots.service import ScreenshotCaptureService as _ScreenshotCaptureService
    
async def create_screenshot_service(config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """
    Factory function to create a screenshot service (for Communication Bus integration).
    
    Args:
        config: Service configuration (optional)
        
    Returns:
        Configured ScreenshotCaptureService instance or None
    """
    imports = _import_screenshots()
    
    if not imports:
        raise ImportError("Screenshot service module not available. Please ensure ai_agents.screenshots is properly installed.")
    
    # Create default configuration
    base_path = config.get("base_path", "runtime/screenshots") if config else "runtime/screenshots"
    
    # Create and return service
    service = imports["ScreenshotCaptureService"](base_path=base_path)
    logger.info(f"[SCREENSHOT-SERVICE] Service created at: {base_path}")
    
    return service


async def close_screenshot_service(service: Any) -> None:
    """Close the screenshot service."""
    # Type is imported dynamically, so use Any for type hint
    logger.info("[SCREENSHOT-SERVICE] Service closed (no cleanup needed)")


# ============================================================================
# SERVICE REGISTRATION WITH COMMUNICATION BUS
# ============================================================================

def register_screenshot_service() -> Dict[str, Any]:
    """
    Register the Screenshot Service with the communication bus.
    
    Returns:
        Registration confirmation dictionary
    """
    try:
        from ai_agents.screenshots.service import ScreenshotCaptureService
        service_type = ScreenshotCaptureService
    except ImportError:
        service_type = None
    
    return {
        "service_name": service_type.__name__ if service_type else "ScreenshotCaptureService",
        "version": "1.0",
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
        "registered_methods": {
            "capture_full_page": "async capture_full_page(page_url, session_id, milestone_id, task_id)",
            "capture_element": "async capture_element(page_url, session_id, milestone_id, task_id, selector)",
            "capture_region": "async capture_region(page_url, session_id, milestone_id, task_id, x, y, width, height)",
            "get_metadata": "get_metadata(screenshot_id)",
            "archive_session": "async archive_session(session_id, keep_screenshots=True)",
            "cleanup_expired": "async cleanup_expired(hours=None)",
        },
        "text_only": False,  # This service handles images for Vision Agent
    }


# ============================================================================
# MAIN CLI ENTRY POINT
# ============================================================================

def main() -> None:
    """CLI entry point for the Screenshot Service Runtime."""
    parser = argparse.ArgumentParser(
        description="Screenshot Service Runtime for Sanskriti AI Studio"
    )
    parser.add_argument(
        "--init", 
        action="store_true",
        help="Initialize the service and show available methods"
    )
    parser.add_argument(
        "--list-methods",
        action="store_true",
        help="List available service methods"
    )
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Show service information"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SCREENSHOT CAPTURE SERVICE RUNTIME - Sanskriti AI Studio")
    print("=" * 60)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - This service captures screenshots for the Vision Agent")
    print()
    
    if args.init:
        print("[INIT] Service initialized successfully")
        print("[INFO] Base path: runtime/screenshots")
        print("[INFO] Storage directory will be created on first capture")
    
    if args.list_methods:
        print("\n[A VAILABLE METHODS]")
        print("  - capture_full_page()  : Capture entire scrollable page")
        print("  - capture_element()    : Capture specific DOM element")
        print("  - capture_region()     : Capture cropped viewport region")
        print("  - get_metadata()       : Get metadata for a screenshot")
        print("  - archive_session()    : Archive completed session")
        print("  - cleanup_expired()    : Remove expired screenshots")
    
    if args.info:
        print("\n[S ERVICE INFORMATION]")
        info = register_screenshot_service()
        print(f"  Name: {info['service_name']}")
        print(f"  Version: {info['version']}")
        print(f"  Capabilities: {', '.join(info['capabilities'][:3])}...")
    
    print("\n" + "=" * 60)
    print("SCREENSHOT SERVICE READY")
    print("=" * 60)


if __name__ == "__main__":
    main()
