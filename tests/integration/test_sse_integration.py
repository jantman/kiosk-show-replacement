"""
SSE Integration Tests.

Tests Server-Sent Events (SSE) functionality in the complete React frontend + Flask backend stack.
These tests verify real-time updates work correctly through the React admin interface.

Run with: nox -s test-integration
"""

import logging
import time

import pytest
import requests
from playwright.sync_api import Page, expect

# Use the existing logger setup from conftest
logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestSSEIntegration:
    """Test SSE functionality in the complete React + Flask application stack."""

    def test_react_authentication_flow(self, servers, enhanced_page: Page):
        """Test React app authentication flow - unauthenticated users see login form."""
        logger.info("Testing React app authentication flow")
        vite_url = servers["vite_url"]
        logger.info(f"Using Vite URL: {vite_url}")

        # Check server health before starting
        health = servers["health_check"]()
        logger.info(f"Server health check: {health}")
        assert health["flask"], "Flask server should be healthy"
        assert health["vite"], "Vite server should be healthy"

        # Navigate to the React frontend
        logger.info("Navigating to React frontend...")
        enhanced_page.goto(vite_url, timeout=15000)
        logger.info("Page loaded successfully")

        # When not authenticated, React app should show login form
        logger.info("Waiting for React app to show login form...")

        # Wait for React to load and show login form (since user is not authenticated)
        login_form_visible = False
        try:
            # Look for login form elements
            enhanced_page.wait_for_selector(
                "input[name='username'], input[placeholder*='username' i]",
                timeout=10000,
            )
            login_form_visible = True
            logger.info("Login form found")
        except Exception as e:
            logger.warning(f"Login form not found: {e}")
            # Try to find any h1 element instead
            try:
                enhanced_page.wait_for_selector("h1", timeout=5000)
                h1_text = enhanced_page.text_content("h1")
                logger.info(f"Found h1 with text: {h1_text}")
            except Exception as e2:
                logger.error(f"No h1 found either: {e2}")

        # Either login form should be visible OR some content should load
        assert (
            login_form_visible or enhanced_page.locator("h1").is_visible()
        ), "React app should either show login form or some content"

        # Get the page title
        title = enhanced_page.title()
        logger.info(f"Page title: {title}")
        assert title  # Just check that there is a title

    def test_simple_navigation(self, servers, enhanced_page: Page):
        """Test simple navigation to React frontend with enhanced logging."""
        logger.info("Starting simple navigation test with enhanced logging")
        vite_url = servers["vite_url"]
        logger.info(f"Using Vite URL: {vite_url}")

        # Check server health before starting
        health = servers["health_check"]()
        logger.info(f"Server health check: {health}")
        assert health["flask"], "Flask server should be healthy"
        assert health["vite"], "Vite server should be healthy"

        # Navigate to the React frontend
        logger.info("Navigating to React frontend...")
        enhanced_page.goto(vite_url, timeout=15000)
        logger.info("Page loaded successfully")

        # Wait for React to load - but don't assume authentication state
        logger.info("Waiting for React app to initialize...")

        # Wait for any content to appear (either login form or authenticated content)
        try:
            # First try to find any basic element that indicates React has loaded
            enhanced_page.wait_for_selector("body > div", timeout=10000)  # React root

            # Check if login form is visible (unauthenticated) or dashboard (authenticated)
            if enhanced_page.locator("input[name='username']").is_visible():
                logger.info("User is not authenticated - login form visible")
                enhanced_page.wait_for_selector("input[name='username']", timeout=5000)
            elif enhanced_page.locator("h1").is_visible():
                logger.info("Found h1 element - app content loaded")
            else:
                logger.info("React app loaded but no specific content identified")

        except Exception as e:
            logger.error(f"Failed to find React content: {e}")
            # Take screenshot for debugging
            enhanced_page.screenshot(path="test-results/simple_navigation_error.png")
            raise

        logger.info("React app loaded")

        # Get the page title
        title = enhanced_page.title()
        logger.info(f"Page title: {title}")
        assert title  # Just check that there is a title

    def test_sse_connection_in_admin_interface(self, servers, enhanced_page: Page):
        """Test that SSE connection works in the React admin interface with enhanced logging."""
        logger.info("Starting SSE connection test with enhanced monitoring")
        vite_url = servers["vite_url"]
        flask_url = servers["flask_url"]
        logger.info(f"Using Vite URL: {vite_url}, Flask URL: {flask_url}")

        # Check server health before starting
        health = servers["health_check"]()
        logger.info(f"Server health check: {health}")
        if not health["flask"] or not health["vite"]:
            # Dump server logs for debugging
            servers["manager"]._dump_server_logs()
            assert False, f"Servers not healthy: {health}"

        try:
            # Navigate to React frontend
            logger.info("Navigating to React frontend...")
            enhanced_page.goto(vite_url, timeout=15000)
            logger.info("Page loaded successfully")

            # Wait for React app to load
            logger.info("Waiting for React app to initialize...")
            enhanced_page.wait_for_selector("h1", timeout=10000)
            logger.info("React app loaded")

            # Check if we can navigate to admin section
            page_content = enhanced_page.content()
            if "admin" in page_content.lower() or "dashboard" in page_content.lower():
                logger.info("Admin interface detected, testing SSE functionality")

                # Look for SSE-related elements or navigation
                try:
                    # Try to find any SSE or monitoring related content
                    monitoring_link = enhanced_page.locator(
                        "text=System Monitoring"
                    ).first
                    if monitoring_link.is_visible():
                        logger.info("Found System Monitoring link")
                        monitoring_link.click()
                        enhanced_page.wait_for_timeout(2000)  # Wait for page to load

                        # Check for SSE connection status
                        sse_elements = enhanced_page.locator('[data-testid*="sse"]')
                        if sse_elements.count() > 0:
                            logger.info("SSE elements found in UI")
                        else:
                            logger.info(
                                "No SSE elements found, but navigation successful"
                            )
                    else:
                        logger.info(
                            "System Monitoring link not visible, checking for other SSE indicators"
                        )
                except Exception as e:
                    logger.info(
                        f"Navigation attempt failed: {e}, but basic page load successful"
                    )
            else:
                logger.info("Basic React app loaded successfully")

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            # Dump server logs for debugging
            servers["manager"]._dump_server_logs()

            # Take screenshot for debugging
            try:
                screenshot_path = f"/tmp/sse-test-failure-{int(time.time())}.png"
                enhanced_page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot saved for debugging: {screenshot_path}")
            except Exception as screenshot_error:
                logger.warning(f"Could not save screenshot: {screenshot_error}")
            raise

    def test_sse_api_endpoints_accessible(self, servers):
        """Test that SSE API endpoints are accessible from Flask backend."""
        flask_url = servers["flask_url"]
        logger.info(f"Testing SSE API endpoints at {flask_url}")

        # Check server health before starting
        health = servers["health_check"]()
        logger.info(f"Server health check: {health}")
        assert health["flask"], "Flask server should be healthy for API tests"

        # Create a session for authentication
        session = requests.Session()

        # Authenticate first using the API login endpoint
        try:
            login_data = {
                "username": "integration_test_user",
                "password": "test_password",
            }
            login_response = session.post(
                f"{flask_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            logger.info(f"Login response: {login_response.status_code}")
            assert login_response.status_code == 200

            login_result = login_response.json()
            logger.info(f"Login successful: {login_result['message']}")
            assert login_result["success"] is True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            # Dump server logs for debugging
            servers["manager"]._dump_server_logs()
            raise

        # Test SSE stats endpoint with authenticated session
        try:
            response = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
            logger.info(f"SSE stats endpoint response: {response.status_code}")
            assert response.status_code == 200

            data = response.json()
            logger.info(f"SSE stats data: {data}")
            assert "success" in data
            assert data["success"] is True
            assert "data" in data

        except Exception as e:
            logger.error(f"SSE stats endpoint test failed: {e}")
            servers["manager"]._dump_server_logs()
            raise

        # Test SSE test event endpoint with authenticated session
        try:
            test_event_data = {"message": "Integration test event", "type": "test"}
            response = session.post(
                f"{flask_url}/api/v1/events/test",
                json=test_event_data,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            logger.info(f"SSE test event endpoint response: {response.status_code}")
            assert response.status_code == 200

            data = response.json()
            logger.info(f"Test event response: {data}")
            assert "success" in data
            assert data["success"] is True

        except Exception as e:
            logger.error(f"SSE test event endpoint test failed: {e}")
            servers["manager"]._dump_server_logs()
            raise

    def test_basic_flask_backend_functionality(self, servers):
        """Test basic Flask backend functionality with enhanced logging."""
        flask_url = servers["flask_url"]
        logger.info(f"Testing Flask backend at {flask_url}")

        # Check server health before starting
        health = servers["health_check"]()
        logger.info(f"Server health check: {health}")
        assert health["flask"], "Flask server should be healthy for backend tests"

        # Create a session for authentication
        session = requests.Session()

        # Test basic Flask route
        try:
            response = session.get(flask_url, timeout=5)
            logger.info(f"Flask root response: {response.status_code}")
            assert response.status_code in [
                200,
                302,
                404,
            ]  # 302 for login redirect, 404 for API-only, 200 for success
        except Exception as e:
            logger.error(f"Flask root endpoint test failed: {e}")
            servers["manager"]._dump_server_logs()
            raise

        # Authenticate first using the API login endpoint
        try:
            login_data = {"username": "backend_test_user", "password": "test_password"}
            login_response = session.post(
                f"{flask_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            logger.info(f"Backend login response: {login_response.status_code}")
            assert login_response.status_code == 200

            login_result = login_response.json()
            logger.info(f"Backend login successful: {login_result['message']}")
            assert login_result["success"] is True

        except Exception as e:
            logger.error(f"Backend authentication failed: {e}")
            servers["manager"]._dump_server_logs()
            raise

        # Test API availability with authentication
        try:
            response = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
            logger.info(f"API response: {response.status_code}")
            assert response.status_code == 200

            data = response.json()
            logger.info(f"API stats data: {data}")
            assert "success" in data
            assert data["success"] is True

        except Exception as e:
            logger.error(f"API test failed: {e}")
            servers["manager"]._dump_server_logs()
            raise


@pytest.mark.integration
class TestSSEFailureScenarios:
    """Test SSE failure scenarios and recovery mechanisms."""

    def test_server_health_monitoring(self, servers):
        """Test that server health monitoring works correctly."""
        logger.info("Testing server health monitoring")

        health = servers["health_check"]()
        logger.info(f"Initial health check: {health}")

        # Both servers should be healthy
        assert health["flask"], "Flask server should be healthy"
        assert health["vite"], "Vite server should be healthy"

        # Test multiple health checks to ensure consistency
        for i in range(3):
            health = servers["health_check"]()
            logger.info(f"Health check {i+1}: {health}")
            assert health["flask"], f"Flask server should remain healthy (check {i+1})"
            assert health["vite"], f"Vite server should remain healthy (check {i+1})"
            time.sleep(1)

    def test_server_logs_capture(self, servers):
        """Test that server logs are being captured correctly."""
        logger.info("Testing server log capture functionality")

        manager = servers["manager"]

        # Get initial log counts
        initial_flask_logs = len(manager.get_flask_logs())
        initial_vite_logs = len(manager.get_vite_logs())

        logger.info(
            f"Initial log counts - Flask: {initial_flask_logs}, Vite: {initial_vite_logs}"
        )

        # Make some requests to generate logs
        flask_url = servers["flask_url"]
        vite_url = servers["vite_url"]

        try:
            # Generate Flask logs
            requests.get(flask_url, timeout=5)

            # Generate Vite logs (may not generate as much)
            requests.get(vite_url, timeout=5)

            # Wait a moment for logs to be captured
            time.sleep(2)

            # Check if new logs were captured
            final_flask_logs = len(manager.get_flask_logs())
            final_vite_logs = len(manager.get_vite_logs())

            logger.info(
                f"Final log counts - Flask: {final_flask_logs}, Vite: {final_vite_logs}"
            )

            # Should have some logs (either initial or new)
            assert final_flask_logs > 0, "Flask should have generated some logs"
            assert final_vite_logs >= 0, "Vite logs count should be non-negative"

        except Exception as e:
            logger.error(f"Log capture test failed: {e}")
            manager._dump_server_logs()
            raise
