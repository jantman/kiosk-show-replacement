# Docker Fix

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The Docker image currently fails to build. We need to fix that, and then verify that both docker-compose files (`docker-compose.yml`) and (`docker-compose.prod.yml`) function correctly (i.e. that if we run each of these via docker compose, the application runs and we can log in to the admin UI and make some changes, which get persisted to the database).

## Root Cause Analysis

**Issue 1: TypeScript compilation errors**

The Docker build initially failed at Step 6/26 during the frontend build stage with TypeScript compilation errors:

```
src/test/sanitizeHtml.test.ts(66,13): error TS6133: 'result' is declared but its value is never read.
src/test/sanitizeHtml.test.ts(82,13): error TS6133: 'text' is declared but its value is never read.
```

Two test cases in `frontend/src/test/sanitizeHtml.test.ts` had incomplete implementations with declared but unused variables.

**Issue 2: Poetry dependency compatibility with Python 3.14**

After fixing Issue 1, the build failed at the Poetry installation step because Poetry 2.2.1's transitive dependency `pbs-installer` requires `zstandard>=0.21.0`, and `zstandard` doesn't have wheels available for Python 3.14 yet.

**Solution**: Use a multi-stage build where Poetry runs in a Python 3.12 stage (which has full wheel support) to export `requirements.txt`, then install those dependencies directly with pip in the Python 3.14 runtime stage.

## Implementation Plan

### Milestone 1 (DFX-M1): Fix Docker Build ✅ COMPLETE

**DFX-M1.1: Fix TypeScript errors in test file** ✅
- Completed the incomplete test cases in `frontend/src/test/sanitizeHtml.test.ts` with proper assertions
- The 'escapes HTML entities' test now verifies script tag stripping
- The 'escapes special characters in plain text' test now verifies content preservation

**DFX-M1.2: Fix Poetry/Python 3.14 compatibility** ✅
- Modified `Dockerfile` to use a multi-stage build approach
- Added a new `deps-export` stage using Python 3.12 to run Poetry and export requirements.txt
- The runtime stage copies requirements.txt from deps-export and installs with pip directly

**DFX-M1.3: Verify Docker build succeeds** ✅
- Docker build completes successfully with all 30 steps
- Image tagged as `kiosk-test:latest`

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
