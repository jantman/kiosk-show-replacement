# Fix Frontend ESLint Errors

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The update to eslint-plugin-react-hooks v7 introduced stricter linting rules that caught pre-existing code quality issues in the frontend. These 12 errors need to be fixed to restore the `nox -s test-frontend` session to passing status.

## Background

During the dependency update (see `docs/features/completed/update-all-deps.md`), eslint-plugin-react-hooks was updated from v5 to v7. The new version includes stricter rules that flag issues that were previously undetected.

## Errors to Fix

### 1. `react-hooks/immutability` - Variables accessed before declaration

Functions are called inside useEffect before they are declared, preventing the earlier access from updating when the value changes.

**Affected files:**
- `src/components/LiveDataIndicator.tsx:40` - `handleUpdate` accessed before declaration
- `src/components/LiveNotifications.tsx:45` - `addNotification` accessed before declaration
- `src/contexts/ErrorContext.tsx:79` - `removeError` accessed before declaration

**Fix:** Move function declarations before the useEffect that uses them, or use useCallback and include in the dependency array.

### 2. `react-hooks/set-state-in-effect` - setState called directly in effects

Calling setState synchronously within an effect body causes cascading renders.

**Affected files:**
- `src/contexts/AuthContext.tsx:63` - `setUser` in effect
- `src/contexts/SSEContext.tsx:117` - `setConnectionState` in effect
- `src/hooks/useSSE.tsx:470` - `setShowReconnected` in effect
- `src/pages/SystemMonitoring.tsx:14` - `setLoading` in effect

**Fix:** Restructure to avoid synchronous setState in effects, or use the callback pattern for subscriptions.

### 3. `no-undef` - Undefined variables

**Affected files:**
- `src/App.tsx:25` - `process` is not defined
- `src/components/SSEDebugger.tsx:75` - `NodeJS` is not defined
- `src/test/ErrorBoundary.test.tsx:6` - `React` is not defined
- `src/test/ErrorContext.test.tsx:6,40` - `React` is not defined

**Fix:** Add proper imports or type declarations for these globals.

### 4. `no-case-declarations` - Lexical declarations in case blocks

**Affected files:**
- `src/components/EnhancedDisplayStatus.tsx:73` - Unexpected lexical declaration in case block

**Fix:** Wrap the case block contents in braces `{ }` to create a proper block scope.

### 5. `react-hooks/exhaustive-deps` - Missing dependencies (warning)

**Affected files:**
- `src/components/EnhancedDisplayStatus.tsx:91` - Missing dependency `fetchDisplayStatuses`

**Fix:** Add the missing dependency to the array or wrap in useCallback.

## Acceptance Criteria

- [ ] All 12 ESLint errors are resolved
- [ ] `npm run lint` passes with no errors in the frontend directory
- [ ] `nox -s test-frontend` passes completely
- [ ] All 101 frontend tests continue to pass
- [ ] Frontend build (`npm run build`) succeeds

---

## Implementation Plan

### Verified Errors (from `npm run lint`)

The actual errors found differ slightly from the original document:

**Errors (12):**
1. `App.tsx:25` - `process` is not defined
2. `EnhancedDisplayStatus.tsx:73` - Unexpected lexical declaration in case block
3. `LiveDataIndicator.tsx:40` - `handleUpdate` accessed before declaration
4. `LiveNotifications.tsx:45` - `addNotification` accessed before declaration
5. `SSEDebugger.tsx:75` - `NodeJS` is not defined
6. `ErrorContext.tsx:79` - `removeError` accessed before declaration
7. `useSSE.tsx:184` - `connect` accessed before declaration (not in original doc)
8. `useSSE.tsx:470` - `setShowReconnected` called in effect
9. `SystemMonitoring.tsx:14` - `setLoading` called in effect
10. `ErrorBoundary.test.tsx:6` - `React` is not defined
11. `ErrorContext.test.tsx:6` - `React` is not defined
12. `ErrorContext.test.tsx:40` - `React` is not defined

**Note:** The original document mentioned `AuthContext.tsx:63` and `SSEContext.tsx:117` which don't have errors in the current codebase. The SSE context code is in `useSSE.tsx`, not a separate `SSEContext.tsx` file.

### Milestone 1: Fix `react-hooks/immutability` Errors (4 files)

These errors occur when functions are called inside useEffect before they are declared. The fix is to convert the functions to `useCallback` hooks and move them before the useEffect that uses them, then add them to the dependency array.

**Tasks:**

1.1. `LiveDataIndicator.tsx` - Convert `handleUpdate` to `useCallback` and move before useEffect
1.2. `LiveNotifications.tsx` - Convert `addNotification` to `useCallback` and move before useEffect
1.3. `ErrorContext.tsx` - Move `removeError` declaration before `addError` (since `addError` calls it)
1.4. `useSSE.tsx` - Restructure the `connect` function to avoid accessing it before declaration

### Milestone 2: Fix `react-hooks/set-state-in-effect` Errors (2 files)

These errors occur when `setState` is called synchronously in an effect body. The fix depends on the use case.

**Tasks:**

2.1. `SystemMonitoring.tsx` - Remove unnecessary useEffect (loading can default to `false` since there's no async initialization)
2.2. `useSSE.tsx:470` (`OfflineBanner`) - Restructure to derive `showReconnected` state from `isOnline` and `wasOffline` instead of using a separate state variable

### Milestone 3: Fix `no-undef` Errors (4 files)

These errors are caused by missing imports or global type declarations.

**Tasks:**

3.1. `App.tsx` - Use `import.meta.env.MODE` instead of `process.env.NODE_ENV` (Vite standard)
3.2. `SSEDebugger.tsx` - Use `ReturnType<typeof setTimeout>` instead of `NodeJS.Timeout`
3.3. `ErrorBoundary.test.tsx` - Add `import React from 'react'`
3.4. `ErrorContext.test.tsx` - Add `import React from 'react'`

### Milestone 4: Fix `no-case-declarations` Error (1 file)

**Tasks:**

4.1. `EnhancedDisplayStatus.tsx` - Wrap case block contents in braces `{ }` to create proper block scope

### Milestone 5: Acceptance Criteria

5.1. Verify `npm run lint` passes with no errors
5.2. Verify `npm run test:run` passes (all 101 tests)
5.3. Verify `npm run build` succeeds
5.4. Run `nox -s test-frontend` to verify the full test session passes
5.5. Update this document with completion status
5.6. Move this document to `docs/features/completed/`
