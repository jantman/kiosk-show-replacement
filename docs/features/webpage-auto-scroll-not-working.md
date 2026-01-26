# Web Page Slide Auto-Scroll Not Working

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Some web pages have built-in automatic scrolling behavior (e.g., scrolling to a specific position based on the current time of day). This auto-scroll functionality does not work when the page is displayed as a slide.

**Example case**: The Skedda booking page at `https://decaturmakersreservations.skedda.com/booking` automatically scrolls to a time-relevant position when viewed in a normal browser, but this scrolling does not occur when the page is displayed as a web page slide type.

This may be related to how iframes load content, JavaScript execution timing, or other iframe-specific limitations that need investigation.
