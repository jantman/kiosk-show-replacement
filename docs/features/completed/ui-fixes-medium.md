# UI Fixes - Medium Priority

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks medium priority UI issues where functionality is degraded but still works. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

## Implementation Plan

### Milestone 1: Assign Slideshow Bug Fix - COMPLETED

**Root Cause Analysis:**
The SSE event broadcast uses `display.to_dict()` which returns `"name"` as the field name, but the frontend `LiveNotifications.tsx` expects `"display_name"`. This mismatch causes `data.display_name` to be `undefined`.

- Backend (`api/v1.py` line 1791): broadcasts `display.to_dict()` with field `name`
- Frontend (`LiveNotifications.tsx` line 70): expects `display_name`

**Tasks:**

#### UI Fixes Medium 1.1: Write integration test for assignment notification - DONE
- Added test `test_assignment_notification_shows_correct_display_name` in `tests/integration/test_display_management.py`
- Test verifies the notification shows the correct display name when changing slideshow assignment

#### UI Fixes Medium 1.2: Fix SSE event data structure - DONE
- Fixed `broadcast_display_update()` in `api/v1.py` to add `display_name`, `slideshow_id`, and `slideshow_name` fields to the SSE event data

#### UI Fixes Medium 1.3: Verify test passes - DONE

---

### Milestone 2: Text Formatting Fix - COMPLETED

**Root Cause Analysis:**
In `display.html` (lines 162-168), text content is rendered as plain text without preserving line breaks. The CSS `white-space` property was set to `normal` which collapses whitespace.

**Tasks:**

#### UI Fixes Medium 2.1: Write E2E test for text formatting - DONE
- Added test `test_text_slide_preserves_line_breaks` in `tests/integration/test_display_playback.py`
- Test creates a text slide with line breaks and verifies they are preserved in the display

#### UI Fixes Medium 2.2: Implement text formatting preservation - DONE
- Added `white-space: pre-wrap` CSS to `.text-content .content` in both `display.html` and `display/slideshow.html`
- This preserves line breaks and wraps text appropriately

#### UI Fixes Medium 2.3: Verify test passes - DONE

---

### Milestone 3: Video Item Duration - COMPLETED

**Root Cause Analysis:**
No automatic video duration extraction existed. Videos were uploaded via `storage.py` but only file validation occurred (extension, MIME type, size). The duration field remained manual.

**Tasks:**

#### UI Fixes Medium 3.1: Write integration test for video duration - DONE
- Added test `test_video_upload_auto_detects_duration` in `tests/integration/test_slideshow_items.py`
- Created test video asset `tests/assets/test_video_5s.mp4` (5-second duration)
- Test verifies duration is auto-detected and set for video uploads

#### UI Fixes Medium 3.2: Implement backend video duration extraction - DONE
- Added `get_video_duration()` method to `StorageManager` in `storage.py`
- Uses `ffprobe` (from ffmpeg) to extract video duration
- Updated `save_file()` to include `duration` and `duration_seconds` in video file info
- Added unit tests in `TestVideoDurationExtraction` class

#### UI Fixes Medium 3.3: Update frontend for video items - DONE
- Updated `SlideshowItemForm.tsx` to track when video duration is auto-detected
- Auto-populate duration field from upload response
- Make duration field read-only when auto-detected
- Update label to "Video Duration (auto-detected)"

#### UI Fixes Medium 3.4: Verify test passes and update dependencies - DONE
- Added `ffmpeg` to Dockerfile system dependencies
- Updated `docs/development.rst` with ffprobe as a system requirement
- Included installation instructions for various platforms

---

### Milestone 4: Acceptance Criteria - COMPLETED

#### UI Fixes Medium 4.1: Final testing - DONE
- All nox sessions pass: format, lint, test-3.14 (372 tests), test-integration (74 tests), test-e2e (15 tests), type_check

#### UI Fixes Medium 4.2: Update documentation - DONE
- Added ffprobe/ffmpeg requirement to `docs/development.rst`
- Added ffmpeg to Dockerfile

#### UI Fixes Medium 4.3: Move to completed - DONE
- This file has been moved to `docs/features/completed/`

---

## Issues

---

### 1. Video Item Duration

**Location:** Slideshow item create/edit

**Description:** Right now, when a video is uploaded to the slideshow the item retains the default item duration or overridden item duration. Video items should always be set to the actual duration of the uploaded video, whatever that is; there should not be UI fields for duration on a video upload (or they should be inactive) and the duration should be calculated and set once the video file is uploaded.

**Expected:** Video duration should be automatically determined from the video file.

**Status:** FIXED - Video duration is now automatically detected using ffprobe and set as the display_duration. The duration field is disabled/read-only for videos with auto-detected duration.

---

### 2. Text Formatting

**Location:** Display view page (slideshow playback)

**Description:** Text slides do not retain formatting such as linebreaks/newlines. We should figure out a better way of handling text content, such as displaying HTML if it has any HTML tags in it and if not then maintaining line breaks.

**Expected:** Text content should preserve line breaks and basic formatting.

**Status:** FIXED - Added `white-space: pre-wrap` CSS to preserve line breaks in text slides.

---

### 3. Assign Slideshow Bug

**Location:** Displays list page (`/admin/displays`)

**Description:** When I have one display and two (or more?) slideshows and I navigate to `/admin/displays` and then use the "Assign Slideshows" button to change the slideshow assignment for this display, I get an alert dialog in the top right of the screen saying `undefined unassigned from slideshow`.

**Expected:** Alert should show the correct display name, or not appear if not meaningful.

**Status:** FIXED - Added `display_name`, `slideshow_id`, and `slideshow_name` fields to SSE broadcast events.
