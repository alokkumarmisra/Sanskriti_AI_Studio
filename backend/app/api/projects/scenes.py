"""API routes for Scenes, Characters, and Locations in Content & Scene Planning Workspace."""

from uuid import UUID
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, status

from app.services.scenes_service import ScenesService
from app.models.scenes import (
    SceneReadResponse, SceneCreateResponse, 
    CharacterReadResponse, LocationReadResponse
)


router = APIRouter(prefix="/projects", tags=["Content & Scene Planning"])

# Global scenes service instance - will be injected by the application with the database session
scenes_service: ScenesService


# ============================================
# SCENE ENDPOINTS
# ============================================

@router.get("/{project_id}/content/scenes")
def list_scenes(project_id: UUID) -> List[SceneReadResponse]:  # type: ignore
    """Retrieve all scenes for a project."""
    scenes = scenes_service.get_all_scenes(str(project_id))
    return [SceneReadResponse.model_validate(s) for s in scenes]


@router.post("/{project_id}/content/scenes", response_model=SceneCreateResponse)
def create_scene(
    project_id: UUID, 
    scene_data: dict
) -> SceneCreateResponse:  # type: ignore
    """Create a new scene for a project."""
    created = scenes_service.create_scene(str(project_id), scene_data)
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create scene")
    return SceneCreateResponse.model_validate(created)


@router.put("/content/scenes/{scene_id}", response_model=SceneReadResponse)
def update_scene(
    scene_id: str,
    project_id: UUID,
    scene_data: dict
) -> SceneReadResponse:  # type: ignore
    """Update an existing scene."""
    updated = scenes_service.update_scene(scene_id, str(project_id), scene_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Scene not found")
    return SceneReadResponse.model_validate(updated)


@router.delete("/content/scenes/{scene_id}", response_model=dict)
def delete_scene(
    scene_id: str
) -> dict:
    """Delete a scene."""
    deleted = scenes_service.delete_scene(scene_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"message": "Scene deleted successfully"}


# ============================================
# SCENE REORDERING ENDPOINTS
# ============================================

@router.post("/{project_id}/content/scenes/reorder", response_model=dict)
def reorder_scenes(
    project_id: UUID,
    order_list: list[dict]
) -> dict:  # type: ignore
    """Reorder scenes in a project.
    
    Args:
        project_id: Project ID
        order_list: List of dicts with {'scene_id': str, 'position': int}
    """
    result = scenes_service.reorder_scenes(str(project_id), order_list)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to reorder scenes")
    return {"message": "Scenes reordered successfully"}


# ============================================
# CHARACTER ENDPOINTS
# ============================================

@router.get("/{project_id}/content/characters")
def list_characters(project_id: UUID) -> List[CharacterReadResponse]:  # type: ignore
    """Retrieve all characters for a project."""
    characters = scenes_service.get_all_characters(str(project_id))
    return [CharacterReadResponse.model_validate(c) for c in characters]


@router.post("/{project_id}/content/characters", response_model=CharacterReadResponse)
def create_character(
    project_id: UUID,
    character_data: dict
) -> CharacterReadResponse:  # type: ignore
    """Create a new character for continuity."""
    created = scenes_service.create_character(str(project_id), character_data)
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create character")
    return CharacterReadResponse.model_validate(created)


@router.put("/content/characters/{character_id}", response_model=CharacterReadResponse)
def update_character(
    character_id: str,
    project_id: UUID,
    character_data: dict
) -> CharacterReadResponse:  # type: ignore
    """Update an existing character."""
    updated = scenes_service.update_character(character_id, str(project_id), character_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Character not found")
    return CharacterReadResponse.model_validate(updated)


@router.delete("/content/characters/{character_id}", response_model=dict)
def delete_character(
    character_id: str
) -> dict:
    """Delete a character."""
    deleted = scenes_service.delete_character(character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}


# ============================================
# LOCATION ENDPOINTS
# ============================================

@router.get("/{project_id}/content/locations")
def list_locations(project_id: UUID) -> List[LocationReadResponse]:  # type: ignore
    """Retrieve all locations for a project."""
    locations = scenes_service.get_all_locations(str(project_id))
    return [LocationReadResponse.model_validate(loc) for loc in locations]


@router.post("/{project_id}/content/locations", response_model=LocationReadResponse)
def create_location(
    project_id: UUID,
    location_data: dict
) -> LocationReadResponse:  # type: ignore
    """Create a new location for continuity."""
    created = scenes_service.create_location(str(project_id), location_data)
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create location")
    return LocationReadResponse.model_validate(created)


@router.put("/content/locations/{location_id}", response_model=LocationReadResponse)
def update_location(
    location_id: str,
    project_id: UUID,
    location_data: dict
) -> LocationReadResponse:  # type: ignore
    """Update an existing location."""
    updated = scenes_service.update_location(location_id, str(project_id), location_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationReadResponse.model_validate(updated)


@router.delete("/content/locations/{location_id}", response_model=dict)
def delete_location(
    location_id: str
) -> dict:
    """Delete a location."""
    deleted = scenes_service.delete_location(location_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted successfully"}


# ============================================
# SCENE PROMPT HISTORY ENDPOINTS (AI REGENERATION)
# ============================================

@router.post("/content/scenes/{scene_id}/prompts", response_model=dict)
def create_prompt_history(
    scene_id: str,
    prompt_data: dict
) -> dict:  # type: ignore
    """Create prompt history for AI regeneration."""
    created = scenes_service.create_prompt_history(scene_id, prompt_data)
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create prompt history")
    return {"message": "Prompt history created", "id": created.id}


@router.get("/content/scenes/{scene_id}/prompts/history", response_model=list[dict])
def get_prompt_history(
    scene_id: str
) -> list[dict]:  # type: ignore
    """Get prompt history for a scene."""
    history = scenes_service.get_prompt_history(scene_id)
    return [{"id": h.id, "version": h.version, "prompt_type": h.prompt_type, "prompt_text": h.prompt_text} for h in history]
