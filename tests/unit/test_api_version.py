"""
Unit tests for the version API endpoint.

Tests that the version endpoint returns the correct version
and does not require authentication.
"""

from kiosk_show_replacement import __version__


class TestVersionAPI:
    """Test version API endpoint."""

    def test_version_endpoint_returns_version(self, client):
        """Test that the version endpoint returns the current version."""
        response = client.get("/api/v1/version")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["version"] == __version__

    def test_version_endpoint_no_auth_required(self, client):
        """Test that the version endpoint does not require authentication."""
        # Make request without any session or auth
        response = client.get("/api/v1/version")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "version" in data["data"]
