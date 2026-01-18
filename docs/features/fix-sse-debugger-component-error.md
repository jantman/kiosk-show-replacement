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

## Implementation Plan

### Investigation Results

Analysis of `frontend/src/components/SSEDebugger.tsx` found the root cause at line 205:

```typescript
{stats.connections.length > 0 ? (
```

The `stats` object is typed as `SSEStats | null` and is checked for nullness on line 175 (`{stats && (...`), but `stats.connections` could be `undefined` if the API response doesn't include it. When `stats.connections` is undefined, calling `.length` throws the TypeError.

### Solution

Add optional chaining to safely access the `connections` array length. Change line 205 from:

```typescript
{stats.connections.length > 0 ? (
```

to:

```typescript
{(stats.connections?.length ?? 0) > 0 ? (
```

This ensures that if `stats.connections` is undefined, the expression evaluates to `0 > 0` (false), displaying the "No active SSE connections found" alert instead of crashing.

### Milestones

**Milestone 1: Fix and Verify (M1)**
- Task 1.1: Fix the SSEDebugger component
- Task 1.2: Run integration tests to verify the fix
- Task 1.3: Run all nox tests to ensure no regressions

**Milestone 2: Acceptance Criteria (M2)**
- Task 2.1: Verify all acceptance criteria are met
- Task 2.2: Move feature file to completed directory

## Acceptance Criteria

1. System Monitoring page loads without errors
2. SSE Debug Tools tab displays properly
3. Display Status tab displays properly
4. System Health tab displays properly
5. Integration tests pass:
   - `test_sse_debug_tools_tab_loads`
   - `test_display_status_tab_loads`
   - `test_system_health_tab_shows_status`
