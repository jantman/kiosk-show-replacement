"""
Configuration module for kiosk-show-replacement.

This module handles different configuration environments and settings.
"""

import os
from datetime import timedelta


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
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "avi", "mov", "mkv", "flv", "wmv"}
    ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    # Use DATABASE_URL if set, otherwise use development default
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        os.environ.get("DEV_DATABASE_URL", "sqlite:///kiosk_show_dev.db"),
    )


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    # Use PostgreSQL in production if available
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///kiosk_show.db")


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
