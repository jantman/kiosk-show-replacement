# Fix SSEDebugger Component Runtime Error

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The System Monitoring page (`/admin/monitoring`) fails to load because the SSEDebugger component has a runtime error that is caught by the ErrorBoundary.

## Problem

Integration tests for the System Monitoring page fail because the SSEDebugger component throws a TypeError:

```
TypeError: Cannot read properties of undefined (reading 'length')
```

This error is caught by the ErrorBoundary component, which displays an error message instead of the System Monitoring page.

### Evidence from Test Logs

```
Browser console: ErrorBoundary caught an error: TypeError: Cannot read properties of undefined (reading 'length')
    at SSEDebugger (http://localhost:3001/src/components/SSEDebugger.tsx:...)
```

### Root Cause

The SSEDebugger component is trying to access the `.length` property on a value that is `undefined`. This likely happens when:

1. Some state variable is not initialized properly
2. An API response is undefined/null and the component tries to access `.length` on it
3. An array operation is performed before data is loaded

## Files Involved

### Frontend
- `frontend/src/components/SSEDebugger.tsx` - The component with the runtime error
- `frontend/src/pages/SystemMonitoring.tsx` - Parent page that renders SSEDebugger
- `frontend/src/components/ErrorBoundary.tsx` - Error boundary that catches the error

## Investigation Needed

1. Search for `.length` usage in SSEDebugger.tsx
2. Check all array operations and ensure they handle undefined/null cases
3. Verify state initialization for any arrays used in the component
4. Check if useSSE hook returns values that could be undefined

## Proposed Solution

Add null/undefined checks before accessing `.length`:

```typescript
// Instead of:
someArray.length

// Use:
someArray?.length ?? 0
// or
(someArray || []).length
```

Alternatively, ensure all state variables are initialized with default values:

```typescript
const [events, setEvents] = useState<Event[]>([]); // Not useState<Event[]>()
```

## Acceptance Criteria

1. System Monitoring page loads without errors
2. SSE Debug Tools tab displays properly
3. Display Status tab displays properly
4. System Health tab displays properly
5. Integration tests pass:
   - `test_sse_debug_tools_tab_loads`
   - `test_display_status_tab_loads`
   - `test_system_health_tab_shows_status`
