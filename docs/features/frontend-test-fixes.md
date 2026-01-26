# Frontend Test Fixes

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

7 frontend tests are failing in `Login.test.tsx` and `SlideshowItemForm.test.tsx`. These are pre-existing test failures discovered during the Docker fix feature verification.

## Failing Tests

### Login.test.tsx (4 failures)

1. **renders login form correctly**
   - Error: Test cannot find elements because component is stuck in loading state
   - The component now calls `apiClient.getHealthReady()` on mount and shows "Checking system status..." while waiting

2. **handles form submission with valid data**
   - Same root cause - component stuck in system health check loading state

3. **displays validation errors for empty fields**
   - Same root cause - component stuck in system health check loading state

4. **shows loading state during authentication**
   - Error: Expected "checking authentication" but component shows "Checking system status..." because `isCheckingSystem` is true first

### SlideshowItemForm.test.tsx (3 failures)

1. **handles form submission for create**
   - Error: `expect(mockApiCall).toHaveBeenCalledWith(...)` assertion fails
   - Missing `scale_factor: null` in expected JSON body

2. **handles form submission for edit**
   - Same issue - missing `scale_factor: null` in expected JSON body

3. **handles text content submission**
   - Same issue - missing `scale_factor: null` in expected JSON body

## Root Cause Analysis

**Login.test.tsx**: The Login component was updated to check system health on mount using `apiClient.getHealthReady()`. The tests only mock `useAuth` but don't mock `apiClient`, so the component gets stuck in the "Checking system status..." loading state. The tests cannot find any form elements because the loading spinner is shown instead.

**SlideshowItemForm.test.tsx**: The component was updated to include `scale_factor` in the submit data:
```typescript
// Only include scale_factor for URL content type
scale_factor: formData.content_type === 'url' ? formData.scale_factor : null,
```
This field is always included (as `null` for non-URL types), but the tests weren't updated to expect this field.

## Implementation Plan

### Milestone 1 (FTF-M1): Fix Login.test.tsx

**FTF-M1.1: Mock apiClient for Login tests**
- Add a mock for `apiClient` that returns successful health check and login responses
- Ensure `getHealthReady()` returns `{ success: true, status: 'ready' }` to allow the component to render the login form
- Ensure `login()` returns appropriate response for form submission tests

**FTF-M1.2: Update loading state test**
- The "shows loading state during authentication" test needs to check for the correct loading message
- The component shows "Checking system status..." when `isCheckingSystem` is true
- The component shows "Checking authentication..." when `isLoading` is true (and `isCheckingSystem` is false)

### Milestone 2 (FTF-M2): Fix SlideshowItemForm.test.tsx

**FTF-M2.1: Update test expectations to include scale_factor**
- Add `scale_factor: null` to the expected JSON body in all failing tests:
  - `handles form submission for create`
  - `handles form submission for edit`
  - `handles text content submission`

### Milestone 3 (FTF-M3): Acceptance Criteria

**FTF-M3.1: Test verification**
- All frontend tests pass: `npm run test:run`
- All nox sessions pass

**FTF-M3.2: Complete feature**
- Move this feature file to `docs/features/completed/`
