"""
Virtual Fence — Health Endpoint Tests
Tests for health check and system status endpoints.
"""

import pytest


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "cameras_active" in data
        assert "database" in data

    def test_health_version_matches(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["version"] == "1.0.0"


class TestSystemStatus:
    def test_status_returns_200(self, client):
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "state" in data
        assert data["state"] in ("SECURE", "BREACH")
        assert "total_cameras" in data
        assert "active_targets" in data
        assert "total_zones" in data
        assert "total_incidents" in data
        assert "uptime_seconds" in data
