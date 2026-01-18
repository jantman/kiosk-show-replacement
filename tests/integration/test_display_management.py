"""
Integration tests for display management in the admin interface.

Tests display listing, searching, filtering, assignment, and deletion:
- View display list (empty state and with data)
- Search displays by name
- Filter displays by status (online/offline)
- Filter displays by assignment status
- Assign slideshow to single display
- Bulk assign slideshow to multiple displays
- Delete display with confirmation

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
class TestDisplayManagement:
    """Test display management through the admin interface."""

    def test_view_display_list_empty(
        self, enhanced_page: Page, servers: dict, test_database: dict
    ):
        """Test viewing the display list when no displays exist."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to displays page
        page.goto(f"{vite_url}/admin/displays")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify page header
        expect(page.locator("h1")).to_contain_text("Display")

        # Check for empty state message or table
        # Note: The page may show "No displays found" or an empty table
        empty_state = page.locator("text=No displays found")
        table = page.locator("table")

        # Either empty state or table should be visible
        assert (
            empty_state.is_visible() or table.is_visible()
        ), "Should show either empty state or displays table"

    def test_view_display_list_with_data(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_display: dict,
    ):
        """Test viewing the display list when displays exist."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Login first
        self._login(page, vite_url, test_database)

        # Navigate to displays page
        page.goto(f"{vite_url}/admin/displays")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify page header
        expect(page.locator("h1")).to_contain_text("Display")

        # Should show the table with our test display
        table = page.locator("table")
        expect(table).to_be_visible(timeout=10000)

        # Verify our test display appears in the table
        display_name = test_display["name"]
        expect(page.locator(f"text={display_name}")).to_be_visible()

    def test_search_displays_by_name(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test searching displays by name."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create displays with different names via API
        display1 = http_client.post(
            "/api/v1/displays",
            json={"name": "Kitchen Display", "location": "Kitchen"},
            headers=auth_headers,
        )
        assert display1.status_code in [200, 201]
        display1_data = display1.json().get("data", display1.json())

        display2 = http_client.post(
            "/api/v1/displays",
            json={"name": "Living Room Display", "location": "Living Room"},
            headers=auth_headers,
        )
        assert display2.status_code in [200, 201]
        display2_data = display2.json().get("data", display2.json())

        try:
            # Login and navigate to displays page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for table to load
            expect(page.locator("table")).to_be_visible(timeout=10000)

            # Both displays should be visible initially
            expect(page.locator("text=Kitchen Display")).to_be_visible()
            expect(page.locator("text=Living Room Display")).to_be_visible()

            # Search for "Kitchen"
            search_input = page.locator("input[placeholder*='Search']")
            expect(search_input).to_be_visible()
            search_input.fill("Kitchen")

            # Wait for filter to apply
            page.wait_for_timeout(500)

            # Kitchen display should be visible, Living Room should not
            expect(page.locator("text=Kitchen Display")).to_be_visible()
            expect(page.locator("text=Living Room Display")).to_be_hidden()

            # Clear search
            search_input.fill("")
            page.wait_for_timeout(500)

            # Both should be visible again
            expect(page.locator("text=Kitchen Display")).to_be_visible()
            expect(page.locator("text=Living Room Display")).to_be_visible()

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display1_data['id']}", headers=auth_headers
            )
            http_client.delete(
                f"/api/v1/displays/{display2_data['id']}", headers=auth_headers
            )

    def test_filter_displays_by_status(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test filtering displays by online/offline status."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create a display via API (it will be offline by default)
        response = http_client.post(
            "/api/v1/displays",
            json={"name": "Status Test Display", "location": "Test"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        display_data = response.json().get("data", response.json())

        try:
            # Login and navigate to displays page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for table to load
            expect(page.locator("table")).to_be_visible(timeout=10000)

            # Display should be visible with "Offline" status
            expect(page.locator("text=Status Test Display")).to_be_visible()

            # Find status filter dropdown
            status_filter = page.locator("select").filter(has_text="All Status").first
            if not status_filter.is_visible():
                # Try alternative selector
                status_filter = page.locator("select").first

            # Filter for "Online Only"
            status_filter.select_option("online")
            page.wait_for_timeout(500)

            # Our offline display should be hidden
            expect(page.locator("text=Status Test Display")).to_be_hidden()

            # Filter for "Offline Only"
            status_filter.select_option("offline")
            page.wait_for_timeout(500)

            # Our offline display should be visible
            expect(page.locator("text=Status Test Display")).to_be_visible()

            # Reset to "All Status"
            status_filter.select_option("all")
            page.wait_for_timeout(500)

            # Display should be visible again
            expect(page.locator("text=Status Test Display")).to_be_visible()

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display_data['id']}", headers=auth_headers
            )

    def test_filter_displays_by_assignment_status(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test filtering displays by assigned/unassigned status."""
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create an assigned display
        assigned_response = http_client.post(
            "/api/v1/displays",
            json={
                "name": "Assigned Display",
                "location": "Assigned",
                "current_slideshow_id": slideshow_id,
            },
            headers=auth_headers,
        )
        assert assigned_response.status_code in [200, 201]
        assigned_data = assigned_response.json().get("data", assigned_response.json())

        # Create an unassigned display
        unassigned_response = http_client.post(
            "/api/v1/displays",
            json={"name": "Unassigned Display", "location": "Unassigned"},
            headers=auth_headers,
        )
        assert unassigned_response.status_code in [200, 201]
        unassigned_data = unassigned_response.json().get(
            "data", unassigned_response.json()
        )

        try:
            # Login and navigate to displays page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for table to load
            expect(page.locator("table")).to_be_visible(timeout=10000)

            # Use row-based locators to avoid matching partial text
            # "Assigned Display" must not match "Unassigned Display"
            assigned_row = page.locator("tr:has-text('Assigned Display')").filter(
                has_not_text="Unassigned"
            )
            unassigned_row = page.locator("tr:has-text('Unassigned Display')")

            # Both displays should be visible initially
            expect(assigned_row).to_be_visible()
            expect(unassigned_row).to_be_visible()

            # Find assignment filter dropdown (second select or one with "All Assignments")
            assignment_filter = (
                page.locator("select").filter(has_text="All Assignments").first
            )
            if not assignment_filter.is_visible():
                # Try getting second select
                assignment_filter = page.locator("select").nth(1)

            # Filter for "Assigned Only"
            assignment_filter.select_option("assigned")
            page.wait_for_timeout(500)

            # Only assigned display should be visible
            expect(assigned_row).to_be_visible()
            expect(unassigned_row).to_be_hidden()

            # Filter for "Unassigned Only"
            assignment_filter.select_option("unassigned")
            page.wait_for_timeout(500)

            # Only unassigned display should be visible
            expect(assigned_row).to_be_hidden()
            expect(unassigned_row).to_be_visible()

            # Reset to "All Assignments"
            assignment_filter.select_option("all")
            page.wait_for_timeout(500)

            # Both should be visible again
            expect(assigned_row).to_be_visible()
            expect(unassigned_row).to_be_visible()

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{assigned_data['id']}", headers=auth_headers
            )
            http_client.delete(
                f"/api/v1/displays/{unassigned_data['id']}", headers=auth_headers
            )

    def test_assign_slideshow_to_single_display(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test assigning a slideshow to a single display."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create an unassigned display
        response = http_client.post(
            "/api/v1/displays",
            json={"name": "Display To Assign", "location": "Test"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        display_data = response.json().get("data", response.json())

        try:
            # Login and navigate to displays page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for table to load
            expect(page.locator("table")).to_be_visible(timeout=10000)

            # Find the row for our display
            row = page.locator("tr:has-text('Display To Assign')")
            expect(row).to_be_visible(timeout=10000)

            # Click the assign button (may be in a dropdown or direct button)
            assign_button = row.locator("button[title*='Assign']")
            if not assign_button.is_visible():
                # Try dropdown menu
                row.locator("button.dropdown-toggle").click()
                assign_button = page.locator("text=Assign Slideshow")
            assign_button.click()

            # Wait for modal to appear
            modal = page.locator(".modal")
            expect(modal).to_be_visible(timeout=5000)

            # Select the slideshow
            slideshow_select = page.locator("#slideshow-select")
            expect(slideshow_select).to_be_visible()
            slideshow_select.select_option(str(test_slideshow["id"]))

            # Submit the assignment
            page.locator("button:has-text('Assign')").click()

            # Wait for modal to close
            expect(modal).to_be_hidden(timeout=10000)

            # Verify the slideshow is now shown in the display row
            page.wait_for_timeout(1000)  # Allow time for UI update
            page.reload()
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Find the row again and verify it shows the slideshow
            row = page.locator("tr:has-text('Display To Assign')")
            expect(row).to_be_visible()
            expect(row.locator(f"text={test_slideshow['name']}")).to_be_visible()

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display_data['id']}", headers=auth_headers
            )

    def test_bulk_assign_slideshow_to_multiple_displays(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test bulk assigning a slideshow to multiple displays."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create multiple unassigned displays
        display1_response = http_client.post(
            "/api/v1/displays",
            json={"name": "Bulk Display 1", "location": "Test 1"},
            headers=auth_headers,
        )
        assert display1_response.status_code in [200, 201]
        display1_data = display1_response.json().get("data", display1_response.json())

        display2_response = http_client.post(
            "/api/v1/displays",
            json={"name": "Bulk Display 2", "location": "Test 2"},
            headers=auth_headers,
        )
        assert display2_response.status_code in [200, 201]
        display2_data = display2_response.json().get("data", display2_response.json())

        try:
            # Login and navigate to displays page
            self._login(page, vite_url, test_database)
            page.goto(f"{vite_url}/admin/displays")
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            # Wait for table to load
            expect(page.locator("table")).to_be_visible(timeout=10000)

            # Find and check the checkboxes for both displays
            row1 = page.locator("tr:has-text('Bulk Display 1')")
            row2 = page.locator("tr:has-text('Bulk Display 2')")
            expect(row1).to_be_visible(timeout=10000)
            expect(row2).to_be_visible(timeout=10000)

            # Check both checkboxes
            row1.locator("input[type='checkbox']").check()
            row2.locator("input[type='checkbox']").check()

            # Click the Bulk Assign button
            bulk_assign_button = page.locator("button:has-text('Bulk Assign')")
            expect(bulk_assign_button).to_be_visible()
            bulk_assign_button.click()

            # Wait for modal to appear (bulk assign modal)
            modal = page.locator(".modal")
            expect(modal).to_be_visible(timeout=5000)

            # Select the slideshow (bulk modal doesn't have id on select)
            slideshow_select = modal.locator("select")
            expect(slideshow_select).to_be_visible()
            slideshow_select.select_option(str(test_slideshow["id"]))

            # Submit the bulk assignment
            modal.locator("button[type='submit']").click()

            # Wait for modal to close
            expect(modal).to_be_hidden(timeout=10000)

            # Verify both displays now show the slideshow
            page.wait_for_timeout(1000)
            page.reload()
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            row1 = page.locator("tr:has-text('Bulk Display 1')")
            row2 = page.locator("tr:has-text('Bulk Display 2')")
            expect(row1.locator(f"text={test_slideshow['name']}")).to_be_visible()
            expect(row2.locator(f"text={test_slideshow['name']}")).to_be_visible()

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/displays/{display1_data['id']}", headers=auth_headers
            )
            http_client.delete(
                f"/api/v1/displays/{display2_data['id']}", headers=auth_headers
            )

    @pytest.mark.xfail(
        reason="Bug: Delete display fails with 500 when display has assignment history. "
        "The AssignmentHistory table has a foreign key to displays without CASCADE DELETE. "
        "See docs/features/fix-display-delete-assignment-history-bug.md for details."
    )
    def test_delete_display_with_confirmation(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test deleting a display with confirmation dialog."""
        page = enhanced_page
        vite_url = servers["vite_url"]

        # Create a display to delete
        response = http_client.post(
            "/api/v1/displays",
            json={"name": "Display To Delete", "location": "Test"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        display_data = response.json().get("data", response.json())
        display_id = display_data["id"]

        # Login and navigate to displays page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/displays")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for table to load
        expect(page.locator("table")).to_be_visible(timeout=10000)

        # Find the row for our display
        row = page.locator("tr:has-text('Display To Delete')")
        expect(row).to_be_visible(timeout=10000)

        # Set up dialog handler to accept the confirmation
        def handle_dialog(dialog):
            dialog.accept()

        page.on("dialog", handle_dialog)

        # Click the delete button
        delete_button = row.locator("button[title='Delete Display']")
        expect(delete_button).to_be_visible()
        delete_button.click()

        # Wait for the display to be removed from the list
        # After delete, loadData() is called which refreshes the list
        expect(row).to_be_hidden(timeout=10000)

        # Verify via API that it's actually deleted
        check_response = http_client.get(
            f"/api/v1/displays/{display_id}",
            headers=auth_headers,
        )
        assert check_response.status_code == 404

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        page.goto(f"{vite_url}/admin/login")
        page.wait_for_selector("input[name='username']", timeout=10000)

        user = test_database["users"][0]
        page.locator("input[name='username']").fill(user["username"])
        page.locator("input[name='password']").fill(user["password"])
        page.locator("button[type='submit']").click()

        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)
