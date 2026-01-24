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

**Root Causes Identified:**

1. The `test_slideshow` fixture creates a slideshow via API before the test runs
2. The dashboard's "Recent Slideshows" section shows `activeSlideShows.slice(0, 5)` - only the first 5 active slideshows
3. The API endpoint `/api/v1/slideshows` returned slideshows without any ordering, so the order was undefined (essentially by primary key)
4. As integration tests run, they create many slideshows that accumulate (cleaned up after each test, but new ones get higher IDs)
5. The test slideshow (created most recently) might not appear in the first 5 if other slideshows have lower IDs
6. The "Recent Slideshows" label was misleading - the API didn't actually order by recency

**Fixes Applied:**
1. Modified `/api/v1/slideshows` to order results by `updated_at DESC` so most recently updated slideshows appear first (matches "Recent Slideshows" label)
2. Added page refresh after login to ensure fresh data is fetched from the API
3. Increased timeout to 10000ms for better reliability
4. Wait for list items to appear before checking for specific slideshow name

### 2. `test_info_overlay_respects_display_setting` Analysis

**Root Cause Identified:**
- The display page has an SSE client (`DisplaySSEClient` in `slideshow.html`)
- The SSE client listens for `display.configuration_changed` events
- When this event fires, it automatically calls `window.location.reload()`
- The test updates the display via API: `http_client.put(f"/api/v1/displays/{display_id}", json={"show_info_overlay": True})`
- This triggers a `display.configuration_changed` SSE event
- The SSE event causes the page to reload automatically
- The test then called `page.reload()` explicitly
- **Race condition**: Two concurrent reloads cause "net::ERR_ABORTED; maybe frame was detached?"

**Fix Applied:**
- Removed explicit `page.reload()` call
- Use `page.expect_navigation()` context manager to wait for the SSE-triggered navigation
- The API update now happens within the `expect_navigation` block, which waits for the SSE-triggered reload to complete

## Implementation Summary

### Changes Made

1. **`kiosk_show_replacement/api/v1.py`**:
   - Modified `list_slideshows()` to order results by `updated_at DESC`
   - This ensures "Recent Slideshows" actually shows the most recently updated slideshows first

2. **`tests/integration/test_dashboard.py`**:
   - Added page refresh after login to ensure fresh data is fetched
   - Added wait for list items to appear before checking for slideshow name
   - Increased timeout to 10000ms

3. **`tests/integration/test_display_playback.py`**:
   - Replaced explicit `page.reload()` with `page.expect_navigation()` context manager
   - The API update now happens within the navigation expectation, which waits for the SSE-triggered reload

### Test Results

- Both tests passed consistently across 5+ runs
- All 91 integration tests pass
- All 418 unit tests pass
- Type checking passes with no issues

## Acceptance Criteria

- [x] Both tests pass consistently (run 5+ times without failure)
- [x] Tests remain meaningful (don't just add arbitrary long waits)
- [x] No new test flakiness introduced
- [x] All other tests continue to pass
