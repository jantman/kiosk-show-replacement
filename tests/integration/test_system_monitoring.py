"""
Integration tests for system monitoring page in the admin interface.

Tests the system monitoring page tabs and functionality:
- SSE debug tools tab loads
- Display status tab loads
- System health tab shows status

Run with: nox -s test-integration
"""

import os

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped",
)
class TestSystemMonitoring:
    """Test system monitoring page through the admin interface."""

    @pytest.mark.xfail(
        reason="Bug: SSEDebugger component has runtime error 'Cannot read properties of undefined (reading length)'. "
        "The error causes ErrorBoundary to display error instead of the monitoring page. "
        "See docs/features/fix-sse-debugger-component-error.md for details."
    )
    def test_sse_debug_tools_tab_loads(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that SSE debug tools tab loads correctly."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for page to fully load (some components might be async)
        page.wait_for_timeout(1000)

        # Verify page header
        expect(page.locator("text=System Monitoring").first).to_be_visible(
            timeout=10000
        )

        # Verify tabs exist
        tabs = page.locator("#monitoring-tabs")
        expect(tabs).to_be_visible()

        # SSE Debug Tools tab should be active by default (first tab)
        sse_tab = tabs.locator("button:has-text('SSE Debug Tools')")
        expect(sse_tab).to_be_visible()

        # Verify SSE tab content is visible
        # The card should have "Server-Sent Events Monitoring" header
        expect(
            page.locator("text=Server-Sent Events Monitoring")
        ).to_be_visible(timeout=5000)

    @pytest.mark.xfail(
        reason="Bug: SSEDebugger component has runtime error that breaks the monitoring page. "
        "See docs/features/fix-sse-debugger-component-error.md for details."
    )
    def test_display_status_tab_loads(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that Display Status tab loads correctly."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)

        # Verify page loads
        expect(page.locator("text=System Monitoring").first).to_be_visible(
            timeout=10000
        )

        # Click on Display Status tab
        tabs = page.locator("#monitoring-tabs")
        display_tab = tabs.locator("button:has-text('Display Status')")
        expect(display_tab).to_be_visible()
        display_tab.click()

        # Verify Display Status tab content is visible
        # Note: The tab content might show error if /api/v1/displays/status returns 404
        # but the tab header should still be visible
        expect(
            page.locator("text=Enhanced Display Monitoring")
        ).to_be_visible(timeout=5000)

    @pytest.mark.xfail(
        reason="Bug: SSEDebugger component has runtime error that breaks the monitoring page. "
        "See docs/features/fix-sse-debugger-component-error.md for details."
    )
    def test_system_health_tab_shows_status(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that System Health tab shows health status."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)

        # Verify page loads
        expect(page.locator("text=System Monitoring").first).to_be_visible(
            timeout=10000
        )

        # Click on System Health tab
        tabs = page.locator("#monitoring-tabs")
        health_tab = tabs.locator("button:has-text('System Health')")
        expect(health_tab).to_be_visible()
        health_tab.click()

        # Verify System Health tab content is visible
        expect(
            page.locator("text=System Health Overview")
        ).to_be_visible(timeout=5000)

        # Verify health status is shown ("System Healthy" message)
        expect(
            page.locator("text=System Healthy")
        ).to_be_visible(timeout=5000)

        # Verify the status cards are shown
        expect(page.locator("text=API Status")).to_be_visible()
        expect(page.locator("text=Database")).to_be_visible()
        expect(page.locator("text=SSE Service")).to_be_visible()

        # Verify all systems show operational status
        expect(page.locator("text=Operational")).to_be_visible()
        expect(page.locator("text=Connected")).to_be_visible()
        expect(page.locator("text=Active")).to_be_visible()

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        page.goto(f"{vite_url}/admin/login")
        page.wait_for_selector("input[name='username']", timeout=10000)

        user = test_database["users"][0]
        page.locator("input[name='username']").fill(user["username"])
        page.locator("input[name='password']").fill(user["password"])
        page.locator("button[type='submit']").click()

        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)
