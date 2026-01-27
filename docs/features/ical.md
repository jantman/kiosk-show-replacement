# iCal support

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We use [Skedda](https://www.skedda.com/) for reserving various pieces of equipment ("spaces") in our makerspace, and want to be able to display reservations on a calendar-type slide. The preferred "Day" display format can be seen at https://decaturmakersreservations.skedda.com/booking or in the screenshot at `docs/features/completed/skedda.png`. Skedda provides an iCal feed of reservations, where the format of the `DESCRIPTION` field is `Spaces: <name of space>\n\nNotes: <notes>` and the format of the `SUMMARY` field is `<person name>: <short description> (<name of space>)`. Each space can only have one booking/event at a given time.

The screenshot at `docs/features/completed/skedda.png` was taken at January 26th 2026 17:48 EST but is showing January 28th 2026 from approximately 7AM EST to approximately 11PM EST. The `.ics` file at `tests/assets/skedda.ics` is the actual Skedda ICS resource at the same time. If using this ICS file in tests, be aware of the times and that we will need to either adjust the file or use something like `freezegun` to freeze the time.

We need to add a new slide type to our slideshows, `Skedda`, to display events these booking events. The calendar itself will be specified via a URL, and the data for it should be downloaded on the backend on a regular basis that is configurable via the slide editing UI (default every 15 minutes). The calendar should be displayed in the frontend using a grid such as that in the above screenshot, that has rows for each 30-minute interval and columns for each distinct space (`name of space`). The bookings should be clearly shown with `person name` and `short description`. At any given time, the calendar should be displayed so that the current time is at the top of the viewable area. The content of the calendar slide should always be updated when the slide is displayed (i.e. this content can't be lazy-loaded at the beginning of the slideshow; if the slideshow is active for hours or days, the calendar slide should be accurate relative to the current time).

When implementing this feature, we should implement it on top of a generic ICS calendar implementation, such that in the future we can also add other calendar types like an event calendar (without the Skedda-specific formatting and columns).

---

## Implementation Plan

### Background Research

**Current State:**
- SlideshowItem model supports content types: `image`, `video`, `url`, `text`
- Display template (display.html) renders slides based on `content_type` using a switch statement
- Frontend SlideshowItemForm has conditional rendering based on content type
- The backend uses Flask/SQLAlchemy, frontend uses React/TypeScript

**ICS File Analysis (from `tests/assets/skedda.ics`):**
- Skedda events have:
  - `SUMMARY`: `<person name>: <short description> (<space name>)` or `<event name> (<space name> + N others)` for multi-space events
  - `RESOURCES`: One or more lines listing each space (e.g., `RESOURCES:Brontë Laser Cutter`)
  - `DESCRIPTION`: `Spaces: <comma-separated spaces>\n\nNotes: <optional notes>`
  - `ATTENDEE`: `CN=<name>:mailto:<email>` (optional)
  - `DTSTART`/`DTEND`: Event times with timezone
- Events can span multiple spaces (blocking all of them simultaneously)

**Key Design Decisions:**
1. **New content type**: Add `skedda` as a new content_type value (building on generic ICS infrastructure)
2. **Backend caching**: ICS data will be fetched and cached on the backend with configurable refresh intervals
3. **Database fields**: Add new fields to SlideshowItem for ICS configuration:
   - `ical_url`: URL of the ICS feed
   - `ical_refresh_minutes`: How often to refresh (default 15)
   - `ical_cached_data`: JSON blob of parsed calendar data
   - `ical_last_fetched`: Timestamp of last fetch
4. **API endpoint**: New endpoint to get parsed/formatted calendar data for display
5. **Frontend rendering**: Custom calendar grid component with auto-scrolling to current time
6. **Python library**: Use `icalendar` library for ICS parsing

### Implementation Approach

The implementation will build a generic ICS calendar infrastructure with Skedda-specific rendering, allowing future calendar types to be added easily.

---

## Milestones

### Milestone 1: Backend ICS Infrastructure (ICAL-M1)

**Goal:** Add ICS parsing capability and new database fields for calendar slides.

#### Task 1.1 (ICAL-M1.1): Add icalendar dependency to pyproject.toml
- Add `icalendar` package to dependencies
- Run `poetry lock` to update lock file

#### Task 1.2 (ICAL-M1.2): Add new fields to SlideshowItem model
- Add `ical_url` (String, optional): URL of ICS feed
- Add `ical_refresh_minutes` (Integer, optional): Refresh interval in minutes (default 15)
- Add `ical_cached_data` (Text, optional): JSON-encoded parsed calendar data
- Add `ical_last_fetched` (DateTime, optional): Last successful fetch timestamp
- Add `skedda` to allowed content_type values
- Update `to_dict()` method to include new fields
- Create database migration

#### Task 1.3 (ICAL-M1.3): Create ICS parser module
- Create `kiosk_show_replacement/ical_parser.py` module
- Implement `parse_ics_data(ics_content: str) -> dict` function:
  - Parse ICS content using icalendar library
  - Extract events with: uid, summary, start, end, resources (spaces), attendee name
  - Return structured dict with events list and metadata
- Implement `parse_skedda_summary(summary: str) -> tuple[str, str, str]`:
  - Parse Skedda SUMMARY format to extract: person_name, description, space_name
  - Handle both single-space and multi-space formats
- Add comprehensive unit tests for parsing functions

#### Task 1.4 (ICAL-M1.4): Create ICS fetcher service
- Create `kiosk_show_replacement/ical_service.py` module
- Implement `fetch_ics_from_url(url: str) -> str | None` function:
  - Use requests library to fetch ICS content
  - Handle errors gracefully (timeout, network errors, invalid content)
  - Return ICS content as string or None on error
- Implement `update_slide_ics_cache(slide: SlideshowItem) -> bool`:
  - Check if cache needs refresh based on `ical_last_fetched` and `ical_refresh_minutes`
  - Fetch ICS data if needed
  - Parse and store in `ical_cached_data`
  - Update `ical_last_fetched` timestamp
  - Return True if cache was updated
- Implement `get_skedda_calendar_data(slide: SlideshowItem, target_date: date | None = None) -> dict`:
  - Get cached data (updating if needed)
  - Filter events for the target date (default today)
  - Group events by space (column) and time slot (row)
  - Return formatted data structure for frontend rendering
- Add unit tests with mocked HTTP responses

**Milestone 1 Deliverables:**
- icalendar dependency added
- SlideshowItem model updated with new fields
- Database migration created and applied
- ICS parser module with unit tests
- ICS service module with unit tests
- All existing tests passing

---

### Milestone 2: Backend API Endpoints (ICAL-M2)

**Goal:** Add API endpoints for creating Skedda slides and retrieving calendar data.

#### Task 2.1 (ICAL-M2.1): Update slideshow item creation endpoint
- Modify `POST /api/v1/slideshows/<id>/items` to accept `skedda` content type
- Accept and validate new fields: `ical_url`, `ical_refresh_minutes`
- Validate URL format and optionally test connectivity
- Initial ICS fetch on creation to validate URL works

#### Task 2.2 (ICAL-M2.2): Update slideshow item update endpoint
- Modify `PUT /api/v1/slideshow-items/<id>` to handle `skedda` type
- Allow updating `ical_url` and `ical_refresh_minutes`
- Re-fetch ICS data when URL changes

#### Task 2.3 (ICAL-M2.3): Add calendar data API endpoint
- Create `GET /api/v1/slideshow-items/<id>/skedda-data` endpoint:
  - Fetch latest calendar data (refreshing cache if needed)
  - Accept optional `date` query parameter (default: today)
  - Return formatted data structure for frontend:
    ```json
    {
      "date": "2026-01-28",
      "spaces": ["CNC Milling Machine", "Glowforge Laser Cutter", ...],
      "time_slots": [
        {"time": "07:00", "display": "7:00 AM"},
        {"time": "07:30", "display": "7:30 AM"},
        ...
      ],
      "events": [
        {
          "id": "...",
          "space": "Brontë Laser Cutter",
          "person_name": "Janelle M",
          "description": "Crafts",
          "start_time": "12:00",
          "end_time": "16:00",
          "row_span": 8
        },
        ...
      ],
      "last_updated": "2026-01-28T10:30:00Z"
    }
    ```
- Add unit tests for new endpoint

**Milestone 2 Deliverables:**
- Updated slideshow item CRUD endpoints for skedda type
- New skedda-data endpoint for frontend
- Unit tests for all API changes
- All tests passing

---

### Milestone 3: Frontend Skedda Form (ICAL-M3)

**Goal:** Add UI for creating and editing Skedda calendar slides.

#### Task 3.1 (ICAL-M3.1): Update TypeScript types
- Add `skedda` to `content_type` union in `SlideshowItem` interface
- Add new optional fields: `ical_url`, `ical_refresh_minutes`, `ical_cached_data`, `ical_last_fetched`
- Add `SkedddaCalendarData` interface for API response

#### Task 3.2 (ICAL-M3.2): Update SlideshowItemForm component
- Add `skedda` option to content type dropdown (labeled "Skedda Calendar")
- Add conditional form fields when `skedda` is selected:
  - ICS Feed URL input (required)
  - Refresh interval dropdown (5, 10, 15, 30, 60 minutes)
- Add URL validation
- Show validation status/errors for ICS URL

#### Task 3.3 (ICAL-M3.3): Add form integration tests
- Test creating a Skedda slide with valid URL
- Test validation errors for invalid URL
- Test editing Skedda slide configuration

**Milestone 3 Deliverables:**
- Updated TypeScript types
- SlideshowItemForm supports Skedda type
- Integration tests for Skedda form
- All tests passing

---

### Milestone 4: Frontend Calendar Display (ICAL-M4)

**Goal:** Create the Skedda calendar grid component for display rendering.

#### Task 4.1 (ICAL-M4.1): Create SkedddaCalendar component
- Create `kiosk_show_replacement/static/js/skedda-calendar.js`:
  - Implement `SkedddaCalendar` class that renders the calendar grid
  - Grid has time slots (rows) and spaces (columns)
  - Events are positioned based on start/end times with appropriate row spans
  - Current time indicator with auto-scroll to keep current time near top
  - Responsive design to fit kiosk display
  - Auto-refresh every minute to update time position
- Style to match Skedda screenshot aesthetic:
  - Green header with space names
  - Time labels on left
  - Events as colored blocks with person name and description
  - Grid lines for visual clarity

#### Task 4.2 (ICAL-M4.2): Update display.html template
- Add case for `skedda` content type in slide creation
- Include skedda-calendar.js
- Render SkedddaCalendar component with API data fetch
- Implement dynamic refresh: fetch new data from API each time slide becomes active
- CSS for calendar styling embedded in template

#### Task 4.3 (ICAL-M4.3): Add E2E tests for calendar display
- Test that Skedda slide renders calendar grid
- Test that events are displayed correctly
- Test auto-scroll behavior (with frozen time)
- Test that calendar refreshes when slide cycles back

**Milestone 4 Deliverables:**
- SkedddaCalendar JavaScript component
- Updated display.html with Skedda rendering
- CSS styling for calendar
- E2E tests for calendar display
- All tests passing

---

### Milestone 5: Acceptance Criteria (ICAL-M5)

**Goal:** Final verification, documentation, and cleanup.

#### Task 5.1 (ICAL-M5.1): Verify all nox sessions pass
- Run all nox sessions: `test-3.14`, `test-integration`, `test-e2e`, `lint`, `type_check`, `format`
- Fix any failures

#### Task 5.2 (ICAL-M5.2): Update documentation
- Update `docs/usage.rst` with Skedda slide configuration
- Update `README.md` if any user-facing changes
- Add any needed information to `CLAUDE.md`

#### Task 5.3 (ICAL-M5.3): Move feature file to completed
- Move this file from `docs/features/` to `docs/features/completed/`

**Milestone 5 Deliverables:**
- All nox sessions passing
- Documentation updated
- Feature file moved to completed directory
- GitHub PR created/updated with all checks passing

---

## Progress Log

### 2026-01-27 - Planning Complete
- Implementation plan created and committed
- Feature branch `feature/ical-calendar` created
