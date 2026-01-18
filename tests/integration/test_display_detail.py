"""
Integration tests for display detail page in the admin interface.

Tests display detail view, editing, quick assignment, and history:
- View display detail page
- Edit display information
- Quick assign slideshow via click
- Unassign slideshow
- Assignment history section displays

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
class TestDisplayDetail:
    """Test display detail page through the admin interface."""

    def test_view_display_detail_page(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_display: dict,
    ):
        """Test viewing the display detail page."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to display detail page
        display_id = test_display["id"]
        page.goto(f"{vite_url}/admin/displays/{display_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify page header shows "Display Details"
        expect(page.locator("h1:has-text('Display Details')")).to_be_visible(
            timeout=10000
        )

        # Verify breadcrumb navigation exists with Displays link
        breadcrumb = page.locator("nav[aria-label='breadcrumb']")
        expect(breadcrumb).to_be_visible()
        expect(breadcrumb.locator("a:has-text('Displays')")).to_be_visible()

        # Verify display name is shown in breadcrumb (second breadcrumb item)
        expect(
            breadcrumb.locator(f".breadcrumb-item:has-text('{test_display['name']}')")
        ).to_be_visible()

        # Verify Display Information card exists
        expect(page.locator("text=Display Information")).to_be_visible()

        # Verify display name is shown in the details table
        expect(page.locator("td:has-text('Name:')")).to_be_visible()

        # Verify Status card exists
        expect(page.locator("text=Status")).to_be_visible()
        expect(page.locator("text=Connection:")).to_be_visible()

        # Verify Quick Assignment card exists
        expect(page.locator("text=Quick Assignment")).to_be_visible()

        # Verify Edit Display button exists
        expect(page.locator("button:has-text('Edit Display')")).to_be_visible()

    def test_edit_display_information(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test editing display information."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create a display to edit
        response = http_client.post(
            "/api/v1/displays",
            json={"name": "Display To Edit", "location": "Original Location"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        display_data = response.json().get("data", response.json())
        display_id = display_data["id"]

        try:
            # Login and navigate to display detail page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays/{display_id}")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for the page to load
            expect(page.locator("h1:has-text('Display Details')")).to_be_visible(
                timeout=10000
            )

            # Click Edit Display button
            edit_button = page.locator("button:has-text('Edit Display')")
            expect(edit_button).to_be_visible()
            edit_button.click()

            # Verify edit form is shown (Save Changes button appears)
            expect(page.locator("button:has-text('Save Changes')")).to_be_visible(
                timeout=5000
            )

            # Verify Cancel button is shown
            expect(page.locator("button:has-text('Cancel')")).to_be_visible()

            # Modify the location field
            location_input = page.locator("input#location")
            expect(location_input).to_be_visible()
            location_input.fill("Updated Location")

            # Modify the description field
            description_input = page.locator("textarea#description")
            expect(description_input).to_be_visible()
            description_input.fill("Updated description for display")

            # Click Save Changes
            page.locator("button:has-text('Save Changes')").click()

            # Verify success message appears
            expect(page.locator("text=Display updated successfully")).to_be_visible(
                timeout=10000
            )

            # Verify the updated values are shown (edit mode should be exited)
            expect(page.locator("button:has-text('Edit Display')")).to_be_visible(
                timeout=5000
            )

            # Verify via API that changes were saved
            verify_response = http_client.get(
                f"/api/v1/displays/{display_id}", headers=auth_headers
            )
            assert verify_response.status_code == 200
            updated_display = verify_response.json().get("data", verify_response.json())
            assert updated_display["location"] == "Updated Location"
            assert updated_display["description"] == "Updated description for display"

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display_id}", headers=auth_headers
            )

    @pytest.mark.xfail(
        reason="Bug: Display API doesn't return assigned_slideshow object. "
        "The frontend DisplayDetail component expects display.assigned_slideshow "
        "but the API only returns current_slideshow_id. "
        "See docs/features/fix-display-assigned-slideshow-api-bug.md for details."
    )
    def test_quick_assign_slideshow_via_click(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test quick assigning a slideshow by clicking on it."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create an unassigned display
        response = http_client.post(
            "/api/v1/displays",
            json={"name": "Display For Quick Assign", "location": "Test"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        display_data = response.json().get("data", response.json())
        display_id = display_data["id"]

        try:
            # Login and navigate to display detail page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays/{display_id}")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for Quick Assignment card to load
            quick_assign_card = page.locator(".card:has-text('Quick Assignment')")
            expect(quick_assign_card).to_be_visible(timeout=10000)
            expect(quick_assign_card.locator("text=Available Slideshows:")).to_be_visible(
                timeout=5000
            )

            # Verify no slideshow is currently assigned (shows "Drop slideshow here")
            expect(
                quick_assign_card.locator("text=Drop slideshow here or use form above")
            ).to_be_visible()

            # Find and click on the test slideshow in the available list
            # The slideshows are shown as clickable div items with strong tags for names
            slideshow_item = quick_assign_card.locator(
                f".available-slideshows div:has(strong:has-text('{test_slideshow['name']}'))"
            ).first
            expect(slideshow_item).to_be_visible(timeout=5000)
            slideshow_item.click()

            # Verify success message appears
            expect(page.locator(".alert-success:has-text('assigned successfully')")).to_be_visible(
                timeout=10000
            )

            # Wait a moment for the UI to refresh
            page.wait_for_timeout(500)

            # Verify via API that assignment was saved
            verify_response = http_client.get(
                f"/api/v1/displays/{display_id}", headers=auth_headers
            )
            assert verify_response.status_code == 200
            updated_display = verify_response.json().get("data", verify_response.json())
            assert updated_display["current_slideshow_id"] == test_slideshow["id"]

            # Verify the "Drop slideshow here" message is no longer visible
            # (indicating something is now assigned)
            expect(
                quick_assign_card.locator("text=Drop slideshow here or use form above")
            ).to_be_hidden(timeout=5000)

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display_id}", headers=auth_headers
            )

    @pytest.mark.xfail(
        reason="Bug: Display API doesn't return assigned_slideshow object. "
        "The frontend DisplayDetail component expects display.assigned_slideshow "
        "but the API only returns current_slideshow_id. "
        "See docs/features/fix-display-assigned-slideshow-api-bug.md for details."
    )
    def test_unassign_slideshow(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test unassigning a slideshow from a display."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create a display with an assigned slideshow
        response = http_client.post(
            "/api/v1/displays",
            json={
                "name": "Display For Unassign",
                "location": "Test",
                "current_slideshow_id": test_slideshow["id"],
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        display_data = response.json().get("data", response.json())
        display_id = display_data["id"]

        try:
            # Login and navigate to display detail page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays/{display_id}")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for Quick Assignment card to load
            quick_assign_card = page.locator(".card:has-text('Quick Assignment')")
            expect(quick_assign_card).to_be_visible(timeout=10000)

            # Verify something is currently assigned (the unassign button should be visible)
            # The unassign button only appears when a slideshow is assigned
            unassign_button = quick_assign_card.locator("button[title='Remove Assignment']")
            expect(unassign_button).to_be_visible(timeout=5000)

            # Click the unassign button
            unassign_button.click()

            # Verify success message appears
            expect(page.locator(".alert-success:has-text('unassigned successfully')")).to_be_visible(
                timeout=10000
            )

            # Verify the display now shows no assignment
            expect(
                quick_assign_card.locator("text=Drop slideshow here or use form above")
            ).to_be_visible(timeout=5000)

            # Verify via API that unassignment was saved
            verify_response = http_client.get(
                f"/api/v1/displays/{display_id}", headers=auth_headers
            )
            assert verify_response.status_code == 200
            updated_display = verify_response.json().get("data", verify_response.json())
            assert updated_display["current_slideshow_id"] is None

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display_id}", headers=auth_headers
            )

    def test_assignment_history_section_displays(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_display: dict,
    ):
        """Test that assignment history section is displayed."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to display detail page
        display_id = test_display["id"]
        page.goto(f"{vite_url}/admin/displays/{display_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for the page to load
        expect(page.locator("h1:has-text('Display Details')")).to_be_visible(
            timeout=10000
        )

        # Find the Assignment History card (not the nav item)
        # Scroll down to find it since it's at the bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)

        # Verify Assignment History card exists with its header
        history_card = page.locator(".card").filter(
            has=page.locator(".card-header:has-text('Assignment History')")
        )
        expect(history_card).to_be_visible(timeout=5000)

        # Verify "View All History" link exists in the card
        expect(history_card.locator("a:has-text('View All History')")).to_be_visible()

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        page.goto(f"{vite_url}/admin/login")
        page.wait_for_selector("input[name='username']", timeout=10000)

        user = test_database["users"][0]
        page.locator("input[name='username']").fill(user["username"])
        page.locator("input[name='password']").fill(user["password"])
        page.locator("button[type='submit']").click()

        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)
