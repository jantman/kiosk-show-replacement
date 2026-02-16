"""
Configuration for integration tests using Playwright.

This configures Playwright to test our Flask application with browser automation
and provides enhanced server management with comprehensive logging.
"""

import logging
import sys
from pathlib import Path

import pytest
import requests
from playwright.sync_api import Page

# Add the tests directory to the Python path for imports
current_dir = Path(__file__).parent
tests_dir = current_dir.parent
sys.path.insert(0, str(tests_dir))

from integration.server_manager import EnhancedServerManager  # noqa: E402

# Import live_server fixture from pytest-flask
pytest_plugins = ["flask"]

# Configure comprehensive logging for integration tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app(test_database):
    """Create Flask app for pytest-flask live_server fixture."""
    from kiosk_show_replacement.app import create_app, db

    # Use the same database as the running Flask server
    db_path = test_database["db_path"]

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SECRET_KEY": "integration-test-secret-key",
            "WTF_CSRF_ENABLED": False,
        }
    )

    # Database is already created by test_database fixture
    # Just ensure we have the correct context
    with app.app_context():
        # Verify connection to the test database
        with db.engine.connect() as conn:
            conn.execute(db.text("SELECT 1")).fetchone()

    return app


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for integration tests."""
    return {
        **browser_context_args,
        # Don't ignore HTTPS errors for security testing
        "ignore_https_errors": False,
        # Set a reasonable viewport size for desktop testing
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch arguments for integration tests."""
    return {
        **browser_type_launch_args,
        # Use headless mode for CI/testing
        "headless": True,
        # Add arguments for more stable testing
        "args": [
            "--no-sandbox",  # Needed for some CI environments
            "--disable-dev-shm-usage",  # Needed for some CI environments
            "--disable-gpu",  # Disable GPU for headless mode
        ],
    }


@pytest.fixture
def page(page: Page):
    """Configure page for integration tests."""
    # Set reasonable timeouts for local testing
    page.set_default_timeout(15000)  # 15 seconds
    page.set_default_navigation_timeout(15000)  # 15 seconds

    # Enable console logging to help with debugging
    page.on("console", lambda msg: print(f"🌐 Browser console: {msg.text}"))
    page.on("pageerror", lambda exc: print(f"🚨 Browser error: {exc}"))

    return page


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    current_file = Path(__file__)
    # Navigate up from tests/integration/conftest.py to project root
    return current_file.parent.parent.parent


@pytest.fixture(scope="session")
def test_database(project_root, tmp_path_factory):
    """Set up a temporary test database with known test users."""
    import os
    import subprocess

    logger.info("Setting up integration test database...")

    # Create temporary database in pytest temp directory
    temp_dir = tmp_path_factory.mktemp("integration_test_db")
    test_db_path = temp_dir / "test_integration.db"

    logger.info(f"Creating temporary test database at: {test_db_path}")

    # Initialize database using the script with admin user
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{test_db_path}"
    env["TESTING"] = "true"

    logger.info("Initializing test database with sample data...")
    init_result = subprocess.run(
        [
            "bash",
            "-c",
            (
                f"cd {project_root} && eval $(poetry env activate) && "
                "python scripts/init_db.py --sample-data "
                "--admin-username admin --admin-password admin"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
    )

    if init_result.returncode != 0:
        logger.error(f"Database initialization failed: {init_result.stderr}")
        raise RuntimeError(f"Failed to initialize test database: {init_result.stderr}")

    logger.info("✓ Test database initialized successfully")

    # Create additional test users directly in the database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{test_db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        from kiosk_show_replacement.models import User

        # Create a regular (non-admin) test user
        regular_user = User(
            username="test_user",
            email="test_user@example.com",
            is_admin=False,
            is_active=True,
        )
        regular_user.set_password("test_password")
        session.add(regular_user)

        # Create an inactive user for testing
        inactive_user = User(
            username="inactive_user",
            email="inactive@example.com",
            is_admin=False,
            is_active=False,
        )
        inactive_user.set_password("test_password")
        session.add(inactive_user)

        session.commit()
        logger.info("✓ Additional test users created successfully")
    except Exception:
        logger.exception("Failed to create additional test users")
        session.rollback()
        raise  # Fail fast - test database state must be guaranteed
    finally:
        session.close()
        engine.dispose()

    yield {
        "db_path": str(test_db_path),
        "users": [
            {"username": "admin", "password": "admin", "is_admin": True},
            {"username": "test_user", "password": "test_password", "is_admin": False},
            {
                "username": "inactive_user",
                "password": "test_password",
                "is_admin": False,
                "is_active": False,
            },
        ],
    }

    # Cleanup happens automatically when temp directory is removed by pytest


@pytest.fixture(scope="session")
def servers(project_root, test_database):
    """Start Flask and Vite servers with enhanced logging for testing."""
    server_manager = EnhancedServerManager(project_root)

    try:
        logger.info("Starting servers for integration tests...")
        success = server_manager.start_servers(db_path=test_database["db_path"])

        if not success:
            logger.error("Failed to start servers")
            server_manager._dump_server_logs()
            raise RuntimeError("Server startup failed")

        # Save initial logs after successful startup
        log_file = project_root / "test-results" / "integration-server-logs.txt"
        log_file.parent.mkdir(exist_ok=True)
        server_manager.save_logs_to_file(str(log_file), append=False)
        logger.info("Initial server logs saved")

        # Provide server URLs and manager for tests
        yield {
            **server_manager.get_server_urls(),
            "manager": server_manager,
            "health_check": server_manager.health_check,
            "_log_file": log_file,  # Pass log file path to tests
        }

    finally:
        logger.info("Stopping servers after integration tests...")

        # Save final logs for debugging
        log_file = project_root / "test-results" / "integration-server-logs.txt"
        log_file.parent.mkdir(exist_ok=True)
        server_manager.save_logs_to_file(str(log_file), append=True)

        server_manager.stop_servers()
        logger.info("✓ Integration test cleanup complete")


@pytest.fixture
def enhanced_page(page: Page, servers):
    """Configure page with enhanced debugging and server health monitoring."""
    # Configure page timeouts (Playwright doesn't have default_timeout property)
    page.set_default_timeout(30000)  # 30 seconds

    # Add enhanced console logging
    def handle_console(msg):
        level = msg.type
        text = msg.text
        if level == "error":
            logger.error(f"🚨 Browser console error: {text}")
        elif level == "warning":
            logger.warning(f"⚠️ Browser console warning: {text}")
        else:
            logger.info(f"🌐 Browser console {level}: {text}")

    def handle_page_error(exc):
        logger.error(f"🚨 Browser page error: {exc}")
        # Dump server logs on page errors
        if "manager" in servers:
            servers["manager"]._dump_server_logs()

    def handle_request_failed(request):
        logger.warning(f"🌐 Failed request: {request.method} {request.url}")

    def handle_response(response):
        if response.status >= 400:
            # Response doesn't have method, need to get it from the request
            request = response.request
            logger.warning(f"🌐 HTTP {response.status}: {request.method} {request.url}")

    # Register event handlers
    page.on("console", handle_console)
    page.on("pageerror", handle_page_error)
    page.on("requestfailed", handle_request_failed)
    page.on("response", handle_response)

    # Configure for debugging
    page.set_default_timeout(20000)  # Longer timeout for debugging
    page.set_default_navigation_timeout(20000)

    yield page

    # Cleanup: reset to default timeout
    page.set_default_timeout(30000)  # Reset to reasonable default


@pytest.fixture(autouse=True)
def mark_test_start(servers, request):
    """Mark the start of each test in the server logs."""
    test_name = f"{request.module.__name__}::{request.function.__name__}"

    if "_log_file" in servers:
        try:
            manager = servers["manager"]
            manager.mark_test_start(test_name)
        except Exception as e:
            logger.warning(f"Failed to mark test start for {test_name}: {e}")


@pytest.fixture(autouse=True)
def save_logs_after_test(servers, request):
    """Automatically save server logs after each test for debugging."""
    # This fixture only runs the cleanup part
    yield

    # This runs after each test - mark test end and save logs
    test_name = f"{request.module.__name__}::{request.function.__name__}"

    if "_log_file" in servers:
        try:
            manager = servers["manager"]
            log_file = servers["_log_file"]

            # Mark test end
            manager.mark_test_end(test_name)

            # Append current logs with test information
            with open(str(log_file), "a") as f:
                f.write(f"\n=== AFTER TEST: {test_name} ===\n")

                # Add recent logs from both servers
                flask_logs = manager.get_flask_logs()
                vite_logs = manager.get_vite_logs()

                f.write(f"Flask logs count: {len(flask_logs)}\n")
                f.write(f"Vite logs count: {len(vite_logs)}\n")

                # Add last few lines of each
                if flask_logs:
                    f.write("Recent Flask logs:\n")
                    for log in flask_logs[-5:]:  # Last 5 lines
                        f.write(f"  {log}\n")

                if vite_logs:
                    f.write("Recent Vite logs:\n")
                    for log in vite_logs[-5:]:  # Last 5 lines
                        f.write(f"  {log}\n")

                f.write("=== END AFTER TEST ===\n\n")

        except Exception as e:
            logger.warning(f"Failed to save logs after test {test_name}: {e}")


@pytest.fixture(scope="session")
def http_client(servers):
    """Create HTTP client for making real requests to running Flask server."""
    flask_url = servers["flask_url"]

    class HTTPClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            # Set timeouts for all requests
            self.session.timeout = 30

        def get(self, path, headers=None, **kwargs):
            return self.session.get(f"{self.base_url}{path}", headers=headers, **kwargs)

        def post(self, path, json=None, data=None, headers=None, **kwargs):
            return self.session.post(
                f"{self.base_url}{path}",
                json=json,
                data=data,
                headers=headers,
                **kwargs,
            )

        def put(self, path, json=None, data=None, headers=None, **kwargs):
            return self.session.put(
                f"{self.base_url}{path}",
                json=json,
                data=data,
                headers=headers,
                **kwargs,
            )

        def delete(self, path, headers=None, **kwargs):
            return self.session.delete(
                f"{self.base_url}{path}", headers=headers, **kwargs
            )

        def close(self):
            self.session.close()

    client = HTTPClient(flask_url)
    yield client
    client.close()


@pytest.fixture
def admin_user(http_client, test_database, db_session, db_models):
    """Get admin user credentials and ensure user exists."""
    # Use the admin user created during database initialization
    # Look up the user ID from the database
    user = db_session.query(db_models["User"]).filter_by(username="admin").first()
    return {
        "username": "admin",
        "password": "admin",
        "is_admin": True,
        "id": user.id if user else 1,
    }


@pytest.fixture
def regular_user(http_client, test_database, db_session, db_models):
    """Get regular (non-admin) user credentials."""
    # Look up the user ID from the database
    user = db_session.query(db_models["User"]).filter_by(username="test_user").first()
    return {
        "username": "test_user",
        "password": "test_password",
        "is_admin": False,
        "id": user.id if user else 2,
    }


@pytest.fixture
def inactive_user(http_client, test_database, db_session, db_models):
    """Get inactive user credentials for testing blocked login."""
    # Look up the user ID from the database
    user = (
        db_session.query(db_models["User"]).filter_by(username="inactive_user").first()
    )
    return {
        "username": "inactive_user",
        "password": "test_password",
        "is_admin": False,
        "is_active": False,
        "id": user.id if user else 3,
    }


@pytest.fixture
def auth_headers(http_client, admin_user):
    """Get authentication headers for API requests."""
    # Login to get session cookie
    login_response = http_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )

    if login_response.status_code != 200:
        raise RuntimeError(f"Failed to authenticate: {login_response.text}")

    # Extract session cookie from response
    session_cookie = None
    for cookie in login_response.cookies:
        if cookie.name == "session":
            session_cookie = cookie.value
            break

    if not session_cookie:
        raise RuntimeError("No session cookie received from login")

    # Return headers with session cookie
    return {"Cookie": f"session={session_cookie}", "Content-Type": "application/json"}


@pytest.fixture
def client(http_client):
    """Alias for http_client to maintain compatibility with existing test code."""
    return http_client


@pytest.fixture
def db_session(test_database):
    """Provide a database session that connects to the same database as the Flask server."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create direct connection to the same database file used by Flask server
    db_path = test_database["db_path"]
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        # Always commit any pending changes and close the session
        session.commit()
        session.close()


@pytest.fixture(autouse=True)
def clean_test_data(db_session, db_models):
    """Clean up test data between tests to ensure isolation.

    This fixture runs automatically before each test to ensure clean state.
    It removes all data except the essential admin user needed for authentication.
    """
    import logging

    logger = logging.getLogger(__name__)

    # Clean up before test - remove all test data except admin user
    try:
        # Note: We keep user ID 2 (integration_test_user) for authentication
        # Clean AssignmentHistory before Display (FK dependency)
        db_session.query(db_models["AssignmentHistory"]).delete()
        db_session.query(db_models["Display"]).delete()
        db_session.query(db_models["DisplayConfigurationTemplate"]).filter(
            db_models["DisplayConfigurationTemplate"].id
            != 1  # Keep the default template
        ).delete()
        db_session.commit()
        logger.debug("✓ Test data cleaned up successfully")
    except Exception as e:
        logger.warning(f"Failed to clean test data: {e}")
        db_session.rollback()

    yield  # Let the test run

    # Also clean up after test for good measure
    try:
        db_session.query(db_models["AssignmentHistory"]).delete()
        db_session.query(db_models["Display"]).delete()
        db_session.query(db_models["DisplayConfigurationTemplate"]).filter(
            db_models["DisplayConfigurationTemplate"].id
            != 1  # Keep the default template
        ).delete()
        db_session.commit()
    except Exception as e:
        logger.warning(f"Failed to clean test data after test: {e}")
        db_session.rollback()


@pytest.fixture
def db_models():
    """Provide access to database models for test setup."""
    from kiosk_show_replacement.models import (
        AssignmentHistory,
        Display,
        DisplayConfigurationTemplate,
        Slideshow,
        SlideshowItem,
        User,
        db,
    )

    return {
        "AssignmentHistory": AssignmentHistory,
        "Display": Display,
        "DisplayConfigurationTemplate": DisplayConfigurationTemplate,
        "Slideshow": Slideshow,
        "SlideshowItem": SlideshowItem,
        "User": User,
        "db": db,
    }


@pytest.fixture
def authenticated_page(page: Page, servers: dict, test_database: dict):
    """
    Provide a Playwright page that is already logged in to the admin interface.

    This fixture handles the login flow via the browser so tests can start
    from an authenticated state. Uses the admin user by default.
    """
    from playwright.sync_api import expect

    vite_url = servers["vite_url"]

    # Use the admin user (first user in the list)
    user = test_database["users"][0]  # admin user
    username = user["username"]
    password = user["password"]

    logger.info(f"Authenticating page as user: {username}")

    # Navigate to the login page
    page.goto(vite_url)

    # Wait for login form to appear
    username_field = page.locator(
        "input[name='username'], input[placeholder*='username' i]"
    ).first
    expect(username_field).to_be_visible(timeout=10000)

    # Fill in credentials
    password_field = page.locator(
        "input[name='password'], input[type='password']"
    ).first
    submit_button = page.locator(
        "button[type='submit'], button:has-text('Sign In')"
    ).first

    username_field.fill(username)
    password_field.fill(password)
    submit_button.click()

    # Wait for dashboard to load (login complete)
    page.locator("h1").filter(has_text="Dashboard").wait_for(
        state="visible", timeout=10000
    )

    logger.info("Page authenticated successfully")

    return page


@pytest.fixture
def test_slideshow(http_client, auth_headers):
    """
    Create a test slideshow via API and return its data.

    The slideshow is cleaned up after the test.
    """
    import time

    # Create a unique slideshow name
    slideshow_name = f"Test Slideshow {int(time.time() * 1000)}"

    response = http_client.post(
        "/api/v1/slideshows",
        json={
            "name": slideshow_name,
            "description": "Test slideshow for integration tests",
            "default_item_duration": 10,
            "transition_type": "fade",
            "is_active": True,
        },
        headers=auth_headers,
    )

    if response.status_code not in [200, 201]:
        raise RuntimeError(f"Failed to create test slideshow: {response.text}")

    response_json = response.json()
    # API wraps data in {"success": true, "data": {...}}
    slideshow_data = response_json.get("data", response_json)
    logger.info(
        f"Created test slideshow: {slideshow_data.get('id')} - {slideshow_name}"
    )

    yield slideshow_data

    # Cleanup: delete the slideshow
    try:
        slideshow_id = slideshow_data.get("id")
        if slideshow_id:
            delete_response = http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )
            if delete_response.status_code in [200, 204, 404]:
                logger.info(f"Cleaned up test slideshow: {slideshow_id}")
            else:
                logger.warning(
                    f"Failed to delete test slideshow {slideshow_id}: "
                    f"{delete_response.status_code}"
                )
    except Exception as e:
        logger.warning(f"Error cleaning up test slideshow: {e}")


@pytest.fixture
def test_display(http_client, auth_headers):
    """
    Create a test display via API and return its data.

    The display is cleaned up after the test.
    """
    import time

    # Create a unique display name
    display_name = f"test-display-{int(time.time() * 1000)}"

    response = http_client.post(
        "/api/v1/displays",
        json={
            "name": display_name,
            "description": "Test display for integration tests",
            "location": "Test Location",
            "resolution_width": 1920,
            "resolution_height": 1080,
        },
        headers=auth_headers,
    )

    if response.status_code not in [200, 201]:
        raise RuntimeError(f"Failed to create test display: {response.text}")

    response_json = response.json()
    # API wraps data in {"success": true, "data": {...}}
    display_data = response_json.get("data", response_json)
    logger.info(f"Created test display: {display_data.get('id')} - {display_name}")

    yield display_data

    # Cleanup: delete the display
    try:
        display_id = display_data.get("id")
        if display_id:
            delete_response = http_client.delete(
                f"/api/v1/displays/{display_id}",
                headers=auth_headers,
            )
            if delete_response.status_code in [200, 204, 404]:
                logger.info(f"Cleaned up test display: {display_id}")
            else:
                logger.warning(
                    f"Failed to delete test display {display_id}: "
                    f"{delete_response.status_code}"
                )
    except Exception as e:
        logger.warning(f"Error cleaning up test display: {e}")


@pytest.fixture
def test_assets_path(project_root):
    """Return the path to the test assets directory."""
    return project_root / "tests" / "assets"
