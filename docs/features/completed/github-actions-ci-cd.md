# GitHub Actions CI/CD Workflows

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Set up comprehensive GitHub Actions workflows for continuous integration and deployment. Where possible, prefer using relevant Actions rather than bash commands. See https://github.com/jantman/machine-access-control/tree/main/.github/workflows for inspiration and ideas, though directly duplicating this is not required.

### CI Workflows (on PR or workflow dispatch)
- Run all test environments: `nox -s test-3.14`, `nox -s test-integration`, `nox -s test-e2e`
- Run linting: `nox -s lint`
- Run type checking: `nox -s type_check`
- Run frontend tests and linting
- Comment on PRs with test results summary where it adds value (failures, coverage changes)

### Release Workflow
- Ideally, this would run on push or PR merge to `main` branch, when the version (Poetry version / version in pyproject.toml) is greater than the latest release version
- Generate changelog notes for changes since last release
- Create tag and GitHub Release with changelog in release notes
- Build Docker image
- Publish Docker container to GitHub Container Registry (ghcr.io)
- Tag container with version and `latest`

---

## Implementation Plan

**Status:** Implementation Complete

### Milestone 1: CI Workflow Setup (GACI-1)

Create the CI workflow that runs on PRs and manual dispatch.

#### Task 1.1: Create CI workflow file (GACI-1.1)
**File:** `.github/workflows/ci.yml`

**Design:**
- Trigger on `pull_request` and `workflow_dispatch`
- Matrix strategy for parallel test jobs
- Jobs:
  1. **lint**: Run `nox -s lint` (Python linting)
  2. **type-check**: Run `nox -s type_check` (mypy)
  3. **test-unit**: Run `nox -s test-3.14` (unit tests with coverage)
  4. **test-integration**: Run `nox -s test-integration` (React + Flask browser tests)
  5. **test-e2e**: Run `nox -s test-e2e` (Flask server-rendered page browser tests)
  6. **test-frontend**: Run `nox -s test-frontend` (Vitest + ESLint + TypeScript)

**Key Implementation Details:**
- Use `actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`
- Install poetry and nox via pip using pipx pattern from reference repo
- Cache pip and npm dependencies for faster builds
- Upload test artifacts (coverage reports, JUnit XML reports)
- Install Playwright browsers for integration/e2e tests

#### Task 1.2: Add coverage reporting job (GACI-1.2)
Add a job that comments on PRs with test results summary.

**Design:**
- Use `MishaKav/pytest-coverage-comment@v1` action
- Downloads coverage artifacts from test-unit job
- Only runs on PRs (not on workflow_dispatch)

#### Task 1.3: Add constraints.txt for pip version pinning (GACI-1.3)
**File:** `.github/workflows/constraints.txt`

Pin pip and nox versions for reproducible CI builds.

---

### Milestone 2: Release Workflow Setup (GACI-2)

Create the release workflow that triggers on version bumps.

#### Task 2.1: Create release workflow file (GACI-2.1)
**File:** `.github/workflows/release.yml`

**Design:**
- Trigger on push to `main` branch
- Compare version in `pyproject.toml` with latest GitHub release
- Only proceed if version is higher (new release)
- Steps:
  1. Check out code
  2. Extract version from `pyproject.toml` using poetry
  3. Get latest release tag from GitHub API
  4. Compare versions - exit early if not a new release
  5. Build and push Docker image to ghcr.io
  6. Create GitHub Release with auto-generated changelog

#### Task 2.2: Docker image build and push (GACI-2.2)
**Design:**
- Use `docker/setup-buildx-action@v3` for efficient multi-platform builds
- Use `docker/build-push-action@v6`
- Login to ghcr.io using `GITHUB_TOKEN`
- Tag image with both version number and `latest`
- Add OCI labels for traceability (source URL, version, revision)

#### Task 2.3: GitHub Release creation with changelog (GACI-2.3)
**Design:**
- Use `softprops/action-gh-release@v2` (preferred over deprecated `actions/create-release@v1`)
- Use `generate_release_notes: true` for auto changelog from commit history
- Include links to Docker image in release notes

---

### Milestone 3: Acceptance Criteria (GACI-3)

#### Task 3.1: Verify workflow syntax (GACI-3.1)
- Validate YAML syntax
- Run `nox` sessions locally to confirm they work

#### Task 3.2: Update documentation (GACI-3.2)
- Add CI status badges to `README.md`
- Update `CLAUDE.md` if any new commands or patterns added

#### Task 3.3: Ensure all nox sessions pass (GACI-3.3)
Run full test suite to verify everything works before completion.

#### Task 3.4: Move feature document to completed (GACI-3.4)
Move `docs/features/github-actions-ci-cd.md` to `docs/features/completed/`

---

## Files to Create/Modify

### New Files:
- `.github/workflows/ci.yml` - CI workflow
- `.github/workflows/release.yml` - Release workflow
- `.github/workflows/constraints.txt` - pip version constraints

### Files to Update:
- `docs/features/github-actions-ci-cd.md` - This file (progress tracking)
- `README.md` - Add CI status badges

---

## Technical Notes

- **Python 3.14 only** - matching project's pyproject.toml specification
- **Node.js 25.x** required for frontend (per package.json `engines` field)
- Integration and E2E tests require Playwright browser installation in CI
- Reference patterns from `jantman/machine-access-control` workflows
- Test reports are generated in `reports/` directory (JUnit XML format)

---

## Progress

- [x] Milestone 1: CI Workflow Setup
  - [x] Task 1.1: Create CI workflow file
  - [x] Task 1.2: Add coverage reporting job
  - [x] Task 1.3: Add constraints.txt
- [x] Milestone 2: Release Workflow Setup
  - [x] Task 2.1: Create release workflow file
  - [x] Task 2.2: Docker image build and push
  - [x] Task 2.3: GitHub Release creation
- [x] Milestone 3: Acceptance Criteria
  - [x] Task 3.1: Verify workflow syntax
  - [x] Task 3.2: Update documentation
  - [x] Task 3.3: Ensure all nox sessions pass
  - [x] Task 3.4: Move feature document to completed
