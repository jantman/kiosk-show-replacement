"""
Simple SSE Integration Tests.

Tests Server-Sent Events (SSE) functionality with minimal browser automation.
These tests verify the basic SSE endpoints work correctly.
"""

import logging
import requests
import pytest
from playwright.sync_api import Page, expect

# Use the existing logger setup from conftest
logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestSSESimple:
    """Test basic SSE functionality with minimal browser automation."""

    def test_api_endpoints_accessible(self, servers, enhanced_page: Page):
        """Test that the SSE API endpoints are accessible."""
        logger.info("Testing SSE API endpoints accessibility")
        
        flask_url = servers["flask_url"]
        logger.info(f"Using Flask URL: {flask_url}")
        
        # Test /api/v1/events/stats endpoint
        stats_url = f"{flask_url}/api/v1/events/stats"
        logger.info(f"Testing stats endpoint: {stats_url}")
        
        response = requests.get(stats_url, timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert "connected_clients" in data
        assert "server_uptime" in data
        
        # Test /api/v1/events/test endpoint (POST)
        test_url = f"{flask_url}/api/v1/events/test"
        logger.info(f"Testing test endpoint: {test_url}")
        
        response = requests.post(test_url, 
                               json={"message": "test_event", "data": {"test": True}},
                               timeout=5)
        assert response.status_code == 200
        
        result = response.json()
        assert "success" in result
        
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
        """Test that the SSE stream endpoint responds correctly."""
        logger.info("Testing SSE stream endpoint")
        
        flask_url = servers["flask_url"]
        stream_url = f"{flask_url}/api/v1/events/stream"
        logger.info(f"Testing SSE stream endpoint: {stream_url}")
        
        # Navigate to the SSE stream endpoint
        response = enhanced_page.goto(stream_url, timeout=10000)
        
        # Should get a response (might be streaming)
        assert response.status in [200, 204]  # 204 is common for SSE with no immediate data
        
        # Check content type indicates SSE
        headers = response.headers
        if "content-type" in headers:
            content_type = headers["content-type"]
            logger.info(f"SSE endpoint content-type: {content_type}")
            # Should be text/event-stream or similar
            assert "text" in content_type or "event-stream" in content_type
        
        logger.info("SSE stream endpoint test completed successfully")
