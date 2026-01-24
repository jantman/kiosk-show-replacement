# Bug: Monitoring Page Shows Errors and Missing Data

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The Monitoring page at `/admin/monitoring` (accessible via http://localhost:3000/admin/monitoring in development) has multiple issues across its tabs.

### SSE Debug Tools Tab

**Observed behavior:**
- Shows "No active SSE connections found."
- All statistics show no data:
  - Total Connections: (empty/zero)
  - Admin Connections: (empty/zero)
  - Display Connections: (empty/zero)
  - Events (Last Hour): (empty/zero)

**Expected behavior:**
- Should reflect actual SSE connection state
- The Admin UI header shows SSE is live and a display is connected, so this data should be displayed here

### Display Status Tab

**Observed behavior:**
- Displays an error div with the message: `Error loading display status: Failed to fetch display status: NOT FOUND`

**Expected behavior:**
- Should show the status of connected displays without errors
