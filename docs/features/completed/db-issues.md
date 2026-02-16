# Database Issues

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

I've finally deployed this application for real, and configured the appropriate `MYSQL_` environment varaibles on the container. The application seems to be running, and the System Monitoring says the system is healthy and the database is connected. I can create a slideshow and add items to it, and if I navigate around the web UI that information is displayed correctly, and I can assign that slideshow to a display and it shows properly. However, the MySQL database has NO TABLES!!! After the last time I restarted the container, all of the data disappeared!

The container has the following environment variables set:

```
SECRET_KEY=<redacted>
APP_PORT=5000
MYSQL_DATABASE=kiosk_show
MYSQL_USER=kiosk
MYSQL_PASSWORD=<redacted>
MYSQL_HOST=mariadb
MYSQL_PORT=3306
KIOSK_ADMIN_USERNAME=admin
KIOSK_ADMIN_PASSWORD=<redacted>
GUNICORN_WORKERS=1
TZ=America/New_York
NEW_RELIC_LICENSE_KEY=<redacted>
NEW_RELIC_APP_NAME=KioskShow
NEW_RELIC_API_KEY=<redacted>
```

## Root Cause Analysis

The application only reads the `DATABASE_URL` environment variable for its database connection string. All config classes (`Config`, `ProductionConfig`, `DevelopmentConfig`) fall back to SQLite when `DATABASE_URL` is not set:

```python
# kiosk_show_replacement/config/__init__.py:85
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///kiosk_show.db")
```

The `docker-compose.prod.yml` constructs `DATABASE_URL` from the individual `MYSQL_*` variables, but no code in the application itself or in `docker-entrypoint.sh` does this. When the container is run directly (not via `docker-compose.prod.yml`), `DATABASE_URL` is never set, and the app silently falls back to an ephemeral SQLite database inside the container.

**Why health checks pass**: The `SELECT 1` connectivity test works on SQLite. The database appears "connected" and "healthy" because SQLite auto-creates a file on first access.

**Why data disappears**: The SQLite file lives inside the container and is destroyed on restart.

## Implementation Plan

### Milestone 1: Config Fix and Validation (DB-1)

#### Task 1.1: Add `build_mysql_url_from_env()` to config module (DB-1.1)

**File**: `kiosk_show_replacement/config/__init__.py`

Add a helper function that:
- Returns `None` if `MYSQL_HOST` is not set (no MySQL intent)
- Returns `None` if `MYSQL_HOST` is set but required vars (`MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`) are missing (partial config - validation catches this later)
- Returns `mysql+pymysql://user:password@host:port/database` when all vars present
- Uses `urllib.parse.quote_plus()` on user and password for special characters
- Defaults `MYSQL_PORT` to `3306`

#### Task 1.2: Update `ProductionConfig` to use helper (DB-1.2)

**File**: `kiosk_show_replacement/config/__init__.py`

Change `ProductionConfig.SQLALCHEMY_DATABASE_URI` to:
```python
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    build_mysql_url_from_env() or "sqlite:///kiosk_show.db"
)
```

The SQLite fallback is kept here because config classes are evaluated at import time for ALL configs. The hard-fail for production happens in `create_app()`.

#### Task 1.3: Add `validate_database_config()` function (DB-1.3)

**File**: `kiosk_show_replacement/config/__init__.py`

Validation function returning `list[tuple[str, str]]` of `(level, message)`:
- **Error**: `MYSQL_HOST` set but other required `MYSQL_*` vars missing
- **Error**: Production config resolved to SQLite
- **Warning**: `MYSQL_*` vars set but resolved URI is SQLite (e.g., explicit SQLite `DATABASE_URL` alongside `MYSQL_*` vars)

#### Task 1.4: Call validation from `create_app()` (DB-1.4)

**File**: `kiosk_show_replacement/app.py`

After config loading, call `validate_database_config()`. Log warnings, raise `ValueError` for errors (prevents app from starting with misconfigured database in production).

#### Task 1.5: Update `docker-entrypoint.sh` (DB-1.5)

**File**: `docker-entrypoint.sh`

Add after the opening banner, before `FLASK_ENV`/`FLASK_APP` setup:
```bash
if [ -z "${DATABASE_URL:-}" ] && [ -n "${MYSQL_HOST:-}" ]; then
    export DATABASE_URL="mysql+pymysql://..."
    echo "Constructed DATABASE_URL from MYSQL_* environment variables"
fi
```

Uses `${VAR:?message}` for required vars to fail with clear error messages.

#### Task 1.6: Unit tests (DB-1.6)

**File**: `tests/unit/test_config.py` (new)

Tests for `build_mysql_url_from_env()`:
- Returns `None` when `MYSQL_HOST` not set
- Returns correct URL with all vars (including default port)
- Returns correct URL with custom port
- Returns `None` when any required var missing
- URL-encodes special characters in password/user

Tests for `validate_database_config()`:
- No issues with MySQL URL in production
- No issues with SQLite in development
- Error on SQLite in production
- Error on partial MYSQL_* config
- Warning on MYSQL_* vars set with SQLite URI

Tests for `ProductionConfig` resolution:
- Uses `DATABASE_URL` when set (via `monkeypatch` + `importlib.reload`)
- Constructs from `MYSQL_*` vars when `DATABASE_URL` not set

### Milestone 2: Health Check Enhancement (DB-2)

#### Task 2.1: Add `database_type` to health check output (DB-2.1)

**File**: `kiosk_show_replacement/health.py`

Add `_get_database_type()` returning `"sqlite"`, `"mysql"`, `"postgresql"`, or `"unknown"`. Include `database_type` in `_check_database()` response dict so it appears in `/health/db` and `/health` responses.

#### Task 2.2: Unit tests for health check enhancement (DB-2.2)

**File**: `tests/unit/test_health.py`

- Test `/health/db` response includes `database_type` field
- Test `/health` response includes `database_type` in database check

### Milestone 3: Acceptance Criteria (DB-3)

#### Task 3.1: Documentation updates (DB-3.1)

- `docs/deployment.rst`: Update "Database Configuration" section to explain auto-construction from `MYSQL_*` vars; add `MYSQL_HOST` and `MYSQL_PORT` to optional variables table; add troubleshooting entry
- `.env.docker.example`: Add comment explaining auto-construction

#### Task 3.2: Run all tests and ensure passing (DB-3.2)

Run format, lint, test, and type_check nox sessions.

#### Task 3.3: Move feature document to completed (DB-3.3)

Update this document with progress, move to `docs/features/completed/`.

## Key Files

| File | Action |
|------|--------|
| `kiosk_show_replacement/config/__init__.py` | Add `build_mysql_url_from_env()`, `validate_database_config()`, update `ProductionConfig` |
| `kiosk_show_replacement/app.py` | Add validation call in `create_app()` |
| `kiosk_show_replacement/health.py` | Add `database_type` to health check output |
| `docker-entrypoint.sh` | Add `DATABASE_URL` construction from `MYSQL_*` vars |
| `tests/unit/test_config.py` | New: tests for config helpers |
| `tests/unit/test_health.py` | Add `database_type` tests |
| `docs/deployment.rst` | Document auto-construction and troubleshooting |
| `.env.docker.example` | Add explanatory comment |

## Progress

- [x] Milestone 1: Config Fix and Validation (DB-1)
- [x] Milestone 2: Health Check Enhancement (DB-2)
- [x] Milestone 3: Acceptance Criteria (DB-3)
