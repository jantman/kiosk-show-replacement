"""Unit tests for the iCal service module."""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from kiosk_show_replacement.ical_service import (
    fetch_ics_from_url,
    get_all_feed_spaces,
    get_events_for_date,
    get_or_create_feed,
    get_skedda_calendar_data,
    needs_refresh,
    refresh_all_feeds,
    refresh_feed,
    sync_feed_events,
)
from kiosk_show_replacement.models import (
    ICalEvent,
    ICalFeed,
    Slideshow,
    SlideshowItem,
    db,
)


class TestFetchIcsFromUrl:
    """Tests for fetch_ics_from_url function."""

    def test_fetch_success(self) -> None:
        """Successful fetch returns ICS content."""
        with patch("kiosk_show_replacement.ical_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = fetch_ics_from_url("https://example.com/cal.ics")

            assert result == "BEGIN:VCALENDAR\nEND:VCALENDAR"
            mock_get.assert_called_once()

    def test_fetch_timeout_returns_none(self) -> None:
        """Timeout returns None."""
        import requests

        with patch("kiosk_show_replacement.ical_service.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            result = fetch_ics_from_url("https://example.com/cal.ics")

            assert result is None

    def test_fetch_connection_error_returns_none(self) -> None:
        """Connection error returns None."""
        import requests

        with patch("kiosk_show_replacement.ical_service.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            result = fetch_ics_from_url("https://example.com/cal.ics")

            assert result is None

    def test_fetch_http_error_returns_none(self) -> None:
        """HTTP error returns None."""
        import requests

        with patch("kiosk_show_replacement.ical_service.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_get.return_value = mock_response

            result = fetch_ics_from_url("https://example.com/cal.ics")

            assert result is None


class TestGetOrCreateFeed:
    """Tests for get_or_create_feed function."""

    def test_creates_new_feed(self, app) -> None:
        """Creates a new feed if URL doesn't exist."""
        with app.app_context():
            url = "https://example.com/new-feed.ics"

            feed = get_or_create_feed(url)

            assert feed is not None
            assert feed.url == url
            assert feed.id is not None

    def test_returns_existing_feed(self, app) -> None:
        """Returns existing feed if URL already exists."""
        with app.app_context():
            url = "https://example.com/existing-feed.ics"

            # Create feed first
            feed1 = get_or_create_feed(url)
            feed1_id = feed1.id

            # Get same feed
            feed2 = get_or_create_feed(url)

            assert feed1_id == feed2.id


class TestNeedsRefresh:
    """Tests for needs_refresh function."""

    def test_needs_refresh_if_never_fetched(self, app) -> None:
        """Feed needs refresh if never fetched."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            assert needs_refresh(feed, 15) is True

    def test_needs_refresh_if_stale(self, app) -> None:
        """Feed needs refresh if last fetch is older than refresh interval."""
        with app.app_context():
            feed = ICalFeed(
                url="https://example.com/cal.ics",
                last_fetched=datetime.now(timezone.utc) - timedelta(minutes=20),
            )
            db.session.add(feed)
            db.session.commit()

            assert needs_refresh(feed, 15) is True

    def test_no_refresh_if_fresh(self, app) -> None:
        """Feed doesn't need refresh if recently fetched."""
        with app.app_context():
            feed = ICalFeed(
                url="https://example.com/cal.ics",
                last_fetched=datetime.now(timezone.utc) - timedelta(minutes=5),
            )
            db.session.add(feed)
            db.session.commit()

            assert needs_refresh(feed, 15) is False


class TestRefreshFeed:
    """Tests for refresh_feed function."""

    def test_refresh_success(self, app) -> None:
        """Successful refresh updates feed and syncs events."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-1
SUMMARY:Test Event
DTSTART:20260128T120000Z
DTEND:20260128T140000Z
END:VEVENT
END:VCALENDAR"""

        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()
            feed_id = feed.id

            with patch(
                "kiosk_show_replacement.ical_service.fetch_ics_from_url"
            ) as mock_fetch:
                mock_fetch.return_value = ics_content

                result = refresh_feed(feed)

                assert result is True
                assert feed.last_fetched is not None
                assert feed.last_error is None

                # Check event was created
                events = ICalEvent.query.filter_by(feed_id=feed_id).all()
                assert len(events) == 1
                assert events[0].uid == "test-event-1"

    def test_refresh_fetch_failure(self, app) -> None:
        """Failed fetch updates last_error."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            with patch(
                "kiosk_show_replacement.ical_service.fetch_ics_from_url"
            ) as mock_fetch:
                mock_fetch.return_value = None

                result = refresh_feed(feed)

                assert result is False
                assert feed.last_error is not None

    def test_refresh_parse_failure(self, app) -> None:
        """Failed parse updates last_error."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            with patch(
                "kiosk_show_replacement.ical_service.fetch_ics_from_url"
            ) as mock_fetch:
                mock_fetch.return_value = "invalid ics content"

                result = refresh_feed(feed)

                assert result is False
                assert "Failed to parse" in feed.last_error


class TestSyncFeedEvents:
    """Tests for sync_feed_events function."""

    def test_creates_new_events(self, app) -> None:
        """New events are created."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()
            feed_id = feed.id

            events = [
                {
                    "uid": "event-1",
                    "summary": "Event 1",
                    "description": None,
                    "start_time": datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                    "resources": ["Room A"],
                    "attendee_name": "John",
                    "attendee_email": "john@example.com",
                }
            ]

            sync_feed_events(feed, events)
            db.session.commit()

            db_events = ICalEvent.query.filter_by(feed_id=feed_id).all()
            assert len(db_events) == 1
            assert db_events[0].uid == "event-1"

    def test_updates_existing_events(self, app) -> None:
        """Existing events are updated."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()
            feed_id = feed.id

            # Create initial event
            event = ICalEvent(
                feed_id=feed_id,
                uid="event-1",
                summary="Old Summary",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
            )
            db.session.add(event)
            db.session.commit()

            # Sync with updated event
            events = [
                {
                    "uid": "event-1",
                    "summary": "New Summary",
                    "description": "Added description",
                    "start_time": datetime(2026, 1, 28, 13, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2026, 1, 28, 15, 0, tzinfo=timezone.utc),
                    "resources": ["Room B"],
                    "attendee_name": None,
                    "attendee_email": None,
                }
            ]

            sync_feed_events(feed, events)
            db.session.commit()

            db_events = ICalEvent.query.filter_by(feed_id=feed_id).all()
            assert len(db_events) == 1
            assert db_events[0].summary == "New Summary"
            assert db_events[0].description == "Added description"

    def test_deletes_removed_events(self, app) -> None:
        """Events no longer in feed are deleted."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()
            feed_id = feed.id

            # Create two events
            for uid in ["event-1", "event-2"]:
                event = ICalEvent(
                    feed_id=feed_id,
                    uid=uid,
                    summary=f"Event {uid}",
                    start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                    end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                )
                db.session.add(event)
            db.session.commit()

            # Sync with only one event
            events = [
                {
                    "uid": "event-1",
                    "summary": "Event 1",
                    "description": None,
                    "start_time": datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                    "resources": [],
                    "attendee_name": None,
                    "attendee_email": None,
                }
            ]

            sync_feed_events(feed, events)
            db.session.commit()

            db_events = ICalEvent.query.filter_by(feed_id=feed_id).all()
            assert len(db_events) == 1
            assert db_events[0].uid == "event-1"


class TestGetEventsForDate:
    """Tests for get_events_for_date function."""

    def test_gets_events_on_date(self, app) -> None:
        """Returns events on the specified date."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            # Create event on target date
            event = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="Event 1",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
            )
            db.session.add(event)
            db.session.commit()

            events = get_events_for_date(feed, date(2026, 1, 28))

            assert len(events) == 1
            assert events[0].uid == "event-1"

    def test_excludes_events_on_other_dates(self, app) -> None:
        """Excludes events on other dates."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            # Create event on different date
            event = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="Event 1",
                start_time=datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 29, 14, 0, tzinfo=timezone.utc),
            )
            db.session.add(event)
            db.session.commit()

            events = get_events_for_date(feed, date(2026, 1, 28))

            assert len(events) == 0

    def test_includes_spanning_events(self, app) -> None:
        """Includes events that span across the date."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            # Create event spanning multiple days
            event = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="Multi-day Event",
                start_time=datetime(2026, 1, 27, 20, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 4, 0, tzinfo=timezone.utc),
            )
            db.session.add(event)
            db.session.commit()

            events = get_events_for_date(feed, date(2026, 1, 28))

            assert len(events) == 1


class TestGetSkeddaCalendarData:
    """Tests for get_skedda_calendar_data function."""

    def test_raises_error_for_non_skedda_slide(self, app, sample_user) -> None:
        """Raises ValueError for non-skedda slide."""
        with app.app_context():
            slideshow = Slideshow(name="Test", owner_id=sample_user.id)
            db.session.add(slideshow)
            db.session.commit()

            slide = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                title="Test",
            )
            db.session.add(slide)
            db.session.commit()

            with pytest.raises(ValueError, match="not a skedda type"):
                get_skedda_calendar_data(slide)

    def test_raises_error_for_no_feed(self, app, sample_user) -> None:
        """Raises ValueError for skedda slide without feed."""
        with app.app_context():
            slideshow = Slideshow(name="Test", owner_id=sample_user.id)
            db.session.add(slideshow)
            db.session.commit()

            slide = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="skedda",
                title="Test",
            )
            db.session.add(slide)
            db.session.commit()

            with pytest.raises(ValueError, match="no iCal feed"):
                get_skedda_calendar_data(slide)

    def test_returns_formatted_data(self, app, sample_user) -> None:
        """Returns properly formatted calendar data."""
        with app.app_context():
            # Create feed with event
            feed = ICalFeed(
                url="https://example.com/cal.ics",
                last_fetched=datetime.now(timezone.utc),
            )
            db.session.add(feed)
            db.session.commit()

            event = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="John Doe: Project (Laser Cutter)",
                start_time=datetime(2026, 1, 28, 17, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 19, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter"]),
                attendee_name="John Doe",
            )
            db.session.add(event)

            slideshow = Slideshow(name="Test", owner_id=sample_user.id)
            db.session.add(slideshow)
            db.session.commit()

            slide = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="skedda",
                title="Calendar",
                ical_feed_id=feed.id,
                ical_refresh_minutes=15,
            )
            db.session.add(slide)
            db.session.commit()

            with patch(
                "kiosk_show_replacement.ical_service.refresh_feed_if_needed"
            ) as mock_refresh:
                mock_refresh.return_value = False

                data = get_skedda_calendar_data(slide, target_date=date(2026, 1, 28))

                assert data["date"] == "2026-01-28"
                assert "Laser Cutter" in data["spaces"]
                assert len(data["time_slots"]) > 0
                assert len(data["events"]) == 1
                assert data["events"][0]["person_name"] == "John Doe"
                assert data["events"][0]["description"] == "Project"


class TestGetAllFeedSpaces:
    """Tests for get_all_feed_spaces function."""

    def test_returns_all_spaces_from_all_events(self, app) -> None:
        """Returns unique spaces from all events in the feed."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            # Event on Jan 28 with "Laser Cutter"
            event1 = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="Event 1",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter"]),
            )
            # Event on Jan 29 with "CNC Machine"
            event2 = ICalEvent(
                feed_id=feed.id,
                uid="event-2",
                summary="Event 2",
                start_time=datetime(2026, 1, 29, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc),
                resources=json.dumps(["CNC Machine"]),
            )
            db.session.add_all([event1, event2])
            db.session.commit()

            spaces = get_all_feed_spaces(feed)

            assert spaces == ["CNC Machine", "Laser Cutter"]

    def test_returns_empty_list_for_no_events(self, app) -> None:
        """Returns empty list when feed has no events."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            spaces = get_all_feed_spaces(feed)

            assert spaces == []

    def test_deduplicates_spaces(self, app) -> None:
        """Deduplicates spaces appearing in multiple events."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            event1 = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="Event 1",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter", "CNC Machine"]),
            )
            event2 = ICalEvent(
                feed_id=feed.id,
                uid="event-2",
                summary="Event 2",
                start_time=datetime(2026, 1, 29, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter"]),
            )
            db.session.add_all([event1, event2])
            db.session.commit()

            spaces = get_all_feed_spaces(feed)

            assert spaces == ["CNC Machine", "Laser Cutter"]

    def test_skips_events_with_invalid_json(self, app) -> None:
        """Skips events with invalid JSON in resources."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()

            event1 = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="Event 1",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                resources="not valid json",
            )
            event2 = ICalEvent(
                feed_id=feed.id,
                uid="event-2",
                summary="Event 2",
                start_time=datetime(2026, 1, 29, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter"]),
            )
            db.session.add_all([event1, event2])
            db.session.commit()

            spaces = get_all_feed_spaces(feed)

            assert spaces == ["Laser Cutter"]

    def test_excludes_other_feeds(self, app) -> None:
        """Only returns spaces from the specified feed."""
        with app.app_context():
            feed1 = ICalFeed(url="https://example.com/cal1.ics")
            feed2 = ICalFeed(url="https://example.com/cal2.ics")
            db.session.add_all([feed1, feed2])
            db.session.commit()

            event1 = ICalEvent(
                feed_id=feed1.id,
                uid="event-1",
                summary="Event 1",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter"]),
            )
            event2 = ICalEvent(
                feed_id=feed2.id,
                uid="event-2",
                summary="Event 2",
                start_time=datetime(2026, 1, 28, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                resources=json.dumps(["3D Printer"]),
            )
            db.session.add_all([event1, event2])
            db.session.commit()

            spaces = get_all_feed_spaces(feed1)

            assert spaces == ["Laser Cutter"]


class TestGetSkeddaCalendarDataShowsAllSpaces:
    """Tests that get_skedda_calendar_data returns all spaces from the feed."""

    def test_includes_spaces_from_other_dates(self, app, sample_user) -> None:
        """Spaces from events on other dates are included in the output."""
        with app.app_context():
            feed = ICalFeed(
                url="https://example.com/cal.ics",
                last_fetched=datetime.now(timezone.utc),
            )
            db.session.add(feed)
            db.session.commit()

            # Event on Jan 28 with "Laser Cutter"
            event1 = ICalEvent(
                feed_id=feed.id,
                uid="event-1",
                summary="John Doe: Laser Project (Laser Cutter)",
                start_time=datetime(2026, 1, 28, 12, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 28, 14, 0, tzinfo=timezone.utc),
                resources=json.dumps(["Laser Cutter"]),
                attendee_name="John Doe",
            )
            # Event on Jan 29 (different date) with "CNC Machine"
            event2 = ICalEvent(
                feed_id=feed.id,
                uid="event-2",
                summary="Jane Smith: CNC Work (CNC Machine)",
                start_time=datetime(2026, 1, 29, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc),
                resources=json.dumps(["CNC Machine"]),
                attendee_name="Jane Smith",
            )
            # Event on Jan 30 with "3D Printer"
            event3 = ICalEvent(
                feed_id=feed.id,
                uid="event-3",
                summary="Bob: 3D Print (3D Printer)",
                start_time=datetime(2026, 1, 30, 14, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 30, 16, 0, tzinfo=timezone.utc),
                resources=json.dumps(["3D Printer"]),
                attendee_name="Bob",
            )
            db.session.add_all([event1, event2, event3])

            slideshow = Slideshow(name="Test", owner_id=sample_user.id)
            db.session.add(slideshow)
            db.session.commit()

            slide = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="skedda",
                title="Calendar",
                ical_feed_id=feed.id,
                ical_refresh_minutes=15,
            )
            db.session.add(slide)
            db.session.commit()

            with patch(
                "kiosk_show_replacement.ical_service.refresh_feed_if_needed"
            ) as mock_refresh:
                mock_refresh.return_value = False

                # Query Jan 28 - only has Laser Cutter event
                data = get_skedda_calendar_data(slide, target_date=date(2026, 1, 28))

                # All three spaces should appear (from all dates in the feed)
                assert data["spaces"] == ["3D Printer", "CNC Machine", "Laser Cutter"]

                # But only the Jan 28 event should be in the events list
                assert len(data["events"]) == 1
                assert data["events"][0]["space"] == "Laser Cutter"


class TestRefreshAllFeeds:
    """Tests for refresh_all_feeds function."""

    def test_refreshes_all_feeds(self, app) -> None:
        """Refreshes all feeds in database."""
        with app.app_context():
            # Create two feeds
            feed1 = ICalFeed(url="https://example.com/cal1.ics")
            feed2 = ICalFeed(url="https://example.com/cal2.ics")
            db.session.add_all([feed1, feed2])
            db.session.commit()

            with patch(
                "kiosk_show_replacement.ical_service.refresh_feed"
            ) as mock_refresh:
                mock_refresh.return_value = True

                result = refresh_all_feeds()

                assert result["refreshed"] == 2
                assert result["errors"] == []
                assert mock_refresh.call_count == 2

    def test_handles_errors(self, app) -> None:
        """Handles errors during refresh."""
        with app.app_context():
            feed = ICalFeed(url="https://example.com/cal.ics")
            db.session.add(feed)
            db.session.commit()
            feed_id = feed.id

            with patch(
                "kiosk_show_replacement.ical_service.refresh_feed"
            ) as mock_refresh:
                mock_refresh.side_effect = Exception("Test error")

                result = refresh_all_feeds()

                assert result["refreshed"] == 0
                assert len(result["errors"]) == 1
                assert result["errors"][0]["feed_id"] == feed_id
                assert "Test error" in result["errors"][0]["error"]
