# Fix Flaky Skedda E2E Tests

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Several E2E tests in `tests/e2e/test_skedda_display.py` are flaky - they pass intermittently locally but fail in CI. These tests verify the Skedda calendar display functionality.

## Affected Tests

1. **`test_skedda_calendar_space_columns`** - Fails waiting for `.skedda-space-header` element
2. **`test_skedda_calendar_shows_recurring_events_differently`** - Fails waiting for `.skedda-event` element

## Observed Behavior

### Local Runs
- Tests pass when run individually: `poetry run -- nox -s test-e2e -- tests/e2e/test_skedda_display.py::TestSkeddaCalendarDisplayE2E::test_skedda_calendar_shows_recurring_events_differently`
- Tests sometimes pass when run as part of full test suite
- Tests sometimes fail locally with same error as CI

### CI Failures
From GitHub Actions logs:

```
FAILED tests/e2e/test_skedda_display.py::TestSkeddaCalendarDisplayE2E::test_skedda_calendar_space_columns[chromium]
AssertionError: Locator expected to be visible
Actual value: None
Error: element(s) not found
Call log:
  - Expect "to_be_visible" with timeout 10000ms
  - waiting for locator(".skedda-space-header").first

FAILED tests/e2e/test_skedda_display.py::TestSkeddaCalendarDisplayE2E::test_skedda_calendar_shows_recurring_events_differently[chromium]
AssertionError: Locator expected to be visible
Actual value: None
Error: element(s) not found
Call log:
  - Expect "to_be_visible" with timeout 10000ms
  - waiting for locator(".skedda-event").first
```

### Server Logs During Failure
The server logs show:
- Display page renders successfully (200 response)
- SSE connection established
- **Skedda data endpoint returns 404**: `GET /api/v1/display/skedda-test-display/skedda-data/1 -> 404`

This 404 on the skedda-data endpoint appears to be the root cause - the calendar renders but has no event data to display.

## Test File Location

`tests/e2e/test_skedda_display.py`

## Related Components

- Skedda calendar JavaScript rendering in display view
- `/api/v1/display/<name>/skedda-data/<feed_id>` endpoint
- Test fixtures that set up Skedda slideshow data

## Notes

- Other Skedda tests in the same file pass consistently:
  - `test_skedda_calendar_renders_grid`
  - `test_skedda_calendar_displays_events`
  - `test_skedda_calendar_loading_state`
- The flaky tests may have timing/race condition issues or fixture setup problems specific to CI environment
