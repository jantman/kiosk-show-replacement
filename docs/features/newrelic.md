# NewRelic and Deployment Docs

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

1. Set up optional NewRelic integration for this application. NewRelic should only be activated/loaded if the `NEW_RELIC_LICENSE_KEY` environment variable is set and non-empty. All NewRelic configuration should be via environment variables, not a `.ini` file. Document basic/minimal NewRelic configuration in `docs/deployment.rst`.
2. Update all relevant documentation (`docs/deployment.rst`, `docs/development.rst`, `docs/installation.rst`, `CLAUDE.md`, and `README.md`) to clarify that Docker is the only supported installation pattern for production deployments and local Python installation is only supported for development. Ensure that instructions for direct local (non-Docker) installation appear ONLY in `docs/development.rst` and `CLAUDE.md` and that all other (deployment, installation, README) documents only give instructions for Docker installation and clarify that this is the only supported method for production use.

---

## Implementation Plan

### Milestone 1: NewRelic Integration (NR-1)

**Objective**: Add optional NewRelic APM integration that activates only when `NEW_RELIC_LICENSE_KEY` is set.

#### Task 1.1: Add NewRelic Dependency (NR-1.1)
- Add `newrelic` package as an optional dependency in `pyproject.toml`
- The package should be included in the main dependencies since it's needed in production Docker deployments

#### Task 1.2: Update Docker Configuration (NR-1.2)
- Modify `docker-entrypoint.sh` to conditionally wrap gunicorn with `newrelic-admin run-program` when `NEW_RELIC_LICENSE_KEY` is set
- This approach allows NewRelic to auto-instrument Flask/gunicorn without code changes
- The entrypoint script will check for the env var and conditionally use the NewRelic wrapper

#### Task 1.3: Update Docker Compose Files (NR-1.3)
- Add commented-out NewRelic environment variables to `.env.docker.example`
- Document the minimum required variables: `NEW_RELIC_LICENSE_KEY`, `NEW_RELIC_APP_NAME`

#### Task 1.4: Document NewRelic Configuration (NR-1.4)
- Add NewRelic configuration section to `docs/deployment.rst`
- Document all supported environment variables with descriptions
- Include minimal and recommended configurations

**Key Environment Variables for NewRelic:**
- `NEW_RELIC_LICENSE_KEY` - Required. Your NewRelic license key.
- `NEW_RELIC_APP_NAME` - Required. Application name shown in NewRelic dashboard.
- `NEW_RELIC_LOG_LEVEL` - Optional. Logging level (default: info).
- `NEW_RELIC_DISTRIBUTED_TRACING_ENABLED` - Optional. Enable distributed tracing.
- `NEW_RELIC_ENVIRONMENT` - Optional. Environment tag (production, staging, etc.)

### Milestone 2: Documentation Updates (NR-2)

**Objective**: Update all documentation to clarify Docker-only production support.

#### Task 2.1: Update docs/deployment.rst (NR-2.1)
- Keep as Docker-focused deployment guide
- Remove "Manual Deployment (Without Docker)" section entirely
- Add clear statement that Docker is the only supported production method
- Add NewRelic configuration section (from Milestone 1)

#### Task 2.2: Update docs/installation.rst (NR-2.2)
- Remove all local/poetry installation instructions
- Transform into a Docker-only quick-start installation guide
- Add reference to `docs/development.rst` for development setup
- Add clear statement about Docker being the only production method

#### Task 2.3: Update README.md (NR-2.3)
- Remove "Manual Deployment" section
- Keep Quick Start focused on development workflow
- Update Deployment section to be Docker-only
- Add link to `docs/development.rst` for local development setup
- Add link to `docs/deployment.rst` for production Docker deployment

#### Task 2.4: Update docs/development.rst (NR-2.4)
- Ensure local Python/Poetry installation instructions are complete and clear
- Add note that this is the ONLY place for non-Docker installation
- Add note clarifying this is for development only, not production

#### Task 2.5: Update CLAUDE.md (NR-2.5)
- Ensure local development instructions remain clear
- Add note clarifying local setup is for development only
- Keep existing content about running locally without Docker

### Milestone 3: Acceptance Criteria (NR-3)

#### Task 3.1: Verify Tests Pass (NR-3.1)
- Run all nox sessions and ensure they pass
- Verify no regressions from changes

#### Task 3.2: Verify Documentation Consistency (NR-3.2)
- Review all updated documentation for consistency
- Ensure no conflicting instructions across documents
- Verify NewRelic documentation is accurate

#### Task 3.3: Test NewRelic Integration (NR-3.3)
- Build Docker image with changes
- Verify NewRelic does NOT load when env var is unset
- Verify NewRelic loads when env var IS set (manual verification with valid key, or log inspection)

#### Task 3.4: Move Feature Document (NR-3.4)
- Move `docs/features/newrelic.md` to `docs/features/completed/`
- Final commit

---

## Progress

- [x] Milestone 1: NewRelic Integration
  - [x] Task 1.1: Add NewRelic Dependency
  - [x] Task 1.2: Update Docker Configuration
  - [x] Task 1.3: Update Docker Compose Files
  - [x] Task 1.4: Document NewRelic Configuration
- [x] Milestone 2: Documentation Updates
  - [x] Task 2.1: Update docs/deployment.rst
  - [x] Task 2.2: Update docs/installation.rst
  - [x] Task 2.3: Update README.md
  - [x] Task 2.4: Update docs/development.rst
  - [x] Task 2.5: Update CLAUDE.md
- [ ] Milestone 3: Acceptance Criteria
  - [ ] Task 3.1: Verify Tests Pass
  - [ ] Task 3.2: Verify Documentation Consistency
  - [ ] Task 3.3: Test NewRelic Integration
  - [ ] Task 3.4: Move Feature Document
