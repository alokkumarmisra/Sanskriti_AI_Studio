#!/usr/bin/env python3
"""
Vision Analysis Report Schema for Sanskriti AI Studio.

This module provides a standardized schema for vision analysis results,
ensuring consistent output from the Vision Pipeline across all analysis tasks.

The schema supports:
- General UI inspection
- Component detection
- OCR text extraction
- Error message detection
- Layout analysis
- Visual regression
- Element verification

Version: 1.0
Last Updated: 2026-08-07
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# =============================================================================
# VISION ANALYSIS REPORT SCHEMA (Phase 3)
# =============================================================================

class VisionAnalysisReport:
    """
    Standard schema for vision analysis results.
    
    This class ensures consistent output from the Vision Pipeline with all required fields:
    - Analysis ID
    - Session ID
    - Screenshot ID
    - Timestamp
    - URL
    - Page Title
    - Summary
    - Detected Components
    - Missing Components
    - OCR Text
    - Visual Issues
    - Warnings
    - Suggested Improvements
    - Confidence Score
    - Processing Time
    """

    def __init__(
        self,
        analysis_id: str,
        session_id: str,
        screenshot_id: str,
        url: str,
        page_title: Optional[str] = None,
        summary: Optional[str] = None,
        detected_components: Optional[List[Dict[str, Any]]] = None,
        missing_components: Optional[List[Dict[str, Any]]] = None,
        ocr_text: Optional[str] = None,
        visual_issues: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[str]] = None,
        suggested_improvements: Optional[List[str]] = None,
        confidence_score: Optional[float] = None,
        processing_time_ms: Optional[float] = None,
        timestamp: Optional[str] = None,
    ):
        """
        Initialize a Vision Analysis Report.

        Args:
            analysis_id: Unique identifier for this analysis
            session_id: Session context identifier
            screenshot_id: Screenshot reference identifier
            url: Page URL analyzed
            page_title: Extracted page title (optional)
            summary: Overall analysis summary
            detected_components: List of detected UI components
            missing_components: List of expected but absent components
            ocr_text: Extracted text from the screenshot
            visual_issues: List of layout/rendering issues found
            warnings: List of non-critical findings
            suggested_improvements: List of recommendations
            confidence_score: Quality score (0-100)
            processing_time_ms: Duration in milliseconds
            timestamp: Analysis timestamp in ISO-8601 format
        """
        self.analysis_id = analysis_id
        self.session_id = session_id
        self.screenshot_id = screenshot_id
        self.url = url
        self.page_title = page_title
        self.summary = summary
        self.detected_components = detected_components or []
        self.missing_components = missing_components or []
        self.ocr_text = ocr_text or ""
        self.visual_issues = visual_issues or []
        self.warnings = warnings or []
        self.suggested_improvements = suggested_improvements or []
        self.confidence_score = confidence_score
        self.processing_time_ms = processing_time_ms
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization/storage."""
        return {
            "analysis_id": self.analysis_id,
            "session_id": self.session_id,
            "screenshot_id": self.screenshot_id,
            "url": self.url,
            "page_title": self.page_title,
            "summary": self.summary,
            "detected_components": self.detected_components,
            "missing_components": self.missing_components,
            "ocr_text": self.ocr_text,
            "visual_issues": self.visual_issues,
            "warnings": self.warnings,
            "suggested_improvements": self.suggested_improvements,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisionAnalysisReport":
        """Create a VisionAnalysisReport from a dictionary."""
        return cls(
            analysis_id=data.get("analysis_id", ""),
            session_id=data.get("session_id", ""),
            screenshot_id=data.get("screenshot_id", ""),
            url=data.get("url", ""),
            page_title=data.get("page_title"),
            summary=data.get("summary"),
            detected_components=data.get("detected_components", []),
            missing_components=data.get("missing_components", []),
            ocr_text=data.get("ocr_text", ""),
            visual_issues=data.get("visual_issues", []),
            warnings=data.get("warnings", []),
            suggested_improvements=data.get("suggested_improvements", []),
            confidence_score=data.get("confidence_score"),
            processing_time_ms=data.get("processing_time_ms"),
            timestamp=data.get("timestamp"),
        )

    @classmethod
    def empty(cls, analysis_id: str, session_id: str, screenshot_id: str, url: str) -> "VisionAnalysisReport":
        """Create an empty report template with required fields."""
        return cls(
            analysis_id=analysis_id,
            session_id=session_id,
            screenshot_id=screenshot_id,
            url=url,
            page_title=None,
            summary="",
            detected_components=[],
            missing_components=[],
            ocr_text="",
            visual_issues=[],
            warnings=[],
            suggested_improvements=[],
            confidence_score=None,
            processing_time_ms=None,
        )

    def is_success(self) -> bool:
        """Check if analysis was successful."""
        return bool(self.summary) and "error" not in self.summary.lower()

    def has_issues(self) -> bool:
        """Check if analysis detected issues."""
        return (
            len(self.visual_issues) > 0 or
            len(self.missing_components) > 0 or
            len(self.warnings) > 0
        )


# =============================================================================
# EMPTY REPORT FACTORY (for error cases)
# =============================================================================

def create_empty_report(analysis_id: str, session_id: str, screenshot_id: str, url: str) -> VisionAnalysisReport:
    """
    Create an empty report for error or timeout cases.
    
    Args:
        analysis_id: Analysis identifier
        session_id: Session context
        screenshot_id: Screenshot reference
        url: Page URL
        
    Returns:
        Empty VisionAnalysisReport instance
    """
    return VisionAnalysisReport.empty(analysis_id, session_id, screenshot_id, url)


# =============================================================================
# SCHEMA DOCUMENTATION (for Reference)
# =============================================================================

SCHEMA_SPECIFICATION = {
    "type": "VisionAnalysisReport",
    "description": "Standard schema for vision analysis results from the Vision Pipeline",
    "required_fields": [
        "analysis_id",      # Unique identifier (UUID or task-specific ID)
        "session_id",       # Session context identifier
        "screenshot_id",    # Screenshot reference identifier
        "url",              # Page URL analyzed
    ],
    "optional_fields": [
        "page_title",       # Extracted page title
        "summary",          # Overall analysis summary (string, max ~5000 chars)
        "detected_components",  # List of detected UI components
        "missing_components",   # Expected but absent components
        "ocr_text",         # Extracted text content
        "visual_issues",    # Layout/rendering issues found
        "warnings",         # Non-critical findings
        "suggested_improvements",  # Recommendations for improvement
        "confidence_score", # Quality score (float, 0-100)
        "processing_time_ms",   # Duration in milliseconds
        "timestamp",        # Analysis timestamp (ISO-8601 UTC)
    ],
    "example": {
        "analysis_id": "STEP235_20260807_analysis_uuid1234",
        "session_id": "my_session",
        "screenshot_id": "milestone_2.0_task_capture_uuid5678",
        "url": "https://example.com/dashboard",
        "page_title": "Dashboard - Example App",
        "summary": "The dashboard displays user statistics with 3 widget cards...",
        "detected_components": [
            {"type": "header", "text": "Dashboard", "location": "top"},
            {"type": "widget_card", "title": "User Stats", "location": "center-left"},
        ],
        "missing_components": [],
        "ocr_text": "Welcome to the Dashboard\nUser: Admin\nDate: 2026-08-07...",
        "visual_issues": [],
        "warnings": ["Widget card shadows inconsistent"],
        "suggested_improvements": ["Standardize shadow styles across all cards"],
        "confidence_score": 95.5,
        "processing_time_ms": 2340.5,
        "timestamp": "2026-08-07T15:30:45.123456+00:00",
    }
}


__all__ = [
    "VisionAnalysisReport",
    "create_empty_report",
    "SCHEMA_SPECIFICATION",
]
