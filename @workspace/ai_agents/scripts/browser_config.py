#!/usr/bin/env python3
"""
Browser Configuration for Sanskriti AI Studio Browser Automation Runtime.

This module provides centralized configuration for the Playwright browser runtime.
All configuration values are externalized via environment variables.

Architecture:
    Application → Browser Config → Environment Variables

Responsibilities:
- Externalize browser type, headless mode, timeouts, viewport
- Configuration validation with error reporting
- Default fallback values

Version: 1.0
Last Updated: 2026-08-06
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("browser_config")


@dataclass
class BrowserConfig:
    """
    Configuration class for Playwright browser runtime.
    
    All values can be overridden via environment variables:
    - BROWSER_TYPE (chromium/firefox/webkit)
    - HEADLESS_MODE (true/false)
    - DEFAULT_TIMEOUT (in seconds)
    - VIEWPORT_WIDTH (in pixels)
    - VIEWPORT_HEIGHT (in pixels)
    - NAVIGATION_TIMEOUT (in seconds)
    - ELEMENT_TIMEOUT (in milliseconds)
    - RETRY_COUNT (number of retries for operations)
    """
    
    # Browser type
    browser_type: str = "chromium"  # chromium | firefox | webkit
    
    # Execution mode
    headless_mode: bool = False  # false for visible, true for headless
    
    # Timeout settings (in seconds)
    default_timeout: float = 30.0
    navigation_timeout: float = 30.0
    element_timeout: int = 5000  # 5 seconds in milliseconds
    
    # Viewport dimensions
    viewport_width: int = 1280
    viewport_height: int = 720
    
    # Retry policy
    retry_count: int = 3
    backoff_factor: float = 2.0
    
    # Browser arguments (for headless/visible mode)
    browser_args: list = field(default_factory=list)
    
    # Color scheme
    color_scheme: str = "dark"  # dark | light | auto
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.browser_type not in ["chromium", "firefox", "webkit"]:
            raise ValueError(f"Invalid browser type: {self.browser_type}. Must be 'chromium', 'firefox', or 'webkit'.")
        
        if self.headless_mode not in [True, False]:
            raise ValueError(f"Invalid headless_mode: {self.headless_mode}. Must be True or False.")
        
        if self.default_timeout <= 0:
            raise ValueError(f"default_timeout must be positive, got {self.default_timeout}")
        
        if self.navigation_timeout <= 0:
            raise ValueError(f"navigation_timeout must be positive, got {self.navigation_timeout}")
        
        if self.element_timeout <= 0:
            raise ValueError(f"element_timeout must be positive, got {self.element_timeout}")
        
        if self.viewport_width <= 0 or self.viewport_height <= 0:
            raise ValueError(f"Viewport dimensions must be positive")
        
        if self.retry_count < 1:
            raise ValueError(f"retry_count must be at least 1, got {self.retry_count}")
    
    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """
        Create BrowserConfig instance from environment variables.
        
        Returns:
            Configured BrowserConfig instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Read browser type
        browser_type_env = os.environ.get("BROWSER_TYPE", "")
        if not browser_type_env:
            browser_type = "chromium"
            logger.info("[BROWSER-CONFIG] Using default browser type: chromium")
        else:
            browser_type = browser_type_env.lower().strip()
            logger.info(f"[BROWSER-CONFIG] Browser type from env: {browser_type}")
        
        # Read headless mode
        headless_str = os.environ.get("HEADLESS_MODE", "false").lower().strip()
        headless_mode = headless_str == "true"
        logger.info(f"[BROWSER-CONFIG] Headless mode from env: {headless_mode}")
        
        # Read default timeout (in seconds)
        timeout_env = os.environ.get("DEFAULT_TIMEOUT", "30")
        try:
            default_timeout = float(timeout_env)
        except ValueError:
            default_timeout = 30.0
            logger.warning(f"[BROWSER-CONFIG] Invalid DEFAULT_TIMEOUT '{timeout_env}', using default: {default_timeout}")
        
        # Read viewport dimensions
        width_env = os.environ.get("VIEWPORT_WIDTH", "1280")
        try:
            viewport_width = int(width_env)
        except ValueError:
            viewport_width = 1280
            logger.warning(f"[BROWSER-CONFIG] Invalid VIEWPORT_WIDTH '{width_env}', using default: {viewport_width}")
        
        height_env = os.environ.get("VIEWPORT_HEIGHT", "720")
        try:
            viewport_height = int(height_env)
        except ValueError:
            viewport_height = 720
            logger.warning(f"[BROWSER-CONFIG] Invalid VIEWPORT_HEIGHT '{height_env}', using default: {viewport_height}")
        
        # Read navigation timeout (in seconds)
        nav_timeout_env = os.environ.get("NAVIGATION_TIMEOUT", "30")
        try:
            navigation_timeout = float(nav_timeout_env)
        except ValueError:
            navigation_timeout = 30.0
            logger.warning(f"[BROWSER-CONFIG] Invalid NAVIGATION_TIMEOUT '{nav_timeout_env}', using default: {navigation_timeout}")
        
        # Read element timeout (in milliseconds)
        elem_timeout_env = os.environ.get("ELEMENT_TIMEOUT", "5000")
        try:
            element_timeout = int(elem_timeout_env)
        except ValueError:
            element_timeout = 5000
            logger.warning(f"[BROWSER-CONFIG] Invalid ELEMENT_TIMEOUT '{elem_timeout_env}', using default: {element_timeout}")
        
        # Read retry count
        retry_env = os.environ.get("RETRY_COUNT", "3")
        try:
            retry_count = int(retry_env)
        except ValueError:
            retry_count = 3
            logger.warning(f"[BROWSER-CONFIG] Invalid RETRY_COUNT '{retry_env}', using default: {retry_count}")
        
        # Read backoff factor
        backoff_env = os.environ.get("BACKOFF_FACTOR", "2.0")
        try:
            backoff_factor = float(backoff_env)
        except ValueError:
            backoff_factor = 2.0
            logger.warning(f"[BROWSER-CONFIG] Invalid BACKOFF_FACTOR '{backoff_env}', using default: {backoff_factor}")
        
        # Read color scheme
        color_scheme_env = os.environ.get("COLOR_SCHEME", "dark")
        valid_schemes = ["dark", "light", "auto"]
        if color_scheme_env.lower() in valid_schemes:
            color_scheme = color_scheme_env.lower()
        else:
            logger.warning(f"[BROWSER-CONFIG] Invalid COLOR_SCHEME '{color_scheme_env}', using default: dark")
            color_scheme = "dark"
        
        # Read browser arguments
        args_env = os.environ.get("BROWSER_ARGS", "")
        if args_env:
            try:
                import shlex
                browser_args = shlex.split(args_env)
            except ValueError as e:
                logger.warning(f"[BROWSER-CONFIG] Failed to parse BROWSER_ARGS, using empty list")
                browser_args = []
        else:
            browser_args = []
        
        # Create and return configuration instance
        config = cls(
            browser_type=browser_type,
            headless_mode=headless_mode,
            default_timeout=default_timeout,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            navigation_timeout=navigation_timeout,
            element_timeout=element_timeout,
            retry_count=retry_count,
            backoff_factor=backoff_factor,
            color_scheme=color_scheme,
            browser_args=browser_args,
        )
        
        logger.info("[BROWSER-CONFIG] Configuration loaded successfully")
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "browser_type": self.browser_type,
            "headless_mode": self.headless_mode,
            "default_timeout": self.default_timeout,
            "navigation_timeout": self.navigation_timeout,
            "element_timeout": self.element_timeout,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "retry_count": self.retry_count,
            "backoff_factor": self.backoff_factor,
            "color_scheme": self.color_scheme,
            "browser_args": self.browser_args,
        }
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if self.browser_type not in ["chromium", "firefox", "webkit"]:
            errors.append(f"Invalid browser type: {self.browser_type}")
        
        if self.default_timeout <= 0:
            errors.append(f"default_timeout must be positive, got {self.default_timeout}")
        
        if self.navigation_timeout <= 0:
            errors.append(f"navigation_timeout must be positive, got {self.navigation_timeout}")
        
        if self.element_timeout <= 0:
            errors.append(f"element_timeout must be positive, got {self.element_timeout}")
        
        if self.viewport_width <= 0 or self.viewport_height <= 0:
            errors.append("Viewport dimensions must be positive")
        
        if len(errors) > 0:
            logger.error(f"[BROWSER-CONFIG] Configuration validation failed with {len(errors)} error(s): {', '.join(errors)}")
            return False, errors
        
        logger.debug("[BROWSER-CONFIG] Configuration validated successfully")
        return True, []


# Singleton configuration instance
_global_config: Optional[BrowserConfig] = None


def get_browser_config() -> BrowserConfig:
    """
    Get the global browser configuration instance.
    
    Returns:
        BrowserConfig instance loaded from environment variables
    
    Raises:
        ValueError: If configuration is not initialized or invalid
    """
    global _global_config
    
    if _global_config is None:
        _global_config = BrowserConfig.from_env()
    
    return _global_config


def reload_browser_config() -> BrowserConfig:
    """
    Reload browser configuration from environment variables.
    
    Returns:
        Fresh BrowserConfig instance
    
    Raises:
        ValueError: If configuration is invalid
    """
    global _global_config
    _global_config = None  # Reset singleton
    return get_browser_config()


def set_browser_config(config: BrowserConfig) -> None:
    """
    Set the global browser configuration.
    
    Args:
        config: BrowserConfig instance to use globally
    """
    global _global_config
    _global_config = config
    logger.info(f"[BROWSER-CONFIG] Configuration set to browser_type={config.browser_type}, headless={config.headless_mode}")


# Export public interface
__all__ = [
    "BrowserConfig",
    "get_browser_config",
    "reload_browser_config",
    "set_browser_config",
]
