"""
Integration tests for admin user management functionality.

Tests the user management UI and API for creating, editing,
and managing users.
"""

import logging
import time

logger = logging.getLogger(__name__)


class TestUserManagementAccess:
    """Test access control for user management."""

    def test_admin_can_access_user_management_page(self, authenticated_page, servers):
        """Test that admin users can access the user management page."""
        from playwright.sync_api import expect

        page = authenticated_page
        vite_url = servers["vite_url"]

        # Navigate to user management page
        page.goto(f"{vite_url}/admin/users")

        # Wait for the page to load
        heading = page.locator("h1").filter(has_text="User Management")
        expect(heading).to_be_visible(timeout=10000)

        logger.info("Admin can access user management page")

    def test_admin_can_see_user_management_nav_link(self, authenticated_page):
        """Test that admin users can see the User Management nav link."""
        from playwright.sync_api import expect

        page = authenticated_page

        # Look for User Management link in navigation
        nav_link = page.locator("a").filter(has_text="User Management")
        expect(nav_link).to_be_visible(timeout=5000)

        logger.info("Admin can see User Management nav link")

    def test_non_admin_cannot_access_user_management_api(
        self, http_client, auth_headers
    ):
        """Test that non-admin users cannot access user management API."""
        # Create a temporary non-admin user to test with
        # (test_user's password may have been changed by password reset tests)
        unique_username = f"non_admin_test_{int(time.time())}"
        temp_password = "test_temp_password"

        # First, create the user as admin
        create_response = http_client.post(
            "/api/v1/admin/users",
            json={
                "username": unique_username,
                "email": f"{unique_username}@example.com",
                "is_admin": False,
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        temp_password = create_response.json()["data"]["temporary_password"]

        # Logout admin and login as the new non-admin user
        http_client.post("/api/v1/auth/logout")
        login_response = http_client.post(
            "/api/v1/auth/login",
            json={
                "username": unique_username,
                "password": temp_password,
            },
        )
        assert login_response.status_code == 200

        # Try to access user management API
        response = http_client.get("/api/v1/admin/users")
        assert response.status_code == 403

        logger.info("Non-admin correctly denied access to user management API")


class TestUserManagementAPI:
    """Test user management through the API."""

    def test_list_users(self, http_client, auth_headers):
        """Test listing all users."""
        response = http_client.get("/api/v1/admin/users", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3  # admin, test_user, inactive_user

        logger.info(f"Listed {len(data['data'])} users")

    def test_create_user(self, http_client, auth_headers):
        """Test creating a new user."""
        unique_username = f"new_user_{int(time.time())}"

        response = http_client.post(
            "/api/v1/admin/users",
            json={
                "username": unique_username,
                "email": f"{unique_username}@example.com",
                "is_admin": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["username"] == unique_username
        assert "temporary_password" in data["data"]
        assert len(data["data"]["temporary_password"]) >= 8

        logger.info(f"Created new user: {unique_username}")

        # Verify the temporary password works
        temp_password = data["data"]["temporary_password"]
        http_client.post("/api/v1/auth/logout")

        login_response = http_client.post(
            "/api/v1/auth/login",
            json={"username": unique_username, "password": temp_password},
        )
        assert login_response.status_code == 200

        logger.info("New user can login with temporary password")

    def test_create_user_duplicate_username(self, http_client, auth_headers):
        """Test that creating user with duplicate username fails."""
        response = http_client.post(
            "/api/v1/admin/users",
            json={
                "username": "admin",  # Already exists
                "email": "new_admin@example.com",
            },
            headers=auth_headers,
        )

        assert response.status_code == 409  # Conflict
        data = response.json()
        assert data["success"] is False

        logger.info("Duplicate username correctly rejected")

    def test_update_user(self, http_client, auth_headers):
        """Test updating a user."""
        # First, list users to get a user ID
        list_response = http_client.get("/api/v1/admin/users", headers=auth_headers)
        users = list_response.json()["data"]

        # Find the test_user
        test_user = next((u for u in users if u["username"] == "test_user"), None)
        assert test_user is not None

        new_email = f"updated_{int(time.time())}@example.com"

        response = http_client.put(
            f"/api/v1/admin/users/{test_user['id']}",
            json={"email": new_email},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == new_email

        logger.info(f"Updated user email to: {new_email}")

    def test_cannot_change_own_admin_status(self, http_client, auth_headers):
        """Test that admin cannot change their own admin status."""
        # Get current user
        user_response = http_client.get("/api/v1/auth/user", headers=auth_headers)
        current_user = user_response.json()["data"]

        response = http_client.put(
            f"/api/v1/admin/users/{current_user['id']}",
            json={"is_admin": False},
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

        logger.info("Admin correctly prevented from demoting self")

    def test_cannot_deactivate_self(self, http_client, auth_headers):
        """Test that admin cannot deactivate themselves."""
        # Get current user
        user_response = http_client.get("/api/v1/auth/user", headers=auth_headers)
        current_user = user_response.json()["data"]

        response = http_client.put(
            f"/api/v1/admin/users/{current_user['id']}",
            json={"is_active": False},
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False

        logger.info("Admin correctly prevented from deactivating self")

    def test_reset_user_password(self, http_client, auth_headers):
        """Test resetting a user's password."""
        # First, list users to get a user ID
        list_response = http_client.get("/api/v1/admin/users", headers=auth_headers)
        users = list_response.json()["data"]

        # Find the test_user
        test_user = next((u for u in users if u["username"] == "test_user"), None)
        assert test_user is not None

        response = http_client.post(
            f"/api/v1/admin/users/{test_user['id']}/reset-password",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "temporary_password" in data["data"]
        assert len(data["data"]["temporary_password"]) >= 8

        logger.info("Password reset succeeded")

        # Verify the new password works
        new_password = data["data"]["temporary_password"]
        http_client.post("/api/v1/auth/logout")

        login_response = http_client.post(
            "/api/v1/auth/login",
            json={"username": "test_user", "password": new_password},
        )
        assert login_response.status_code == 200

        logger.info("User can login with reset password")


class TestUserManagementUI:
    """Test user management through the UI."""

    def test_users_table_displays(self, authenticated_page, servers):
        """Test that users are displayed in a table."""
        from playwright.sync_api import expect

        page = authenticated_page
        vite_url = servers["vite_url"]

        # Navigate to user management page
        page.goto(f"{vite_url}/admin/users")

        # Wait for the table to load
        table = page.locator("table")
        expect(table).to_be_visible(timeout=10000)

        # Check for expected columns
        expect(page.locator("th").filter(has_text="Username")).to_be_visible()
        expect(page.locator("th").filter(has_text="Email")).to_be_visible()
        expect(page.locator("th").filter(has_text="Role")).to_be_visible()
        expect(page.locator("th").filter(has_text="Status")).to_be_visible()

        # Check that admin user is displayed - use first cell in table body
        # The first column is Username, so look for a row containing "admin" in first td
        admin_row = page.locator("tbody tr").first
        expect(admin_row).to_be_visible()

        logger.info("Users table displays correctly")

    def test_create_user_modal(self, authenticated_page, servers):
        """Test the create user modal workflow."""
        from playwright.sync_api import expect

        page = authenticated_page
        vite_url = servers["vite_url"]

        # Navigate to user management page
        page.goto(f"{vite_url}/admin/users")

        # Click Create User button
        create_button = page.locator("button").filter(has_text="Create User")
        expect(create_button).to_be_visible(timeout=10000)
        create_button.click()

        # Wait for modal to appear
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Check modal title
        expect(modal.locator(".modal-title")).to_have_text("Create User")

        # Fill in user details
        unique_username = f"ui_test_user_{int(time.time())}"
        page.locator("input[placeholder='Enter username']").fill(unique_username)
        page.locator("input[placeholder*='email']").fill(
            f"{unique_username}@example.com"
        )

        # Submit the form
        submit_button = modal.locator("button[type='submit']")
        submit_button.click()

        # Wait for password modal to appear
        password_modal = page.locator(".modal").filter(has_text="Temporary Password")
        expect(password_modal).to_be_visible(timeout=10000)

        # Verify temporary password is shown
        password_display = password_modal.locator("code")
        expect(password_display).to_be_visible()

        # Close the modal
        done_button = password_modal.locator("button").filter(has_text="Done")
        done_button.click()

        # Verify user appears in table - use get_by_role for exact match
        expect(
            page.get_by_role("cell", name=unique_username, exact=True)
        ).to_be_visible(timeout=5000)

        logger.info(f"Created user via UI: {unique_username}")

    def test_edit_user_modal(self, authenticated_page, servers):
        """Test the edit user modal workflow."""
        from playwright.sync_api import expect

        page = authenticated_page
        vite_url = servers["vite_url"]

        # Navigate to user management page
        page.goto(f"{vite_url}/admin/users")

        # Find the test_user row and click Edit - use exact match to avoid ui_test_user
        test_user_cell = page.get_by_role("cell", name="test_user", exact=True)
        expect(test_user_cell).to_be_visible(timeout=10000)
        test_user_row = test_user_cell.locator("xpath=ancestor::tr")

        edit_button = test_user_row.locator("button").filter(has_text="Edit")
        edit_button.click()

        # Wait for modal to appear
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Check modal title contains username
        expect(modal.locator(".modal-title")).to_contain_text("test_user")

        # Update email
        email_input = modal.locator("input[type='email']")
        email_input.clear()
        email_input.fill("edited_via_ui@example.com")

        # Save changes
        save_button = modal.locator("button").filter(has_text="Save Changes")
        save_button.click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=5000)

        logger.info("Edited user via UI")

    def test_reset_password_confirmation(self, authenticated_page, servers):
        """Test the reset password confirmation dialog."""
        from playwright.sync_api import expect

        page = authenticated_page
        vite_url = servers["vite_url"]

        # Navigate to user management page
        page.goto(f"{vite_url}/admin/users")

        # Find the test_user row and click Reset Password - use exact match
        test_user_cell = page.get_by_role("cell", name="test_user", exact=True)
        expect(test_user_cell).to_be_visible(timeout=10000)
        test_user_row = test_user_cell.locator("xpath=ancestor::tr")

        reset_button = test_user_row.locator("button").filter(has_text="Reset Password")
        reset_button.click()

        # Wait for confirmation modal
        modal = page.locator(".modal").filter(has_text="Reset Password")
        expect(modal).to_be_visible(timeout=5000)

        # Confirm the reset
        confirm_button = modal.locator("button.btn-warning")
        confirm_button.click()

        # Wait for password modal to appear
        password_modal = page.locator(".modal").filter(has_text="Temporary Password")
        expect(password_modal).to_be_visible(timeout=10000)

        # Verify temporary password is shown
        password_display = password_modal.locator("code")
        expect(password_display).to_be_visible()

        logger.info("Reset password via UI")
