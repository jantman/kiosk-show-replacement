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
