---
name: prod-bugs
description: Start the production Docker environment for manual testing, capture bugs/issues as feature files, and shut down when done.
disable-model-invocation: true
---

# Production Bug Testing Workflow

This skill guides you through starting the production Docker Compose environment, capturing bugs and issues found during manual testing, and shutting down the environment when done.

## Phase 1: Start the Production Environment

1. **Create data directories** (if they don't exist):
   ```bash
   mkdir -p .docker-data/prod/uploads .docker-data/prod/mariadb
   ```

2. **Verify `.env` file exists** with required variables:
   - `SECRET_KEY`
   - `MYSQL_ROOT_PASSWORD`
   - `MYSQL_PASSWORD`
   - `KIOSK_ADMIN_PASSWORD`

   If missing, copy from `.env.docker.example` and configure.

3. **Start the environment**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Wait for health checks** and verify both containers are healthy:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

5. **Test the endpoints**:
   - Health: http://localhost:5000/health
   - Ready: http://localhost:5000/health/ready
   - Admin: http://localhost:5000/admin/

6. Inform the user the environment is ready and provide the admin credentials from `.env`.

## Phase 2: Capture Bugs and Issues

When the user reports bugs or issues:

1. **Read the feature template** at `docs/features/template.md` to understand the format.

2. **Read the feature README** at `docs/features/README.md` for guidelines.

3. **For each bug/issue reported**, create a new feature file:
   - Location: `docs/features/<descriptive-name>.md`
   - Use kebab-case for filenames
   - Include:
     - A descriptive title (replacing "Feature Template")
     - The reference to follow `./README.md` instructions
     - An Overview section describing the bug/issue as reported
   - Do NOT research or investigate the bug - just capture it

4. **Commit each feature file** immediately after creation with a concise commit message.

5. Continue capturing bugs until the user indicates they are done.

## Phase 3: Shut Down the Environment

When the user is done testing:

1. **Stop and remove containers**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. Confirm the environment has been shut down.

## Notes

- The production environment uses MariaDB (not SQLite like development)
- Data persists in `.docker-data/prod/` between sessions
- If the Docker build fails, check for TypeScript errors in the frontend
- The user may ask you to prioritize the captured bugs after testing is complete
