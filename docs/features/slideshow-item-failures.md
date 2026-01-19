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

## Acceptance Criteria

- [ ] Creating a text item with content and duration override persists all values
- [ ] Creating an image item with uploaded file persists the image association
- [ ] Creating a video item persists the video content
- [ ] Editing any item type shows current values in the form
- [ ] Saving edits persists all changed values
- [ ] Items list displays correct values for all fields
