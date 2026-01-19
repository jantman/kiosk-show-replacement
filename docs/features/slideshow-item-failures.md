# Slideshow Item Failures

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks issues with slideshow item creation and editing where data appears to save successfully but is not actually persisted.

## Issues

### 1. Slideshow Item Values Not Persisting

**Location:** Slideshow edit page - Create/Edit Slideshow Item modal

**Description:** When creating or editing slideshow items, certain values are not being persisted:
- Created a slide with text content type and duration override of 3
- Neither value was persisted after creation
- Values do not appear in the Slideshow Items list
- Values do not appear in the Edit Slideshow Item modal
- Filling in values on the edit modal and saving still does not persist them

**Steps to Reproduce:**
1. Go to a slideshow's edit page
2. Add a new slideshow item
3. Set content type to "text" and duration override to 3
4. Save the item
5. Observe that the values are not shown in the items list
6. Open the edit modal for that item
7. Observe that the values are not populated
8. Fill in the values again and save
9. Observe that they still do not persist

**Expected:** All slideshow item values should be properly saved and displayed.

**Log Analysis:**
- Flask backend logs show no errors
- `PUT /api/v1/slideshow-items/2` returns 200 OK
- Log message: "User admin updated item helloAgain3s"
- Vite dev server logs show no frontend errors

**Likely Causes:**
1. Frontend may not be sending `content_type` and `duration_override` in the PUT request body
2. Backend may be accepting the request but not persisting those specific fields
3. GET response may not be returning those fields to populate the UI

**Status:** Open

### 2. Uploaded Images Not Associated with Slideshow Items

**Location:** Slideshow edit page - Create Slideshow Item modal

**Description:** When creating a slideshow item with an uploaded image:
- The image upload appears to succeed
- The item creation appears to succeed
- However, when editing the item, no image is associated with it

**Steps to Reproduce:**
1. Go to a slideshow's edit page
2. Add a new slideshow item
3. Upload an image file
4. Save the item
5. Open the edit modal for that item
6. Observe that no image is associated

**Log Analysis:**
- `POST /api/v1/uploads/image` returns 201: "User admin uploaded image smallPhoto.jpg to slideshow test1"
- `POST /api/v1/slideshows/1/items` returns 201: "User admin created item in slideshow test1"
- No errors in Flask or Vite logs

**Likely Causes:**
1. The uploaded image ID/path may not be sent when creating the slideshow item
2. The image association may not be persisted in the database
3. Similar root cause to issue #1 - frontend/backend field handling mismatch

**Status:** Open
