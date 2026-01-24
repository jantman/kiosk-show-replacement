# Bug: Assignment History Page Fails to Load

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Status: RESOLVED

## Overview

The "Assignment History & Audit Trail" page at `/admin/assignment-history` (accessible via http://localhost:3000/admin/assignment-history in development) was not functioning correctly.

**Observed behavior:**
- The page displayed "0 records"
- An error box was shown with the message: `Failed to load assignment history. Please try again.`

**Expected behavior:**
- The page should load assignment history data (or show an empty state if no history exists, without an error)
- No error message should be displayed when the API is functioning correctly

## Root Cause

The frontend React component (`frontend/src/pages/AssignmentHistory.tsx`) was making API calls to `/api/v1/assignment-history`, but this endpoint did not exist in the backend. The `AssignmentHistory` model existed and was already being used to create records when slideshow assignments changed, but there was no API endpoint to retrieve these records.

## Solution

Added the missing `/api/v1/assignment-history` GET endpoint to the backend API (`kiosk_show_replacement/api/v1.py`).

The endpoint:
- Returns assignment history records ordered by `created_at` descending (newest first)
- Supports optional query parameters for filtering:
  - `limit`: Maximum number of records to return (default: 50, max: 200)
  - `display_id`: Filter by specific display ID
  - `action`: Filter by action type (assign, unassign, change)
  - `user_id`: Filter by user who made the change
- Requires authentication

## Changes Made

1. **Backend API** (`kiosk_show_replacement/api/v1.py`):
   - Added `AssignmentHistory` to the module-level imports
   - Added `list_assignment_history()` endpoint at `/api/v1/assignment-history`
   - Removed redundant local imports of `AssignmentHistory` in `update_display()` and `assign_slideshow_to_display()` functions

2. **Integration Tests** (`tests/integration/test_assignment_history_api.py`):
   - Added comprehensive tests for the new endpoint:
     - Empty list handling
     - List with records
     - Filtering by display_id
     - Filtering by action type
     - Filtering by user_id
     - Limit parameter
     - Authentication requirement
     - Combined filters
     - Record ordering (descending by created_at)

## Testing

- All 381 unit tests pass
- All 10 new integration tests for assignment history pass
- Type checking passes with no issues
- Format and lint checks pass
