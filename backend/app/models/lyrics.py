"""Lyrics model for database storage."""

from datetime import datetime  # noqa: F401
from uuid import uuid4

from sqlalchemy import String, DateTime, ForeignKey, Text, func, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy base class for database models."""
    pass


class Lyrics(Base):  # type: ignore[name-defined]
    """Lyrics entity.

    Every lyrics record belongs to one Project.
    """

    __tablename__ = "lyrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), default="English", nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationship to Project
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="lyrics",
        foreign_keys=[project_id],
        lazy="joined"
    )