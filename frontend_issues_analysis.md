# Frontend API Issues Analysis

## Overview
This document identifies discrepancies between the React frontend implementation and the documented Flask backend API based on the comprehensive analysis conducted.

## Critical Issues Found

### 1. Logout Endpoint Mismatch
**Issue**: Frontend uses incorrect logout endpoint
- **Frontend**: `/auth/logout` (POST)
- **Backend**: `/api/v1/auth/logout` (POST)
- **Files**: 
  - `frontend/src/utils/apiClient.ts` line 89
  - `frontend/src/hooks/useApi.ts` line 99
- **Impact**: Logout functionality fails

### 2. Reorder Item Parameter Mismatch
**Issue**: Frontend sends wrong parameter name for reordering slideshow items
- **Frontend**: `{ order: newOrder }` (SlideshowDetail.tsx line 95)
- **Backend**: Expects `{ order_index: newOrder }` (per documentation)
- **Files**: 
  - `frontend/src/pages/SlideshowDetail.tsx` line 95
  - `frontend/src/utils/apiClient.ts` line 161 (correctly uses `order_index`)
- **Impact**: Reordering functionality fails

### 3. Display Assignment Using ID Instead of Name
**Issue**: Frontend uses display ID for assignment instead of display name
- **Frontend**: `/api/v1/displays/${displayId}` (PUT with slideshow_id)
- **Backend**: Expects `/api/v1/displays/{display_name}/assign-slideshow` (POST)
- **Files**: 
  - `frontend/src/pages/Displays.tsx` lines 98, 148
  - `frontend/src/utils/apiClient.ts` line 186 (correctly uses display name)
- **Impact**: Display assignment may not work correctly

### 4. Slideshow Item Field Name Inconsistencies
**Issue**: Frontend uses `order` field while backend uses `order_index`
- **Frontend**: Displays `item.order` in SlideshowDetail.tsx
- **Backend**: API returns `order_index` field
- **Files**: 
  - `frontend/src/pages/SlideshowDetail.tsx` line 317
  - Type definitions in `frontend/src/types/index.ts`
- **Impact**: Ordering display shows undefined/incorrect values

### 5. Assignment History Data Model Discrepancies
**Issue**: Frontend expects different field names than backend provides
- **Frontend**: Uses `display_id`, `previous_slideshow_id`, `new_slideshow_id`
- **Backend**: May use different field names in actual responses
- **Files**: 
  - `frontend/src/pages/AssignmentHistory.tsx`
  - `frontend/src/utils/apiClient.ts` lines 224-231
- **Impact**: Assignment history may not display correctly

## Minor Issues

### 6. Missing Error Handling for Specific Status Codes
**Issue**: Frontend doesn't handle specific HTTP status codes mentioned in API docs
- **Missing**: 409 (Conflict), 422 (Validation Error) specific handling
- **Files**: Throughout frontend components
- **Impact**: Generic error messages instead of specific feedback

### 7. File Upload Size Validation
**Issue**: Frontend doesn't validate file sizes before upload
- **Backend**: Has 10MB limit for images, 100MB for videos
- **Frontend**: No client-side validation
- **Files**: File upload components
- **Impact**: Poor user experience with large file uploads

### 8. Missing Query Parameters
**Issue**: Some API calls don't use available query parameters
- **Missing**: Pagination parameters (limit, offset)
- **Missing**: Filtering parameters for assignment history
- **Files**: Various list components
- **Impact**: Performance issues with large datasets

## Type Definition Issues

### 9. Slideshow Type Definition Inconsistencies
**Issue**: Frontend types don't match backend data model
- **Frontend**: `Slideshow.item_count` field
- **Backend**: May not provide this field in all responses
- **Files**: `frontend/src/types/index.ts`
- **Impact**: TypeScript errors or undefined values

### 10. Display Type Definition Inconsistencies
**Issue**: Frontend types include fields not in backend model
- **Frontend**: `Display.assigned_slideshow` field
- **Backend**: Doesn't provide nested slideshow object
- **Files**: `frontend/src/types/index.ts`
- **Impact**: Potential runtime errors

## Authentication Issues

### 11. Session Management
**Issue**: Frontend doesn't handle session expiration gracefully
- **Current**: Basic error handling
- **Expected**: Automatic logout on 401 responses
- **Files**: API client and auth context
- **Impact**: Poor user experience on session timeout

## Recommendations

### High Priority Fixes
1. **Fix logout endpoint**: Change from `/auth/logout` to `/api/v1/auth/logout`
2. **Fix reorder parameter**: Use `order_index` instead of `order` in reorder calls
3. **Fix display assignment**: Use correct API endpoint with display name
4. **Fix field name consistency**: Ensure frontend displays `order_index` correctly

### Medium Priority Fixes
1. **Add client-side file validation**: Implement size limits before upload
2. **Improve error handling**: Add specific status code handling
3. **Add pagination**: Implement proper pagination for list views
4. **Fix type definitions**: Align frontend types with actual backend responses

### Low Priority Fixes
1. **Add session management**: Implement automatic logout on auth errors
2. **Add loading states**: Improve user feedback during operations
3. **Add retry logic**: Implement automatic retry for transient failures

## Testing Recommendations

1. **Integration Testing**: Test all API endpoints against actual backend
2. **Error Scenario Testing**: Test network failures, timeouts, and error responses
3. **File Upload Testing**: Test various file sizes and types
4. **Authentication Testing**: Test session expiration and renewal

## Files Requiring Changes

### Critical Changes
- `frontend/src/utils/apiClient.ts` (logout endpoint)
- `frontend/src/hooks/useApi.ts` (logout endpoint)
- `frontend/src/pages/SlideshowDetail.tsx` (reorder parameter, field display)
- `frontend/src/pages/Displays.tsx` (assignment endpoint)

### Type Definition Changes
- `frontend/src/types/index.ts` (align with backend model)

### Minor Changes
- Various components for improved error handling
- File upload components for size validation
- List components for pagination

This analysis provides a roadmap for fixing the frontend-backend integration issues to ensure the application functions correctly.
