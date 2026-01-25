# Feature: Web Page Slide Scaling for Full Visibility

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Web page slide types need a mechanism to handle pages with content that exceeds the display viewport, ensuring the full page is visible at one time.

**Current behavior:**
- Web page slides are displayed at their native size/scale
- Pages with content longer than the viewport height require scrolling to see all content
- Since displays are non-interactive, scrollable content is effectively cut off

**Desired behavior:**
- Provide a way to scale/zoom web pages to fit entirely within the display viewport
- The entire page content should be visible without scrolling

**Considerations:**
- This could be implemented as a per-slide option (e.g., "Scale to fit")
- May need to handle both vertical and horizontal overflow
- Could involve CSS transforms, viewport scaling, or iframe zoom techniques

---

## Implementation Plan

### User Experience

**Target user:** Non-technical users who notice that a webpage slide is "cut off" and want to see the whole page.

**User flow:**
1. User adds a webpage slide to their slideshow
2. On the display, they notice only part of the page is visible
3. In the admin, they see a "Zoom" slider for URL slides
4. They drag the slider toward "Zoom out" until the preview shows all the content they want
5. Save and verify on the actual display

**Admin UI:**
- Slider labeled "Zoom" ranging from "Normal" (100%) to "Zoomed out" (10%)
- Only visible for URL-type slides
- Live preview in the admin showing the effect
- Default: 100% (normal, no zoom)

### Technical Approach

The implementation will use CSS transforms to scale iframe content. This approach:
- Works reliably across browsers
- Does not require same-origin access to iframe content
- Can be configured per-slide
- Uses a simple scale factor (percentage)

**CSS Transform Technique:**
- Apply `transform: scale(X)` to the iframe where X is the scale factor (e.g., 0.5 for 50%)
- Set `transform-origin: 0 0` (top-left) for predictable positioning
- Expand iframe dimensions inversely (e.g., at 50% scale, use 200vw × 200vh) so the scaled content fills the viewport

### Design Principles for Future Flexibility

This implementation uses a simple fixed-percentage approach. To support future enhancements (e.g., adaptive scaling based on display size), the following boundaries are maintained:

1. **Data layer isolation**: The model stores only `scale_factor` (integer 10-100). Future implementations could reinterpret this or add new fields.

2. **Rendering logic isolation**: The CSS transform calculation is contained in a single, clearly-documented section of `slideshow.html`. Swapping to a different scaling method requires changes only there.

3. **API abstraction**: The API accepts/returns `scale_factor` without exposing implementation details. Future versions could accept additional parameters.

4. **UI abstraction**: The admin presents a user-friendly "Zoom" slider. The underlying value (percentage) is an implementation detail that could change.

### Known Limitations (Documented)

- **Fixed percentage**: The scale factor is a fixed percentage applied identically regardless of display resolution. A 50% zoom on a 1080p display and a 4K display will show different amounts of content.
- **Multi-display slideshows**: If a slideshow is shown on displays of different sizes, the same scale factor may produce different results. Users with varied display sizes may need separate slideshows.
- **No auto-detection**: The system cannot automatically detect webpage content dimensions due to cross-origin iframe restrictions.

These limitations are candidates for future feature work (e.g., "adaptive scaling" or "per-display overrides").

---

### Milestone 1: Database and Model Changes

Add a `scale_factor` field to store the zoom percentage for URL slides.

**Prefix:** `WPS-M1`

**Tasks:**
1. **M1.1**: Add `scale_factor` column to `SlideshowItem` model
   - Type: `Integer`, nullable
   - Valid range: 10-100 (representing percentage)
   - `null` or `100` = no scaling (100%)
   - Only meaningful for `content_type='url'`

2. **M1.2**: Create Alembic database migration

3. **M1.3**: Update `SlideshowItem.to_dict()` to include `scale_factor` in output

4. **M1.4**: Add unit tests for model changes

**Status:** Not started

---

### Milestone 2: API Updates

Update the REST API to accept and return the scale_factor field.

**Prefix:** `WPS-M2`

**Tasks:**
1. **M2.1**: Update `POST /api/v1/slideshows/<id>/items` to accept `scale_factor`
   - Validate range (10-100 or null)
   - Only applies when `content_type='url'`

2. **M2.2**: Update `PUT /api/v1/slideshow-items/<id>` to accept `scale_factor`
   - Same validation as create

3. **M2.3**: Add unit tests for API endpoints with scale_factor

**Status:** Not started

---

### Milestone 3: Display Rendering

Update the display template to apply CSS transform scaling based on scale_factor.

**Prefix:** `WPS-M3`

**Tasks:**
1. **M3.1**: Update `slideshow.html` CSS to support scaled iframes
   - Add CSS class for scaled iframes
   - Handle transform and dimension calculations

2. **M3.2**: Update JavaScript slide rendering to apply scaling
   - Read scale_factor from slide data
   - Apply appropriate CSS transform and container sizing
   - Ensure proper transform-origin (top-left)

3. **M3.3**: Add integration tests verifying scaled iframe rendering

**Status:** Not started

---

### Milestone 4: Frontend Admin UI

Add zoom controls to the admin interface for URL slides.

**Prefix:** `WPS-M4`

**Tasks:**
1. **M4.1**: Update TypeScript types for slideshow items to include `scale_factor`

2. **M4.2**: Update `SlideshowItemForm.tsx` to include zoom slider
   - Show slider only for URL content type
   - Label: "Zoom" with "Normal" (100%) to "Zoomed out" (10%) range
   - Default: 100 (no zoom/normal)
   - Include preview showing scaled iframe

3. **M4.3**: Add integration tests for admin UI zoom controls

**Status:** Not started

---

### Milestone 5: Acceptance Criteria

Final validation and documentation.

**Prefix:** `WPS-M5`

**Tasks:**
1. **M5.1**: Update documentation as needed (README.md, docs/*.rst)

2. **M5.2**: Verify all unit tests pass and have appropriate coverage

3. **M5.3**: Verify all nox sessions pass successfully

4. **M5.4**: Move feature file to `docs/features/completed/`

**Status:** Not started

---

## Progress Log

_Progress updates will be added here as milestones are completed._
