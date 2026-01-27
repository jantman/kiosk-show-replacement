# iCal support

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We use [Skedda](https://www.skedda.com/) for reserving various pieces of equipment ("spaces") in our makerspace, and want to be able to display reservations on a calendar-type slide. The preferred "Day" display format can be seen at https://decaturmakersreservations.skedda.com/booking or in the screenshot at `docs/features/completed/skedda.png`. Skedda provides an iCal feed of reservations, where the format of the `DESCRIPTION` field is `Spaces: <name of space>\n\nNotes: <notes>` and the format of the `SUMMARY` field is `<person name>: <short description> (<name of space>)`. Each space can only have one booking/event at a given time.

The screenshot at `docs/features/completed/skedda.png` was taken at January 26th 2026 17:48 EST but is showing January 28th 2026 from approximately 7AM EST to approximately 11PM EST. The `.ics` file at `tests/assets/skedda.ics` is the actual Skedda ICS resource at the same time. If using this ICS file in tests, be aware of the times and that we will need to either adjust the file or use something like `freezegun` to freeze the time.

We need to add a new slide type to our slideshows, `Skedda`, to display events these booking events. The calendar itself will be specified via a URL, and the data for it should be downloaded on the backend on a regular basis that is configurable via the slide editing UI (default every 15 minutes). The calendar should be displayed in the frontend using a grid such as that in the above screenshot, that has rows for each 30-minute interval and columns for each distinct space (`name of space`). The bookings should be clearly shown with `person name` and `short description`. At any given time, the calendar should be displayed so that the current time is at the top of the viewable area. The content of the calendar slide should always be updated when the slide is displayed (i.e. this content can't be lazy-loaded at the beginning of the slideshow; if the slideshow is active for hours or days, the calendar slide should be accurate relative to the current time).

When implementing this feature, we should implement it on top of a generic ICS calendar implementation, such that in the future we can also add other calendar types like an event calendar (without the Skedda-specific formatting and columns).
