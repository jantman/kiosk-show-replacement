# Update All Dependencies

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Update ALL dependencies to their latest versions. For the Python runtime, update to 3.14. For Python dependencies, use `poetry update`. For the Dockerfile, find the latest version of each container on Docker Hub and update accordingly; ask me for help if you need it. For the frontend, update dependencies using the proper tools. Also ensure all GitHub Actions used in workflows are their latest version.

## Implementation Plan

### Milestone 1: Update Runtime Versions (Python 3.14, Node 25)

Update all configuration files to use Python 3.14 and Node.js 25 as the runtime versions.

**Tasks:**

- **UAD-1.1**: Update `pyproject.toml`:
  - Change `python = "^3.9"` to `python = "^3.14"`
  - Update classifiers to only include Python 3.14
  - Update `tool.black.target-version` to `['py314']`
  - Update `tool.mypy.python_version` to `"3.14"`

- **UAD-1.2**: Update `noxfile.py`:
  - Change `PYTHON_VERSIONS` to `["3.14"]`
  - Change `DEFAULT_PYTHON` to `"3.14"`

- **UAD-1.3**: Update `Dockerfile`:
  - Change `FROM python:3.13-slim AS runtime` to `FROM python:3.14.2-slim-trixie AS runtime`
  - Change `FROM node:22-alpine AS frontend-build` to `FROM node:25.3.0-alpine3.23 AS frontend-build`
  - Update Poetry version from `1.8.4` to latest (2.2.1)

- **UAD-1.4**: Update `frontend/package.json`:
  - Add `engines` field specifying `"node": ">=25.0.0"`

- **UAD-1.5**: Run all nox tests to verify Python 3.14 compatibility

### Milestone 2: Update Python Dependencies

Use Poetry to update all Python dependencies to their latest versions.

**Tasks:**

- **UAD-2.1**: Run `poetry update` to update all Python dependencies
- **UAD-2.2**: Review changes to `poetry.lock` for any major version bumps that may require code changes
- **UAD-2.3**: Run all nox tests to verify compatibility with updated dependencies

### Milestone 3: Update Frontend Dependencies

Update all npm dependencies in the frontend directory.

**Tasks:**

- **UAD-3.1**: Run `npm update` in the `frontend/` directory to update dependencies within semver ranges
- **UAD-3.2**: Run `npm outdated` to identify any dependencies that need major version updates
- **UAD-3.3**: Update any outdated dependencies to their latest versions using `npm install <package>@latest`
- **UAD-3.4**: Run frontend tests (`npm run test:run`) and build (`npm run build`) to verify compatibility

### Milestone 4: GitHub Actions

**Tasks:**

- **UAD-4.1**: Verify that no `.github/workflows/` directory exists (confirmed: no workflows present)
- **UAD-4.2**: No action required - skip this milestone

### Milestone 5: Acceptance Criteria

**Tasks:**

- **UAD-5.1**: Verify all documentation is up to date (no changes expected for dependency updates)
- **UAD-5.2**: Run all nox sessions and verify they pass:
  - `nox -s format`
  - `nox -s lint`
  - `nox -s test-3.14`
  - `nox -s type_check`
  - `nox -s test-integration`
  - `nox -s test-e2e`
  - `nox -s test-frontend`
- **UAD-5.3**: Move this feature file to `docs/features/completed/`

## Progress

- [x] Milestone 1: Update Runtime Versions (Python 3.14, Node 25) - COMPLETE
  - Updated pyproject.toml, noxfile.py, Dockerfile, .python-version, frontend/package.json
  - Updated Pillow from ^10.0.0 to ^12.0.0 for Python 3.14 compatibility
  - All 364 unit tests passing
- [x] Milestone 2: Update Python Dependencies - COMPLETE
  - Updated 46 packages via poetry update
  - All 364 unit tests passing
- [ ] Milestone 3: Update Frontend Dependencies
- [ ] Milestone 4: GitHub Actions (N/A)
- [ ] Milestone 5: Acceptance Criteria
