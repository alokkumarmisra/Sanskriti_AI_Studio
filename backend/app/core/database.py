"""Database layer for Sanskriti AI Studio backend."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import config  # noqa: F401


def get_engine() -> Engine:
    """Create SQLAlchemy engine with connection pooling."""
    return create_engine(
        f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def db_health_check() -> bool:
    """Check if the database is reachable and accepting connections."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return result.scalar() == 1