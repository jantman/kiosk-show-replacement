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

**Status:** Open

---

### 2. Images not working

**Location:** Display view page (slideshow playback)

**Description:** I have a slideshow that consists of four uploaded images. I have verified that the uploaded images exist on the server filesystem (`instance/uploads/images/`). However, when I assign the slideshow to a display, it just continually shows "Failed to load image" and an error icon.

**Expected:** Uploaded images should display correctly on the display.

**Status:** Open

---

### 3. Slideshows Not Changing

**Location:** Display view page (slideshow playback)

**Description:** I have a display that's live and showing a slideshow. I change the slideshow assignment of that display in `/admin/displays` but the display keeps showing the same slideshow it was, even minutes later. It does not change until I refresh the display browser.

**Expected:** When a display's slideshow assignment changes, the display should automatically switch to the new slideshow via SSE.

**Status:** Open
