# UI Fixes - High Priority

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This document tracks high priority UI issues with significant functionality impact. For each of these issues, unless stated otherwise, we must FIRST write an integration test that checks for the desired behavior (should initially be failing), then implement our fix and verify that the test now passes.

## Implementation Plan

### Milestone 1: New Default Slideshow Fix

**Root Cause Analysis:**
The frontend `SlideshowForm.tsx` correctly sends the `is_default` field in the JSON payload when creating a slideshow. However, the backend API endpoint at `POST /api/v1/slideshows` (in `kiosk_show_replacement/api/v1.py`, lines 92-137) creates the slideshow with `is_default=False` hardcoded and ignores the `is_default` field from the request.

**Tasks:**

#### UI Fixes 1.1: Write integration test for default slideshow on create
- Create an integration test that:
  1. Creates a new slideshow with `is_default` checked
  2. Verifies the slideshow is saved as the default
  3. Test should initially fail

#### UI Fixes 1.2: Fix API to handle is_default on create
- Modify `POST /api/v1/slideshows` endpoint to:
  1. Read `is_default` from request JSON
  2. If `is_default=True`, clear existing defaults before creating
  3. Set the new slideshow's `is_default` appropriately
- Add unit tests for the API changes

#### UI Fixes 1.3: Verify integration test passes
- Run the integration test and confirm it passes

---

### Milestone 2: Text Title Fix

**Root Cause Analysis:**
In `kiosk_show_replacement/templates/display.html` (lines 162-169), the text slide rendering logic explicitly includes the title:
```javascript
case 'text':
    content = `
        <div class="text-content">
            ${slide.title ? `<div class="title">${slide.title}</div>` : ''}
            <div>${slide.content_text || ''}</div>
        </div>
    `;
```
The fix is to remove the title rendering for text slides, showing only `content_text`.

**Tasks:**

#### UI Fixes 2.1: Write integration/E2E test for text slide display
- Create a test that:
  1. Creates a slideshow with a text slide that has both a title and content
  2. Views the display page
  3. Verifies only the text content is shown, not the title
  4. Test should initially fail

#### UI Fixes 2.2: Fix text slide rendering in display.html
- Remove the title rendering from the text slide case in `createSlideElements()`
- Keep only the `content_text` div

#### UI Fixes 2.3: Verify test passes
- Run the test and confirm it passes

---

### Milestone 3: Acceptance Criteria

#### UI Fixes 3.1: Final testing
- Run all nox sessions and ensure they pass
- Manually verify both fixes work in the UI

#### UI Fixes 3.2: Update documentation
- Update any relevant documentation if needed

#### UI Fixes 3.3: Move to completed
- Move this file to `docs/features/completed/`

---

## Issues

---

### 1. New Default Slideshow

**Location:** Slideshow create page

**Description:** When I create a new slideshow and check the `Set as Default Slideshow` box, this is not persisted.

**Expected:** The default slideshow checkbox should be saved when creating a new slideshow.

**Status:** Open

---

### 2. Text Title

**Location:** Display view page (slideshow playback)

**Description:** Text slides are displaying the title in addition to the text; they should only display the "Text Content".

**Expected:** Text slides should only show the text content, not the title.

**Status:** Open
