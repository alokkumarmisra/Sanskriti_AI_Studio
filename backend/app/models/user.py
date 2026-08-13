"""User model for database storage."""

from datetime import datetime  # noqa: F401
from uuid import uuid4

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.project import Project, Base as ProjectBase


class Base(DeclarativeBase):
    """SQLAlchemy base class for user models."""
    pass


class User(Base):  # type: ignore[name-defined]
    """User entity.

    Every user can own multiple projects.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32), default="viewer")  # viewer, editor, admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        foreign_keys="User.owned_project_ids",
    )
    owned_project_ids: Mapped[list[str]] = mapped_column(String, nullable=False, default=list)


class AuthSession(Base):  # type: ignore[name-defined]
    """Authentication session for refresh tokens."""

    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))  # NVARCHAR in SQL Server
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
