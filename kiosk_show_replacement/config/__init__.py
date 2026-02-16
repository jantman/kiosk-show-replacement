"""
Configuration module for kiosk-show-replacement.

This module handles different configuration environments and settings.
"""

import os
from datetime import timedelta
from urllib.parse import quote_plus

# Get the project root directory (two levels up from this config file)
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def build_mysql_url_from_env() -> str | None:
    """Construct a MySQL connection URL from individual MYSQL_* environment variables.

    Returns a mysql+pymysql:// URL if MYSQL_HOST and all required variables
    (MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE) are set. Returns None if
    MYSQL_HOST is not set or if any required variable is missing (partial
    config is caught by validate_database_config()).

    Returns:
        MySQL connection URL string, or None
    """
    host = os.environ.get("MYSQL_HOST")
    if not host:
        return None

    user = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    database = os.environ.get("MYSQL_DATABASE")

    if not user or not password or not database:
        return None

    port = os.environ.get("MYSQL_PORT", "3306")
    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def validate_database_config(
    config_name: str, resolved_uri: str
) -> list[tuple[str, str]]:
    """Validate the database configuration and return any issues found.

    Args:
        config_name: The active configuration name (e.g. "production", "development")
        resolved_uri: The resolved SQLALCHEMY_DATABASE_URI value

    Returns:
        List of (level, message) tuples where level is "error" or "warning"
    """
    issues: list[tuple[str, str]] = []
    mysql_host = os.environ.get("MYSQL_HOST")
    is_sqlite = resolved_uri.startswith("sqlite")

    # Check for partial MYSQL_* config
    if mysql_host:
        missing = []
        for var in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"):
            if not os.environ.get(var):
                missing.append(var)
        if missing:
            issues.append(
                (
                    "error",
                    f"MYSQL_HOST is set but required variable(s) missing: "
                    f"{', '.join(missing)}. Set all MYSQL_* variables or use "
                    f"DATABASE_URL directly.",
                )
            )

    # Check for production using SQLite
    if config_name == "production" and is_sqlite:
        issues.append(
            (
                "error",
                "Production configuration resolved to SQLite. Set DATABASE_URL "
                "or MYSQL_HOST/MYSQL_USER/MYSQL_PASSWORD/MYSQL_DATABASE environment "
                "variables to configure a production database.",
            )
        )

    # Check for MYSQL_* vars set but SQLite in use (e.g. explicit SQLite DATABASE_URL)
    if mysql_host and is_sqlite and not any(i[0] == "error" for i in issues):
        issues.append(
            (
                "warning",
                "MYSQL_* environment variables are set but the resolved database "
                "URI is SQLite. If you intended to use MySQL, remove the explicit "
                "DATABASE_URL or set it to a MySQL connection string.",
            )
        )

    return issues


class Config:
    """Base configuration class."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///kiosk_show.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "instance/uploads")
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH", str(500 * 1024 * 1024))
    )  # 500MB default

    # File upload limits by type (in bytes)
    MAX_IMAGE_SIZE = int(
        os.environ.get("MAX_IMAGE_SIZE", str(50 * 1024 * 1024))
    )  # 50MB
    MAX_VIDEO_SIZE = int(
        os.environ.get("MAX_VIDEO_SIZE", str(500 * 1024 * 1024))
    )  # 500MB

    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"}
    ALLOWED_VIDEO_EXTENSIONS = {
        "mp4",
        "webm",
        "avi",
        "mov",
        "mkv",
        "flv",
        "wmv",
        "mpeg",
        "mpg",
    }
    ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Session cookie settings - configure for development/testing compatibility
    # SameSite=Lax is the default but can cause issues with proxy setups
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    # Use DATABASE_URL if set, otherwise use development default
    # Use absolute path for SQLite to avoid path resolution issues
    _DEFAULT_DEV_DB = (
        f"sqlite:///{os.path.join(_PROJECT_ROOT, 'instance', 'kiosk_show_dev.db')}"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        os.environ.get("DEV_DATABASE_URL", _DEFAULT_DEV_DB),
    )


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    # Use DATABASE_URL if set, otherwise construct from MYSQL_* vars, else SQLite fallback.
    # The SQLite fallback is kept here because config classes are evaluated at import time;
    # the hard-fail for production using SQLite happens in create_app() via
    # validate_database_config().
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", build_mysql_url_from_env() or "sqlite:///kiosk_show.db"
    )


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    # Use DATABASE_URL if explicitly set (for integration tests), otherwise in-memory
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
