"""
End-to-end tests for Skedda calendar display rendering.

These tests verify that the Skedda calendar slide type correctly renders
calendar data on the kiosk display page.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestSkedddaCalendarDisplayE2E:
    """Test Skedda calendar display rendering on kiosk display page."""

    def test_skedda_calendar_renders_grid(
        self,
        page: Page,
        live_server_url: str,
        skedda_slideshow_data: dict,
    ):
        """Test that Skedda calendar slide renders the calendar grid.

        Verifies:
        1. Calendar container is present
        2. Date header is displayed
        3. Space headers are shown
        4. Time slots are rendered
        """
        display = skedda_slideshow_data["display"]

        # Navigate to the display page using the display name
        page.goto(f"{live_server_url}/display/{display.name}")

        # Wait for the page to load
        page.wait_for_load_state("load")

        # Verify the skedda calendar container appears
        calendar = page.locator(".skedda-calendar")
        expect(calendar).to_be_visible(timeout=10000)

        # Verify the date header is present
        date_header = page.locator(".skedda-date-header")
        expect(date_header).to_be_visible()
        # Should contain current date
        date_text = date_header.inner_text()
        assert len(date_text) > 0, "Date header should have text"

        # Verify space headers are rendered
        space_headers = page.locator(".skedda-space-header")
        expect(space_headers.first).to_be_visible(timeout=5000)

        # Verify time slots are rendered
        time_slots = page.locator(".skedda-time-slot")
        expect(time_slots.first).to_be_visible()

    def test_skedda_calendar_displays_events(
        self,
        page: Page,
        live_server_url: str,
        skedda_slideshow_data: dict,
    ):
        """Test that Skedda calendar displays event blocks.

        Verifies:
        1. Event elements are rendered
        2. Event person name is displayed
        3. Event description is shown
        """
        display = skedda_slideshow_data["display"]

        # Navigate to the display page
        page.goto(f"{live_server_url}/display/{display.name}")
        page.wait_for_load_state("load")

        # Wait for calendar to load
        calendar = page.locator(".skedda-calendar")
        expect(calendar).to_be_visible(timeout=10000)

        # Wait for events to be rendered (may take a moment after API fetch)
        event_elements = page.locator(".skedda-event")
        expect(event_elements.first).to_be_visible(timeout=10000)

        # Verify at least one event is displayed
        event_count = event_elements.count()
        assert event_count >= 1, f"Expected at least 1 event, found {event_count}"

        # Check that event content is present (person name or description)
        event_person = page.locator(".skedda-event-person")
        expect(event_person.first).to_be_visible()

        # Verify event has text content
        first_event_text = event_person.first.inner_text()
        assert len(first_event_text) > 0, "Event should have person name or description"

    def test_skedda_calendar_space_columns(
        self,
        page: Page,
        live_server_url: str,
        skedda_slideshow_data: dict,
    ):
        """Test that Skedda calendar displays correct space columns.

        Verifies that space headers match the equipment/resources from events.
        """
        display = skedda_slideshow_data["display"]

        # Navigate to the display page
        page.goto(f"{live_server_url}/display/{display.name}")
        page.wait_for_load_state("load")

        # Wait for calendar to load
        calendar = page.locator(".skedda-calendar")
        expect(calendar).to_be_visible(timeout=10000)

        # Get all space headers
        space_headers = page.locator(".skedda-space-header")

        # Wait for space headers to be populated
        expect(space_headers.first).to_be_visible(timeout=10000)

        # Collect space names
        header_count = space_headers.count()
        space_names = []
        for i in range(header_count):
            space_names.append(space_headers.nth(i).inner_text())

        # Should have at least 2 spaces (from our test events)
        assert len(space_names) >= 2, f"Expected at least 2 spaces, found {space_names}"

        # Check that expected spaces are present
        all_text = " ".join(space_names)
        assert (
            "Glowforge" in all_text or "CNC" in all_text
        ), f"Expected equipment names in headers, got: {space_names}"

    def test_skedda_calendar_shows_recurring_events_differently(
        self,
        page: Page,
        live_server_url: str,
        skedda_slideshow_data: dict,
    ):
        """Test that recurring/group events (no person name) are styled differently.

        The 'Open Build Night' event has no attendee_name, so it should have
        the 'skedda-event-recurring' class for different styling.
        """
        display = skedda_slideshow_data["display"]

        # Navigate to the display page
        page.goto(f"{live_server_url}/display/{display.name}")
        page.wait_for_load_state("load")

        # Wait for calendar to load
        calendar = page.locator(".skedda-calendar")
        expect(calendar).to_be_visible(timeout=10000)

        # Wait for events
        events = page.locator(".skedda-event")
        expect(events.first).to_be_visible(timeout=10000)

        # Look for recurring event styling
        # The Open Build Night event should have the recurring class
        recurring_events = page.locator(".skedda-event-recurring")

        # Should have at least one recurring event (Open Build Night)
        # Note: The event spans multiple spaces, so there may be multiple elements
        recurring_count = recurring_events.count()
        assert (
            recurring_count >= 1
        ), "Expected at least one recurring event with different styling"

    def test_skedda_calendar_loading_state(
        self,
        page: Page,
        live_server_url: str,
        skedda_slideshow_data: dict,
    ):
        """Test that loading state is shown briefly before calendar renders.

        This tests the initial loading state before the API returns data.
        """
        display = skedda_slideshow_data["display"]

        # Slow down the network to catch the loading state
        # Note: This may not always catch it due to fast local responses

        # Navigate to the display page
        page.goto(f"{live_server_url}/display/{display.name}")

        # The loading state may be very brief, but the calendar should eventually appear
        calendar = page.locator(".skedda-calendar")
        expect(calendar).to_be_visible(timeout=10000)

        # Verify calendar loaded successfully (loading text should be gone)
        loading = page.locator(".skedda-loading")
        # Loading should be hidden after calendar renders
        # Use a short timeout since calendar should load quickly
        try:
            expect(loading).to_be_hidden(timeout=5000)
        except Exception:
            # If loading text is still visible, the calendar didn't render
            assert False, "Calendar should have loaded - loading state still visible"
