# Bug: Admin Changes Not Applied to Displays in Real-Time

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Changes made in the Admin UI are not propagated to connected displays in real-time.

### Display Settings Changes

**Steps to reproduce:**
1. Have a display connected and live (e.g., at `/display/{name}`)
2. In the Admin UI, edit the display settings
3. Enable "Show Info Overlay" (or toggle another setting)
4. Save the changes

**Observed behavior:**
- The setting change is saved in the Admin UI
- The display does not reflect the change until the page is manually refreshed

**Expected behavior:**
- Display setting changes should be pushed to the display via SSE and applied immediately without requiring a manual page refresh

### Slideshow Changes

**Steps to reproduce:**
1. Have a display connected and live, showing a slideshow
2. In the Admin UI, modify the slideshow (e.g., add/remove/reorder slides, change content)
3. Save the changes

**Observed behavior:**
- The slideshow changes are saved in the Admin UI
- The display continues showing the old slideshow content until the page is manually refreshed

**Expected behavior:**
- Slideshow changes should be pushed to the display via SSE and applied immediately without requiring a manual page refresh

---

## Technical Analysis

### Root Cause 1: Display Settings Not Broadcast

The `update_display()` endpoint in `kiosk_show_replacement/api/v1.py:738-818` updates display settings (like `show_info_overlay`, `name`, `location`, `description`) but does NOT broadcast any SSE events after saving.

Additionally, the `broadcast_display_update()` function only sends events to display connections when `event_type == "assignment_changed"`. For other event types like `configuration_changed`, it only broadcasts to admin connections.

The display page's JavaScript (`templates/display/slideshow.html:826-834`) DOES have a listener for `display.configuration_changed` events and reloads the page when received. However, no such event is ever sent when settings change.

**Fix Required:**
1. Call `broadcast_display_update()` with event type `"configuration_changed"` in `update_display()` when settings change
2. Update `broadcast_display_update()` to also send to the specific display connection for `"configuration_changed"` events (not just `"assignment_changed"`)

### Root Cause 2: Slideshow Updates Not Reaching Displays

The `update_slideshow()` endpoint in `kiosk_show_replacement/api/v1.py:164-247` correctly calls `broadcast_slideshow_update()` with event type `"updated"`.

However, `broadcast_slideshow_update()` (lines 1993-2039) has an event type mismatch:
- It sends `slideshow.updated` events to **admin** connections (correct)
- For **display** connections, it creates a DIFFERENT event: `display.slideshow_changed` (line 2027)

The display page's JavaScript (`templates/display/slideshow.html:789-798`) listens for `slideshow.updated` events, NOT `display.slideshow_changed`. This event type mismatch means displays never receive slideshow update notifications.

**Fix Required:**
- Update `broadcast_slideshow_update()` to send `slideshow.updated` events to display connections (instead of `display.slideshow_changed`)

---

## Implementation Plan

### Milestone 1: Regression Tests (M1)

Create integration tests that verify the bug exists. Tests should initially fail and pass after the fix.

#### M1.1 - Test display settings SSE broadcast
Create an integration test that:
1. Creates a display with SSE connection
2. Updates display settings (e.g., `show_info_overlay`)
3. Verifies that a `display.configuration_changed` SSE event is sent to the display connection

#### M1.2 - Test slideshow update SSE broadcast to displays
Create an integration test that:
1. Creates a slideshow assigned to a display
2. Establishes SSE connection for that display
3. Updates the slideshow
4. Verifies that a `slideshow.updated` SSE event is sent to the display connection

### Milestone 2: Fix Display Settings SSE Broadcast (M2)

#### M2.1 - Update broadcast_display_update() to send to displays for configuration changes
Modify `broadcast_display_update()` in `kiosk_show_replacement/api/v1.py` to also send events to the specific display connection when `event_type == "configuration_changed"` (in addition to the existing `"assignment_changed"` logic).

#### M2.2 - Add SSE broadcast call in update_display()
Modify `update_display()` in `kiosk_show_replacement/api/v1.py` to call `broadcast_display_update()` with event type `"configuration_changed"` when display settings change.

### Milestone 3: Fix Slideshow Update SSE Broadcast (M3)

#### M3.1 - Fix event type in broadcast_slideshow_update()
Modify `broadcast_slideshow_update()` in `kiosk_show_replacement/api/v1.py` to send `slideshow.updated` events directly to display connections instead of creating a separate `display.slideshow_changed` event.

### Milestone 4: Acceptance Criteria (M4)

#### M4.1 - Verify all regression tests pass
Run the regression tests created in M1 and confirm they now pass.

#### M4.2 - Run all nox tests
Ensure all existing tests still pass: `poetry run -- nox -s test-3.14`, `poetry run -- nox -s test-integration`, `poetry run -- nox -s test-e2e`.

#### M4.3 - Documentation review
Review and update documentation if needed (CLAUDE.md, README.md, docs/).

#### M4.4 - Move feature file to completed
Move this feature markdown file from `docs/features/` to `docs/features/completed/`.

---

## Progress

- [x] Milestone 1: Regression Tests
  - [x] M1.1 - Test display settings SSE broadcast
  - [x] M1.2 - Test slideshow update SSE broadcast to displays
- [x] Milestone 2: Fix Display Settings SSE Broadcast
  - [x] M2.1 - Update broadcast_display_update() to send to displays for configuration changes
  - [x] M2.2 - Add SSE broadcast call in update_display()
- [x] Milestone 3: Fix Slideshow Update SSE Broadcast
  - [x] M3.1 - Fix event type in broadcast_slideshow_update()
- [x] Milestone 4: Acceptance Criteria
  - [x] M4.1 - Verify all regression tests pass
  - [x] M4.2 - Run all nox tests
  - [x] M4.3 - Documentation review
  - [x] M4.4 - Move feature file to completed
