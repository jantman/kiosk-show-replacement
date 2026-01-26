# Frontend Test Fixes

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

7 frontend tests are failing in `History.test.tsx` and `SlideshowItemForm.test.tsx`. These are pre-existing test failures discovered during the Docker fix feature verification.

## Failing Tests

### History.test.tsx (3 failures)

1. **displays placeholder when no history exists**
   - Error: Expected `handleSSEReconnection` to have been called
   - The test expects SSE reconnection to be triggered but it's not being called

2. **renders history entries correctly**
   - Error: Expected `handleSSEReconnection` to have been called
   - Same SSE reconnection issue

3. **formats dates correctly**
   - Error: Expected `handleSSEReconnection` to have been called
   - Same SSE reconnection issue

### SlideshowItemForm.test.tsx (4 failures)

1. **calls onSubmit with new text item data**
   - Error: `expect(mockApiCall).toHaveBeenCalledWith(...)` assertion fails
   - The API call is not being made with the expected parameters
   - Form data key mismatch: expected `textContent` but receiving `text_content`

2. **calls onSubmit with image item data**
   - Similar form submission issue

3. **calls onSubmit with video item data**
   - Similar form submission issue

4. **updates existing text item**
   - Similar form submission issue

## Root Cause Analysis

**History.test.tsx**: The tests mock `useSSE` but expect `handleSSEReconnection` to be called. The SSE context may have been refactored and the tests weren't updated.

**SlideshowItemForm.test.tsx**: There's a mismatch between the form field names used in the component (snake_case: `text_content`) and what the tests expect (camelCase: `textContent`). This could be due to API contract changes.

## Implementation Plan

### Milestone 1 (FTF-M1): Fix History.test.tsx

**FTF-M1.1: Investigate SSE reconnection expectations**
- Review how `handleSSEReconnection` is used in the History component
- Determine if the mock setup is correct or if the component behavior changed

**FTF-M1.2: Update tests**
- Fix the mock setup or test expectations to match current behavior

### Milestone 2 (FTF-M2): Fix SlideshowItemForm.test.tsx

**FTF-M2.1: Investigate form field naming**
- Determine the correct field names used in the API
- Check if component uses snake_case or camelCase

**FTF-M2.2: Update tests**
- Align test expectations with actual component behavior

### Milestone 3 (FTF-M3): Acceptance Criteria

**FTF-M3.1: Test verification**
- All frontend tests pass: `npm run test:run`

**FTF-M3.2: Complete feature**
- Move this feature file to `docs/features/completed/`
