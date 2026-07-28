"""API routes for Projects."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.project_service import ProjectService  # noqa: F401
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectsListResponse,
)


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