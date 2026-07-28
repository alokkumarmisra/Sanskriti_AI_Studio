"""Repository for Project CRUD operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.project import Project


class ProjectRepository:
    """Data access layer for Projects.

    Contains only database queries - no business logic.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_all(self) -> list[Project]:
        """Retrieve all projects."""
        if not self.db:
            return []
        stmt = select(Project).order_by(Project.created_at.desc())
        results = self.db.execute(stmt).scalars().all()
        return list(results)

    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Retrieve a single project by ID."""
        if not self.db:
            return None
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt).scalars().first()
        return result

    def create(
        self, 
        name: str, 
        description: Optional[str] | None = None,
        project_type: str = "general",
        slug: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        if not self.db:
            raise RuntimeError("No database session provided")
        project = Project(name=name, description=description)
        project.project_type = project_type
        if slug is None:
            slug = ""
        project.slug = slug
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: str, **kwargs) -> Optional[Project]:
        """Update a project's fields."""
        if not self.db:
            return None
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt).scalars().first()
        if not result:
            return None
        for key, value in kwargs.items():
            if hasattr(result, key):
                setattr(result, key, value)
        self.db.commit()
        self.db.refresh(result)
        return result

    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        if not self.db:
            return False
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt).scalars().first()
        if not result:
            return False
        self.db.delete(result)
        self.db.commit()
        return True

    def get_by_status(self, status: str) -> list[Project]:
        """Retrieve projects filtered by status."""
        if not self.db:
            return []
        stmt = select(Project).where(Project.status == status).order_by(
            Project.created_at.desc()
        )
        results = self.db.execute(stmt).scalars().all()
        return list(results)