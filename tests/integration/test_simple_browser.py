"""
Simple browser test to verify Playwright works with local server.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.integration
class TestSimpleBrowser:
    """Simple browser test to verify Playwright works."""

    def test_simple_navigation(self, page: Page, live_server):
        """Test simple browser navigation to local server."""
        # Navigate to the live server - call url() method to get the actual URL
        server_url = live_server.url()
        page.goto(server_url, timeout=10000)

        # Wait for page to load and check basic content
        expect(page.locator("body")).to_be_visible(timeout=5000)

        # Get the page title - should be something from our app
        title = page.title()
        assert title  # Just check that there is a title
