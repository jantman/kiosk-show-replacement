# Slideshow Transitions Not Working

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Slideshow transitions do not appear to work. When slides change, they jump directly from one slide to the next with no visible transition effect. There is no observable difference between selecting "Fade" or "Slide" as the transition type - both result in an immediate jump between slides.

This bug needs investigation to determine whether the issue is in the frontend display rendering, the transition CSS/animation implementation, or the configuration not being properly passed to the display.

## Investigation Findings

### Data Flow Analysis

The transition configuration flows through the system as follows:

1. **Backend Model** (`kiosk_show_replacement/models/__init__.py:494`): The `Slideshow` model stores `transition_type` field with default "fade". Valid values are: `["none", "fade", "slide", "zoom"]`.

2. **API Response**: The `to_dict()` method correctly includes `transition_type` in JSON responses.

3. **Admin Interface** (`frontend/src/pages/SlideshowForm.tsx`): The React admin UI correctly displays a dropdown for selecting transition type and submits it to the API.

4. **Display Template** (`kiosk_show_replacement/templates/display/slideshow.html`): The template receives the `slideshow` object via Jinja2, which includes the `transition_type` field.

### Root Cause

The bug had **three root causes**:

1. **API not setting transition_type on create** (`kiosk_show_replacement/api/v1.py`): The `create_slideshow` function didn't pass `transition_type` to the Slideshow constructor, causing all new slideshows to use the default 'fade' regardless of what was specified.

2. **JavaScript hardcoding fade-transition** (line 350 in slideshow.html): The `createSlideElements()` method hardcoded the CSS class to `'slide fade-transition'` instead of reading from `slideshow.transition_type`.

3. **Missing CSS implementations**: Only the `fade-transition` CSS was defined. The other transition types (`slide`, `zoom`, `none`) had no corresponding CSS.

## Implementation Summary

### Milestone 1: Regression Tests (Prefix: `Transitions-1`)

- Added integration tests in `tests/integration/test_display_playback.py` that verify each transition type applies the correct CSS class:
  - `test_slideshow_transition_type_fade_applies_correct_css_class`
  - `test_slideshow_transition_type_slide_applies_correct_css_class`
  - `test_slideshow_transition_type_zoom_applies_correct_css_class`
  - `test_slideshow_transition_type_none_applies_correct_css_class`

### Milestone 2: Implement Transition CSS (Prefix: `Transitions-2`)

- Added CSS for all transition types in `kiosk_show_replacement/templates/display/slideshow.html`:
  - `fade-transition`: Smooth opacity change (existing, unchanged)
  - `slide-transition`: Horizontal slide from right with opacity
  - `zoom-transition`: Scale from 0.8 to 1.0 with opacity
  - `none-transition`: Immediate display change with no animation

### Milestone 3: Implement JavaScript Transition Logic (Prefix: `Transitions-3`)

1. **Task 3.1**: Added `transitionType` property in SlideshowPlayer constructor that reads from Jinja2 context
2. **Task 3.2**: Updated `createSlideElements()` to apply dynamic transition class
3. **Task 3.2 (additional fix)**: Fixed `create_slideshow` API to pass `transition_type` to Slideshow constructor

### Milestone 4: Acceptance Criteria (Prefix: `Transitions-4`)

- All nox sessions pass:
  - `nox -s format` - Code formatted
  - `nox -s lint` - No lint errors
  - `nox -s test-3.14` - 488 unit tests pass
  - `nox -s type_check` - No type errors
  - `nox -s test-integration` - 111 integration tests pass (+ 2 xpassed)

## Progress

- [x] Investigation complete
- [x] Implementation plan created
- [x] Milestone 1: Regression Tests
- [x] Milestone 2: Implement Transition CSS
- [x] Milestone 3: Implement JavaScript Transition Logic
- [x] Milestone 4: Acceptance Criteria

## Related Commits

1. `Transitions-1.1`: Add regression tests for transition CSS classes
2. `Transitions-2.1`: Add CSS for all transition types
3. `Transitions-3.1`: Update JavaScript to read and apply transition type
4. `Transitions-3.2`: Fix API to set transition_type when creating slideshows
