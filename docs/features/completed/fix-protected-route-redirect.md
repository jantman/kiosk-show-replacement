# Fix ProtectedRoute Login Redirect Path

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The `ProtectedRoute` component in the React frontend redirects unauthenticated users to `/login` instead of `/admin/login`, causing a 404 error.

## Problem

When an unauthenticated user attempts to access a protected route:
1. User navigates to `/` or `/admin`
2. `ProtectedRoute` component checks authentication status
3. User is not authenticated
4. Component redirects to `/login` (INCORRECT)
5. `/login` is not a defined route in App.tsx
6. User sees 404 "Page not found" error

## Root Cause

In `frontend/src/components/ProtectedRoute.tsx` line 26:
```jsx
return <Navigate to="/login" replace />;
```

The correct route is `/admin/login` as defined in `frontend/src/App.tsx` line 33:
```jsx
<Route path="/admin/login" element={<Login />} />
```

## Solution

Change the redirect path in `ProtectedRoute.tsx` from `/login` to `/admin/login`:

```jsx
// Before
return <Navigate to="/login" replace />;

// After
return <Navigate to="/admin/login" replace />;
```

## Acceptance Criteria

1. Fix the redirect path in `ProtectedRoute.tsx`
2. Verify unauthenticated users are redirected to the login page
3. Remove the `pytest.skip` decorator from `test_user_can_login_and_see_dashboard` in `tests/integration/test_full_user_experience.py`
4. Run integration tests and verify the test passes
5. All existing tests must continue to pass

## Discovered During

This bug was discovered during implementation of the admin-integration-tests feature (AIT-1.4) when the `test_user_can_login_and_see_dashboard` test failed with a 404 error.

## Impact

- **Severity**: High - Breaks normal user login flow
- **User Impact**: Users navigating to the root URL cannot log in
- **Workaround**: Users can directly navigate to `/admin/login`

## Implementation Plan

Given the simplicity of this fix (single line change + test enablement), this will be completed as a single milestone.

### Milestone 1: Fix and Verify (PRR-1) - COMPLETED

| Task | Description | Status |
|------|-------------|--------|
| PRR-1.1 | Fix redirect path in `frontend/src/components/ProtectedRoute.tsx` line 26 | Complete |
| PRR-1.2 | Remove `pytest.skip` decorator from `test_user_can_login_and_see_dashboard` | Complete |
| PRR-1.3 | Rebuild frontend with `npm run build` | Complete |
| PRR-1.4 | Run integration tests to verify the fix works | Complete |
| PRR-1.5 | Run all nox tests to ensure no regressions | Complete |
| PRR-1.6 | Move feature document to `docs/features/completed/` | Complete |
