"""
End-to-end tests for Dashboard page navigation links.

These tests verify that navigation links and Quick Actions buttons
on the Dashboard page work correctly and navigate to the expected URLs.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestDashboardNavigation:
    """Test Dashboard page navigation links and buttons."""

    def _login_user(self, page: Page, live_server_url: str, credentials: dict):
        """Helper to log in a test user."""
        page.goto(live_server_url)

        # Fill in login credentials
        username_field = page.locator(
            "input[name='username'], input[type='text'], "
            "input[placeholder*='username' i]"
        ).first
        password_field = page.locator(
            "input[name='password'], input[type='password']"
        ).first

        username_field.fill(credentials["username"])
        password_field.fill(credentials["password"])

        # Submit login form
        submit_button = page.locator(
            "button[type='submit'], input[type='submit'], "
            "button:has-text('Login'), button:has-text('Sign In')"
        ).first
        submit_button.click()

        # Wait for navigation to complete
        page.wait_for_load_state("networkidle")

    def test_navbar_slideshows_link_href(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that the Slideshows link in the navbar has the correct href."""
        self._login_user(page, live_server_url, test_credentials)

        # Find the Slideshows link in the navbar
        slideshows_link = page.locator("nav a:has-text('Slideshows')").first

        expect(slideshows_link).to_be_visible()
        expect(slideshows_link).to_have_attribute("href", "/admin/slideshows")

        print("✓ Navbar Slideshows link has correct href")

    def test_navbar_displays_link_href(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that the Displays link in the navbar has the correct href."""
        self._login_user(page, live_server_url, test_credentials)

        # Find the Displays link in the navbar
        displays_link = page.locator("nav a:has-text('Displays')").first

        expect(displays_link).to_be_visible()
        expect(displays_link).to_have_attribute("href", "/admin/displays")

        print("✓ Navbar Displays link has correct href")

    def test_quick_action_manage_slideshows_href(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that the Manage Slideshows Quick Action has the correct href."""
        self._login_user(page, live_server_url, test_credentials)

        # Find the Manage Slideshows button in Quick Actions
        manage_slideshows_btn = page.locator("a.btn:has-text('Manage Slideshows')")

        expect(manage_slideshows_btn).to_be_visible()
        expect(manage_slideshows_btn).to_have_attribute("href", "/admin/slideshows")

        print("✓ Quick Action 'Manage Slideshows' has correct href")

    def test_quick_action_view_displays_href(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that the View Displays Quick Action has the correct href."""
        self._login_user(page, live_server_url, test_credentials)

        # Find the View Displays button in Quick Actions
        view_displays_btn = page.locator("a.btn:has-text('View Displays')")

        expect(view_displays_btn).to_be_visible()
        expect(view_displays_btn).to_have_attribute("href", "/admin/displays")

        print("✓ Quick Action 'View Displays' has correct href")

    def test_quick_action_settings_link(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that the Settings Quick Action link works correctly."""
        self._login_user(page, live_server_url, test_credentials)

        # Find the Settings button in Quick Actions
        settings_btn = page.locator("a.btn:has-text('Settings')")

        expect(settings_btn).to_be_visible()
        expect(settings_btn).to_have_attribute("href", "/settings")

        print("✓ Quick Action 'Settings' has correct href")

    def test_quick_action_profile_link(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that the Profile Quick Action link works correctly."""
        self._login_user(page, live_server_url, test_credentials)

        # Find the Profile button in Quick Actions
        profile_btn = page.locator("a.btn:has-text('Profile')")

        expect(profile_btn).to_be_visible()
        expect(profile_btn).to_have_attribute("href", "/profile")

        print("✓ Quick Action 'Profile' has correct href")

    def test_navbar_slideshows_link_navigation(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that clicking the Slideshows link navigates correctly."""
        self._login_user(page, live_server_url, test_credentials)

        # Click the Slideshows link in the navbar
        slideshows_link = page.locator("nav a:has-text('Slideshows')").first
        slideshows_link.click()

        # Wait for navigation
        page.wait_for_load_state("networkidle")

        # Should navigate to /admin/slideshows
        expect(page).to_have_url(f"{live_server_url}/admin/slideshows")

        print("✓ Navbar Slideshows link navigates correctly")

    def test_navbar_displays_link_navigation(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that clicking the Displays link navigates correctly."""
        self._login_user(page, live_server_url, test_credentials)

        # Click the Displays link in the navbar
        displays_link = page.locator("nav a:has-text('Displays')").first
        displays_link.click()

        # Wait for navigation
        page.wait_for_load_state("networkidle")

        # Should navigate to /admin/displays
        expect(page).to_have_url(f"{live_server_url}/admin/displays")

        print("✓ Navbar Displays link navigates correctly")


@pytest.mark.e2e
class TestDashboardLinksNotBroken:
    """Test that Dashboard links don't point to broken /api/ URLs."""

    def _login_user(self, page: Page, live_server_url: str, credentials: dict):
        """Helper to log in a test user."""
        page.goto(live_server_url)

        username_field = page.locator(
            "input[name='username'], input[type='text'], "
            "input[placeholder*='username' i]"
        ).first
        password_field = page.locator(
            "input[name='password'], input[type='password']"
        ).first

        username_field.fill(credentials["username"])
        password_field.fill(credentials["password"])

        submit_button = page.locator(
            "button[type='submit'], input[type='submit'], "
            "button:has-text('Login'), button:has-text('Sign In')"
        ).first
        submit_button.click()

        page.wait_for_load_state("networkidle")

    def test_no_links_to_api_root(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that no links on the Dashboard point to /api/ (broken)."""
        self._login_user(page, live_server_url, test_credentials)

        # Find all links on the page
        all_links = page.locator("a[href]").all()

        broken_links = []
        for link in all_links:
            href = link.get_attribute("href")
            # Check for broken /api/ or /api/slideshows or /api/displays links
            if href and (
                href == "/api/"
                or href.startswith("/api/slideshows")
                or href.startswith("/api/displays")
            ):
                text = link.text_content() or ""
                broken_links.append(f"{text.strip()}: {href}")

        assert (
            not broken_links
        ), f"Found links pointing to broken /api/ URLs: {broken_links}"

        print("✓ No links point to broken /api/ URLs")

    def test_navbar_links_not_pointing_to_api(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that navbar links don't point to /api/ endpoints."""
        self._login_user(page, live_server_url, test_credentials)

        # Check Slideshows link
        slideshows_link = page.locator("nav a:has-text('Slideshows')").first
        slideshows_href = slideshows_link.get_attribute("href")
        assert (
            slideshows_href != "/api/slideshows"
        ), f"Slideshows link should not point to /api/slideshows, got: {slideshows_href}"

        # Check Displays link
        displays_link = page.locator("nav a:has-text('Displays')").first
        displays_href = displays_link.get_attribute("href")
        assert (
            displays_href != "/api/displays"
        ), f"Displays link should not point to /api/displays, got: {displays_href}"

        print("✓ Navbar links don't point to /api/ endpoints")

    def test_quick_actions_not_pointing_to_api(
        self,
        page: Page,
        live_server_url: str,
        e2e_data,
        test_credentials: dict,
    ):
        """Test that Quick Action buttons don't point to /api/ endpoints."""
        self._login_user(page, live_server_url, test_credentials)

        # Check Manage Slideshows button
        manage_btn = page.locator("a.btn:has-text('Manage Slideshows')")
        manage_href = manage_btn.get_attribute("href")
        assert (
            manage_href != "/api/"
        ), f"Manage Slideshows should not point to /api/, got: {manage_href}"

        # Check View Displays button
        view_btn = page.locator("a.btn:has-text('View Displays')")
        view_href = view_btn.get_attribute("href")
        assert (
            view_href != "/api/"
        ), f"View Displays should not point to /api/, got: {view_href}"

        print("✓ Quick Action buttons don't point to /api/ endpoints")
