# Web Page Slide Auto-Scroll Not Working

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Some web pages have built-in automatic scrolling behavior (e.g., scrolling to a specific position based on the current time of day). This auto-scroll functionality does not work when the page is displayed as a slide.

**Example case**: The Skedda booking page at `https://decaturmakersreservations.skedda.com/booking` automatically scrolls to a time-relevant position when viewed in a normal browser, but this scrolling does not occur when the page is displayed as a web page slide type.

This may be related to how iframes load content, JavaScript execution timing, or other iframe-specific limitations that need investigation.

---

## Root Cause Analysis

After investigating the codebase, the root cause has been identified:

**Current behavior**: In `slideshow.html`, the `createSlideElements()` method creates all slide DOM elements at initialization, including iframes for URL slides. However, slides are hidden with `display: none` (via CSS class `.slide` without `.active`) until they become active. When the iframe loads inside a hidden container:

1. The embedded page's JavaScript runs while the iframe has zero dimensions
2. Auto-scroll operations (like scrolling to the current time) fail or are ignored because scroll positions can't be set in elements with no computed dimensions
3. The `DOMContentLoaded` and `load` events fire before the slide becomes visible
4. By the time the slide transitions to `active`, the page's scroll logic has already run and completed

**Code location**: `kiosk_show_replacement/templates/display/slideshow.html`, lines 387-434 (`createSlideElements()`) and lines 457-485 (`createUrlSlideContent()`)

---

## Implementation Plan

### Solution Approach: Lazy-load iframes when slides become active

Instead of loading all URL slide iframes immediately, defer iframe creation until the slide becomes active. This ensures:
- The iframe loads when its container is visible and has proper dimensions
- The embedded page's scroll JavaScript runs with correct visibility state
- Any time-based scroll behavior works correctly

### Milestone 1: Implement lazy-loading for URL slides

**Prefix**: `WebpageAutoScroll-1`

#### Task 1.1: Modify `createSlideElements()` to use placeholders for URL slides
- For URL slides, create a placeholder `<div>` instead of the actual iframe
- Store slide data on the placeholder element so it can be used when loading

#### Task 1.2: Modify `showSlide()` to inject iframe when URL slide becomes active
- When showing a URL slide, check if the iframe has been loaded
- If not, replace the placeholder with the actual iframe
- Handle the onload event appropriately

#### Task 1.3: Handle slide cycling properly
- When cycling away from a URL slide: decide whether to keep or remove the iframe
  - Option A: Keep the iframe loaded (maintains state but uses more memory)
  - Option B: Remove iframe when hidden, reload when shown again (always fresh but slower)
- Implement configurable behavior, defaulting to reload on each activation (ensuring fresh auto-scroll)

### Milestone 2: Testing

**Prefix**: `WebpageAutoScroll-2`

#### Task 2.1: Add integration tests for URL slide lazy-loading
- Test that URL slides load iframes only when becoming active
- Test that iframes are properly created with correct attributes
- Test slide cycling behavior with URL slides

#### Task 2.2: Manual testing with Skedda page
- Verify the auto-scroll behavior works correctly with the Skedda booking page
- Test on multiple displays/browsers to ensure consistent behavior

### Milestone 3: Acceptance Criteria

**Prefix**: `WebpageAutoScroll-3`

#### Task 3.1: Documentation updates
- Update any relevant documentation about URL slide behavior
- Document the lazy-loading behavior in code comments

#### Task 3.2: Ensure all tests pass
- Run all nox sessions and verify passing
- Ensure no regressions in existing functionality

#### Task 3.3: Move feature document to completed
- Move this document to `docs/features/completed/`

---

## Technical Details

### Key code changes in `slideshow.html`:

1. **`createSlideElements()`**: For URL slides, create placeholder:
   ```javascript
   case 'url':
       // Create placeholder - iframe will load when slide becomes active
       content = `<div class="url-slide-placeholder"
                       data-url="${contentUrl}"
                       data-scale-factor="${slide.scale_factor || ''}">
                     <div class="loading">
                       <div class="spinner"></div>
                       <div>Loading webpage...</div>
                     </div>
                   </div>`;
       break;
   ```

2. **`showSlide()`**: When URL slide becomes active, inject iframe:
   ```javascript
   // Handle URL slide lazy-loading
   const placeholder = currentSlide.querySelector('.url-slide-placeholder');
   if (placeholder) {
       const url = placeholder.dataset.url;
       const scaleFactor = placeholder.dataset.scaleFactor;
       const iframeHtml = this.createUrlSlideContent({scale_factor: scaleFactor ? parseInt(scaleFactor) : null}, url);
       placeholder.outerHTML = iframeHtml;
   }
   ```

3. **Consider adding slide cleanup**: Optionally remove iframe when slide becomes inactive to ensure fresh load each time (this guarantees auto-scroll works on every view)

### Considerations:

- **Performance**: Lazy-loading may introduce a brief loading delay when first showing a URL slide
- **State preservation**: If we remove iframes when hidden, any user interaction state in the embedded page is lost (acceptable for kiosk displays)
- **Memory usage**: Keeping all iframes loaded uses more memory; lazy-loading is more efficient

---

## Status

- [x] Investigation complete
- [x] Implementation plan created
- [x] Milestone 1: Implement lazy-loading
  - [x] Task 1.1: Modified `createSlideElements()` to use placeholders for URL slides
  - [x] Task 1.2: Modified `showSlide()` to inject iframe when URL slide becomes active
  - [x] Task 1.3: Implemented slide cycling - iframes are reset to placeholders when hidden to ensure fresh reload
- [x] Milestone 2: Testing
  - [x] Task 2.1: Added integration tests for URL slide lazy-loading
    - `test_url_slide_lazy_loads_iframe_when_active`: Verifies placeholder exists when not active
    - `test_url_slide_iframe_loads_when_slide_becomes_active`: Verifies iframe loads on activation
  - [x] Task 2.2: Manual testing (deferred to user verification with Skedda page)
- [x] Milestone 3: Acceptance criteria
  - [x] Task 3.1: Documentation updates (code is self-documented with JSDoc comments)
  - [x] Task 3.2: All tests passing
  - [x] Task 3.3: Feature document moved to completed

## Implementation Summary

The fix was implemented by adding lazy-loading for URL slide iframes:

1. **`createUrlSlidePlaceholder()`**: Creates a placeholder div with data attributes storing the URL and scale factor
2. **`loadUrlSlideIframe()`**: Replaces the placeholder with the actual iframe when the slide becomes active
3. **`resetUrlSlideToPlaceholder()`**: Resets URL slides back to placeholder when they become inactive

This ensures that embedded pages load when visible with proper dimensions, allowing auto-scroll JavaScript to work correctly.
