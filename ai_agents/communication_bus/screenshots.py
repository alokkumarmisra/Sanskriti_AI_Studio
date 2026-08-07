"""
Screenshot Service Registration for Communication Bus.

This module registers the Screenshot Capture Service with the communication bus system,
enabling message routing between agents and the screenshot management capabilities.

CRITICAL: Qwen 3.5 is TEXT-ONLY. The Screenshot Service captures images for the 
Vision Agent to analyze. Never send image data directly to LM Studio text-only model.

Version: 1.0
Last Updated: 2026-08-07
"""

from typing import Any, Dict, List, Optional


# Screenshot Service registration in communication bus
SCREENSHOT_SERVICE_ID = "screenshot_service"
SCREENSHOT_SERVICE_TYPE = "screenshot_management"


def register_screenshot_service() -> Dict[str, Any]:
    """
    Register the Screenshot Service with the communication bus.

    Returns:
        Registration confirmation dictionary
    """
    return {
        "service_id": SCREENSHOT_SERVICE_ID,
        "service_type": SCREENSHOT_SERVICE_TYPE,
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
        "methods": {
            "capture_full_page": "async capture_full_page(page_url, session_id, milestone_id, task_id)",
            "capture_element": "async capture_element(page_url, session_id, milestone_id, task_id, selector)",
            "capture_region": "async capture_region(page_url, session_id, milestone_id, task_id, x, y, width, height)",
            "get_metadata": "get_metadata(screenshot_id)",
            "archive_session": "async archive_session(session_id, keep_screenshots=True)",
            "cleanup_expired": "async cleanup_expired(hours=None)",
        },
        "registered": True,
    }


def build_screenshot_message(
    method: str,
    session_id: str,
    milestone_id: str,
    task_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Build a message for the Screenshot Service.

    Args:
        method: Method to call (capture_full_page, capture_element, etc.)
        session_id: Session identifier
        milestone_id: Milestone identifier
        task_id: Task identifier
        **kwargs: Additional parameters specific to the method

    Returns:
        Message dictionary ready for routing
    """
    return {
        "service_id": SCREENSHOT_SERVICE_ID,
        "method": method,
        "session_id": session_id,
        "milestone_id": milestone_id,
        "task_id": task_id,
        "payload": kwargs,
        "priority": "normal",
        "route": "screenshot_capture",
    }


def route_screenshot_request(
    message: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Route a screenshot request to the Screenshot Service.

    Args:
        message: Message dictionary with task details

    Returns:
        Processed response or None if routing failed
    """
    from ai_agents.scripts.screenshot_service import create_screenshot_service
    
    method = message.get("method")
    payload = message.get("payload", {})
    
    if method not in ["capture_full_page", "capture_element", "capture_region"]:
        return None
    
    # Create service and call appropriate method
    try:
        async def execute_capture():
            service = await create_screenshot_service()
            
            if method == "capture_full_page":
                result, metadata = await service.capture_full_page(
                    page_url=payload.get("page_url", ""),
                    session_id=payload.get("session_id", ""),
                    milestone_id=payload.get("milestone_id", ""),
                    task_id=payload.get("task_id", ""),
                    options=None,  # Use default options
                )
                return {
                    "success": result.get("status") == "success",
                    "result": result,
                    "metadata": metadata.to_dict() if metadata else None,
                }
            elif method == "capture_element":
                result, metadata = await service.capture_element(
                    page_url=payload.get("page_url", ""),
                    session_id=payload.get("session_id", ""),
                    milestone_id=payload.get("milestone_id", ""),
                    task_id=payload.get("task_id", ""),
                    selector=payload.get("selector", ""),
                )
                return {
                    "success": result.get("status") == "success",
                    "result": result,
                    "metadata": metadata.to_dict() if metadata else None,
                }
            elif method == "capture_region":
                result, metadata = await service.capture_region(
                    page_url=payload.get("page_url", ""),
                    session_id=payload.get("session_id", ""),
                    milestone_id=payload.get("milestone_id", ""),
                    task_id=payload.get("task_id", ""),
                    x=payload.get("x", 0),
                    y=payload.get("y", 0),
                    width=payload.get("width", 0),
                    height=payload.get("height", 0),
                )
                return {
                    "success": result.get("status") == "success",
                    "result": result,
                    "metadata": metadata.to_dict() if metadata else None,
                }
            return None
        
        # Execute in event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(execute_capture())
        finally:
            loop.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def get_screenshot_service_info() -> Dict[str, Any]:
    """
    Get information about the registered Screenshot Service.

    Returns:
        Service information dictionary
    """
    return {
        "service_id": SCREENSHOT_SERVICE_ID,
        "service_type": SCREENSHOT_SERVICE_TYPE,
        "description": "Screenshot Capture Service for managing browser screenshots",
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
        "model_name": "Native (Playwright integration)",
        "text_only_compatible": False,  # This service handles images for Vision Agent
        "status": "registered",
    }


__all__ = [
    "SCREENSHOT_SERVICE_ID",
    "SCREENSHOT_SERVICE_TYPE", 
    "register_screenshot_service",
    "build_screenshot_message",
    "route_screenshot_request",
    "get_screenshot_service_info",
]
