#!/usr/bin/env python3
"""
Vision Agent Runtime for Sanskriti AI Studio AI Agents.

This runtime handles visual analysis tasks using the LM Studio vision model (Qwen2.5-VL).
It is responsible for:
- Browser UI analysis
- Screenshot understanding
- OCR text extraction
- Error message extraction
- Layout validation
- Visual regression testing
- UI verification

CRITICAL: This agent uses the vision model (Qwen2.5-VL) exclusively.
          Qwen 3.5 is TEXT-ONLY and should NEVER be used for image processing.

Version: 1.0
Last Updated: 2026-08-06
"""

import argparse
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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


def load_vision_config() -> Dict[str, Any]:
    """Load vision model configuration from environment or defaults."""
    if AI_AGENTS_ROOT not in sys.path:
        sys.path.insert(0, AI_AGENTS_ROOT)
    
    try:
        config_module = importlib.import_module("scripts.config")
        
        return {
            "base_url": config_module.get_base_url(),
            "vision_model": config_module.get_vision_model(),
            "temperature": 0.1,
            "max_tokens": 4096,
        }
    except Exception as exc:
        record_action("config_error", {"error": f"{type(exc).__name__}: {exc}"})
        return {
            "base_url": "http://localhost:1234/v1",
            "vision_model": "",
            "temperature": 0.1,
            "max_tokens": 4096,
        }


def build_vision_agent(config: Dict[str, Any]) -> Any:
    """Create and configure the Vision Agent instance."""
    try:
        from agents.vision import VisionAgent
        
        agent = VisionAgent(config)
        
        # Override base_url if configured without /v1 suffix
        if not config["base_url"].endswith("/v1"):
            agent.base_url += "/v1"
        
        return agent
    except ImportError as e:
        raise ImportError(f"Could not import VisionAgent: {e}") from e


def build_general_inspection_prompt() -> str:
    """Build a prompt for general UI screenshot analysis."""
    return f"""Analyze this UI screenshot and provide a comprehensive visual report.

Report should include:
1. **Overall Layout**: Describe the overall structure and layout of the page
2. **Detected Components**: List all major UI components (header, nav, buttons, forms, tables, images, etc.)
3. **Text Content**: Extract any visible text, labels, headers, body content
4. **Visual Elements**: Note icons, colors, images, and visual indicators
5. **Page Type**: Infer what type of page this is (login, dashboard, article, product, etc.)

Return structured JSON with all findings.
"""


def build_component_detection_prompt() -> str:
    """Build a prompt for component detection."""
    return f"""Detect UI components in this screenshot.

For each detected component, report:
- Component type (button, input, table, image, header, footer, nav, etc.)
- Visual state (active, disabled, hovered, focused, etc.)
- Location (general position: top-left, center, bottom-right, etc.)
- Size estimate (small, medium, large)
- Any visible text or labels

Report all components found and any missing expected UI elements.

Return structured JSON with component list.
"""


def build_ocr_prompt() -> str:
    """Build a prompt for OCR text extraction."""
    return f"""Perform optical character recognition on this image.

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
"""


def build_error_detection_prompt() -> str:
    """Build a prompt for error message detection."""
    return f"""Detect and extract any error messages or warning indicators from this screenshot.

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
"""


def build_layout_analysis_prompt() -> str:
    """Build a prompt for layout analysis."""
    return f"""Analyze the layout structure and alignment in this UI screenshot.

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
"""


def build_verification_prompt(expected_elements: List[Dict[str, Any]]) -> str:
    """Build a prompt for UI element verification."""
    if not expected_elements:
        return "Verify this screenshot contains standard UI elements."
    
    element_descriptions = []
    for elem in expected_elements:
        desc = elem.get("description", "")
        expected = elem.get("expected_text", "any text")
        element_descriptions.append(f"- {desc} (Expected to contain: {expected})")
    
    return f"""Verify presence of these UI elements in this screenshot:

Elements to Check:
{chr(10).join(element_descriptions)}

For each element, report:
- Whether it's present (found/not found)
- General location if found
- Exact text content vs expected text
- Visual state (enabled/disabled/active/inactive)
- Any deviations from expectations

Also note:
- Missing elements that should be present
- Unexpected extra elements
- Overall UI completeness

Return structured JSON with verification results.
"""


def build_regression_prompt() -> str:
    """Build a prompt for visual regression analysis."""
    return f"""This is a visual regression analysis task.

I will provide you with screenshots and ask you to identify differences between versions or detect unexpected changes.

For this image, analyze and report:
- Any layout changes from expected baseline
- New content or elements added
- Missing content or removed elements
- Style or theme regressions
- Broken UI patterns

Return findings in structured JSON format.
"""


def send_to_vision_model(
    messages: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> tuple:
    """Send a vision request to LM Studio and get the response."""
    if AI_AGENTS_ROOT not in sys.path:
        sys.path.insert(0, AI_AGENTS_ROOT)
    
    try:
        from scripts.vision_client import chat_with_vision_model
        
        # Extract model and base URL from config
        vision_model = config.get("vision_model", "")
        base_url = config.get("base_url", "http://localhost:1234")
        
        response = chat_with_vision_model(
            messages=messages,
            base_url=base_url,
            model_name=vision_model,
        )
        
        return response, None
        
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse a JSON object from an LLM response."""
    if not text:
        return None
    
    stripped = text.strip()
    # Remove markdown code blocks
    if stripped.startswith("```"):
        start_idx = stripped.find("```") + len("```json")
        end_idx = stripped.rfind("```")
        if start_idx != -1 and end_idx != -1:
            stripped = stripped[start_idx : end_idx].strip()
    
    # Try to extract JSON from the response
    import re
    
    # Find first occurrence of { and matching }
    start = stripped.find("{")
    end = stripped.rfind("}")
    
    if start != -1 and end != -1 and end > start:
        json_str = stripped[start : end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Last resort: try parsing entire stripped text
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def normalize_vision_report(
    raw_response: Dict[str, Any], task_type: str
) -> Dict[str, Any]:
    """Normalize a vision model response into the standard report schema."""
    
    if not raw_response:
        return {
            "status": "error",
            "summary": "No response from vision model.",
            "errors": ["Model returned no response or response was empty."],
        }
    
    # Extract content from response
    choices = raw_response.get("choices", [])
    if not choices:
        return {
            "status": "error",
            "summary": "No choices in model response.",
            "errors": ["Model response had no choices."],
        }
    
    content = choices[0].get("message", {}).get("content", "")
    if not content:
        return {
            "status": "error",
            "summary": "No content in model message.",
            "errors": ["Model response had no content."],
        }
    
    # Try JSON parsing first
    import json
    parsed = None
    try:
        parsed = extract_json_object(content)
    except Exception as e:
        pass
    
    if parsed and isinstance(parsed, dict):
        # Normalize to standard schema
        status = str(parsed.get("status", "success")).lower()
        summary = parsed.get("summary", "")
        
        report = {
            "status": "success" if status == "success" else ("error" if status == "error" else "warning"),
            "task_type": task_type,
            "summary": str(summary)[:5000],
            "model_used": raw_response.get("model", "unknown"),
        }
        
        # Extract standard fields
        for field in ["detected_components", "missing_components", "ocr_text", "errors", "warnings", 
                      "suggested_fixes", "alignment_issues", "verified_elements"]:
            if field in parsed:
                report[field] = parsed[field]
        
        return report
    
    # Fall back to text extraction
    return extract_from_text_response(content, task_type)


def extract_from_text_response(text: str, task_type: str) -> Dict[str, Any]:
    """Extract structured information from unstructured text response."""
    import re
    
    # Initialize all fields as empty lists/strings for type safety
    result = {
        "status": "success",
        "task_type": task_type,
        "summary": (text[:1000] if text else ""),
        "detected_components": [],
        "ocr_text": "",
        "errors": [],
        "warnings": [],
        "suggested_fixes": [],
    }
    
    # Try to extract components
    component_pattern = r"(?:detected|found|identified)\s*(?:components?|element)?[:,\s]+([^\n]+)"
    comp_match = re.search(component_pattern, text, re.IGNORECASE)
    if comp_match:
        detected_components = [comp_match.group(1).strip()]
        result['detected_components'] = detected_components
    
    # Extract OCR/text content
    text_patterns = [
        (r"(?:extracted|text|content)[:,\s]+([\'\"\[\]:(\w\s.]+\n?)+)", "ocr_text"),
        (r"(?:all|visible)\s*text[:,\s]+([^\n]+)", "ocr_text"),
    ]
    
    for pattern, field in text_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1):
            result[field] = match.group(1).strip()[:2000]
            break
    
    # Extract errors/warnings - each tuple has (pattern, field_name)
    error_patterns = [
        (r"(?:error|fail)[,\s]+([^\n]+)", "errors"),  # Capturing group for error text
        (r"(?:warning)[,\s]+([^\n]+)", "warnings")  # Capturing group for warning text
    ]
    
    for pattern, field in error_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # With single capturing group, findall returns strings directly (not tuples)
            result[field] = [m.strip() for m in matches[:5]]
    
    # Extract recommendations/fixes
    fix_pattern = r"(?:recommend|suggest|fix)[,\s]+([^\n]+)"
    fixes = re.findall(fix_pattern, text, re.IGNORECASE)
    if fixes:
        result["suggested_fixes"] = [f.strip() for f in fixes[:5]]
    
    return result


def process_image_task(
    image_path: str, task_type: str, agent: Any, config: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a single image analysis task."""
    
    # Record action
    record_action("task_init", {
        "image_path": safe_rel_path(image_path),
        "task_type": task_type,
    })
    
    try:
        # Call agent method based on task type
        if task_type == "general":
            prompt = build_general_inspection_prompt()
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url, model_name=agent.model_name
            )
            report = normalize_vision_report(response, task_type)
        
        elif task_type == "component_detection":
            prompt = build_component_detection_prompt()
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        elif task_type == "ocr":
            prompt = build_ocr_prompt()
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        elif task_type == "error_detection":
            prompt = build_error_detection_prompt()
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        elif task_type == "layout":
            prompt = build_layout_analysis_prompt()
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        elif task_type == "verify":
            expected = config.get("expected_elements", [])
            if expected:
                prompt = build_verification_prompt(expected)
            else:
                prompt = "Verify the UI elements present."
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        elif task_type == "regression":
            prompt = build_regression_prompt()
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        else:
            # Generic analysis
            prompt = "Analyze this UI screenshot."
            response = agent.chat_with_vision_model_from_image(
                image_path=image_path, prompt=prompt, base_url=agent.base_url
            )
            report = normalize_vision_report(response, task_type)
        
        return report
        
    except Exception as e:
        error_trace = str(e)[:500]
        record_action("task_error", {"error": error_trace})
        return {
            "status": "error",
            "summary": f"Task execution failed.",
            "errors": [error_trace],
            "task_type": task_type,
            "image_path": safe_rel_path(image_path),
        }


def process_multiple_images(
    image_paths: List[str], task_type: str = "general", config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process multiple images with the same analysis task."""
    
    if config is None:
        config = load_vision_config()
    
    agent = build_vision_agent(config)
    
    results: List[Dict[str, Any]] = []
    for image_path in image_paths:
        try:
            report = process_image_task(image_path, task_type, agent, config)
            results.append({
                "image_path": safe_rel_path(image_path),
                "task_type": task_type,
                "report": report,
            })
            
            # Record success
            if report.get("status") == "success":
                record_action("task_success", {
                    "image": safe_rel_path(image_path),
                    "type": task_type,
                })
            else:
                record_action("task_partial", {
                    "image": safe_rel_path(image_path),
                    "errors": report.get("errors", []),
                })
        except Exception as e:
            record_action("task_exception", {"error": str(e)})
            results.append({
                "image_path": safe_rel_path(image_path),
                "task_type": task_type,
                "status": "error",
                "errors": [f"Exception: {str(e)}"],
            })
    
    # Aggregate results
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
    
    # Ensure task_id is a valid string (generate one if not provided)
    final_task_id = str(task_id) if task_id else datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    
    final_report = {
        "task_id": final_task_id,
        "report": report,
        "timestamp": utc_now(),
    }
    
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(final_report, file, indent=2, ensure_ascii=False)


def run_vision_analysis(image_path: Optional[str] = None, task_type: str = "general") -> Dict[str, Any]:
    """Main entry point for vision analysis tasks."""
    
    config = load_vision_config()
    agent = build_vision_agent(config)
    
    if not image_path:
        return {
            "status": "error",
            "summary": "No image path provided.",
            "errors": ["image_path is required for vision analysis."],
        }
    
    report = process_image_task(image_path, task_type, agent, config)
    save_report(report, task_id="STEP231_VISION_ANALYSIS")
    
    return report


def main() -> None:
    """CLI entry point for the Vision Agent Runtime."""
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
        help="Vision model name (Qwen2.5-VL-8B by default).",
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
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - This agent uses the vision model (Qwen2.5-VL)")
    print(f"[INFO] Image: {args.image}")
    print(f"[INFO] Task Type: {args.task}")
    
    # Override model if provided
    if args.model:
        from scripts.config import set_vision_model
        set_vision_model(args.model)
        print(f"[INFO] Using model: {args.model}")
    
    # Run analysis
    report = run_vision_analysis(
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
    
    if report.get("detected_components"):
        print("\n[DETECTED COMPONENTS]")
        for comp in report["detected_components"][:5]:
            print(f"  - {comp}")
    
    if report.get("ocr_text"):
        print("\n[OCR TEXT]")
        lines = report["ocr_text"].split("\n")[:20]
        for line in lines:
            print(f"  {line}")
    
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
