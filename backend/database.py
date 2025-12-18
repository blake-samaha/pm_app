"""Database configuration and session management."""

from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel, create_engine

from config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.environment == "development",  # SQL logging in development
    poolclass=QueuePool,
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Additional connections if pool exhausted
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)


def get_session():
    """Get database session (FastAPI dependency)."""
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)
