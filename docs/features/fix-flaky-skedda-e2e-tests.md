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

---

## Implementation Plan

### Root Cause Analysis

The tests fail because of **SQLite cross-process visibility issues**. The test data flow is:

1. `_create_session_test_data()` creates test data (display, slideshow, skedda item, events)
2. WAL checkpoint is performed to sync data to disk
3. `live_server` fixture forks a subprocess running Flask
4. Test navigates to display page - renders successfully because `SlideshowItem.query.filter_by(slideshow_id=X)` through relationship works
5. JavaScript calls `/api/v1/display/skedda-test-display/skedda-data/{item_id}`
6. API endpoint queries `SlideshowItem.query.filter_by(id=item_id).first()` - returns `None` → 404

The issue is that `SlideshowItem.query.filter_by(id=item_id)` in the forked server process sometimes cannot see data created before the fork, even with WAL checkpoint. This is a known SQLite cross-process visibility issue that manifests as a race condition - more likely to fail in CI due to timing differences.

**Why some tests pass consistently:**
- `test_skedda_calendar_renders_grid` - checks structural elements (calendar grid) that render even if API fails
- `test_skedda_calendar_loading_state` - only checks loading state transitions, not event data
- The failing tests specifically require event data from the API endpoint

### Solution

**Primary Fix:** Ensure complete database session cleanup and reconnection before the live_server fork to guarantee cross-process visibility.

### Milestones

#### Milestone 1: Improve Database Synchronization (FST-1)

**Task 1.1:** Modify `tests/e2e/conftest.py` to ensure complete database session cleanup after creating test data:
- After the WAL checkpoint, close the session completely with `db.session.close()`
- Remove the session from the scoped session registry with `db.session.remove()`
- Dispose of the engine to close all connections with `db.engine.dispose()`
- This ensures the forked server process creates fresh connections that will see the committed data

**Task 1.2:** Run E2E tests locally multiple times to verify fix:
- Run `poetry run -- nox -s test-e2e -- tests/e2e/test_skedda_display.py` at least 5 times
- All runs should pass consistently

#### Milestone 2: Acceptance Criteria (FST-2)

**Task 2.1:** Ensure all nox sessions pass:
- Run `poetry run -- nox -s test-e2e` - all tests pass
- Run `poetry run -- nox -s test-3.14` - unit tests still pass
- Run `poetry run -- nox -s lint` - no lint errors
- Run `poetry run -- nox -s type_check` - no type errors

**Task 2.2:** Verify CI passes:
- Push branch and create PR
- All GitHub Actions checks must pass

**Task 2.3:** Move feature file to completed:
- Move `docs/features/fix-flaky-skedda-e2e-tests.md` to `docs/features/completed/`

### Progress

- [x] Milestone 1: Improve Database Synchronization (FST-1)
  - [x] Task 1.1: Modify conftest.py for complete session cleanup
  - [x] Task 1.2: Verify fix with multiple local test runs (10/10 passed)
- [ ] Milestone 2: Acceptance Criteria (FST-2)
  - [x] Task 2.1: All nox sessions pass
  - [ ] Task 2.2: CI passes
  - [ ] Task 2.3: Move feature file to completed

### Implementation Notes

The original plan needed to be expanded during implementation. Through investigation, we discovered:

1. The root cause was more nuanced: `Display.query.filter_by(name=X).first()` would return `None` even when `Display.query.all()` showed the record existed in the database. This is a SQLAlchemy/SQLite session state issue.

2. The fix required changes in two places:
   - **tests/e2e/conftest.py**: Use NullPool, TRUNCATE WAL checkpoint mode, and session cleanup
   - **kiosk_show_replacement/api/v1.py**: Add `db.session.expire_all()` and fallback logic in `get_display_skedda_data()` to handle cases where filter_by queries fail but .all() queries succeed
