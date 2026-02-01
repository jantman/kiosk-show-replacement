"""
Unit tests for authentication system.

Tests authentication decorators, views, and utility functions.
"""

from flask import session

from kiosk_show_replacement.app import db
from kiosk_show_replacement.auth.decorators import (
    get_current_user,
    is_admin,
    is_authenticated,
)
from kiosk_show_replacement.models import User


class TestAuthenticationDecorators:
    """Test authentication decorators and utility functions."""

    def test_is_authenticated_with_logged_in_user(self, app):
        """Test is_authenticated returns True when user is logged in."""
        with app.test_request_context():
            session["user_id"] = 123
            session["username"] = "testuser"
            assert is_authenticated() is True

    def test_is_authenticated_without_session(self, app):
        """Test is_authenticated returns False when no session."""
        with app.test_request_context():
            assert is_authenticated() is False

    def test_is_authenticated_with_partial_session(self, app):
        """Test is_authenticated returns False with incomplete session."""
        with app.test_request_context():
            session["user_id"] = 123
            # Missing username - should still be authenticated since we only
            # check user_id
            assert is_authenticated() is True

    def test_is_admin_with_admin_user(self, app):
        """Test is_admin returns True for admin users."""
        with app.test_request_context():
            session["user_id"] = 123
            session["username"] = "admin"
            session["is_admin"] = True
            assert is_admin() is True

    def test_is_admin_with_regular_user(self, app):
        """Test is_admin returns False for regular users."""
        with app.test_request_context():
            session["user_id"] = 123
            session["username"] = "user"
            session["is_admin"] = False
            assert is_admin() is False

    def test_is_admin_without_session(self, app):
        """Test is_admin returns False when not authenticated."""
        with app.test_request_context():
            assert is_admin() is False

    def test_get_current_user_with_session(self, app):
        """Test get_current_user returns user object when authenticated
        with valid user."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        with app.test_request_context():
            session["user_id"] = user_id
            session["username"] = "testuser"
            session["is_admin"] = False

            current_user = get_current_user()
            assert current_user is not None
            assert current_user.id == user_id
            assert current_user.username == "testuser"

    def test_get_current_user_without_session(self, app):
        """Test get_current_user returns None when not authenticated."""
        with app.test_request_context():
            assert get_current_user() is None


class TestAuthenticationViews:
    """Test authentication views and login/logout functionality."""

    def test_login_page_redirects_to_admin(self, client):
        """Test GET /auth/login redirects to React admin interface."""
        response = client.get("/auth/login")
        assert response.status_code == 302
        assert "/admin/" in response.location

    def test_login_fails_for_nonexistent_user(self, client, app):
        """Test login fails for a user that doesn't exist."""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent", "password": "anypassword"},
        )

        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_login_fails_for_wrong_password(self, client, app):
        """Test login fails when password is incorrect."""
        # Create a user with known credentials
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("correctpassword")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_login_fails_for_inactive_user(self, client, app):
        """Test login fails when user account is inactive."""
        # Create an inactive user
        with app.app_context():
            user = User(username="inactiveuser", email="inactive@example.com")
            user.set_password("password")
            user.is_active = False
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "inactiveuser", "password": "password"},
        )

        assert response.status_code == 200
        assert b"Account is inactive" in response.data

    def test_login_succeeds_for_valid_active_user(self, client, app):
        """Test login succeeds for valid credentials of an active user."""
        # Create an active user
        with app.app_context():
            user = User(username="activeuser", email="active@example.com")
            user.set_password("correctpassword")
            user.is_active = True
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/auth/login",
            data={"username": "activeuser", "password": "correctpassword"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Should redirect to dashboard after successful login
        assert b"Dashboard" in response.data or b"Welcome" in response.data

    def test_login_creates_session_for_valid_user(self, client, app):
        """Test successful login creates proper session."""
        # Create a user
        with app.app_context():
            user = User(username="sessionuser", email="session@example.com")
            user.set_password("password")
            user.is_admin = True
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/auth/login",
            data={"username": "sessionuser", "password": "password"},
        )

        # Check session was created correctly
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["user_id"] == user_id
            assert sess["username"] == "sessionuser"
            assert sess["is_admin"] is True

    def test_login_post_empty_username(self, client):
        """Test POST to login with empty username."""
        response = client.post(
            "/auth/login", data={"username": "", "password": "testpass"}
        )

        assert response.status_code == 200
        assert b"Username is required" in response.data

    def test_login_post_empty_password(self, client):
        """Test POST to login with empty password."""
        response = client.post(
            "/auth/login", data={"username": "testuser", "password": ""}
        )

        assert response.status_code == 200
        assert b"Password is required" in response.data

    def test_logout_redirects_to_admin(self, client):
        """Test logout redirects to React admin interface."""
        # First login
        with client.session_transaction() as sess:
            sess["user_id"] = 123
            sess["username"] = "testuser"

        response = client.get("/auth/logout")
        assert response.status_code == 302
        assert "/admin/" in response.location

    def test_logout_clears_session(self, client):
        """Test logout clears session data."""
        # First login
        with client.session_transaction() as sess:
            sess["user_id"] = 123
            sess["username"] = "testuser"
            sess["is_admin"] = False

        # Logout
        client.get("/auth/logout")

        # Check session is cleared
        with client.session_transaction() as sess:
            assert "user_id" not in sess
            assert "username" not in sess
            assert "is_admin" not in sess

    def test_admin_user_gets_admin_privileges(self, client, app):
        """Test admin user gets admin privileges in session."""
        # Create an admin user
        with app.app_context():
            user = User(username="adminuser", email="admin@example.com")
            user.set_password("password")
            user.is_admin = True
            db.session.add(user)
            db.session.commit()

        client.post(
            "/auth/login",
            data={"username": "adminuser", "password": "password"},
        )

        with client.session_transaction() as sess:
            assert sess["is_admin"] is True

    def test_regular_user_does_not_get_admin_privileges(self, client, app):
        """Test non-admin user does not get admin privileges in session."""
        # Create a non-admin user
        with app.app_context():
            user = User(username="regularuser", email="regular@example.com")
            user.set_password("password")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()

        client.post(
            "/auth/login",
            data={"username": "regularuser", "password": "password"},
        )

        with client.session_transaction() as sess:
            assert sess["is_admin"] is False


class TestAuthenticationIntegration:
    """Test authentication integration with protected routes."""

    def test_dashboard_requires_authentication(self, client):
        """Test dashboard redirects to login when not authenticated."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/admin/" in response.location

    def test_dashboard_accessible_when_authenticated(self, client, app):
        """Test dashboard accessible when authenticated."""
        # Create and login a user
        with app.app_context():
            user = User(username="dashuser", email="dash@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        client.post(
            "/auth/login", data={"username": "dashuser", "password": "password"}
        )

        response = client.get("/")
        assert response.status_code == 200

    def test_protected_route_redirects_to_admin(self, client):
        """Test protected Flask routes redirect to React admin interface."""
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/admin/" in response.location

    def test_admin_route_requires_admin_privileges(self, client, app):
        """Test admin routes require admin privileges."""
        # Create a non-admin user
        with app.app_context():
            user = User(username="nonadminuser", email="nonadmin@example.com")
            user.set_password("password")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()

        # Login as regular user
        client.post(
            "/auth/login", data={"username": "nonadminuser", "password": "password"}
        )

        # Try to access admin route (settings) - should be denied
        response = client.get("/settings")
        # Either 403 or redirect to unauthorized page
        assert response.status_code in [302, 403]

    def test_admin_route_accessible_to_admin(self, client, app):
        """Test admin routes accessible to admin users."""
        # Create an admin user
        with app.app_context():
            user = User(username="adminforroute", email="adminroute@example.com")
            user.set_password("password")
            user.is_admin = True
            db.session.add(user)
            db.session.commit()

        # Login as admin
        client.post(
            "/auth/login", data={"username": "adminforroute", "password": "password"}
        )

        # Access admin route
        response = client.get("/settings")
        assert response.status_code == 200


class TestAPIAuthentication:
    """Test API authentication endpoints."""

    def test_api_login_fails_for_nonexistent_user(self, client, app):
        """Test API login returns 401 for non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "anypassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "Invalid username or password" in data["error"]

    def test_api_login_fails_for_wrong_password(self, client, app):
        """Test API login returns 401 for wrong password."""
        # Create a user
        with app.app_context():
            user = User(username="apiuser", email="api@example.com")
            user.set_password("correctpassword")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "apiuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "Invalid username or password" in data["error"]

    def test_api_login_fails_for_inactive_user(self, client, app):
        """Test API login returns 403 for inactive user."""
        # Create an inactive user
        with app.app_context():
            user = User(username="inactiveapi", email="inactiveapi@example.com")
            user.set_password("password")
            user.is_active = False
            db.session.add(user)
            db.session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactiveapi", "password": "password"},
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data["success"] is False
        assert "inactive" in data["error"].lower()

    def test_api_login_succeeds_for_valid_user(self, client, app):
        """Test API login succeeds for valid credentials."""
        # Create a user
        with app.app_context():
            user = User(username="validapiuser", email="validapi@example.com")
            user.set_password("correctpassword")
            user.is_admin = True
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "validapiuser", "password": "correctpassword"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == user_id
        assert data["data"]["username"] == "validapiuser"
        assert data["data"]["is_admin"] is True

    def test_api_login_creates_session(self, client, app):
        """Test API login creates proper session."""
        # Create a user
        with app.app_context():
            user = User(username="apisessionuser", email="apisession@example.com")
            user.set_password("password")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "apisessionuser", "password": "password"},
        )

        # Check session was created correctly
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["user_id"] == user_id
            assert sess["username"] == "apisessionuser"
            assert sess["is_admin"] is False

    def test_api_login_requires_username(self, client):
        """Test API login requires username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "password"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Username is required" in data["error"]

    def test_api_login_requires_password(self, client):
        """Test API login requires password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "user"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Password is required" in data["error"]


class TestProfileAPI:
    """Test user profile API endpoints."""

    def test_update_profile_email_success(self, client, app):
        """Test successfully updating user email."""
        # Create and login user
        with app.app_context():
            user = User(username="profileuser", email="old@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "profileuser", "password": "password"},
        )

        # Update email
        response = client.put(
            "/api/v1/auth/profile",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["email"] == "new@example.com"

        # Verify in database
        with app.app_context():
            updated_user = db.session.get(User, user_id)
            assert updated_user.email == "new@example.com"

    def test_update_profile_email_conflict(self, client, app):
        """Test updating email fails if already used by another user."""
        # Create two users
        with app.app_context():
            user1 = User(username="user1", email="user1@example.com")
            user1.set_password("password")
            user2 = User(username="user2", email="taken@example.com")
            user2.set_password("password")
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

        # Login as user1
        client.post(
            "/api/v1/auth/login",
            json={"username": "user1", "password": "password"},
        )

        # Try to use user2's email
        response = client.put(
            "/api/v1/auth/profile",
            json={"email": "taken@example.com"},
        )

        assert response.status_code == 409
        data = response.get_json()
        assert data["success"] is False
        assert "already in use" in data["error"].lower()

    def test_update_profile_clear_email(self, client, app):
        """Test clearing user email by setting it to empty string."""
        # Create and login user
        with app.app_context():
            user = User(username="clearemailuser", email="has@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "clearemailuser", "password": "password"},
        )

        # Clear email
        response = client.put(
            "/api/v1/auth/profile",
            json={"email": ""},
        )

        assert response.status_code == 200

        # Verify in database
        with app.app_context():
            updated_user = db.session.get(User, user_id)
            assert updated_user.email is None

    def test_update_profile_requires_auth(self, client):
        """Test profile update requires authentication."""
        response = client.put(
            "/api/v1/auth/profile",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 401

    def test_change_password_success(self, client, app):
        """Test successfully changing password."""
        # Create and login user
        with app.app_context():
            user = User(username="pwduser", email="pwd@example.com")
            user.set_password("oldpassword")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "pwduser", "password": "oldpassword"},
        )

        # Change password
        response = client.put(
            "/api/v1/auth/password",
            json={"current_password": "oldpassword", "new_password": "newpassword"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # Verify new password works
        with app.app_context():
            updated_user = db.session.get(User, user_id)
            assert updated_user.check_password("newpassword")
            assert not updated_user.check_password("oldpassword")

    def test_change_password_wrong_current(self, client, app):
        """Test changing password fails with wrong current password."""
        # Create and login user
        with app.app_context():
            user = User(username="wrongpwduser", email="wrongpwd@example.com")
            user.set_password("correctpassword")
            db.session.add(user)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "wrongpwduser", "password": "correctpassword"},
        )

        # Try to change password with wrong current password
        response = client.put(
            "/api/v1/auth/password",
            json={"current_password": "wrongpassword", "new_password": "newpassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "incorrect" in data["error"].lower()

    def test_change_password_requires_current(self, client, app):
        """Test changing password requires current password."""
        # Create and login user
        with app.app_context():
            user = User(username="reqcurrentuser", email="req@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "reqcurrentuser", "password": "password"},
        )

        response = client.put(
            "/api/v1/auth/password",
            json={"new_password": "newpassword"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Current password is required" in data["error"]

    def test_change_password_requires_new(self, client, app):
        """Test changing password requires new password."""
        # Create and login user
        with app.app_context():
            user = User(username="reqnewuser", email="reqnew@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "reqnewuser", "password": "password"},
        )

        response = client.put(
            "/api/v1/auth/password",
            json={"current_password": "password"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "New password is required" in data["error"]

    def test_change_password_requires_auth(self, client):
        """Test password change requires authentication."""
        response = client.put(
            "/api/v1/auth/password",
            json={"current_password": "old", "new_password": "new"},
        )

        assert response.status_code == 401
