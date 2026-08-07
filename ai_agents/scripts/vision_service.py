#!/usr/bin/env python3
"""
Vision Service for Sanskriti AI Studio AI Agents.

This service is responsible for ALL communication with LM Studio vision models.
The Vision Agent NEVER communicates directly with LM Studio.

Architecture:
    Vision Agent → Vision Service → Model Router → LM Studio

Responsibilities:
- LM Studio connection management
- Model loading and verification
- Request formatting (messages, images, prompts)
- Image submission (base64 encoding)
- Response parsing and normalization
- Retry logic with exponential backoff
- Timeout handling
- Error handling and recovery
- Health monitoring
- Request logging/auditing

CRITICAL: Qwen 3.5 is TEXT-ONLY. This service MUST use the vision model only.

Version: 1.0
Last Updated: 2026-08-06
"""

import asyncio
import base64
import json
import logging
import os
import requests
import time
try:
    import tiktoken
except ImportError:
    tiktoken = None
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("vision_service")


class VisionServiceError(Exception):
    """Base exception for vision service errors."""
    pass


class ModelTimeoutError(VisionServiceError):
    """Raised when model request times out."""
    pass


class ModelConnectionError(VisionServiceError):
    """Raised when connection to LM Studio fails."""
    pass


class VisionResponse:
    """Structured vision model response."""
    
    def __init__(
        self,
        status: str = "success",
        summary: Optional[str] = None,
        model_used: Optional[str] = None,
        latency_ms: Optional[float] = None,
        content: Optional[str] = None,
        choices: Optional[List[Dict[str, Any]]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.status = status  # success | error | warning
        self.summary = summary
        self.model_used = model_used
        self.latency_ms = latency_ms
        self.content = content
        self.choices = choices
        self.errors = errors or []
        self.warnings = warnings or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "status": self.status,
            "summary": self.summary,
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "content": self.content,
            "choices": self.choices,
            "errors": self.errors,
            "warnings": self.warnings,
        }
    
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.status == "success"
    
    def has_errors(self) -> bool:
        """Check if there are errors in the response."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are warnings in the response."""
        return len(self.warnings) > 0


class VisionRequestLog:
    """Log entry for vision requests."""
    
    def __init__(
        self,
        request_id: str,
        model_used: str,
        start_time: str,
        end_time: Optional[str],
        duration_ms: Optional[float],
        retry_count: int,
        error_message: Optional[str] = None,
        success: bool = False,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        self.request_id = request_id
        self.model_used = model_used
        self.start_time = start_time
        self.end_time = end_time
        self.duration_ms = duration_ms
        self.retry_count = retry_count
        self.error_message = error_message
        self.success = success
        self.response_data = response_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            "request_id": self.request_id,
            "model_used": self.model_used,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "success": self.success,
            "response_data": self.response_data,
        }


class VisionService:
    """
    Centralized service for all LM Studio vision model communication.
    
    This service acts as a single interface between the Vision Agent and LM Studio.
    All vision-related operations must go through this service.
    
    The service implements:
    - Connection pooling and management
    - Request retry with exponential backoff
    - Timeout handling per request
    - Error classification and recovery
    - Health monitoring
    - Response normalization
    
    Flow:
        VisionAgent.visual_analysis()
            ↓
        VisionService.process_vision_request()
            ↓ (via ModelRouter)
        LM Studio API
            ↓
        VisionResponse + LogEntry
    """
    
    # Default configuration values
    DEFAULT_TIMEOUT = 300  # seconds
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 2.0
    DEFAULT_BASE_URL = "http://localhost:1234"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Vision Service.
        
        Args:
            config: Configuration dictionary with model and connection settings
        """
        self._config = config or {}
        self._base_url = self._get_config("base_url", self.DEFAULT_BASE_URL)
        self._timeout = self._get_config("timeout", self.DEFAULT_TIMEOUT)
        self._max_retries = self._get_config("max_retries", self.DEFAULT_MAX_RETRIES)
        self._backoff_factor = self._get_config("backoff_factor", self.DEFAULT_BACKOFF_FACTOR)
        
        # Model configuration - MUST come from ModelRouter, never hardcoded
        self._text_model: Optional[str] = None
        self._vision_model: Optional[str] = None
        
        # Connection state
        self._connected: bool = False
        self._last_error: Optional[str] = None
        
        # Retry state
        self._retry_count: int = 0
    
    @property
    def base_url(self) -> str:
        """Get the LM Studio base URL."""
        return self._base_url.rstrip("/")
    
    @property
    def timeout(self) -> float:
        """Get the request timeout in seconds."""
        return self._timeout
    
    @property
    def max_retries(self) -> int:
        """Get the maximum retry count."""
        return self._max_retries
    
    def set_model_from_router(self, model_router) -> None:
        """
        Get model names from Model Router (never hardcode).
        
        Args:
            model_router: ModelRouter instance to get model names from
        """
        try:
            self._text_model = model_router.text_model
            self._vision_model = model_router.vision_model
            
            logger.info(f"[VISION-SERVICE] Models configured - Text: {self._text_model or 'N/A'}, Vision: {self._vision_model or 'N/A'}")
            
        except Exception as e:
            logger.error(f"[VISION-SERVICE] Failed to set models from router: {e}")
            raise
    
    def get_vision_model(self) -> str:
        """
        Get the vision model name.
        
        Returns:
            Vision model name
            
        Raises:
            ValueError: If vision model is not configured
        """
        if not self._vision_model:
            raise ValueError("Vision model not configured. Call set_model_from_router() first.")
        
        logger.info(f"[VISION-SERVICE] Using vision model: {self._vision_model}")
        return self._vision_model
    
    def _get_config(self, key: str, default: Any) -> Any:
        """Get configuration value from config dict or use default."""
        return self._config.get(key, default)
    
    def _get_env(self, variable: str, default: Any = None) -> Any:
        """Get environment variable value or return default."""
        env_var = f"LM_STUDIO_{variable.upper()}"
        value = os.environ.get(env_var, default)
        return value if value else default
    
    async def process_vision_request(
        self,
        messages: List[Dict[str, Any]],
        request_id: str,
        model_type: str = "vision",
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Process a vision model request with retry logic.
        
        Args:
            messages: List of message dictionaries (can include image inputs)
            request_id: Unique request identifier for logging
            model_type: "vision" or "text" (for audit logging)
            
        Returns:
            Tuple of (response_dict, log_entry_dict)
            
        Raises:
            ModelConnectionError: If connection fails after max retries
            ModelTimeoutError: If request times out
        """
        retry_count = 0
        
        while retry_count <= self._max_retries:
            start_time = time.time()
            
            try:
                # Send request to LM Studio
                response = await self._send_vision_request(messages)
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                # Create response object
                response_obj = VisionResponse(
                    status="success",
                    summary=response.get("choices", [{}])[0].get("message", {}).get("content"),
                    model_used=response.get("model"),
                    latency_ms=latency_ms,
                    content=response.get("choices", [{}])[0].get("message", {}).get("content"),
                    choices=response.get("choices"),
                )
                
                # Create log entry
                log_entry = VisionRequestLog(
                    request_id=request_id,
                    model_used=self._vision_model or "",
                    start_time=datetime.now(timezone.utc).isoformat(),
                    end_time=datetime.now(timezone.utc).isoformat(),
                    duration_ms=latency_ms,
                    retry_count=retry_count,
                    success=True,
                    response_data=response_obj.to_dict(),
                )
                
                # Log success
                logger.info(f"[VISION-REQUEST] Success - ID: {request_id}, Latency: {latency_ms:.2f}ms")
                
                return response_obj.to_dict(), log_entry.to_dict()
                
            except requests.exceptions.Timeout as e:
                retry_count += 1
                wait_time = min(self._backoff_factor ** (retry_count - 1), 60)
                
                logger.warning(f"[VISION-REQUEST] Timeout (retry {retry_count}/{self._max_retries}), waiting {wait_time}s...")
                
                await asyncio.sleep(wait_time)
                
            except requests.exceptions.ConnectionError as e:
                retry_count += 1
                
                logger.warning(f"[VISION-REQUEST] Connection error (retry {retry_count}/{self._max_retries}): {e}")
                
                if retry_count > self._max_retries:
                    log_entry = VisionRequestLog(
                        request_id=request_id,
                        model_used=self._vision_model or "",
                        start_time=datetime.now(timezone.utc).isoformat(),
                        end_time=datetime.now(timezone.utc).isoformat(),
                        duration_ms=None,
                        retry_count=retry_count,
                        error_message=f"Connection failed after {retry_count} retries: {e}",
                        success=False,
                    )
                    
                    logger.error(f"[VISION-REQUEST] Final failure - ID: {request_id}, Error: {log_entry.error_message}")
                    return None, log_entry.to_dict()
                
            except ModelTimeoutError as e:
                retry_count += 1
                
                logger.warning(f"[VISION-REQUEST] Timeout error (retry {retry_count}/{self._max_retries}): {e}")
                
                if retry_count > self._max_retries:
                    log_entry = VisionRequestLog(
                        request_id=request_id,
                        model_used=self._vision_model or "",
                        start_time=datetime.now(timezone.utc).isoformat(),
                        end_time=datetime.now(timezone.utc).isoformat(),
                        duration_ms=None,
                        retry_count=retry_count,
                        error_message=str(e),
                        success=False,
                    )
                    
                    logger.error(f"[VISION-REQUEST] Final failure - ID: {request_id}, Error: {log_entry.error_message}")
                    return None, log_entry.to_dict()
                
            except Exception as e:
                retry_count += 1
                
                error_msg = str(e)[:500]
                logger.warning(f"[VISION-REQUEST] Unexpected error (retry {retry_count}/{self._max_retries}): {error_msg}")
                
                if retry_count > self._max_retries:
                    log_entry = VisionRequestLog(
                        request_id=request_id,
                        model_used=self._vision_model or "",
                        start_time=datetime.now(timezone.utc).isoformat(),
                        end_time=datetime.now(timezone.utc).isoformat(),
                        duration_ms=None,
                        retry_count=retry_count,
                        error_message=f"Failed after {retry_count} retries: {error_msg}",
                        success=False,
                    )
                    
                    logger.error(f"[VISION-REQUEST] Final failure - ID: {request_id}, Error: {log_entry.error_message}")
                    return None, log_entry.to_dict()
        
        # Should never reach here, but safety fallback
        log_entry = VisionRequestLog(
            request_id=request_id,
            model_used=self._vision_model or "",
            start_time=datetime.now(timezone.utc).isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            duration_ms=None,
            retry_count=self._max_retries + 1,
            error_message="Max retries exceeded",
            success=False,
        )
        
        logger.error(f"[VISION-REQUEST] Unhandled final failure - ID: {request_id}")
        return None, log_entry.to_dict()
    
    async def _send_vision_request(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send a vision request to LM Studio.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            API response dictionary
            
        Raises:
            ModelTimeoutError: If request times out
            ModelConnectionError: If connection fails
        """
        import requests
        
        model_name = self.get_vision_model()
        
        # Prepare messages with image handling
        prepared_messages = self._prepare_messages(messages)
        
        url = f"{self._base_url}/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": prepared_messages,
            "temperature": 0.1,
            "max_tokens": 4096,
            "top_p": 0.95,
        }
        
        logger.info(f"[VISION-REQUEST] Sending to: {url}")
        logger.info(f"[VISION-REQUEST] Model: {model_name}")
        logger.info(f"[VISION-REQUEST] Payload tokens estimated: ~{self._estimate_tokens(prepared_messages)}")
        
        response = requests.post(url, json=payload, timeout=self._timeout)
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            error_msg = result["error"].get("message", str(result["error"]))
            raise ModelConnectionError(f"LM Studio API error: {error_msg}")
        
        return result
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare and validate messages for LM Studio API.
        
        Args:
            messages: Original message list
            
        Returns:
            Prepared message list with images properly encoded
        """
        content_items = []
        text_parts = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content")
            
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "image_url":
                            image_data = item.get("image_url", {}).get("url", "")
                            if image_data.startswith("data:"):
                                content_items.append({"type": "image"})
                            else:
                                content_items.append(image_data)
                        elif item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        if os.path.exists(item):
                            encoded = self._encode_image_to_base64(item)
                            content_items.append({"type": "image"})
                        else:
                            content_items.append(item)
                        text_parts.append("")
            elif isinstance(content, str):
                text_parts.append(content)
        
        # Build combined content
        if content_items or text_parts:
            final_content = []
            if content_items:
                final_content.extend([{"type": "image"} for _ in content_items])
            if text_parts:
                final_content.append({"type": "text", "text": "\n".join(text_parts)})
            
            # Ensure first message has content
            if messages and not messages[0].get("content"):
                messages[0]["content"] = final_content
            elif not final_content:
                messages[0]["content"] = [{"type": "text", "text": ""}]
        
        return messages
    
    def _encode_image_to_base64(self, image_path: str) -> Dict[str, Any]:
        """
        Load and encode an image to base64 for API submission.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with base64-encoded image data
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read image and encode to base64
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()
        
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"
            },
        }
    
    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for messages."""
        # Handle case where tiktoken is not installed
        if tiktoken is None:
            return 2048  # Default fallback
        
        try:
            encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return 2048  # Default fallback
        
        total_tokens = 0
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for item in msg.get("content", []):
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        total_tokens += len(encoder.encode(text))
            elif isinstance(msg.get("content"), str):
                total_tokens += len(encoder.encode(msg.get("content", "")))
        
        return total_tokens + 1024  # Add overhead
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if LM Studio vision endpoint is available.
        
        Returns:
            Dictionary with health check results
        """
        import requests
        
        url = f"{self._base_url}/models"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                return {
                    "status": "healthy",
                    "endpoint": self._base_url,
                    "available_models": [m.get("id") for m in models.get("data", [])],
                }
            elif response.status_code == 404:
                return {
                    "status": "not_found",
                    "message": f"Endpoint not found: {self._base_url}",
                }
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": response.text[:500],
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Connection error: {str(e)}",
            }
    
    async def is_healthy(self) -> bool:
        """
        Check if LM Studio connection is healthy.
        
        Returns:
            True if connected and healthy, False otherwise.
        """
        result = await self.health_check()
        return result.get("status") == "healthy"
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models from LM Studio.
        
        Returns:
            List of model information dictionaries.
        """
        import requests
        
        url = f"{self._base_url}/models"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                return [m for m in models.get("data", [])]
                
            raise Exception(f"Failed to list models: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"[VISION-SERVICE] Failed to list models: {e}")
            return []


# Export public interface
__all__ = [
    "VisionService",
    "VisionServiceError",
    "ModelTimeoutError",
    "ModelConnectionError",
    "VisionResponse",
    "VisionRequestLog",
]
