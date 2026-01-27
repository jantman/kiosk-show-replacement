# Video URL Slides Missing Duration Detection and Format Check

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

When a video slide is added or edited using a URL instead of a file upload, the video duration detection and video format validation do not occur. These checks only appear to run for uploaded video files.

This means:
- Video slides added via URL will not have their duration automatically detected
- Invalid or unsupported video formats provided via URL are not caught during slide creation/editing

The duration detection and format checking logic needs to be extended to also handle video URLs.

## Implementation Plan

### Background Analysis

The existing video validation and duration detection code in `kiosk_show_replacement/storage.py` uses `ffprobe` (from ffmpeg) to:
1. Extract video duration via `get_video_duration()`
2. Extract codec info via `get_video_codec_info()`
3. Validate browser-compatible formats via `validate_video_format()`

These functions currently only accept local file paths. However, `ffprobe` natively supports remote URLs, so the core approach will be to:
1. Modify the storage functions to also accept URLs
2. Create a new API endpoint for validating video URLs
3. Update the frontend to call this endpoint when a video URL is entered

### Milestone 1: Backend - Extend Storage Functions for URL Support

**Prefix: VideoURLValidation-1**

#### Task 1.1: Modify `get_video_duration()` to Accept URLs
- Update the function signature to accept either a `Path` or a URL string
- Add URL detection logic (strings starting with `http://` or `https://`)
- For URLs, pass the URL directly to ffprobe (it supports remote URLs)
- Add a longer timeout for URLs (60 seconds vs 30 for local files) to account for network latency
- Add appropriate error handling for network-related failures

#### Task 1.2: Modify `get_video_codec_info()` to Accept URLs
- Same approach as Task 1.1
- Update function signature to accept Path or URL string
- Add URL detection and appropriate timeout handling

#### Task 1.3: Create `validate_video_url()` Function
- New function that combines codec validation and duration detection for URLs
- Returns a tuple with validation result, duration, and any error message
- Handles common URL-specific errors (network failures, 404s, access denied)

#### Task 1.4: Add Unit Tests for URL Support
- Test `get_video_duration()` with a mocked ffprobe subprocess for URLs
- Test `get_video_codec_info()` with URLs
- Test `validate_video_url()` with various scenarios (valid, invalid codec, network error)
- Test error handling for unreachable URLs and timeouts

### Milestone 2: Backend - Add API Endpoint for Video URL Validation

**Prefix: VideoURLValidation-2**

#### Task 2.1: Create Video URL Validation Endpoint
- New endpoint: `POST /api/v1/validate/video-url`
- Request body: `{ "url": "https://example.com/video.mp4" }`
- Response: `{ "valid": true, "duration_seconds": 120, "codec_info": {...} }` or error
- Requires authentication (@api_auth_required)
- Include rate limiting considerations (ffprobe on URLs can be resource-intensive)

#### Task 2.2: Update Create/Update Slideshow Item Endpoints
- When creating/updating a video item with `content_url` (no `content_file_path`):
  - Validate the video URL format and codec
  - If validation fails, return appropriate error
  - This is a safety net - frontend should pre-validate, but backend enforces

#### Task 2.3: Add API Tests
- Test the new validation endpoint
- Test create/update slideshow item with video URLs (valid and invalid)

### Milestone 3: Frontend - Integrate URL Validation

**Prefix: VideoURLValidation-3**

#### Task 3.1: Add Video URL Validation Hook/Function
- Create a function to call the new validation endpoint
- Handle loading states and errors
- Return duration and validation result

#### Task 3.2: Update SlideshowItemForm for Video URL Validation
- When content_type is "video" and user enters a URL (onBlur or debounced):
  - Show loading indicator while validating
  - If valid: auto-populate duration, show success
  - If invalid: show error message explaining the issue
- Clear validation state when URL changes
- Disable form submission while validation is in progress

#### Task 3.3: Add Frontend Tests
- Test video URL validation flow
- Test error display for invalid video URLs
- Test duration auto-population from URL validation

### Milestone 4: Acceptance Criteria

**Prefix: VideoURLValidation-4**

#### Task 4.1: Documentation Updates
- Update relevant documentation if needed (likely minimal since this is a bug fix/enhancement)

#### Task 4.2: Full Test Suite Verification
- Run all nox sessions and ensure all tests pass
- Verify no regressions in existing video upload functionality

#### Task 4.3: Manual Testing
- Test creating a video slide via URL with a valid video
- Test creating a video slide via URL with an invalid codec
- Test editing a video slide to change from file to URL
- Verify duration auto-detection works for URLs

#### Task 4.4: Move Feature Document to Completed
- Move this file to `docs/features/completed/`

## Current Status

**Status:** Planning Complete - Awaiting Human Approval

## Progress Log

*(To be updated as milestones are completed)*
