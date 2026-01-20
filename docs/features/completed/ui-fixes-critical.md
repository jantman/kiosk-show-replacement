# UI Fixes - Critical

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks critical UI issues that break core system functionality. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

## Issues

---

### 1. Slides Not Changing

**Location:** Display view page (slideshow playback)

**Description:** I create a slideshow with three text slides, the first and third of which have the default (10 second) duration and the second has a overridden 3-second duration. The slideshow just loops over the second slide infinitely; the first and third are never shown.

**Expected:** All slides should display in order, each for their configured duration.

**Status:** ✅ Fixed

**Root Cause Analysis:**
The JavaScript in `kiosk_show_replacement/templates/display/slideshow.html` lines 463 and 467 uses `this.slides[...].display_duration * 1000` directly. The `display_duration` field is the *optional* per-item override duration, which is `null` when no override is set. When JavaScript evaluates `null * 1000`, it returns `0` (zero milliseconds), causing slides without a duration override to be immediately skipped.

The model provides an `effective_duration` field (computed property) that correctly falls back to the slideshow's `default_item_duration` when `display_duration` is null. The JavaScript should use `effective_duration` instead of `display_duration`.

**Files to Modify:**
- `kiosk_show_replacement/templates/display/slideshow.html` (lines 463, 467)

---

### 2. Images not working

**Location:** Display view page (slideshow playback)

**Description:** I have a slideshow that consists of four uploaded images. I have verified that the uploaded images exist on the server filesystem (`instance/uploads/images/`). However, when I assign the slideshow to a display, it just continually shows "Failed to load image" and an error icon.

**Expected:** Uploaded images should display correctly on the display.

**Status:** ✅ Fixed

**Root Cause Analysis:**
This requires further investigation through integration testing. The suspected issue areas are:
1. The `display_url` property on `SlideshowItem` not generating correct URLs for uploaded files
2. The Flask `/uploads/<path:filename>` route not resolving paths correctly
3. Path storage mismatch between where files are saved and what's stored in `content_file_path`
4. Potential URL encoding issues between what `display_url` returns and what the browser requests

The investigation will begin by writing a failing integration test that uploads an image, assigns the slideshow to a display, navigates to the display view, and verifies the image loads successfully. This test will help identify the exact failure point.

**Files to Investigate:**
- `kiosk_show_replacement/models/__init__.py` (`display_url` property)
- `kiosk_show_replacement/app.py` (upload file serving route)
- `kiosk_show_replacement/storage.py` (file path handling)

**Fix Applied:**
The issue was in `kiosk_show_replacement/app.py`. The `send_from_directory()` call was using a relative path from `app.config["UPLOAD_FOLDER"]`, which Flask's path resolution struggled with depending on the working directory state. Fixed by converting the upload folder to an absolute path with `os.path.abspath()` before passing to `send_from_directory()`.

---

### 3. Slideshows Not Changing

**Location:** Display view page (slideshow playback)

**Description:** I have a display that's live and showing a slideshow. I change the slideshow assignment of that display in `/admin/displays` but the display keeps showing the same slideshow it was, even minutes later. It does not change until I refresh the display browser.

**Expected:** When a display's slideshow assignment changes, the display should automatically switch to the new slideshow via SSE.

**Status:** ✅ Fixed

**Root Cause Analysis:**
The `broadcast_display_update()` function in `kiosk_show_replacement/api/v1.py` (line 1796) only broadcasts display update events to `connection_type="admin"`, not to display connections. This means when a slideshow assignment changes:

1. The admin UI receives the SSE event (for real-time dashboard updates)
2. The display connection does NOT receive the event
3. The display continues showing the old slideshow until manually refreshed

In contrast, `broadcast_slideshow_update()` correctly sends events to both admin and display connections when a slideshow is updated or deleted. The fix should update `broadcast_display_update()` to also notify the affected display when the event type is `assignment_changed`.

**Files to Modify:**
- `kiosk_show_replacement/api/v1.py` (`broadcast_display_update()` function)

---

## Implementation Plan

### Milestone 1: Issue 1 - Slides Not Changing (1.x)

**Task 1.1:** Write integration test for slide duration handling
- Create test in `tests/integration/test_display_playback.py` (new file)
- Test creates a slideshow with 3 text slides: slide 1 (default duration), slide 2 (3s override), slide 3 (default duration)
- Test navigates to display view and verifies all slides are displayed
- Test should initially FAIL due to the bug

**Task 1.2:** Fix the JavaScript duration bug
- In `kiosk_show_replacement/templates/display/slideshow.html`:
  - Line 463: Change `this.slides[this.currentSlideIndex].display_duration` to `this.slides[this.currentSlideIndex].effective_duration`
  - Line 467: Change `this.slides[0].display_duration` to `this.slides[0].effective_duration`
- Run the integration test to verify it now passes

**Task 1.3:** Run full test suite and update documentation

---

### Milestone 2: Issue 2 - Images Not Working (2.x)

**Task 2.1:** Write integration test for image display on display view
- Add test to `tests/integration/test_display_playback.py`
- Test uploads an image via API
- Test creates slideshow item referencing the uploaded image
- Test navigates to display view
- Test verifies image loads successfully (no onerror triggered)
- Test should initially FAIL due to the bug

**Task 2.2:** Debug and identify root cause
- Use test failure to identify exact failure point
- Check browser network requests for 404s or other errors
- Verify file paths match between storage, database, and URL generation

**Task 2.3:** Implement fix based on findings
- Fix will be determined by debugging results

**Task 2.4:** Run tests and verify fix

---

### Milestone 3: Issue 3 - Slideshows Not Changing via SSE (3.x)

**Task 3.1:** Write integration test for SSE slideshow assignment change
- Add test to `tests/integration/test_sse_integration.py` (or new file)
- Test creates display and assigns a slideshow
- Test opens display view in browser
- Test changes slideshow assignment via API
- Test verifies display page reloads/updates without manual refresh
- Test should initially FAIL due to the bug

**Task 3.2:** Fix `broadcast_display_update()` to notify displays
- In `kiosk_show_replacement/api/v1.py`, update `broadcast_display_update()`:
  - When `event_type == "assignment_changed"`, also send event to the specific display connection
  - Use similar pattern to `broadcast_slideshow_update()` for targeting display connections
- Run the integration test to verify it now passes

**Task 3.3:** Run full test suite and update documentation

---

### Milestone 4: Acceptance Criteria (4.x)

**Task 4.1:** Verify all nox sessions pass
- `nox -s format`
- `nox -s lint`
- `nox -s test-3.14`
- `nox -s type_check`
- `nox -s test-integration`
- `nox -s test-e2e`

**Task 4.2:** Update documentation if needed

**Task 4.3:** Move feature file to `docs/features/completed/`
