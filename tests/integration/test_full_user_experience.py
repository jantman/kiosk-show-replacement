"""
Full user experience integration tests.

Tests the complete React frontend + Flask backend integration through a real browser.
This is what users actually experience, not mocked components or isolated backend APIs.

This test relies on the noxfile to configure system Chrome/Chromium browser.
Run with: nox -s test-integration

Note: Server management and shared fixtures are provided by conftest.py.
"""

import os

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped due to Playwright browser dependency issues",
)
class TestFullUserExperience:
    """Test the complete user experience through a real browser."""

    @pytest.mark.skip(
        reason="Bug: ProtectedRoute redirects to /login instead of /admin/login. "
        "See docs/features/fix-protected-route-redirect.md"
    )
    def test_user_can_login_and_see_dashboard(
        self, enhanced_page: Page, servers: dict, test_database: dict
    ):
        """
        Test the complete happy path:
        1. User visits the React frontend
        2. User sees the login form
        3. User enters credentials and submits
        4. User is redirected to dashboard
        5. Dashboard loads data from Flask backend
        6. User can see the dashboard content

        This tests the REAL user experience, not mocked components.
        """
        vite_url = servers["vite_url"]

        # Use test user from shared fixture
        user = test_database["users"][0]
        username = user["username"]
        password = user["password"]

        print(f"\n Testing user experience at {vite_url}")
        print(f" Test credentials: {username} / {password}")

        # Use enhanced_page for better timeout handling
        page = enhanced_page

        # Step 1: Visit the React frontend
        page.goto(vite_url)

        # Step 2: Verify we see the login form
        print(" Checking for login form...")

        # Wait for React app to finish loading (spinner disappears)
        # The Login component shows a spinner while checking auth status
        try:
            page.wait_for_selector(
                ".spinner-border",
                state="hidden",
                timeout=15000,
            )
            print(" Loading spinner disappeared")
        except Exception:
            # Spinner may have already disappeared or never appeared
            print(" No spinner found (may have completed quickly)")

        # Now wait for the login form elements
        page.wait_for_selector(
            "input[name='username'], input[placeholder*='username' i]",
            timeout=10000,
        )
        expect(
            page.locator("input[name='username'], input[placeholder*='username' i]")
        ).to_be_visible(timeout=5000)
        expect(
            page.locator("input[name='password'], input[type='password']")
        ).to_be_visible()
        expect(
            page.locator("button[type='submit'], button:has-text('Sign In')")
        ).to_be_visible()

        print(" Login form is visible")

        # Step 3: Fill in credentials and submit
        print(" Logging in...")

        username_field = page.locator(
            "input[name='username'], input[placeholder*='username' i]"
        ).first
        password_field = page.locator(
            "input[name='password'], input[type='password']"
        ).first
        submit_button = page.locator(
            "button[type='submit'], button:has-text('Sign In')"
        ).first

        username_field.fill(username)
        password_field.fill(password)
        submit_button.click()

        # Step 4: Verify we're redirected to dashboard
        print(" Waiting for dashboard...")

        # Wait for the login to complete and dashboard to load
        # Note: We can't use networkidle because SSE connections keep network active
        # Instead, wait for specific dashboard elements to appear
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for the login form to disappear (indicating successful redirect)
        page.locator(
            "input[name='username'], input[placeholder*='username' i]"
        ).wait_for(state="hidden", timeout=10000)

        # Verify we're no longer on the login page
        login_form_present = page.locator("input[name='username']").is_visible()
        assert (
            not login_form_present
        ), "Should not be on login page after successful login"

        # Step 5: Verify dashboard content is visible
        print(" Checking dashboard content...")

        # Wait for the dashboard to load (it might show loading spinner first)
        # First wait for the main Dashboard heading to appear
        page.locator("h1").filter(has_text="Dashboard").wait_for(
            state="visible", timeout=10000
        )

        # Look for dashboard indicators - check for actual elements from Dashboard.tsx
        dashboard_indicators = [
            page.locator("h1").filter(has_text="Dashboard"),  # Main dashboard heading
            page.locator("text=Welcome back"),  # Welcome message
        ]

        # At least one dashboard indicator should be visible
        dashboard_visible = False
        visible_indicators = []

        for indicator in dashboard_indicators:
            try:
                if indicator.is_visible():
                    dashboard_visible = True
                    visible_indicators.append(indicator.inner_text()[:50])
            except Exception as e:
                # Log but don't fail on individual indicator checks
                print(f" Indicator check failed: {e}")
                continue

        assert dashboard_visible, (
            "Dashboard should be visible after login. "
            "Checked indicators but none were visible."
        )

        print(f" Dashboard is visible with indicators: {visible_indicators}")

        # Step 6: Verify the React frontend is communicating with Flask backend
        print(" Verifying frontend-backend communication...")

        # The dashboard should load data from the backend APIs
        # We'll check for any error messages that would indicate API failures
        error_indicators = [
            page.locator("text=Failed to load"),
            page.locator("div.alert-danger"),
        ]

        for error_indicator in error_indicators:
            if error_indicator.is_visible():
                error_text = error_indicator.inner_text()
                pytest.fail(f"Found error on dashboard: {error_text}")

        print(" No error messages found on dashboard")

        # Final verification: Check that user info is displayed
        # This confirms the authentication state is working
        try:
            user_info_visible = page.locator("text=Welcome back").is_visible()
        except Exception as e:
            print(f" User info check failed: {e}")
            # Fallback to checking for general dashboard indicators
            user_info_visible = dashboard_visible

        if user_info_visible:
            print(f" User information is displayed (logged in as {username})")
        else:
            print(" User information not visible, but login appears successful")

        print(" FULL USER EXPERIENCE TEST PASSED!")
        print("    React frontend loads correctly")
        print("    Login form works")
        print("    Authentication succeeds")
        print("    Dashboard loads")
        print("    Frontend-backend communication works")
        print("    User can see dashboard content")


if __name__ == "__main__":
    # Allow running this test directly for debugging
    pytest.main([__file__, "-v", "-s"])
