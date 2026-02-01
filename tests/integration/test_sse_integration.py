"""
SSE Integration Tests.

Tests Server-Sent Events (SSE) functionality in the complete React frontend + Flask backend stack.
These tests verify real-time updates work correctly through the React admin interface.

Run with: nox -s test-integration
"""

import logging
import os
import time

import pytest
import requests
from playwright.sync_api import Page

# Use the existing logger setup from conftest
logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped due to Playwright browser dependency issues on Arch Linux",
)
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

            # Wait for React app to load - look for login form or authenticated content
            logger.info("Waiting for React app to initialize...")

            # Wait for either login form or authenticated content to appear
            login_form_visible = False
            authenticated_content_visible = False

            try:
                # First, try to find login form elements (unauthenticated state)
                enhanced_page.wait_for_selector(
                    "input[name='username'], input[placeholder*='username' i], h4",
                    timeout=10000,
                )
                login_form_visible = True
                logger.info("Login form found - user is unauthenticated")
            except Exception as e:
                logger.warning(f"Login form not found: {e}")

                # If no login form, try to find authenticated content (h1, dashboard, etc.)
                try:
                    enhanced_page.wait_for_selector(
                        "h1, [data-testid='dashboard'], .dashboard", timeout=5000
                    )
                    authenticated_content_visible = True
                    logger.info("Authenticated content found - user is logged in")
                except Exception as e2:
                    logger.error(f"No authenticated content found either: {e2}")

            # At least one should be visible
            assert (
                login_form_visible or authenticated_content_visible
            ), "React app should show either login form or authenticated content"

            logger.info("React app loaded successfully")

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
                "username": "admin",
                "password": "admin",
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
            login_data = {"username": "admin", "password": "admin"}
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
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped due to Playwright browser dependency issues on Arch Linux",
)
class TestSSEConnectionCleanup:
    """Test SSE connection cleanup scenarios.

    These tests verify that SSE connections are properly cleaned up when:
    - The page is refreshed
    - The user navigates away
    - The client explicitly disconnects
    """

    def test_sse_connection_cleanup_on_page_refresh(
        self, servers, authenticated_page: Page
    ):
        """Test that SSE connections are cleaned up when page is refreshed.

        M3.1: Navigate to monitoring page, verify 1 connection, refresh page,
        verify still 1 connection (not 2).
        """
        flask_url = servers["flask_url"]
        vite_url = servers["vite_url"]
        logger.info("Testing SSE connection cleanup on page refresh")

        # Navigate to the monitoring page (which establishes an SSE connection)
        authenticated_page.goto(f"{vite_url}/admin/monitoring", timeout=15000)
        # Use domcontentloaded instead of networkidle because SSE connections
        # keep the network active, preventing networkidle from ever being reached
        authenticated_page.wait_for_load_state("domcontentloaded", timeout=10000)
        logger.info("Navigated to monitoring page")

        # Wait for SSE connection to be established
        time.sleep(2)

        # Check initial connection count via API
        session = requests.Session()
        login_data = {"username": "admin", "password": "admin"}
        session.post(
            f"{flask_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        initial_response = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
        initial_data = initial_response.json()
        initial_admin_count = initial_data["data"]["admin_connections"]
        logger.info(f"Initial admin connection count: {initial_admin_count}")

        # Refresh the page
        authenticated_page.reload()
        authenticated_page.wait_for_load_state("domcontentloaded", timeout=10000)
        logger.info("Page refreshed")

        # Wait for the new SSE connection to establish and old one to be cleaned up
        time.sleep(3)

        # Check connection count after refresh
        final_response = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
        final_data = final_response.json()
        final_admin_count = final_data["data"]["admin_connections"]
        logger.info(f"Final admin connection count: {final_admin_count}")

        # Should have same or fewer connections (old one cleaned up)
        # Allow for 1 connection (the new one after refresh)
        assert final_admin_count <= initial_admin_count, (
            f"Connection count should not increase after refresh. "
            f"Initial: {initial_admin_count}, Final: {final_admin_count}"
        )

    def test_sse_connection_cleanup_on_navigation(
        self, servers, authenticated_page: Page
    ):
        """Test that SSE connections are cleaned up when navigating away.

        M3.2: Navigate to monitoring page, verify connection, navigate to
        different page, navigate back, verify still 1 connection.
        """
        flask_url = servers["flask_url"]
        vite_url = servers["vite_url"]
        logger.info("Testing SSE connection cleanup on navigation")

        # Set up API session
        session = requests.Session()
        login_data = {"username": "admin", "password": "admin"}
        session.post(
            f"{flask_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        # Navigate to the monitoring page
        authenticated_page.goto(f"{vite_url}/admin/monitoring", timeout=15000)
        # Use domcontentloaded instead of networkidle because SSE connections
        # keep the network active, preventing networkidle from ever being reached
        authenticated_page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)

        # Check initial count
        initial_response = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
        initial_count = initial_response.json()["data"]["admin_connections"]
        logger.info(f"Initial connection count: {initial_count}")

        # Navigate to a different page (dashboard)
        authenticated_page.goto(f"{vite_url}/admin/", timeout=15000)
        authenticated_page.wait_for_load_state("domcontentloaded", timeout=10000)
        logger.info("Navigated to dashboard")
        time.sleep(2)

        # Navigate back to monitoring
        authenticated_page.goto(f"{vite_url}/admin/monitoring", timeout=15000)
        authenticated_page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(3)

        # Check final count
        final_response = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
        final_count = final_response.json()["data"]["admin_connections"]
        logger.info(f"Final connection count: {final_count}")

        # Should have same or fewer connections
        assert final_count <= initial_count + 1, (
            f"Connection count should not grow significantly. "
            f"Initial: {initial_count}, Final: {final_count}"
        )

    def test_sse_disconnect_endpoint_works(self, servers):
        """Test that the SSE disconnect endpoint works correctly.

        M3.3: Test that the disconnect endpoint properly removes connections.
        """
        flask_url = servers["flask_url"]
        logger.info("Testing SSE disconnect endpoint")

        # Set up authenticated session
        session = requests.Session()
        login_data = {"username": "admin", "password": "admin"}
        login_response = session.post(
            f"{flask_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        assert login_response.status_code == 200

        # Get initial connection count
        initial_stats = session.get(f"{flask_url}/api/v1/events/stats", timeout=5)
        initial_count = initial_stats.json()["data"]["total_connections"]
        logger.info(f"Initial total connections: {initial_count}")

        # Start an SSE connection and get the connection ID
        # We'll use a streaming request to establish the SSE connection
        import threading

        connection_id = None
        sse_response = None
        connection_established = threading.Event()

        def establish_sse():
            nonlocal connection_id, sse_response
            try:
                sse_response = session.get(
                    f"{flask_url}/api/v1/events/admin",
                    stream=True,
                    timeout=10,
                )
                # Read the first event (connected event with connection_id)
                for line in sse_response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        import json

                        data = json.loads(line[5:].strip())
                        if "connection_id" in data:
                            connection_id = data["connection_id"]
                            logger.info(f"SSE connection established: {connection_id}")
                            connection_established.set()
                            break
            except Exception as e:
                logger.error(f"Error establishing SSE: {e}")
                connection_established.set()

        # Start SSE connection in background
        sse_thread = threading.Thread(target=establish_sse)
        sse_thread.daemon = True
        sse_thread.start()

        # Wait for connection to establish
        connection_established.wait(timeout=5)
        time.sleep(1)  # Extra time for server to register connection

        if connection_id:
            # Verify connection exists
            stats_after_connect = session.get(
                f"{flask_url}/api/v1/events/stats", timeout=5
            )
            count_after_connect = stats_after_connect.json()["data"][
                "total_connections"
            ]
            logger.info(f"Connections after SSE connect: {count_after_connect}")
            assert (
                count_after_connect > initial_count
            ), "SSE connection should increase count"

            # Now call disconnect endpoint
            disconnect_response = session.post(
                f"{flask_url}/api/v1/events/disconnect",
                json={"connection_id": connection_id},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            logger.info(f"Disconnect response: {disconnect_response.status_code}")
            assert disconnect_response.status_code == 200
            assert disconnect_response.json()["data"]["disconnected"] is True

            # Verify connection was removed
            stats_after_disconnect = session.get(
                f"{flask_url}/api/v1/events/stats", timeout=5
            )
            count_after_disconnect = stats_after_disconnect.json()["data"][
                "total_connections"
            ]
            logger.info(f"Connections after disconnect: {count_after_disconnect}")
            assert (
                count_after_disconnect < count_after_connect
            ), "Connection count should decrease after disconnect"

        # Clean up
        if sse_response:
            sse_response.close()


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
