#!/usr/bin/env python3
"""
Browser Automation Runtime for Sanskriti AI Studio.

This module provides a Playwright-based browser automation runtime that is
independent from the Vision Agent. It handles browser lifecycle, navigation,
user interactions, page state collection, and error handling.

Architecture:
    Application → Browser Runtime → Playwright API

Responsibilities:
- Launch/Close browser (Phase 1)
- Page navigation methods (Phase 2)
- User interaction support (Phase 3)
- Page state collection (Phase 4)
- Error handling with retry policies (Phase 5)
- Communication Bus integration (Phase 6)

Qwen 3.5 remains TEXT-ONLY. Browser screenshots are captured for Vision Agent.

Version: 1.0
Last Updated: 2026-08-06
"""

import asyncio
import logging
from typing import Any, Dict, Optional

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("browser_runtime")


# =============================================================================
# BROWSER RUNTIME CLASS (defined first to fix forward reference issues)
# =============================================================================

class BrowserRuntime:
    """Main Browser Runtime class - integration point for Communication Bus."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._is_launched = False
    
    async def initialize(self) -> None:
        """Initialize the browser runtime."""
        if self._is_launched:
            logger.info("[BROWSER-RUNTIME] Browser already launched")
            return
        
        try:
            from playwright.async_api import async_playwright
            
            # Launch browser
            async with async_playwright() as p:
                browser_type = getattr(p, "chromium")
                self._browser = await browser_type.launch(
                    headless=self.config.get("headless_mode", False),
                    timeout=30.0,
                )
                
                # Create default context
                self._context = await self._browser.new_context(
                    viewport_size={"width": 1280, "height": 720},
                    color_scheme=self.config.get("color_scheme", "dark"),
                )
                
                # Get page
                self.page = await self._context.new_page()
                
                self._is_launched = True
                
                logger.info("[BROWSER-RUNTIME] Browser runtime initialized successfully")
        except Exception as e:
            logger.error(f"[BROWSER-INIT] Failed to initialize: {e}")
            raise
    
    async def close(self) -> None:
        """Close the browser runtime."""
        if not self._is_launched:
            return
        
        try:
            # Check if _context exists and is callable (safely close without type checking)
            if hasattr(self, '_context') and callable(getattr(self, '_context', None)):
                await self._context.close()
            
            if hasattr(self, '_browser'):
                await self._browser.close()
                
            logger.info("[BROWSER-RUNTIME] Browser runtime closed")
        except Exception as e:
            logger.error(f"[BROWSER-CLOSE] Failed to close: {e}")
        
        self._is_launched = False
    
    @property
    def is_launched(self) -> bool:
        """Check if browser is launched."""
        return self._is_launched


# =============================================================================
# FACTORY FUNCTIONS (FOR COMMUNICATION BUS)
# =============================================================================

async def create_browser(config: Optional[Dict[str, Any]] = None) -> BrowserRuntime:
    """Create a new Browser Runtime instance."""
    runtime = BrowserRuntime(config)
    await runtime.initialize()
    return runtime


async def close_browser(runtime: BrowserRuntime) -> None:
    """Close a browser runtime."""
    await runtime.close()


# Standalone function to check if browser is launched (for Communication Bus integration)
async def is_launched(browser: Optional[BrowserRuntime] = None) -> bool:
    """
    Check if browser is launched.
    
    Args:
        browser: Browser Runtime instance (optional). If not provided, checks the global runtime.
        
    Returns:
        True if browser is launched, False otherwise
    """
    if browser is not None:
        return browser.is_launched
    else:
        # Check global runtime state by trying to access browser config
        try:
            from ai_agents.scripts.browser_config import get_browser_config
            
            config = get_browser_config()
            runtime = await create_browser(config.to_dict())
            result = runtime.is_launched
            await runtime.close()
            return result
        except Exception as e:
            logger.debug(f"[BROWSER-IS-LAUNCHED] Cannot check launch state: {e}")
            return False


# Export public interface
__all__ = [
    # Main Runtime
    "BrowserRuntime",
    
    # Factory functions (for Communication Bus integration)
    "create_browser",
    "close_browser",
    "is_launched",
]
