"""Unit tests for the iCal parser module."""

import os
from datetime import datetime, timezone

import pytest

from kiosk_show_replacement.ical_parser import (
    extract_notes_from_description,
    extract_resources_from_event,
    parse_ics_data,
    parse_skedda_summary,
)


class TestParseIcsData:
    """Tests for parse_ics_data function."""

    def test_parse_empty_content_raises_error(self) -> None:
        """Empty content should raise ValueError."""
        with pytest.raises(ValueError, match="Empty ICS content"):
            parse_ics_data("")

        with pytest.raises(ValueError, match="Empty ICS content"):
            parse_ics_data("   ")

    def test_parse_invalid_content_raises_error(self) -> None:
        """Invalid ICS content should raise ValueError."""
        with pytest.raises(ValueError, match="Failed to parse ICS content"):
            parse_ics_data("This is not valid ICS content")

    def test_parse_minimal_calendar(self) -> None:
        """Parse a minimal valid ICS calendar with one event."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-uid-123
SUMMARY:Test Event
DTSTART:20260128T120000Z
DTEND:20260128T140000Z
END:VEVENT
END:VCALENDAR"""

        events = parse_ics_data(ics_content)

        assert len(events) == 1
        event = events[0]
        assert event["uid"] == "test-uid-123"
        assert event["summary"] == "Test Event"
        assert event["start_time"] == datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)
        assert event["end_time"] == datetime(2026, 1, 28, 14, 0, 0, tzinfo=timezone.utc)
        assert event["description"] is None
        assert event["resources"] == []
        assert event["attendee_name"] is None
        assert event["attendee_email"] is None

    def test_parse_event_with_description(self) -> None:
        """Parse event with description."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-uid-456
SUMMARY:Described Event
DESCRIPTION:This is a test description
DTSTART:20260128T120000Z
DTEND:20260128T140000Z
END:VEVENT
END:VCALENDAR"""

        events = parse_ics_data(ics_content)

        assert len(events) == 1
        assert events[0]["description"] == "This is a test description"

    def test_parse_event_with_resources(self) -> None:
        """Parse event with RESOURCES property."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-uid-789
SUMMARY:Resource Event
DTSTART:20260128T120000Z
DTEND:20260128T140000Z
RESOURCES:Laser Cutter
RESOURCES:CNC Machine
END:VEVENT
END:VCALENDAR"""

        events = parse_ics_data(ics_content)

        assert len(events) == 1
        assert sorted(events[0]["resources"]) == ["CNC Machine", "Laser Cutter"]

    def test_parse_event_with_attendee(self) -> None:
        """Parse event with ATTENDEE property."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-uid-att
SUMMARY:Attendee Event
DTSTART:20260128T120000Z
DTEND:20260128T140000Z
ATTENDEE;CN=John Doe:mailto:john@example.com
END:VEVENT
END:VCALENDAR"""

        events = parse_ics_data(ics_content)

        assert len(events) == 1
        assert events[0]["attendee_name"] == "John Doe"
        assert events[0]["attendee_email"] == "john@example.com"

    def test_parse_event_skips_invalid(self) -> None:
        """Events missing required fields are skipped."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:valid-event
SUMMARY:Valid Event
DTSTART:20260128T120000Z
DTEND:20260128T140000Z
END:VEVENT
BEGIN:VEVENT
UID:missing-summary
DTSTART:20260128T150000Z
DTEND:20260128T160000Z
END:VEVENT
END:VCALENDAR"""

        events = parse_ics_data(ics_content)

        assert len(events) == 1
        assert events[0]["uid"] == "valid-event"

    def test_parse_event_with_timezone(self) -> None:
        """Parse event with timezone-aware datetime."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:20070101T020000
TZNAME:EST
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
UID:tz-event
SUMMARY:Timezone Event
DTSTART;TZID=America/New_York:20260128T120000
DTEND;TZID=America/New_York:20260128T140000
END:VEVENT
END:VCALENDAR"""

        events = parse_ics_data(ics_content)

        assert len(events) == 1
        # 12:00 EST = 17:00 UTC (EST is UTC-5)
        assert events[0]["start_time"].tzinfo == timezone.utc

    def test_parse_skedda_ics_file(self) -> None:
        """Parse the actual Skedda ICS file from test assets."""
        ics_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "skedda.ics"
        )

        if not os.path.exists(ics_path):
            pytest.skip("Skedda ICS test file not found")

        with open(ics_path, "r", encoding="utf-8") as f:
            ics_content = f.read()

        events = parse_ics_data(ics_content)

        # Should have many events
        assert len(events) > 10

        # All events should have required fields
        for event in events:
            assert event["uid"]
            assert event["summary"]
            assert event["start_time"]
            assert event["end_time"]

        # Find an event with an attendee
        attendee_events = [e for e in events if e["attendee_name"]]
        assert len(attendee_events) > 0

        # Find an event with resources
        resource_events = [e for e in events if e["resources"]]
        assert len(resource_events) > 0


class TestParseSkedaSummary:
    """Tests for parse_skedda_summary function."""

    def test_parse_personal_booking(self) -> None:
        """Parse personal booking format: 'Person: Description (Space)'."""
        person, desc, space = parse_skedda_summary(
            "Janelle McDaniel: Crafts (Brontë Laser Cutter)"
        )
        assert person == "Janelle McDaniel"
        assert desc == "Crafts"
        assert space == "Brontë Laser Cutter"

    def test_parse_personal_booking_with_colon_in_description(self) -> None:
        """Parse booking where description contains a colon."""
        person, desc, space = parse_skedda_summary(
            "John Doe: Project: Phase 2 (CNC Machine)"
        )
        assert person == "John Doe"
        assert desc == "Project: Phase 2"
        assert space == "CNC Machine"

    def test_parse_multi_space_event(self) -> None:
        """Parse multi-space event format: 'Event (Space + N others)'."""
        person, desc, space = parse_skedda_summary(
            "Family Build Night (CNC Milling Machine + 4 others)"
        )
        assert person == ""
        assert desc == "Family Build Night"
        assert space == "CNC Milling Machine"

    def test_parse_multi_space_event_one_other(self) -> None:
        """Parse multi-space event with singular 'other'."""
        person, desc, space = parse_skedda_summary(
            "Cleaning (Glowforge Laser Cutter + 1 other)"
        )
        assert person == ""
        assert desc == "Cleaning"
        assert space == "Glowforge Laser Cutter"

    def test_parse_simple_event(self) -> None:
        """Parse simple event format: 'Event (Space)'."""
        person, desc, space = parse_skedda_summary(
            "Cleaning (Glowforge Laser Cutter)"
        )
        assert person == ""
        assert desc == "Cleaning"
        assert space == "Glowforge Laser Cutter"

    def test_parse_no_parentheses(self) -> None:
        """Parse event with no parentheses."""
        person, desc, space = parse_skedda_summary("Just an event name")
        assert person == ""
        assert desc == "Just an event name"
        assert space == ""

    def test_parse_empty_summary(self) -> None:
        """Parse empty summary."""
        person, desc, space = parse_skedda_summary("")
        assert person == ""
        assert desc == ""
        assert space == ""

    def test_parse_whitespace_handling(self) -> None:
        """Parse summary with extra whitespace."""
        person, desc, space = parse_skedda_summary(
            "  John Doe:  My Project  (  Laser Cutter  )  "
        )
        assert person == "John Doe"
        assert desc == "My Project"
        assert space == "Laser Cutter"


class TestExtractResourcesFromEvent:
    """Tests for extract_resources_from_event function."""

    def test_extract_single_resource(self) -> None:
        """Extract single RESOURCES property."""
        from icalendar import Event

        event = Event()
        event.add("resources", "Laser Cutter")

        resources = extract_resources_from_event(event)

        assert resources == ["Laser Cutter"]

    def test_extract_multiple_resources(self) -> None:
        """Extract multiple RESOURCES properties."""
        from icalendar import Event

        event = Event()
        event.add("resources", "Laser Cutter")
        event.add("resources", "CNC Machine")
        event.add("resources", "3D Printer")

        resources = extract_resources_from_event(event)

        assert sorted(resources) == ["3D Printer", "CNC Machine", "Laser Cutter"]

    def test_extract_resources_from_description(self) -> None:
        """Extract resources from DESCRIPTION in Skedda format."""
        from icalendar import Event

        event = Event()
        event.add("description", "Spaces: Laser Cutter, CNC Machine\n\nNotes: test")

        resources = extract_resources_from_event(event)

        assert sorted(resources) == ["CNC Machine", "Laser Cutter"]

    def test_extract_resources_deduplicates(self) -> None:
        """Resources are deduplicated between RESOURCES and DESCRIPTION."""
        from icalendar import Event

        event = Event()
        event.add("resources", "Laser Cutter")
        event.add("description", "Spaces: Laser Cutter, CNC Machine")

        resources = extract_resources_from_event(event)

        assert sorted(resources) == ["CNC Machine", "Laser Cutter"]

    def test_extract_no_resources(self) -> None:
        """Event with no resources returns empty list."""
        from icalendar import Event

        event = Event()

        resources = extract_resources_from_event(event)

        assert resources == []


class TestExtractNotesFromDescription:
    """Tests for extract_notes_from_description function."""

    def test_extract_notes(self) -> None:
        """Extract notes from Skedda description format."""
        description = "Spaces: Laser Cutter\n\nNotes: This is my project note"
        notes = extract_notes_from_description(description)
        assert notes == "This is my project note"

    def test_extract_multiline_notes(self) -> None:
        """Extract multi-line notes."""
        description = "Spaces: Laser Cutter\n\nNotes: Line 1\nLine 2\nLine 3"
        notes = extract_notes_from_description(description)
        assert notes == "Line 1\nLine 2\nLine 3"

    def test_no_notes_section(self) -> None:
        """Return None when no Notes section."""
        description = "Spaces: Laser Cutter"
        notes = extract_notes_from_description(description)
        assert notes is None

    def test_empty_description(self) -> None:
        """Return None for empty description."""
        assert extract_notes_from_description("") is None
        assert extract_notes_from_description(None) is None

    def test_escaped_newlines(self) -> None:
        """Handle escaped newlines in ICS format."""
        description = "Spaces: Laser Cutter\\n\\nNotes: My note"
        notes = extract_notes_from_description(description)
        assert notes == "My note"
