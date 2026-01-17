# Admin Integration Tests

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

In `tests/integration/test_full_user_experience.py` we have an integration test (full browser test of the actual React frontend and Flask backend) that claims to test the "complete user experience" but this really only tests the ability to login and see the dashboard. We need to first specify and then implement integration tests for the full functionality of the admin interface, including flows such as adding, editing, and managing slideshows, adding, editing, managing, and rearranging slideshow items (including uploading items of each supported type), managing displays and assigning slideshows to them, and all other user flows supported by the admin interface.

We should identify a list of user flows supported by the admin interface of the application and then specify and implement a test for each of them.

It is important to note that this application is very early in its development phase and many critical flows may currently be broken; so when we run the tests, we cannot assume that any test failures are a problem with the test, it may have found a legitimate problem with the application.

These tests are scoped to the admin functionality only; the display functionality will be tested in a future feature.

## Implementation Plan

### Identified User Flows

Based on codebase analysis, the following user flows exist in the admin interface:

**Authentication (1 flow)**
1. Login with credentials → redirect to dashboard

**Dashboard (3 flows)**
1. View dashboard statistics (slideshows count, displays count, online/offline)
2. View recent slideshows list
3. Navigate via quick action buttons

**Slideshow Management (5 flows)**
1. View slideshow list
2. Create new slideshow (with form validation)
3. Edit existing slideshow
4. Delete slideshow (with confirmation)
5. Set slideshow as default

**Slideshow Item Management (5 flows)**
1. Add item to slideshow (image upload)
2. Add item to slideshow (video upload)
3. Add item to slideshow (URL)
4. Add item to slideshow (text)
5. Edit slideshow item
6. Delete slideshow item
7. Reorder slideshow items (move up/down)

**Display Management (6 flows)**
1. View display list
2. Search/filter displays
3. Assign slideshow to single display
4. Bulk assign slideshow to multiple displays
5. Delete display
6. Open display in new tab

**Display Detail (4 flows)**
1. View display details
2. Edit display information
3. Quick assign slideshow (click or drag-drop)
4. View assignment history section

**Assignment History (2 flows)**
1. View assignment history list
2. Filter assignment history

**System Monitoring (3 flows)**
1. View SSE debug tools
2. View display status tab
3. View system health tab

**Note:** The Assignment History API endpoint (`/api/v1/assignment-history`) does not currently exist in the backend. A separate feature file will be created to implement this endpoint.

### Milestones

#### Milestone 1: Test Infrastructure & Helpers
**Prefix:** `AIT-1`

Establish shared test infrastructure, fixtures, and helper utilities to support all integration tests.

**Tasks:**
1. **AIT-1.1** Create `tests/integration/conftest.py` with shared fixtures:
   - `authenticated_page` fixture that handles login
   - `test_slideshow` fixture that creates a slideshow via API
   - `test_display` fixture that creates a display via API
   - Helper functions for common operations
2. **AIT-1.2** Create `tests/integration/helpers.py` with utility functions:
   - `wait_for_toast()` - wait for success/error toast messages
   - `fill_form()` - standardized form filling
   - `confirm_dialog()` - handle confirmation dialogs
   - API helper functions for test data setup/teardown
3. **AIT-1.3** Refactor existing `test_full_user_experience.py` to use new fixtures
4. **AIT-1.4** Verify all existing tests still pass

#### Milestone 2: Slideshow CRUD Tests
**Prefix:** `AIT-2`

Test slideshow listing, creation, editing, deletion, and default setting.

**Tasks:**
1. **AIT-2.1** Create `tests/integration/test_slideshow_management.py`
2. **AIT-2.2** Implement test: view slideshow list (empty state and with data)
3. **AIT-2.3** Implement test: create new slideshow with all form fields
4. **AIT-2.4** Implement test: create slideshow validation errors
5. **AIT-2.5** Implement test: edit existing slideshow
6. **AIT-2.6** Implement test: delete slideshow with confirmation
7. **AIT-2.7** Implement test: set slideshow as default
8. **AIT-2.8** Run full test suite, ensure all tests pass

#### Milestone 3: Slideshow Item Management Tests
**Prefix:** `AIT-3`

Test adding, editing, deleting, and reordering slideshow items of all content types.

**Tasks:**
1. **AIT-3.1** Create `tests/integration/test_slideshow_items.py`
2. **AIT-3.2** Implement test: add image item via file upload
3. **AIT-3.3** Implement test: add image item via URL
4. **AIT-3.4** Implement test: add video item via file upload
5. **AIT-3.5** Implement test: add video item via URL
6. **AIT-3.6** Implement test: add URL item
7. **AIT-3.7** Implement test: add text item
8. **AIT-3.8** Implement test: edit existing item
9. **AIT-3.9** Implement test: delete item with confirmation
10. **AIT-3.10** Implement test: reorder items (move up/down)
11. **AIT-3.11** Run full test suite, ensure all tests pass

#### Milestone 4: Display Management Tests
**Prefix:** `AIT-4`

Test display listing, searching, filtering, and bulk operations.

**Tasks:**
1. **AIT-4.1** Create `tests/integration/test_display_management.py`
2. **AIT-4.2** Implement test: view display list (empty state and with data)
3. **AIT-4.3** Implement test: search displays by name
4. **AIT-4.4** Implement test: filter displays by status (online/offline)
5. **AIT-4.5** Implement test: filter displays by assignment status
6. **AIT-4.6** Implement test: assign slideshow to single display
7. **AIT-4.7** Implement test: bulk assign slideshow to multiple displays
8. **AIT-4.8** Implement test: delete display with confirmation
9. **AIT-4.9** Run full test suite, ensure all tests pass

#### Milestone 5: Display Detail & Assignment Tests
**Prefix:** `AIT-5`

Test display detail view, editing, and quick assignment features.

**Tasks:**
1. **AIT-5.1** Create `tests/integration/test_display_detail.py`
2. **AIT-5.2** Implement test: view display detail page
3. **AIT-5.3** Implement test: edit display information
4. **AIT-5.4** Implement test: quick assign slideshow via click
5. **AIT-5.5** Implement test: unassign slideshow
6. **AIT-5.6** Implement test: assignment history section displays (if data exists)
7. **AIT-5.7** Run full test suite, ensure all tests pass

#### Milestone 6: Dashboard & Navigation Tests
**Prefix:** `AIT-6`

Test dashboard statistics, recent items, and navigation flows.

**Tasks:**
1. **AIT-6.1** Create `tests/integration/test_dashboard.py`
2. **AIT-6.2** Implement test: dashboard displays correct statistics
3. **AIT-6.3** Implement test: dashboard shows recent slideshows
4. **AIT-6.4** Implement test: dashboard shows display status
5. **AIT-6.5** Implement test: quick action buttons navigate correctly
6. **AIT-6.6** Implement test: navigation bar links work correctly
7. **AIT-6.7** Run full test suite, ensure all tests pass

#### Milestone 7: System Monitoring Tests
**Prefix:** `AIT-7`

Test system monitoring page tabs and functionality.

**Tasks:**
1. **AIT-7.1** Create `tests/integration/test_system_monitoring.py`
2. **AIT-7.2** Implement test: SSE debug tools tab loads
3. **AIT-7.3** Implement test: display status tab loads
4. **AIT-7.4** Implement test: system health tab shows status
5. **AIT-7.5** Run full test suite, ensure all tests pass

#### Milestone 8: Acceptance Criteria
**Prefix:** `AIT-8`

Final validation and documentation.

**Tasks:**
1. **AIT-8.1** Ensure all integration tests pass
2. **AIT-8.2** Update `CLAUDE.md` with any new testing patterns or conventions
3. **AIT-8.3** All nox sessions must pass (`nox -s test`, `nox -s test-integration`, `nox -s lint`, `nox -s type_check`)
4. **AIT-8.4** Move feature file to `docs/features/completed/`

### Bug Handling Strategy

When a test discovers an application bug:
1. Mark the test with `pytest.skip("Bug: <description>")` or `@pytest.mark.xfail(reason="Bug: <description>")`
2. In the same commit, create a new feature file in `docs/features/` describing the bug and proposed fix
3. Continue with remaining tests
4. Document all discovered bugs in this feature file under "Discovered Issues" section

### Test Assets

Test files for upload tests are located in `tests/assets/`:
- **Images:** `smallPhoto.jpg`, `bigPhoto.jpg`, `tallPhoto.jpg`, `widePhoto.jpg`
- **Video:** `crash_into_pole.mpeg`

For URL-type slideshow items, tests should use `https://example.com` (IANA reserved domain, guaranteed stable).

### Out of Scope

The following are explicitly out of scope for this feature:
- **Assignment History Backend API**: The `/api/v1/assignment-history` endpoint does not exist. A separate feature file will be created for this.
- **Display Client Tests**: Testing the display rendering (non-admin) functionality
- **Real-time SSE Event Testing**: Deep testing of SSE event propagation (basic connectivity only)
- **Performance/Load Testing**: Only functional correctness is tested

### Progress Tracking

| Milestone | Status | Notes |
|-----------|--------|-------|
| M1: Test Infrastructure | Not Started | |
| M2: Slideshow CRUD | Not Started | |
| M3: Slideshow Items | Not Started | |
| M4: Display Management | Not Started | |
| M5: Display Detail | Not Started | |
| M6: Dashboard & Navigation | Not Started | |
| M7: System Monitoring | Not Started | |
| M8: Acceptance Criteria | Not Started | |

### Discovered Issues

_This section will be updated as bugs are discovered during test implementation._
