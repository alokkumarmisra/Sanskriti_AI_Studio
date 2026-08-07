#!/usr/bin/env python3
"""
Vision Configuration Module for Sanskriti AI Studio.

This module provides centralized configuration for all vision-related operations.
All configuration values are externalized - never hardcoded in agents.

Configuration Categories:
1. Connection Settings
2. Model Settings
3. Request Settings
4. Retry/Timeout Settings

CRITICAL: Qwen 3.5 is TEXT-ONLY. Vision configuration MUST use the vision model only.

Version: 1.0
Last Updated: 2026-08-06
"""

import logging
import os
from typing import Any, Dict, Optional

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("vision_config")


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    pass


class VisionConfiguration:
    """
    Centralized configuration for all vision-related operations.
    
    Configuration is loaded from environment variables and defaults.
    All values are validated before use.
    """
    
    # Default connection settings
    DEFAULT_BASE_URL = "http://localhost:1234"
    DEFAULT_TIMEOUT = 300  # seconds
    
    # Default model settings
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_TOKENS = 4096
    
    # Default retry/timeout settings
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_BACKOFF_FACTOR = 2.0
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the configuration with defaults or custom values.
        
        Args:
            config: Custom configuration dictionary (can override defaults)
        """
        self._config = config or {}
        self._validated: bool = False
        self._issues: list = []
    
    @property
    def base_url(self) -> str:
        """Get the LM Studio base URL."""
        return self._get("base_url", self.DEFAULT_BASE_URL)
    
    @property
    def timeout(self) -> int:
        """Get the request timeout in seconds."""
        return self._get("timeout", self.DEFAULT_TIMEOUT)
    
    @property
    def temperature(self) -> float:
        """Get the model temperature (0.0 to 2.0)."""
        temp = self._get("temperature", self.DEFAULT_TEMPERATURE)
        return float(temp) if temp else self.DEFAULT_TEMPERATURE
    
    @property
    def max_tokens(self) -> int:
        """Get maximum tokens to generate."""
        return self._get("max_tokens", self.DEFAULT_MAX_TOKENS)
    
    @property
    def retry_count(self) -> int:
        """Get the maximum retry count for failed requests."""
        retries = self._get("retry_count", self.DEFAULT_RETRY_COUNT)
        return int(retries) if retries else self.DEFAULT_RETRY_COUNT
    
    @property
    def backoff_factor(self) -> float:
        """Get the exponential backoff factor."""
        return float(self._get("backoff_factor", self.DEFAULT_BACKOFF_FACTOR))
    
    def _get(
        self,
        key: str,
        default: Any,
        config_key: Optional[str] = None,
    ) -> Any:
        """
        Get configuration value from custom config or environment.
        
        Args:
            key: Internal configuration key
            default: Default value to use if not configured
            config_key: Optional alternative key name in config dict
            
        Returns:
            Configuration value or default
        """
        # Check custom config first
        if config_key:
            if key in self._config:
                return self._config[key]
        
        # Then check environment variable
        env_var = f"VISION_{key.upper().replace('_', '_')}"
        value = os.environ.get(env_var)
        
        if value is not None and value:
            try:
                # Try to parse as int/float if it looks like a number
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                return value
        
        return default
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate the configuration.
        
        Returns:
            Dictionary with validation results including issues
            
        Raises:
            ConfigValidationError: If critical configuration is missing
        """
        self._issues = []
        
        # Validate base URL
        base_url = self.base_url
        if not base_url:
            self._issues.append("LM_STUDIO_BASE_URL environment variable is not set")
        
        # Base URL must be valid
        try:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            if not parsed.scheme or not parsed.netloc:
                self._issues.append(f"Invalid base URL format: {base_url}")
        except Exception as e:
            self._issues.append(f"Failed to parse base URL: {e}")
        
        # Validate timeout
        timeout = self.timeout
        if not (10 <= timeout <= 600):
            self._issues.append(f"Timeout must be between 10 and 600 seconds, got {timeout}")
        
        # Validate temperature
        temp = self.temperature
        if not (0.0 <= temp <= 2.0):
            self._issues.append(f"Temperature must be between 0.0 and 2.0, got {temp}")
        
        # Validate max tokens
        tokens = self.max_tokens
        if not (100 <= tokens <= 32768):
            self._issues.append(f"Max tokens must be between 100 and 32768, got {tokens}")
        
        # Validate retry count
        retries = self.retry_count
        if not (0 <= retries <= 10):
            self._issues.append(f"Retry count must be between 0 and 10, got {retries}")
        
        # Mark as validated
        self._validated = len(self._issues) == 0
        
        return {
            "valid": len(self._issues) == 0,
            "base_url": base_url,
            "timeout": timeout,
            "temperature": temp,
            "max_tokens": tokens,
            "retry_count": retries,
            "backoff_factor": self.backoff_factor,
            "issues": self._issues,
        }
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "retry_count": self.retry_count,
            "backoff_factor": self.backoff_factor,
        }


def get_vision_config(config: Optional[Dict[str, Any]] = None) -> VisionConfiguration:
    """
    Get a vision configuration instance.
    
    Args:
        config: Optional custom configuration to override defaults
        
    Returns:
        VisionConfiguration instance with environment-based settings
    """
    return VisionConfiguration(config=config)


def validate_vision_config() -> Dict[str, Any]:
    """
    Validate the current vision configuration.
    
    Returns:
        Dictionary with validation results
    """
    config = get_vision_config()
    result = config.validate()
    
    if not result["valid"]:
        logger.warning(f"[VISION-CFG] Configuration has issues: {result['issues']}")
    
    return result


def print_config_status():
    """Print current configuration status to console."""
    config = validate_vision_config()
    
    print("=" * 60)
    print("VISION CONFIGURATION STATUS")
    print("=" * 60)
    print(f"Base URL:     {config['base_url']}")
    print(f"Timeout:      {config['timeout']} seconds")
    print(f"Temperature:  {config['temperature']}")
    print(f"Max Tokens:   {config['max_tokens']}")
    print(f"Retry Count:  {config['retry_count']}")
    
    if config["issues"]:
        print("\n[ISSUES]")
        for issue in config["issues"]:
            print(f"  - {issue}")
    else:
        print("\n✓ Configuration is valid")
    
    print("=" * 60)


# Export public interface
__all__ = [
    "ConfigValidationError",
    "VisionConfiguration",
    "get_vision_config",
    "validate_vision_config",
    "print_config_status",
]
