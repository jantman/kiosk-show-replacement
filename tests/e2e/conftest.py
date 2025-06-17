"""
Shared fixtures for E2E tests.

This module provides fixtures specifically for end-to-end testing using
Playwright and a live Flask server.
"""

import pytest
from flask import Flask

from kiosk_show_replacement.app import create_app, db
from kiosk_show_replacement.models import User, Slideshow, Display


@pytest.fixture(scope="session")
def e2e_app():
    """Create application instance for E2E testing."""
    app = create_app()
    
    # Use a temporary database file that both test setup and live server can access
    import tempfile
    import os
    
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close the file descriptor, we just need the path
    
    # Configure for E2E testing
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "e2e-test-secret-key",
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_recycle": -1,
            "pool_pre_ping": True,
        },
    })
    
    with app.app_context():
        db.create_all()

        # Create test user for authentication using the app's own method
        test_user = User(
            username="testuser",
            email="test@example.com",
            is_active=True
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
            is_default=False
        )
        db.session.add(test_slideshow)

        # Create test display
        test_display = Display(
            name="e2e-test-display",
            description="Display for E2E testing",
            is_active=True
        )
        db.session.add(test_display)
        db.session.commit()  # Commit all changes
        
        yield app
        
        # Cleanup
        try:
            db.session.rollback()
            db.session.close()
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        except Exception:
            pass
        
        # Clean up the temporary database file
        try:
            os.unlink(db_path)
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
    return {
        "username": "testuser",
        "password": "password"
    }


@pytest.fixture
def expected_counts():
    """Expected counts for dashboard verification."""
    return {
        "slideshows": 1,
        "displays": 1
    }
