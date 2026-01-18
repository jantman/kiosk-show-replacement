"""
Integration tests for dashboard and navigation in the admin interface.

Tests dashboard statistics, recent items, and navigation flows:
- Dashboard displays correct statistics
- Dashboard shows recent slideshows
- Dashboard shows display status
- Quick action buttons navigate correctly
- Navigation bar links work correctly

Run with: nox -s test-integration
"""

import os
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped",
)
class TestDashboard:
    """Test dashboard and navigation through the admin interface."""

    def test_dashboard_displays_statistics(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        test_display: dict,
    ):
        """Test that dashboard displays correct statistics cards."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Should be on dashboard after login
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Verify statistics cards are present
        # Active Slideshows card
        active_slideshows_card = page.locator(".card:has-text('Active Slideshows')")
        expect(active_slideshows_card).to_be_visible()
        # The count should be visible (h3 element with number)
        expect(active_slideshows_card.locator("h3")).to_be_visible()

        # Online Displays card
        online_displays_card = page.locator(".card:has-text('Online Displays')")
        expect(online_displays_card).to_be_visible()
        expect(online_displays_card.locator("h3")).to_be_visible()

        # Assigned Displays card
        assigned_displays_card = page.locator(".card:has-text('Assigned Displays')")
        expect(assigned_displays_card).to_be_visible()
        expect(assigned_displays_card.locator("h3")).to_be_visible()

        # Offline Displays card
        offline_displays_card = page.locator(".card:has-text('Offline Displays')")
        expect(offline_displays_card).to_be_visible()
        expect(offline_displays_card.locator("h3")).to_be_visible()

    def test_dashboard_shows_recent_slideshows(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test that dashboard shows recent slideshows section."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Wait for dashboard to load
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Verify Recent Slideshows card exists
        recent_slideshows_card = page.locator(".card").filter(
            has=page.locator(".card-header:has-text('Recent Slideshows')")
        )
        expect(recent_slideshows_card).to_be_visible()

        # Verify "View All" link exists
        expect(recent_slideshows_card.locator("a:has-text('View All')")).to_be_visible()

        # The test slideshow should appear in the list
        expect(
            recent_slideshows_card.locator(f"text={test_slideshow['name']}")
        ).to_be_visible(timeout=5000)

    def test_dashboard_shows_display_status(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_display: dict,
    ):
        """Test that dashboard shows display status section."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Wait for dashboard to load
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Verify Display Status card exists
        display_status_card = page.locator(".card").filter(
            has=page.locator(".card-header:has-text('Display Status')")
        )
        expect(display_status_card).to_be_visible()

        # Verify "View All" link exists
        expect(display_status_card.locator("a:has-text('View All')")).to_be_visible()

        # The test display should appear in the list with an Online/Offline badge
        expect(
            display_status_card.locator(f"text={test_display['name']}")
        ).to_be_visible(timeout=5000)

        # The display should have a status badge (either Online or Offline)
        status_badge = display_status_card.locator(".badge")
        expect(status_badge.first).to_be_visible()

    def test_quick_actions_navigate_correctly(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that quick action buttons navigate to correct pages."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Wait for dashboard to load
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Verify Quick Actions card exists
        quick_actions_card = page.locator(".card").filter(
            has=page.locator(".card-header:has-text('Quick Actions')")
        )
        expect(quick_actions_card).to_be_visible()

        # Test "Create New Slideshow" button
        create_btn = quick_actions_card.locator("a:has-text('Create New Slideshow')")
        expect(create_btn).to_be_visible()
        create_btn.click()
        expect(page).to_have_url(re.compile(r".*/admin/slideshows/new$"), timeout=10000)

        # Go back to dashboard (dashboard is at /admin, not /admin/dashboard)
        page.goto(f"{vite_url}/admin")
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Test "Manage Slideshows" button
        manage_btn = page.locator(".card:has-text('Quick Actions')").locator(
            "a:has-text('Manage Slideshows')"
        )
        expect(manage_btn).to_be_visible()
        manage_btn.click()
        expect(page).to_have_url(re.compile(r".*/admin/slideshows$"), timeout=10000)

        # Go back to dashboard
        page.goto(f"{vite_url}/admin")
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Test "Monitor Displays" button
        monitor_btn = page.locator(".card:has-text('Quick Actions')").locator(
            "a:has-text('Monitor Displays')"
        )
        expect(monitor_btn).to_be_visible()
        monitor_btn.click()
        expect(page).to_have_url(re.compile(r".*/admin/displays$"), timeout=10000)

    def test_navigation_bar_links_work(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
    ):
        """Test that navigation bar links work correctly."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Wait for dashboard to load
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible(timeout=10000)

        # Get the navigation bar
        navbar = page.locator("nav.navbar")
        expect(navbar).to_be_visible()

        # Test Slideshows nav link
        navbar.locator("a.nav-link:has-text('Slideshows')").click()
        expect(page).to_have_url(re.compile(r".*/admin/slideshows$"), timeout=10000)
        expect(page.locator("h1")).to_contain_text("Slideshow")

        # Test Displays nav link
        navbar.locator("a.nav-link:has-text('Displays')").click()
        expect(page).to_have_url(re.compile(r".*/admin/displays$"), timeout=10000)
        expect(page.locator("h1")).to_contain_text("Display")

        # Test Dashboard nav link (go back) - dashboard is at /admin
        navbar.locator("a.nav-link:has-text('Dashboard')").click()
        expect(page).to_have_url(re.compile(r".*/admin$"), timeout=10000)
        expect(page.locator("h1:has-text('Dashboard')")).to_be_visible()

        # Test System Monitoring nav link - it's at /admin/monitoring
        navbar.locator("a.nav-link:has-text('System Monitoring')").click()
        expect(page).to_have_url(re.compile(r".*/admin/monitoring$"), timeout=10000)

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        page.goto(f"{vite_url}/admin/login")
        page.wait_for_selector("input[name='username']", timeout=10000)

        user = test_database["users"][0]
        page.locator("input[name='username']").fill(user["username"])
        page.locator("input[name='password']").fill(user["password"])
        page.locator("button[type='submit']").click()

        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)
