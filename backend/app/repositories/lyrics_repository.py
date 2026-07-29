"""Repository for Lyrics CRUD operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lyrics import Lyrics
from app.models.project import Project


class LyricsRepository:
    """Data access layer for Lyrics.

    Contains only database queries - no business logic.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_all(self) -> list["Lyrics"]:
        """Retrieve all lyrics."""
        if not self.db:
            return []
        stmt = select(Lyrics).order_by(Lyrics.created_at.desc())
        results = self.db.execute(stmt).scalars().all()
        return list(results)

    def get_by_id(self, lyrics_id: str) -> Optional[Lyrics]:
        """Retrieve a single lyrics by ID."""
        if not self.db:
            return None
        stmt = select(Lyrics).where(Lyrics.id == lyrics_id)
        result = self.db.execute(stmt).scalars().first()
        return result

    def get_by_project(self, project_id: str) -> list["Lyrics"]:
        """Retrieve all lyrics for a specific project."""
        if not self.db:
            return []
        stmt = select(Lyrics).where(
            Lyrics.project_id == project_id
        ).order_by(Lyrics.created_at.desc())
        results = self.db.execute(stmt).scalars().all()
        return list(results)

    def create(self, project_id: str, **kwargs) -> Lyrics:
        """Create a new lyrics entry."""
        if not self.db:
            raise RuntimeError("No database session provided")

        lyrics = Lyrics(project_id=project_id)
        # Set optional fields
        if "title" in kwargs:
            lyrics.title = kwargs["title"]
        if "content" in kwargs:
            lyrics.content = kwargs["content"]
        if "language" in kwargs:
            lyrics.language = kwargs["language"]
        if "status" in kwargs:
            lyrics.status = kwargs["status"]

        self.db.add(lyrics)
        self.db.commit()
        self.db.refresh(lyrics)
        return lyrics

    def update(self, lyrics_id: str, **kwargs) -> Optional[Lyrics]:
        """Update a lyrics entry's fields."""
        if not self.db:
            return None
        stmt = select(Lyrics).where(Lyrics.id == lyrics_id)
        result = self.db.execute(stmt).scalars().first()
        if not result:
            return None
        for key, value in kwargs.items():
            if hasattr(result, key):
                setattr(result, key, value)
        self.db.commit()
        self.db.refresh(result)
        return result

    def delete(self, lyrics_id: str) -> bool:
        """Delete a lyrics entry."""
        if not self.db:
            return False
        stmt = select(Lyrics).where(Lyrics.id == lyrics_id)
        result = self.db.execute(stmt).scalars().first()
        if not result:
            return False
        self.db.delete(result)
        self.db.commit()
        return True

    def verify_project_exists(self, project_id: str) -> bool:
        """Verify that a project exists."""
        if not self.db:
            return False
        stmt = select(Project).where(Project.id == project_id)
        result = self.db.execute(stmt).scalars().first()
        return result is not None