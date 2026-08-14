"""Project model for database storage."""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.lyrics import Lyrics
    from app.models.scenes import Scene


class Base(DeclarativeBase):
    """SQLAlchemy base class for database models."""
    pass


class Project(Base):  # type: ignore[name-defined]
    """AI video project entity.

    Every resource belongs to one Project.
    """

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1024))
    owner: Mapped[str | None] = mapped_column(String(256))
    project_type: Mapped[str] = mapped_column(String(64), default="general")
    status: Mapped[str] = mapped_column(String(32), default="active")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    specs: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Relationship to Lyrics
    lyrics: Mapped[list["Lyrics"]] = relationship(
        "Lyrics",
        back_populates="project",
        lazy="dynamic"
    )

    # Relationship to Scenes
    scenes: Mapped[list["Scene"]] = relationship(
        "Scene",
        back_populates="project",
        lazy="joined"
    )
