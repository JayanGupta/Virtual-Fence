"""
Virtual Fence — Pytest Configuration & Fixtures
Provides test database, FastAPI test client, and mock vision engines.
"""

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, get_db
from backend.main import app


# ---------------------------------------------------------------------------
# In-memory test database
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///./test_virtual_fence.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Yields a test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables for each test, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up test database file
    try:
        os.remove("./test_virtual_fence.db")
    except OSError:
        pass


@pytest.fixture
def client():
    """FastAPI test client with test database override."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Direct database session for test setup/verification."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_zone_payload():
    """A valid zone creation payload."""
    return {
        "name": "Test Zone Alpha",
        "type": "POLYGON",
        "points": [[0.1, 0.2], [0.5, 0.2], [0.5, 0.8], [0.1, 0.8]],
    }


@pytest.fixture
def created_zone(client, sample_zone_payload):
    """Create a zone and return the response data."""
    response = client.post("/api/v1/zones", json=sample_zone_payload)
    assert response.status_code == 201
    return response.json()
