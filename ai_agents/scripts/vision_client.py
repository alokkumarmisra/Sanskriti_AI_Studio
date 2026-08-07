"""
LM Studio Vision Client for Sanskriti AI Studio.

This module provides a client for LM Studio's vision model API (Qwen2.5-VL).
It supports image inputs for visual analysis tasks including:
- UI screenshot understanding
- OCR text extraction
- Component detection
- Layout analysis
- Error message extraction
- Visual regression testing

IMPORTANT: Qwen 3.5 is TEXT-ONLY. This client should ONLY be used with the 
vision model (Qwen2.5-VL) for image processing tasks.
"""

import os
import base64
import requests
from typing import Any, Dict, List, Optional


class LMStudioVisionClient:
    """Synchronous client for LM Studio vision/chat completions API."""

    def __init__(self, model_name: str = "", base_url: str = "http://localhost:1234") -> None:
        """
        Initialize the Vision Client.

        Args:
            model_name: Name of the vision model (e.g., qwen/Qwen2.5-VL-8B)
            base_url: Base URL for LM Studio API (default: http://localhost:1234)
        """
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")

    @property
    def model_name(self) -> str:
        return self._model_name

    @model_name.setter
    def model_name(self, value: str) -> None:
        self._model_name = value

    @property
    def base_url(self) -> str:
        return self._base_url.rstrip("/")

    @base_url.setter
    def base_url(self, value: str) -> None:
        self._base_url = value.rstrip("/") + "/v1"

    def _prepare_image_base64(
        self, image_path: str, format_type: str = "png"
    ) -> Dict[str, Any]:
        """
        Load and encode an image to base64 for API submission.

        Args:
            image_path: Path to the image file
            format_type: Image format (png, jpg, webp)

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
                "url": f"data:{format_type};base64,{base64.b64encode(image_data).decode('utf-8')}"
            },
        }

    def _prepare_image_url(self, image_url: str) -> Dict[str, Any]:
        """
        Prepare an external image URL for API submission.

        Args:
            image_url: URL to the image

        Returns:
            Dictionary with image URL reference
        """
        return {
            "type": "image_url",
            "image_url": {"url": image_url},
        }

    def chat_with_vision_model(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        top_p: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Send a chat request to LM Studio with vision model.

        Args:
            messages: List of message dictionaries (can include image inputs)
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter

        Returns:
            API response dictionary

        Raises:
            Exception: If the request fails or model returns an error
        """
        if not self._model_name:
            raise ValueError(
                "Vision model name not set. Please call set_model_name() first."
            )

        # Validate messages - check for image data
        content_items = []
        text_parts: List[str] = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content")

            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "image_url":
                            # Extract image URL (base64 or external)
                            image_data = item.get("image_url", {}).get("url", "")
                            if image_data.startswith("data:"):
                                content_items.append({"type": "image"})
                            else:
                                content_items.append(image_data)
                        elif item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                    elif isinstance(item, str):
                        # Direct image path or URL
                        if os.path.exists(item):
                            encoded = self._prepare_image_base64(item)
                            content_items.append({"type": "image"})
                        else:
                            content_items.append(item)
                        text_parts.append("")
            elif isinstance(content, str):
                text_parts.append(content)

        # Build combined content if we have both text and images
        if content_items or text_parts:
            final_content = []
            if content_items:
                final_content.extend([{"type": "image"} for _ in content_items])
            if text_parts:
                final_content.append({"type": "text", "text": "\n".join(text_parts)})

            messages[0]["content"] = final_content  # Ensure at least one message has content

        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            error_msg = result["error"].get("message", str(result["error"]))
            raise Exception(f"LM Studio vision API error: {error_msg}")

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

    def chat_with_vision_model_from_image(
        self,
        image_path: str,
        prompt: str,
        format_type: str = "png",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        top_p: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Convenience method to send a prompt with an image to the vision model.

        Args:
            image_path: Path to the image file
            prompt: Text prompt for analysis
            format_type: Image format (png, jpg, webp)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            top_p: Nucleus sampling parameter

        Returns:
            API response dictionary
        """
        # Build messages with image and text
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},  # Image marker (actual image will be added)
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Replace image marker with actual base64-encoded image
        messages[0]["content"][0] = self._prepare_image_base64(
            image_path, format_type=format_type
        )

        return self.chat_with_vision_model(messages, temperature, max_tokens, top_p)

    def health_check(self) -> Dict[str, Any]:
        """
        Check if LM Studio vision endpoint is available.

        Returns:
            Dictionary with health check results
        """
        url = f"{self._base_url}/models"
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

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured vision model.

        Returns:
            Model information dictionary or None if not found
        """
        if not self._model_name:
            return None

        url = f"{self._base_url}/models"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            models = response.json()
            for model in models.get("data", []):
                if self._model_name.lower() in model.get("id", "").lower():
                    return {
                        "id": model.get("id"),
                        "object": model.get("object"),
                        "created": model.get("created"),
                        "owned_by": model.get("owned_by"),
                        "size": model.get("size"),
                        "format": model.get("format"),
                    }
        return None


def chat_with_vision_model(
    messages: List[Dict[str, Any]],
    base_url: str = "http://localhost:1234",
    model_name: str = "",
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    Convenience function to send a chat request to LM Studio vision model.

    Args:
        messages: List of message dictionaries (can include image inputs)
        base_url: Base URL for LM Studio API
        model_name: Name of the vision model
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        API response dictionary

    Raises:
        Exception: If the request fails or model returns an error
    """
    client = LMStudioVisionClient(model_name=model_name, base_url=base_url)
    return client.chat_with_vision_model(messages, temperature, max_tokens)


def chat_with_vision_model_from_image(
    image_path: str,
    prompt: str,
    base_url: str = "http://localhost:1234",
    model_name: str = "",
    format_type: str = "png",
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    Convenience function to send a prompt with an image to the vision model.

    Args:
        image_path: Path to the image file
        prompt: Text prompt for analysis
        base_url: Base URL for LM Studio API
        model_name: Name of the vision model
        format_type: Image format
        temperature: Sampling temperature
        max_tokens: Maximum tokens

    Returns:
        API response dictionary
    """
    client = LMStudioVisionClient(model_name=model_name, base_url=base_url)
    return client.chat_with_vision_model_from_image(
        image_path, prompt, format_type, temperature, max_tokens
    )


# Export main classes and functions
__all__ = [
    "LMStudioVisionClient",
    "chat_with_vision_model",
    "chat_with_vision_model_from_image",
]
