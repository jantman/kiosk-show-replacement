# SSE Connection Monitor Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We did some recent work (see `completed/bug-monitoring-page-errors.md`) to fix bugs in the system monitoring page (`http://localhost:3000/admin/monitoring`). We've successfully fixed the issues with Display Status, but despite our work for that feature and the fact that we added tests for this work, I'm still seeing no information in the "Total Connections", "Admin Connections", "Display Connections" and "Events (Last Hour)" fields of the "SSE Debug Tools" tab of the System Monitoring page. I also see an info box saying "No active SSE connections found." even though both one display and my current admin session have SSE connections. We need to revisit the tests that we added for this functionality and then fix these bugs so this page works as expected. If needed, I can use the Claude Chrome extension and/or Chrome DevTools MCP server to help explore the live UI with you to analyze this bug.

---

## Root Cause Analysis

### Existing Test Gap

The integration test `test_sse_debug_tools_shows_connection_stats` in `tests/integration/test_system_monitoring.py` only verifies that the *labels* "Admin Connections" and "Total Connections" are visible, but it does NOT verify:
1. That these values are non-zero
2. That the connections table shows actual connection data
3. That "No active SSE connections found." is NOT displayed

**Problematic test assertions (lines 183-191):**
```python
# Verify the admin connection count is shown
# The "Admin Connections" stat should show at least 1 (our connection)
admin_connections = page.locator("text=Admin Connections").first
expect(admin_connections).to_be_visible(timeout=5000)

# The total connections should be visible and have a non-zero count
total_connections = page.locator("text=Total Connections").first
expect(total_connections).to_be_visible(timeout=5000)
```

This only checks that the text labels are visible, not that the actual count values are greater than zero or that the connections table is populated.

### Architecture Analysis

**SSE Connection Flow:**
1. Frontend `SSEDebugger.tsx` uses `useSSE('/api/v1/events/admin')` hook
2. `useSSE` creates an `EventSource` connection to the backend
3. Backend's `/api/v1/events/admin` endpoint calls `sse_manager.create_connection()`
4. Connection is stored in `sse_manager.connections` dictionary
5. When `fetchStats()` is called, it hits `/api/v1/events/stats`
6. The stats endpoint reads from the same `sse_manager.connections`

**Potential Issues Identified:**

1. **Timing/Race Condition**: On component mount, both `fetchStats()` and `useSSE` hook start simultaneously. The stats fetch may complete before the SSE connection is established on the server side.

2. **Component Mount Order**: The SSEDebugger component's `useEffect` hook calls `fetchStats()` immediately on mount (lines 92-94), but the SSE connection establishment is asynchronous.

3. **Test Verification Gap**: Even clicking "Refresh" may not help if the initial SSE connection was never properly established.

---

## Implementation Plan

### Milestone 1: Regression Tests (M1)
**Prefix:** `M1`

Per the guidelines, bug fixes must BEGIN with creating regression tests that should initially fail.

#### Task 1.1: Fix SSE stats integration test to verify actual values

Update `tests/integration/test_system_monitoring.py::test_sse_debug_tools_shows_connection_stats` to:
- Wait for the SSE connection to be established (check `connectionState` in the UI or wait for the connected event)
- Click refresh button AFTER SSE connection is confirmed established
- Verify that the total connections count shows at least 1 (not just that the label is visible)
- Verify that admin connections count shows at least 1
- Verify that "No active SSE connections found." is NOT visible

#### Task 1.2: Add test for connections table visibility

Add test to verify that when an admin session is active with SSE:
- The connections table is visible
- At least one row appears in the connections table
- The connection shows "admin" type

---

### Milestone 2: Investigate and Fix SSE Connection Issues (M2)
**Prefix:** `M2`

#### Task 2.1: Live debugging with Chrome DevTools

Use Chrome DevTools MCP server (if available) to:
- Navigate to the monitoring page
- Check what `/api/v1/events/stats` actually returns
- Verify the EventSource connection to `/api/v1/events/admin` is established
- Check browser console for any errors
- Identify the exact point of failure

#### Task 2.2: Fix identified issues

Based on debugging findings, fix the root cause. Potential fixes may include:
- Adding a delay in `fetchStats()` to wait for SSE connection
- Using SSE connection state to trigger stats refresh
- Ensuring the SSE connection is properly registered before stats are fetched
- Fix any backend issues with connection registration

---

### Milestone 3: Acceptance Criteria (M3)
**Prefix:** `M3`

#### Task 3.1: Verify all unit tests pass
Run `nox -s test-3.14` and ensure all tests pass.

#### Task 3.2: Verify all integration tests pass
Run `nox -s test-integration` and ensure all tests pass.

#### Task 3.3: Verify all nox sessions pass
Run all nox sessions:
- `nox -s format`
- `nox -s lint`
- `nox -s type_check`
- `nox -s test-3.14`
- `nox -s test-integration`

#### Task 3.4: Update documentation if needed
Review and update any relevant documentation.

#### Task 3.5: Move feature file to completed
Move this file to `docs/features/completed/`.

---

## Progress Tracking

- [x] **Milestone 1: Regression Tests** - Complete
  - [x] Task 1.1: Fix SSE stats integration test to verify actual values
  - [x] Task 1.2: Add test for connections table visibility
- [x] **Milestone 2: Investigate and Fix** - Complete
  - [x] Task 2.1: Live debugging with Chrome DevTools - Found root cause
  - [x] Task 2.2: Fix identified issues - Fixed `setStats(data)` to `setStats(data.data)`
- [x] **Milestone 3: Acceptance Criteria** - Complete
  - [x] Task 3.1: Unit tests pass (418 passed)
  - [x] Task 3.2: Integration tests pass (93 passed, 2 xpassed)
  - [x] Task 3.3: All nox sessions pass (format, lint, type_check, test-3.14, test-integration)
  - [x] Task 3.4: Documentation updated
  - [x] Task 3.5: Feature file moved to completed

## Root Cause (Final)

The bug was in `frontend/src/components/SSEDebugger.tsx` line 44:

```tsx
const data = await response.json();
setStats(data);  // BUG: data is { success: true, data: {...} }
```

The API returns a wrapper object `{ success: true, data: {...}, message: "..." }` but the
component was setting `stats` to the entire response instead of extracting `data.data`.
This caused `stats.total_connections` etc. to be undefined since the actual stats were
nested one level deeper.

**Fix:** Changed to `setStats(data.data)` to properly extract the stats object.
