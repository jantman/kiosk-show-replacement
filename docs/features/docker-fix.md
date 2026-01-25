# Docker Fix

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The Docker image currently fails to build. We need to fix that, and then verify that both docker-compose files (`docker-compose.yml`) and (`docker-compose.prod.yml`) function correctly (i.e. that if we run each of these via docker compose, the application runs and we can log in to the admin UI and make some changes, which get persisted to the database).

## Root Cause Analysis

The Docker build fails at Step 6/26 during the frontend build stage with TypeScript compilation errors:

```
src/test/sanitizeHtml.test.ts(66,13): error TS6133: 'result' is declared but its value is never read.
src/test/sanitizeHtml.test.ts(82,13): error TS6133: 'text' is declared but its value is never read.
```

Two test cases in `frontend/src/test/sanitizeHtml.test.ts` have incomplete implementations with declared but unused variables.

## Implementation Plan

### Milestone 1 (DFX-M1): Fix Docker Build

**DFX-M1.1: Fix TypeScript errors in test file**
- Remove the unused variables from the incomplete test cases in `frontend/src/test/sanitizeHtml.test.ts`
- The tests at lines 64-70 and 81-87 have variables declared but never used, with comments indicating the test author realized the scenario wasn't what they intended
- Either complete these tests with proper assertions or remove the unused variable declarations

**DFX-M1.2: Verify Docker build succeeds**
- Run `docker build -t kiosk-test .` and confirm it completes without errors

### Milestone 2 (DFX-M2): Verify Development Docker Compose

**DFX-M2.1: Start development environment**
- Create required directories: `mkdir -p .docker-data/dev/instance/uploads && sudo chown -R 1000:1000 .docker-data/dev`
- Run `docker-compose up` and verify the container starts successfully
- Confirm health check passes

**DFX-M2.2: Verify functionality**
- Access admin UI at http://localhost:5000/admin/
- Log in with default credentials (admin/admin)
- Create a test slideshow or make a change
- Verify the change persists after container restart

### Milestone 3 (DFX-M3): Verify Production Docker Compose

**DFX-M3.1: Start production environment**
- Create required directories: `mkdir -p .docker-data/prod/uploads .docker-data/prod/mariadb && sudo chown -R 1000:1000 .docker-data/prod/uploads`
- Create `.env` file with required environment variables (SECRET_KEY, MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD, KIOSK_ADMIN_PASSWORD)
- Run `docker-compose -f docker-compose.prod.yml up` and verify both app and db containers start
- Confirm health checks pass for both services

**DFX-M3.2: Verify functionality**
- Access admin UI at http://localhost:5000/admin/
- Log in with configured admin credentials
- Create a test slideshow or make a change
- Verify the change persists after container restart

### Milestone 4 (DFX-M4): Acceptance Criteria

**DFX-M4.1: Documentation**
- Review and update Docker-related documentation if any changes are needed

**DFX-M4.2: Test verification**
- Run all nox sessions and verify all tests pass
- Frontend tests must pass (npm run test:run)

**DFX-M4.3: Complete feature**
- Move this feature file to `docs/features/completed/`
