# Edit Slide Form Population Issues

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

There seem to be issues with the population of edit slide modal forms. For example:

* When editing an existing Skedda Calendar slide type, the `iCal/ICS Feed URL` form field is empty and just shows the `https://app.skedda.com/ical/...` placeholder text.
* When editing an uploaded image or video slideshow item, the "Choose File" field shows `No file chosen`, which is misleading.

## Root Cause Analysis

### Issue 1: Skedda iCal URL empty

The `SlideshowItem.to_dict()` method (`kiosk_show_replacement/models/__init__.py:754-762`) only includes `ical_url` in the serialized output when the `ical_feed` SQLAlchemy relationship is already eager-loaded into `__dict__`. This is an intentional guard against N+1 queries.

The `list_slideshow_items()` API endpoint (`kiosk_show_replacement/api/v1.py:372-409`) iterates `slideshow.items` and calls `to_dict()` without first loading the `ical_feed` relationship on skedda items. The result: `ical_url` is missing from the API response, and the frontend form field is empty.

The update endpoint (`api/v1.py:698-699`) already handles this correctly by triggering `_ = item.ical_feed` after commit, so the response from PUT includes `ical_url`. The list endpoint simply needs the same treatment.

### Issue 2: File upload "No file chosen"

Browser security prevents JavaScript from programmatically setting values on `<input type="file">` elements. When editing an existing file-upload item, the form state correctly has `content_file_path` set and a green badge appears below the input, but the file input itself always shows "No file chosen" which is misleading. The label also shows "Upload image *" (with required asterisk) even though no new upload is needed when editing.

## Implementation Plan

### Milestone 1: Regression Tests (Tasks 1.1-1.2)

Per feature process rules, bug fixes begin with regression tests that initially fail.

**Task 1.1**: Add unit test `test_list_skedda_items_includes_ical_url` in `tests/unit/test_api.py`
- Create a skedda slideshow item with an associated `ICalFeed`
- Call `GET /api/v1/slideshows/{id}/items`
- Assert `ical_url` is present in the response and matches the feed URL
- Should **fail** initially (proving the bug exists)

**Task 1.2**: Add integration test for file upload edit UX in `tests/integration/test_slideshow_items.py`
- When editing an existing file-upload image item, assert that the current filename is displayed prominently (not just the misleading bare file input)
- Should **fail** initially

### Milestone 2: Backend Fix - Eager Load ical_feed (Task 2.1)

**Task 2.1**: Fix `list_slideshow_items()` in `kiosk_show_replacement/api/v1.py` (lines 372-409)
- After fetching `slideshow.items`, iterate skedda items and access `item.ical_feed` to trigger lazy load (same pattern as the update endpoint at line 699)
- This ensures `to_dict()` finds the relationship in `__dict__` and includes `ical_url`

### Milestone 3: Frontend Fix - File Upload Edit UX (Task 3.1)

**Task 3.1**: Update `SlideshowItemForm.tsx` file upload section (lines 586-628)
- When editing an item that already has `content_file_path`, show the current filename prominently above the file input
- Change the file upload label from "Upload image *" to "Replace file (optional)" when a file already exists
- Remove the required asterisk since no new upload is needed when editing

### Milestone 4: Acceptance Criteria (Tasks 4.1-4.3)

**Task 4.1**: Ensure all unit tests pass (`nox -s test-3.14`)
**Task 4.2**: Ensure all integration tests pass (`nox -s test-integration`)
**Task 4.3**: Move feature doc to `docs/features/completed/`
