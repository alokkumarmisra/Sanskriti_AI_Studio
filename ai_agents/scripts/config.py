"""
LM Studio Configuration Module for Sanskriti AI Studio AI Agents

This module provides configuration management for LM Studio connections.
All model names are configurable via environment variables - never hardcoded.

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images to the Coding Model.
"""

import os
from typing import Optional


def get_config():
    """
    Retrieve LM Studio configuration from environment variables.
    
    Returns a dictionary with all configuration values.
    """
    return {
        'base_url': _get_env('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1'),
        'coding_model': _get_env('LM_STUDIO_CODING_MODEL', ''),
        'vision_model': _get_env('LM_STUDIO_VISION_MODEL', ''),
    }


def _get_env(variable: str, default: Optional[str] = None) -> str:
    """
    Get environment variable value or return default if not set.
    
    Args:
        variable: Environment variable name (without LM_STUDIO_ prefix typically)
        default: Default value if env var is not set
    
    Returns:
        Environment variable value or default string
    """
    env_var = f"LM_STUDIO_{variable.upper()}"
    value = os.environ.get(env_var, default)
    
    # Return empty string for unset variables (not None)
    return value if value else ''


def get_base_url() -> str:
    """
    Get the LM Studio base URL.
    
    Returns:
        Base URL for LM Studio API endpoint
    
    Default: http://localhost:1234/v1
    """
    return _get_env('BASE_URL', 'http://localhost:1234/v1')


def set_base_url(url: str) -> None:
    """
    Set the LM Studio base URL.
    
    Args:
        url: New base URL for LM Studio API
    """
    os.environ['LM_STUDIO_BASE_URL'] = url


def get_coding_model() -> str:
    """
    Get the coding model name for text-only requests.
    
    Returns:
        Model name to use for Coding Agent (Qwen 3.5 or similar)
    
    IMPORTANT: This model receives TEXT-ONLY input only.
               Never send images, screenshots, or visual data.
    """
    return _get_env('CODING_MODEL', '')


def set_coding_model(model_name: str) -> None:
    """
    Set the coding model name.
    
    Args:
        model_name: Model identifier for text/code tasks
    
    IMPORTANT: Qwen 3.5 is TEXT-ONLY. This model will not accept image inputs.
    """
    os.environ['LM_STUDIO_CODING_MODEL'] = model_name


def get_vision_model() -> str:
    """
    Get the vision model name for visual analysis.
    
    Returns:
        Model name to use for Vision Agent (Qwen3-VL-8B or similar)
    
    NOTE: This model can process images and visual input.
          The Coding Model should NEVER receive images.
    """
    return _get_env('VISION_MODEL', '')


def set_vision_model(model_name: str) -> None:
    """
    Set the vision model name.
    
    Args:
        model_name: Model identifier for visual analysis tasks
    
    NOTE: Use this for Vision Agent, not Coding Agent.
          Qwen 3.5 (Coding Model) is TEXT-ONLY only.
    """
    os.environ['LM_STUDIO_VISION_MODEL'] = model_name


def get_debugging_model() -> str:
    """
    Get the debugging model name for failure analysis.
    
    Returns:
        Model name to use for Debugging Agent (Qwen 3.5 or similar)
    
    IMPORTANT: This model receives TEXT-ONLY input only.
               Never send images, screenshots, or visual data.
    """
    return _get_env('DEBUGGING_MODEL', '')


def set_debugging_model(model_name: str) -> None:
    """
    Set the debugging model name.
    
    Args:
        model_name: Model identifier for failure analysis tasks
    
    IMPORTANT: Qwen 3.5 is TEXT-ONLY. This model will not accept image inputs.
    """
    os.environ['LM_STUDIO_DEBUGGING_MODEL'] = model_name


def get_coding_model_url() -> str:
    """
    Get the full URL to query the coding model.
    
    Returns:
        Full endpoint URL including model name
    """
    base_url = get_base_url()
    model = get_coding_model()
    
    if not model:
        return f"{base_url}/chat/completions"  # Default to generic chat
    
    # For OpenAI-compatible API with model routing
    return f"{base_url}/chat/completions"


def validate_config() -> dict:
    """
    Validate the LM Studio configuration.
    
    Returns:
        Dictionary with validation results
    
    Raises:
        ValueError: If required configuration is missing or invalid
    """
    config = get_config()
    issues = []
    
    if not config['base_url']:
        issues.append("LM_STUDIO_BASE_URL is not set")
    
    if not config['coding_model']:
        issues.append("LM_STUDIO_CODING_MODEL is not set (required for Coding Agent)")
    
    # Warn about mismatched models
    has_vision_model = bool(config['vision_model'])
    if has_vision_model:
        print(f"[WARN] Vision model set: {config['vision_model']}")
        print("[WARN] Remember: Qwen 3.5 (coding) is TEXT-ONLY, use vision model for images")
    
    return {
        'valid': len(issues) == 0,
        'base_url': config['base_url'],
        'coding_model': config['coding_model'],
        'vision_model': config['vision_model'],
        'issues': issues,
    }


def print_config_status():
    """
    Print current configuration status to console.
    
    Useful for debugging and verification before running agents.
    """
    config = validate_config()
    
    print("=" * 60)
    print("LM STUDIO CONFIGURATION STATUS")
    print("=" * 60)
    print(f"Base URL:     {config['base_url']}")
    print(f"Coding Model: {config['coding_model'] or '(not set - will use default)'}")
    print(f"Vision Model: {config['vision_model'] or '(not set - will use default)'}")
    
    if config['issues']:
        print("\n[ISSUES]")
        for issue in config['issues']:
            print(f"  - {issue}")
    else:
        print("\n✓ Configuration is valid")
    
    print("=" * 60)


if __name__ == '__main__':
    # Example usage when run directly
    print_config_status()
