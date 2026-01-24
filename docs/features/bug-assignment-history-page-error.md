# Bug: Assignment History Page Fails to Load

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The "Assignment History & Audit Trail" page at `/admin/assignment-history` (accessible via http://localhost:3000/admin/assignment-history in development) is not functioning correctly.

**Observed behavior:**
- The page displays "0 records"
- An error box is shown with the message: `Failed to load assignment history. Please try again.`

**Expected behavior:**
- The page should load assignment history data (or show an empty state if no history exists, without an error)
- No error message should be displayed when the API is functioning correctly
