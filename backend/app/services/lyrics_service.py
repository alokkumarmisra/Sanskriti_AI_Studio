"""Service layer for Lyrics business logic."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.lyrics import Lyrics
from app.repositories.lyrics_repository import LyricsRepository


logger = logging.getLogger(__name__)


class LyricsService:
    """Business logic for Lyrics.

    Coordinates repositories and handles validation.
    Never communicates with UI directly.
    """

    def create_lyrics(
        self, 
        project_id: str, 
        title: Optional[str] | None = None,
        content: str | None = None,
        language: str = "English",
        status: str = "active"
    ) -> Lyrics:
        """Create a new lyrics entry."""
        logger.debug("Creating lyrics for project: %s", project_id)
        
        session = next(get_db())
        try:
            repo = LyricsRepository(session)
            
            # Verify the project exists
            if not repo.verify_project_exists(project_id):
                raise ValueError(f"Project with ID {project_id} not found")
            
            result = repo.create(
                project_id=project_id,
                title=title,
                content=content,
                language=language,
                status=status,
            )
            return result
        finally:
            session.close()

    def get_all_lyrics(self) -> list[Lyrics]:
        """Retrieve all lyrics."""
        logger.debug("Fetching all lyrics")
        session = next(get_db())
        try:
            repo = LyricsRepository(session)
            results = repo.get_all()
            return results
        finally:
            session.close()

    def get_lyrics_by_id(self, lyrics_id: str) -> Lyrics | None:
        """Retrieve a single lyrics by ID."""
        logger.debug("Fetching lyrics: %s", lyrics_id)
        session = next(get_db())
        try:
            repo = LyricsRepository(session)
            result = repo.get_by_id(lyrics_id)
            return result
        finally:
            session.close()

    def get_lyrics_by_project(self, project_id: str) -> list[Lyrics]:
        """Retrieve all lyrics for a specific project."""
        logger.debug("Fetching lyrics for project: %s", project_id)
        session = next(get_db())
        try:
            repo = LyricsRepository(session)
            results = repo.get_by_project(project_id)
            return results
        finally:
            session.close()

    def update_lyrics(
        self, 
        lyrics_id: str, 
        **kwargs
    ) -> Optional[Lyrics]:
        """Update a lyrics entry's fields.

        Allowed fields: title, content, language, status
        """
        logger.debug("Updating lyrics: %s", lyrics_id)
        session = next(get_db())
        try:
            repo = LyricsRepository(session)
            result = repo.update(lyrics_id, **kwargs)
            return result
        finally:
            session.close()

    def delete_lyrics(self, lyrics_id: str) -> bool:
        """Delete a lyrics entry."""
        logger.debug("Deleting lyrics: %s", lyrics_id)
        session = next(get_db())
        try:
            repo = LyricsRepository(session)
            result = repo.delete(lyrics_id)
            return result
        finally:
            session.close()