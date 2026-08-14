"""Scene model for database storage - Content & Scene Planning Workspace."""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any

from sqlalchemy import JSON, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel


# ============================================
# API RESPONSE MODELS (Pydantic)
# ============================================

class SceneResponse(BaseModel):
    """Scene model for API response."""
    
    id: str
    project_id: UUID
    lyrics_id: str
    scene_number: int
    lyric_section: Optional[str] = None
    lyric_text: Optional[str] = None
    title: str
    description: Optional[str] = None
    characters: Optional[Dict[str, Any]] = None
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    time_period: Optional[str] = None
    emotion: Optional[str] = None
    action: Optional[str] = None
    visual_theme: Optional[str] = None
    visual_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    camera_angle: Optional[str] = None
    lighting: Optional[str] = None
    composition: Optional[str] = None
    duration_seconds: int
    continuity_notes: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SceneCreateResponse(BaseModel):
    """Pydantic-compatible create payload for scene."""
    id: Optional[str] = None
    project_id: UUID
    lyrics_id: str
    scene_number: int = 1
    title: str
    description: Optional[str] = None
    characters: Optional[List[Dict[str, Any]]] = None
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    time_period: Optional[str] = None
    emotion: Optional[str] = None
    action: Optional[str] = None
    visual_theme: Optional[str] = None
    visual_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    camera_angle: Optional[str] = None
    lighting: Optional[str] = None
    composition: Optional[str] = None
    duration_seconds: int = 8
    continuity_notes: Optional[str] = None
    status: str = "draft"


class SceneReadResponse(BaseModel):
    """Pydantic-compatible response model for scene."""
    
    id: Optional[str] = None
    project_id: Optional[UUID] = None
    lyrics_id: Optional[str] = None
    scene_number: Optional[int] = None
    lyric_section: Optional[str] = None
    lyric_text: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    characters: Optional[Dict[str, Any]] = None
    location_name: Optional[str] = None
    location_description: Optional[str] = None
    time_period: Optional[str] = None
    emotion: Optional[str] = None
    action: Optional[str] = None
    visual_theme: Optional[str] = None
    visual_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    camera_angle: Optional[str] = None
    lighting: Optional[str] = None
    composition: Optional[str] = None
    duration_seconds: Optional[int] = None
    continuity_notes: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CharacterResponse(BaseModel):
    """Character model for API response."""
    
    id: str
    project_id: UUID
    character_name: str
    display_name: Optional[str] = None
    age_range: Optional[str] = None
    appearance: Optional[str] = None
    clothing: Optional[str] = None
    accessories: Optional[str] = None
    hair_style: Optional[str] = None
    eye_color: Optional[str] = None
    skin_tone: Optional[str] = None
    personality: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CharacterReadResponse(BaseModel):
    """Pydantic-compatible response model for character."""
    
    id: Optional[str] = None
    project_id: Optional[UUID] = None
    character_name: Optional[str] = None
    display_name: Optional[str] = None
    age_range: Optional[str] = None
    appearance: Optional[str] = None
    clothing: Optional[str] = None
    accessories: Optional[str] = None
    hair_style: Optional[str] = None
    eye_color: Optional[str] = None
    skin_tone: Optional[str] = None
    personality: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LocationResponse(BaseModel):
    """Location model for API response."""
    
    id: str
    project_id: UUID
    location_name: str
    display_name: Optional[str] = None
    environment_type: Optional[str] = None
    description: Optional[str] = None
    time_of_day: Optional[str] = None
    season: Optional[str] = None
    lighting_condition: Optional[str] = None
    architecture_style: Optional[str] = None
    interior_exterior: Optional[str] = None
    color_palette: Optional[str] = None
    atmospheric_effects: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LocationReadResponse(BaseModel):
    """Pydantic-compatible response model for location."""
    
    id: Optional[str] = None
    project_id: Optional[UUID] = None
    location_name: Optional[str] = None
    display_name: Optional[str] = None
    environment_type: Optional[str] = None
    description: Optional[str] = None
    time_of_day: Optional[str] = None
    season: Optional[str] = None
    lighting_condition: Optional[str] = None
    architecture_style: Optional[str] = None
    interior_exterior: Optional[str] = None
    color_palette: Optional[str] = None
    atmospheric_effects: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ============================================
# SQLALCHEMY MODELS
# ============================================

class Base(DeclarativeBase):
    """SQLAlchemy base class for database models."""
    pass


class SceneDB(Base):  # type: ignore[name-defined]
    """Scene entity for content planning.

    Every scene belongs to one Project and is associated with Lyrics.
    """

    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lyrics_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Scene ordering
    scene_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Lyric association
    lyric_section: Mapped[str | None] = mapped_column(String(256), nullable=True)
    lyric_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scene content
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Character information (JSON for flexible storage)
    characters: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Location information  
    location_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scene attributes
    time_period: Mapped[str | None] = mapped_column(String(256), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(256), nullable=True)
    action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Visual information
    visual_theme: Mapped[str | None] = mapped_column(String(256), nullable=True)
    visual_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Camera and lighting
    camera_angle: Mapped[str | None] = mapped_column(String(256), nullable=True)
    lighting: Mapped[str | None] = mapped_column(String(256), nullable=True)
    composition: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Duration in seconds
    duration_seconds: Mapped[int] = mapped_column(Integer, default=8, nullable=False)

    # Continuity notes
    continuity_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status management
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CharacterDB(Base):  # type: ignore[name-defined]
    """Character entity for content planning - maintains visual continuity."""

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Character identity
    character_name: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Physical description
    age_range: Mapped[str | None] = mapped_column(String(64), nullable=True)
    appearance: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Clothing and accessories
    clothing: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessories: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Visual traits
    hair_style: Mapped[str | None] = mapped_column(String(256), nullable=True)
    eye_color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    skin_tone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Personality and traits
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class LocationDB(Base):  # type: ignore[name-defined]
    """Location entity for content planning - maintains visual continuity."""

    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Location identity
    location_name: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Environment and setting
    environment_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Time and atmosphere
    time_of_day: Mapped[str | None] = mapped_column(String(128), nullable=True)
    season: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Lighting
    lighting_condition: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Architecture and structure
    architecture_style: Mapped[str | None] = mapped_column(String(256), nullable=True)
    interior_exterior: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Visual characteristics
    color_palette: Mapped[str | None] = mapped_column(String(256), nullable=True)
    atmospheric_effects: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class ScenePrompt(Base):  # type: ignore[name-defined]
    """Scene prompt history for AI regeneration and versioning."""

    __tablename__ = "scene_prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scene_id: Mapped[str] = mapped_column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    
    # Prompt content
    prompt_type: Mapped[str] = mapped_column(String(32), nullable=False)  # "visual", "description", "negative"
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class SceneCreatePayload(Dict[str, Any]):  # type: ignore[name-defined]
    """Pydantic-compatible create payload for scene."""
    def __init__(self, data: dict | None = None):
        self.data = data or {}
