# Display Reload Button

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Sometimes when slideshows are changed, displays miss the SSE event notification. To address this, add a capability to manually send a slideshow update SSE message to a specific display, causing it to reload its slideshow.

This should be implemented as a new action button on the Displays admin page (`/admin/displays`). When clicked, the button should trigger an SSE message to the targeted display instructing it to reload its current slideshow.
