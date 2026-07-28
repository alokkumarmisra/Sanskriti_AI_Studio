"""Service layer for Projects business logic."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository


logger = logging.getLogger(__name__)


class ProjectService:
    """Business logic for Projects.

    Coordinates repositories and handles validation.
    Never communicates with UI directly.
    """

    def create_project(
        self, 
        name: str, 
        description: Optional[str] | None = None,
        project_type: str = "general"
    ) -> Project:
        """Create a new project."""
        logger.debug("Creating project: %s", name)
        # Generate slug from name (lowercase, spaces/hyphens replaced with hyphens, stripped)
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower()).strip().replace(' ', '-')
        session = next(get_db())
        try:
            repo = ProjectRepository(session)
            result = repo.create(
                name=name, 
                description=description,
                project_type=project_type,
                slug=slug
            )
            return result
        finally:
            session.close()

    def get_all_projects(self) -> list[Project]:
        """Retrieve all projects."""
        logger.debug("Fetching all projects")
        session = next(get_db())
        try:
            repo = ProjectRepository(session)
            results = repo.get_all()
            return results
        finally:
            session.close()

    def get_project_by_id(self, project_id: str) -> Project | None:
        """Retrieve a single project by ID."""
        logger.debug("Fetching project: %s", project_id)
        session = next(get_db())
        try:
            repo = ProjectRepository(session)
            result = repo.get_by_id(project_id)
            return result
        finally:
            session.close()

    def update_project(
        self, project_id: str, **kwargs
    ) -> Optional[Project]:
        """Update a project's fields.

        Allowed fields: name, description, project_type, status
        """
        logger.debug("Updating project: %s", project_id)
        session = next(get_db())
        try:
            repo = ProjectRepository(session)
            result = repo.update(project_id, **kwargs)
            return result
        finally:
            session.close()

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        logger.debug("Deleting project: %s", project_id)
        session = next(get_db())
        try:
            repo = ProjectRepository(session)
            result = repo.delete(project_id)
            return result
        finally:
            session.close()