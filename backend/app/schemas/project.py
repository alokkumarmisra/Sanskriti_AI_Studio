"""Pydantic schemas for Projects API."""

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
