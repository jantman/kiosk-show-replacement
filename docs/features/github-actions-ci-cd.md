# GitHub Actions CI/CD Workflows

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Set up comprehensive GitHub Actions workflows for continuous integration and deployment. Where possible, prefer using relevant Actions rather than bash commands. See https://github.com/jantman/machine-access-control/tree/main/.github/workflows for inspiration and ideas, though directly duplicating this is not required.

### CI Workflows (on PR or workflow dispatch)
- Run all test environments: `nox -s test-3.13`, `nox -s test-integration`, `nox -s test-e2e`
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
