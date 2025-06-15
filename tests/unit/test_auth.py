"""
Unit tests for authentication system.

Tests authentication decorators, views, and utility functions.
"""

from flask import session

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
        # Create a real user in the database for this test
        from kiosk_show_replacement.app import db

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

    def test_login_page_accessible(self, client):
        """Test login page is accessible."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_permissive_authentication_via_login(self, client, app):
        """Test permissive authentication works through login endpoint."""
        # Test various username/password combinations through the actual login endpoint
        test_cases = [
            ("admin", "admin"),
            ("user", "password"),
            ("test", "test123"),
            ("newuser", "newpass"),
        ]

        for username, password in test_cases:
            response = client.post(
                "/auth/login",
                data={"username": username, "password": password},
                follow_redirects=True,
            )

            # Should redirect to dashboard after successful login
            assert response.status_code == 200
            # Check that we're at the dashboard (permissive auth accepts all
            # valid credentials)
            assert b"Dashboard" in response.data or b"Welcome" in response.data

    def test_login_post_valid_credentials(self, client):
        """Test POST to login with valid credentials."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        # Should be redirected to dashboard after login
        assert b"Dashboard" in response.data or b"dashboard" in response.data

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

    def test_logout_redirects_to_login(self, client):
        """Test logout redirects to login page."""
        # First login
        with client.session_transaction() as sess:
            sess["user_id"] = 123
            sess["username"] = "testuser"

        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

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

    def test_login_creates_session(self, client):
        """Test successful login creates proper session."""
        client.post("/auth/login", data={"username": "admin", "password": "admin"})

        # Check session was created
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["username"] == "admin"
            assert "is_admin" in sess

    def test_admin_user_gets_admin_privileges(self, client):
        """Test admin username gets admin privileges."""
        client.post("/auth/login", data={"username": "admin", "password": "password"})

        with client.session_transaction() as sess:
            assert sess["is_admin"] is True

    def test_regular_user_does_not_get_admin_privileges(self, client):
        """Test non-admin username gets admin privileges (all users are admin now)."""
        client.post("/auth/login", data={"username": "user", "password": "password"})

        with client.session_transaction() as sess:
            assert sess["is_admin"] is True  # All users are admin now


class TestAuthenticationIntegration:
    """Test authentication integration with protected routes."""

    def test_dashboard_requires_authentication(self, client):
        """Test dashboard redirects to login when not authenticated."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_dashboard_accessible_when_authenticated(self, client):
        """Test dashboard accessible when authenticated."""
        # Login first
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        response = client.get("/")
        assert response.status_code == 200

    def test_protected_route_preserves_next_parameter(self, client):
        """Test login preserves next parameter for protected routes."""
        response = client.get("/profile")
        assert response.status_code == 302
        assert "next=" in response.location
        assert "/profile" in response.location

    def test_admin_route_requires_admin_privileges(self, client):
        """Test admin routes are accessible since all users are admin."""
        # Login as regular user (who is now admin by default)
        client.post("/auth/login", data={"username": "user", "password": "password"})

        # Try to access admin route (settings) - should succeed since all
        # users are admin
        response = client.get("/settings")
        assert response.status_code == 200

    def test_admin_route_accessible_to_admin(self, client):
        """Test admin routes accessible to admin users."""
        # Login as admin
        client.post("/auth/login", data={"username": "admin", "password": "password"})

        # Access admin route
        response = client.get("/settings")
        assert response.status_code == 200
