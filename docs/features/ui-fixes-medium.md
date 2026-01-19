# UI Fixes - Medium Priority

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks medium priority UI issues where functionality is degraded but still works. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

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
