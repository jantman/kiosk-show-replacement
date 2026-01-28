"""
ICS/iCal parser module for the Kiosk.show Replacement application.

This module provides functions for parsing iCal/ICS content, with specific
support for Skedda calendar format. It extracts events and their metadata
into a structured format suitable for database storage and display rendering.
"""

import re
from datetime import datetime, timezone
from typing import Any, Optional

from icalendar import Calendar


def parse_ics_data(ics_content: str) -> list[dict[str, Any]]:
    """Parse ICS content and extract events.

    Args:
        ics_content: Raw ICS/iCal content as a string

    Returns:
        List of event dictionaries with keys:
        - uid: str - Event unique identifier
        - summary: str - Event summary/title
        - description: str | None - Event description
        - start_time: datetime - Event start (UTC)
        - end_time: datetime - Event end (UTC)
        - resources: list[str] - List of space/resource names
        - attendee_name: str | None - Attendee name (if present)
        - attendee_email: str | None - Attendee email (if present)

    Raises:
        ValueError: If the ICS content is invalid or cannot be parsed
    """
    if not ics_content or not ics_content.strip():
        raise ValueError("Empty ICS content")

    try:
        cal = Calendar.from_ical(ics_content)
    except Exception as e:
        raise ValueError(f"Failed to parse ICS content: {e}") from e

    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        event = _parse_vevent(component)
        if event:
            events.append(event)

    return events


def _parse_vevent(component: Any) -> Optional[dict[str, Any]]:
    """Parse a VEVENT component into an event dictionary.

    Args:
        component: icalendar VEVENT component

    Returns:
        Event dictionary or None if essential fields are missing
    """
    # Required fields
    uid = component.get("uid")
    summary = component.get("summary")
    dtstart = component.get("dtstart")
    dtend = component.get("dtend")

    if not all([uid, summary, dtstart, dtend]):
        return None

    # Convert to datetime objects in UTC
    start_time = _to_utc_datetime(dtstart.dt)
    end_time = _to_utc_datetime(dtend.dt)

    if start_time is None or end_time is None:
        return None

    # Optional fields
    description = str(component.get("description", "") or "")

    # Extract resources from RESOURCES property (can have multiple)
    resources = extract_resources_from_event(component)

    # Extract attendee info
    attendee_name, attendee_email = _extract_attendee(component)

    return {
        "uid": str(uid),
        "summary": str(summary),
        "description": description if description else None,
        "start_time": start_time,
        "end_time": end_time,
        "resources": resources,
        "attendee_name": attendee_name,
        "attendee_email": attendee_email,
    }


def _to_utc_datetime(dt: Any) -> Optional[datetime]:
    """Convert an icalendar datetime to a UTC datetime.

    Args:
        dt: icalendar datetime object (can be date or datetime)

    Returns:
        UTC datetime or None if conversion fails
    """
    from datetime import date

    if dt is None:
        return None

    # Handle date-only values (convert to datetime at midnight)
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())

    if not isinstance(dt, datetime):
        return None

    # If timezone-aware, convert to UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)

    # If naive, assume UTC
    return dt.replace(tzinfo=timezone.utc)


def extract_resources_from_event(component: Any) -> list[str]:
    """Extract resource/space names from a VEVENT component.

    Resources can come from:
    1. RESOURCES property (one or more, comma-separated within each)
    2. DESCRIPTION field in Skedda format: "Spaces: space1, space2"

    Args:
        component: icalendar VEVENT component

    Returns:
        List of unique resource/space names
    """
    resources = set()

    # Method 1: Extract from RESOURCES property
    # The RESOURCES property can appear multiple times
    resources_props = component.get("resources")
    if resources_props:
        if isinstance(resources_props, list):
            for prop in resources_props:
                resources.add(str(prop).strip())
        else:
            # Single value - could be comma-separated
            for r in str(resources_props).split(","):
                r = r.strip()
                if r:
                    resources.add(r)

    # Method 2: Extract from DESCRIPTION (Skedda format)
    description = str(component.get("description", "") or "")
    if description:
        spaces_match = re.match(r"Spaces:\s*(.+?)(?:\n\n|$)", description, re.DOTALL)
        if spaces_match:
            spaces_str = spaces_match.group(1)
            # Handle escaped commas in ICS format
            spaces_str = spaces_str.replace("\\,", ",")
            for space in spaces_str.split(","):
                space = space.strip()
                if space:
                    resources.add(space)

    return sorted(resources)


def _extract_attendee(component: Any) -> tuple[Optional[str], Optional[str]]:
    """Extract attendee name and email from a VEVENT component.

    Args:
        component: icalendar VEVENT component

    Returns:
        Tuple of (name, email), both may be None
    """
    attendee = component.get("attendee")
    if not attendee:
        return None, None

    # Handle multiple attendees (take the first one)
    if isinstance(attendee, list):
        attendee = attendee[0]

    # Extract name from CN parameter
    name = None
    if hasattr(attendee, "params"):
        cn = attendee.params.get("CN")
        if cn:
            name = str(cn)

    # Extract email from mailto: value
    email = None
    attendee_str = str(attendee)
    if attendee_str.lower().startswith("mailto:"):
        email = attendee_str[7:]  # Remove "mailto:" prefix

    return name, email


def parse_skedda_summary(summary: str) -> tuple[str, str, str]:
    """Parse a Skedda event summary into its components.

    Skedda SUMMARY formats:
    1. Personal booking: "<person name>: <description> (<space name>)"
       Example: "Janelle McDaniel: Crafts (Brontë Laser Cutter)"

    2. Multi-space event: "<event name> (<space name> + N other[s])"
       Example: "Family Build Night (CNC Milling Machine + 4 others)"

    3. Simple event: "<event name> (<space name>)"
       Example: "Cleaning (Glowforge Laser Cutter)"

    Args:
        summary: Event summary string

    Returns:
        Tuple of (person_name, description, space_name)
        - For personal bookings: (person_name, description, space_name)
        - For multi-space events: ("", event_name, primary_space)
        - For simple events: ("", event_name, space_name)
        - If parsing fails: ("", summary, "")
    """
    if not summary:
        return "", "", ""

    summary = summary.strip()

    # Try to extract the space name from parentheses at the end
    space_match = re.search(r"\(([^)]+)\)\s*$", summary)
    if not space_match:
        # No parentheses - return as-is
        return "", summary, ""

    space_part = space_match.group(1)
    before_space = summary[: space_match.start()].strip()

    # Check if it's a multi-space format: "Space Name + N other[s]"
    multi_match = re.match(r"(.+?)\s*\+\s*\d+\s+others?$", space_part)
    if multi_match:
        space_name = multi_match.group(1).strip()
    else:
        space_name = space_part.strip()

    # Check if it's a personal booking: "Person Name: Description"
    colon_match = re.match(r"(.+?):\s*(.+)$", before_space)
    if colon_match:
        person_name = colon_match.group(1).strip()
        description = colon_match.group(2).strip()
        return person_name, description, space_name

    # Simple event or multi-space event without person
    return "", before_space, space_name


def extract_notes_from_description(description: str) -> Optional[str]:
    """Extract notes from a Skedda DESCRIPTION field.

    Skedda DESCRIPTION format:
    "Spaces: space1, space2

    Notes: optional notes here"

    Args:
        description: Event description string

    Returns:
        Notes text or None if no notes found
    """
    if not description:
        return None

    # Handle escaped newlines
    description = description.replace("\\n", "\n")

    # Look for "Notes:" section
    notes_match = re.search(r"\n\nNotes:\s*(.+?)$", description, re.DOTALL)
    if notes_match:
        return notes_match.group(1).strip()

    return None
