# Bug: Video Slides Display Black Screen Instead of Playing

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Video slides uploaded to a slideshow do not play on the display.

**Steps to reproduce:**
1. Create or edit a slideshow
2. Add a video slide by uploading a video file (tested with `tests/assets/crash_into_pole.mpeg`)
3. View the slideshow on a display

**Observed behavior:**
- The video upload succeeds
- The video duration is correctly detected (e.g., 9 seconds for the test file)
- When the slide is displayed, only a black screen is shown
- The video does not play

**Expected behavior:**
- The video should play on the display when its slide is shown

---

## Root Cause Analysis

Investigation of the codebase revealed the following issues:

### 1. Incorrect `<source>` Element Configuration

In `kiosk_show_replacement/templates/display/slideshow.html` (lines 345-354), the video element is created with three `<source>` elements, all pointing to the **same URL** but with different `type` attributes:

```javascript
content = `<video autoplay muted loop preload="metadata" ...>
    <source src="${contentUrl}" type="video/mp4">
    <source src="${contentUrl}" type="video/webm">
    <source src="${contentUrl}" type="video/ogg">
    Your browser does not support video playback.
</video>`;
```

This is semantically incorrect. The browser interprets multiple `<source>` elements as fallback options for different formats of the same content (e.g., providing mp4 and webm versions at different URLs). Declaring the same URL three times with different type hints confuses the browser and can cause loading failures.

### 2. CSS Opacity Transition Dependency

The video element has CSS that starts it at `opacity: 0` (line 75):

```css
.slide video {
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
}

.slide video.loaded {
    opacity: 1;
}
```

The visibility depends on the `onloadeddata` event firing to add the `loaded` class. If the video fails to load due to the incorrect source configuration, this event never fires and the video remains invisible while the black background shows through.

### 3. Note on Test File Format

The bug report mentions `crash_into_pole.mpeg` which is an MPEG-1 format that browsers don't support in HTML5 video. However, there is a valid test file `test_video_5s.mp4` available. The fix should work with properly supported formats (MP4/WebM).

---

## Implementation Plan

### Milestone 1 (M1): Create Failing Regression Test

**Prefix:** `M1`

**Tasks:**

1. **M1.1** - Create an integration test in `tests/integration/test_display_playback.py` that:
   - Creates a slideshow
   - Uploads a video file (`test_video_5s.mp4`) via the API
   - Creates a video slideshow item
   - Assigns the slideshow to a display
   - Navigates to the display view
   - Verifies the video element becomes visible (has `loaded` class or `opacity: 1`)
   - Verifies no error message is shown

2. **M1.2** - Run the test and confirm it fails (demonstrating the bug exists)

3. **M1.3** - Commit the failing test

### Milestone 2 (M2): Fix Video Playback

**Prefix:** `M2`

**Tasks:**

1. **M2.1** - Update `slideshow.html` to use a single `<source>` element without hardcoded type attributes. The browser will auto-detect the format from the file content. Replace:
   ```javascript
   <source src="${contentUrl}" type="video/mp4">
   <source src="${contentUrl}" type="video/webm">
   <source src="${contentUrl}" type="video/ogg">
   ```
   With:
   ```javascript
   <source src="${contentUrl}">
   ```

2. **M2.2** - Add defensive logic to ensure videos become visible even if `onloadeddata` doesn't fire perfectly. Consider adding a timeout fallback that sets `opacity: 1` after a short delay if the video element exists.

3. **M2.3** - Run the regression test and verify it passes

4. **M2.4** - Commit the fix

### Milestone 3 (M3): Acceptance Criteria

**Prefix:** `M3`

**Tasks:**

1. **M3.1** - Run all nox test sessions and ensure all tests pass
2. **M3.2** - Review and update documentation if needed (none expected for this bug fix)
3. **M3.3** - Move the feature file to `docs/features/completed/`
4. **M3.4** - Final commit

---

## Progress

- [x] **M1: Create Failing Regression Test** - Completed
  - Added integration test `test_uploaded_video_displays_on_display_view` in `tests/integration/test_display_playback.py`
  - Test uploads a video, creates a slideshow item, and verifies video displays correctly
  - Test initially failed with `net::ERR_ABORTED` confirming the bug
- [x] **M2: Fix Video Playback** - Completed
  - Fixed `<source>` element to use a single element without type attribute
  - Changed preload from "metadata" to "auto" for better loading
  - Added defensive visibility fallback with `ensureVisible()` helper and 1-second timeout
  - Regression test now passes
- [x] **M3: Acceptance Criteria** - Completed
  - All nox test sessions pass (format, lint, type_check, test-3.14, test-integration, test-e2e)
  - No documentation updates needed (internal bug fix)
  - Feature file moved to completed
