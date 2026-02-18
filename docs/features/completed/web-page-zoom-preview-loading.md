# Web Page Zoom Preview Loading

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

I'm creating a Web Page slideshow item. I enter a Title of `TopGolf` and a URL of `http://decaturmakers.org/topgolf`, and the Preview appears as expected. However, if I drag the Zoom slider, the Preview window just shows a spinner icon with the text `Loading preview...`. I never see this change, never see the updated/zoomed preview, and also don't see any error messages in my browser console. This Preview should work as expected at various zooms.

As a larger issue though, the web page zoom preview seems very misleading since it doesn't take (possibly very varying) display sizes into account.

We need to figure out a better, more user-friendly way of handling this.

Some options that I can think of include fixing the current preview and also having it take specific display sizes into account (either average, or selecting a specific display to preview), or getting rid of the zoom functionality and adding some fixed options such as "fit width", "50% reduction", "fit height", etc.

## Implementation Plan

### Milestone 1: Regression Tests (Completed)
- Added failing frontend unit test and integration test proving the zoom slider causes a permanent spinner.

### Milestone 2: Bug Fix (Completed)
- Removed `setPreviewLoading(true)` and `setPreviewError(false)` from the zoom slider `onChange` handler. The zoom only changes CSS transforms, not the iframe src, so there is nothing to "load".

### Milestone 3: Display Selector and Dynamic Preview (Completed)
- Added `is_archived` to the `Display` TypeScript interface.
- Added state for `displays` and `selectedDisplayId`.
- Added `useEffect` to fetch non-archived displays with resolution data when content type is `url`.
- Added `getEffectiveDimensions` helper to swap width/height for 90/270 degree rotated displays.
- Added `Form.Select` dropdown for selecting a preview display, with dynamic aspect ratio on the preview container.

### Milestone 4: Tests for Display Selector (Completed)
- 6 frontend unit tests covering selector visibility, default aspect ratio, display selection, rotation, and revert.
- 2 integration tests covering display selector with a standard display and a rotated display.

### Milestone 5: Acceptance Criteria (Completed)
- All nox sessions passing (test-3.14, lint, format, type_check).
- All frontend checks passing (type-check, lint, test:run).
- Feature doc moved to `docs/features/completed/`.

## Status: COMPLETED
