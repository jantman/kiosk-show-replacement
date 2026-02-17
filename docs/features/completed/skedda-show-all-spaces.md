# Skedda Show All Spaces

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Currently, the Skedda slide type only displays the spaces/resources that are present in the shown timeframe. For example, if all reservations for today are for a single space/resource, only that column is shown. This slide type should be updated so that it shows columns for all known spaces/resources, even if some are completely empty in the currently rendered timeframe.

---

## Implementation

### Approach

In `get_skedda_calendar_data()`, instead of collecting spaces only from today's events, we query all unique spaces from ALL events in the feed via a new `get_all_feed_spaces()` helper function. This naturally captures the full set of known resources.

### Changes

1. **`kiosk_show_replacement/ical_service.py`**:
   - Added `get_all_feed_spaces(feed)` function that queries all unique space names across all events for a given feed
   - Updated `get_skedda_calendar_data()` to call `get_all_feed_spaces()` instead of collecting spaces only from today's events

2. **`tests/unit/test_ical_service.py`**:
   - Added `TestGetAllFeedSpaces` class with 5 tests covering: basic operation, empty feeds, deduplication, invalid JSON handling, and feed isolation
   - Added `TestGetSkeddaCalendarDataShowsAllSpaces` class testing that spaces from other dates appear in the output

3. **`tests/integration/test_display_playback.py`**:
   - Updated `skedda_test_data` fixture to include a "3D Printer" event on a future date
   - Added `test_skedda_calendar_shows_all_spaces` integration test verifying that columns render for spaces with no events today

### Acceptance Criteria

- [x] All known spaces from the feed appear as columns, even with no events on the displayed date
- [x] Unit tests pass (`nox -s test-3.14`)
- [x] Integration tests pass (`nox -s test-integration`)
- [x] Format/lint clean (`nox -s format && nox -s lint`)
- [x] Type check clean (`nox -s type_check`)
