"""Unified Model Management API routes for Sanskriti AI Studio."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any

from app.api.models.unified import UnifiedModelManager


# Initialize unified model manager
unified_manager = UnifiedModelManager()


router = APIRouter(prefix="/api/v1/models", tags=["Model Management"])


@router.get("/inventory", response_model=Dict[str, Any])
async def get_model_inventory(
    limit: Optional[int] = Query(None, description="Limit number of models to return"),
    filter_status: Optional[str] = Query(None, description="Filter by status (available, loaded)"),
):
    """
    Get unified inventory of all AI models from LM Studio and ComfyUI.
    
    Returns a comprehensive list of all available models with their types,
    classifications, sizes, and source applications.
    """
    
    try:
        result = unified_manager.get_unified_inventory(
            limit=limit,
            filter_status=filter_status,
        )
        
        return {
            "success": True,
            **result,
            "resource_info": unified_manager.get_resource_info(),
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get model inventory: {str(e)}",
        }


@router.get("/text", response_model=Dict[str, Any])
async def get_text_models():
    """Get list of text models suitable for language tasks."""
    
    try:
        text_models = unified_manager.get_text_models()
        
        return {
            "success": True,
            "models": text_models,
            "count": len(text_models),
            "description": "Text-only models (Qwen 3.5, etc.)",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get text models: {str(e)}",
        }


@router.get("/vision", response_model=Dict[str, Any])
async def get_vision_models():
    """Get list of vision models capable of image analysis."""
    
    try:
        vision_models = unified_manager.get_vision_models()
        
        return {
            "success": True,
            "models": vision_models,
            "count": len(vision_models),
            "description": "Vision-capable models (Qwen-VL, etc.)",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get vision models: {str(e)}",
        }


@router.get("/loaded", response_model=Dict[str, Any])
async def get_loaded_models():
    """Get list of currently loaded models in memory."""
    
    try:
        loaded_models = unified_manager.get_loaded_models()
        
        return {
            "success": True,
            "models": loaded_models,
            "count": len(loaded_models),
            "description": "Models currently loaded into GPU memory",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get loaded models: {str(e)}",
        }


@router.get("/generation", response_model=Dict[str, Any])
async def get_generation_models():
    """Get list of image generation models from ComfyUI."""
    
    try:
        gen_models = unified_manager.get_generation_models()
        
        return {
            "success": True,
            "models": gen_models,
            "count": len(gen_models),
            "description": "Image generation checkpoints (ComfyUI)",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get generation models: {str(e)}",
        }


@router.get("/details/{model_id}", response_model=Dict[str, Any])
async def get_model_details(model_id: str):
    """
    Get detailed information about a specific model.
    
    Accepts either the model ID or name as parameter.
    """
    
    try:
        details = unified_manager.get_model_details(model_id)
        
        if not details:
            return {
                "success": False,
                "error_message": f"Model '{model_id}' not found",
            }
        
        return {
            "success": True,
            **details,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get model details: {str(e)}",
        }


@router.get("/search")
async def search_models(
    query: str = Query(..., description="Search query (name, type, capability)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
):
    """Search models by name, type, or capability."""
    
    try:
        result = unified_manager.search_models(query=query, limit=limit)
        
        return {
            "success": True,
            **result,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Search failed: {str(e)}",
        }


@router.get("/filter")
async def filter_models(
    model_type: Optional[str] = Query(None, description="Filter by type (TEXT, VISION, etc.)"),
    application: Optional[str] = Query(None, description="Filter by application (LM Studio, ComfyUI)"),
    status: Optional[str] = Query(None, description="Filter by status (available, loaded, unavailable)"),
):
    """Filter models by type, application, or status."""
    
    try:
        result = unified_manager.filter_models(
            model_type=model_type,
            application=application,
            status=status,
        )
        
        return {
            "success": True,
            **result,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Filter failed: {str(e)}",
        }


@router.get("/health")
async def get_model_health():
    """Get health status of model servers."""
    
    try:
        health = unified_manager.get_model_health()
        
        return {
            "success": True,
            **health,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Health check failed: {str(e)}",
        }


@router.get("/routing")
async def get_routing_view():
    """Display how models are currently routed for different request types."""
    
    try:
        routing = unified_manager.get_routing_view()
        
        return {
            "success": True,
            **routing,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get routing view: {str(e)}",
        }


@router.get("/resource")
async def get_resource_info():
    """Get GPU resource information and compatibility checks."""
    
    try:
        resource = unified_manager.get_resource_info()
        
        return {
            "success": True,
            **resource,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Failed to get resource info: {str(e)}",
        }


@router.post("/test/text")
async def test_text_model(payload: Dict[str, str]):
    """Test a text model with a simple prompt."""
    
    try:
        # Check connection first
        if not unified_manager.lmstudio_connected:
            return {
                "success": False,
                "status": "disconnected",
                "response": None,
                "error_message": "LM Studio server not connected",
            }
        
        # Get configured text model
        model = unified_manager._lmstudio_manager.text_model
        
        if not model:
            return {
                "success": False,
                "status": "not_configured",
                "response": None,
                "error_message": "Text model not configured. Set LM_STUDIO_CODING_MODEL.",
            }
        
        # Send test prompt
        test_prompt = payload.get("prompt", "This is a text-only test prompt. Please confirm you received this.")
        
        result = unified_manager._lmstudio_manager.generate_text(
            model=model,
            messages=[
                {"role": "system", "content": "You are the text model for Sanskriti AI Studio."},
                {"role": "user", "content": test_prompt},
            ],
        )
        
        response_time = unified_manager._lmstudio_manager.get_response_time()
        
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
            "error_message": f"Text model test failed: {str(e)}",
        }


@router.post("/test/vision")
async def test_vision_model(payload: Dict[str, Any]):
    """Test a vision model with an image and prompt."""
    
    try:
        # Check connection first
        if not unified_manager.lmstudio_connected:
            return {
                "success": False,
                "status": "disconnected",
                "response": None,
                "error_message": "LM Studio server not connected",
            }
        
        # Get configured vision model
        model = unified_manager._lmstudio_manager.vision_model
        
        if not model:
            return {
                "success": False,
                "status": "not_configured",
                "response": None,
                "error_message": "Vision model not configured. Set LM_STUDIO_VISION_MODEL.",
            }
        
        # Get image path
        image_path = payload.get("image")
        
        if not image_path:
            # Use default test image path
            image_path = "ai_agents/screenshots/test_ui_0.png"
            
            import os
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "status": "image_not_found",
                    "response": None,
                    "error_message": f"Test image not found: {image_path}",
                }
        
        # Send vision prompt
        test_prompt = payload.get("prompt", "Analyze this UI screenshot and describe what you see.")
        
        result = unified_manager._lmstudio_manager.generate_vision(
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
        
        response_time = unified_manager._lmstudio_manager.get_response_time()
        
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
            "error_message": f"Vision model test failed: {str(e)}",
        }


@router.post("/refresh")
async def refresh_models():
    """Refresh model inventory and connection status."""
    
    try:
        result = unified_manager.refresh()
        
        return {
            "success": result.get("success", False),
            **result,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Refresh failed: {str(e)}",
        }
