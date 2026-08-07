"""LM Studio Client for Sanskriti AI Studio."""
import os  # type: ignore[import]
import requests  # type: ignore[import]
from typing import Any, Dict, List, Optional


# Create global client instance for coding model operations
_lmstudio_client = None


class LMStudioClient:
    """Synchronous client for LM Studio v1 chat completion API."""

    def __init__(self) -> None:
        self._base_url = "http://localhost:1234/v1"
        self._model = ""

    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        self._base_url = value.rstrip("/") + "/v1"

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    def chat(
        self,
        messages: List[Dict[str, str]],
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """Send a chat request to LM Studio."""

        if base_url:
            self._base_url = base_url.rstrip("/") + "/v1"
        if model:
            self._model = model

        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise Exception(result["error"]["message"] or str(result["error"]))

        return {
            "id": result.get("id"),
            "object": result.get("object"),
            "created": result.get("created"),
            "model": result.get("model"),
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
                for item in result.get("choices", [])
            ],
            "usage": result.get("usage"),
        }

    def generate(
        self,
        prompt: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Generate text using LM Studio's completion API."""

        if base_url:
            self._base_url = base_url.rstrip("/") + "/v1"
        if model:
            self._model = model

        url = f"{self._base_url}/completions"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise Exception(result["error"]["message"] or str(result["error"]))

        return {
            "id": result.get("id"),
            "object": result.get("object"),
            "created": result.get("created"),
            "model": result.get("model"),
            "choices": [
                {
                    "text": choice.get("text", ""),
                    "finish_reason": choice.get("finish_reason"),
                }
                for choice in result.get("choices", [])
            ],
        }


def chat_with_coding_model(
    messages: List[Dict[str, str]],
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 0.9,
) -> Dict[str, Any]:
    """
    Chat with a coding-focused model via LM Studio.
    
    This is a convenience wrapper for coding/analysis tasks.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        base_url: Optional custom LM Studio API URL
        model: Optional model name (defaults to env var or empty)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
    
    Returns:
        Chat response dict with choices, model info, etc.
    
    Raises:
        Exception: If API request fails or model returns an error
    """
    client = LMStudioClient()
    
    # Get config from environment
    if model is None:
        model = os.getenv("QWEN_3_5_MODEL", "")
    if base_url is None:
        base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    
    # Apply to client
    client.base_url = base_url
    client.model = model
    
    # Use the chat method with default parameters
    return client.chat(
        messages=messages,
        base_url=None,  # Already set above
        model=None,     # Already set above
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )
