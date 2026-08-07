"""
Screenshot Capture Service for Sanskriti AI Studio.

This service is independent from both the Browser Runtime and the Vision Agent.
It captures, stores, organizes, and manages browser screenshots.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    SCREENSHOT SERVICE                          │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │              ScreenshotCaptureService                     │ │
    │  │  - Capture full page screenshots                           │ │
    │  │  - Capture viewport screenshots                             │ │
    │  │  - Capture element screenshots                              │ │
    │  │  - Capture cropped region screenshots                       │ │
    │  │  - Store screenshots in structured format                    │ │
    │  │  - Generate metadata for each capture                       │ │
    │  │  - Implement PNG optimization                               │ │
    │  │  - Manage screenshot lifecycle (session/archive/cleanup)    │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │                                                                │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │                    Storage Layer                          │ │
    │  │  - Directory-based storage (PNG + Metadata JSON)          │ │
    │  │  - Session/task hierarchy                                   │ │
    │  │  - Duplicate detection                                      │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │                                                                │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │                 Communication Bus Integration               │ │
    │  │  - Register service methods with router                     │ │
    │  │  - Expose capture, metadata, lifecycle operations           │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │                                                                │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │              Screenshot Metadata Generator                 │ │
    │  │  - Generate unique IDs                                      │ │
    │  │  - Capture timestamps                                        │ │
    │  │  - Store dimensions, browser info                           │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │                                                                │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │           Lifecycle Manager                               │ │
    │  │  - Session creation/archive                                 │ │
    │  │  - Expiration handling                                      │ │
    │  │  - Cleanup policy enforcement                               │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │                                                                │
    └─────────────────────────────────────────────────────────────┘

CRITICAL: Qwen 3.5 is TEXT-ONLY. This service captures screenshots for the 
Vision Agent to analyze. Never send image data directly to LM Studio text-only model.

Version: 1.0
Last Updated: 2026-08-07
"""

from .service import ScreenshotCaptureService, CaptureMode, CaptureOptions
from .storage import ScreenshotStorage, StorageConfig
from .metadata import ScreenshotMetadata, MetadataGenerator
from .lifecycle import LifecycleManager, CleanupPolicy
from .optimization import ImageOptimizer, OptimizationConfig

__all__ = [
    # Main Service
    "ScreenshotCaptureService",
    # Capture modes
    "CaptureMode",
    "CaptureOptions",
    # Storage
    "ScreenshotStorage",
    "StorageConfig",
    # Metadata
    "ScreenshotMetadata",
    "MetadataGenerator",
    # Lifecycle
    "LifecycleManager",
    "CleanupPolicy",
    # Optimization
    "ImageOptimizer",
    "OptimizationConfig",
]
