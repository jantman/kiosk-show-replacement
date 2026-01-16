# Feature: Docker & Deployment

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This feature provides Docker containerization and deployment tooling for easy, reproducible deployment of the application. The goal is to enable users to deploy the application with minimal configuration using Docker, while also supporting traditional deployment methods. The deployment should be suitable for self-hosted environments ranging from a single Raspberry Pi to multi-server setups.

## High-Level Deliverables

### Docker Container

- Multi-stage Dockerfile optimized for small image size and fast builds
- Proper layer caching for efficient rebuilds
- Non-root user for container security
- Health check configuration for container orchestration
- Support for both SQLite (single-node) and PostgreSQL (multi-node) databases
- Volume mounts for persistent data (database, uploads)
- Environment variable configuration for all settings

### Docker Compose

- Development compose file with hot-reload and debugging support
- Production compose file with proper resource limits and restart policies
- Optional MariaDB service for production deployments
- Volume definitions for data persistence
- Network configuration for service isolation

### Database Management

- Database initialization in containerized environment
- Migration handling on container startup
- SQLite to MariaDB migration guidance

### Deployment Documentation

- Quick start guide for Docker deployment
- Production deployment checklist
- Environment variable reference
- Upgrade procedures between versions
- Troubleshooting guide for common deployment issues

## Implementation Plan

### Technology Decisions

Based on planning discussions:
- **Database**: MariaDB for production (SQLite for development/single-node)
- **Architecture**: Multi-arch support (amd64 + arm64) for Raspberry Pi compatibility
- **WSGI Server**: Gunicorn with eventlet worker (required for SSE support)

### Milestone 1: Core Docker Infrastructure - COMPLETE

**Prefix**: `Docker - 1`

Tasks completed:
- [x] Task 1.1: Create `.dockerignore` to exclude unnecessary files from Docker context
- [x] Task 1.2: Create multi-stage `Dockerfile` with Node.js frontend build and Python runtime
- [x] Task 1.3: Create `docker-entrypoint.sh` for database migrations and initialization
- [x] Task 1.4: Add gunicorn and pymysql dependencies to `pyproject.toml`

Files created/modified:
- `.dockerignore` (new)
- `Dockerfile` (new)
- `docker-entrypoint.sh` (new)
- `pyproject.toml` (modified - added gunicorn, pymysql)
- `poetry.lock` (updated)

### Milestone 2: Docker Compose Configuration

**Prefix**: `Docker - 2`

Tasks:
- [ ] Task 2.1: Create `docker-compose.yml` for development
- [ ] Task 2.2: Create `docker-compose.prod.yml` for production with MariaDB
- [ ] Task 2.3: Create `.env.docker.example` with documented configuration options

### Milestone 3: Database Migration Support

**Prefix**: `Docker - 3`

Tasks:
- [ ] Task 3.1: Verify MariaDB configuration works with current config module
- [ ] Task 3.2: Test database migrations in containerized environment

### Milestone 4: Acceptance Criteria

**Prefix**: `Docker - 4`

Tasks:
- [ ] Task 4.1: Create deployment documentation (`docs/deployment.rst`)
- [ ] Task 4.2: Update README and CLAUDE.md
- [ ] Task 4.3: Verify Docker build succeeds
- [ ] Task 4.4: Verify Docker Compose works (dev and prod)
- [ ] Task 4.5: Run all nox sessions
- [ ] Task 4.6: Move feature file to `docs/features/completed/`

## Acceptance Criteria

The final milestone must verify:

1. Deployment documentation complete and accurate
2. Docker build succeeds and produces working image
3. Docker Compose starts all services correctly
4. Application functions correctly in containerized environment
5. All nox sessions pass successfully
6. Feature file moved to `docs/features/completed/`
