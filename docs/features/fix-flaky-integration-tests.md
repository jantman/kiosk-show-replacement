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

## Investigation Needed

Before implementing fixes, investigate:

1. **test_dashboard_shows_recent_slideshows:**
   - Is the slideshow actually being created before the assertion?
   - Is there an SSE event that should trigger a dashboard refresh?
   - Should the test wait for a specific SSE event or API response before checking?

2. **test_info_overlay_respects_display_setting:**
   - What triggers the page reload in this test?
   - Is the SSE connection causing an unexpected reload?
   - Should the test disable SSE or handle the reload more gracefully?

## Acceptance Criteria

- [ ] Both tests pass consistently (run 5+ times without failure)
- [ ] Tests remain meaningful (don't just add arbitrary long waits)
- [ ] No new test flakiness introduced
- [ ] All other tests continue to pass
