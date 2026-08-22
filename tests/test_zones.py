"""
Virtual Fence — Zone API Tests
Tests for zone CRUD operations and validation.
"""

import pytest


class TestListZones:
    def test_list_zones_empty(self, client):
        response = client.get("/api/v1/zones")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_zones_returns_created(self, client, created_zone):
        response = client.get("/api/v1/zones")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(z["name"] == "Test Zone Alpha" for z in data)


class TestCreateZone:
    def test_create_zone_success(self, client, sample_zone_payload):
        response = client.post("/api/v1/zones", json=sample_zone_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Zone Alpha"
        assert data["type"] == "POLYGON"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_zone_minimum_points(self, client):
        payload = {
            "name": "Triangle Zone",
            "type": "POLYGON",
            "points": [[0.0, 0.0], [0.5, 0.0], [0.25, 0.5]],
        }
        response = client.post("/api/v1/zones", json=payload)
        assert response.status_code == 201

    def test_create_zone_too_few_points(self, client):
        payload = {
            "name": "Bad Zone",
            "type": "POLYGON",
            "points": [[0.1, 0.2], [0.5, 0.2]],  # Only 2 points
        }
        response = client.post("/api/v1/zones", json=payload)
        assert response.status_code == 422  # Pydantic validation error

    def test_create_zone_empty_name(self, client):
        payload = {
            "name": "",
            "type": "POLYGON",
            "points": [[0.1, 0.2], [0.5, 0.2], [0.5, 0.8]],
        }
        response = client.post("/api/v1/zones", json=payload)
        assert response.status_code == 422

    def test_create_zone_missing_name(self, client):
        payload = {
            "type": "POLYGON",
            "points": [[0.1, 0.2], [0.5, 0.2], [0.5, 0.8]],
        }
        response = client.post("/api/v1/zones", json=payload)
        assert response.status_code == 422


class TestDeleteZone:
    def test_delete_zone_success(self, client, created_zone):
        zone_id = created_zone["id"]
        response = client.delete(f"/api/v1/zones/{zone_id}")
        assert response.status_code == 204

        # Verify it's gone
        list_response = client.get("/api/v1/zones")
        assert all(z["id"] != zone_id for z in list_response.json())

    def test_delete_zone_not_found(self, client):
        response = client.delete("/api/v1/zones/nonexistent-id")
        assert response.status_code == 404
