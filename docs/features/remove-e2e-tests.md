# Remove e2e Tests

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This application has three test suites, per `docs/development.rst`:

1. **Unit Tests** (``tests/unit/``): Test individual functions and classes in isolation
2. **Integration Tests** (``tests/integration/``): Full-stack browser tests of React frontend + Flask backend
3. **End-to-End Tests** (``tests/e2e/``): Browser tests of Flask server-rendered pages

There are currently 589 unit tests and 130 integration tests but only 26 e2e tests, 6 of which are skipped. Your task is to:

1. Systematically identify the functionality being tested by each integration test, and determine if this functionality is already being checked via an integration test. If not, add or update integration tests to ensure that they're also verifying the functionality tested by the e2e test.
2. Completely and totally remove the e2e tests from this repository - the tests themselves, the nox environment, the github actions jobs, and any mentions in `README.md`, `CLAUDE.md`, or `docs/*.rst`. From now on we will just have unit tests and integration tests.

---

## Implementation Plan

### E2E Test Coverage Analysis

| E2E Test File | Tests | Already Covered in Integration? | Action |
|---------------|-------|--------------------------------|--------|
| `test_basic_access.py` | 2 | Yes - login form tests exist in test_dashboard.py, test_sse_integration.py | No migration needed |
| `test_sse_workflows.py` | 6 (ALL SKIPPED) | N/A - tests are skipped | No migration needed |
| `test_user_workflows.py` | 2 | Yes - login workflow in test_dashboard.py `_login()` method, authentication in test_sse_integration.py | No migration needed |
| `test_dashboard_navigation.py` | 12 | Mostly - test_dashboard.py has `test_quick_actions_navigate_correctly` and `test_navigation_bar_links_work` | No migration needed - navigation behavior is tested |
| `test_skedda_display.py` | 5 | **No** - Skedda calendar display rendering on kiosk page is NOT tested | **Must migrate** |

### Summary of Gaps

Only the **Skedda calendar display tests** need to be migrated. These tests verify that when navigating to `/display/{display_name}`, a Skedda calendar slide correctly renders:
- Calendar container (`.skedda-calendar`)
- Date header (`.skedda-date-header`)
- Space headers (`.skedda-space-header`)
- Time slots (`.skedda-time-slot`)
- Events (`.skedda-event`)
- Recurring event styling (`.skedda-event-recurring`)
- Loading state transition

The integration test `test_display_playback.py` already tests the `/display/{display_name}` page, so we can add Skedda-specific tests there.

---

## Milestone 1: Migrate Skedda Display Tests (RET-1)

Migrate the 5 Skedda calendar display tests from `tests/e2e/test_skedda_display.py` to `tests/integration/test_display_playback.py`.

### Task 1.1: Add Skedda calendar rendering tests
- Create a new test class `TestSkeddaCalendarDisplay` in `tests/integration/test_display_playback.py`
- Add test fixtures to create an iCal feed, events, Skedda slideshow item, and display
- Migrate the following tests:
  - `test_skedda_calendar_renders_grid` - verify calendar container, date header, space headers, time slots
  - `test_skedda_calendar_displays_events` - verify event elements render with person/description
  - `test_skedda_calendar_space_columns` - verify space headers from resources
  - `test_skedda_calendar_shows_recurring_events_differently` - verify recurring event styling
  - `test_skedda_calendar_loading_state` - verify loading state transitions to calendar

### Task 1.2: Verify migrated tests pass
- Run `poetry run -- nox -s test-integration -- tests/integration/test_display_playback.py::TestSkeddaCalendarDisplay`
- Ensure all 5 migrated tests pass

---

## Milestone 2: Remove E2E Tests (RET-2)

Completely remove all e2e test infrastructure.

### Task 2.1: Remove e2e test files
- Delete `tests/e2e/` directory and all contents

### Task 2.2: Update noxfile.py
- Remove `test-e2e` session (lines ~270-289)
- Remove `test-e2e` from `test_all` notification (line ~302)
- Remove `test-e2e` from help output (line ~469)

### Task 2.3: Update GitHub Actions CI
- Remove `test-e2e` job from `.github/workflows/ci.yml` (lines ~167-213)
- Update comment at top of file that mentions e2e tests (line 4)

### Task 2.4: Update documentation
- **CLAUDE.md**: Remove e2e references (lines ~43, ~160, ~180)
- **docs/development.rst**: Remove all e2e references (lines ~107-108, ~157, ~249-282, ~329-332, ~403, ~474, ~540-544, ~584)
- **.github/copilot-instructions.md**: Remove e2e references (lines ~91-94)

### Task 2.5: Verify removal is complete
- Run `grep -r "e2e\|test-e2e" --include="*.py" --include="*.yml" --include="*.md" --include="*.rst" .` and verify only completed feature docs remain

---

## Milestone 3: Acceptance Criteria (RET-3)

### Task 3.1: Verify all nox sessions pass
- `poetry run -- nox -s format`
- `poetry run -- nox -s lint`
- `poetry run -- nox -s type_check`
- `poetry run -- nox -s test-3.14`
- `poetry run -- nox -s test-integration`

### Task 3.2: Verify `nox -s test-e2e` no longer exists
- Confirm error when running `poetry run -- nox -s test-e2e`

### Task 3.3: Update documentation status
- Ensure docs accurately reflect only unit tests and integration tests

### Task 3.4: Complete feature
- Move `docs/features/remove-e2e-tests.md` to `docs/features/completed/`
- Create GitHub PR

---

## Progress Log

### 2026-02-01: Milestone 1 Complete
- [x] **Task 1.1**: Added `TestSkeddaCalendarDisplay` class with 5 tests to `tests/integration/test_display_playback.py`
- [x] **Task 1.2**: All 5 migrated tests pass (135 integration tests total)
