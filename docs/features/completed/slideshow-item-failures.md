# Fix Slideshow Item Creation and Editing

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Slideshow item creation and editing in the admin frontend is fundamentally broken. When creating or editing slideshow items, values appear to save successfully (API returns 200/201, no errors logged) but the data is not actually persisted. This affects all item types: text, image, and video.

## Problem Description

The Create/Edit Slideshow Item modal on the slideshow edit page (`/admin/slideshows/{id}`) does not properly save item data:

1. **On Create:** Item is created but field values are not saved
2. **On Edit:** Existing values are not populated in the form, and saving does not persist changes
3. **Affects all content types:** Text, image, and video items all exhibit this behavior

### Symptoms

- Content type selection is not persisted
- Duration override values are not persisted
- Uploaded images are not associated with items (upload succeeds, but item has no image)
- Video items similarly fail to retain their content
- The items list does not display the configured values
- Opening the edit modal shows empty/default values instead of saved data

## Integration Test Investigation - Mandatory First Step

Perform this step BEFORE proceeding with any analysis or investigation!

We previously implemented integration tests for slideshow item adding and editing as described in Milestone 3 of `./completed/admin-integration-tests.md` and committed in `6eb6451`. These tests were intended to catch exactly the sort of bugs this feature is describing. Please analyze the existing integration tests for adding/editing slideshow items and determine why they are all passing when the functionality they're intended to test does not work.

## Log Analysis

Despite the failures, all API calls return success responses with no errors:

**Item Update (PUT):**
```
PUT /api/v1/slideshow-items/2 -> 200 OK
Log: "User admin updated item helloAgain3s"
```

**Image Upload:**
```
POST /api/v1/uploads/image -> 201
Log: "User admin uploaded image smallPhoto.jpg to slideshow test1"
```

**Item Creation:**
```
POST /api/v1/slideshows/1/items -> 201
Log: "User admin created item in slideshow test1"
```

No errors appear in Flask backend or Vite dev server logs.

## Likely Root Causes

1. **Frontend not sending field values:** The form may not be including all fields in the POST/PUT request body
2. **Backend not persisting fields:** The API may accept the request but ignore certain fields during save
3. **Field name mismatch:** Frontend and backend may use different field names (e.g., `content_type` vs `contentType`)
4. **Upload-to-item linking broken:** Uploaded files may not be properly linked to items when the item is created/updated

## Investigation Approach

1. Inspect browser DevTools Network tab to see actual request payloads being sent
2. Compare request payload field names with backend API expectations
3. Check backend API endpoint handlers for field processing logic
4. Verify database schema matches expected fields
5. Trace the data flow from form submission through API to database

## Investigation Results

### Integration Test Analysis

The existing integration tests in `tests/integration/test_slideshow_items.py` pass because they only verify:
1. Item **title** appears correctly in the table (title field works fine)
2. Content type **badge** displays correctly (content_type works in create)

The tests do **NOT** verify:
- Text content (`text_content`) is actually persisted
- URLs (`url`) are persisted
- File paths (`file_path`) are persisted
- Duration overrides (`duration`) are persisted
- That editing populates the form with saved values for these fields

### Root Cause: Field Name Mismatches

There is a systematic mismatch between field names used by the frontend and backend:

| Frontend Uses | Backend Expects | Model Column |
|--------------|-----------------|--------------|
| `url` | `content_url` | `content_url` |
| `file_path` | `content_file_path` | `content_file_path` |
| `text_content` | `content_text` | `content_text` |
| `duration` | `display_duration` | `display_duration` |

**Frontend sends** (from `SlideshowItemForm.tsx` lines 106-115):
```javascript
{
  title: "...",
  content_type: "...",
  url: "...",           // Backend expects content_url
  text_content: "...",  // Backend expects content_text
  file_path: "...",     // Backend expects content_file_path
  duration: 30,         // Backend expects display_duration
  is_active: true
}
```

**Backend expects** (from `api/v1.py` `create_slideshow_item` lines 352-363):
```python
SlideshowItem(
  title=data.get("title", ""),
  content_type=content_type,
  content_url=data.get("content_url"),      # Frontend sends url
  content_text=data.get("content_text"),    # Frontend sends text_content
  display_duration=data.get("display_duration", 30),  # Frontend sends duration
)
```

Additionally, the `update_slideshow_item` function is missing handlers for:
- `content_type` updates
- `content_file_path` / `file_path`
- `is_active`

### API Response Mismatch

The model's `to_dict()` method returns database column names:
```python
{
  "content_url": "...",
  "content_text": "...",
  "content_file_path": "...",
  "display_duration": 30
}
```

But the frontend TypeScript types expect:
```typescript
interface SlideshowItem {
  url?: string;
  file_path?: string;
  text_content?: string;
  duration?: number;
}
```

This causes the edit form to not populate with saved values (it looks for `url` but receives `content_url`).

## Implementation Plan

### Approach

1. **Test-Driven Development**: Write/enhance integration tests first (they should fail), then fix the code until tests pass.
2. **Frontend alignment**: Update frontend to use the same field names as the backend/database schema. The database schema is the source of truth.
3. **API verification**: Tests verify data persistence via API calls rather than UI inspection.

### Milestone 1: Enhance Integration Tests (TDD - Write Failing Tests)
**Prefix:** `SIF-1`

Update integration tests to properly verify data persistence for all item types. Tests should fail initially, confirming the bug exists.

**Tasks:**
1. **SIF-1.1** Update `test_add_text_item` to verify via API that `content_text` is persisted
2. **SIF-1.2** Update `test_add_url_item` to verify via API that `content_url` is persisted
3. **SIF-1.3** Update `test_add_image_item_via_url` to verify via API that `content_url` is persisted
4. **SIF-1.4** Update `test_add_image_item_via_file_upload` to verify via API:
   - `content_file_path` is persisted
   - Uploaded file size matches original test asset
5. **SIF-1.5** Update `test_add_video_item_via_url` to verify via API that `content_url` is persisted
6. **SIF-1.6** Update `test_add_video_item_via_file_upload` to verify via API:
   - `content_file_path` is persisted
   - Uploaded file size matches original test asset
7. **SIF-1.7** Update `test_edit_existing_item` to verify via API:
   - All field changes are persisted (not just title)
8. **SIF-1.8** Add test for editing a file upload item to change the file
9. **SIF-1.9** Add test to verify `display_duration` override is persisted
10. **SIF-1.10** Run tests and confirm they fail (documenting the bug)

### Milestone 2: Fix Frontend Field Names
**Prefix:** `SIF-2`

Update frontend TypeScript types and components to use backend field names.

**Tasks:**
1. **SIF-2.1** Update `frontend/src/types/index.ts` `SlideshowItem` interface:
   - `url` → `content_url`
   - `file_path` → `content_file_path`
   - `text_content` → `content_text`
   - `duration` → `display_duration`
2. **SIF-2.2** Update `frontend/src/components/SlideshowItemForm.tsx`:
   - Update form state interface to use backend field names
   - Update form field bindings and submission payload
3. **SIF-2.3** Update `frontend/src/pages/SlideshowDetail.tsx`:
   - Update references to item fields in the table display
4. **SIF-2.4** Run frontend tests (`npm run test:run`) to catch any missed references

### Milestone 3: Fix Backend Update Handler
**Prefix:** `SIF-3`

The `update_slideshow_item` API handler is missing support for several fields.

**Tasks:**
1. **SIF-3.1** Update `update_slideshow_item` in `api/v1.py` to handle:
   - `content_type` updates
   - `content_file_path` updates
   - `is_active` updates
2. **SIF-3.2** Run backend tests (`nox -s test-3.14`) to ensure no regressions

### Milestone 4: Verify Tests Pass
**Prefix:** `SIF-4`

Run the enhanced integration tests and confirm they now pass.

**Tasks:**
1. **SIF-4.1** Run integration tests (`nox -s test-integration`)
2. **SIF-4.2** Fix any remaining issues until all tests pass

### Milestone 5: Acceptance Criteria
**Prefix:** `SIF-5`

Final validation and documentation.

**Tasks:**
1. **SIF-5.1** Ensure all nox sessions pass
2. **SIF-5.2** Move feature file to `docs/features/completed/`

## Progress Tracking

| Milestone | Status | Notes |
|-----------|--------|-------|
| M1: Enhance Integration Tests | Complete | Tests enhanced to verify all field persistence via API |
| M2: Fix Frontend Field Names | Complete | TypeScript types and form updated to use backend field names |
| M3: Fix Backend Update Handler | Complete | Added content_type, content_file_path, is_active handlers |
| M4: Verify Tests Pass | Complete | All 66 integration tests pass (64 passed + 2 xpassed) |
| M5: Acceptance Criteria | Complete | All criteria met |

## Implementation Summary

### Commits

1. **2dc1623** - SIF-1: Enhanced integration tests with API verification
2. **9f9b2ac** - SIF-2: Frontend field name fixes (types, form, detail page)
3. **1975878** - SIF-3: Backend update handler (added missing fields)
4. **48ae4e8** - SIF-4: Backend create handler fix (added content_file_path)

### Key Changes

1. **Frontend Types** (`frontend/src/types/index.ts`):
   - Updated `SlideshowItem` interface to use backend field names

2. **Frontend Form** (`frontend/src/components/SlideshowItemForm.tsx`):
   - Updated form state to use `content_url`, `content_text`, `content_file_path`, `display_duration`
   - Fixed data binding in useEffect, validation, and submission

3. **Frontend Detail Page** (`frontend/src/pages/SlideshowDetail.tsx`):
   - Updated table display to use correct field names

4. **Backend API** (`kiosk_show_replacement/api/v1.py`):
   - `update_slideshow_item`: Added handlers for `content_type`, `content_file_path`, `is_active`
   - `create_slideshow_item`: Added `content_file_path`, fixed `display_duration` default, made `is_active` configurable

5. **Integration Tests** (`tests/integration/test_slideshow_items.py`):
   - All tests now verify field persistence via API calls
   - Added `test_add_text_item_with_duration_override`
   - Added `test_edit_file_upload_item`

## Acceptance Criteria

- [x] Creating a text item with content and duration override persists all values
- [x] Creating an image item with uploaded file persists the image association
- [x] Creating a video item persists the video content
- [x] Editing any item type shows current values in the form
- [x] Saving edits persists all changed values
- [x] Items list displays correct values for all fields
