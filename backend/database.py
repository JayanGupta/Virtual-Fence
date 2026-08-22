"""
Virtual Fence — Database Configuration
SQLAlchemy engine, session factory, and declarative base.
Supports config-driven database URL and connection pooling.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import get_settings


def _create_engine():
    """Create the SQLAlchemy engine from application settings."""
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite + threads
        pool_pre_ping=True,
        echo=False,
    )


engine = _create_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
