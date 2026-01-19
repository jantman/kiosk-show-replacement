# UI Fixes

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks UI issues discovered during testing of the admin interface. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

## Issues

### 1. Slideshow Item Action Icons Not Displaying

**Location:** Slideshow edit page (e.g., `/admin/slideshows/1`)

**Description:** The icons for slideshow item actions (Move Up, Move Down, Edit, Delete) are not displaying. The buttons appear as empty outlined objects instead of showing their respective icons.

**Expected:** Buttons should display appropriate icons (arrows for move, pencil for edit, trash for delete).

**Status:** Open

### 2. Confusing Dual Admin Interfaces

(No integration tests required)

**Location:** `/admin/` on both port 5000 (Flask) and port 3000 (Vite)

**Description:** There appear to be two completely separate admin interfaces:
- Port 5000 (Flask): Admin UI exists but doesn't function properly
- Port 3000 (Vite): Admin UI works correctly

This is confusing for users. It seems like:
- Flask server (port 5000) should only serve the API and display pages
- Admin UI should only be served via Vite dev server (port 3000) during development

**Expected:** Clear separation of concerns with documentation:
- Flask (5000): API endpoints and display serving only
- Vite (3000): Admin UI during development
- Production: Single entry point with built React assets served by Flask

**Action Items:**
- Clarify/fix the architecture so there's only one admin UI
- Update documentation to clearly explain where the admin UI is and how to access it
- Consider removing or redirecting the non-functional Flask admin routes

**Status:** Open

### 3. Display Info Overlay Should Be Optional

**Location:** Display view page (slideshow playback)

**Description:** When a slideshow is displayed, a small box appears in the lower left showing:
- Slide number/count
- Slideshow name
- Display name

This overlay is always visible, but it should be optional and configurable per display.

**Expected:**
- Add a per-display configuration option to show/hide the info overlay
- Default should be hidden (not shown)

**Status:** Open

### 4. Confusing Slideshow Action Link Names

**Location:** Slideshows list page (`/admin/slideshows`)

**Description:** Each slideshow has "Edit" and "View Details" links, but the naming is not intuitive:
- "Edit" - edits slideshow metadata
- "View Details" - this is where you actually edit the slides in the slideshow

Users would not intuitively know that "View Details" is where to go to manage slides.

**Expected:** Rename the links to be more descriptive, e.g.:
- "Edit" → "Edit Slideshow" or "Settings"
- "View Details" → "Manage Slides" or "Edit Slides"

**Status:** Open

### 5. Video Item Duration

Right now, when a video is uploaded to the slideshow the item retains the default item duration or overridden item duration. Video items should always be set to the actual duration of the uploaded video, whatever that is; there should not be UI fields for duration on a video upload (or they should be inactive) and the duration should be calculated and set once the video file is uploaded.

### 6. New Default Slideshow

When I create a new slideshow and check the `Set as Default Slideshow` box, this is not persisted.

### 7. Text Title

Text slides are displaying the title in addition to the text; they should only display the "Text Content".

### 8. Text Formatting

Text slides do not retain formatting such as linebreaks/newlines. We should figure out a better way of handling text content, such as displaying HTML if it has any HTML tags in it and if not then maintaining line breaks.

### 9. Slides Not Changing

I create a slideshow with three text slides, the first and third of which have the default (10 second) duration and the second has a overridden 3-second duration. The slideshow just loops over the second slide infinitely; the first and third are never shown.

### 10. Automatic Titles

For Image, Video, and Web Page slide types, the Title should default to the filename (upload) or URL (URL) if not previously specified as otherwise. This is mostly a frontend issue.

### 11. Assign Slideshow Bug

When I have one display and two (or more?) slideshows and I navigate to `/admin/displays` and then use the "Assign Slideshows" button to change the slideshow assignment for this display, I get an alert dialog in the top right of the screen saying `undefined unassigned from slideshow`.

### 12. Slideshows Not Changing

I have a display that's live and showing a slideshow. I change the slideshow assignment of that display in `/admin/displays` but the display keeps showing the same slideshow it was, even minutes later. It does not change until I refresh the display browser.

### 13. Images not working

I have a slideshow that consists of four uploaded images. I have verified that the uploaded images exist on the server filesystem (`instance/uploads/images/`). However, when I assign the slideshow to a display, it just continually shows "Failed to load image" and an error icon.
