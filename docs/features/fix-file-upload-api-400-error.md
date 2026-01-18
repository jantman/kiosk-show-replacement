# Fix File Upload API 400 Error

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

When uploading files (images or videos) through the React admin interface, the upload API endpoints (`/api/v1/uploads/image` and `/api/v1/uploads/video`) return a 400 Bad Request error.

## Problem

Integration tests `test_add_image_item_via_file_upload` and `test_add_video_item_via_file_upload` in `tests/integration/test_slideshow_items.py` fail because file uploads are rejected with HTTP 400.

### Evidence from Test Logs

```
POST /api/v1/uploads/image - 400 (5ms)
POST /api/v1/uploads/video - 400 (5ms)
```

### Possible 400 Error Causes

Looking at `kiosk_show_replacement/api/v1.py`, the upload endpoints return 400 for:
1. `"No file provided"` - if `file` not in request.files or filename is empty
2. `"slideshow_id is required"` - if slideshow_id missing from form data
3. `"Invalid slideshow_id"` - if slideshow_id can't be parsed as int

## Investigation Needed

1. **Verify form data construction** - Check if `SlideshowItemForm.tsx` correctly appends `slideshow_id` to the FormData
2. **Check API request format** - Verify the multipart form data is being sent correctly by the browser
3. **Test manually** - Use browser dev tools or curl to test the upload endpoint directly
4. **Check CORS/authentication** - Ensure cookies/credentials are being sent with the fetch request

## Files Involved

### Frontend
- `frontend/src/components/SlideshowItemForm.tsx` - Contains `handleFileUpload` function
- `frontend/src/contexts/AuthContext.tsx` - Contains `apiCall` function that makes requests

### Backend
- `kiosk_show_replacement/api/v1.py` - Upload endpoints at lines 1432-1557

## Reproduction Steps

1. Run the integration tests: `poetry run nox -s test-integration`
2. Observe `test_add_image_item_via_file_upload` fails
3. Check server logs showing `POST /api/v1/uploads/image -> 400`

Or manually:
1. Run the application (`python run.py` and `cd frontend && npm run dev`)
2. Log in to the admin interface
3. Create or open a slideshow
4. Click "Add Item"
5. Select content type "Image"
6. Upload a file
7. Check browser Network tab for 400 response and response body for error message

## Proposed Solution

Pending investigation results. Likely fixes:
1. Ensure `slideshowId` prop is defined when form renders
2. Add explicit `credentials: 'include'` to fetch options if not present
3. Debug the actual error message from the 400 response

## Acceptance Criteria

1. File upload tests pass:
   - `test_add_image_item_via_file_upload`
   - `test_add_video_item_via_file_upload`
2. Manual upload via admin UI works correctly
3. Both image and video uploads function properly
