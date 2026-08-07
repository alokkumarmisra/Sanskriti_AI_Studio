"""LM Studio Client for Sanskriti AI Studio."""
import os
import requests
from typing import Any, Dict, List, Optional


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


# =============================================================================
# STANDALONE FUNCTIONS (for direct import)
# =============================================================================

def chat_with_coding_model(
    messages: List[Dict[str, str]],
    base_url: str = "http://localhost:1234/v1",
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """
    Standalone function to chat with the coding model for LM Studio.
    
    Args:
        messages: List of message dicts with role and content
        base_url: Base URL for LM Studio API
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    
    Returns:
        Chat response from LM Studio
    """
    client = LMStudioClient()
    client.base_url = base_url
    client.model = model
    
    return client.chat(
        messages=messages,
        base_url=None,  # Already set
        model=None,     # Already set
        temperature=temperature,
        max_tokens=max_tokens,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LMStudioClient",
    "chat_with_coding_model",
]
