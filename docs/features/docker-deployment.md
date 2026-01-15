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
- Optional PostgreSQL service for production deployments
- Optional nginx reverse proxy service with SSL termination
- Volume definitions for data persistence
- Network configuration for service isolation

### Reverse Proxy Configuration

- nginx configuration for production deployment
- SSL/TLS termination with Let's Encrypt integration guidance
- Static file serving optimization
- WebSocket/SSE proxy configuration
- Security headers at proxy level
- Example configurations for common scenarios

### Database Management

- Database initialization in containerized environment
- Migration handling on container startup
- Backup and restore procedures for containerized databases
- SQLite to PostgreSQL migration guidance (optional)

### Deployment Documentation

- Quick start guide for Docker deployment
- Production deployment checklist
- Environment variable reference
- Backup and restore procedures
- Upgrade procedures between versions
- Troubleshooting guide for common deployment issues

## Out of Scope

- Kubernetes manifests (may be added in future)
- Cloud-specific deployment (AWS, GCP, Azure)
- Automated CI/CD pipeline configuration
- High availability / clustering setup

## Dependencies

- Requires completed Milestones 12-14 (Error Handling, Performance, Security)
- Docker and Docker Compose for testing

## Acceptance Criteria

The final milestone must verify:

1. Deployment documentation complete and accurate
2. Docker build succeeds and produces working image
3. Docker Compose starts all services correctly
4. Application functions correctly in containerized environment
5. All nox sessions pass successfully
6. Feature file moved to `docs/features/completed/`
