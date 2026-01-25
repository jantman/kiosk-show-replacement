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
        expect(page.locator("text=Server-Sent Events Monitoring")).to_be_visible(
            timeout=5000
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
        expect(page.locator("text=Enhanced Display Monitoring")).to_be_visible(
            timeout=5000
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

        # Wait for tab content to be visible and get the health tab panel
        health_panel = page.get_by_role("tabpanel", name="System Health")
        expect(health_panel).to_be_visible(timeout=5000)

        # Verify System Health tab content is visible
        expect(health_panel.locator("text=System Health Overview")).to_be_visible(
            timeout=5000
        )

        # Verify health status is shown ("System Healthy" message)
        expect(health_panel.locator("text=System Healthy")).to_be_visible(timeout=5000)

        # Verify the status cards are shown
        expect(health_panel.locator("text=API Status")).to_be_visible()
        expect(health_panel.locator("text=Database")).to_be_visible()
        expect(health_panel.locator("text=SSE Service")).to_be_visible()

        # Verify all systems show operational status (scoped to health panel)
        expect(health_panel.get_by_text("Operational", exact=True)).to_be_visible()
        expect(health_panel.get_by_text("Connected", exact=True)).to_be_visible()
        expect(health_panel.get_by_text("Active", exact=True)).to_be_visible()

    def test_sse_debug_tools_shows_connection_stats(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that SSE debug tools tab shows SSE connection statistics.

        This is a regression test for the bug where the SSE Debug Tools tab
        showed "No active SSE connections found" even when connections exist.
        The admin UI itself maintains an SSE connection, so we should see at
        least 1 admin connection.

        The test verifies:
        1. SSE connection is established (Connected badge visible)
        2. Total Connections shows >= 1
        3. Admin Connections shows >= 1
        4. "No active SSE connections found" is NOT visible
        5. The connections table shows at least one admin connection
        """
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for SSE connection to be established
        # The SSEDebugger component shows "Connected" badge when SSE is connected
        connected_badge = page.locator("span.badge.bg-success:has-text('Connected')")
        expect(connected_badge).to_be_visible(timeout=10000)

        # Click refresh to get fresh stats after SSE connection is established
        refresh_button = page.locator("button:has-text('Refresh')").first
        expect(refresh_button).to_be_visible(timeout=5000)
        refresh_button.click()
        page.wait_for_timeout(1000)

        # Verify "No active SSE connections found" is NOT visible
        # This was the bug: the message showed even when connections existed
        no_connections_alert = page.locator("text=No active SSE connections found")
        expect(no_connections_alert).not_to_be_visible()

        # Verify the Total Connections count is at least 1
        # The structure is: <h4 class="text-primary">{count}</h4><p>Total Connections</p>
        # We need to find the h4 that precedes the "Total Connections" label
        total_connections_container = page.locator(
            ".col-md-3:has(p:text('Total Connections'))"
        )
        total_connections_value = total_connections_container.locator("h4")
        expect(total_connections_value).to_be_visible(timeout=5000)
        total_count_text = total_connections_value.text_content()
        assert total_count_text is not None, "Total Connections value should exist"
        total_count = int(total_count_text)
        assert (
            total_count >= 1
        ), f"Total Connections should be at least 1, got {total_count}"

        # Verify the Admin Connections count is at least 1
        admin_connections_container = page.locator(
            ".col-md-3:has(p:text('Admin Connections'))"
        )
        admin_connections_value = admin_connections_container.locator("h4")
        expect(admin_connections_value).to_be_visible(timeout=5000)
        admin_count_text = admin_connections_value.text_content()
        assert admin_count_text is not None, "Admin Connections value should exist"
        admin_count = int(admin_count_text)
        assert (
            admin_count >= 1
        ), f"Admin Connections should be at least 1, got {admin_count}"

    def test_sse_debug_tools_shows_connections_table(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that SSE debug tools tab shows the connections table with data.

        This is a regression test for the bug where the SSE Debug Tools tab
        showed "No active SSE connections found" instead of the connections table.
        When an admin session is active with SSE, the table should show at least
        one row with "admin" type.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for SSE connection to be established
        connected_badge = page.locator("span.badge.bg-success:has-text('Connected')")
        expect(connected_badge).to_be_visible(timeout=10000)

        # Click refresh to get fresh stats
        refresh_button = page.locator("button:has-text('Refresh')").first
        expect(refresh_button).to_be_visible(timeout=5000)
        refresh_button.click()
        page.wait_for_timeout(1000)

        # Verify the connections table is visible (not the "no connections" alert)
        connections_table = page.locator("table")
        expect(connections_table).to_be_visible(timeout=5000)

        # Verify the table has headers including "Type", "User/Display", etc.
        expect(page.locator("th:has-text('Type')")).to_be_visible()
        expect(page.locator("th:has-text('User/Display')")).to_be_visible()

        # Verify at least one row exists in the table body with "admin" type badge
        admin_badge = page.locator("table tbody span.badge:has-text('admin')").first
        expect(admin_badge).to_be_visible(timeout=5000)

    def test_display_status_tab_no_error(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that Display Status tab does not show an error message.

        This is a regression test for the bug where the Display Status tab
        showed "Error loading display status: Failed to fetch display status: NOT FOUND"
        because the /api/v1/displays/status endpoint didn't exist.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)

        # Click on Display Status tab
        tabs = page.locator("#monitoring-tabs")
        display_tab = tabs.locator("button:has-text('Display Status')")
        expect(display_tab).to_be_visible()
        display_tab.click()

        page.wait_for_timeout(1000)

        # The error message should NOT be visible
        # This was the original bug: "Error loading display status: ..."
        error_message = page.locator("text=Error loading display status")
        expect(error_message).not_to_be_visible()

        # Also verify the "NOT FOUND" error is not visible
        not_found_error = page.locator("text=NOT FOUND")
        expect(not_found_error).not_to_be_visible()

    def test_display_status_tab_shows_display_info(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that Display Status tab shows display information when displays exist.

        This test verifies that when displays are configured in the system,
        they are properly shown in the Display Status tab with their status.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        flask_url = servers["flask_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Create a test display via API
        import requests

        session = requests.Session()
        # Login to API
        login_resp = session.post(
            f"{flask_url}/api/v1/auth/login",
            json={
                "username": test_database["users"][0]["username"],
                "password": test_database["users"][0]["password"],
            },
        )
        assert login_resp.status_code == 200

        # Create display
        create_resp = session.post(
            f"{flask_url}/api/v1/displays",
            json={
                "name": "test-monitoring-display",
                "location": "Test Location",
            },
        )
        assert create_resp.status_code == 201

        # Navigate to system monitoring page
        page.goto(f"{vite_url}/admin/monitoring")
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)

        # Click on Display Status tab
        tabs = page.locator("#monitoring-tabs")
        display_tab = tabs.locator("button:has-text('Display Status')")
        display_tab.click()

        page.wait_for_timeout(1000)

        # Should see the display name in the tab content
        expect(page.locator("text=test-monitoring-display")).to_be_visible(timeout=5000)

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        page.goto(f"{vite_url}/admin/login")
        page.wait_for_selector("input[name='username']", timeout=10000)

        user = test_database["users"][0]
        page.locator("input[name='username']").fill(user["username"])
        page.locator("input[name='password']").fill(user["password"])
        page.locator("button[type='submit']").click()

        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)
