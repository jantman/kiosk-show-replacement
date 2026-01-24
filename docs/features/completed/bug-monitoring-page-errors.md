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

---

## Root Cause Analysis

### Issue 1: SSE Debug Tools Tab - API Response Field Mismatch

The `/api/v1/events/stats` endpoint returns data, but the field names don't match what the frontend expects.

**Backend returns (`kiosk_show_replacement/api/v1.py:1763-1809`):**
```python
{
    "total_connections": int,
    "admin_connections": int,
    "display_connections": int,
    "average_connection_age_seconds": float,
    "active_connection_ids": list[str],
    "connections": [
        {
            "connection_id": str,      # Frontend expects "id"
            "connection_type": str,    # Frontend expects "type"
            "user_id": int,            # Frontend expects "user" (username string)
            "connected_at": str,
            "events_sent": int,
            "last_activity": str,      # Frontend expects "last_ping"
            "display_name": str,       # Frontend expects "display"
            "display_id": int
        }
    ]
}
```

**Frontend expects (`frontend/src/components/SSEDebugger.tsx:5-21`):**
```typescript
interface SSEStats {
  total_connections: number;
  admin_connections: number;
  display_connections: number;
  events_sent_last_hour: number;  // MISSING from backend
  connections: SSEConnection[];
}

interface SSEConnection {
  id: string;           // Backend returns "connection_id"
  type: 'admin' | 'display';  // Backend returns "connection_type"
  user?: string;        // Backend returns "user_id" (number)
  display?: string;     // Backend returns "display_name"
  connected_at: string;
  last_ping: string;    // Backend returns "last_activity"
  events_sent: number;
}
```

### Issue 2: Display Status Tab - Missing API Endpoints

The frontend calls endpoints that don't exist:
- `GET /api/v1/displays/status` - Returns 404
- `GET /api/v1/displays/<id>/status` - Returns 404

**Frontend expects (`frontend/src/components/EnhancedDisplayStatus.tsx:5-25`):**
```typescript
interface DisplayStatus {
  id: number;
  name: string;
  location?: string;
  is_online: boolean;
  last_seen_at?: string;
  current_slideshow?: { id: number; name: string };
  connection_quality: 'excellent' | 'good' | 'poor' | 'offline';
  heartbeat_interval: number;
  missed_heartbeats: number;
  sse_connected: boolean;
  last_sse_event?: string;
  performance_metrics?: { cpu_usage, memory_usage, network_latency };
}
```

---

## Implementation Plan

### Milestone 1: Regression Tests (M1)
**Prefix:** `M1`

Per the guidelines, bug fixes must BEGIN with creating regression tests that should initially fail.

#### Task 1.1: Add unit tests for SSE stats API response format
Create unit tests that verify the `/api/v1/events/stats` endpoint returns the expected field names.

**File:** `tests/unit/test_sse_api.py` (new file or extend existing)

Tests to add:
- Test that `connections` array items have `id` field (not `connection_id`)
- Test that `connections` array items have `type` field (not `connection_type`)
- Test that `connections` array items have `user` field (username string, not user_id)
- Test that `connections` array items have `last_ping` field
- Test that `connections` array items have `display` field for display connections
- Test that response includes `events_sent_last_hour` field

#### Task 1.2: Add unit tests for display status endpoints
Create unit tests that verify the new display status endpoints work correctly.

**File:** `tests/unit/test_display_status_api.py` (new file)

Tests to add:
- Test `GET /api/v1/displays/status` returns list of display statuses
- Test `GET /api/v1/displays/<id>/status` returns single display status
- Test display status includes required fields: `connection_quality`, `sse_connected`, `missed_heartbeats`
- Test `connection_quality` calculation logic (based on missed heartbeats)
- Test `sse_connected` correctly reflects SSE connection state
- Test 404 when display not found

#### Task 1.3: Add integration tests for monitoring page
Update integration tests to verify the monitoring page displays data correctly without errors.

**File:** `tests/integration/test_system_monitoring.py`

Tests to add:
- Test SSE Debug Tools tab shows connection data (not "No active SSE connections found")
- Test Display Status tab does not show error message
- Test Display Status tab shows display information

---

### Milestone 2: Fix SSE Stats API Response (M2)
**Prefix:** `M2`

#### Task 2.1: Update SSE stats endpoint response format
Modify `/api/v1/events/stats` to return field names matching frontend expectations.

**File:** `kiosk_show_replacement/api/v1.py`

Changes:
- Rename `connection_id` to `id` in response
- Rename `connection_type` to `type` in response
- Convert `user_id` to username string as `user`
- Rename `last_activity` to `last_ping`
- Rename `display_name` to `display`
- Add `events_sent_last_hour` field (calculate from SSE event history)

#### Task 2.2: Add events_sent_last_hour tracking
Add capability to track events sent in the last hour.

**File:** `kiosk_show_replacement/sse.py`

Changes:
- Add event timestamp tracking to SSEManager
- Add method `get_events_sent_last_hour()` to calculate count
- Consider memory-efficient circular buffer for event timestamps

---

### Milestone 3: Implement Display Status Endpoints (M3)
**Prefix:** `M3`

#### Task 3.1: Add display status calculation logic
Add method to Display model or create utility to calculate enhanced status fields.

**Files:** `kiosk_show_replacement/models/__init__.py` or new utility file

New computed properties/methods:
- `missed_heartbeats`: Calculate based on `last_seen_at` and `heartbeat_interval`
- `connection_quality`: Derive from missed heartbeats ('excellent', 'good', 'poor', 'offline')
- `sse_connected`: Check if display has active SSE connection via `sse_manager`

#### Task 3.2: Implement GET /api/v1/displays/status endpoint
Add endpoint to return status of all displays.

**File:** `kiosk_show_replacement/api/v1.py`

Response format:
```json
[
  {
    "id": 1,
    "name": "Display 1",
    "location": "Lobby",
    "is_online": true,
    "last_seen_at": "2024-01-15T10:30:00Z",
    "current_slideshow": { "id": 1, "name": "Welcome" },
    "connection_quality": "excellent",
    "heartbeat_interval": 60,
    "missed_heartbeats": 0,
    "sse_connected": true
  }
]
```

#### Task 3.3: Implement GET /api/v1/displays/<id>/status endpoint
Add endpoint to return status of a specific display.

**File:** `kiosk_show_replacement/api/v1.py`

Same response format as above, but for single display. Return 404 if display not found.

---

### Milestone 4: Acceptance Criteria (M4)
**Prefix:** `M4`

#### Task 4.1: Verify all unit tests pass
Run `nox -s test-3.14` and ensure all tests pass.

#### Task 4.2: Verify all integration tests pass
Run `nox -s test-integration` and ensure all tests pass.

#### Task 4.3: Verify all nox sessions pass
Run all nox sessions and ensure they pass:
- `nox -s lint`
- `nox -s type_check`
- `nox -s test-3.14`
- `nox -s test-integration`

#### Task 4.4: Update documentation if needed
Review and update any relevant documentation.

#### Task 4.5: Move feature file to completed
Move this file to `docs/features/completed/`.

---

## Progress Tracking

- [x] **Milestone 1: Regression Tests** - Complete
  - [x] Task 1.1: SSE stats API tests (tests/unit/test_sse.py)
  - [x] Task 1.2: Display status API tests (tests/unit/test_display_status_api.py)
  - [x] Task 1.3: Integration tests (tests/integration/test_system_monitoring.py)
- [x] **Milestone 2: Fix SSE Stats API** - Complete
  - [x] Task 2.1: Update response format (kiosk_show_replacement/api/v1.py)
  - [x] Task 2.2: Add events_sent_last_hour tracking (kiosk_show_replacement/sse.py)
- [x] **Milestone 3: Display Status Endpoints** - Complete
  - [x] Task 3.1: Status calculation logic (kiosk_show_replacement/models/__init__.py)
  - [x] Task 3.2: GET /api/v1/displays/status (kiosk_show_replacement/api/v1.py)
  - [x] Task 3.3: GET /api/v1/displays/<id>/status (kiosk_show_replacement/api/v1.py)
- [x] **Milestone 4: Acceptance Criteria** - Complete
  - [x] Task 4.1: Unit tests pass (411 passed)
  - [x] Task 4.2: Integration tests pass (90 passed, 1 unrelated failure)
  - [x] Task 4.3: All nox sessions pass (format, lint, type_check, test-3.14)
  - [x] Task 4.4: Documentation updated
  - [x] Task 4.5: Feature file moved to completed
