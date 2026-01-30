# Admin Slide Inactive

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

When a slideshow slide is changed to inactive (Active false) via the admin UI, it disappears from the admin UI! There's no way to reactivate it! Inactive slides should still be shown in the admin UI (so that they can be reactivated if/when desired) but should be visually distinct such as being grayed out.

We need to fix this bug while ensuring that it does not change the behavior for actual slideshows; i.e. inactive slides should be visible and edit-able in the admin UI but still not appear in a slideshow.

Before fixing this, we should add the following integration tests:

1. Ability to see inactive slides in the admin UI (currently failing; should pass when our bug fix is complete).
2. Ability to re-activate an inactive slide via the admin UI (currently failing; should pass when our bug fix is complete).
3. If we don't already have a test for this, inactive slides are not included in slideshow display (should already be passing).

---

## Implementation Plan

### Root Cause Analysis

The bug occurs because the API endpoints filter slides by `is_active=True` before returning them:

1. **`GET /api/v1/slideshows/<id>`** (v1.py line ~160): Returns items filtered to only active
2. **`GET /api/v1/slideshows/<id>/items`** (v1.py line ~345): Returns items filtered to only active

When a slide is marked inactive, it never gets returned to the React admin UI, so users cannot see or reactivate it.

The display playback endpoint correctly filters inactive slides and should continue to do so.

### Solution Approach

Add an optional query parameter `include_inactive` (defaulting to `false`) to the relevant API endpoints. This preserves the current default behavior while allowing the admin UI to explicitly request inactive slides.

**API Changes:**
- `GET /api/v1/slideshows/<id>?include_inactive=true` - Include inactive items in response
- `GET /api/v1/slideshows/<id>/items?include_inactive=true` - Return all items including inactive

### Files to Modify

| File | Change |
|------|--------|
| `kiosk_show_replacement/api/v1.py` | Add `include_inactive` query parameter to relevant endpoints |
| `frontend/src/pages/SlideshowDetail.tsx` | Pass `include_inactive=true` and style inactive slides (grayed out) |
| `tests/integration/test_admin_slides.py` | New file with regression tests |

### Files NOT to Modify

| File | Reason |
|------|--------|
| `kiosk_show_replacement/display/views.py` | Must continue filtering inactive slides for display playback |

---

## Milestones

### Milestone 1: Regression Tests (ASI-1)

Create integration tests that initially fail, demonstrating the bug.

**Tasks:**

- **ASI-1.1**: Create `tests/integration/test_admin_slides.py` with a test that verifies inactive slides remain visible in the admin UI (should fail initially)
- **ASI-1.2**: Add test that verifies inactive slides can be reactivated via the admin UI (should fail initially)
- **ASI-1.3**: Verify existing test coverage for inactive slides not appearing in display playback (should already pass; add test if missing)

**Commit prefix:** `ASI-1`

### Milestone 2: Backend API Fix (ASI-2)

Add `include_inactive` query parameter to API endpoints, defaulting to `false` to preserve existing behavior.

**Tasks:**

- **ASI-2.1**: Update `get_slideshow_by_id()` to accept `include_inactive` query parameter; when `true`, include inactive items in response
- **ASI-2.2**: Update `list_slideshow_items()` to accept `include_inactive` query parameter; when `true`, return all items
- **ASI-2.3**: Add unit tests for the new query parameter behavior
- **ASI-2.4**: Verify display playback still filters inactive slides correctly (existing test should pass)

**Commit prefix:** `ASI-2`

### Milestone 3: Frontend UI Update (ASI-3)

Update React admin UI to request and display inactive slides.

**Tasks:**

- **ASI-3.1**: Update `SlideshowDetail.tsx` API calls to pass `include_inactive=true` query parameter
- **ASI-3.2**: Style inactive slides with reduced opacity/grayed out appearance
- **ASI-3.3**: Ensure the "Active" toggle/badge is clearly visible and actionable for inactive slides
- **ASI-3.4**: Verify all regression tests from Milestone 1 now pass

**Commit prefix:** `ASI-3`

### Milestone 4: Acceptance Criteria (ASI-4)

Final validation and documentation.

**Tasks:**

- **ASI-4.1**: Ensure all nox sessions pass (`test-3.14`, `test-integration`, `test-e2e`, `lint`, `type_check`)
- **ASI-4.2**: Review and update documentation if needed (none expected for this bug fix)
- **ASI-4.3**: Move feature file to `docs/features/completed/`

**Commit prefix:** `ASI-4`

---

## Progress

- [ ] Milestone 1: Regression Tests
- [ ] Milestone 2: Backend API Fix
- [ ] Milestone 3: Frontend UI Update
- [ ] Milestone 4: Acceptance Criteria
