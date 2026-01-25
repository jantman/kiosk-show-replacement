# SSE Slideshow Update Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We did some recent work (see `completed/bug-display-settings-not-realtime.md`) on SSE bugs where slideshows did not update after changes without a manual browser refresh. We have fixed it so changes to the default slideshow duration are picked up immediately by displays, but I've tried adding, deleting, and editing slides within a slideshow and those changes are not being reflected on the display. I think we need to revisit the integration tests that were added during our earlier work to ensure they're complete, and then fix this bug. If needed, I can use the Claude Chrome extension and/or Chrome DevTools MCP server to help explore the live UI with you to analyze this bug.
