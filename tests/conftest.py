"""
Test configuration and fixtures for kiosk-show-replacement.

This module provides common test fixtures and configuration
for unit, integration, and end-to-end tests.
"""

import gc
import os
import tempfile

import pytest
from sqlalchemy.pool import NullPool

from kiosk_show_replacement.app import create_app, db
from kiosk_show_replacement.models import SlideItem, Slideshow


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "poolclass": NullPool,  # Disable connection pooling for tests
                "pool_recycle": -1,
                "pool_pre_ping": True,
                "echo": False,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20,
                },
            },
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
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
            
            # Explicitly close all connections in the engine
            # Get the raw connection and close it
            try:
                with db.engine.connect() as conn:
                    conn.close()
            except Exception:
                pass
            
            # Dispose of the engine completely - this should close all connections
            db.engine.dispose()
                
        except Exception:
            pass


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_slideshow(app):
    """Create a sample slideshow for testing."""
    with app.app_context():
        slideshow = Slideshow(
            name="Test Slideshow", description="A slideshow for testing"
        )
        db.session.add(slideshow)
        db.session.commit()

        # Add some sample slides
        slides = [
            SlideItem(
                slideshow_id=slideshow.id,
                title="Test Image Slide",
                content_type="image",
                content_url="https://example.com/image.jpg",
                display_duration=30,
                order_index=0,
            ),
            SlideItem(
                slideshow_id=slideshow.id,
                title="Test Text Slide",
                content_type="text",
                content_text="This is a test text slide",
                display_duration=15,
                order_index=1,
            ),
            SlideItem(
                slideshow_id=slideshow.id,
                title="Test Web Slide",
                content_type="url",
                content_url="https://example.com",
                display_duration=45,
                order_index=2,
            ),
        ]

        for slide in slides:
            db.session.add(slide)

        db.session.commit()

        # Refresh the slideshow to ensure all relationships are loaded
        db.session.refresh(slideshow)
        slideshow_id = slideshow.id
        
        # Close the session after setup
        db.session.close()

        yield slideshow

        # Cleanup after test
        try:
            # Get a fresh instance and delete it
            fresh_slideshow = db.session.get(Slideshow, slideshow_id)
            if fresh_slideshow:
                db.session.delete(fresh_slideshow)
                db.session.commit()
        except Exception:
            # If there's an error, just roll back
            db.session.rollback()
        finally:
            # Ensure session is closed
            db.session.close()


@pytest.fixture
def auth_client(client):
    """Create authenticated test client."""
    # Since we have permissive auth, any login works
    client.post("/auth/login", data={"username": "testuser", "password": "testpass"})
    return client


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_slideshow(name="Test Slideshow", description="Test Description"):
        """Create a test slideshow."""
        return Slideshow(name=name, description=description)

    @staticmethod
    def create_slide_item(slideshow_id, content_type="text", **kwargs):
        """Create a test slide item."""
        defaults = {
            "title": f"Test {content_type.title()} Slide",
            "content_type": content_type,
            "display_duration": 30,
            "order_index": 0,
        }

        if content_type == "text":
            defaults["content_text"] = "Test content text"
        elif content_type in ["image", "url"]:
            defaults["content_url"] = "https://example.com/test"

        defaults.update(kwargs)
        defaults["slideshow_id"] = slideshow_id

        return SlideItem(**defaults)


@pytest.fixture
def test_factory():
    """Provide test data factory."""
    return TestDataFactory


@pytest.fixture(autouse=True)
def cleanup_db_session(app):
    """Automatically cleanup database sessions after each test."""
    yield  # Run the test
    
    # Clean up after each test to prevent connection leaks
    with app.app_context():
        try:
            # Close and remove any open sessions - this should be sufficient
            db.session.rollback()
            db.session.close()
            db.session.remove()
            
            # Dispose of the engine to close all connections
            db.engine.dispose()
            
        except Exception:
            pass


@pytest.fixture(scope="session", autouse=True)
def configure_sqlalchemy_session():
    """Configure SQLAlchemy for better connection management in tests."""
    yield
    # Session cleanup is handled by individual test cleanup
    # Python's automatic garbage collection will handle the rest
