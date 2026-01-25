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

### Technical Approach

The implementation will use CSS transforms to scale iframe content. This approach:
- Works reliably across browsers
- Does not require same-origin access to iframe content
- Can be configured per-slide
- Uses a simple scale factor (percentage) that users can understand

**CSS Transform Technique:**
- Apply `transform: scale(X)` to the iframe where X is the scale factor (e.g., 0.5 for 50%)
- Set `transform-origin: 0 0` (top-left) for predictable positioning
- Expand iframe dimensions inversely (e.g., at 50% scale, use 200vw × 200vh) so the scaled content fills the viewport

**User Interface:**
- Add a "Scale" slider/input for URL-type slides (10% to 100%)
- Default to 100% (no scaling) for backward compatibility
- Only show the option for URL content type slides

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

Add scale factor controls to the admin interface for URL slides.

**Prefix:** `WPS-M4`

**Tasks:**
1. **M4.1**: Update `SlideshowItemForm.tsx` to include scale_factor field
   - Show slider/input only for URL content type
   - Range: 10-100 (percentage)
   - Default: 100 (no scaling)

2. **M4.2**: Update TypeScript types for slideshow items

3. **M4.3**: Add integration tests for admin UI scale controls

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
