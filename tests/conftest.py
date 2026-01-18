"""
Test configuration and fixtures for kiosk-show-replacement.

This module provides common test fixtures and configuration
for unit, integration, and end-to-end tests.

Performance optimization: The app fixture is session-scoped to avoid
recreating the Flask app and database schema for each test. Instead,
the clean_test_data fixture truncates tables between tests.
"""

import pytest
from sqlalchemy.pool import NullPool

from kiosk_show_replacement.app import create_app, db
from kiosk_show_replacement.models import SlideItem, Slideshow


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    """Create application for testing (session-scoped for performance).

    The app and database schema are created once per test session.
    Data cleanup between tests is handled by the clean_test_data fixture.
    """
    app = create_app()

    # Use pytest's temporary directory for the database file
    tmp_path = tmp_path_factory.mktemp("test_db")
    db_file = tmp_path / "test.db"

    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
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

    # Create tables once at session start
    with app.app_context():
        db.create_all()

    yield app

    # Comprehensive cleanup at end of test session
    with app.app_context():
        try:
            db.session.rollback()
            db.session.close()
            db.session.remove()
            db.drop_all()
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
def sample_user(app):
    """Create a sample user for testing."""
    import uuid

    with app.app_context():
        # Use unique username to avoid conflicts in integration tests
        unique_id = str(uuid.uuid4())[:8]
        user = TestDataFactory.create_user(
            username=f"sample_user_{unique_id}", email=f"sample_{unique_id}@example.com"
        )
        db.session.add(user)
        db.session.commit()
        yield user
        # Cleanup happens in cleanup_db_session fixture


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    import uuid

    with app.app_context():
        # Use unique username to avoid conflicts in integration tests
        unique_id = str(uuid.uuid4())[:8]
        user = TestDataFactory.create_user(
            username=f"admin_user_{unique_id}", email=f"admin_{unique_id}@example.com"
        )
        user.is_admin = True
        db.session.add(user)
        db.session.commit()
        yield user
        # Cleanup happens in cleanup_db_session fixture


@pytest.fixture
def regular_user(app):
    """Create a regular (non-admin) user for testing."""
    import uuid

    with app.app_context():
        # Use unique username to avoid conflicts in integration tests
        unique_id = str(uuid.uuid4())[:8]
        user = TestDataFactory.create_user(
            username=f"regular_user_{unique_id}",
            email=f"regular_{unique_id}@example.com",
        )
        user.is_admin = False
        db.session.add(user)
        db.session.commit()
        yield user
        # Cleanup happens in cleanup_db_session fixture


@pytest.fixture
def sample_slideshow(app, sample_user):
    """Create a sample slideshow for testing."""
    with app.app_context():
        slideshow = TestDataFactory.create_slideshow(owner_id=sample_user.id)
        db.session.add(slideshow)
        db.session.commit()

        # Add some sample slides using factory
        slides = [
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="image",
                content_url="https://example.com/image.jpg",
                display_duration=30,
                order_index=0,
            ),
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="text",
                content_text="This is a test text slide",
                display_duration=15,
                order_index=1,
            ),
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="url",
                content_url="https://example.com",
                display_duration=45,
                order_index=2,
            ),
        ]

        for slide in slides:
            db.session.add(slide)

        db.session.commit()
        yield slideshow
        # Cleanup happens in cleanup_db_session fixture


@pytest.fixture
def sample_slideshow_with_items(app, sample_user):
    """Create a sample slideshow with multiple slide items for testing."""
    with app.app_context():
        slideshow = TestDataFactory.create_slideshow(
            name="Test Slideshow with Items",
            description="A slideshow with multiple items for testing",
            owner_id=sample_user.id,
        )
        db.session.add(slideshow)
        db.session.flush()  # Get the ID

        # Add different types of slides using factory
        items = [
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="image",
                content_url="https://example.com/image.jpg",
                display_duration=5,
                order_index=1,
            ),
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="video",
                content_url="https://example.com/video.mp4",
                display_duration=10,
                order_index=2,
            ),
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="url",
                content_url="https://example.com",
                display_duration=15,
                order_index=3,
            ),
            TestDataFactory.create_slide_item(
                slideshow_id=slideshow.id,
                content_type="text",
                content_text="This is test text content",
                display_duration=8,
                order_index=4,
            ),
        ]
        db.session.add_all(items)
        db.session.commit()

        yield slideshow, items
        # Cleanup happens in cleanup_db_session fixture


@pytest.fixture
def auth_client(client):
    """Create authenticated test client."""
    import uuid

    # Use unique username to avoid conflicts with other fixtures
    unique_id = str(uuid.uuid4())[:8]
    username = f"auth_user_{unique_id}"
    # Since we have permissive auth, any login works
    client.post("/auth/login", data={"username": username, "password": "testpass"})
    return client


@pytest.fixture
def authenticated_user(app, client):
    """Create a sample user and authenticate the session."""
    import uuid

    with app.app_context():
        # Use a unique username for each test to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        user = TestDataFactory.create_user(
            username=f"testuser_{unique_id}", email=f"test_{unique_id}@example.com"
        )
        db.session.add(user)
        db.session.commit()

        # Set up authenticated session
        with client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["username"] = user.username
            sess["is_admin"] = user.is_admin

        yield user
        # Cleanup happens in cleanup_db_session fixture


@pytest.fixture
def auth_headers(client, admin_user):
    """Create authentication headers for API testing (actually sets up session)."""
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.id
        sess["username"] = admin_user.username
        sess["is_admin"] = admin_user.is_admin
    # Return empty dict since we use session-based auth, not header-based
    return {}


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user(
        username="testuser", email="test@example.com", password="testpassword"
    ):
        """Create a test user."""
        from kiosk_show_replacement.models import User

        user = User(username=username, email=email)
        user.set_password(password)
        return user

    @staticmethod
    def create_slideshow(
        name="Test Slideshow",
        description="A slideshow for testing",
        owner_id=None,
        **kwargs,
    ):
        """Create a test slideshow."""
        defaults = {
            "name": name,
            "description": description,
            "owner_id": owner_id,
            "is_active": True,
            "is_default": False,
        }
        defaults.update(kwargs)
        return Slideshow(**defaults)

    @staticmethod
    def create_slide_item(slideshow_id, content_type="text", **kwargs):
        """Create a test slide item."""
        # Map content types to more user-friendly slide titles
        content_type_titles = {
            "text": "Text",
            "image": "Image",
            "url": "Web",
            "video": "Video",
        }

        defaults = {
            "title": f"Test {content_type_titles.get(content_type, content_type.title())} Slide",  # noqa: E501
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
def clean_test_data(app):
    """Clean up test data between tests to ensure isolation.

    This fixture runs automatically before and after each test.
    It truncates all tables (much faster than drop/create) while
    preserving the schema.
    """
    from kiosk_show_replacement.models import (
        AssignmentHistory,
        Display,
        DisplayConfigurationTemplate,
        Slideshow,
        SlideshowItem,
        User,
    )

    def _clean_all_tables():
        """Delete all data from tables in correct order (respecting FK constraints)."""
        # Delete in order to respect foreign key constraints
        # Children first, then parents
        # Note: Display has current_slideshow_id FK, so delete Display before Slideshow
        db.session.query(AssignmentHistory).delete()
        db.session.query(SlideshowItem).delete()
        db.session.query(Display).delete()  # Has FK to Slideshow via current_slideshow_id
        db.session.query(Slideshow).delete()
        db.session.query(DisplayConfigurationTemplate).delete()
        db.session.query(User).delete()
        db.session.commit()

    # Clean before test to ensure clean state
    with app.app_context():
        _clean_all_tables()

    yield  # Run the test

    # Clean after test and reset session state
    with app.app_context():
        _clean_all_tables()
        try:
            db.session.rollback()
            db.session.close()
            db.session.remove()
        except Exception:
            pass
