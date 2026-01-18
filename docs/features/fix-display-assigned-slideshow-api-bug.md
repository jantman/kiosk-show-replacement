# Fix Display assigned_slideshow API Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The Display Detail page's Quick Assignment section doesn't work correctly because the Display API doesn't return the `assigned_slideshow` object that the frontend expects.

## Problem

Integration tests `test_quick_assign_slideshow_via_click` and `test_unassign_slideshow` in `tests/integration/test_display_detail.py` fail because the Quick Assignment section doesn't show the currently assigned slideshow, and the unassign button doesn't appear.

### Root Cause

The frontend DisplayDetail component (`frontend/src/pages/DisplayDetail.tsx`) uses `display.assigned_slideshow` to render the Quick Assignment section:

```typescript
// Line 533
{display.assigned_slideshow ? (
  // Show assigned slideshow name and unassign button
) : (
  // Show "Drop slideshow here" message
)}
```

However, the Display model's `to_dict()` method (`kiosk_show_replacement/models/__init__.py:231`) only returns `current_slideshow_id`:

```python
def to_dict(self) -> dict:
    return {
        # ... other fields ...
        "current_slideshow_id": self.current_slideshow_id,
        # Note: No "assigned_slideshow" field
    }
```

The frontend expects `assigned_slideshow` to be a joined slideshow object with `name` and `description` properties, but the API never populates this field.

## Evidence from Test Failures

1. After assigning a slideshow via quick click, the "Drop slideshow here" message is still visible (because `display.assigned_slideshow` is undefined)
2. For a display created with `current_slideshow_id` set, the unassign button doesn't appear (because the conditional `display.assigned_slideshow ?` evaluates to false)

## Files Involved

### Backend
- `kiosk_show_replacement/models/__init__.py` - Display model `to_dict()` method (lines 231-257)
- `kiosk_show_replacement/api/v1.py` - Display API endpoints

### Frontend
- `frontend/src/pages/DisplayDetail.tsx` - Quick Assignment section (lines 523-593)
- `frontend/src/types/index.ts` - Display type definition (should have `assigned_slideshow` field)

## Proposed Solution

Option 1: Add `assigned_slideshow` to the Display API response (Recommended)

Modify `to_dict()` to include the joined slideshow:
```python
def to_dict(self) -> dict:
    assigned_slideshow = None
    if self.current_slideshow_id and self.current_slideshow:
        assigned_slideshow = {
            "id": self.current_slideshow.id,
            "name": self.current_slideshow.name,
            "description": self.current_slideshow.description
        }
    return {
        # ... existing fields ...
        "current_slideshow_id": self.current_slideshow_id,
        "assigned_slideshow": assigned_slideshow,
    }
```

Option 2: Fix the frontend to use `current_slideshow_id` and look up the slideshow from the slideshows list

The component already fetches slideshows and has a `getCurrentSlideshow()` helper:
```typescript
const getCurrentSlideshow = () => {
  if (!display?.current_slideshow_id) return null;
  return slideshows.find(s => s.id === display.current_slideshow_id);
};
```

The Quick Assignment section could use this pattern instead of `display.assigned_slideshow`.

## Implementation Plan

**Selected Approach**: Option 1 - Add `assigned_slideshow` to the Display API response

This is the cleanest solution because:
1. The frontend TypeScript type (`frontend/src/types/index.ts` line 29) already defines `assigned_slideshow?: Slideshow`
2. It's a single change in one location (the `to_dict()` method)
3. The Display model already has a relationship to Slideshow via `current_slideshow`

### Milestone 1: Backend Fix (DASA-1)

**Task 1.1**: Modify `Display.to_dict()` to include `assigned_slideshow`
- File: `kiosk_show_replacement/models/__init__.py`
- Add logic to include `assigned_slideshow` object when `current_slideshow_id` is set
- Include `id`, `name`, and `description` fields from the related Slideshow

**Task 1.2**: Add unit tests for the new `assigned_slideshow` field
- File: `tests/unit/test_models.py` (or appropriate test file)
- Test that `to_dict()` returns `assigned_slideshow: None` when no slideshow assigned
- Test that `to_dict()` returns proper `assigned_slideshow` object when slideshow is assigned

### Milestone 2: Acceptance Criteria (DASA-2)

**Task 2.1**: Verify integration tests pass
- Run `test_quick_assign_slideshow_via_click`
- Run `test_unassign_slideshow`

**Task 2.2**: Run all nox test sessions to ensure no regressions

**Task 2.3**: Move feature file to completed directory

## Acceptance Criteria

1. Quick Assignment section shows the currently assigned slideshow name when one is assigned
2. Unassign button appears when a slideshow is assigned
3. Clicking on an available slideshow successfully assigns it and updates the UI
4. Clicking unassign removes the assignment and updates the UI
5. Integration tests pass:
   - `test_quick_assign_slideshow_via_click`
   - `test_unassign_slideshow`

## Progress

- [x] Milestone 1: Backend Fix
  - [x] Task 1.1: Modify `Display.to_dict()` - Added `assigned_slideshow` field to Display model's `to_dict()` method
  - [x] Task 1.2: Add unit tests - Added `test_display_to_dict_with_assigned_slideshow` and updated `test_display_to_dict` to verify `assigned_slideshow` is None when not set
- [ ] Milestone 2: Acceptance Criteria
  - [ ] Task 2.1: Verify integration tests pass
  - [ ] Task 2.2: Run all nox sessions
  - [ ] Task 2.3: Move feature file to completed
