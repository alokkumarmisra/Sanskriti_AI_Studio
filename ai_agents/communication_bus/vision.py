"""
Vision Agent Registration for Communication Bus.

This module registers the Vision Agent with the communication bus system,
enabling message routing between agents and the vision analysis capabilities.
"""

from typing import Any, Dict, List, Optional


# Vision Agent registration in communication bus
VISION_AGENT_ID = "vision_agent"
VISION_AGENT_TYPE = "visual_analysis"


def register_vision_agent(agent: Any) -> Dict[str, Any]:
    """
    Register the Vision Agent with the communication bus.

    Args:
        agent: The VisionAgent instance to register

    Returns:
        Registration confirmation dictionary
    """
    registration = {
        "agent_id": VISION_AGENT_ID,
        "agent_type": VISION_AGENT_TYPE,
        "capabilities": [
            "ui_analysis",
            "screenshot_understanding",
            "ocr_extraction",
            "error_detection",
            "layout_validation",
            "visual_regression",
            "ui_verification",
        ],
        "model": "Qwen2.5-VL",
        "text_only": False,  # Vision agent processes images
        "registered": True,
    }
    
    return registration


def build_vision_message(
    task_type: str,
    image_path: Optional[str] = None,
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a message for the Vision Agent.

    Args:
        task_type: Type of visual analysis task
        image_path: Path to image file (required for vision tasks)
        prompt: Custom prompt override

    Returns:
        Message dictionary ready for routing
    """
    if not image_path:
        raise ValueError("Vision Agent requires an image_path parameter.")
    
    # Load default prompts based on task type
    default_prompts = {
        "general": """Analyze this UI screenshot and provide a comprehensive visual report.

Report should include:
1. **Overall Layout**: Describe the overall structure and layout of the page
2. **Detected Components**: List all major UI components (header, nav, buttons, forms, tables, images, etc.)
3. **Text Content**: Extract any visible text, labels, headers, body content
4. **Visual Elements**: Note icons, colors, images, and visual indicators
5. **Page Type**: Infer what type of page this is (login, dashboard, article, product, etc.)

Return structured JSON with all findings.""",
        
        "component_detection": """Detect UI components in this screenshot.

For each detected component, report:
- Component type (button, input, table, image, header, footer, nav, etc.)
- Visual state (active, disabled, hovered, focused, etc.)
- Location (general position: top-left, center, bottom-right, etc.)
- Size estimate (small, medium, large)
- Any visible text or labels

Report all components found and any missing expected UI elements.

Return structured JSON with component list.""",
        
        "ocr": """Perform optical character recognition on this image.

Extract ALL visible text including:
- Button labels
- Form field labels and placeholders
- Error/success message text
- Navigation items
- Menu content
- Body text paragraphs
- Footer information

Return all extracted text in structured JSON format.""",
        
        "error_detection": """Detect and extract any error messages or warning indicators from this screenshot.

Look for:
- Error dialogs or modals
- Warning notifications/banners
- Red text, borders, or icons
- Alert symbols

For each error detected, report:
- Error type
- The exact error message text
- Location on screen
- Severity indicator

Return structured JSON with all errors found.""",
        
        "layout_analysis": """Analyze the layout structure and alignment in this UI screenshot.

Check for:
- Element alignment issues
- Inconsistent spacing/padding
- Grid adherence
- Overflowing content
- Visual hierarchy issues

Report any alignment or layout issues found with severity and suggested fixes.

Return structured JSON with analysis results.""",
        
        "verification": """Verify the presence of UI elements in this screenshot.

For each specified element, report:
- Whether it's present
- Location if found
- Exact text vs expected
- Visual state (enabled/disabled)

Also note missing or unexpected elements.

Return structured JSON with verification results.""",
    }
    
    prompt_to_use = prompt or default_prompts.get(task_type, "")
    
    return {
        "agent_id": VISION_AGENT_ID,
        "task_type": task_type,
        "image_path": image_path,
        "prompt": prompt_to_use,
        "priority": "normal",
        "route": "vision_analysis",
    }


def route_vision_request(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Route a vision request to the Vision Agent.

    Args:
        message: Message dictionary with task details

    Returns:
        Processed response or None if routing failed
    """
    agent_id = message.get("agent_id")
    task_type = message.get("task_type", "general")
    image_path = message.get("image_path")
    
    if agent_id != VISION_AGENT_ID or not image_path:
        return None
    
    # Process the vision request
    try:
        from scripts.vision_agent import run_vision_analysis
        
        task_id = f"vision_{task_type}_{hash(image_path) % 10000}"
        report = run_vision_analysis(
            image_path=image_path,
            task_type=task_type,
        )
        
        return {
            "success": report.get("status") == "success",
            "report": report,
            "task_id": task_id,
            "agent_id": agent_id,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_id": agent_id,
        }


def get_vision_agent_info() -> Dict[str, Any]:
    """
    Get information about the registered Vision Agent.

    Returns:
        Agent information dictionary
    """
    return {
        "agent_id": VISION_AGENT_ID,
        "agent_type": VISION_AGENT_TYPE,
        "description": "Vision Agent for visual analysis tasks using Qwen2.5-VL",
        "capabilities": [
            "ui_analysis",
            "screenshot_understanding", 
            "ocr_extraction",
            "error_detection",
            "layout_validation",
            "visual_regression",
            "ui_verification",
        ],
        "model_name": "Qwen2.5-VL (via LM Studio)",
        "text_only_compatible": False,
        "status": "registered",
    }


# Register agent at module level for bootstrap integration
__all__ = [
    "VISION_AGENT_ID",
    "VISION_AGENT_TYPE", 
    "register_vision_agent",
    "build_vision_message",
    "route_vision_request",
    "get_vision_agent_info",
]
