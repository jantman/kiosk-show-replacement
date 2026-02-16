"""
Unit tests for Flask application factory and configuration.

Tests application creation, configuration loading,
and basic application setup.
"""

from kiosk_show_replacement.app import create_app, db


class TestAppFactory:
    """Test cases for the Flask application factory."""

    def test_create_app_default_config(self):
        """Test creating app with default configuration."""
        app = create_app()

        assert app is not None
        assert app.config["TESTING"] is False
        assert "SECRET_KEY" in app.config
        assert "SQLALCHEMY_DATABASE_URI" in app.config
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False

    def test_create_app_testing_config(self):
        """Test creating app with testing configuration."""
        app = create_app("testing")

        assert app is not None
        # Note: We don't have a separate testing config yet,
        # but this tests the config_name parameter

    def test_app_has_blueprints(self):
        """Test that app has all required blueprints registered."""
        app = create_app()

        blueprint_names = [bp.name for bp in app.blueprints.values()]

        assert "api" in blueprint_names
        assert "display" in blueprint_names
        assert "slideshow" in blueprint_names

    def test_database_initialization(self, app):
        """Test that database can be initialized."""
        with app.app_context():
            # Database should be created by the app fixture
            assert db.engine is not None

            # Test that we can create tables
            db.create_all()

            # Verify tables exist
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()

            assert "slideshows" in table_names
            assert "slideshow_items" in table_names

    def test_health_check_endpoint(self, client, sample_user):
        """Test the health check endpoint.

        The health check requires an initialized database (at least one user).
        """
        response = client.get("/health")

        assert response.status_code == 200

        data = response.get_json()
        # Status can be healthy or degraded depending on storage state
        assert data["status"] in ["healthy", "degraded"]
        from kiosk_show_replacement import __version__

        assert data["version"] == __version__
        assert data["checks"]["database"]["initialized"] is True


class TestAppConfiguration:
    """Test application configuration management."""

    def test_instance_path_creation(self):
        """Test that instance path and upload folder are created."""
        import os

        app = create_app()

        # Instance path should exist
        assert os.path.exists(app.instance_path)

        # Upload folder should exist
        upload_path = app.config["UPLOAD_FOLDER"]
        assert os.path.exists(upload_path)

    def test_default_configuration_values(self):
        """Test default configuration values."""
        app = create_app()

        assert app.config["MAX_CONTENT_LENGTH"] == 500 * 1024 * 1024  # 500MB
        assert "uploads" in app.config["UPLOAD_FOLDER"]
        assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False

    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        # Set environment variables
        monkeypatch.setenv("SECRET_KEY", "test-secret-from-env")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test-from-env.db")

        # Reload the config module to pick up new environment variables
        import importlib

        from kiosk_show_replacement import config

        importlib.reload(config)

        app = create_app()

        assert app.config["SECRET_KEY"] == "test-secret-from-env"
        assert "test-from-env.db" in app.config["SQLALCHEMY_DATABASE_URI"]


class TestAppExtensions:
    """Test Flask extensions initialization."""

    def test_sqlalchemy_initialization(self, app):
        """Test that SQLAlchemy is properly initialized."""
        with app.app_context():
            assert db.engine is not None

    def test_migrate_initialization(self, app):
        """Test that Flask-Migrate is initialized."""
        # Check that migrate is configured
        assert hasattr(app, "extensions")
        assert "migrate" in app.extensions

    def test_cors_initialization(self, app, client):
        """Test that CORS is properly configured."""
        response = client.get("/health")

        # CORS headers should be present
        assert "Access-Control-Allow-Origin" in response.headers
