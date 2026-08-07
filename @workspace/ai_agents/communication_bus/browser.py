"""
Browser Runtime Registration for Communication Bus.

This module registers the Browser Automation Runtime with the communication bus system,
enabling message routing between agents and browser automation capabilities.

The Browser Runtime is independent from the Vision Agent.
Future consumers:
- Testing Agent (browser testing)
- Reviewer Agent (UI verification)
- Other automation tasks

Version: 1.0
Last Updated: 2026-08-06
"""

from typing import Any, Callable, Dict, List, Optional


# Browser Runtime registration in communication bus
BROWSER_RUNTIME_ID = "browser_runtime"
BROWSER_RUNTIME_TYPE = "browser_automation"


def register_browser_runtime(agent: Any) -> Dict[str, Any]:
    """
    Register the Browser Runtime with the communication bus.

    Args:
        agent: The BrowserRuntime instance to register

    Returns:
        Registration confirmation dictionary
    """
    registration = {
        "agent_id": BROWSER_RUNTIME_ID,
        "agent_type": BROWSER_RUNTIME_TYPE,
        "capabilities": [
            "launch_browser",
            "close_browser",
            "navigate_to_url",
            "page_interactions",
            "element_manipulation",
            "page_state_collection",
            "error_handling",
            "browser_testing",
        ],
        "browser_type": "chromium",
        "headless_mode": False,
        "text_only": True,  # Browser runtime itself is text-only
        "registered": True,
    }

    return registration


def build_browser_message(
    action: str,
    url: Optional[str] = None,
    selector: Optional[str] = None,
    value: Optional[str] = None,
    element_index: Optional[int] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Build a message for the Browser Runtime.

    Args:
        action: Action to perform (launch, navigate, click, fill, etc.)
        url: URL to navigate to (optional)
        selector: CSS selector for element interaction (optional)
        value: Text/value to set in input (optional)
        element_index: Index if targeting multiple elements (optional)
        timeout: Operation timeout in seconds (optional)

    Returns:
        Message dictionary ready for routing
    """
    message = {
        "agent_id": BROWSER_RUNTIME_ID,
        "action": action,
        "priority": "normal",
        "route": "browser_automation",
    }

    if url is not None:
        message["url"] = url
    if selector is not None:
        message["selector"] = selector
    if value is not None:
        message["value"] = value
    if element_index is not None:
        message["element_index"] = element_index
    if timeout is not None:
        message["timeout"] = timeout

    return message


async def execute_browser_action(
    message: Dict[str, Any],
    browser_runtime=None,
) -> Optional[Dict[str, Any]]:
    """
    Execute a browser action via the runtime.

    Args:
        message: Message dictionary with action details
        browser_runtime: Optional BrowserRuntime instance (if not using global registry)

    Returns:
        Processed response or None if routing failed
    """
    agent_id = message.get("agent_id")
    action = message.get("action", "")
    url = message.get("url")
    selector = message.get("selector")
    value = message.get("value")
    element_index = message.get("element_index")

    if agent_id != BROWSER_RUNTIME_ID:
        return None

    # Process the browser action
    try:
        from scripts.browser_runtime import BrowserRuntime, create_browser, close_browser
        from scripts.browser_config import get_browser_config

        runtime = browser_runtime or await create_browser()
        response = {}

        # Handle different actions
        if action == "launch":
            await runtime.launch()
            response = {
                "success": True,
                "action": "launch",
                "status": "browser_launched",
            }

        elif action == "navigate":
            url = url or message.get("url")
            if url:
                current_url = await runtime.goto(url)
                response = {
                    "success": True,
                    "action": "navigate",
                    "current_url": current_url,
                }
            else:
                response = {"success": False, "error": "URL required for navigation"}

        elif action == "click":
            selector = selector or message.get("selector")
            if selector:
                await runtime.click(selector)
                response = {
                    "success": True,
                    "action": "click",
                    "selector": selector,
                }
            else:
                response = {"success": False, "error": "Selector required for click"}

        elif action == "fill":
            selector = selector or message.get("selector")
            if selector and value:
                await runtime.fill(selector, value)
                response = {
                    "success": True,
                    "action": "fill",
                    "selector": selector,
                    "value": value,
                }
            else:
                response = {"success": False, "error": "Selector and value required"}

        elif action == "get_title":
            title = await runtime.get_title()
            response = {
                "success": True,
                "action": "get_title",
                "title": title,
            }

        elif action == "get_url":
            url = await runtime.get_url()
            response = {
                "success": True,
                "action": "get_url",
                "url": url,
            }

        elif action == "console_errors":
            errors = await runtime.console_errors()
            response = {
                "success": True,
                "action": "console_errors",
                "errors": errors,
            }

        elif action == "close":
            await runtime.close()
            response = {
                "success": True,
                "action": "close",
                "status": "browser_closed",
            }

        else:
            response = {"success": False, "error": f"Unknown action: {action}"}

        # Log request
        log_entry = {
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "action": action,
            "status": response.get("success", False),
            "details": {k: v for k, v in response.items() if k not in ["success"]},
        }
        logger.info(f"[BROWSER-BUS] Action: {action} - Status: {response.get('success')}, Details: {log_entry}")

        return response

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_id": agent_id,
        }


def route_browser_request(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Route a browser request to the Browser Runtime.

    Args:
        message: Message dictionary with action details

    Returns:
        Processed response or None if routing failed
    """
    agent_id = message.get("agent_id")

    if agent_id != BROWSER_RUNTIME_ID:
        return None

    # Execute the browser action (async call handled by caller)
    # This is a synchronous stub for non-async context
    return {
        "status": "pending",
        "message": "Browser action queued for execution",
        "agent_id": agent_id,
    }


def get_browser_runtime_info() -> Dict[str, Any]:
    """
    Get information about the registered Browser Runtime.

    Returns:
        Agent information dictionary
    """
    return {
        "agent_id": BROWSER_RUNTIME_ID,
        "agent_type": BROWSER_RUNTIME_TYPE,
        "description": "Browser Automation Runtime for Playwright-based browser automation",
        "capabilities": [
            "launch_browser",
            "close_browser",
            "navigate_to_url",
            "page_interactions",
            "element_manipulation",
            "page_state_collection",
            "error_handling",
            "browser_testing",
        ],
        "browser_type": "chromium",
        "headless_mode": False,
        "text_only_compatible": True,
        "status": "registered",
    }


# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
import logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("browser_bus")


# Register agent at module level for bootstrap integration
__all__ = [
    "BROWSER_RUNTIME_ID",
    "BROWSER_RUNTIME_TYPE",
    "register_browser_runtime",
    "build_browser_message",
    "execute_browser_action",
    "route_browser_request",
    "get_browser_runtime_info",
]
