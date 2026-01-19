#!/bin/bash
set -e

# Docker entrypoint script for kiosk-show-replacement
# Handles database initialization/migration and starts the application

echo "=== Kiosk Show Replacement - Docker Entrypoint ==="

# Set default environment variables if not provided
export FLASK_ENV="${FLASK_ENV:-production}"
export FLASK_APP="kiosk_show_replacement.app:create_app('${FLASK_ENV}')"

# Wait for database if using external database (MariaDB/PostgreSQL)
if [[ "$DATABASE_URL" == mysql* ]] || [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Waiting for database to be ready..."

    # Extract host and port from DATABASE_URL for health check
    # Format: mysql+pymysql://user:pass@host:port/db or postgresql://user:pass@host:port/db
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')

    # Default ports if not specified
    if [[ "$DATABASE_URL" == mysql* ]]; then
        DB_PORT="${DB_PORT:-3306}"
    else
        DB_PORT="${DB_PORT:-5432}"
    fi

    # Wait up to 60 seconds for database
    RETRIES=30
    until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null || [ $RETRIES -eq 0 ]; do
        echo "Waiting for database at $DB_HOST:$DB_PORT... ($RETRIES retries left)"
        RETRIES=$((RETRIES-1))
        sleep 2
    done

    if [ $RETRIES -eq 0 ]; then
        echo "ERROR: Database not available after 60 seconds"
        exit 1
    fi

    echo "Database is available!"
fi

# Run database migrations
echo "Running database migrations..."
python -c "
from kiosk_show_replacement.app import create_app
from flask_migrate import upgrade

app = create_app('${FLASK_ENV}')
with app.app_context():
    upgrade()
    print('Migrations completed successfully')
"

# Check if this is a fresh database (no admin user exists)
echo "Checking database state..."
python -c "
import sys
from kiosk_show_replacement.app import create_app
from kiosk_show_replacement.models import User

app = create_app('${FLASK_ENV}')
with app.app_context():
    admin = User.query.filter_by(is_admin=True).first()
    if admin is None:
        print('No admin user found - database needs initialization')
        sys.exit(1)
    else:
        print('Admin user exists - database is ready')
        sys.exit(0)
" || {
    echo "Initializing database with default admin user..."

    # Get admin credentials from environment or use defaults
    ADMIN_USER="${KIOSK_ADMIN_USERNAME:-admin}"
    ADMIN_PASS="${KIOSK_ADMIN_PASSWORD:-admin}"
    ADMIN_EMAIL="${KIOSK_ADMIN_EMAIL:-}"

    python -c "
from kiosk_show_replacement.app import create_app
from kiosk_show_replacement.database_utils import DatabaseUtils

app = create_app('${FLASK_ENV}')
with app.app_context():
    # Create tables if they don't exist
    DatabaseUtils.create_all_tables()

    # Create admin user
    admin = DatabaseUtils.create_admin_user(
        username='${ADMIN_USER}',
        password='${ADMIN_PASS}',
        email='${ADMIN_EMAIL}' if '${ADMIN_EMAIL}' else None
    )
    if admin:
        print(f'Created admin user: ${ADMIN_USER}')
    else:
        print('Admin user may already exist')
"
    echo "Database initialization completed"
}

echo "Starting application..."

# Check if NewRelic is enabled (NEW_RELIC_LICENSE_KEY is set and non-empty)
if [ -n "${NEW_RELIC_LICENSE_KEY:-}" ]; then
    echo "NewRelic monitoring enabled"

    # Set default app name if not provided
    export NEW_RELIC_APP_NAME="${NEW_RELIC_APP_NAME:-kiosk-show-replacement}"

    # Wrap the command with newrelic-admin for automatic instrumentation
    exec newrelic-admin run-program "$@"
else
    echo "NewRelic monitoring disabled (NEW_RELIC_LICENSE_KEY not set)"
    # Execute the main command directly (usually gunicorn)
    exec "$@"
fi
