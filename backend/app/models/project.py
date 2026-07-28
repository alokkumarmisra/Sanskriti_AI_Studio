"""Project model for database storage."""

from datetime import datetime  # noqa: F401
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, DateTime
from sqlalchemy.sql.functions import now as func_now  # noqa: F401
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func_now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func_now(), onupdate=func_now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    specs: Mapped[dict | None] = mapped_column(JSON, default=dict)