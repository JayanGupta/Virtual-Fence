"""
Virtual Fence — Database Configuration
SQLAlchemy engine, session factory, and declarative base for SQLite persistence.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# Database path — stored alongside backend in the storage directory
# ---------------------------------------------------------------------------
_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
os.makedirs(_STORAGE_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(_STORAGE_DIR, 'virtual_fence.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + threads
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
