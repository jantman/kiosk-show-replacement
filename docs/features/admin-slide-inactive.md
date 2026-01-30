# Admin Slide Inactive

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

When a slideshow slide is changed to inactive (Active false) via the admin UI, it disappears from the admin UI! There's no way to reactivate it! Inactive slides should still be shown in the admin UI (so that they can be reactivated if/when desired) but should be visually distinct such as being grayed out.

We need to fix this bug while ensuring that it does not change the behavior for actual slideshows; i.e. inactive slides should be visible and edit-able in the admin UI but still not appear in a slideshow.

Before fixing this, we should add the following integration tests:

1. Ability to see inactive slides in the admin UI (currently failing; should pass when our bug fix is complete).
2. Ability to re-activate an inactive slide via the admin UI (currently failing; should pass when our bug fix is complete).
3. If we don't already have a test for this, inactive slides are not included in slideshow display (should already be passing).
