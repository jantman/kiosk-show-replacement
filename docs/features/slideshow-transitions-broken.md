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

The bug has two root causes in the display template JavaScript:

1. **Transition type is never read** (line 350): The `createSlideElements()` method hardcodes the CSS class to `'slide fade-transition'` instead of reading from `slideshow.transition_type`:
   ```javascript
   slideElement.className = 'slide fade-transition';  // Hardcoded!
   ```

2. **Missing CSS implementations** (lines 210-217): Only the `fade-transition` CSS is defined. The other transition types (`slide`, `zoom`, `none`) have no corresponding CSS.

### Current CSS (lines 210-217)
```css
.fade-transition {
    opacity: 0;
    transition: opacity 0.5s ease-in-out;
}

.fade-transition.active {
    opacity: 1;
}
```

## Implementation Plan

### Milestone 1: Regression Tests (Prefix: `Transitions-1`)

Create integration tests that verify transition behavior. These tests should initially fail.

#### Task 1.1: Add transition-specific display playback tests
- Add tests in `tests/integration/test_display_playback.py` that verify:
  - Fade transition applies the correct CSS class and animation
  - Slide transition applies the correct CSS class and animation
  - Zoom transition applies the correct CSS class and animation
  - None transition shows no animation (immediate switch)
- Tests should verify the transition type CSS class is applied to slide elements

### Milestone 2: Implement Transition CSS (Prefix: `Transitions-2`)

#### Task 2.1: Add CSS for all transition types
In `kiosk_show_replacement/templates/display/slideshow.html`, add CSS for:
- `slide-transition`: Horizontal slide animation (slide in from right, slide out to left)
- `zoom-transition`: Scale/zoom animation
- `none-transition`: Immediate display change (no animation)

#### Task 2.2: Update existing fade CSS if needed
Verify the existing fade transition CSS works correctly and adjust timing if needed.

### Milestone 3: Implement JavaScript Transition Logic (Prefix: `Transitions-3`)

#### Task 3.1: Store transition type in SlideshowPlayer
In the constructor, store the transition type from the Jinja2 context:
```javascript
this.transitionType = '{{ slideshow.transition_type }}' || 'fade';
```

#### Task 3.2: Apply dynamic transition class in createSlideElements
Update line 350 to use the stored transition type:
```javascript
slideElement.className = `slide ${this.transitionType}-transition`;
```

#### Task 3.3: Update showSlide method for different transitions
Ensure the `showSlide()` method properly handles all transition types, particularly the `slide` and `zoom` transitions which may require different CSS class manipulation.

### Milestone 4: Acceptance Criteria (Prefix: `Transitions-4`)

#### Task 4.1: Verify all transitions work visually
- Manual verification that each transition type produces the expected visual effect
- Fade: Smooth opacity change between slides
- Slide: Horizontal sliding motion
- Zoom: Scale animation
- None: Immediate switch with no animation

#### Task 4.2: Run all tests
- All nox sessions must pass
- All new and existing tests must pass

#### Task 4.3: Update documentation if needed
- Review if any documentation updates are required for the transition feature

#### Task 4.4: Move feature file to completed
- Move this file to `docs/features/completed/`

## Progress

- [x] Investigation complete
- [x] Implementation plan created
- [ ] Milestone 1: Regression Tests
- [ ] Milestone 2: Implement Transition CSS
- [ ] Milestone 3: Implement JavaScript Transition Logic
- [ ] Milestone 4: Acceptance Criteria
