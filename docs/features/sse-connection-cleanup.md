# SSE Connection Cleanup Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

SSE (Server-Sent Events) connections are not being properly cleaned up when clients disconnect. This results in stale connections accumulating in the SSE Connection Monitor.

## Observed Behavior

On the System Monitoring page (`/admin/monitoring`), the SSE Connection Monitor shows multiple admin connections even when only a single admin browser tab is open.

### Specific Observations

- **URL**: `http://localhost:3000/admin/monitoring`
- **Expected**: 1 admin SSE connection (matching the single open browser tab)
- **Actual**: 7 admin SSE connections displayed
- All connections show user "admin"
- Connection times vary (some 3 minutes old, some 1 minute old)
- All connections show 0 events sent
- Last ping times are recent (within 30 seconds), suggesting the server thinks these connections are still active

### Connection Details from Monitor

| Type  | User  | Connected             | Duration | Last Ping             | Events |
|-------|-------|-----------------------|----------|-----------------------|--------|
| admin | admin | 1/25/2026, 11:30:36 AM | 3m       | 1/25/2026, 11:33:06 AM | 0      |
| admin | admin | 1/25/2026, 11:30:37 AM | 3m       | 1/25/2026, 11:33:07 AM | 0      |
| admin | admin | 1/25/2026, 11:30:37 AM | 3m       | 1/25/2026, 11:33:07 AM | 0      |
| admin | admin | 1/25/2026, 11:30:37 AM | 3m       | 1/25/2026, 11:33:07 AM | 0      |
| admin | admin | 1/25/2026, 11:32:36 AM | 1m       | 1/25/2026, 11:33:06 AM | 0      |
| admin | admin | 1/25/2026, 11:32:47 AM | 1m       | 1/25/2026, 11:33:17 AM | 0      |
| admin | admin | 1/25/2026, 11:32:47 AM | 1m       | 1/25/2026, 11:33:17 AM | 0      |

## Expected Behavior

- When a client disconnects (browser tab closed, page navigation, refresh), the SSE connection should be removed from the connection tracker
- The SSE Connection Monitor should only show active, valid connections
- Connection count should match the actual number of connected clients

## Relevant Files

- `kiosk_show_replacement/sse.py` - SSE manager and connection handling
- `frontend/src/hooks/useSSE.tsx` - Frontend SSE connection management
- `kiosk_show_replacement/api/v1.py` - SSE API endpoints

## Root Cause Analysis

The SSE connection cleanup issue stems from multiple factors:

### 1. Generator Cleanup is Reactive, Not Proactive
The `finally` block in `create_sse_response()` only runs when `GeneratorExit` is raised. This requires Flask/WSGI to detect a broken pipe during a write operation, which doesn't happen reliably.

### 2. 30-Second Ping Interval Masks Disconnections
The generator in `SSEConnection.get_events()` blocks for up to 30 seconds waiting for events. If a client disconnects during this wait, the server won't detect it until the next write attempt.

### 3. TCP/OS Buffering Delays Failure Detection
Even when writing ping events, TCP buffering can cause writes to appear successful even after the client has closed the connection.

### 4. Frontend Close Not Propagated to Backend
While `eventSource.close()` is called on React unmount, this only closes the client-side connection. The server continues holding the connection reference until either:
- A write fails (up to 30 seconds later)
- The `GeneratorExit` exception is somehow triggered

### 5. Page Navigation Can Interrupt Cleanup
Browser navigation or refresh may interrupt React's cleanup lifecycle before `eventSource.close()` completes.

## Implementation Plan

### Milestone 1: Add Explicit Disconnect Notification (M1)

Implement client-to-server disconnect notification so the server immediately knows when a client disconnects.

**Tasks:**

1. **M1.1 - Add disconnect endpoint to backend**
   - Add `POST /api/v1/events/disconnect` endpoint in `api/v1.py`
   - Accept `connection_id` parameter
   - Call `sse_manager.remove_connection(connection_id)` immediately
   - No authentication required (connection ID serves as auth token)

2. **M1.2 - Send connection ID to client**
   - Modify the initial "connected" event in `create_sse_response()` to include `connection_id`
   - Frontend already receives this event and parses the data

3. **M1.3 - Frontend tracks connection ID and sends disconnect on cleanup**
   - Update `useSSE.tsx` to store the connection ID from the "connected" event
   - In `disconnect()`, use `navigator.sendBeacon()` to POST to `/api/v1/events/disconnect`
   - `sendBeacon` is reliable even during page unload/navigation
   - Add `beforeunload` event listener as backup for tab close

4. **M1.4 - Add unit tests for disconnect endpoint**
   - Test disconnect endpoint removes connection from manager
   - Test invalid connection ID returns appropriate response

### Milestone 2: Improve Write Failure Detection (M2)

Ensure that when ping writes fail, the connection is properly cleaned up.

**Tasks:**

1. **M2.1 - Add write error handling in event generator**
   - Wrap the `yield` statement in `event_stream()` with try/except
   - Catch `BrokenPipeError`, `ConnectionResetError`, and other socket errors
   - Mark connection as inactive and trigger cleanup on any write error

2. **M2.2 - Add unit tests for write failure cleanup**
   - Test that write errors trigger connection removal
   - Test that `is_active` is set to False on write failure

### Milestone 3: Add Integration Tests (M3)

Create Playwright integration tests to verify the fix works end-to-end.

**Tasks:**

1. **M3.1 - Create test for page refresh cleanup**
   - Navigate to monitoring page, verify 1 connection
   - Refresh page, verify still 1 connection (not 2)
   - Use SSE stats API to verify connection count

2. **M3.2 - Create test for tab navigation cleanup**
   - Navigate to monitoring page, verify 1 connection
   - Navigate to different admin page
   - Navigate back to monitoring, verify still 1 connection

3. **M3.3 - Create test for explicit disconnect**
   - Verify that disconnect() properly removes connection

### Milestone 4: Acceptance Criteria Verification (M4)

Final verification and documentation.

**Tasks:**

1. **M4.1 - Run all nox test sessions**
   - Ensure all unit tests pass
   - Ensure all integration tests pass
   - Ensure type checking passes

2. **M4.2 - Manual verification**
   - Test with single browser tab: verify 1 connection
   - Test page refresh: verify no orphaned connections
   - Test tab close: verify connection removed
   - Test navigation: verify connection cleanup

3. **M4.3 - Update documentation if needed**
   - Review if any documentation needs updates

4. **M4.4 - Move feature file to completed**
   - Move this file to `docs/features/completed/`

## Acceptance Criteria

- [ ] SSE connections are removed when clients disconnect
- [ ] Page refresh does not leave orphaned connections
- [ ] Browser tab close properly cleans up connections
- [ ] Navigation away from admin pages properly cleans up connections
- [ ] SSE Connection Monitor accurately reflects actual connected clients

## Progress

- [x] M1: Add Explicit Disconnect Notification (COMPLETE)
  - [x] M1.1 - Add disconnect endpoint to backend
  - [x] M1.2 - Send connection ID to client (already implemented)
  - [x] M1.3 - Frontend tracks connection ID and sends disconnect
  - [x] M1.4 - Add unit tests for disconnect endpoint
- [x] M2: Improve Write Failure Detection (COMPLETE)
  - [x] M2.1 - Add write error handling in event generator
  - [x] M2.2 - Add unit tests for write failure cleanup
- [ ] M3: Add Integration Tests
  - [ ] M3.1 - Test for page refresh cleanup
  - [ ] M3.2 - Test for tab navigation cleanup
  - [ ] M3.3 - Test for explicit disconnect
- [ ] M4: Acceptance Criteria Verification
  - [ ] M4.1 - Run all nox test sessions
  - [ ] M4.2 - Manual verification
  - [ ] M4.3 - Update documentation if needed
  - [ ] M4.4 - Move feature file to completed
