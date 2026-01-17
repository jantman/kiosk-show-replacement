"""
Shared fixtures for E2E tests.

This module provides fixtures specifically for end-to-end testing using
Playwright and a live Flask server.
"""

import pytest

from kiosk_show_replacement.app import create_app, db
from kiosk_show_replacement.models import Display, Slideshow, User


# Configure Playwright timeouts for all E2E tests
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with proper timeouts."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="session")
def e2e_app(tmp_path_factory):
    """Create application instance for E2E testing."""
    app = create_app()

    # Use pytest's session temporary directory for the database file
    tmp_path = tmp_path_factory.mktemp("e2e_test")
    db_file = tmp_path / "e2e_test.db"

    # Configure for E2E testing
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "SECRET_KEY": "e2e-test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "pool_recycle": -1,
                "pool_pre_ping": True,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                },
            },
        }
    )

    with app.app_context():
        db.create_all()

        yield app

        # Comprehensive cleanup to prevent ResourceWarnings
        try:
            # First, close any active transactions
            db.session.rollback()

            # Close all active sessions
            db.session.close()
            db.session.remove()

            # Drop all tables
            db.drop_all()

            # Dispose of the engine to close all connections
            db.engine.dispose()
        except Exception:
            # Ignore cleanup errors
            pass


@pytest.fixture(scope="function")
def e2e_data(e2e_app):
    """Create fresh test data for each E2E test."""
    with e2e_app.app_context():
        # Clear existing data
        db.session.query(Display).delete()
        db.session.query(Slideshow).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Create test user for authentication using the app's own method
        # Make user an admin so they can access Settings page
        test_user = User(
            username="testuser", email="test@example.com", is_active=True, is_admin=True
        )
        # Use the app's set_password method which will generate the correct hash
        test_user.set_password("password")
        db.session.add(test_user)
        db.session.flush()  # Flush to get the user ID

        # Create test slideshow
        test_slideshow = Slideshow(
            name="E2E Test Slideshow",
            description="Slideshow for end-to-end testing",
            owner_id=test_user.id,
            is_active=True,
            is_default=False,
        )
        db.session.add(test_slideshow)

        # Create test display
        test_display = Display(
            name="e2e-test-display",
            description="Display for E2E testing",
            is_active=True,
        )
        db.session.add(test_display)
        db.session.commit()  # Commit all changes

        yield {"user": test_user, "slideshow": test_slideshow, "display": test_display}

        # Clean up test data after each test
        try:
            db.session.rollback()
        except Exception:
            pass


@pytest.fixture(scope="session")
def app(e2e_app):
    """Provide app fixture for pytest-flask."""
    return e2e_app


@pytest.fixture(scope="session")
def live_server_url(live_server):
    """Get the live server URL from pytest-flask."""
    return live_server.url()


@pytest.fixture
def test_credentials():
    """Provide test user credentials."""
    return {"username": "testuser", "password": "password"}


@pytest.fixture
def expected_counts():
    """Expected counts for dashboard verification."""
    return {"slideshows": 1, "displays": 1}
