"""
Standalone Simple SSE Test.

Tests basic functionality without complex dependencies.
"""

import logging
import subprocess
import time
import threading
from pathlib import Path

import pytest


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def flask_server():
    """Start a simple Flask server for testing."""
    project_root = Path(__file__).parent.parent.parent
    logger.info(f"Project root: {project_root}")
    
    # Start Flask server
    process = subprocess.Popen(
        ["poetry", "run", "python", "-m", "kiosk_show_replacement.app"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"FLASK_ENV": "testing", "PORT": "5001"}
    )
    
    # Wait a bit for server to start
    time.sleep(2)
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:5001", timeout=5)
        logger.info(f"Server health check: {response.status_code}")
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
    
    yield "http://localhost:5001"
    
    # Cleanup
    logger.info("Shutting down Flask server")
    process.terminate()
    process.wait(timeout=5)


def test_flask_server_starts(flask_server):
    """Test that Flask server starts correctly."""
    import requests
    
    logger.info(f"Testing server at: {flask_server}")
    
    try:
        response = requests.get(flask_server, timeout=10)
        logger.info(f"Server responded with status: {response.status_code}")
        assert response.status_code in [200, 302, 404]  # Any valid HTTP response is good
        
    except Exception as e:
        logger.error(f"Server test failed: {e}")
        raise


def test_basic_playwright_functionality(page):
    """Test basic Playwright functionality without server dependencies."""
    logger.info("Testing basic Playwright functionality")
    
    try:
        # Test basic navigation to a simple page
        page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
        
        # Check that page loaded
        title = page.text_content("h1")
        assert title == "Test Page"
        
        logger.info("Basic Playwright test passed")
        
    except Exception as e:
        logger.error(f"Playwright test failed: {e}")
        page.screenshot(path="playwright_basic_error.png")
        raise
