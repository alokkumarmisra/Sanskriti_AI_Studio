"""Pydantic schemas for Projects and Lyrics APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    """Project data model without database fields."""

    name: str
    description: str | None = None
    project_type: str = "general"


class ProjectCreate(ProjectBase):
    """Request schema for creating a project."""

    status: str | None = None


class ProjectUpdate(BaseModel):
    """Request schema for updating a project."""

    name: str | None = None
    description: str | None = None
    project_type: str | None = None
    status: str | None = None


class ProjectRead(BaseModel):
    """Response schema for a project with database fields.

    Used when returning project data from API endpoints.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    project_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectsListResponse(BaseModel):
    """Response schema for listing projects."""

    success: bool = True
    data: list[ProjectRead]
    message: str = "Projects retrieved successfully"


# ============================================
# LYRICS SCHEMAS
# ============================================

class LyricsBase(BaseModel):
    """Lyrics data model without database fields."""

    title: str | None = None
    content: str
    language: str = "English"
    status: str = "active"


class LyricsCreate(LyricsBase):
    """Request schema for creating a lyrics entry."""

    project_id: UUID


class LyricsUpdate(BaseModel):
    """Request schema for updating a lyrics entry."""

    title: str | None = None
    content: str | None = None
    language: str | None = None
    status: str | None = None


class LyricsRead(BaseModel):
    """Response schema for a lyrics entry with database fields.

    Used when returning lyrics data from API endpoints.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str | None = None
    content: str
    language: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class LyricsListResponse(BaseModel):
    """Response schema for listing lyrics."""

    success: bool = True
    data: list[LyricsRead]
    message: str = "Lyrics retrieved successfully"