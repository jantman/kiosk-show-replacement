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

## Acceptance Criteria

1. Quick Assignment section shows the currently assigned slideshow name when one is assigned
2. Unassign button appears when a slideshow is assigned
3. Clicking on an available slideshow successfully assigns it and updates the UI
4. Clicking unassign removes the assignment and updates the UI
5. Integration tests pass:
   - `test_quick_assign_slideshow_via_click`
   - `test_unassign_slideshow`
