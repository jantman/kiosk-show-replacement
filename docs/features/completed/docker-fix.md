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

**Issue 3: password_hash column too small for scrypt hashes**

During production docker-compose testing with MariaDB, user creation failed with "Data too long for column 'password_hash'" error. Werkzeug's scrypt password hashing produces hashes approximately 175 characters long, but the `password_hash` column was defined as `String(128)`. This didn't manifest in development (SQLite) because SQLite doesn't strictly enforce VARCHAR length limits, but MariaDB does.

**Solution**: Increased `User.password_hash` column from `String(128)` to `String(256)` and added an Alembic migration.

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

### Milestone 2 (DFX-M2): Verify Development Docker Compose ✅ COMPLETE

**DFX-M2.1: Start development environment** ✅
- Created directories: `.docker-data/dev/instance/uploads`
- Container starts successfully with healthy status
- Health check passes

**DFX-M2.2: Verify functionality** ✅
- Login API works with admin/admin credentials
- Created test slideshow "Docker Test Slideshow" via API
- Verified slideshow data persists after container restart

### Milestone 3 (DFX-M3): Verify Production Docker Compose ✅ COMPLETE

**DFX-M3.1: Start production environment** ✅
- Created required directories for uploads and MariaDB data
- Created `.env` file with required environment variables
- Both app and db containers start and become healthy

**DFX-M3.2: Fix password_hash column size** ✅
- Discovered password_hash column (128 chars) too small for scrypt hashes (~175 chars)
- Updated User model to use String(256) for password_hash
- Created Alembic migration using MariaDB container (SQLite doesn't detect column size changes)

**DFX-M3.3: Verify functionality** ✅
- Login API works with configured admin credentials
- Created test slideshow "Production Test Slideshow" via API
- Verified data persists after container restart

### Milestone 4 (DFX-M4): Acceptance Criteria ✅ COMPLETE

**DFX-M4.1: Documentation** ✅
- Updated this feature file with root cause analysis and implementation details

**DFX-M4.2: Test verification** ✅
- Backend unit tests: 466/466 passing
- Type check: passing
- Lint: passing
- Frontend tests: 109/116 passing
  - 7 pre-existing failures in `History.test.tsx` and `SlideshowItemForm.test.tsx` are unrelated to Docker fix
  - Created `docs/features/frontend-test-fixes.md` to track these as a separate issue

**DFX-M4.3: Complete feature** ✅
- Moved this feature file to `docs/features/completed/`
