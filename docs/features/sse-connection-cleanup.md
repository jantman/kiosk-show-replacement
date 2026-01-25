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
- `frontend/src/contexts/SSEContext.tsx` - Frontend SSE connection management (likely)

## Acceptance Criteria

- [ ] SSE connections are removed when clients disconnect
- [ ] Page refresh does not leave orphaned connections
- [ ] Browser tab close properly cleans up connections
- [ ] Navigation away from admin pages properly cleans up connections
- [ ] SSE Connection Monitor accurately reflects actual connected clients
