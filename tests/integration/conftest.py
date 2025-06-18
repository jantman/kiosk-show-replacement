"""
Configuration for integration tests using Playwright.

This configures Playwright to use the system browser and provides
any additional setup needed for full-stack integration testing.
"""

import pytest
from playwright.sync_api import Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for integration tests."""
    return {
        **browser_context_args,
        # Don't ignore HTTPS errors in case we need to test with SSL
        "ignore_https_errors": True,
        # Set a reasonable viewport size
        "viewport": {"width": 1280, "height": 720},
        # Enable console logging
        "record_video_size": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="session") 
def browser_type_launch_args(browser_type_launch_args):
    """Configure browser launch arguments for integration tests."""
    return {
        **browser_type_launch_args,
        # Use system browser (configured via environment variable in nox)
        # Add any additional Chrome arguments needed
        "args": [
            "--no-sandbox",  # Needed for some CI environments
            "--disable-dev-shm-usage",  # Needed for some CI environments
            # Uncomment the next line to run in headed mode for debugging
            # "--start-maximized",
        ],
    }


@pytest.fixture
def page(page: Page):
    """Configure page for integration tests."""
    # Set longer timeout for integration tests since we're starting servers
    page.set_default_timeout(30000)  # 30 seconds
    page.set_default_navigation_timeout(30000)  # 30 seconds
    
    # Enable console logging to help with debugging
    page.on("console", lambda msg: print(f"🌐 Browser console: {msg.text}"))
    page.on("pageerror", lambda exc: print(f"🚨 Browser error: {exc}"))
    
    return page
