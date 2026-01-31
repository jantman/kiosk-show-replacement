"""
Shared fixtures for E2E tests.

This module provides fixtures specifically for end-to-end testing using
Playwright and a live Flask server.
"""

import multiprocessing

import pytest

# Python 3.14 changed the default multiprocessing start method to 'forkserver',
# but pytest-flask's LiveServer requires 'fork' for pickling to work correctly.
# Set the start method to 'fork' before any tests run.
if multiprocessing.get_start_method(allow_none=True) != "fork":
    try:
        multiprocessing.set_start_method("fork", force=True)
    except RuntimeError:
        # Start method has already been set, ignore
        pass

from datetime import datetime, timedelta, timezone

from kiosk_show_replacement.app import create_app, db
from kiosk_show_replacement.models import (
    Display,
    ICalEvent,
    ICalFeed,
    Slideshow,
    SlideshowItem,
    User,
)


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
    # Use "testing" mode to serve static files directly instead of
    # redirecting to the Vite dev server (which doesn't exist in tests)
    app = create_app("testing")

    # Use pytest's session temporary directory for the database file
    tmp_path = tmp_path_factory.mktemp("e2e_test")
    db_file = tmp_path / "e2e_test.db"

    # Configure for E2E testing
    # Use NullPool to disable connection pooling - this ensures each request gets
    # a fresh database connection. This prevents cross-process visibility issues
    # where forked server processes might have stale connection state.
    from sqlalchemy.pool import NullPool

    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "SECRET_KEY": "e2e-test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "poolclass": NullPool,
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

        # Enable WAL mode for better cross-process visibility
        # WAL (Write-Ahead Logging) allows concurrent reads and immediate
        # visibility of committed changes across different connections
        db.session.execute(db.text("PRAGMA journal_mode=WAL"))
        db.session.commit()

        # Create session-scoped test data that must be visible to the forked
        # live_server process. This data is created BEFORE the fork happens,
        # so the server process will inherit it.
        _create_session_test_data(app)

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


def _create_session_test_data(app):
    """Create session-scoped test data visible to the live_server fork.

    This data is created BEFORE the live_server fork happens, so it's
    visible to both the test process and the server process. This is
    necessary because SQLite cross-process visibility doesn't work well
    with data created after the fork.

    The created objects are stored in app.config['E2E_TEST_DATA'] so they
    can be accessed without re-querying the database (which has session
    isolation issues).
    """
    # Create test user for authentication
    test_user = User(
        username="testuser", email="test@example.com", is_active=True, is_admin=True
    )
    test_user.set_password("password")
    db.session.add(test_user)
    db.session.flush()

    # Create ICalFeed for skedda tests
    feed = ICalFeed(
        url="https://test.skedda.com/ical/test-feed.ics",
        last_fetched=datetime.now(timezone.utc),
        last_error=None,
    )
    db.session.add(feed)
    db.session.flush()

    # Create test events for today (use UTC to match API behavior)
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    events = [
        ICalEvent(
            feed_id=feed.id,
            uid="event-1",
            summary="Alice: Laser Cutting",
            description="Laser workshop",
            start_time=today + timedelta(hours=10),
            end_time=today + timedelta(hours=12),
            resources='["Glowforge Laser Cutter"]',
            attendee_name="Alice",
            attendee_email="alice@example.com",
        ),
        ICalEvent(
            feed_id=feed.id,
            uid="event-2",
            summary="Bob: CNC Project",
            description="Custom parts",
            start_time=today + timedelta(hours=14),
            end_time=today + timedelta(hours=16),
            resources='["CNC Milling Machine"]',
            attendee_name="Bob",
            attendee_email="bob@example.com",
        ),
        ICalEvent(
            feed_id=feed.id,
            uid="event-3",
            summary="Open Build Night",
            description="Open Build Night",
            start_time=today + timedelta(hours=18),
            end_time=today + timedelta(hours=21),
            resources='["Glowforge Laser Cutter", "CNC Milling Machine"]',
            attendee_name=None,
            attendee_email=None,
        ),
    ]
    for event in events:
        db.session.add(event)
    db.session.flush()

    # Create skedda slideshow
    skedda_slideshow = Slideshow(
        name="Skedda Test Slideshow",
        description="Slideshow with Skedda calendar for E2E testing",
        owner_id=test_user.id,
        is_active=True,
        is_default=False,
        default_item_duration=30,
    )
    db.session.add(skedda_slideshow)
    db.session.flush()

    # Create skedda slideshow item
    skedda_item = SlideshowItem(
        slideshow_id=skedda_slideshow.id,
        title="Equipment Calendar",
        content_type="skedda",
        ical_feed_id=feed.id,
        ical_refresh_minutes=15,
        order_index=0,
        is_active=True,
        display_duration=30,
    )
    db.session.add(skedda_item)
    db.session.flush()

    # Create skedda display with slideshow assigned
    skedda_display = Display(
        name="skedda-test-display",
        description="Display for Skedda E2E testing",
        is_active=True,
        current_slideshow_id=skedda_slideshow.id,
    )
    db.session.add(skedda_display)
    db.session.flush()

    # Create a general E2E test slideshow (for other tests)
    test_slideshow = Slideshow(
        name="E2E Test Slideshow",
        description="Slideshow for end-to-end testing",
        owner_id=test_user.id,
        is_active=True,
        is_default=False,
    )
    db.session.add(test_slideshow)
    db.session.flush()

    # Create a general E2E test display (for other tests)
    test_display = Display(
        name="e2e-test-display",
        description="Display for E2E testing",
        is_active=True,
    )
    db.session.add(test_display)

    db.session.commit()

    # Force WAL checkpoint to ensure all data is written to the main database file
    # This prevents intermittent cross-process visibility issues where direct queries
    # (like SlideshowItem.query.filter_by(id=1)) might not see data that relationship
    # access (like slideshow.items) can see.
    #
    # Use TRUNCATE mode instead of FULL to reset the WAL file after checkpointing.
    # This helps ensure that newly forked processes start with a clean view of the
    # database rather than potentially reading stale data from WAL file caches.
    db.session.execute(db.text("PRAGMA wal_checkpoint(TRUNCATE)"))

    # Store object data in app config BEFORE closing session (while objects are still bound)
    # Store primitive values that survive context changes
    app.config["E2E_TEST_DATA"] = {
        "user": {"id": test_user.id, "username": test_user.username},
        "skedda_display": {"id": skedda_display.id, "name": skedda_display.name},
        "skedda_slideshow": {"id": skedda_slideshow.id, "name": skedda_slideshow.name},
        "skedda_item": {"id": skedda_item.id, "title": skedda_item.title},
        "feed": {"id": feed.id, "url": feed.url},
        "events": [{"id": e.id, "summary": e.summary} for e in events],
        "test_display": {"id": test_display.id, "name": test_display.name},
        "test_slideshow": {"id": test_slideshow.id, "name": test_slideshow.name},
    }

    # Close and remove the session to release all connections.
    # This ensures that when the live_server fork happens, no stale connection
    # state is inherited. New connections will be created when needed, and they
    # will see the fully committed and checkpointed data.
    db.session.close()
    db.session.remove()


@pytest.fixture(scope="function")
def e2e_data(e2e_app):
    """Provide test data for E2E tests.

    This fixture returns the session-scoped test data that was created
    before the live_server fork. Uses data stored in app.config to avoid
    database session isolation issues.
    """
    # Get the stored test data from app config (created in _create_session_test_data)
    test_data = e2e_app.config.get("E2E_TEST_DATA", {})

    # Create simple namespace objects with the data we need for tests
    class UserData:
        def __init__(self, data):
            self.id = data["id"]
            self.username = data["username"]

    class DisplayData:
        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]

    class SlideshowData:
        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]

    yield {
        "user": UserData(test_data["user"]),
        "slideshow": SlideshowData(test_data["test_slideshow"]),
        "display": DisplayData(test_data["test_display"]),
    }


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
    # Note: Now includes both the general E2E slideshow and the skedda slideshow
    return {"slideshows": 2, "displays": 2}


@pytest.fixture(scope="function")
def skedda_slideshow_data(e2e_app):
    """Provide skedda test data for E2E tests.

    This fixture returns the session-scoped skedda test data that was created
    before the live_server fork. Uses data stored in app.config to avoid
    database session isolation issues.
    """
    # Get the stored test data from app config (created in _create_session_test_data)
    test_data = e2e_app.config.get("E2E_TEST_DATA", {})

    # Create simple namespace objects with the data we need for tests
    class DisplayData:
        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]

    class SlideshowData:
        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]

    class ItemData:
        def __init__(self, data):
            self.id = data["id"]
            self.title = data["title"]

    class FeedData:
        def __init__(self, data):
            self.id = data["id"]
            self.url = data["url"]

    class EventData:
        def __init__(self, data):
            self.id = data["id"]
            self.summary = data["summary"]

    yield {
        "display": DisplayData(test_data["skedda_display"]),
        "slideshow": SlideshowData(test_data["skedda_slideshow"]),
        "item": ItemData(test_data["skedda_item"]),
        "feed": FeedData(test_data["feed"]),
        "events": [EventData(e) for e in test_data["events"]],
    }
