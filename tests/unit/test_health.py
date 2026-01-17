"""
Tests for health check endpoints.

This module tests:
- /health - Overall health check
- /health/db - Database health check
- /health/storage - Storage health check
- /health/ready - Readiness probe
- /health/live - Liveness probe
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200_when_healthy(self, app, client):
        """Test health endpoint returns 200 when all checks pass."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json

        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "storage" in data["checks"]

    def test_health_includes_database_check(self, app, client):
        """Test health endpoint includes database check results."""
        response = client.get("/health")
        data = response.json

        db_check = data["checks"]["database"]
        assert "status" in db_check
        # If healthy, should have latency
        if db_check["status"] == "healthy":
            assert "latency_ms" in db_check

    def test_health_includes_storage_check(self, app, client):
        """Test health endpoint includes storage check results."""
        response = client.get("/health")
        data = response.json

        storage_check = data["checks"]["storage"]
        assert "status" in storage_check
        if storage_check["status"] != "unhealthy":
            assert "free_space_mb" in storage_check
            assert "total_space_mb" in storage_check


class TestDatabaseHealthEndpoint:
    """Tests for the /health/db endpoint."""

    def test_db_health_returns_200_when_connected(self, app, client):
        """Test database health returns 200 when database is connected."""
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json

        assert data["status"] == "healthy"
        assert "latency_ms" in data
        assert "timestamp" in data

    def test_db_health_returns_503_on_failure(self, app, client):
        """Test database health returns 503 when database fails."""
        with patch("kiosk_show_replacement.health._check_database") as mock_check:
            mock_check.return_value = {"status": "unhealthy", "error": "Connection refused"}
            response = client.get("/health/db")
            assert response.status_code == 503
            data = response.json
            assert data["status"] == "unhealthy"


class TestStorageHealthEndpoint:
    """Tests for the /health/storage endpoint."""

    def test_storage_health_returns_200(self, app, client):
        """Test storage health returns 200 when storage is available."""
        response = client.get("/health/storage")
        assert response.status_code == 200
        data = response.json

        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "free_space_mb" in data
        assert "total_space_mb" in data
        assert "used_percent" in data
        assert "writable" in data
        assert "path" in data

    def test_storage_health_checks_writability(self, app, client):
        """Test storage health verifies write access."""
        response = client.get("/health/storage")
        data = response.json

        # Storage should be writable in test environment
        assert data["writable"] is True


class TestReadinessProbe:
    """Tests for the /health/ready endpoint."""

    def test_ready_returns_200_when_db_healthy(self, app, client):
        """Test readiness probe returns 200 when database is healthy."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json

        assert data["status"] == "ready"
        assert "timestamp" in data

    def test_ready_returns_503_when_db_fails(self, app, client):
        """Test readiness probe returns 503 when database fails."""
        with patch("kiosk_show_replacement.health._check_database") as mock_check:
            mock_check.return_value = {"status": "unhealthy", "error": "Connection failed"}
            response = client.get("/health/ready")
            assert response.status_code == 503
            data = response.json
            assert data["status"] == "not_ready"
            assert "reason" in data


class TestLivenessProbe:
    """Tests for the /health/live endpoint."""

    def test_live_always_returns_200(self, app, client):
        """Test liveness probe always returns 200 if app is running."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json

        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_live_is_fast(self, app, client):
        """Test liveness probe responds quickly (no heavy checks)."""
        import time

        start = time.perf_counter()
        response = client.get("/health/live")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        # Should respond in under 100ms
        assert elapsed < 0.1


class TestHealthCheckHelpers:
    """Tests for health check helper functions."""

    def test_check_database_returns_latency(self, app):
        """Test database check returns latency measurement."""
        from kiosk_show_replacement.health import _check_database

        with app.app_context():
            result = _check_database()
            assert "status" in result
            if result["status"] == "healthy":
                assert "latency_ms" in result
                assert result["latency_ms"] >= 0

    def test_check_storage_returns_disk_info(self, app):
        """Test storage check returns disk space information."""
        from kiosk_show_replacement.health import _check_storage

        with app.app_context():
            result = _check_storage()
            assert "status" in result
            if result["status"] != "unhealthy":
                assert "free_space_mb" in result
                assert "total_space_mb" in result
                assert "used_percent" in result
                assert result["free_space_mb"] > 0
                assert result["total_space_mb"] > 0
                assert 0 <= result["used_percent"] <= 100

    def test_get_overall_status_all_healthy(self, app):
        """Test overall status is healthy when all checks pass."""
        from kiosk_show_replacement.health import _get_overall_status

        checks = {
            "database": {"status": "healthy"},
            "storage": {"status": "healthy"},
        }
        assert _get_overall_status(checks) == "healthy"

    def test_get_overall_status_one_degraded(self, app):
        """Test overall status is degraded when one check is degraded."""
        from kiosk_show_replacement.health import _get_overall_status

        checks = {
            "database": {"status": "healthy"},
            "storage": {"status": "degraded"},
        }
        assert _get_overall_status(checks) == "degraded"

    def test_get_overall_status_one_unhealthy(self, app):
        """Test overall status is unhealthy when one check fails."""
        from kiosk_show_replacement.health import _get_overall_status

        checks = {
            "database": {"status": "unhealthy"},
            "storage": {"status": "healthy"},
        }
        assert _get_overall_status(checks) == "unhealthy"
