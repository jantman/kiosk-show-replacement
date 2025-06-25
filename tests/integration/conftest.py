"""
Configuration for integration tests using Playwright.

This configures Playwright to test our Flask application with browser automation
and provides enhanced server management with comprehensive logging.
"""

import pytest
import logging
import sys
import os
from pathlib import Path
from playwright.sync_api import Page

# Add the tests directory to the Python path for imports
current_dir = Path(__file__).parent
tests_dir = current_dir.parent
sys.path.insert(0, str(tests_dir))

from integration.server_manager import EnhancedServerManager

# Import live_server fixture from pytest-flask
pytest_plugins = ["flask"]

# Configure comprehensive logging for integration tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app():
    """Create Flask app for pytest-flask live_server fixture."""
    from kiosk_show_replacement.app import create_app, db
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "integration-test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })
    
    with app.app_context():
        db.create_all()
        
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
def test_database(project_root):
    """Set up a test database with known test users."""
    import os
    import subprocess
    
    logger.info("Setting up integration test database...")
    
    # Create test database path
    test_db_path = project_root / "instance" / "test_integration.db"
    test_db_path.parent.mkdir(exist_ok=True)

    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()

    # Initialize database using the script
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
                "python scripts/init_db.py --sample-data"
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
    
    yield {
        "db_path": str(test_db_path),
        "users": [
            {"username": "integration_test_user", "password": "test_password"},
            {"username": "backend_test_user", "password": "test_password"},
        ]
    }

    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


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
            "_log_file": log_file  # Pass log file path to tests
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
            logger.warning(f"🌐 HTTP {response.status}: {request.method} {response.url}")
    
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
            with open(str(log_file), 'a') as f:
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
