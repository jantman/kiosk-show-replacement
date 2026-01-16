# Feature: Error Handling & Resilience

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This feature adds comprehensive error handling and system resilience throughout the application. The goal is to ensure the system handles failures gracefully, provides meaningful feedback to users, and recovers automatically from transient issues. This is critical for production readiness, especially for kiosk displays that may run unattended for extended periods.

## High-Level Deliverables

### Backend Error Handling

- Standardized error response format across all API endpoints with consistent structure and error codes
- Comprehensive exception handling that catches and logs all errors appropriately
- Proper HTTP status codes for all error conditions (400, 401, 403, 404, 500, etc.)
- Structured logging with correlation IDs to trace requests across the system
- Error reporting hooks for integration with external monitoring systems

### Frontend Error Handling

- React error boundaries to isolate component failures and prevent full application crashes
- Global error handling for API requests with user-friendly error messages
- Graceful degradation when backend services are unavailable
- Retry mechanisms for transient failures
- For kiosk displays, automatic reload/refresh on connectivity loss or significant errors

### Display Resilience

- Automatic retry logic for failed content loading (images, videos, web pages)
- Fallback content when primary content is unavailable
- Automatic reconnection for lost SSE connections with exponential backoff
- Display health self-monitoring and recovery
- Graceful handling of network interruptions without crashing

### Database & File System Resilience

- Database connection retry logic for transient failures
- File system error handling for upload/storage operations
- Data integrity validation and corruption detection
- Graceful handling of disk space issues

### Monitoring & Health Checks

- Health check endpoints for all critical services (`/health`, `/health/db`, `/health/storage`)
- Structured logging suitable for log aggregation systems
- Performance metrics collection hooks (Prometheus endpoint)
- Prometheus metrics for critical failures

## Acceptance Criteria

The final milestone must verify:

1. All documentation updated for error handling patterns and monitoring endpoints
2. Unit test coverage for all error handling scenarios
3. Integration tests verify graceful degradation under failure conditions
4. All nox sessions pass successfully
5. Feature file moved to `docs/features/completed/`

---

## Implementation Plan

### Current Architecture Analysis

Based on exploration of the codebase, the following patterns and gaps were identified:

**Existing Patterns:**
- Basic try-catch blocks with generic exception handling in API endpoints
- Database rollback on failure in some endpoints
- Logging via `current_app.logger`
- `api_response()` and `api_error()` helpers for JSON responses
- SSE with basic reconnection support in frontend
- Storage validation for file uploads

**Key Gaps:**
- No custom exception hierarchy for error classification
- No correlation IDs for request tracing
- Inconsistent error response format across endpoints
- No React error boundaries
- No retry logic in API client
- Limited health check endpoints (only `/api/v1/status`)
- No Prometheus metrics
- No database connection retry logic
- No frontend graceful degradation patterns

---

### Milestone 1: Backend Error Handling Foundation

**Prefix:** `Error Handling - 1`

This milestone establishes the core error handling infrastructure on the backend.

#### Task 1.1: Create Custom Exception Hierarchy

Create `kiosk_show_replacement/exceptions.py` with:
- `AppException` - base exception with error code, message, HTTP status
- `ValidationError` - for request validation failures (400)
- `NotFoundError` - for resource not found (404)
- `AuthenticationError` - for auth failures (401)
- `AuthorizationError` - for permission failures (403)
- `ConflictError` - for integrity/conflict errors (409)
- `StorageError` - for file system issues (500)
- `DatabaseError` - for database issues (500)
- `ExternalServiceError` - for third-party service failures (502/503)

#### Task 1.2: Create Standardized Error Response Format

Update `kiosk_show_replacement/api/helpers.py` with:
- Standardized error response structure:
  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Human-readable message",
      "details": {},
      "correlation_id": "uuid"
    }
  }
  ```
- Helper functions for each error type
- Flask error handlers for custom exceptions

#### Task 1.3: Add Correlation ID Middleware

Create request middleware that:
- Generates or accepts correlation ID from `X-Correlation-ID` header
- Attaches correlation ID to Flask's `g` object
- Includes correlation ID in all responses
- Logs correlation ID with all log messages

#### Task 1.4: Update API Endpoints

Refactor existing endpoints in `kiosk_show_replacement/api/v1.py` to:
- Raise custom exceptions instead of returning `api_error()` directly
- Use global error handlers to convert exceptions to responses
- Ensure consistent error format across all endpoints

**Milestone 1 Verification:**
- [ ] All unit tests pass
- [ ] New exception types have test coverage
- [ ] API responses follow standardized format
- [ ] Correlation IDs appear in logs and responses

---

### Milestone 2: Health Checks & Monitoring

**Prefix:** `Error Handling - 2`

This milestone adds health check endpoints and monitoring infrastructure.

#### Task 2.1: Add Comprehensive Health Check Endpoints

Create `kiosk_show_replacement/api/health.py` with:
- `GET /health` - overall health status (returns 200 if healthy, 503 if unhealthy)
- `GET /health/db` - database connectivity check
- `GET /health/storage` - storage availability and disk space check
- `GET /health/ready` - readiness probe for Kubernetes/container orchestration
- `GET /health/live` - liveness probe

Response format:
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO8601",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 5},
    "storage": {"status": "healthy", "free_space_mb": 1024}
  }
}
```

#### Task 2.2: Add Prometheus Metrics Endpoint

Create `kiosk_show_replacement/metrics.py` with:
- `GET /metrics` - Prometheus-compatible metrics endpoint
- Metrics to collect:
  - `http_requests_total` - request count by endpoint and status
  - `http_request_duration_seconds` - request latency histogram
  - `active_sse_connections` - current SSE connection count
  - `database_errors_total` - database error count
  - `storage_errors_total` - storage error count
  - `display_heartbeat_age_seconds` - age of last display heartbeat

#### Task 2.3: Enhance Structured Logging

Update logging configuration to:
- Use JSON format for production logs
- Include correlation ID in all log entries
- Add log levels for error classification
- Create request/response logging middleware

**Milestone 2 Verification:**
- [ ] Health endpoints return appropriate status codes
- [ ] `/metrics` returns valid Prometheus format
- [ ] Logs include correlation IDs
- [ ] All unit tests pass

---

### Milestone 3: Database & Storage Resilience

**Prefix:** `Error Handling - 3`

This milestone improves database and file system error handling.

#### Task 3.1: Add Database Connection Retry Logic

Create `kiosk_show_replacement/db_utils.py` with:
- Connection retry decorator with exponential backoff
- Configurable retry count and delay
- Specific handling for transient database errors (connection lost, deadlock)
- Circuit breaker pattern for persistent failures

#### Task 3.2: Improve Storage Error Handling

Update `kiosk_show_replacement/storage.py` to:
- Raise `StorageError` exceptions instead of returning tuples
- Add disk space checking before uploads
- Implement atomic file writes (write to temp, then rename)
- Add cleanup on partial failures
- Add file integrity validation (checksum verification)

#### Task 3.3: Add Data Integrity Validation

Add validation utilities for:
- File upload integrity (size, checksum)
- Database constraint validation before operations
- Orphaned file detection and cleanup
- Storage consistency checks

**Milestone 3 Verification:**
- [ ] Database operations retry on transient failures
- [ ] Storage operations use exception-based error handling
- [ ] Integrity checks detect corruption
- [ ] All unit tests pass

---

### Milestone 4: Frontend Error Handling

**Prefix:** `Error Handling - 4`

This milestone adds comprehensive error handling to the React frontend.

#### Task 4.1: Create React Error Boundaries

Create `frontend/src/components/ErrorBoundary.tsx`:
- Generic `ErrorBoundary` component for catching React errors
- `ApiErrorBoundary` for API-related failures
- Fallback UI components for error states
- Error reporting to console/monitoring

#### Task 4.2: Enhance API Client with Retry Logic

Update `frontend/src/utils/apiClient.ts`:
- Add retry logic with exponential backoff for transient failures
- Classify retryable vs non-retryable errors
- Add request timeout configuration
- Add correlation ID header support
- Add circuit breaker for persistent failures

#### Task 4.3: Add Global Error Handling

Create `frontend/src/contexts/ErrorContext.tsx`:
- Global error state management
- Toast/notification system for user-friendly error messages
- Error categorization (network, auth, validation, server)
- Automatic error clearing after timeout

#### Task 4.4: Add Graceful Degradation Patterns

Update components to handle:
- Offline state detection and UI feedback
- Stale data display when server unavailable
- Loading states for slow responses
- Partial failure handling (some data loads, some fails)

**Milestone 4 Verification:**
- [ ] Error boundaries prevent full app crashes
- [ ] API errors trigger user-friendly notifications
- [ ] Retry logic works for transient failures
- [ ] Frontend tests pass
- [ ] All nox sessions pass

---

### Milestone 5: SSE & Display Resilience

**Prefix:** `Error Handling - 5`

This milestone improves real-time communication and display reliability.

#### Task 5.1: Enhance SSE Error Handling

Update `kiosk_show_replacement/sse.py`:
- Add error event broadcasting to clients
- Add connection health monitoring
- Add metrics for SSE connections
- Improve reconnection logging

Update `frontend/src/hooks/useSSE.tsx`:
- Improve reconnection with jitter
- Add connection state to UI
- Handle specific error types differently

#### Task 5.2: Add Display Health Monitoring

Create display self-monitoring:
- Content load failure detection
- Network connectivity monitoring
- Automatic page reload on critical errors
- Heartbeat improvements for failure detection

#### Task 5.3: Add Fallback Content Support

Implement fallback mechanisms:
- Default content when slideshow unavailable
- Cached content for offline display
- Error message display for extended outages
- Graceful degradation for individual slide failures

**Milestone 5 Verification:**
- [ ] SSE reconnects reliably after failures
- [ ] Displays recover from content load failures
- [ ] Fallback content appears when primary unavailable
- [ ] All unit tests pass

---

### Milestone 6: Acceptance Criteria

**Prefix:** `Error Handling - 6`

Final milestone to complete the feature.

#### Task 6.1: Update Documentation

- Update `README.md` with health check and monitoring endpoints
- Update `CLAUDE.md` with error handling patterns
- Create `docs/error-handling.md` with detailed error handling guide
- Document Prometheus metrics available

#### Task 6.2: Ensure Test Coverage

- Add unit tests for all exception classes
- Add unit tests for health check endpoints
- Add unit tests for retry logic
- Add integration tests for graceful degradation
- Verify coverage meets standards

#### Task 6.3: Verify All Nox Sessions Pass

Run and verify:
- `nox -s format`
- `nox -s lint`
- `nox -s test`
- `nox -s type_check`
- `nox -s test-integration`
- `nox -s test-e2e`

#### Task 6.4: Complete Feature

- Move feature file to `docs/features/completed/`
- Create final commit summarizing all changes

**Milestone 6 Verification:**
- [ ] All documentation updated
- [ ] All tests pass with adequate coverage
- [ ] All nox sessions pass
- [ ] Feature file moved to completed

---

## Progress Tracking

| Milestone | Status | Notes |
|-----------|--------|-------|
| Milestone 1: Backend Error Handling Foundation | Not Started | |
| Milestone 2: Health Checks & Monitoring | Not Started | |
| Milestone 3: Database & Storage Resilience | Not Started | |
| Milestone 4: Frontend Error Handling | Not Started | |
| Milestone 5: SSE & Display Resilience | Not Started | |
| Milestone 6: Acceptance Criteria | Not Started | |
