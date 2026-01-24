# Bug: Admin Changes Not Applied to Displays in Real-Time

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Changes made in the Admin UI are not propagated to connected displays in real-time.

### Display Settings Changes

**Steps to reproduce:**
1. Have a display connected and live (e.g., at `/display/{name}`)
2. In the Admin UI, edit the display settings
3. Enable "Show Info Overlay" (or toggle another setting)
4. Save the changes

**Observed behavior:**
- The setting change is saved in the Admin UI
- The display does not reflect the change until the page is manually refreshed

**Expected behavior:**
- Display setting changes should be pushed to the display via SSE and applied immediately without requiring a manual page refresh

### Slideshow Changes

**Steps to reproduce:**
1. Have a display connected and live, showing a slideshow
2. In the Admin UI, modify the slideshow (e.g., add/remove/reorder slides, change content)
3. Save the changes

**Observed behavior:**
- The slideshow changes are saved in the Admin UI
- The display continues showing the old slideshow content until the page is manually refreshed

**Expected behavior:**
- Slideshow changes should be pushed to the display via SSE and applied immediately without requiring a manual page refresh
