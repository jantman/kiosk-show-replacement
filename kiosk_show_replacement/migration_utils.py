"""
Database migration utilities for kiosk-show-replacement.

This module provides utilities for managing database migrations using Flask-Migrate,
including migration creation, application, and rollback operations.
"""

import os
from typing import List, Optional

from flask import current_app
from flask_migrate import current, downgrade, init, migrate, show, stamp, upgrade


class MigrationUtils:
    """Utilities for database migration management."""

    @staticmethod
    def init_migration_repository() -> bool:
        """
        Initialize the migration repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            init()
            current_app.logger.info("Migration repository initialized")
            return True
        except Exception as e:
            current_app.logger.error(f"Error initializing migration repository: {e}")
            return False

    @staticmethod
    def create_migration(message: str, autogenerate: bool = True) -> bool:
        """
        Create a new migration.

        Args:
            message: Migration message/description
            autogenerate: Whether to auto-generate migration based on model changes

        Returns:
            True if successful, False otherwise
        """
        try:
            if autogenerate:
                migrate(message=message)
            else:
                migrate(message=message, sql=True)
            current_app.logger.info(f"Migration '{message}' created successfully")
            return True
        except Exception as e:
            current_app.logger.error(f"Error creating migration '{message}': {e}")
            return False

    @staticmethod
    def apply_migrations(revision: Optional[str] = None) -> bool:
        """
        Apply migrations to the database.

        Args:
            revision: Specific revision to upgrade to (default: latest)

        Returns:
            True if successful, False otherwise
        """
        try:
            if revision:
                upgrade(revision)
            else:
                upgrade()
            current_app.logger.info("Migrations applied successfully")
            return True
        except Exception as e:
            current_app.logger.error(f"Error applying migrations: {e}")
            return False

    @staticmethod
    def rollback_migration(revision: str) -> bool:
        """
        Rollback to a specific migration revision.

        Args:
            revision: Revision to rollback to

        Returns:
            True if successful, False otherwise
        """
        try:
            downgrade(revision)
            current_app.logger.info(f"Rolled back to revision: {revision}")
            return True
        except Exception as e:
            current_app.logger.error(f"Error rolling back to revision {revision}: {e}")
            return False

    @staticmethod
    def get_current_revision() -> Optional[str]:
        """
        Get the current migration revision.

        Returns:
            Current revision string or None if not available
        """
        try:
            return current()
        except Exception as e:
            current_app.logger.error(f"Error getting current revision: {e}")
            return None

    @staticmethod
    def show_migration_history() -> List[str]:
        """
        Show migration history.

        Returns:
            List of migration history lines
        """
        try:
            history = show()
            return history.split("\n") if history else []
        except Exception as e:
            current_app.logger.error(f"Error showing migration history: {e}")
            return []

    @staticmethod
    def stamp_database(revision: str) -> bool:
        """
        Stamp the database with a specific revision without running migrations.

        Args:
            revision: Revision to stamp with

        Returns:
            True if successful, False otherwise
        """
        try:
            stamp(revision)
            current_app.logger.info(f"Database stamped with revision: {revision}")
            return True
        except Exception as e:
            current_app.logger.error(
                f"Error stamping database with revision {revision}: {e}"
            )
            return False


def check_migration_status() -> dict:
    """
    Check the current migration status of the database.

    Returns:
        Dictionary containing migration status information
    """
    try:
        current_rev = MigrationUtils.get_current_revision()
        history = MigrationUtils.show_migration_history()

        # Check if migrations directory exists
        migrations_dir = os.path.join(current_app.root_path, "..", "migrations")
        migrations_exist = os.path.exists(migrations_dir)

        return {
            "status": "healthy" if current_rev else "uninitialized",
            "current_revision": current_rev,
            "migrations_directory_exists": migrations_exist,
            "migration_history_count": len(history),
            "migration_history": history[:10],  # Last 10 entries
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
