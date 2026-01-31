"""
Integration tests for admin slide management, specifically for inactive slide handling.

These tests verify that:
1. Inactive slides remain visible in the admin UI (regression test for bug fix)
2. Inactive slides can be reactivated via the admin UI
3. Inactive slides are NOT shown in display playback

Tests ASI-1.1, ASI-1.2, and ASI-1.3 from the admin-slide-inactive feature.
"""

import logging
import time

import pytest
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestAdminInactiveSlides:
    """Test inactive slide visibility and management in the admin UI."""

    def test_inactive_slide_visible_in_admin_ui(
        self,
        authenticated_page: Page,
        servers: dict,
        http_client,
        auth_headers,
    ):
        """
        ASI-1.1: Verify that inactive slides remain visible in the admin UI.

        This test creates a slideshow with a slide, marks the slide as inactive,
        and verifies that the slide is still visible in the admin UI (even though
        it won't appear in display playback).

        This test should FAIL initially and PASS after the bug fix is implemented.
        """
        page = authenticated_page
        vite_url = servers["vite_url"]

        # Create a test slideshow via API
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": f"Inactive Slide Test {int(time.time() * 1000)}",
                "description": "Test slideshow for inactive slide visibility",
                "default_item_duration": 10,
                "transition_type": "fade",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create a slide that will be marked inactive
            slide_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Inactive Test Slide",
                    "content_type": "text",
                    "content_text": "This slide will be marked inactive",
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert slide_response.status_code in [200, 201]
            slide_data = slide_response.json().get("data", slide_response.json())
            slide_id = slide_data["id"]

            # Navigate to slideshow detail page and verify the slide is visible
            page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
            page.wait_for_load_state("domcontentloaded")

            # Wait for the table to load
            page.wait_for_selector("table", timeout=10000)

            # Verify the slide appears in the table
            slide_row = page.locator("tr", has_text="Inactive Test Slide")
            expect(slide_row).to_be_visible(timeout=10000)

            # Now mark the slide as inactive via API
            update_response = http_client.put(
                f"/api/v1/slideshow-items/{slide_id}",
                json={"is_active": False},
                headers=auth_headers,
            )
            assert update_response.status_code == 200

            # Refresh the page
            page.reload()
            page.wait_for_load_state("domcontentloaded")

            # Wait for the page content to load - look for the card that contains
            # either the items table or the "No Items Yet" message
            page.wait_for_selector(".card-body", timeout=10000)

            # THE KEY ASSERTION: The inactive slide should still be visible
            # This test will FAIL until the bug is fixed - currently when
            # a slide is marked inactive, the API filters it out and the
            # UI shows "No Items Yet" instead of the slide row.
            slide_row = page.locator("tr", has_text="Inactive Test Slide")
            expect(slide_row).to_be_visible(timeout=5000)

            # Additionally verify it shows as "Inactive"
            inactive_badge = slide_row.locator("text=Inactive")
            expect(inactive_badge).to_be_visible()

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}", headers=auth_headers
            )

    def test_reactivate_inactive_slide_via_admin_ui(
        self,
        authenticated_page: Page,
        servers: dict,
        http_client,
        auth_headers,
    ):
        """
        ASI-1.2: Verify that inactive slides can be reactivated via the admin UI.

        This test creates a slideshow with an inactive slide, then uses the
        admin UI to reactivate the slide and verifies the change persists.

        This test should FAIL initially and PASS after the bug fix is implemented.
        """
        page = authenticated_page
        vite_url = servers["vite_url"]

        # Create a test slideshow via API
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": f"Reactivate Slide Test {int(time.time() * 1000)}",
                "description": "Test slideshow for reactivating inactive slides",
                "default_item_duration": 10,
                "transition_type": "fade",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create a slide that starts as INACTIVE
            slide_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Slide To Reactivate",
                    "content_type": "text",
                    "content_text": "This slide starts inactive and will be reactivated",
                    "is_active": False,  # Start as inactive
                },
                headers=auth_headers,
            )
            assert slide_response.status_code in [200, 201]
            slide_data = slide_response.json().get("data", slide_response.json())
            slide_id = slide_data["id"]

            # Navigate to slideshow detail page
            page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
            page.wait_for_load_state("domcontentloaded")

            # Wait for the page content to load - look for the card that contains
            # either the items table or the "No Items Yet" message
            page.wait_for_selector(".card-body", timeout=10000)

            # THE KEY ASSERTION: The inactive slide should be visible
            # This will FAIL until the bug is fixed - the slide is created
            # with is_active=False, and the API filters it out, so we see
            # "No Items Yet" instead of the slide row.
            slide_row = page.locator("tr", has_text="Slide To Reactivate")
            expect(slide_row).to_be_visible(timeout=5000)

            # Click the edit button for this slide
            edit_button = slide_row.locator("button[title='Edit']")
            expect(edit_button).to_be_visible()
            edit_button.click()

            # Wait for the modal to appear
            modal = page.locator(".modal")
            expect(modal).to_be_visible(timeout=10000)

            # Find and check the "Active" checkbox/toggle to reactivate
            # The form should have an is_active field
            active_checkbox = modal.locator(
                "input[name='is_active'], input[type='checkbox']"
            ).first
            expect(active_checkbox).to_be_visible()

            # If it's unchecked (inactive), check it to activate
            if not active_checkbox.is_checked():
                active_checkbox.check()

            # Submit the form
            submit_button = modal.locator(
                "button[type='submit'], button:has-text('Save')"
            ).first
            submit_button.click()

            # Wait for modal to close
            expect(modal).to_be_hidden(timeout=10000)

            # Wait for the data to refresh after save
            page.wait_for_timeout(500)  # Brief wait for API response

            # Verify the slide now shows as "Active"
            slide_row = page.locator("tr", has_text="Slide To Reactivate")
            active_badge = slide_row.locator(".badge", has_text="Active")
            expect(active_badge).to_be_visible()

            # Also verify via API that the slide is now active
            get_response = http_client.get(
                f"/api/v1/slideshow-items/{slide_id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200
            updated_slide = get_response.json().get("data", get_response.json())
            assert updated_slide["is_active"] is True

        finally:
            # Cleanup
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}", headers=auth_headers
            )


@pytest.mark.integration
class TestDisplayPlaybackInactiveSlides:
    """Test that inactive slides are NOT shown in display playback."""

    def test_inactive_slides_not_shown_in_display_playback(
        self,
        enhanced_page: Page,
        servers: dict,
        http_client,
        auth_headers,
    ):
        """
        ASI-1.3: Verify that inactive slides are NOT included in slideshow display.

        This test creates a slideshow with both active and inactive slides,
        assigns it to a display, and verifies that only active slides appear
        during playback.

        This test should PASS already (the display playback correctly filters
        inactive slides).
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Create a test slideshow
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": f"Playback Filter Test {int(time.time() * 1000)}",
                "description": "Test that inactive slides don't appear in playback",
                "default_item_duration": 3,  # Short duration for faster testing
                "transition_type": "none",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create an ACTIVE slide (should appear)
            active_slide_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Active Slide",
                    "content_type": "text",
                    "content_text": "VISIBLE_ACTIVE_CONTENT",
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert active_slide_response.status_code in [200, 201]

            # Create an INACTIVE slide (should NOT appear)
            inactive_slide_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Inactive Slide",
                    "content_type": "text",
                    "content_text": "HIDDEN_INACTIVE_CONTENT",
                    "is_active": False,  # This slide should NOT appear
                },
                headers=auth_headers,
            )
            assert inactive_slide_response.status_code in [200, 201]

            # Create another ACTIVE slide (should appear)
            active_slide2_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Another Active Slide",
                    "content_type": "text",
                    "content_text": "VISIBLE_ACTIVE_CONTENT_2",
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert active_slide2_response.status_code in [200, 201]

            # Create a display and assign the slideshow
            display_name = f"test-playback-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for inactive slide filtering",
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Navigate to the display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Wait for slideshow container to appear
                page.wait_for_selector("#slideshowContainer", timeout=10000)

                # Give it time to cycle through slides (with 3 second duration)
                # We'll wait and check multiple times over 15 seconds
                inactive_content_found = False
                active_content_found = False

                for _ in range(5):  # Check 5 times over ~15 seconds
                    page_content = page.content()

                    if "HIDDEN_INACTIVE_CONTENT" in page_content:
                        inactive_content_found = True
                        break

                    if "VISIBLE_ACTIVE_CONTENT" in page_content:
                        active_content_found = True

                    time.sleep(3)  # Wait for potential slide transition

                # ASSERTIONS
                # The inactive slide content should NEVER appear
                assert not inactive_content_found, (
                    "Inactive slide content was found in display playback! "
                    "Inactive slides should be filtered out."
                )

                # At least one active slide should have appeared
                assert active_content_found, (
                    "Active slide content was not found in display playback. "
                    "Something may be wrong with the test setup."
                )

            finally:
                # Cleanup display
                http_client.delete(
                    f"/api/v1/displays/{display_id}", headers=auth_headers
                )

        finally:
            # Cleanup slideshow
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}", headers=auth_headers
            )
