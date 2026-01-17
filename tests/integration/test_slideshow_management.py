"""
Integration tests for slideshow management in the admin interface.

Tests the slideshow CRUD operations through a real browser:
- Viewing slideshow list (empty and with data)
- Creating new slideshows
- Editing existing slideshows
- Deleting slideshows
- Setting default slideshow

Run with: nox -s test-integration
"""

import os
import re
import time

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped",
)
class TestSlideshowManagement:
    """Test slideshow CRUD operations through the admin interface."""

    def test_view_slideshow_list_empty(
        self, enhanced_page: Page, servers: dict, test_database: dict
    ):
        """Test viewing the slideshow list when no slideshows exist."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to slideshows page
        page.goto(f"{vite_url}/admin/slideshows")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify page header
        expect(page.locator("h1")).to_contain_text("Slideshows")

        # Verify "Create New Slideshow" button exists
        create_button = page.locator("a:has-text('Create New Slideshow')")
        expect(create_button).to_be_visible()

        # Check for empty state OR slideshow table
        # (depends on whether sample data was loaded)
        empty_state = page.locator("text=No Slideshows Found")
        table = page.locator("table")

        # Either empty state or table should be visible
        assert (
            empty_state.is_visible() or table.is_visible()
        ), "Should show either empty state or slideshow table"

    def test_view_slideshow_list_with_data(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test viewing the slideshow list when slideshows exist."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to slideshows page
        page.goto(f"{vite_url}/admin/slideshows")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify page header
        expect(page.locator("h1")).to_contain_text("Slideshows")

        # Should show the table with our test slideshow
        table = page.locator("table")
        expect(table).to_be_visible(timeout=10000)

        # Verify our test slideshow appears in the table
        slideshow_name = test_slideshow["name"]
        expect(page.locator(f"text={slideshow_name}")).to_be_visible()

        # Verify table has expected columns
        headers = page.locator("th")
        header_texts = [headers.nth(i).inner_text() for i in range(headers.count())]
        assert "Name" in header_texts
        assert "Status" in header_texts
        assert "Actions" in header_texts

    def test_create_slideshow_success(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test creating a new slideshow with all form fields."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to create slideshow page
        page.goto(f"{vite_url}/admin/slideshows/new")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify form page loaded
        expect(page.locator("h1")).to_contain_text("Create New Slideshow")

        # Generate unique name
        slideshow_name = f"Test Slideshow {int(time.time() * 1000)}"

        # Fill in the form
        page.locator("#slideshow-name").fill(slideshow_name)
        page.locator("#description").fill("Test description for integration test")
        page.locator("#default-item-duration").fill("15")
        page.locator("#transition-type").select_option("slide")

        # Check the "Active" checkbox (should be checked by default, but ensure it)
        active_checkbox = page.locator("#is_active")
        if not active_checkbox.is_checked():
            active_checkbox.check()

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for navigation to slideshow detail page (not /new or /edit)
        # The detail page URL is /admin/slideshows/{id} where id is a number
        # Use expect().to_have_url() with regex for more reliable matching
        expect(page).to_have_url(re.compile(r".*/admin/slideshows/\d+$"), timeout=10000)
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for the page to load and verify we're on the detail page
        # The detail page shows the slideshow name in an h1
        expect(page.locator("h1").first).to_contain_text(slideshow_name, timeout=10000)

        # Cleanup: delete the created slideshow via API
        # Extract slideshow ID from URL
        url = page.url
        slideshow_id = url.split("/")[-1]
        if slideshow_id.isdigit():
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )

    def test_create_slideshow_validation_errors(
        self, enhanced_page: Page, servers: dict, test_database: dict
    ):
        """Test that validation errors are shown for invalid input."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to create slideshow page
        page.goto(f"{vite_url}/admin/slideshows/new")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Try to submit with empty name
        page.locator("#slideshow-name").fill("")
        page.locator("button[type='submit']").click()

        # Should show validation error
        expect(page.locator("text=Slideshow name is required")).to_be_visible(
            timeout=5000
        )

        # URL should not have changed (still on /new page)
        assert "/new" in page.url, "Should stay on form page when validation fails"

    def test_edit_slideshow(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test editing an existing slideshow."""
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to edit page
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}/edit")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify form loaded with existing data
        expect(page.locator("h1")).to_contain_text("Edit Slideshow")

        # Verify name field has the slideshow name
        name_field = page.locator("#slideshow-name")
        expect(name_field).to_have_value(test_slideshow["name"])

        # Update the description
        new_description = f"Updated description {int(time.time())}"
        page.locator("#description").fill(new_description)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for navigation to detail page
        page.wait_for_url(f"**/admin/slideshows/{slideshow_id}", timeout=10000)

        # Navigate back to edit page to verify change persisted
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}/edit")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify the description was updated
        expect(page.locator("#description")).to_have_value(new_description)

    def test_delete_slideshow_with_confirmation(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test deleting a slideshow with confirmation dialog."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create a slideshow specifically for this test
        slideshow_name = f"Delete Test {int(time.time() * 1000)}"
        response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": slideshow_name,
                "description": "Slideshow to be deleted",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        response_data = response.json().get("data", response.json())
        slideshow_id = response_data["id"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to slideshows page
        page.goto(f"{vite_url}/admin/slideshows")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Find the delete button for our slideshow
        # The row contains the slideshow name and has a delete button
        row = page.locator(f"tr:has-text('{slideshow_name}')")
        expect(row).to_be_visible(timeout=10000)

        delete_button = row.locator("button[title='Delete']")

        # Set up dialog handler to accept the confirmation
        page.on("dialog", lambda dialog: dialog.accept())

        # Click delete
        delete_button.click()

        # Wait for the slideshow to be removed from the list
        expect(page.locator(f"text={slideshow_name}")).to_be_hidden(timeout=10000)

        # Verify via API that it's actually deleted
        check_response = http_client.get(
            f"/api/v1/slideshows/{slideshow_id}",
            headers=auth_headers,
        )
        assert check_response.status_code == 404

    def test_set_slideshow_as_default(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test setting a slideshow as the default."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create a non-default slideshow for this test
        slideshow_name = f"Default Test {int(time.time() * 1000)}"
        response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": slideshow_name,
                "description": "Slideshow to be set as default",
                "is_active": True,
                "is_default": False,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        response_data = response.json().get("data", response.json())
        slideshow_id = response_data["id"]

        try:
            # Login first
            self._login(page, vite_url, test_database)

            # Navigate to slideshows page
            page.goto(f"{vite_url}/admin/slideshows")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Find the row for our slideshow
            row = page.locator(f"tr:has-text('{slideshow_name}')")
            expect(row).to_be_visible(timeout=10000)

            # Verify it doesn't have the "Default" badge yet
            # Use a specific selector for the badge to avoid matching text in the name
            default_badge = row.locator(".badge:has-text('Default')")
            # It might not be visible if not default
            initial_has_default = default_badge.is_visible()
            assert not initial_has_default, "Slideshow should not be default initially"

            # Click the "Set as Default" button (star icon)
            set_default_button = row.locator("button[title='Set as Default']")
            expect(set_default_button).to_be_visible()
            set_default_button.click()

            # Wait for the page to refresh and show the Default badge
            page.wait_for_timeout(1000)  # Allow time for API call

            # Reload the page to see updated state
            page.reload()
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Find the row again and verify it has the Default badge
            row = page.locator(f"tr:has-text('{slideshow_name}')")
            expect(row).to_be_visible(timeout=10000)
            expect(row.locator(".badge:has-text('Default')")).to_be_visible(
                timeout=5000
            )

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        # Navigate to login page
        page.goto(f"{vite_url}/admin/login")

        # Wait for login form
        page.wait_for_selector("input[name='username']", timeout=10000)

        # Get credentials
        user = test_database["users"][0]
        username = user["username"]
        password = user["password"]

        # Fill and submit
        page.locator("input[name='username']").fill(username)
        page.locator("input[name='password']").fill(password)
        page.locator("button[type='submit']").click()

        # Wait for login to complete (dashboard loads)
        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)
