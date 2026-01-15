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

## Acceptance Criteria

The final milestone must verify:

1. Deployment documentation complete and accurate
2. Docker build succeeds and produces working image
3. Docker Compose starts all services correctly
4. Application functions correctly in containerized environment
5. All nox sessions pass successfully
6. Feature file moved to `docs/features/completed/`
