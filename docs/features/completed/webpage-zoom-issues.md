# Web Page Slide Zoom Issues

## Status: Completed

**Completion Date:** 2026-01-26

## Overview

Two issues were identified with the web page slide scaling/zoom feature:

1. **Display not updating on zoom changes**: When the scale/zoom setting for a web page slide type is modified in the admin interface, displays were expected to not receive update notifications.

2. **Missing admin preview**: The completed feature implementation plan (`docs/features/completed/feature-webpage-slide-scaling.md`) specified an admin preview of the web page zoom, but this preview was not present in the admin interface.

## Resolution

### Issue 1: SSE Notification Verification

After investigation and testing, the SSE broadcast for scale_factor changes was found to be working correctly. The existing implementation in `kiosk_show_replacement/api/v1.py` properly calls `broadcast_slideshow_update()` after updating any slide item properties, including `scale_factor`.

**Tests Added:**
- `tests/unit/test_sse_broadcast.py::TestSlideItemCRUDBroadcastToDisplays::test_update_scale_factor_broadcasts_slideshow_updated_to_display` - Unit test verifying SSE event is sent when scale_factor changes
- `tests/integration/test_display_playback.py::TestDisplayPlayback::test_display_reloads_on_zoom_change` - Integration test verifying displays reload and apply new scale_factor via SSE

### Issue 2: Admin Preview Feature

Added a visual preview iframe below the zoom slider in the admin interface that shows how the zoomed webpage will appear on the display.

**Implementation:**
- File: `frontend/src/components/SlideshowItemForm.tsx`
- Preview container with 16:9 aspect ratio
- Uses CSS transform scaling matching the display template (scale(X) where X = scale_factor/100)
- Shows loading state while iframe loads
- Shows "Preview unavailable" message if iframe fails to load (e.g., X-Frame-Options blocking)
- Preview only appears for URL content type with a valid URL entered

**Tests Added:**
- `tests/integration/test_slideshow_items.py::TestSlideshowItems::test_url_item_preview_appears_when_url_entered` - Verifies preview appears when URL is entered
- `tests/integration/test_slideshow_items.py::TestSlideshowItems::test_url_item_preview_updates_on_zoom_change` - Verifies preview transform updates when zoom slider changes
- `tests/integration/test_slideshow_items.py::TestSlideshowItems::test_url_item_preview_not_visible_for_other_types` - Verifies preview is only shown for URL content type

## Files Changed

- `frontend/src/components/SlideshowItemForm.tsx` - Added preview iframe with CSS transform scaling
- `tests/unit/test_sse_broadcast.py` - Added unit test for scale_factor SSE broadcast
- `tests/integration/test_display_playback.py` - Added integration test for display reload on zoom change
- `tests/integration/test_slideshow_items.py` - Added integration tests for preview feature

## Testing

All tests pass:
- `poetry run -- nox -s test-3.14` - 492 unit tests passed
- `poetry run -- nox -s test-integration` - 119 tests passed (117 passed + 2 xpassed)
- `poetry run -- nox -s lint` - Passed
- `poetry run -- nox -s type_check` - Passed
- `cd frontend && npm run type-check` - Passed
- `cd frontend && npm run lint` - Passed
