"""
Simple SSE Integration Tests.

Tests Server-Sent Events (SSE) functionality with minimal browser automation.
These tests verify the basic SSE endpoints work correctly.
"""

import logging

import pytest
import requests
from playwright.sync_api import Page, expect

# Use the existing logger setup from conftest
logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestSSESimple:
    """Test basic SSE functionality with minimal browser automation."""

    def test_api_endpoints_accessible(self, servers, enhanced_page: Page):
        """Test that the SSE API endpoints are accessible with authentication."""
        logger.info("Testing SSE API endpoints accessibility")

        flask_url = servers["flask_url"]
        logger.info(f"Using Flask URL: {flask_url}")

        # Create a session to maintain authentication
        session = requests.Session()

        # First, authenticate via API login
        login_url = f"{flask_url}/api/v1/auth/login"
        logger.info(f"Authenticating at: {login_url}")

        login_response = session.post(
            login_url,
            json={"username": "test_user", "password": "test_pass"},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        assert login_response.status_code == 200

        login_data = login_response.json()
        assert login_data["success"] is True
        logger.info("Successfully authenticated")

        # Test /api/v1/events/stats endpoint
        stats_url = f"{flask_url}/api/v1/events/stats"
        logger.info(f"Testing stats endpoint: {stats_url}")

        response = session.get(stats_url, timeout=5)
        assert response.status_code == 200

        data = response.json()
        # Check API response format
        assert data["success"] is True
        assert "data" in data

        # Check SSE stats structure
        stats_data = data["data"]
        assert "total_connections" in stats_data
        assert "admin_connections" in stats_data
        assert "display_connections" in stats_data
        assert "connections" in stats_data

        # Test /api/v1/events/test endpoint (POST)
        test_url = f"{flask_url}/api/v1/events/test"
        logger.info(f"Testing test endpoint: {test_url}")

        response = session.post(
            test_url, json={"message": "test_event", "data": {"test": True}}, timeout=5
        )
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "message" in result

        logger.info("SSE API endpoints accessible and responding correctly")

    def test_basic_page_load(self, servers, enhanced_page: Page):
        """Test basic page loading functionality."""
        logger.info("Testing basic page load")

        vite_url = servers["vite_url"]
        logger.info(f"Loading React page: {vite_url}")

        # Just test basic page loading
        enhanced_page.goto(vite_url, wait_until="domcontentloaded", timeout=15000)

        # Check for any basic content
        title = enhanced_page.title()
        logger.info(f"Page title: {title}")

        # Wait for React to render something
        enhanced_page.wait_for_selector("body", timeout=10000)

        logger.info("Basic page load test completed successfully")

    def test_sse_stream_endpoint(self, servers, enhanced_page: Page):
        """Test that the SSE admin stream endpoint responds correctly."""
        logger.info("Testing SSE admin stream endpoint")

        flask_url = servers["flask_url"]
        admin_stream_url = f"{flask_url}/api/v1/events/admin"
        logger.info(f"Testing SSE admin stream endpoint: {admin_stream_url}")

        # This endpoint requires authentication, so we expect a 401 without auth
        response = enhanced_page.goto(admin_stream_url, timeout=10000)

        # Should get 401 Unauthorized since we're not authenticated
        assert response.status == 401

        logger.info(
            "SSE admin stream endpoint responds correctly with authentication requirement"
        )
