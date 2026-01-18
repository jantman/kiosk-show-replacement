# GitHub Actions CI/CD Workflows

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Set up comprehensive GitHub Actions workflows for continuous integration and deployment:

### CI Workflows (on push/PR)
- Run all test environments: `nox -s test-3.13`, `nox -s test-integration`, `nox -s test-e2e`
- Run linting: `nox -s lint`
- Run type checking: `nox -s type_check`
- Run frontend tests and linting
- Comment on PRs with test results summary where it adds value (failures, coverage changes)

### Release Workflow (on version tag)
- Triggered by version tags (e.g., `v1.0.0`)
- Generate changelog notes from commits since last release
- Create GitHub Release with changelog in release notes
- Build Docker image
- Publish Docker container to GitHub Container Registry (ghcr.io)
- Tag container with version and `latest`
