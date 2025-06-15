#!/usr/bin/env python3
"""
Database initialization script for kiosk-show-replacement.

This script initializes the database tables and optionally adds sample data
for testing and demonstration purposes. Uses the new comprehensive database
models and utilities.
"""

import sys
from datetime import datetime
from typing import Optional

import click
from flask import Flask

from ..app import create_app
from ..database_utils import BackupUtils, DatabaseUtils
from ..models import User


def init_database(
    app: Flask,
    create_sample_data: bool = False,
    reset_existing: bool = False,
    admin_username: str = "admin",
    admin_password: str = "admin",
    admin_email: Optional[str] = None,
) -> bool:
    """
    Initialize the database with all required tables.

    Args:
        app: Flask application instance
        create_sample_data: Whether to create sample data for testing
        reset_existing: Whether to drop existing tables first
        admin_username: Username for admin user
        admin_password: Password for admin user
        admin_email: Email for admin user (optional)
    """
    with app.app_context():
        if reset_existing:
            print("🗑️  Dropping existing database tables...")
            success = DatabaseUtils.drop_all_tables()
            if success:
                print("✅ Existing tables dropped successfully.")
            else:
                print("❌ Error dropping existing tables.")
                return False

        # Create all tables
        print("📋 Creating database tables...")
        success = DatabaseUtils.create_all_tables()
        if success:
            print("✅ Database tables created successfully.")
        else:
            print("❌ Error creating database tables.")
            return False

        # Create admin user
        print(f"👤 Creating admin user '{admin_username}'...")
        admin_user = DatabaseUtils.create_admin_user(
            username=admin_username, password=admin_password, email=admin_email
        )
        if admin_user:
            print(f"✅ Admin user '{admin_username}' created successfully.")
        else:
            print(
                f"⚠️  Admin user '{admin_username}' may already exist or "
                f"creation failed."
            )
            # Try to get existing user
            admin_user = User.query.filter_by(username=admin_username).first()

        if create_sample_data:
            print("🎨 Creating sample data...")
            success = DatabaseUtils.create_sample_data(user=admin_user)
            if success:
                print("✅ Sample data created successfully.")
            else:
                print("❌ Error creating sample data.")
                return False

        # Health check
        print("🏥 Performing database health check...")
        health_status = DatabaseUtils.check_database_health()
        if health_status["status"] == "healthy":
            print("✅ Database health check passed.")
            print(f"   Tables: {', '.join(health_status['tables'].keys())}")
            for table, status in health_status["tables"].items():
                if status["exists"]:
                    print(f"   - {table}: {status['record_count']} records")
                else:
                    print(f"   - {table}: ❌ Missing")
        else:
            print(
                f"❌ Database health check failed: "
                f"{health_status.get('error', 'Unknown error')}"
            )
            return False

        print("🎉 Database initialization completed successfully!")
        return True


@click.command()
@click.option(
    "--sample-data",
    is_flag=True,
    help="Create sample data for testing and demonstration",
)
@click.option(
    "--reset", is_flag=True, help="Drop existing tables before creating new ones"
)
@click.option(
    "--admin-username", default="admin", help="Username for admin user (default: admin)"
)
@click.option(
    "--admin-password", default="admin", help="Password for admin user (default: admin)"
)
@click.option("--admin-email", default=None, help="Email for admin user (optional)")
@click.option("--backup", is_flag=True, help="Create backup before making changes")
@click.option(
    "--backup-path", default=None, help="Path for backup file (default: auto-generated)"
)
def main(
    sample_data: bool,
    reset: bool,
    admin_username: str,
    admin_password: str,
    admin_email: Optional[str],
    backup: bool,
    backup_path: Optional[str],
) -> None:
    """Initialize the kiosk-show-replacement database."""

    print("🚀 Kiosk Show Replacement - Database Initialization")
    print("=" * 50)

    # Create Flask app
    app = create_app()

    # Create backup if requested
    if backup:
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"database_backup_{timestamp}.db"

        print(f"💾 Creating database backup: {backup_path}")
        with app.app_context():
            success = BackupUtils.create_sqlite_backup(backup_path)
            if success:
                print(f"✅ Backup created: {backup_path}")
            else:
                print("❌ Backup failed. Continuing without backup...")

    # Initialize database
    success = init_database(
        app=app,
        create_sample_data=sample_data,
        reset_existing=reset,
        admin_username=admin_username,
        admin_password=admin_password,
        admin_email=admin_email,
    )

    if success:
        print("\n🎯 Next steps:")
        print(
            f"   1. Login with username: {admin_username}, password: {admin_password}"
        )
        print("   2. Run the development server: python run.py")
        print("   3. Open your browser to: http://localhost:5000")

        if sample_data:
            print("\n📊 Sample data includes:")
            print("   - 2 sample slideshows")
            print("   - 3 sample displays")
            print("   - Various slideshow items (text, images, URLs)")

        sys.exit(0)
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
