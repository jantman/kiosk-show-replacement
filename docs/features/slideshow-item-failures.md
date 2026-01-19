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

### Milestone 1: Fix Field Name Mapping
**Prefix:** `SIF-1`

Update the backend to accept frontend field names and map them to model columns, and update the model's `to_dict()` to include frontend-friendly aliases.

**Tasks:**
1. **SIF-1.1** Update `SlideshowItem.to_dict()` to include both database column names and frontend aliases for backward compatibility
2. **SIF-1.2** Update `create_slideshow_item` API handler to accept both naming conventions
3. **SIF-1.3** Update `update_slideshow_item` API handler to:
   - Accept both naming conventions
   - Handle `content_type` updates
   - Handle `file_path`/`content_file_path` updates
   - Handle `is_active` updates
4. **SIF-1.4** Run existing tests to ensure no regressions

### Milestone 2: Enhance Integration Tests
**Prefix:** `SIF-2`

Update integration tests to properly verify data persistence.

**Tasks:**
1. **SIF-2.1** Update `test_add_text_item` to verify text content is persisted (reload page and check)
2. **SIF-2.2** Update `test_edit_existing_item` to verify:
   - Form is pre-populated with all saved values (not just title)
   - All field changes are persisted after save
3. **SIF-2.3** Add test to verify duration override is persisted
4. **SIF-2.4** Run full test suite to ensure all tests pass

### Milestone 3: Acceptance Criteria
**Prefix:** `SIF-3`

Final validation and documentation.

**Tasks:**
1. **SIF-3.1** Manual testing of all acceptance criteria
2. **SIF-3.2** Ensure all nox sessions pass
3. **SIF-3.3** Move feature file to `docs/features/completed/`

## Progress Tracking

| Milestone | Status | Notes |
|-----------|--------|-------|
| M1: Fix Field Name Mapping | Not Started | |
| M2: Enhance Integration Tests | Not Started | |
| M3: Acceptance Criteria | Not Started | |

## Acceptance Criteria

- [ ] Creating a text item with content and duration override persists all values
- [ ] Creating an image item with uploaded file persists the image association
- [ ] Creating a video item persists the video content
- [ ] Editing any item type shows current values in the form
- [ ] Saving edits persists all changed values
- [ ] Items list displays correct values for all fields
