# Display Reload Button

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Sometimes when slideshows are changed, displays miss the SSE event notification. To address this, add a capability to manually send a slideshow update SSE message to a specific display, causing it to reload its slideshow.

This should be implemented as a new action button on the Displays admin page (`/admin/displays`). When clicked, the button should trigger an SSE message to the targeted display instructing it to reload its current slideshow.

---

## Implementation Plan

### Summary

This feature requires adding:
1. A new API endpoint to send reload commands to displays
2. A new SSE event type (`display.reload_requested`) that displays listen for
3. JavaScript handling in display templates to respond to reload events
4. A reload button in the React admin interface (Displays page)
5. Integration tests for the new functionality

### Milestones

#### Milestone 1: Backend API and SSE Event

**Tasks:**

**1.1: Add API endpoint for display reload**
- Add `POST /api/v1/displays/<int:display_id>/reload` endpoint in `kiosk_show_replacement/api/v1.py`
- The endpoint should:
  - Require authentication (existing `@require_auth` decorator)
  - Look up the display by ID
  - Return 404 if display not found
  - Send an SSE event to the specific display connection
  - Return success response with message

**1.2: Update SSE broadcast for reload events**
- Modify `broadcast_display_update()` in `kiosk_show_replacement/api/v1.py` to also send events to display connections when event_type is `"reload_requested"`
- The event data should include:
  - `display_id`
  - `display_name`
  - `timestamp`
  - `requested_by` (username of admin who triggered it)

**1.3: Add unit tests for the reload endpoint**
- Add tests to `tests/unit/test_api.py` for:
  - Successful reload request returns 200
  - Reload for non-existent display returns 404
  - Unauthenticated request returns 401/403

#### Milestone 2: Display Client JavaScript

**Tasks:**

**2.1: Add reload event listener to slideshow.html**
- In `kiosk_show_replacement/templates/display/slideshow.html`, add an event listener for `display.reload_requested`
- When received, call `window.location.reload()` to refresh the display
- Only reload if the event matches this display's name

**2.2: Add reload event listener to no_content.html and configure.html**
- These templates also use SSE for real-time updates
- Add the same event listener pattern to ensure reload works regardless of display state

#### Milestone 3: React Admin Interface

**Tasks:**

**3.1: Add reload button to Displays page**
- In `frontend/src/pages/Displays.tsx`, add a reload button (arrow-clockwise icon) to the action buttons column
- Button should be styled like existing action buttons (outline-primary or similar)
- Add `handleReloadDisplay(display: Display)` function that:
  - Makes POST request to `/api/v1/displays/{id}/reload`
  - Shows success message on success
  - Shows error message on failure

**3.2: Add API client method**
- In `frontend/src/utils/apiClient.ts`, add `reloadDisplay(id: number)` method
- Use `requestNoRetry` since this is a side-effect operation

**3.3: Add reload button to DisplayDetail page (optional)**
- In `frontend/src/pages/DisplayDetail.tsx`, add a reload button to the header button bar
- Provides convenience for reloading from the detail view

#### Milestone 4: Integration Tests

**Tasks:**

**4.1: Add integration tests for reload functionality**
- In `tests/integration/`, add tests that:
  - Verify reload button appears in the Displays table
  - Verify clicking reload button triggers API call
  - Verify success/error messages appear appropriately

#### Milestone 5: Acceptance Criteria

**Tasks:**

**5.1: Documentation review**
- Review and update documentation if needed (unlikely for this small feature)

**5.2: Test coverage verification**
- Ensure unit tests cover the new API endpoint
- Ensure integration tests cover the UI functionality

**5.3: Final test run**
- Run all nox sessions to ensure everything passes

**5.4: Move feature document to completed/**
- Move this file to `docs/features/completed/`

---

## Progress

- [ ] Milestone 1: Backend API and SSE Event
  - [ ] Task 1.1: Add API endpoint for display reload
  - [ ] Task 1.2: Update SSE broadcast for reload events
  - [ ] Task 1.3: Add unit tests for the reload endpoint
- [ ] Milestone 2: Display Client JavaScript
  - [ ] Task 2.1: Add reload event listener to slideshow.html
  - [ ] Task 2.2: Add reload event listener to no_content.html and configure.html
- [ ] Milestone 3: React Admin Interface
  - [ ] Task 3.1: Add reload button to Displays page
  - [ ] Task 3.2: Add API client method
  - [ ] Task 3.3: Add reload button to DisplayDetail page
- [ ] Milestone 4: Integration Tests
  - [ ] Task 4.1: Add integration tests for reload functionality
- [ ] Milestone 5: Acceptance Criteria
  - [ ] Task 5.1: Documentation review
  - [ ] Task 5.2: Test coverage verification
  - [ ] Task 5.3: Final test run
  - [ ] Task 5.4: Move feature document to completed/
