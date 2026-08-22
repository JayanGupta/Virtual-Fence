"""
Virtual Fence — Incident API Tests
Tests for incident listing and status management.
"""

import json
from datetime import datetime, timezone

import pytest


def _create_incident(db_session, zone_id: str, status: str = "UNREAD"):
    """Helper to insert an incident directly into the test DB."""
    from backend.models import IncidentModel
    import uuid

    incident = IncidentModel(
        id=str(uuid.uuid4()),
        zone_id=zone_id,
        object_id=1,
        timestamp=datetime.now(timezone.utc),
        snapshot_path="/snapshots/test.jpg",
        video_path=None,
        status=status,
        severity="MEDIUM",
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)
    return incident


class TestListIncidents:
    def test_list_incidents_empty(self, client):
        response = client.get("/api/v1/incidents")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_incidents_with_data(self, client, created_zone, db_session):
        _create_incident(db_session, created_zone["id"])
        _create_incident(db_session, created_zone["id"])

        response = client.get("/api/v1/incidents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_incidents_with_limit(self, client, created_zone, db_session):
        for _ in range(5):
            _create_incident(db_session, created_zone["id"])

        response = client.get("/api/v1/incidents?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_incidents_filter_by_status(self, client, created_zone, db_session):
        _create_incident(db_session, created_zone["id"], status="UNREAD")
        _create_incident(db_session, created_zone["id"], status="ACKNOWLEDGED")

        response = client.get("/api/v1/incidents?status=UNREAD")
        assert response.status_code == 200
        data = response.json()
        assert all(inc["status"] == "UNREAD" for inc in data)


class TestPatchIncident:
    def test_patch_incident_acknowledge(self, client, created_zone, db_session):
        incident = _create_incident(db_session, created_zone["id"])

        response = client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": "ACKNOWLEDGED"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ACKNOWLEDGED"

    def test_patch_incident_resolve(self, client, created_zone, db_session):
        incident = _create_incident(db_session, created_zone["id"])

        response = client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": "RESOLVED"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RESOLVED"

    def test_patch_incident_invalid_status(self, client, created_zone, db_session):
        incident = _create_incident(db_session, created_zone["id"])

        response = client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": "INVALID"},
        )
        assert response.status_code == 422

    def test_patch_incident_not_found(self, client):
        response = client.patch(
            "/api/v1/incidents/nonexistent-id",
            json={"status": "ACKNOWLEDGED"},
        )
        assert response.status_code == 404
