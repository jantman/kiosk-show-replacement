"""
Integration tests for authentication flows.

Tests the complete authentication flow through the UI and API,
including login, logout, profile updates, and password changes.
"""

import logging

logger = logging.getLogger(__name__)


class TestLoginFlow:
    """Test login authentication flow through the UI."""

    def test_login_with_valid_credentials(self, page, servers, test_database):
        """Test successful login with valid credentials."""
        from playwright.sync_api import expect

        vite_url = servers["vite_url"]
        admin_user = test_database["users"][0]  # admin user

        # Navigate to login page
        page.goto(vite_url)

        # Wait for login form
        username_field = page.locator("input[name='username']")
        expect(username_field).to_be_visible(timeout=10000)

        # Fill in valid credentials
        password_field = page.locator("input[name='password']")
        submit_button = page.locator("button[type='submit']")

        username_field.fill(admin_user["username"])
        password_field.fill(admin_user["password"])
        submit_button.click()

        # Wait for dashboard to load (indicates successful login)
        dashboard_heading = page.locator("h1").filter(has_text="Dashboard")
        expect(dashboard_heading).to_be_visible(timeout=10000)

        logger.info("Login with valid credentials succeeded")

    def test_login_with_invalid_username(self, page, servers):
        """Test login fails with non-existent username."""
        from playwright.sync_api import expect

        vite_url = servers["vite_url"]

        # Navigate to login page
        page.goto(vite_url)

        # Wait for login form
        username_field = page.locator("input[name='username']")
        expect(username_field).to_be_visible(timeout=10000)

        # Fill in invalid credentials
        password_field = page.locator("input[name='password']")
        submit_button = page.locator("button[type='submit']")

        username_field.fill("nonexistent_user")
        password_field.fill("any_password")
        submit_button.click()

        # Wait for error message
        error_alert = page.locator(".alert-danger")
        expect(error_alert).to_be_visible(timeout=5000)

        # Should still be on login page
        expect(username_field).to_be_visible()

        logger.info("Login with invalid username correctly rejected")

    def test_login_with_wrong_password(self, page, servers, test_database):
        """Test login fails with wrong password."""
        from playwright.sync_api import expect

        vite_url = servers["vite_url"]
        admin_user = test_database["users"][0]

        # Navigate to login page
        page.goto(vite_url)

        # Wait for login form
        username_field = page.locator("input[name='username']")
        expect(username_field).to_be_visible(timeout=10000)

        # Fill in wrong password
        password_field = page.locator("input[name='password']")
        submit_button = page.locator("button[type='submit']")

        username_field.fill(admin_user["username"])
        password_field.fill("wrong_password")
        submit_button.click()

        # Wait for error message
        error_alert = page.locator(".alert-danger")
        expect(error_alert).to_be_visible(timeout=5000)

        # Should still be on login page
        expect(username_field).to_be_visible()

        logger.info("Login with wrong password correctly rejected")

    def test_login_with_inactive_user(self, page, servers, test_database):
        """Test login fails for inactive user."""
        from playwright.sync_api import expect

        vite_url = servers["vite_url"]
        inactive_user = test_database["users"][2]  # inactive_user

        # Navigate to login page
        page.goto(vite_url)

        # Wait for login form
        username_field = page.locator("input[name='username']")
        expect(username_field).to_be_visible(timeout=10000)

        # Fill in inactive user credentials
        password_field = page.locator("input[name='password']")
        submit_button = page.locator("button[type='submit']")

        username_field.fill(inactive_user["username"])
        password_field.fill(inactive_user["password"])
        submit_button.click()

        # Wait for error message
        error_alert = page.locator(".alert-danger")
        expect(error_alert).to_be_visible(timeout=5000)

        # Should still be on login page
        expect(username_field).to_be_visible()

        logger.info("Login with inactive user correctly rejected")


class TestLogoutFlow:
    """Test logout flow through the UI."""

    def test_logout_redirects_to_login(self, authenticated_page, servers):
        """Test that logout redirects to login page."""
        from playwright.sync_api import expect

        page = authenticated_page

        # Click on user dropdown
        user_dropdown = page.locator("#user-dropdown")
        user_dropdown.click()

        # Click Sign Out
        sign_out_button = page.locator("text=Sign Out")
        sign_out_button.click()

        # Should be redirected to login page
        username_field = page.locator("input[name='username']")
        expect(username_field).to_be_visible(timeout=10000)

        logger.info("Logout correctly redirected to login page")


class TestLoginAPI:
    """Test login authentication through the API."""

    def test_api_login_success(self, http_client, admin_user):
        """Test successful login through API."""
        response = http_client.post(
            "/api/v1/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["username"] == admin_user["username"]

        logger.info("API login with valid credentials succeeded")

    def test_api_login_invalid_username(self, http_client):
        """Test login fails with non-existent username."""
        response = http_client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "any_password"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

        logger.info("API login with invalid username correctly rejected")

    def test_api_login_wrong_password(self, http_client, admin_user):
        """Test login fails with wrong password."""
        response = http_client.post(
            "/api/v1/auth/login",
            json={"username": admin_user["username"], "password": "wrong_password"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

        logger.info("API login with wrong password correctly rejected")

    def test_api_login_inactive_user(self, http_client, inactive_user):
        """Test login fails for inactive user."""
        response = http_client.post(
            "/api/v1/auth/login",
            json={
                "username": inactive_user["username"],
                "password": inactive_user["password"],
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

        logger.info("API login with inactive user correctly rejected")


class TestProfileAPI:
    """Test profile update functionality through the API."""

    def test_update_profile_email(self, http_client, auth_headers):
        """Test updating user email through API."""
        new_email = "updated_email@example.com"

        response = http_client.put(
            "/api/v1/auth/profile",
            json={"email": new_email},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == new_email

        logger.info("Profile email update succeeded")

    def test_update_profile_requires_auth(self, http_client):
        """Test that profile update requires authentication."""
        # Clear any existing session
        http_client.post("/api/v1/auth/logout")

        response = http_client.put(
            "/api/v1/auth/profile",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 401

        logger.info("Profile update correctly requires authentication")


class TestPasswordChangeAPI:
    """Test password change functionality through the API."""

    def test_change_password_success(self, http_client, admin_user):
        """Test changing password with correct current password."""
        # Use admin user for this test since test_user's password may be
        # modified by other tests (like password reset tests)
        original_password = admin_user["password"]
        new_password = "new_secure_password"

        # Ensure we're logged in fresh as admin
        http_client.post("/api/v1/auth/logout")
        login_response = http_client.post(
            "/api/v1/auth/login",
            json={
                "username": admin_user["username"],
                "password": original_password,
            },
        )
        assert login_response.status_code == 200

        # Change password
        response = http_client.put(
            "/api/v1/auth/password",
            json={
                "current_password": original_password,
                "new_password": new_password,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        logger.info("Password change succeeded")

        # Verify new password works
        # Logout first
        http_client.post("/api/v1/auth/logout")

        # Login with new password
        login_response = http_client.post(
            "/api/v1/auth/login",
            json={"username": admin_user["username"], "password": new_password},
        )
        assert login_response.status_code == 200

        logger.info("Login with new password succeeded")

        # Change password back to original for other tests
        restore_response = http_client.put(
            "/api/v1/auth/password",
            json={
                "current_password": new_password,
                "new_password": original_password,
            },
        )
        assert restore_response.status_code == 200
        logger.info("Password restored to original")

    def test_change_password_wrong_current(self, http_client, admin_user):
        """Test password change fails with wrong current password."""
        # Ensure we're logged in fresh
        http_client.post("/api/v1/auth/logout")
        login_resp = http_client.post(
            "/api/v1/auth/login",
            json={
                "username": admin_user["username"],
                "password": admin_user["password"],
            },
        )
        assert login_resp.status_code == 200

        response = http_client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "wrong_password",
                "new_password": "new_password",
            },
        )

        # API returns 401 for wrong current password (authentication failure)
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

        logger.info("Password change with wrong current password correctly rejected")

    def test_change_password_requires_auth(self, http_client):
        """Test that password change requires authentication."""
        # Clear any existing session
        http_client.post("/api/v1/auth/logout")

        response = http_client.put(
            "/api/v1/auth/password",
            json={
                "current_password": "any",
                "new_password": "any",
            },
        )

        assert response.status_code == 401

        logger.info("Password change correctly requires authentication")
