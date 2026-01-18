"""
Flask application factory for kiosk-show-replacement.

This module contains the Flask application factory that creates and configures
the Flask app instance with all necessary blueprints, extensions, and configuration.
"""

import os
import re
from typing import Any, Optional

from flask import Flask, Response, abort, redirect, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


def sanitize_database_uri(uri: str) -> str:
    """
    Sanitize database URI by removing password information for logging.

    Args:
        uri: Database URI that may contain sensitive information

    Returns:
        str: Sanitized URI safe for logging
    """
    if not uri:
        return "None"

    # Pattern to match and replace password in various URI formats
    # Handles: scheme://user:password@host/db -> scheme://user:***@host/db
    sanitized = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", uri)
    return sanitized


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: The configuration name to use (development, production, testing)

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    # Load configuration from config module
    from .config import config

    app.config.from_object(config.get(config_name, config["default"]))

    # Configure SQLAlchemy engine options for better connection management
    if config_name == "testing" or app.config.get("TESTING"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "echo": False,
        }

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Enable SQLite foreign key constraint enforcement
    # SQLite requires this pragma to be set for each connection
    # Without this, ON DELETE CASCADE and other FK constraints are ignored
    if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        from sqlalchemy import event

        def _set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        with app.app_context():
            event.listen(db.engine, "connect", _set_sqlite_pragma)

    # Initialize middleware (correlation IDs, request logging)
    from .middleware import init_middleware

    init_middleware(app)

    # Initialize structured logging
    from .logging_config import init_logging

    init_logging(app)

    # Register error handlers for custom exceptions
    from .api.helpers import register_error_handlers

    register_error_handlers(app)

    # Log database configuration for debugging
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "Not configured")
    sanitized_uri = sanitize_database_uri(db_uri)
    app.logger.info(f"Flask app initialized with database: {sanitized_uri}")

    # Also log the database file path if it's SQLite
    if db_uri and db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        app.logger.info(f"SQLite database file: {db_path}")
        # Check if file exists and log its size
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            app.logger.info(f"Database file exists, size: {file_size} bytes")
        else:
            app.logger.warning(f"Database file does not exist: {db_path}")

    # Register blueprints
    from .auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Register health check blueprint (before other blueprints for priority)
    from .health import health_bp

    app.register_blueprint(health_bp)

    # Register metrics blueprint and initialize metrics collection
    from .metrics import init_metrics, metrics_bp

    app.register_blueprint(metrics_bp)
    init_metrics(app)

    from .dashboard import dashboard_bp

    app.register_blueprint(dashboard_bp)

    from .api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    from .display import display_bp

    app.register_blueprint(display_bp)

    from .slideshow import bp as slideshow_bp

    app.register_blueprint(slideshow_bp, url_prefix="/slideshow")

    # Register CLI commands
    from .cli.main import cli

    app.cli.add_command(cli)

    # File serving endpoint
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename: str) -> Response:
        """Serve uploaded files."""
        from urllib.parse import unquote_plus

        # Decode the URL-encoded filename
        decoded_filename = unquote_plus(filename)

        try:
            return send_from_directory(app.config["UPLOAD_FOLDER"], decoded_filename)
        except FileNotFoundError:
            abort(404)

    # Initialize storage system
    from .storage import init_storage

    init_storage(app)

    # Serve React frontend (for production build)
    @app.route("/admin")
    @app.route("/admin/<path:path>")
    def serve_admin(path: str = "") -> Any:
        """Serve React admin interface."""
        import os

        from flask import send_from_directory

        # In development, redirect to Vite dev server
        if app.config.get("ENV") == "development":
            return redirect("http://localhost:3000/admin")

        # In production, serve from static/dist
        static_dir = os.path.join(app.root_path, "static", "dist")
        if os.path.exists(static_dir):
            if path and os.path.exists(os.path.join(static_dir, path)):
                return send_from_directory(static_dir, path)
            else:
                return send_from_directory(static_dir, "index.html")

        # Fallback if build doesn't exist
        return (
            """
        <h1>Admin Interface Not Available</h1>
        <p>The React admin interface has not been built yet.</p>
        <p>Run: <code>cd frontend && npm run build</code></p>
        """,
            404,
        )

    return app
