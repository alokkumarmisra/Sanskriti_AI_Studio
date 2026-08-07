#!/usr/bin/env python3
"""
Vision Analysis Pipeline for Sanskriti AI Studio.

This module provides the complete end-to-end pipeline that connects all existing
Vision components into a unified orchestration system.

Architecture:
    Browser Runtime → Screenshot Service → Vision Agent → Vision Service → Model Router → LM Studio (Qwen2.5-VL)

The pipeline automatically processes screenshots using the local Qwen2.5-VL model
and produces structured analysis results.

CRITICAL: Qwen 3.5 is TEXT-ONLY. This pipeline uses the vision model (Qwen2.5-VL) exclusively.

Version: 1.0
Last Updated: 2026-08-07
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import existing components (STEP 23.1-23.4)
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPTS_DIR)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")

from ai_agents.screenshots.service import ScreenshotCaptureService
from ai_agents.screenshots.metadata import MetadataGenerator
from ai_agents.scripts.model_router import ModelRouter, ModelNotFoundError
from ai_agents.scripts.vision_response_schema import VisionAnalysisReport


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

DEFAULT_BASE_URL = "http://localhost:1234"
DEFAULT_TIMEOUT = 300  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_VISION_MODEL = "Qwen2.5-VL-8B"


# =============================================================================
# LIFECYCLE EVENTS (Phase 4)
# =============================================================================

EVENT_ANALYSIS_STARTED = "analysis_started"
EVENT_SCREENSHOT_CAPTURED = "screenshot_captured"
EVENT_VISION_REQUEST_SENT = "vision_request_sent"
EVENT_VISION_RESPONSE_RECEIVED = "vision_response_received"
EVENT_ANALYSIS_COMPLETED = "analysis_completed"
EVENT_ANALYSIS_FAILED = "analysis_failed"


def publish_event(event_type: str, data: Dict[str, Any]) -> None:
    """Publish a lifecycle event via the Communication Bus."""
    event_data = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    
    logger = logging.getLogger("vision_pipeline")
    logger.info(f"[EVENT-{event_type}] {json.dumps(event_data, default=str)}")


# =============================================================================
# ERROR HANDLING & RECOVERY (Phase 5)
# =============================================================================

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class ScreenshotMissingError(PipelineError):
    """Raised when screenshot cannot be captured or is missing."""
    pass


class VisionTimeoutError(PipelineError):
    """Raised when vision request times out."""
    pass


class LmStudioUnavailableError(PipelineError):
    """Raised when LM Studio is unavailable."""
    pass


class InvalidResponseError(PipelineError):
    """Raised when model response is invalid or corrupt."""
    pass


async def handle_screenshot_error(error: Exception, retry_count: int = 0, max_retries: int = 2) -> bool:
    """Handle screenshot capture errors with retry logic."""
    if retry_count < max_retries:
        wait_time = min(2 ** retry_count * 1, 30)
        logger = logging.getLogger("vision_pipeline")
        logger.warning(f"[RECOVERY] Screenshot error, retry {retry_count + 1}/{max_retries} in {wait_time}s...")
        await asyncio.sleep(wait_time)
        return True
    return False


async def handle_vision_timeout(error: Exception, retry_count: int = 0, max_retries: int = DEFAULT_MAX_RETRIES, backoff_factor: float = DEFAULT_BACKOFF_FACTOR) -> bool:
    """Handle vision timeout errors with exponential backoff."""
    if retry_count < max_retries:
        wait_time = min(backoff_factor ** retry_count, 60)
        logger = logging.getLogger("vision_pipeline")
        logger.warning(f"[RECOVERY] Vision timeout, retry {retry_count + 1}/{max_retries} in {wait_time}s...")
        await asyncio.sleep(wait_time)
        return True
    return False


async def handle_lmstudio_error(error: Exception, retry_count: int = 0, max_retries: int = DEFAULT_MAX_RETRIES) -> bool:
    """Handle LM Studio connection errors with health check and retry."""
    if retry_count < max_retries:
        wait_time = min(3 ** retry_count * 1, 45)
        logger = logging.getLogger("vision_pipeline")
        logger.warning(f"[RECOVERY] LM Studio error, retry {retry_count + 1}/{max_retries} in {wait_time}s...")
        
        try:
            router = ModelRouter()
            if not router.is_healthy():
                logger.info("[RECOVERY] LM Studio still unavailable, will retry...")
        except Exception:
            pass
        
        await asyncio.sleep(wait_time)
        return True
    return False


# =============================================================================
# EXECUTION HISTORY (Phase 7)
# =============================================================================

HISTORY_FILE = os.path.join(STATE_DIR, "vision_history.jsonl")

def ensure_history_dir() -> None:
    """Ensure history directory exists."""
    history_path = Path(HISTORY_FILE).parent
    history_path.mkdir(parents=True, exist_ok=True)


def append_to_history(entry: Dict[str, Any]) -> None:
    """Append a history entry to the JSONL file."""
    ensure_history_dir()
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def load_history() -> List[Dict[str, Any]]:
    """Load all history entries from the file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    
    entries = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def get_history_by_analysis_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Get history entry by analysis ID."""
    history = load_history()
    for entry in history:
        if entry.get("analysis_id") == analysis_id:
            return entry
    return None


# =============================================================================
# VISION PIPELINE ORCHESTRATOR (Phase 1)
# =============================================================================

class VisionPipeline:
    """Main Vision Pipeline Orchestrator that coordinates the full analysis flow."""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES, backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
                 vision_model: str = DEFAULT_VISION_MODEL):
        """Initialize the Vision Pipeline."""
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.vision_model = vision_model
        
        # Initialize components (reusing existing STEP 23.1-23.4 components)
        self.metadata_generator = MetadataGenerator()
        self.screenshot_service = ScreenshotCaptureService(
            base_path="runtime/screenshots",
            metadata_generator=self.metadata_generator,
        )
        
        # Model Router for model selection (STEP 23.2)
        try:
            self.model_router = ModelRouter()
            self.vision_model = self.model_router.get_vision_model()
            logger = logging.getLogger("vision_pipeline")
            logger.info(f"[PIPELINE] Using vision model from router: {self.vision_model}")
        except ModelNotFoundError as e:
            logger = logging.getLogger("vision_pipeline")  # Create logger here to avoid unbound error
            logger.warning(f"[PIPELINE] No vision model configured in router, using default: {DEFAULT_VISION_MODEL}")
            self.vision_model = DEFAULT_VISION_MODEL

    async def run_analysis(
        self, page_url: str, session_id: str, milestone_id: str, task_id: str,
        analysis_type: str = "general_inspection", baseline_path: Optional[str] = None,
        comparison_path: Optional[str] = None, expected_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Dict[str, Any], VisionAnalysisReport]:
        """Run the full analysis pipeline with lifecycle events and history tracking."""
        start_time = datetime.now(timezone.utc)
        analysis_id = f"STEP235_{datetime.now().strftime('%Y%m%d')}_{'_'.join([session_id[:8], milestone_id.replace('.', '_'), task_id[:12]])}"
        
        # Create execution history entry
        history_entry = {
            "analysis_id": analysis_id, "session_id": session_id,
            "milestone_id": milestone_id, "task_id": task_id,
            "analysis_type": analysis_type, "start_time": start_time.isoformat(),
            "status": "running",
        }
        
        # Step 1: Publish Analysis Started event (Phase 4)
        publish_event(EVENT_ANALYSIS_STARTED, {
            "analysis_id": analysis_id, "session_id": session_id,
            "milestone_id": milestone_id, "task_id": task_id,
            "analysis_type": analysis_type, "url": page_url or "",
        })
        
        # Step 2: Capture screenshot (if not provided)
        image_path = None
        if not baseline_path and not comparison_path:
            try:
                capture_result, metadata = await self.screenshot_service.capture_full_page(
                    page_url=page_url, session_id=session_id, milestone_id=milestone_id, task_id=task_id,
                )
                image_path = metadata.image_path
                
                publish_event(EVENT_SCREENSHOT_CAPTURED, {
                    "screenshot_id": metadata.screenshot_id, "image_path": image_path, "url": page_url,
                })
            except Exception as e:
                error_msg = str(e)[:500]
                logger = logging.getLogger("vision_pipeline")
                logger.error(f"[PIPELINE] Screenshot capture failed: {error_msg}")
                
                publish_event(EVENT_ANALYSIS_FAILED, {
                    "analysis_id": analysis_id, "screenshot_id": "",
                    "error_type": "screenshot_capture", "error_message": error_msg,
                })
                
                return {"status": "failed", "type": "screenshot_capture_failed", "error": str(e)}, VisionAnalysisReport.empty(analysis_id, session_id, "screenshot_error", page_url or "")
        
        # Step 3: Process image with Vision Agent (STEP 23.1) via chat_with_vision_model_from_image
        # Determine the actual image path - must be non-None
        actual_image_path = image_path or baseline_path or comparison_path
        
        if actual_image_path is None:
            error_msg = "No valid image path provided: neither screenshot was captured nor baseline/comparison paths were specified."
            publish_event(EVENT_ANALYSIS_FAILED, {
                "analysis_id": analysis_id,
                "error_type": "no_image_path", "error_message": error_msg,
            })
            return {"status": "failed", "type": "no_image_path", "error": error_msg}, VisionAnalysisReport.empty(analysis_id, session_id, "", page_url or "")
        
        try:
            raw_result = self._process_image_with_vision_agent(
                image_path=actual_image_path,
                analysis_type=analysis_type, expected_elements=expected_elements,
            )
        except Exception as e:
            error_msg = str(e)[:500]
            logger = logging.getLogger("vision_pipeline")
            logger.error(f"[PIPELINE] Vision agent processing failed: {error_msg}")
            
            publish_event(EVENT_ANALYSIS_FAILED, {
                "analysis_id": analysis_id,
                "screenshot_id": (actual_image_path.split("/")[-1].replace(".png", "") if actual_image_path else ""),
                "error_type": "vision_processing", "error_message": error_msg,
            })
            
            return {"status": "failed", "type": "vision_processing_failed", "error": error_msg}, VisionAnalysisReport.empty(analysis_id, session_id, (actual_image_path.split("/")[-1].replace(".png", "") if actual_image_path else ""), page_url or "")
        
        # Step 4: Call Vision Service (STEP 23.2) - Already integrated via chat_with_vision_model_from_image
        
        end_time = datetime.now(timezone.utc)
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Step 5: Parse response and generate structured report (Phase 3)
        report = self._generate_structured_report(
            analysis_id=analysis_id, session_id=session_id,
            screenshot_id=(actual_image_path.split("/")[-1].replace(".png", "") if actual_image_path else ""),
            url=page_url or "", raw_result=raw_result, processing_time_ms=processing_time_ms,
        )
        
        # Step 6: Update history and publish Completed event (Phase 4)
        history_entry["end_time"] = end_time.isoformat()
        history_entry["duration_ms"] = str(int(processing_time_ms))
        history_entry["status"] = "completed"
        history_entry["report_summary"] = report.summary[:200] if report.summary else ""
        
        append_to_history(history_entry)
        
        publish_event(EVENT_ANALYSIS_COMPLETED, {
            "analysis_id": analysis_id,
            "screenshot_id": (actual_image_path.split("/")[-1].replace(".png", "") if actual_image_path else ""),
            "status": "completed", "summary": report.summary[:200] if report.summary else "",
        })
        
        return {"status": "success", "type": analysis_type, "report": report.to_dict(), "raw_response": raw_result}, report

    def _process_image_with_vision_agent(self, image_path: str, analysis_type: str,
                                         expected_elements: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Process image using Vision Agent (STEP 23.1)."""
        # Import the standalone function from vision_client (FIXED: was incorrectly importing from vision_agent)
        import sys
        sys.path.insert(0, SCRIPTS_DIR)
        
        try:
            from scripts.vision_client import chat_with_vision_model_from_image
        except (ImportError, ModuleNotFoundError):
            # Fallback to direct LM Studio API if script doesn't exist and openai is available
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(base_url=self.base_url, api_key="not-needed")
                prompt = self._build_prompt(analysis_type, expected_elements)
                response = client.chat.completions.create(
                    model=self.vision_model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": f"file://{image_path}"},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                return {
                    "choices": [{"message": {"content": response.choices[0].message.content}}],
                    "model": self.vision_model,
                }
            except (ImportError, ModuleNotFoundError):
                raise ImportError("Neither vision_client script nor openai package is available for LM Studio connection.")

        # Call the vision client function
        report = chat_with_vision_model_from_image(
            image_path=image_path,
            prompt=self._build_prompt(analysis_type, expected_elements),
            base_url=self.base_url,
        )
        return report

    def _build_prompt(self, analysis_type: str, expected_elements: Optional[List[Dict[str, Any]]]) -> str:
        """Build a prompt based on analysis type."""
        if analysis_type == "general_inspection":
            return "Analyze this UI screenshot and provide a comprehensive visual report."
        elif analysis_type == "component_detection":
            return "Detect all UI components in this screenshot."
        elif analysis_type == "ocr_extraction":
            return "Extract all visible text from this image."
        elif analysis_type == "error_detection":
            return "Detect and extract any error messages or warnings from this screenshot."
        elif analysis_type == "layout_analysis":
            return "Analyze the layout structure and alignment in this UI screenshot."
        elif analysis_type == "verification":
            if expected_elements:
                descriptions = [e.get("description", "") for e in expected_elements]
                return f"Verify these elements are present:\n{'\n'.join(descriptions)}"
            return "Verify standard UI elements are present."
        elif analysis_type == "regression":
            return "Compare this screenshot with the baseline and identify differences."
        else:
            return "Analyze this UI screenshot."

    def _generate_structured_report(self, analysis_id: str, session_id: str, screenshot_id: str,
                                    url: str, raw_result: Dict[str, Any], processing_time_ms: float) -> VisionAnalysisReport:
        """Generate structured Vision Analysis Report from raw response (Phase 3)."""
        choices = raw_result.get("choices", [])
        
        if not choices:
            return VisionAnalysisReport.empty(analysis_id, session_id, screenshot_id, url)
        
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            return VisionAnalysisReport.empty(analysis_id, session_id, screenshot_id, url)
        
        # Extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = content
        
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            parsed = {"summary": json_str[:4000], "detected_components": [], "missing_components": [],
                     "ocr_text": "", "visual_issues": [], "warnings": [], "suggested_improvements": []}
        
        summary = parsed.get("summary", "")
        return VisionAnalysisReport(
            analysis_id=analysis_id, session_id=session_id, screenshot_id=screenshot_id, url=url,
            page_title=parsed.get("page_title"), summary=summary if summary else None,
            detected_components=parsed.get("detected_components", []),
            missing_components=parsed.get("missing_components", []), ocr_text=parsed.get("ocr_text", ""),
            visual_issues=parsed.get("visual_issues", []), warnings=parsed.get("warnings", []),
            suggested_improvements=parsed.get("suggested_improvements", []),
            confidence_score=parsed.get("confidence_score"), processing_time_ms=processing_time_ms,
        )


# =============================================================================
# FACTORY FUNCTIONS (for Communication Bus integration)
# =============================================================================

async def create_vision_pipeline(config: Optional[Dict[str, Any]] = None) -> VisionPipeline:
    """Factory function to create a configured Vision Pipeline."""
    if config is None:
        return VisionPipeline()
    
    return VisionPipeline(
        base_url=config.get("base_url", DEFAULT_BASE_URL),
        timeout=config.get("timeout", DEFAULT_TIMEOUT),
        max_retries=config.get("max_retries", DEFAULT_MAX_RETRIES),
        backoff_factor=config.get("backoff_factor", DEFAULT_BACKOFF_FACTOR),
        vision_model=config.get("vision_model", DEFAULT_VISION_MODEL),
    )


async def close_vision_pipeline(pipeline: VisionPipeline) -> None:
    """Close the vision pipeline (cleanup if needed)."""
    pass


async def run_vision_analysis(
    page_url: str, session_id: str, milestone_id: str, task_id: str,
    analysis_type: str = "general_inspection", base_url: Optional[str] = None,
    vision_model: Optional[str] = None,
) -> Tuple[Dict[str, Any], VisionAnalysisReport]:
    """Standalone function to run a vision analysis without creating pipeline instance."""
    config = {"base_url": base_url or DEFAULT_BASE_URL, "vision_model": vision_model or DEFAULT_VISION_MODEL}
    
    pipeline = await create_vision_pipeline(config)
    
    try:
        return await pipeline.run_analysis(
            page_url=page_url, session_id=session_id, milestone_id=milestone_id, task_id=task_id,
            analysis_type=analysis_type,
        )
    finally:
        await close_vision_pipeline(pipeline)


__all__ = [
    "VisionPipeline", "create_vision_pipeline", "close_vision_pipeline", "run_vision_analysis",
    "EVENT_ANALYSIS_STARTED", "EVENT_SCREENSHOT_CAPTURED", "EVENT_VISION_REQUEST_SENT",
    "EVENT_VISION_RESPONSE_RECEIVED", "EVENT_ANALYSIS_COMPLETED", "EVENT_ANALYSIS_FAILED",
    "PipelineError", "ScreenshotMissingError", "VisionTimeoutError",
    "LmStudioUnavailableError", "InvalidResponseError",
]
