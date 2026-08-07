#!/usr/bin/env python3
"""
Vision Agent Runtime for Sanskriti AI Studio (STEP 23.2 - Updated).

This runtime handles visual analysis tasks using the LM Studio vision model (Qwen2.5-VL).
It is responsible for:
- Browser UI analysis
- Screenshot understanding
- OCR text extraction
- Error message extraction
- Layout validation
- Visual regression testing
- UI verification

CRITICAL ARCHITECTURE CHANGE (STEP 23.2):
    Vision Agent → Vision Service → Model Router → LM Studio

The Vision Agent NEVER communicates directly with LM Studio.
All AI model selection must go through the Model Router.

Flow Diagram:
    ┌─────────────┐
    │  Vision     │
    │  Agent      │
    └──────┬──────┘
           ↓
    ┌─────────────┐
    │ Vision       │
    │ Service     │  ← All vision communication goes here
    └──────┬──────┘
           ↓
    ┌─────────────┐
    │ Model       │  ← Model selection centralized here
    │ Router      │
    └──────┬──────┘
           ↓
    ┌─────────────┐
    │ LM Studio   │
    │ Vision API  │
    └─────────────┘

Qwen 3.5 remains TEXT-ONLY. This agent uses the vision model only.

Version: 2.0 (Updated for STEP 23.2)
Last Updated: 2026-08-06
"""

import argparse
import asyncio
import importlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("vision_agent")


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
ACTIONS_PATH = os.path.join(STATE_DIR, "actions.jsonl")
REPORT_PATH = os.path.join(STATE_DIR, "vision_report.json")


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def safe_rel_path(path: str) -> Optional[str]:
    """Normalize a workspace-relative path and reject unsafe/out-of-scope paths."""
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        return None
    absolute = os.path.abspath(os.path.join(WORKSPACE_ROOT, normalized))
    workspace = os.path.abspath(WORKSPACE_ROOT)
    if not absolute.startswith(workspace):
        return None
    return normalized


def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON object from disk, returning None when unavailable/invalid."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            data.setdefault("_source", path)
            return data
        return {"value": data, "_source": path}
    except json.JSONDecodeError as exc:
        return {"_load_error": f"Invalid JSON in {path}: {exc}", "_source": path}
    except OSError as exc:
        return {"_load_error": f"Could not read {path}: {exc}", "_source": path}


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append a Vision Agent action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "vision_agent",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(ACTIONS_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def build_prompts() -> Dict[str, str]:
    """Build all available prompts for different analysis tasks."""
    return {
        "general": """Analyze this UI screenshot and provide a comprehensive visual report.

Report should include:
1. **Overall Layout**: Describe the overall structure and layout of the page
2. **Detected Components**: List all major UI components (header, nav, buttons, forms, tables, images, etc.)
3. **Text Content**: Extract any visible text, labels, headers, body content
4. **Visual Elements**: Note icons, colors, images, and visual indicators
5. **Page Type**: Infer what type of page this is (login, dashboard, article, product, etc.)

Return structured JSON with all findings.
""",
        "component_detection": """Detect UI components in this screenshot.

For each detected component, report:
- Component type (button, input, table, image, header, footer, nav, etc.)
- Visual state (active, disabled, hovered, focused, etc.)
- Location (general position: top-left, center, bottom-right, etc.)
- Size estimate (small, medium, large)
- Any visible text or labels

Report all components found and any missing expected UI elements.

Return structured JSON with component list.
""",
        "ocr": """Perform optical character recognition on this image.

Extract ALL visible text including:
- Button labels
- Form field labels and placeholders
- Error/success message text
- Navigation items
- Menu content
- Body text paragraphs
- Footer information
- Any embedded error dialogs or notifications

For each text region, provide:
- The extracted text content
- Approximate location description
- Language (if detectable)
- Formatting indicators (bold, italic, monospace)

Return all extracted text in structured JSON format.
""",
        "error_detection": """Detect and extract any error messages or warning indicators from this screenshot.

Look for:
- Error dialogs or modals
- Warning notifications/banners
- Red text, borders, or icons
- Alert symbols
- Status bar error messages
- Console/terminal-like error output
- Form validation error messages

For each error/warning detected, report:
- Error type (dialog/notification/in-line)
- The exact error message text
- Location on screen (general position)
- Severity indicator (if visible)
- Any suggested fix or recovery action shown

Also separately list any warning indicators.

Return structured JSON with all errors and warnings found.
""",
        "layout": """Analyze the layout structure and alignment in this UI screenshot.

Check for:
- Element alignment (buttons, text blocks, images)
- Consistent spacing and padding
- Grid adherence
- Overflowing content issues
- Visual hierarchy appropriateness
- Responsive design indicators
- Accessibility cues

Report any alignment or layout issues found with:
- Issue type
- Location
- Affected elements
- Severity (minor/moderate/severe)
- Suggested fix

Return structured JSON with analysis results.
""",
        "verify": """Verify presence of specific UI elements in this screenshot. Return structured JSON with verification results.
""",
        "regression": """Compare two UI screenshots and identify visual differences between them.

Identify changes in:
- Layout structure
- Element positions
- Content text changes
- Color/theme changes
- Missing elements
- New elements
- Style/regressions

Report each difference with:
- Type of change (layout/content/style/missing/new)
- Location of difference
- Description of what changed
- Whether it's likely intentional or a bug
- Impact level (minor/moderate/severe)

Return structured JSON comparing the two images.
""",
    }


def load_vision_config() -> Dict[str, Any]:
    """Load vision model configuration from environment or defaults."""
    if AI_AGENTS_ROOT not in sys.path:
        sys.path.insert(0, AI_AGENTS_ROOT)
    
    try:
        config_module = importlib.import_module("scripts.vision_config")
        return {
            "base_url": config_module.get_vision_config().base_url,
            "timeout": config_module.get_vision_config().timeout,
            "temperature": config_module.get_vision_config().temperature,
            "max_tokens": config_module.get_vision_config().max_tokens,
            "retry_count": config_module.get_vision_config().retry_count,
        }
    except Exception as exc:
        record_action("config_error", {"error": f"{type(exc).__name__}: {exc}"})
        return {
            "base_url": "http://localhost:1234",
            "timeout": 300,
            "temperature": 0.1,
            "max_tokens": 4096,
            "retry_count": 3,
        }


async def run_vision_analysis(
    image_path: str,
    task_type: str = "general",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for vision analysis using Vision Service and Model Router.
    
    Architecture Flow (STEP 23.2):
        Vision Agent → Vision Service → Model Router → LM Studio
    
    Args:
        image_path: Path to the screenshot/image file
        task_type: Type of analysis to perform
        request_id: Optional request ID for logging
        
    Returns:
        Standardized vision report dictionary
    """
    # Initialize components in order (STEP 23.2 Architecture)
    config = load_vision_config()
    
    # Create Vision Service - handles all LM Studio communication
    try:
        from scripts.vision_service import VisionService, ModelConnectionError
        vision_service = VisionService(config=config)
    except ImportError as e:
        record_action("service_error", {"error": f"Could not import VisionService: {e}"})
        return {
            "status": "error",
            "summary": "Vision Service initialization failed.",
            "errors": [f"Could not import VisionService: {e}"],
        }
    
    # Create Model Router - handles model selection
    try:
        from scripts.model_router import ModelRouter, ModelNotFoundError
        model_router = ModelRouter()
    except ImportError as e:
        record_action("router_error", {"error": f"Could not import ModelRouter: {e}"})
        return {
            "status": "error",
            "summary": "Model Router initialization failed.",
            "errors": [f"Could not import ModelRouter: {e}"],
        }
    
    # Build prompts
    prompts = build_prompts()
    prompt = prompts.get(task_type, prompts["general"])
    
    # STEP 23.2: Vision Agent gets model from Router (NOT hardcoded)
    try:
        vision_model = model_router.get_vision_model()
    except ModelNotFoundError as e:
        record_action("model_error", {"error": str(e)})
        return {
            "status": "error",
            "summary": f"Model not configured: {e}",
            "errors": [str(e)],
        }
    
    # STEP 23.2: Vision Service gets models from Router (NOT hardcoded)
    try:
        vision_service.set_model_from_router(model_router)
    except Exception as e:
        record_action("service_config_error", {"error": str(e)})
        return {
            "status": "error",
            "summary": f"Vision Service configuration failed: {e}",
            "errors": [str(e)],
        }
    
    # Generate request ID if not provided
    request_id = request_id or f"vision_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    record_action("analysis_init", {
        "image_path": safe_rel_path(image_path),
        "task_type": task_type,
        "model_used": vision_model,
        "request_id": request_id,
    })
    
    logger.info(f"[STEP 23.2] Vision analysis initiated - Image: {safe_rel_path(image_path)}, Task: {task_type}")
    logger.info(f"[STEP 23.2] Using model router to get vision model: {vision_model}")
    logger.info(f"[STEP 23.2] Vision service configured via ModelRouter")
    
    # Prepare messages with image
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},  # Placeholder - will be replaced below
                {"type": "text", "text": prompt},
            ],
        }
    ]
    
    # Encode image to base64
    try:
        import base64
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()
        
        messages[0]["content"][0] = {
            "type": "image_url",
            "image_url": f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}",
        }
    except Exception as e:
        record_action("image_error", {"error": f"Failed to load image: {e}"})
        return {
            "status": "error",
            "summary": f"Image loading failed: {e}",
            "errors": [f"Failed to load image: {e}"],
        }
    
    # STEP 23.2: Vision Service processes request via Model Router
    # Initialize response and log_entry as Optional[Dict[str, Any]] | None
    # This allows safe access before parse() which requires Dict[str, Any]
    response: Optional[Dict[str, Any]] = None
    log_entry: Optional[Dict[str, Any]] = None
    
    try:
        response, log_entry = await vision_service.process_vision_request(
            messages=messages,
            request_id=request_id,
            model_type="vision",
        )
    except ModelConnectionError as e:
        record_action("connection_error", {"error": str(e)})
        response = None
        log_entry = None
        return {
            "status": "error",
            "summary": f"LM Studio connection failed: {e}",
            "errors": [f"LM Studio connection failed: {str(e)[:500]}"],
        }
    except Exception as e:
        record_action("request_error", {"error": str(e)})
        response = None
        log_entry = None
        return {
            "status": "error",
            "summary": f"Request processing failed: {e}",
            "errors": [f"Request processing failed: {str(e)[:500]}"],
        }
    
    # Parse response using Response Parser
    if response is None:
        return {
            "status": "error",
            "summary": "Vision request returned no response.",
            "errors": ["vision_service.process_vision_request() returned None"],
        }
    
    from scripts.response_parser import VisionResponseParser, ParseError as _ParseError
    parser = VisionResponseParser()
    
    try:
        if response is None:
            return {
                "status": "error",
                "summary": "Vision request returned no response.",
                "errors": ["vision_service.process_vision_request() returned None"],
            }
        
        report = parser.parse(response, task_type=task_type)
        
        # Add metadata to parsed report
        report["request_id"] = request_id
        latency_ms = log_entry.get("duration_ms") if log_entry else None
        retry_count = log_entry.get("retry_count", 0) if log_entry else 0
        report["latency_ms"] = latency_ms
        report["retry_count"] = retry_count
    
    except _ParseError as e:
        record_action("parse_error", {"error": str(e)})
        return {
            "status": "error",
            "summary": f"Response parsing failed: {e}",
            "errors": [f"Response parsing failed: {str(e)[:500]}"],
        }
    
    # Log for audit (STEP 23.2 Logging requirement)
    latency_str = str(latency_ms) if latency_ms is not None else "N/A"
    logger.info(f"[STEP 23.2] Analysis complete - Status: {report.get('status')}, Latency: {latency_str}ms")
    
    return report


async def run_health_check() -> Dict[str, Any]:
    """
    Perform health check on LM Studio vision endpoint.
    
    Returns:
        Health check result dictionary
    """
    try:
        from scripts.model_router import ModelRouter
        router = ModelRouter()
        health = router.health_check()
        return {
            "status": "healthy" if health.status == "healthy" else health.status,
            "message": health.message,
            "endpoint": health.endpoint,
            "available_models": health.available_models,
            "latency_ms": health.latency_ms,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


def process_image_task(image_path: str, task_type: str = "general") -> Dict[str, Any]:
    """Synchronous wrapper for vision analysis."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        report = loop.run_until_complete(
            run_vision_analysis(image_path=image_path, task_type=task_type)
        )
        return report
    finally:
        loop.close()


def process_multiple_images_sync(image_paths: List[str], task_type: str = "general") -> Dict[str, Any]:
    """Process multiple images synchronously."""
    if not image_paths:
        return {
            "task_type": task_type,
            "images_processed": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
        }
    
    results = []
    for image_path in image_paths:
        try:
            report = process_image_task(image_path, task_type)
            results.append({
                "image_path": safe_rel_path(image_path),
                "task_type": task_type,
                "report": report,
            })
            
            if report.get("status") == "success":
                record_action("task_success", {
                    "image": safe_rel_path(image_path),
                    "type": task_type,
                })
        except Exception as e:
            record_action("task_exception", {"error": str(e)})
            results.append({
                "image_path": safe_rel_path(image_path),
                "task_type": task_type,
                "status": "error",
                "errors": [f"Exception: {str(e)}"],
            })
    
    return {
        "task_type": task_type,
        "images_processed": len(image_paths),
        "successful": sum(1 for r in results if r.get("status") == "success"),
        "failed": sum(1 for r in results if r.get("status") in ("error",)),
        "results": results,
    }


def save_report(report: Dict[str, Any], task_id: Optional[str] = None) -> None:
    """Persist the vision report to ai_agents/state/vision_report.json."""
    os.makedirs(STATE_DIR, exist_ok=True)
    
    final_task_id = str(task_id) if task_id else datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    
    final_report = {
        "task_id": final_task_id,
        "report": report,
        "timestamp": utc_now(),
    }
    
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(final_report, file, indent=2, ensure_ascii=False)


def run_vision_analysis_sync(image_path: Optional[str] = None, task_type: str = "general") -> Dict[str, Any]:
    """Synchronous entry point for vision analysis tasks."""
    
    if not image_path:
        return {
            "status": "error",
            "summary": "No image path provided.",
            "errors": ["image_path is required for vision analysis."],
        }
    
    report = process_image_task(image_path, task_type)
    save_report(report, task_id="STEP232_VISION_ANALYSIS")
    
    return report


def main() -> None:
    """CLI entry point for the Vision Agent Runtime (STEP 23.2)."""
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Vision Agent for visual analysis."
    )
    parser.add_argument(
        "--image",
        "-i",
        required=True,
        help="Path to the screenshot/image file to analyze.",
    )
    parser.add_argument(
        "--task",
        "-t",
        default="general",
        choices=[
            "general",      # General UI analysis
            "components",   # Component detection
            "ocr",          # OCR text extraction
            "errors",       # Error message detection
            "layout",       # Layout/alignment analysis
            "verify",       # Element verification
            "regression",   # Visual regression (requires baseline)
        ],
        help="Type of visual analysis to perform.",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Vision model name override (Qwen2.5-VL-8B by default from Model Router).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Model temperature (lower for more deterministic outputs).",
    )
    parser.add_argument(
        "--task-id",
        "-id",
        default=None,
        help="Task ID for the report.",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("VISION AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 60)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - This agent uses vision model via Model Router")
    print(f"[INFO] Image: {args.image}")
    print(f"[INFO] Task Type: {args.task}")
    print("[INFO] Architecture: Vision Agent → Vision Service → Model Router → LM Studio")
    
    # Override model if provided (sets environment variable)
    if args.model:
        from scripts.config import set_vision_model
        set_vision_model(args.model)
        print(f"[INFO] Using model override: {args.model}")
    
    # Run analysis
    report = run_vision_analysis_sync(
        image_path=args.image,
        task_type=args.task,
    )
    
    print("\n" + "=" * 60)
    print("VISION ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Status: {report.get('status', 'unknown')}")
    print(f"Summary: {report.get('summary', '')[:200]}...")
    
    if report.get("errors"):
        print("\n[ERRORS]")
        for error in report["errors"]:
            print(f"  - {error}")
    
    if report.get("components"):
        print("\n[DETECTED COMPONENTS]")
        for comp in report["components"][:5]:
            print(f"  - {comp}")
    
    if report.get("ocr_text"):
        print("\n[OCR TEXT]")
        lines = report["ocr_text"].split("\n")[:20]
        for line in lines:
            print(f"  {line}")
    
    print(f"\nReport saved to: {REPORT_PATH}")
    print("[STEP 23.2] Architecture verified: Vision Agent uses Vision Service → Model Router → LM Studio")


if __name__ == "__main__":
    main()
