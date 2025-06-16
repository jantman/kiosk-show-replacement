"""
Flask application factory for kiosk-show-replacement.

This module contains the Flask application factory that creates and configures
the Flask app instance with all necessary blueprints, extensions, and configuration.
"""

import os
from typing import Optional

from flask import Flask, abort, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


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

    # Register blueprints
    from .auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

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

    # Health check endpoint
    @app.route("/health")
    def health_check() -> dict[str, str]:
        from . import __version__

        return {"status": "healthy", "version": __version__}

    # File serving endpoint
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename: str):
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

    return app
