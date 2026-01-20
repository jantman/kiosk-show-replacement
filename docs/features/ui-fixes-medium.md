# UI Fixes - Medium Priority

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks medium priority UI issues where functionality is degraded but still works. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

## Implementation Plan

### Milestone 1: Assign Slideshow Bug Fix

**Root Cause Analysis:**
The SSE event broadcast uses `display.to_dict()` which returns `"name"` as the field name, but the frontend `LiveNotifications.tsx` expects `"display_name"`. This mismatch causes `data.display_name` to be `undefined`.

- Backend (`api/v1.py` line 1791): broadcasts `display.to_dict()` with field `name`
- Frontend (`LiveNotifications.tsx` line 70): expects `display_name`

**Tasks:**

#### UI Fixes Medium 1.1: Write integration test for assignment notification
- Test that changing slideshow assignment shows the correct display name in the notification

#### UI Fixes Medium 1.2: Fix SSE event data structure
- Option A: Add `display_name` field to the SSE event data in `broadcast_display_update()`
- Option B: Update frontend to use `name` instead of `display_name`
- Recommendation: Option A - add `display_name` to event data for consistency with frontend types

#### UI Fixes Medium 1.3: Verify test passes

---

### Milestone 2: Text Formatting Fix

**Root Cause Analysis:**
In `display.html` (lines 162-168), text content is rendered as plain text without preserving line breaks. The content is inserted directly into HTML which collapses whitespace.

**Tasks:**

#### UI Fixes Medium 2.1: Write E2E test for text formatting
- Create a text slide with line breaks
- Verify the display page preserves the line breaks

#### UI Fixes Medium 2.2: Implement text formatting preservation
- Approach: Convert newlines to `<br>` tags for plain text, or render as-is if HTML tags are detected
- Sanitize HTML to prevent XSS attacks
- Update the text slide rendering in `display.html`

#### UI Fixes Medium 2.3: Verify test passes

---

### Milestone 3: Video Item Duration

**Root Cause Analysis:**
No automatic video duration extraction exists. Videos are uploaded via `storage.py` but only file validation occurs (extension, MIME type, size). The duration field remains manual.

**Tasks:**

#### UI Fixes Medium 3.1: Write integration test for video duration
- Upload a video file
- Verify the duration is automatically set based on the video's actual duration

#### UI Fixes Medium 3.2: Implement backend video duration extraction
- Add video duration extraction using `ffprobe` (part of ffmpeg) or a Python library like `moviepy` or `python-ffmpeg`
- Update the video upload endpoint to return duration
- Set `display_duration` automatically for video items

#### UI Fixes Medium 3.3: Update frontend for video items
- Disable/hide the duration override field for video uploads
- Show the detected duration as read-only information

#### UI Fixes Medium 3.4: Verify test passes and update dependencies
- Add any new dependencies to pyproject.toml
- Update documentation if ffmpeg is required

---

### Milestone 4: Acceptance Criteria

#### UI Fixes Medium 4.1: Final testing
- Run all nox sessions and ensure they pass
- Manually verify all three fixes work in the UI

#### UI Fixes Medium 4.2: Update documentation
- Document any new dependencies (e.g., ffmpeg requirement)
- Update CLAUDE.md if needed

#### UI Fixes Medium 4.3: Move to completed
- Move this file to `docs/features/completed/`

---

## Issues

---

### 1. Video Item Duration

**Location:** Slideshow item create/edit

**Description:** Right now, when a video is uploaded to the slideshow the item retains the default item duration or overridden item duration. Video items should always be set to the actual duration of the uploaded video, whatever that is; there should not be UI fields for duration on a video upload (or they should be inactive) and the duration should be calculated and set once the video file is uploaded.

**Expected:** Video duration should be automatically determined from the video file.

**Status:** Open

---

### 2. Text Formatting

**Location:** Display view page (slideshow playback)

**Description:** Text slides do not retain formatting such as linebreaks/newlines. We should figure out a better way of handling text content, such as displaying HTML if it has any HTML tags in it and if not then maintaining line breaks.

**Expected:** Text content should preserve line breaks and basic formatting.

**Status:** Open

---

### 3. Assign Slideshow Bug

**Location:** Displays list page (`/admin/displays`)

**Description:** When I have one display and two (or more?) slideshows and I navigate to `/admin/displays` and then use the "Assign Slideshows" button to change the slideshow assignment for this display, I get an alert dialog in the top right of the screen saying `undefined unassigned from slideshow`.

**Expected:** Alert should show the correct display name, or not appear if not meaningful.

**Status:** Open
