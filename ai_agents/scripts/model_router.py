#!/usr/bin/env python3
"""
Model Router for Sanskriti AI Studio AI Agents.

This module provides a centralized router for managing and selecting AI models.
It routes requests to the appropriate model based on task type (text or vision).

Architecture:
    Agent Request → Model Router → [Text/Vision/Other Models]

The Model Router ensures:
1. All model selection goes through a single entry point
2. Text-only models never receive image inputs (Qwen 3.5 rule)
3. Vision models handle visual analysis tasks
4. Future models can be added without modifying agents

Version: 1.0
Last Updated: 2026-08-06
"""

import json
import logging
import os
import requests
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("model_router")


class ModelRouterError(Exception):
    """Base exception for model router errors."""
    pass


class ModelNotFoundError(ModelRouterError):
    """Raised when a requested model is not available."""
    pass


class HealthCheckResult:
    """Result of a health check operation."""
    
    def __init__(
        self,
        status: str,
        message: str = "",
        endpoint: Optional[str] = None,
        latency_ms: Optional[float] = None,
        available_models: Optional[List[str]] = None,
    ):
        self.status = status  # healthy | unhealthy | not_found | error
        self.message = message
        self.endpoint = endpoint
        self.latency_ms = latency_ms
        self.available_models = available_models
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "status": self.status,
            "message": self.message,
            "endpoint": self.endpoint,
            "latency_ms": self.latency_ms,
            "available_models": self.available_models,
        }


class ModelInfo:
    """Information about an available model."""
    
    def __init__(
        self,
        id: str,
        object: str,
        created: int,
        owned_by: str,
        size: Optional[int] = None,
        format: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.object = object
        self.created = created
        self.owned_by = owned_by
        self.size = size
        self.format = format
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "owned_by": self.owned_by,
            "size": self.size,
            "format": self.format,
            **(self.details or {}),
        }


class ModelRouter:
    """
    Centralized router for AI model selection and management.
    
    The Model Router provides a single interface for all agents to request models.
    It ensures proper separation of concerns:
    - Text models go through get_text_model()
    - Vision models go through get_vision_model()
    - All routing logic is centralized here
    
    This prevents hardcoding model names in agent implementations.
    """
    
    # Model type constants
    TEXT_MODEL = "text"
    VISION_MODEL = "vision"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Model Router.
        
        Args:
            config: Optional configuration dictionary with model settings
        """
        self._config = config or {}
        self._base_url = self._get_env("LM_STUDIO_BASE_URL", "http://localhost:1234")
        self._text_model_name = self._get_env("CODING_MODEL", "")
        self._vision_model_name = self._get_env("VISION_MODEL", "")
        
        # Connection state
        self._connected: bool = False
        self._last_error: Optional[str] = None
        
        # Cache for health check results
        self._health_cache: Optional[HealthCheckResult] = None
        self._health_cache_expiry: float = 0.0
        
    @property
    def base_url(self) -> str:
        """Get the LM Studio base URL."""
        return self._base_url.rstrip("/")
    
    @property
    def text_model(self) -> Optional[str]:
        """Get the configured text model name."""
        return self._text_model_name
    
    @property
    def vision_model(self) -> Optional[str]:
        """Get the configured vision model name."""
        return self._vision_model_name
    
    def _get_env(self, variable: str, default: Any = None) -> Any:
        """Get environment variable value or return default if not set."""
        env_var = f"LM_STUDIO_{variable.upper()}"
        value = os.environ.get(env_var, default)
        return value if value else default
    
    def get_text_model(self) -> str:
        """
        Get the text model for text-only tasks.
        
        Returns:
            Model name to use for coding/documentation/debugging tasks.
            
        Raises:
            ModelNotFoundError: If no text model is configured.
        """
        if not self._text_model_name:
            raise ModelNotFoundError(
                "Text model not configured. Set LM_STUDIO_CODING_MODEL environment variable."
            )
        
        # Log model selection for audit trail
        logger.info(f"[TEXT-ROUTER] Selected text model: {self._text_model_name}")
        
        return self._text_model_name
    
    def get_vision_model(self) -> str:
        """
        Get the vision model for visual analysis tasks.
        
        Returns:
            Model name to use for vision agent (Qwen2.5-VL or similar).
            
        Raises:
            ModelNotFoundError: If no vision model is configured.
        """
        if not self._vision_model_name:
            raise ModelNotFoundError(
                "Vision model not configured. Set LM_STUDIO_VISION_MODEL environment variable."
            )
        
        # Log model selection for audit trail
        logger.info(f"[VISION-ROUTER] Selected vision model: {self._vision_model_name}")
        
        return self._vision_model_name
    
    def get_current_model(self, model_type: str = "text") -> str:
        """
        Get the current active model based on type.
        
        Args:
            model_type: "text" or "vision"
            
        Returns:
            Active model name
            
        Raises:
            ModelNotFoundError: If requested model type is not configured.
        """
        if model_type == self.TEXT_MODEL:
            return self.get_text_model()
        elif model_type == self.VISION_MODEL:
            return self.get_vision_model()
        else:
            raise ModelNotFoundError(f"Unknown model type: {model_type}")
    
    def health_check(self) -> HealthCheckResult:
        """
        Perform health check on LM Studio endpoint.
        
        Returns:
            Health check result with status and available models.
            
        Raises:
            Exception: If health check fails
        """
        endpoint = f"{self._base_url}/models"
        start_time = time.time()
        
        try:
            response = requests.get(endpoint, timeout=10)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m.get("id") for m in models_data.get("data", [])]
                
                self._connected = True
                self._last_error = None
                
                logger.info(f"[HEALTH-CHECK] Endpoint healthy. Models: {len(available_models)}")
                
                return HealthCheckResult(
                    status="healthy",
                    message="LM Studio endpoint is available",
                    endpoint=endpoint,
                    latency_ms=latency_ms,
                    available_models=available_models,
                )
            elif response.status_code == 404:
                logger.warning(f"[HEALTH-CHECK] Endpoint not found: {endpoint}")
                
                self._connected = False
                return HealthCheckResult(
                    status="not_found",
                    message=f"Endpoint not found: {endpoint}",
                    endpoint=endpoint,
                    latency_ms=latency_ms,
                )
            else:
                error_msg = response.text[:500] if response.text else "Unknown error"
                logger.warning(f"[HEALTH-CHECK] Status {response.status_code}: {error_msg}")
                
                self._connected = False
                return HealthCheckResult(
                    status="error",
                    message=f"HTTP {response.status_code}: {error_msg}",
                    endpoint=endpoint,
                    latency_ms=latency_ms,
                )
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"[HEALTH-CHECK] Connection failed: {e}")
            
            self._connected = False
            self._last_error = str(e)
            
            return HealthCheckResult(
                status="unhealthy",
                message=f"Connection error: {str(e)}",
                endpoint=endpoint,
                latency_ms=None,
            )
        except requests.exceptions.Timeout as e:
            logger.warning(f"[HEALTH-CHECK] Timeout: {e}")
            
            self._connected = False
            return HealthCheckResult(
                status="error",
                message=f"Timeout: {str(e)}",
                endpoint=endpoint,
                latency_ms=None,
            )
        except Exception as e:
            logger.warning(f"[HEALTH-CHECK] Unexpected error: {e}")
            
            self._connected = False
            self._last_error = str(e)
            
            return HealthCheckResult(
                status="error",
                message=f"Error: {str(e)}",
                endpoint=endpoint,
                latency_ms=None,
            )
    
    def is_healthy(self) -> bool:
        """
        Check if LM Studio connection is healthy (with caching).
        
        Returns:
            True if connected and healthy, False otherwise.
        """
        current_time = time.time()
        
        # Use cached result if fresh (< 60 seconds old)
        if self._health_cache and (current_time - self._health_cache_expiry) < 60:
            return self._health_cache.status == "healthy"
        
        # Perform fresh health check
        result = self.health_check()
        
        # Update cache
        self._health_cache = result
        self._health_cache_expiry = current_time + 60
        
        return result.status == "healthy"
    
    def list_available_models(self) -> List[ModelInfo]:
        """
        List all available models from LM Studio.
        
        Returns:
            List of model information dictionaries.
        """
        endpoint = f"{self._base_url}/models"
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                models = []
                
                for model in models_data.get("data", []):
                    info = ModelInfo(
                        id=model.get("id"),
                        object=model.get("object"),
                        created=model.get("created"),
                        owned_by=model.get("owned_by"),
                        size=model.get("size"),
                        format=model.get("format"),
                        details={k: v for k, v in model.items() 
                                if k not in ["id", "object", "created", "owned_by", "size", "format"]},
                    )
                    models.append(info.to_dict())
                
                logger.info(f"[MODELS-LIST] Found {len(models)} available models")
                
                return models
                
            raise ModelNotFoundError(f"Failed to list models: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"[MODELS-LIST] Failed: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Model information or None if not found.
        """
        endpoint = f"{self._base_url}/models/{model_id}"
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                model_data = response.json()
                return ModelInfo(
                    id=model_data.get("id"),
                    object=model_data.get("object"),
                    created=model_data.get("created"),
                    owned_by=model_data.get("owned_by"),
                    size=model_data.get("size"),
                    format=model_data.get("format"),
                    details={k: v for k, v in model_data.items() 
                            if k not in ["id", "object", "created", "owned_by", "size", "format"]},
                )
            elif response.status_code == 404:
                logger.info(f"[MODEL-INFO] Model not found: {model_id}")
                return None
                
            raise ModelNotFoundError(f"Failed to get model info: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"[MODEL-INFO] Failed for {model_id}: {e}")
            return None
    
    def record_request(self, request_id: str, model_type: str, details: Dict[str, Any]) -> None:
        """
        Record a model request for logging/audit purposes.
        
        Args:
            request_id: Unique request identifier
            model_type: "text" or "vision"
            details: Request details (prompt, images, etc.)
        """
        # Get active model name - handle invalid model types gracefully
        if model_type == self.TEXT_MODEL:
            model_name = self.text_model or ""
        elif model_type == self.VISION_MODEL:
            model_name = self.vision_model or ""
        else:
            model_name = ""
        
        log_entry: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_type": model_type,
            "model_name": model_name,
            "details": details if details else {},
        }
        
        logger.info(f"[MODEL-LOG] {json.dumps(log_entry)}")
    
    def _get_active_model(self, model_type: str) -> Optional[str]:
        """Get the active model name for a given type."""
        if model_type == self.TEXT_MODEL:
            return self.text_model
        elif model_type == self.VISION_MODEL:
            return self.vision_model
        return None
    
    def reset_connection(self) -> None:
        """Reset connection state after error recovery."""
        self._connected = False
        self._last_error = None
        logger.info("[CONNECTION-RESET] Connection state reset")


# Factory function for creating Model Router instances
def create_router(config: Optional[Dict[str, Any]] = None) -> ModelRouter:
    """
    Create a Model Router instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured ModelRouter instance
    """
    return ModelRouter(config=config)


# Export public interface
__all__ = [
    "ModelRouter",
    "ModelRouterError",
    "ModelNotFoundError",
    "HealthCheckResult",
    "ModelInfo",
    "create_router",
]
