# SSE Slideshow Update Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We did some recent work (see `completed/bug-display-settings-not-realtime.md`) on SSE bugs where slideshows did not update after changes without a manual browser refresh. We have fixed it so changes to the default slideshow duration are picked up immediately by displays, but I've tried adding, deleting, and editing slides within a slideshow and those changes are not being reflected on the display. I think we need to revisit the integration tests that were added during our earlier work to ensure they're complete, and then fix this bug. If needed, I can use the Claude Chrome extension and/or Chrome DevTools MCP server to help explore the live UI with you to analyze this bug.

---

## Technical Analysis

### Root Cause: Slide Item CRUD Operations Do Not Trigger SSE Broadcasts

The previous bug fix (`completed/bug-display-settings-not-realtime.md`) addressed the issue where **slideshow-level** updates (via `update_slideshow()`) were not reaching displays. That fix added the `broadcast_slideshow_update()` call to the slideshow update endpoint and fixed the event type mismatch.

However, individual **slide item** operations (create, update, delete, reorder) use separate API endpoints that do NOT call `broadcast_slideshow_update()`.

The following endpoints in `kiosk_show_replacement/api/v1.py` are affected:

| Endpoint | Function | Lines | Issue |
|----------|----------|-------|-------|
| `POST /api/v1/slideshows/<id>/items` | `create_slideshow_item()` | 359-418 | No SSE broadcast |
| `PUT /api/v1/slideshow-items/<id>` | `update_slideshow_item()` | 421-469 | No SSE broadcast |
| `DELETE /api/v1/slideshow-items/<id>` | `delete_slideshow_item()` | 472-502 | No SSE broadcast |
| `POST /api/v1/slideshow-items/<id>/reorder` | `reorder_slideshow_item()` | 505-573 | No SSE broadcast |

**Contrast with Working Behavior:**

The `update_slideshow()` endpoint (lines 170-252) correctly calls `broadcast_slideshow_update()` at line 239:
```python
broadcast_slideshow_update(
    slideshow,
    "updated",
    {"updated_by": current_user.username, "updated_fields": list(data.keys())},
)
```

The display pages already have JavaScript listeners for `slideshow.updated` events (in `templates/display/slideshow.html:801`, `templates/display/index.html:226`, `templates/display/no_content.html:182`) that reload the page when received. The infrastructure is in place; we just need to trigger the events.

**Fix Required:**

Add a call to `broadcast_slideshow_update(slideshow, "updated", {...})` after the `db.session.commit()` in each of the four slide item endpoints.

---

## Implementation Plan

### Milestone 1: Regression Tests (M1)

Create integration tests that verify the bug exists. Tests should initially fail and pass after the fix.

#### M1.1 - Test slide item create SSE broadcast to displays

Create an integration test that:
1. Creates a slideshow assigned to a display
2. Establishes SSE connection for that display (using the display SSE endpoint)
3. Creates a new slide item in the slideshow via API
4. Verifies that a `slideshow.updated` SSE event is sent to the display connection

#### M1.2 - Test slide item update SSE broadcast to displays

Create an integration test that:
1. Creates a slideshow with an existing slide, assigned to a display
2. Establishes SSE connection for that display
3. Updates the slide item via API
4. Verifies that a `slideshow.updated` SSE event is sent to the display connection

#### M1.3 - Test slide item delete SSE broadcast to displays

Create an integration test that:
1. Creates a slideshow with an existing slide, assigned to a display
2. Establishes SSE connection for that display
3. Deletes the slide item via API
4. Verifies that a `slideshow.updated` SSE event is sent to the display connection

#### M1.4 - Test slide item reorder SSE broadcast to displays

Create an integration test that:
1. Creates a slideshow with at least 2 slides, assigned to a display
2. Establishes SSE connection for that display
3. Reorders a slide item via API
4. Verifies that a `slideshow.updated` SSE event is sent to the display connection

### Milestone 2: Fix Slide Item SSE Broadcasts (M2)

#### M2.1 - Add SSE broadcast to create_slideshow_item()

Modify `create_slideshow_item()` in `kiosk_show_replacement/api/v1.py` to call `broadcast_slideshow_update()` with event type `"updated"` after the database commit.

#### M2.2 - Add SSE broadcast to update_slideshow_item()

Modify `update_slideshow_item()` in `kiosk_show_replacement/api/v1.py` to call `broadcast_slideshow_update()` with event type `"updated"` after the database commit.

#### M2.3 - Add SSE broadcast to delete_slideshow_item()

Modify `delete_slideshow_item()` in `kiosk_show_replacement/api/v1.py` to call `broadcast_slideshow_update()` with event type `"updated"` after the database commit.

#### M2.4 - Add SSE broadcast to reorder_slideshow_item()

Modify `reorder_slideshow_item()` in `kiosk_show_replacement/api/v1.py` to call `broadcast_slideshow_update()` with event type `"updated"` after the database commit.

### Milestone 3: Acceptance Criteria (M3)

#### M3.1 - Verify all regression tests pass

Run the regression tests created in M1 and confirm they now pass.

#### M3.2 - Run all nox tests

Ensure all existing tests still pass: `poetry run -- nox -s test-3.14`, `poetry run -- nox -s test-integration`, `poetry run -- nox -s test-e2e`.

#### M3.3 - Documentation review

Review and update documentation if needed (CLAUDE.md, README.md, docs/).

#### M3.4 - Move feature file to completed

Move this feature markdown file from `docs/features/` to `docs/features/completed/`.

---

## Progress

- [ ] Milestone 1: Regression Tests
  - [ ] M1.1 - Test slide item create SSE broadcast to displays
  - [ ] M1.2 - Test slide item update SSE broadcast to displays
  - [ ] M1.3 - Test slide item delete SSE broadcast to displays
  - [ ] M1.4 - Test slide item reorder SSE broadcast to displays
- [ ] Milestone 2: Fix Slide Item SSE Broadcasts
  - [ ] M2.1 - Add SSE broadcast to create_slideshow_item()
  - [ ] M2.2 - Add SSE broadcast to update_slideshow_item()
  - [ ] M2.3 - Add SSE broadcast to delete_slideshow_item()
  - [ ] M2.4 - Add SSE broadcast to reorder_slideshow_item()
- [ ] Milestone 3: Acceptance Criteria
  - [ ] M3.1 - Verify all regression tests pass
  - [ ] M3.2 - Run all nox tests
  - [ ] M3.3 - Documentation review
  - [ ] M3.4 - Move feature file to completed
