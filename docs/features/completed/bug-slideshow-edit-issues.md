# Bug: Slideshow Edit Issues - Duration Not Saved and Undefined in Success Message

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Multiple issues occur when editing slideshow details in the Admin UI.

### Default Item Duration Not Persisted

**Steps to reproduce:**
1. Edit an existing slideshow's details
2. Change the "Default Item Duration" value
3. Save the changes

**Observed behavior:**
- After saving, the default item duration reverts to its previous value
- The change is not persisted

**Expected behavior:**
- The new default item duration value should be saved and persist

### Success Modal Shows "undefined"

**Steps to reproduce:**
1. Edit a slideshow's details
2. Save the changes

**Observed behavior:**
- A popup modal appears with the message: `"undefined" has been updated`

**Expected behavior:**
- The modal should display the slideshow name, e.g., `"My Slideshow" has been updated`

---

## Root Cause Analysis

### Bug #1: Default Item Duration Not Persisted

**Location:** `kiosk_show_replacement/api/v1.py`, lines 163-221, function `update_slideshow()`

**Problem:** The `update_slideshow()` endpoint only handles `name` and `description` fields. It ignores `default_item_duration`, `transition_type`, `is_active`, and `is_default` fields even though:
- The frontend `SlideshowForm` component correctly sends all these fields
- The `Slideshow` model supports all these fields

**Current code only processes:**
```python
if "name" in data:
    slideshow.name = name
if "description" in data:
    slideshow.description = data["description"]
```

**Missing handlers for:** `default_item_duration`, `transition_type`, `is_active`, `is_default`

### Bug #2: Success Modal Shows "undefined"

**Location:** `kiosk_show_replacement/api/v1.py`, lines 1848-1891, function `broadcast_slideshow_update()`

**Problem:** The `broadcast_slideshow_update()` function creates SSE event data using `slideshow.to_dict()`, which returns a `name` field, but the frontend's `LiveNotifications` component expects a `slideshow_name` field.

**Frontend expects (in `frontend/src/components/LiveNotifications.tsx`):**
```typescript
message: `"${data.slideshow_name}" has been updated`
```

**Backend provides:**
```python
data = slideshow.to_dict()  # Returns {"name": "...", ...} not {"slideshow_name": "..."}
```

**Comparison:** The `broadcast_display_update()` function correctly adds `data["display_name"] = display.name` for frontend compatibility.

---

## Implementation Plan

Since this is a small, targeted bug fix with clear scope, we will use a single milestone approach.

### Milestone 1: Bug Fixes and Tests (Prefix: `SLSH-1`)

#### Task 1.1: Fix `update_slideshow()` to handle all editable fields

**File:** `kiosk_show_replacement/api/v1.py`

Add handlers for missing fields after the existing `description` handler (line 200):

```python
if "default_item_duration" in data:
    duration = data["default_item_duration"]
    if not isinstance(duration, int) or duration < 1:
        raise ValidationError(
            "Default item duration must be a positive integer",
            field="default_item_duration"
        )
    slideshow.default_item_duration = duration

if "transition_type" in data:
    slideshow.transition_type = data["transition_type"]

if "is_active" in data:
    slideshow.is_active = data["is_active"]

if "is_default" in data:
    is_default = data["is_default"]
    if is_default:
        # Clear any existing default slideshow
        Slideshow.query.filter(
            Slideshow.is_default == True,
            Slideshow.id != slideshow_id
        ).update({"is_default": False})
    slideshow.is_default = is_default
```

#### Task 1.2: Fix `broadcast_slideshow_update()` to include `slideshow_name`

**File:** `kiosk_show_replacement/api/v1.py`

Add `slideshow_name` field after `slideshow.to_dict()` call (around line 1863):

```python
data = slideshow.to_dict()
# Add slideshow_name field for frontend compatibility (frontend expects slideshow_name,
# but to_dict() returns 'name')
data["slideshow_name"] = slideshow.name
```

#### Task 1.3: Add/update unit tests for `update_slideshow()` endpoint

**File:** `tests/unit/test_api_v1.py` (or appropriate test file)

Add tests to verify:
- Updating `default_item_duration` persists correctly
- Updating `transition_type` persists correctly
- Updating `is_active` persists correctly
- Updating `is_default` persists correctly and clears other defaults
- Invalid `default_item_duration` (negative, non-integer) returns validation error

#### Task 1.4: Add unit test for SSE event including `slideshow_name`

Verify that `broadcast_slideshow_update()` includes `slideshow_name` in the event data.

### Milestone 2: Acceptance Criteria (Prefix: `SLSH-2`)

#### Task 2.1: Verify all nox sessions pass
- Run `poetry run -- nox -s format`
- Run `poetry run -- nox -s lint`
- Run `poetry run -- nox -s test-3.14`
- Run `poetry run -- nox -s type_check`
- Run `poetry run -- nox -s test-integration`
- Run `poetry run -- nox -s test-e2e`

#### Task 2.2: Move feature file to completed
- Move this file to `docs/features/completed/`

---

## Progress

- [x] Milestone 1: Bug Fixes and Tests
  - [x] Task 1.1: Fix `update_slideshow()` to handle all editable fields
  - [x] Task 1.2: Fix `broadcast_slideshow_update()` to include `slideshow_name`
  - [x] Task 1.3: Add unit tests for updated endpoint
  - [x] Task 1.4: Add unit test for SSE event
- [x] Milestone 2: Acceptance Criteria
  - [x] Task 2.1: Verify all nox sessions pass
  - [x] Task 2.2: Move feature file to completed
