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
