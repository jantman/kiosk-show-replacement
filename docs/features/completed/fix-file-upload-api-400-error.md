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

## Root Cause Analysis

**The bug is in `frontend/src/hooks/useApi.ts` at line 95.**

The `useApi` hook routes upload requests to the `apiClient` based on the upload type (image/video). The code extracts the upload type using:

```typescript
const uploadType = url.split('/')[3];
```

For the URL `/api/v1/uploads/image`, splitting by `/` produces:
- Index 0: `''` (empty string)
- Index 1: `'api'`
- Index 2: `'v1'`
- Index 3: `'uploads'`  ← **BUG: code uses this index**
- Index 4: `'image'`    ← **correct index**

Because `uploadType` equals `'uploads'` instead of `'image'` or `'video'`, neither the `if (uploadType === 'image')` nor `else if (uploadType === 'video')` condition matches.

The code then falls through to the fallback path (lines 127+), which:
1. Sets `Content-Type: application/json` header (inappropriate for FormData)
2. Attempts a generic fetch request

When `Content-Type: application/json` is set for a FormData body, the browser doesn't serialize the multipart form data correctly, causing the server to not find the `file` or `slideshow_id` in the request, resulting in the 400 error.

## Implementation Plan

### Milestone 1: Fix the Bug and Harden Fallback

**Task 1.1**: Fix array index in `useApi.ts`
- Change line 95 from `url.split('/')[3]` to `url.split('/')[4]`
- File: `frontend/src/hooks/useApi.ts`

**Task 1.2**: Improve fallback to handle FormData correctly
- In the fallback path, detect when `options.body` is a `FormData` instance
- When FormData is detected, don't set `Content-Type: application/json` (let browser set the correct multipart boundary automatically)
- File: `frontend/src/hooks/useApi.ts`

**Task 1.3**: Add console.warn for unmatched endpoints
- Add a warning when the fallback path is used, especially for endpoints that look like they should have explicit handlers (e.g., `/api/v1/uploads/*`)
- This surfaces routing bugs during development
- File: `frontend/src/hooks/useApi.ts`

**Task 1.4**: Remove `@pytest.mark.xfail` markers from integration tests
- Remove xfail from `test_add_image_item_via_file_upload` (lines 36-39)
- Remove xfail from `test_add_video_item_via_file_upload` (lines 142-145)
- File: `tests/integration/test_slideshow_items.py`

### Milestone 2: Acceptance Criteria

**Task 2.1**: Run frontend linting
- Run `cd frontend && npm run lint` to ensure TypeScript changes pass linting

**Task 2.2**: Verify fix with integration tests
- Run `poetry run -- nox -s test-integration`
- Confirm `test_add_image_item_via_file_upload` passes
- Confirm `test_add_video_item_via_file_upload` passes

**Task 2.3**: Run all nox sessions
- Ensure all tests pass: `poetry run -- nox`

**Task 2.4**: Move feature document to completed folder
- Move `docs/features/fix-file-upload-api-400-error.md` to `docs/features/completed/`

## Acceptance Criteria

1. File upload tests pass:
   - `test_add_image_item_via_file_upload`
   - `test_add_video_item_via_file_upload`
2. Manual upload via admin UI works correctly
3. Both image and video uploads function properly
4. Fallback path correctly handles FormData without setting incorrect Content-Type
5. Console warning is logged when fallback is used for unmatched endpoints
6. All nox sessions pass

## Completion Status

**COMPLETED** - 2026-01-18

### Summary of Changes

1. **Fixed array index bug** in `frontend/src/hooks/useApi.ts` - Changed `url.split('/')[3]` to `url.split('/')[4]` to correctly extract upload type from URL

2. **Hardened fallback handler** in `frontend/src/hooks/useApi.ts`:
   - Added FormData detection to avoid setting `Content-Type: application/json` for multipart requests
   - Added `console.warn` in development mode when fallback is used for unmatched endpoints

3. **Removed xfail markers** from integration tests in `tests/integration/test_slideshow_items.py`

4. **Added mpeg/mpg support** to `ALLOWED_VIDEO_EXTENSIONS` in `kiosk_show_replacement/config/__init__.py` to support the test video asset

### Commits

- `FUAE-1.1`: Fix array index bug in useApi.ts upload routing
- `FUAE-1.2/1.3`: Harden fallback handler with FormData support and warnings
- `FUAE-1.4`: Remove xfail markers from file upload integration tests
- `FUAE-2.1`: Fix Vite environment check in useApi.ts
- `FUAE-2.2`: Add mpeg/mpg to allowed video extensions
- `FUAE-2.3`: Apply code formatting from nox format session

### Test Results

- All 366 unit tests pass
- All 64 integration tests pass (including both file upload tests)
- All nox sessions (format, lint, test-3.14) pass
