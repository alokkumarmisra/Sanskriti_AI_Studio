"""LM Studio Manager Service for Sanskriti AI Studio."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests


class LMStudioManager:
    """
    Manager for LM Studio local server communication and model management.
    
    This service communicates with the local LM Studio server (default: localhost:1234)
    to manage models, health checks, and generation tasks.
    
    IMPORTANT: Qwen 3.5 is TEXT-ONLY - never send images to this model.
    Use the configured vision model for visual analysis tasks.
    """

    def __init__(self):
        """Initialize LM Studio manager with configuration from environment."""
        self._base_url = self._get_env("LM_STUDIO_BASE_URL", "http://localhost:1234")
        self._text_model = self._get_env("CODING_MODEL", "")
        self._vision_model = self._get_env("VISION_MODEL", "")

        # Connection state
        self._connected: bool = False
        self._last_error: Optional[str] = None
        self._response_time_ms: float = 0.0
        self._last_health_check: Optional[datetime] = None

    def _get_env(self, variable: str, default: Any = None) -> Any:
        """Get environment variable value or return default."""
        env_var = f"LM_STUDIO_{variable.upper()}"
        value = os.environ.get(env_var, default)
        if variable.upper() in ["CODING_MODEL", "VISION_MODEL"]:
            return value if value else default
        return value if value is not None else default

    def set_base_url(self, url: str) -> None:
        """Set custom base URL for LM Studio."""
        self._base_url = url.rstrip("/")

    def set_text_model(self, model_name: str) -> None:
        """Set text-only model name (e.g., Qwen 3.5)."""
        os.environ['LM_STUDIO_CODING_MODEL'] = model_name
        self._text_model = model_name

    def set_vision_model(self, model_name: str) -> None:
        """Set vision model name (e.g., Qwen-VL-8B)."""
        os.environ['LM_STUDIO_VISION_MODEL'] = model_name
        self._vision_model = model_name

    @property
    def base_url(self) -> str:
        """Get the LM Studio base URL."""
        return self._base_url.rstrip("/") + "/v1"

    @property
    def text_model(self) -> Optional[str]:
        """Get configured text-only model name."""
        return self._text_model if self._text_model else None

    @property
    def vision_model(self) -> Optional[str]:
        """Get configured vision model name."""
        return self._vision_model if self._vision_model else None

    def get_server_url(self) -> str:
        """Get the full server URL without /v1 suffix."""
        return self._base_url.rstrip("/")

    def is_connected(self) -> bool:
        """Check if LM Studio server is reachable."""
        endpoint = f"{self._base_url}/health"

        try:
            response = requests.get(endpoint, timeout=5)

            if response.status_code == 200:
                self._connected = True
                self._last_error = None
                return True
            elif response.status_code == 404:
                chat_endpoint = f"{self._base_url}/chat/completions"
                response = requests.get(chat_endpoint, timeout=5)

                if response.status_code in [200, 400]:
                    self._connected = True
                    self._last_error = None
                    return True

            self._connected = False
            self._last_error = f"HTTP {response.status_code} from {endpoint}"

        except requests.exceptions.ConnectionError:
            self._connected = False
            self._last_error = "Connection refused"
        except requests.exceptions.Timeout:
            self._connected = False
            self._last_error = "Connection timeout"
        except Exception as e:
            self._connected = False
            self._last_error = str(e)

        return False

    def get_response_time(self) -> Optional[float]:
        """Get the last response time in milliseconds."""
        return self._response_time_ms

    def set_last_health_check(self, now: Optional[datetime] = None) -> None:
        """Update last health check timestamp."""
        if now is None:
            now = datetime.now(timezone.utc)
        self._last_health_check = now

    def get_response_time_ms(self) -> float:
        """Get response time in milliseconds."""
        return self._response_time_ms * 1000 if self._response_time_ms else 0.0

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models from LM Studio."""
        try:
            response = requests.get(
                f"{self._base_url}/models",
                timeout=10
            )

            if response.status_code == 200:
                models_data = response.json()

                models = []
                for model in models_data.get("data", []):
                    models.append({
                        "id": model.get("id"),
                        "name": model.get("name") or model.get("id"),
                        "object": model.get("object"),
                        "created": model.get("created"),
                        "owned_by": model.get("owned_by"),
                        "size": model.get("size"),
                        "format": model.get("format"),
                        "quantization": model.get("quantization"),
                        "organization": model.get("organization") or model.get("owned_by"),
                    })

                return models

            return []

        except Exception as e:
            self._last_error = f"Failed to list models: {str(e)}"
            return []

    def get_loaded_models_info(self) -> Dict[str, Any]:
        """Get information about currently loaded models."""
        try:
            response = requests.get(
                f"{self._base_url}/models",
                timeout=10
            )

            if response.status_code == 200:
                models_data = response.json()

                return {
                    "data": models_data,
                    "count": len(models_data.get("data", [])),
                }

            return {"data": [], "count": 0}

        except Exception as e:
            self._last_error = f"Failed to get loaded models: {str(e)}"
            return {"data": [], "count": 0}

    def classify_model(self, model_data: Dict[str, Any]) -> str:
        """Classify model type (TEXT/VISION/MULTIMODAL/UNKNOWN)."""
        model_id = model_data.get("id", "").lower() or model_data.get("name", "").lower()

        vision_keywords = ["vision", "vl", "multimodal", "llava", "qwen-vl"]

        if any(kw in model_id for kw in vision_keywords):
            return "VISION"

        return "TEXT"  # Default to TEXT for safety (Qwen 3.5 rule)

    def get_coding_model(self) -> Optional[str]:
        """Get configured text model."""
        return self.text_model
    
    def get_vision_model(self) -> Optional[str]:
        """Get configured vision model."""
        return self.vision_model

    def generate_text(
        self,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """Generate text using the configured text model."""

        use_model = model or self._text_model

        if not use_model:
            raise ValueError("Text model not configured. Set LM_STUDIO_CODING_MODEL.")

        messages = messages or []

        try:
            result = requests.post(
                f"{self._base_url}/chat/completions",
                json={
                    "model": use_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120,
            )

            if result.status_code == 200:
                data = result.json()

                choices = data.get("choices", [])
                if choices:
                    return {
                        "id": data.get("id"),
                        "object": data.get("object"),
                        "created": data.get("created"),
                        "model": data.get("model") or use_model,
                        "choices": [
                            {
                                "index": item.get("index"),
                                "message": {
                                    "role": item.get("message", {}).get("role"),
                                    "content": item.get("message", {}).get("content", ""),
                                    "tool_calls": item.get("message", {}).get("tool_calls"),
                                },
                                "logprobs": item.get("logprobs"),
                                "finish_reason": item.get("finish_reason"),
                            }
                            for item in data.get("choices", [])
                        ],
                        "usage": data.get("usage"),
                    }

            return None

        except requests.exceptions.Timeout:
            raise Exception("Text generation timeout. Please check LM Studio server.")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            self._last_error = str(e)
            return None

    def generate_vision(
        self,
        model: Optional[str] = None,
        image_path: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """Generate response using the configured vision model."""

        use_model = model or self._vision_model

        if not use_model:
            raise ValueError("Vision model not configured. Set LM_STUDIO_VISION_MODEL.")

        messages = messages or []

        try:
            result = requests.post(
                f"{self._base_url}/chat/completions",
                json={
                    "model": use_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120,
            )

            if result.status_code == 200:
                data = result.json()

                choices = data.get("choices", [])
                if choices:
                    return {
                        "id": data.get("id"),
                        "object": data.get("object"),
                        "created": data.get("created"),
                        "model": data.get("model") or use_model,
                        "choices": [
                            {
                                "index": item.get("index"),
                                "message": {
                                    "role": item.get("message", {}).get("role"),
                                    "content": item.get("message", {}).get("content", ""),
                                    "tool_calls": item.get("message", {}).get("tool_calls"),
                                },
                                "logprobs": item.get("logprobs"),
                                "finish_reason": item.get("finish_reason"),
                            }
                            for item in data.get("choices", [])
                        ],
                        "usage": data.get("usage"),
                    }

            return None

        except requests.exceptions.Timeout:
            raise Exception("Vision generation timeout. Please check LM Studio server.")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            self._last_error = str(e)
            return None
