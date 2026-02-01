# Remove e2e Tests

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

This application has three test suites, per `docs/development.rst`:

1. **Unit Tests** (``tests/unit/``): Test individual functions and classes in isolation
2. **Integration Tests** (``tests/integration/``): Full-stack browser tests of React frontend + Flask backend
3. **End-to-End Tests** (``tests/e2e/``): Browser tests of Flask server-rendered pages

There are currently 589 unit tests and 130 integration tests but only 26 e2e tests, 6 of which are skipped. Your task is to:

1. Systematically identify the functionality being tested by each integration test, and determine if this functionality is already being checked via an integration test. If not, add or update integration tests to ensure that they're also verifying the functionality tested by the e2e test.
2. Completely and totally remove the e2e tests from this repository - the tests themselves, the nox environment, the github actions jobs, and any mentions in `README.md`, `CLAUDE.md`, or `docs/*.rst`. From now on we will just have unit tests and integration tests.
