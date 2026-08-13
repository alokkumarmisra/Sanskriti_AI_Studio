"""LM Studio Manager API routes."""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException

from app.api.lmstudio.service import LMStudioManager


# Define available agent types for reference (existing infrastructure)
AGENT_TYPES = [
    {"id": "planner_agent", "name": "Planner Agent"},
    {"id": "coder_agent", "name": "Coding Agent"},
    {"id": "tester_agent", "name": "Testing Agent"},
    {"id": "documentation_agent", "name": "Documentation Agent"},
    {"id": "reviewer_agent", "name": "Reviewer Agent"},
    {"id": "debugger_agent", "name": "Debugging Agent"},
    {"id": "vision_agent", "name": "Vision Agent"},
    {"id": "browser_runtime", "name": "Browser Runtime"},
    {"id": "screenshot_service", "name": "Screenshot Service"},
]


router = APIRouter(prefix="/api/v1/dashboard/lmstudio", tags=["LM Studio Manager"])


def _get_agent_state(agent_id: str) -> Optional[Dict[str, Any]]:
    """Load agent state from state files."""
    # Placeholder - integrates with existing agent state system
    state_path = f"ai_agents/state/{agent_id.replace('-', '_')}/current_state.json"
    
    if not os.path.exists(state_path):
        return None
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _get_orchestrator_logs() -> str:
    """Get orchestrator logs for LM Studio events."""
    log_path = "ai_agents/logs/orchestrator/execution.log"
    
    if not os.path.exists(log_path):
        return ""
    
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Filter for LM Studio related logs only
        lmstudio_lines = []
        for line in content.split("\n"):
            if "lmstudio" in line.lower() or "lm_studio" in line.lower():
                lmstudio_lines.append(line)
        
        return "\n".join(lmstudio_lines[:100])  # Limit to last 100 lines


def _safe_get_status(state: Dict[str, Any], key: str) -> Optional[str]:
    """Safely get status from state dict."""
    if not state:
        return None
    value = state.get(key)
    if isinstance(value, str):
        return value
    return None


def _safe_get_str(state: Dict[str, Any], key: str, default: str = "") -> str:
    """Safely get string value from state dict."""
    if not state:
        return default
    value = state.get(key)
    if isinstance(value, str):
        return value
    return default


def _safe_get_int(state: Dict[str, Any], key: str, default: int = 0) -> int:
    """Safely get integer value from state dict."""
    if not state:
        return default
    value = state.get(key)
    if isinstance(value, int):
        return value
    return default


@router.get("/status", response_model=Dict[str, Any])
async def get_lmstudio_status():
    """Get LM Studio server status and health information."""
    
    lmstudio_manager = LMStudioManager()
    
    try:
        # Check connection
        is_connected = lmstudio_manager.is_connected()
        
        if not is_connected:
            return {
                "success": True,
                "server_status": "disconnected",
                "server_url": lmstudio_manager.get_server_url(),
                "text_model": None,
                "vision_model": None,
                "response_time_ms": None,
                "last_health_check": None,
                "error_message": None,
            }
        
        # Get health metrics
        response_time = lmstudio_manager.get_response_time()
        last_health_check = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": True,
            "server_status": "connected",
            "server_url": lmstudio_manager.get_server_url(),
            "text_model": lmstudio_manager.text_model,
            "vision_model": lmstudio_manager.vision_model,
            "response_time_ms": response_time,
            "last_health_check": last_health_check,
            "error_message": None,
        }
    
    except Exception as e:
        return {
            "success": True,
            "server_status": "unavailable",
            "server_url": lmstudio_manager.get_server_url(),
            "text_model": None,
            "vision_model": None,
            "response_time_ms": None,
            "last_health_check": datetime.now(timezone.utc).isoformat(),
            "error_message": f"Server unavailable: {str(e)}",
        }


@router.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """Get list of all available models from LM Studio."""
    
    lmstudio_manager = LMStudioManager()
    
    try:
        models_data = lmstudio_manager.list_models()
        
        if not models_data:
            return {
                "success": True,
                "models": [],
                "count": 0,
            }
        
        formatted_models = []
        for model in models_data:
            # Classify model type (TEXT/VISION/MULTIMODAL/UNKNOWN)
            classification = "UNKNOWN"
            
            model_name_lower = str(model.get("name", "")).lower() if isinstance(model, dict) else ""
            
            # Check for vision capabilities
            if isinstance(model, dict):
                details = model.get("details", {}) or {}
                
                # Vision model indicators
                if any(term in model_name_lower for term in [
                    "vision", "vl", "multimodal", "llava", "qwen-vl"
                ]):
                    classification = "VISION"
                elif any(term in str(details).lower() for term in [
                    "vision", "multimodal"
                ]):
                    classification = "MULTIMODAL"
            
            # Handle size_gb calculation safely (fix: avoid division by None)
            size_value = model.get("size") if isinstance(model, dict) else None
            size_gb = (size_value / 1073741824.0) if size_value is not None else None
            
            formatted_models.append({
                "name": model.get("name") or model.get("id") or "",
                "id": model.get("id") or "",
                "type": model.get("type", ""),
                "size_gb": size_gb,
                "format": model.get("format", "") if isinstance(model, dict) else None,
                "quantization": model.get("quantization", "") if isinstance(model, dict) else None,
                "organization": model.get("organization") or model.get("owned_by") or "",
                "classification": classification,
            })
        
        return {
            "success": True,
            "models": formatted_models,
            "count": len(formatted_models),
        }
    
    except Exception as e:
        return {
            "success": True,
            "models": [],
            "count": 0,
            "error_message": f"Failed to list models: {str(e)}",
        }


@router.get("/loaded", response_model=Dict[str, Any])
async def get_loaded_models():
    """Get information about currently loaded models."""
    
    lmstudio_manager = LMStudioManager()
    
    try:
        loaded_info = lmstudio_manager.get_loaded_models_info()
        
        return {
            "success": True,
            "loaded_models": loaded_info,
            "count": len(loaded_info),
        }
    
    except Exception as e:
        return {
            "success": True,
            "loaded_models": [],
            "count": 0,
            "error_message": f"Failed to get loaded models info: {str(e)}",
        }


@router.post("/test/text")
async def test_text_model(payload: Dict[str, str]):
    """Test text model with a simple prompt."""
    
    lmstudio_manager = LMStudioManager()
    base_url = payload.get("url", lmstudio_manager.get_server_url())
    model = payload.get("model") or lmstudio_manager.get_coding_model()
    
    if not model:
        return {
            "success": False,
            "status": "error",
            "response": None,
            "response_time_ms": None,
            "error_message": "Text model not configured. Set LM_STUDIO_CODING_MODEL environment variable.",
        }
    
    try:
        # Check connection first
        if not lmstudio_manager.is_connected():
            return {
                "success": False,
                "status": "disconnected",
                "response": None,
                "response_time_ms": None,
                "error_message": f"LM Studio server not connected at {base_url}",
            }
        
        # Send text-only prompt (never send images to Qwen 3.5)
        test_prompt = payload.get("prompt", "Hello! This is a text-only test prompt.")
        
        result = lmstudio_manager.generate_text(model=model, messages=[
            {
                "role": "system",
                "content": "You are the text model for Sanskriti AI Studio.",
            },
            {"role": "user", "content": test_prompt},
        ])
        
        response_time = lmstudio_manager.get_response_time()
        
        return {
            "success": True,
            "status": "success",
            "model": model,
            "response": result.get("choices", [{}])[0].get("message", {}).get("content", "") if result else "",
            "response_time_ms": response_time,
            "error_message": None,
        }
    
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "response": None,
            "response_time_ms": None,
            "error_message": f"Text model test failed: {str(e)}",
        }


@router.post("/test/vision")
async def test_vision_model(payload: Dict[str, Any]):
    """Test vision model with image and prompt."""
    
    lmstudio_manager = LMStudioManager()
    base_url = payload.get("url", lmstudio_manager.get_server_url())
    model = payload.get("model") or lmstudio_manager.get_vision_model()
    
    if not model:
        return {
            "success": False,
            "status": "error",
            "response": None,
            "response_time_ms": None,
            "error_message": "Vision model not configured. Set LM_STUDIO_VISION_MODEL environment variable.",
        }
    
    try:
        # Check connection first
        if not lmstudio_manager.is_connected():
            return {
                "success": False,
                "status": "disconnected",
                "response": None,
                "response_time_ms": None,
                "error_message": f"LM Studio server not connected at {base_url}",
            }
        
        # Get or create test image
        image_path = payload.get("image")
        
        if not image_path:
            # Use default test image path
            image_path = "ai_agents/screenshots/test_ui_0.png"
            
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "status": "error",
                    "response": None,
                    "response_time_ms": None,
                    "error_message": f"Test image not found: {image_path}",
                }
        
        # Send vision + text prompt to vision model (Qwen-VL for visual analysis)
        test_prompt = payload.get("prompt", "Analyze this UI screenshot.")
        
        result = lmstudio_manager.generate_vision(
            model=model,
            image_path=image_path,
            messages=[
                {
                    "role": "system",
                    "content": f"You are the vision model for Sanskriti AI Studio. Analyze visual inputs.",
                },
                {"role": "user", "content": test_prompt},
            ],
        )
        
        response_time = lmstudio_manager.get_response_time()
        
        return {
            "success": True,
            "status": "success",
            "model": model,
            "response": result.get("choices", [{}])[0].get("message", {}).get("content", "") if result else "",
            "response_time_ms": response_time,
            "error_message": None,
        }
    
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "response": None,
            "response_time_ms": None,
            "error_message": f"Vision model test failed: {str(e)}",
        }


@router.get("/logs")
async def get_lmstudio_logs(
    limit: int = 100,
    filter_level: Optional[str] = None,
):
    """Get LM Studio-related log entries."""
    
    raw_logs = _get_orchestrator_logs()
    
    if not raw_logs:
        return {
            "agent": "lmstudio_manager",
            "logs": [],
            "count": 0,
            "path": "ai_agents/logs/orchestrator/execution.log",
        }
    
    filtered_lines = []
    for line in raw_logs.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if filter_level and filter_level.upper() != "ALL":
            if f"[{filter_level.upper()}]" not in line:
                continue
        
        filtered_lines.append(line)
    
    return {
        "agent": "lmstudio_manager",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/orchestrator/execution.log",
    }
