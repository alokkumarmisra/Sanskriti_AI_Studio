"""Unified Model Management Service for Sanskriti AI Studio."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

# From workspace root: backend/app/api/models/
# Need to go up two levels to reach backend/app/, then into api/lmstudio/
from backend.app.api.lmstudio.service import LMStudioManager  # type: ignore[import-not-found]
from backend.app.api.comfyui.service_final import ComfyUIManager  # type: ignore[import-not-found]


class UnifiedModelManager:
    """
    Unified manager for AI model inventory across LM Studio and ComfyUI.
    
    This service provides a centralized view of all models used by the platform,
    including text models, vision models, generation models, and resource information.
    
    IMPORTANT: Qwen 3.5 is TEXT-ONLY - never send images to this model.
    Use the configured vision model for visual analysis tasks.
    """

    # Model type classifications
    MODEL_TYPES = [
        "TEXT",
        "VISION",
        "MULTIMODAL",
        "IMAGE_GENERATION",
        "VIDEO_GENERATION",
        "UPSCALE",
        "EMBEDDING",
        "CONTROLNET",
        "LORA",
        "VAE",
        "CHECKPOINT",
        "UNKNOWN"
    ]

    # Status values
    STATUS_AVAILABLE = "available"
    STATUS_LOADED = "loaded"
    STATUS_UNAVAILABLE = "unavailable"

    # Health status values
    HEALTH_HEALTHY = "healthy"
    HEALTH_ERROR = "error"
    HEALTH_UNKNOWN = "unknown"

    def __init__(self):
        """Initialize unified model manager with configuration from environment."""
        self._lmstudio_manager = LMStudioManager()
        self._comfyui_manager = ComfyUIManager()
        
        # Connection state
        self._lmstudio_connected: bool = False
        self._comfyui_connected: bool = False
        
        # Resource awareness - Primary GPU info (RTX 3060 12GB)
        self._gpu_name: str = "NVIDIA RTX 3060"
        self._total_vram_gb: float = 12.0

    def set_lmstudio_url(self, url: str) -> None:
        """Set custom LM Studio base URL."""
        self._lmstudio_manager.set_base_url(url)

    def set_comfyui_url(self, url: str) -> None:
        """Set custom ComfyUI base URL."""
        self._comfyui_manager.set_base_url(url)

    @property
    def lmstudio_connected(self) -> bool:
        """Check if LM Studio server is reachable."""
        return self._lmstudio_connected

    @property
    def comfyui_connected(self) -> bool:
        """Check if ComfyUI server is reachable."""
        return self._comfyui_connected

    def check_connection(self) -> Dict[str, Any]:
        """Check connection status for both servers."""
        lmconnected = self._lmstudio_manager.is_connected()
        comfyconnected = self._comfyui_manager.is_connected()
        
        return {
            "lmstudio": {
                "connected": lmconnected,
                "url": self._lmstudio_manager.get_server_url(),
                "text_model": self._lmstudio_manager.text_model,
                "vision_model": self._lmstudio_manager.vision_model,
            },
            "comfyui": {
                "connected": comfyconnected,
                "url": self._comfyui_manager.server_url,
            },
            "both_connected": lmconnected and comfyconnected,
        }

    def get_resource_info(self) -> Dict[str, Any]:
        """Get GPU resource information."""
        # Get VRAM info from ComfyUI if available
        comfy_stats = self._comfyui_manager.get_system_stats()
        
        vram_info = {
            "gpu_name": self._gpu_name,
            "total_vram_gb": self._total_vram_gb,
            "vram_used_gb": 0.0,
            "vram_available_gb": self._total_vram_gb,
            "utilization_percent": 0,
        }
        
        if comfy_stats.get("success") and comfy_stats.get("gpu_info"):
            gpu_info = comfy_stats["gpu_info"]
            vram_mb = gpu_info.get("vram_total_mb") or self._total_vram_gb * 1024
            used_mb = gpu_info.get("vram_used_mb") or 0
            available_mb = gpu_info.get("vram_available_mb") or (vram_mb - used_mb)
            
            vram_info.update({
                "gpu_name": gpu_info.get("name", self._gpu_name),
                "total_vram_gb": round((vram_mb / 1024), 2),
                "vram_used_gb": round((used_mb / 1024), 2),
                "vram_available_gb": round((available_mb / 1024), 2),
                "utilization_percent": gpu_info.get("utilization_percent") or 0,
            })
        
        return vram_info

    def get_compatibility_check(self, model_size_mb: Optional[float], 
                                model_vram_required_gb: Optional[float]) -> str:
        """
        Check VRAM compatibility for a model.
        
        Returns one of: LIKELY SAFE, HIGH VRAM USAGE, POSSIBLE VRAM LIMIT, UNKNOWN
        """
        if model_vram_required_gb is None or model_vram_required_gb == 0:
            return "UNKNOWN"
        
        total_vram = self._total_vram_gb
        used_vram = self.get_resource_info()["vram_used_gb"]
        available_vram = total_vram - used_vram
        
        # Estimate VRAM usage based on model size (rough heuristic)
        estimated_usage_gb = model_size_mb / 1024 / 1024 * 1.5 if model_size_mb else None
        
        if estimated_usage_gb is None:
            return "UNKNOWN"
        
        if estimated_usage_gb < available_vram * 0.7:
            return "LIKELY SAFE"
        elif estimated_usage_gb < total_vram * 0.9:
            return "HIGH VRAM USAGE"
        else:
            return "POSSIBLE VRAM LIMIT"

    def get_unified_inventory(self, 
                              limit: Optional[int] = None,
                              filter_status: Optional[str] = None) -> Dict[str, Any]:
        """Get unified inventory of all models from both services."""
        
        lm_models = []
        comfy_models = []
        
        # Get LM Studio models
        try:
            if self._lmstudio_connected:
                models_data = self._lmstudio_manager.list_models()
                for model in models_data:
                    # Classify model type (TEXT/VISION/MULTIMODAL/UNKNOWN)
                    classification = self._classify_lmstudio_model(model)
                    
                    lm_models.append({
                        "id": model.get("id") or "",
                        "name": model.get("name") or model.get("id") or "",
                        "type": model.get("type") or "",
                        "classification": classification,
                        "size_gb": None,
                        "organization": model.get("organization") or model.get("owned_by") or "",
                        "format": model.get("format"),
                        "quantization": model.get("quantization"),
                        "source": "lmstudio",
                        "application": "LM Studio",
                    })
        except Exception as e:
            print(f"Failed to list LM Studio models: {e}")
        
        # Get ComfyUI model types (checkpoints, LoRAs, etc.)
        try:
            if self._comfyui_connected:
                comfy_models.extend(self._get_comfyui_model_types())
        except Exception as e:
            print(f"Failed to list ComfyUI models: {e}")
        
        # Combine and filter
        all_models = lm_models + comfy_models
        
        # Apply status filter if provided
        if filter_status:
            filtered = [m for m in all_models if m.get("status") == filter_status]
            all_models = filtered
        
        return {
            "success": True,
            "models": all_models,
            "count": len(all_models),
            "lmstudio_count": len(lm_models),
            "comfyui_count": len(comfy_models),
            "total_count": len(all_models),
        }

    def _classify_lmstudio_model(self, model: Dict[str, Any]) -> str:
        """Classify LM Studio model type (TEXT/VISION/MULTIMODAL/UNKNOWN)."""
        model_id = model.get("id", "") or ""
        model_name = model.get("name", "") or ""
        
        # Combine id and name for classification
        full_name = f"{model_id} {model_name}".lower()
        
        # Vision model indicators (Qwen 3.5 rule: keep as TEXT unless proven otherwise)
        vision_keywords = ["vision", "vl", "multimodal", "llava", "qwen-vl"]
        
        if any(kw in full_name for kw in vision_keywords):
            return "VISION"
        
        # Default to TEXT for safety (Qwen 3.5 rule)
        return "TEXT"

    def _get_comfyui_model_types(self) -> List[Dict[str, Any]]:
        """Get model type counts from ComfyUI (simulated based on common types)."""
        # ComfyUI typically stores models in specific directories
        # We'll provide a unified view of what's available
        
        return [
            {
                "id": "checkpoints",
                "name": "Checkpoints",
                "type": "CHECKPOINT",
                "classification": "IMAGE_GENERATION",
                "source": "comfyui",
                "application": "ComfyUI",
                "status": "available",
                "capabilities": ["Text-to-Image", "Image-to-Image", "Inpainting"],
            },
            {
                "id": "loras",
                "name": "LoRA Adapters",
                "type": "LORA",
                "classification": "UNKNOWN",
                "source": "comfyui",
                "application": "ComfyUI",
                "status": "available",
                "capabilities": ["Model Fine-tuning", "Style Transfer"],
            },
            {
                "id": "vae",
                "name": "VAE Models",
                "type": "VAE",
                "classification": "UNKNOWN",
                "source": "comfyui",
                "application": "ComfyUI",
                "status": "available",
                "capabilities": ["Latent Space Decoding"],
            },
            {
                "id": "controlnet",
                "name": "ControlNet Models",
                "type": "CONTROLNET",
                "classification": "UNKNOWN",
                "source": "comfyui",
                "application": "ComfyUI",
                "status": "available",
                "capabilities": ["Edge Control", "Pose Control", "Depth Control"],
            },
            {
                "id": "upscale",
                "name": "Upscale Models",
                "type": "UPSCALE",
                "classification": "UNKNOWN",
                "source": "comfyui",
                "application": "ComfyUI",
                "status": "available",
                "capabilities": ["4x Upscaling", "Real-ESRGAN"],
            },
        ]

    def get_text_models(self) -> List[Dict[str, Any]]:
        """Get list of text models from LM Studio."""
        all_models = self.get_unified_inventory()
        return [m for m in all_models["models"] 
                if m.get("classification") == "TEXT" or m.get("source") == "lmstudio"]

    def get_vision_models(self) -> List[Dict[str, Any]]:
        """Get list of vision models from LM Studio."""
        all_models = self.get_unified_inventory()
        return [m for m in all_models["models"] 
                if m.get("classification") == "VISION" or "vision" in m.get("name", "").lower()]

    def get_generation_models(self) -> List[Dict[str, Any]]:
        """Get generation models from ComfyUI."""
        all_models = self.get_unified_inventory()
        return [m for m in all_models["models"] 
                if m.get("classification") == "IMAGE_GENERATION" or 
                   m.get("type") == "CHECKPOINT"]

    def get_loaded_models(self) -> List[Dict[str, Any]]:
        """Get list of currently loaded models from LM Studio."""
        try:
            if self._lmstudio_connected:
                loaded_info = self._lmstudio_manager.get_loaded_models_info()
                models = loaded_info.get("data", [])
                
                loaded = []
                for model in models:
                    classification = self._classify_lmstudio_model(model)
                    
                    loaded.append({
                        "id": model.get("id") or "",
                        "name": model.get("name") or model.get("id") or "",
                        "type": model.get("type") or "",
                        "classification": classification,
                        "size_gb": None,
                        "organization": model.get("organization") or "",
                        "source": "lmstudio",
                        "application": "LM Studio",
                        "status": self.STATUS_LOADED,
                    })
                
                return loaded
        except Exception as e:
            print(f"Failed to get loaded models: {e}")
        
        return []

    def get_model_details(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        all_models = self.get_unified_inventory()
        
        for model in all_models["models"]:
            if model.get("id") == model_id or model.get("name").lower() == model_id.lower():
                return {
                    **model,
                    "details": self._get_model_specific_details(model),
                }
        
        return None

    def _get_model_specific_details(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Get additional details for a specific model."""
        return {
            "location": "LM Studio / ComfyUI",
            "last_used": datetime.now(timezone.utc).isoformat(),
            "compatible_with": [
                "Text Generation",
                "Image Generation", 
                "Vision Analysis"
            ],
        }

    def search_models(self, query: str, 
                      limit: int = 50) -> Dict[str, Any]:
        """Search models by name, type, or capability."""
        all_models = self.get_unified_inventory()
        
        query_lower = query.lower()
        filtered = []
        
        for model in all_models["models"]:
            searchable_fields = [
                model.get("name", ""),
                model.get("id", ""),
                model.get("type", ""),
                model.get("classification", ""),
                " ".join(model.get("capabilities", [])).lower(),
            ]
            
            if any(query_lower in field for field in searchable_fields):
                filtered.append(model)
        
        return {
            "success": True,
            "query": query,
            "models": filtered,
            "count": len(filtered),
            "total_available": all_models["count"],
        }

    def filter_models(self, 
                      model_type: Optional[str] = None,
                      application: Optional[str] = None,
                      status: Optional[str] = None) -> Dict[str, Any]:
        """Filter models by type, application, or status."""
        all_models = self.get_unified_inventory()
        
        filtered = all_models["models"]
        
        if model_type and model_type in self.MODEL_TYPES:
            filtered = [m for m in filtered 
                        if m.get("classification") == model_type or 
                           m.get("type") == model_type]
        
        if application:
            filtered = [m for m in filtered 
                        if m.get("application") == application]
        
        if status:
            filtered = [m for m in filtered 
                        if m.get("status") == status]
        
        return {
            "success": True,
            "filters": {
                "model_type": model_type,
                "application": application,
                "status": status,
            },
            "models": filtered,
            "count": len(filtered),
            "total_available": all_models["count"],
        }

    def get_model_health(self) -> Dict[str, Any]:
        """Get health status of all models."""
        health_checks = {
            "lmstudio_server": self._lmstudio_manager.is_connected(),
            "comfyui_server": self._comfyui_manager.is_connected(),
            "models_healthy": True,  # No expensive checks - assume healthy unless errors reported
        }
        
        return {
            "success": True,
            "checks": health_checks,
            "overall_status": "healthy" if all(health_checks.values()) else "unhealthy",
        }

    def get_routing_view(self) -> Dict[str, Any]:
        """Display how models are currently used."""
        text_model = self._lmstudio_manager.text_model
        vision_model = self._lmstudio_manager.vision_model
        
        return {
            "success": True,
            "routing": [
                {
                    "request_type": "TEXT",
                    "step1": "Model Router",
                    "step2": text_model or "Qwen 3.5 (default)",
                    "application": "Text Generation / Coding",
                },
                {
                    "request_type": "VISION",
                    "step1": "Model Router",
                    "step2": vision_model or "Qwen-VL (default)",
                    "application": "Visual Analysis / UI Screenshots",
                },
                {
                    "request_type": "IMAGE_GENERATION",
                    "step1": "Model Router",
                    "step2": "ComfyUI Checkpoints",
                    "application": "Image Generation Workflows",
                },
            ],
        }

    def refresh(self) -> Dict[str, Any]:
        """Refresh model inventory and connection status."""
        try:
            lmconnected = self._lmstudio_manager.is_connected()
            comfyconnected = self._comfyui_manager.is_connected()
            
            return {
                "success": True,
                "lmstudio_connected": lmconnected,
                "comfyui_connected": comfyconnected,
                "refreshed_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
            }
