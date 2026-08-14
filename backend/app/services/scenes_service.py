"""Scene Service for Content & Scene Planning Workspace."""

from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.scenes import SceneDB, CharacterDB, LocationDB, ScenePrompt


class ScenesService:
    """Service for managing scenes in a project."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # SCENE CRUD OPERATIONS
    # ============================================

    def get_all_scenes(self, project_id: str) -> List[SceneDB]:
        """Get all scenes for a project."""
        return self.db.query(SceneDB).filter(
            SceneDB.project_id == UUID(project_id)
        ).order_by(SceneDB.scene_number).all()

    def get_scene_by_id(self, scene_id: str, project_id: Optional[str] = None) -> Optional[SceneDB]:
        """Get a single scene by ID."""
        if project_id is not None and len(project_id) > 0:
            return self.db.query(SceneDB).filter(
                SceneDB.id == scene_id,
                SceneDB.project_id == UUID(project_id)
            ).first()
        return self.db.query(SceneDB).filter(SceneDB.id == scene_id).first()

    def create_scene(self, project_id: str, payload: dict) -> Optional[SceneDB]:
        """Create a new scene."""
        try:
            # Parse the payload
            characters = payload.get('characters', [])
            
            scene = SceneDB(
                id=payload.get('id'),
                project_id=UUID(project_id),
                lyrics_id=payload.get('lyrics_id'),
                scene_number=payload.get('scene_number', 1),
                title=payload.get('title'),
                description=payload.get('description'),
                characters=characters,
                location_name=payload.get('location_name'),
                location_description=payload.get('location_description'),
                time_period=payload.get('time_period'),
                emotion=payload.get('emotion'),
                action=payload.get('action'),
                visual_theme=payload.get('visual_theme'),
                visual_prompt=payload.get('visual_prompt'),
                negative_prompt=payload.get('negative_prompt'),
                camera_angle=payload.get('camera_angle'),
                lighting=payload.get('lighting'),
                composition=payload.get('composition'),
                duration_seconds=payload.get('duration_seconds', 8),
                continuity_notes=payload.get('continuity_notes'),
                status=payload.get('status', 'draft')
            )
            
            self.db.add(scene)
            self.db.commit()
            return scene
        except Exception:
            self.db.rollback()
            return None

    def update_scene(self, scene_id: str, project_id: str, payload: dict) -> Optional[SceneDB]:
        """Update an existing scene."""
        scene = self.get_scene_by_id(scene_id, project_id)
        if not scene:
            return None
        
        try:
            for field, value in payload.items():
                if hasattr(scene, field):
                    setattr(scene, field, value)
            
            # Use setattr to assign None (compatible with Mapped[datetime] type)
            setattr(scene, 'updated_at', None)
            
            self.db.commit()
            return scene
        except Exception:
            self.db.rollback()
            return None

    def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene."""
        scene = self.get_scene_by_id(scene_id)
        if not scene:
            return False
        
        try:
            self.db.delete(scene)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    # ============================================
    # SCENE REORDERING
    # ============================================

    def reorder_scenes(self, project_id: str, order_list: List[dict]) -> bool:
        """Reorder scenes by position.
        
        Args:
            project_id: Project ID
            order_list: List of dicts with {'scene_id': ..., 'position': ...}
        """
        try:
            for item in order_list:
                scene = self.get_scene_by_id(item['scene_id'], project_id)
                if scene:
                    scene.scene_number = item.get('position', 1)
            
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    # ============================================
    # CHARACTER OPERATIONS
    # ============================================

    def get_all_characters(self, project_id: str) -> List[CharacterDB]:
        """Get all characters for a project."""
        return self.db.query(CharacterDB).filter(
            CharacterDB.project_id == UUID(project_id)
        ).all()

    def create_character(self, project_id: str, payload: dict) -> Optional[CharacterDB]:
        """Create a new character."""
        try:
            char = CharacterDB(
                id=payload.get('id'),
                project_id=UUID(project_id),
                character_name=payload.get('character_name'),
                display_name=payload.get('display_name'),
                age_range=payload.get('age_range'),
                appearance=payload.get('appearance'),
                clothing=payload.get('clothing'),
                accessories=payload.get('accessories'),
                hair_style=payload.get('hair_style'),
                eye_color=payload.get('eye_color'),
                skin_tone=payload.get('skin_tone'),
                personality=payload.get('personality'),
                role=payload.get('role')
            )
            
            self.db.add(char)
            self.db.commit()
            return char
        except Exception:
            self.db.rollback()
            return None

    def update_character(self, char_id: str, project_id: str, payload: dict) -> Optional[CharacterDB]:
        """Update an existing character."""
        char = self.db.query(CharacterDB).filter(
            CharacterDB.id == char_id,
            CharacterDB.project_id == UUID(project_id)
        ).first()
        
        if not char:
            return None
        
        try:
            for field, value in payload.items():
                if hasattr(char, field):
                    setattr(char, field, value)
            
            self.db.commit()
            return char
        except Exception:
            self.db.rollback()
            return None

    def delete_character(self, char_id: str) -> bool:
        """Delete a character."""
        char = self.db.query(CharacterDB).filter(CharacterDB.id == char_id).first()
        if not char:
            return False
        
        try:
            self.db.delete(char)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    # ============================================
    # LOCATION OPERATIONS
    # ============================================

    def get_all_locations(self, project_id: str) -> List[LocationDB]:
        """Get all locations for a project."""
        return self.db.query(LocationDB).filter(
            LocationDB.project_id == UUID(project_id)
        ).all()

    def create_location(self, project_id: str, payload: dict) -> Optional[LocationDB]:
        """Create a new location."""
        try:
            loc = LocationDB(
                id=payload.get('id'),
                project_id=UUID(project_id),
                location_name=payload.get('location_name'),
                display_name=payload.get('display_name'),
                environment_type=payload.get('environment_type'),
                description=payload.get('description'),
                time_of_day=payload.get('time_of_day'),
                season=payload.get('season'),
                lighting_condition=payload.get('lighting_condition'),
                architecture_style=payload.get('architecture_style'),
                interior_exterior=payload.get('interior_exterior'),
                color_palette=payload.get('color_palette'),
                atmospheric_effects=payload.get('atmospheric_effects')
            )
            
            self.db.add(loc)
            self.db.commit()
            return loc
        except Exception:
            self.db.rollback()
            return None

    def update_location(self, loc_id: str, project_id: str, payload: dict) -> Optional[LocationDB]:
        """Update an existing location."""
        loc = self.db.query(LocationDB).filter(
            LocationDB.id == loc_id,
            LocationDB.project_id == UUID(project_id)
        ).first()
        
        if not loc:
            return None
        
        try:
            for field, value in payload.items():
                if hasattr(loc, field):
                    setattr(loc, field, value)
            
            self.db.commit()
            return loc
        except Exception:
            self.db.rollback()
            return None

    def delete_location(self, loc_id: str) -> bool:
        """Delete a location."""
        loc = self.db.query(LocationDB).filter(LocationDB.id == loc_id).first()
        if not loc:
            return False
        
        try:
            self.db.delete(loc)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    # ============================================
    # PROMPT OPERATIONS (AI REGENERATION)
    # ============================================

    def create_prompt_history(self, scene_id: str, payload: dict) -> Optional[ScenePrompt]:
        """Create a prompt history entry for regeneration."""
        try:
            prompt = ScenePrompt(
                id=payload.get('id'),
                scene_id=scene_id,
                prompt_type=payload.get('prompt_type', 'visual'),
                prompt_text=payload.get('prompt_text'),
                version=payload.get('version', 1),
                created_by=payload.get('created_by'),
                change_summary=payload.get('change_summary')
            )
            
            self.db.add(prompt)
            self.db.commit()
            return prompt
        except Exception:
            self.db.rollback()
            return None

    def get_prompt_history(self, scene_id: str) -> List[ScenePrompt]:
        """Get prompt history for a scene."""
        return self.db.query(ScenePrompt).filter(
            ScenePrompt.scene_id == scene_id
        ).order_by(ScenePrompt.version.desc()).all()
