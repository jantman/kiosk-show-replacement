# Fix Flaky Integration Tests

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Two integration tests are intermittently failing due to timing/race condition issues. These tests fail regardless of recent code changes, indicating pre-existing flakiness in the test implementation.

### Failing Tests

#### 1. `test_dashboard_shows_recent_slideshows`

**Location:** `tests/integration/test_dashboard.py`

**Error:**
```
AssertionError: Locator expected to be visible
Actual value: None
Error: element(s) not found
Call log:
  - Expect "to_be_visible" with timeout 5000ms
  - waiting for locator(".card").filter(has=locator(".card-header:has-text('Recent Slideshows')")).locator("text=Test Slideshow ...")
```

**Likely Cause:**
- The test creates a slideshow via API and immediately expects it to appear in the dashboard UI
- The React frontend may not have refreshed/re-fetched data yet
- The 5000ms timeout may not be sufficient, or the locator strategy may be too specific

#### 2. `test_info_overlay_respects_display_setting`

**Location:** `tests/integration/test_display_playback.py`

**Error:**
```
playwright._impl._errors.Error: Page.reload: net::ERR_ABORTED; maybe frame was detached?
Call log:
  - waiting for navigation until "load"
```

**Likely Cause:**
- The test triggers a page reload (possibly via SSE event or explicit reload)
- The page reload is happening while another navigation or operation is in progress
- Race condition between SSE-triggered reload and test-initiated operations

## Investigation Results

### 1. `test_dashboard_shows_recent_slideshows` Analysis

**Root Cause Identified:**
- The `test_slideshow` fixture creates a slideshow via API before the test runs
- The test then logs in, which navigates to the dashboard
- The Dashboard React component fetches slideshows in `useEffect()` when it mounts
- The "Recent Slideshows" section only shows slideshows where `is_active=true` (line 146: `activeSlideShows.length === 0`)
- The test uses a 5000ms timeout which should be sufficient, but the locator may be matching before data is loaded

**Fix Strategy:**
- Wait for dashboard to finish loading (ensure loading spinner is gone) before checking for slideshow
- Increase timeout to 10000ms for more reliability
- The slideshow should appear since it's created with `is_active: True` by the fixture

### 2. `test_info_overlay_respects_display_setting` Analysis

**Root Cause Identified:**
- The display page has an SSE client (`DisplaySSEClient` in `slideshow.html`)
- The SSE client listens for `display.configuration_changed` events
- When this event fires, it automatically calls `window.location.reload()`
- The test updates the display via API at line 914: `http_client.put(f"/api/v1/displays/{display_id}", json={"show_info_overlay": True})`
- This triggers a `display.configuration_changed` SSE event
- The SSE event causes the page to reload automatically
- The test then calls `page.reload()` at line 922
- **Race condition**: Two concurrent reloads cause "net::ERR_ABORTED; maybe frame was detached?"

**Fix Strategy:**
- After updating the display via API, wait for the SSE-triggered reload to complete naturally
- Use `page.wait_for_load_state()` instead of explicit `page.reload()`
- OR: Use `page.wait_for_url()` to detect that the page has reloaded via SSE

## Implementation Plan

### Milestone 1: Fix Both Tests (M1)

**Task 1.1:** Fix `test_dashboard_shows_recent_slideshows`
- Wait for loading spinner to disappear before checking for slideshow content
- Increase timeout to 10000ms for reliability
- Add assertion that loading is complete

**Task 1.2:** Fix `test_info_overlay_respects_display_setting`
- Remove explicit `page.reload()` call
- Wait for SSE-triggered reload to complete using `page.wait_for_load_state("domcontentloaded")`
- Add small delay after API update to allow SSE event to propagate
- Use `page.wait_for_selector()` to detect when the page has reloaded with new content

### Milestone 2: Acceptance Criteria (M2)

**Task 2.1:** Run tests multiple times to verify stability
- Run both specific tests 5+ times each
- Run full integration test suite

**Task 2.2:** Documentation and cleanup
- Update this feature document with completion status
- Move to `docs/features/completed/`

## Acceptance Criteria

- [ ] Both tests pass consistently (run 5+ times without failure)
- [ ] Tests remain meaningful (don't just add arbitrary long waits)
- [ ] No new test flakiness introduced
- [ ] All other tests continue to pass
