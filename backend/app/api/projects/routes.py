"""API routes for Projects and Lyrics."""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.services.project_service import ProjectService  # noqa: F401
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectsListResponse,
)
from app.services.lyrics_service import LyricsService  # noqa: F401
from app.schemas.project import (
    LyricsRead,
    LyricsUpdate,
    LyricsListResponse,
)


# Dependency to get lyrics service
LyricsServiceDep = Annotated[LyricsService, Depends(LyricsService)]


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectsListResponse)
def list_projects() -> ProjectsListResponse:
    """Retrieve all projects."""
    service = ProjectService()
    projects = service.get_all_projects()
    return ProjectsListResponse(data=[ProjectRead.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ProjectsListResponse)
def get_project(project_id: UUID) -> ProjectsListResponse:
    """Retrieve a single project by ID."""
    service = ProjectService()
    project = service.get_project_by_id(str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectsListResponse(data=[ProjectRead.model_validate(project)])


@router.post("", response_model=ProjectsListResponse)
def create_project(project: ProjectCreate) -> ProjectsListResponse:
    """Create a new project."""
    service = ProjectService()
    created = service.create_project(
        name=project.name,
        description=project.description,
        project_type=project.project_type,
    )
    return ProjectsListResponse(data=[ProjectRead.model_validate(created)])


@router.put("/{project_id}", response_model=ProjectsListResponse)
def update_project(project_id: UUID, project: ProjectCreate) -> ProjectsListResponse:
    """Update an existing project."""
    service = ProjectService()
    updated = service.update_project(
        str(project_id),
        name=project.name,
        description=project.description,
        project_type=project.project_type,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectsListResponse(data=[ProjectRead.model_validate(updated)])


@router.delete("/{project_id}", response_model=ProjectsListResponse)
def delete_project(project_id: UUID) -> ProjectsListResponse:
    """Delete a project."""
    service = ProjectService()
    deleted = service.delete_project(str(project_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectsListResponse(data=[], message="Project deleted successfully")


# ============================================
# LYRICS ENDPOINTS
# ============================================

@router.get("/{project_id}/lyrics", response_model=LyricsListResponse)
def list_lyrics(project_id: UUID, service: LyricsServiceDep = Depends()) -> LyricsListResponse:
    """Retrieve all lyrics for a specific project."""
    lyrics = service.get_lyrics_by_project(str(project_id))
    return LyricsListResponse(
        data=[LyricsRead.model_validate(l) for l in lyrics]
    )


@router.post("/{project_id}/lyrics", response_model=ProjectsListResponse)
def create_lyrics(project_id: UUID, lyrics_create: LyricsCreate) -> ProjectsListResponse:
    """Create a new lyrics entry for a project."""
    service = LyricsService()
    created = service.create_lyrics(
        project_id=str(project_id),
        title=lyrics_create.title,
        content=lyrics_create.content,
        language=lyrics_create.language,
        status=lyrics_create.status,
    )
    return ProjectsListResponse(data=[LyricsRead.model_validate(created)])


@router.put("/lyrics/{lyrics_id}", response_model=ProjectsListResponse)
def update_lyrics(lyrics_id: UUID, lyrics_update: LyricsUpdate) -> ProjectsListResponse:
    """Update an existing lyrics entry."""
    service = LyricsService()
    
    # Verify lyrics exists first
    lyrics_data = service.get_lyrics_by_id(str(lyrics_id))
    if not lyrics_data:
        raise HTTPException(status_code=404, detail="Lyrics not found")
    
    # Build update kwargs from payload
    kwargs = {}
    if lyrics_update.title is not None:
        kwargs["title"] = lyrics_update.title
    if lyrics_update.content is not None:
        kwargs["content"] = lyrics_update.content
    if lyrics_update.language is not None:
        kwargs["language"] = lyrics_update.language
    if lyrics_update.status is not None:
        kwargs["status"] = lyrics_update.status
    
    updated = service.update_lyrics(str(lyrics_id), **kwargs)
    return ProjectsListResponse(data=[LyricsRead.model_validate(updated)])


@router.delete("/lyrics/{lyrics_id}", response_model=ProjectsListResponse)
def delete_lyrics(lyrics_id: UUID, service: LyricsServiceDep = Depends()) -> ProjectsListResponse:
    """Delete a lyrics entry."""
    deleted = service.delete_lyrics(str(lyrics_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Lyrics not found")
    return ProjectsListResponse(data=[], message="Lyrics deleted successfully")


# Pydantic import for LyricsCreate
from app.schemas.project import LyricsCreate  # noqa: F401