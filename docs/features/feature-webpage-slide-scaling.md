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
