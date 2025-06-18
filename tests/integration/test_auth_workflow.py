"""
Integration tests for authentication workflows.

These tests simulate the complete end-to-end authentication flow
including both frontend UI login and API authentication, testing
the interaction between the React frontend and Flask backend.
"""

import json
from datetime import datetime, timezone

from kiosk_show_replacement.models import User, db


class TestUILoginWorkflow:
    """Test complete UI login workflow (HTML form to API)."""

    def test_login_page_accessible(self, client):
        """Test that login page is accessible and contains expected elements."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        
        # Check for essential form elements
        assert b"Login" in response.data
        assert b'name="username"' in response.data
        assert b'name="password"' in response.data
        assert b"Permissive Authentication" in response.data
        assert b"Any username is accepted" in response.data

    def test_html_form_login_creates_user_and_session(self, client, app):
        """Test HTML form login creates user and establishes session."""
        # Login via HTML form
        response = client.post(
            "/auth/login",
            data={"username": "htmlformuser", "password": "testpass"},
            follow_redirects=True,
        )
        
        assert response.status_code == 200
        # Should be redirected to dashboard after successful login
        assert b"Dashboard" in response.data
        
        # Verify session was created
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["username"] == "htmlformuser"
            assert sess["is_admin"] is True
        
        # Verify user was created in database
        with app.app_context():
            user = User.query.filter_by(username="htmlformuser").first()
            assert user is not None
            assert user.username == "htmlformuser"
            assert user.is_admin is True
            assert user.check_password("testpass")
            assert user.last_login_at is not None

    def test_api_login_workflow_end_to_end(self, client, app):
        """Test complete API login workflow as used by React frontend."""
        # Step 1: Verify we can't access protected API endpoint without auth
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 401
        
        # Step 2: Login via API (as React frontend would do)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "reactuser", "password": "frontendpass"},
            content_type="application/json",
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == "reactuser"
        assert data["data"]["is_admin"] is True
        
        # Step 3: Verify session was established and we can access protected endpoints
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 200
        slideshow_data = response.get_json()
        assert slideshow_data["success"] is True
        
        # Step 4: Get current user info via API
        response = client.get("/api/v1/auth/user")
        assert response.status_code == 200
        user_data = response.get_json()
        assert user_data["success"] is True
        assert user_data["data"]["username"] == "reactuser"
        
        # Step 5: Logout via API
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        logout_data = response.get_json()
        assert logout_data["success"] is True
        
        # Step 6: Verify we can no longer access protected endpoints
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 401
        
        # Verify user was created in database
        with app.app_context():
            user = User.query.filter_by(username="reactuser").first()
            assert user is not None
            assert user.username == "reactuser"
            assert user.is_admin is True
            assert user.check_password("frontendpass")

    def test_mixed_auth_workflow_html_then_api(self, client, app):
        """Test workflow where user logs in via HTML form then uses API."""
        # Step 1: Login via HTML form
        response = client.post(
            "/auth/login",
            data={"username": "mixeduser", "password": "mixedpass"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        
        # Verify session was created
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["username"] == "mixeduser"
        
        # Step 2: Use API endpoints with existing session
        response = client.get("/api/v1/auth/user")
        assert response.status_code == 200
        user_data = response.get_json()
        assert user_data["success"] is True
        assert user_data["data"]["username"] == "mixeduser"
        
        # Step 3: Access other API endpoints
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 200
        slideshow_data = response.get_json()
        assert slideshow_data["success"] is True
        
        # Step 4: Logout via HTML (traditional way)
        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data  # Should be back at login page
        
        # Step 5: Verify API access is revoked
        response = client.get("/api/v1/auth/user")
        assert response.status_code == 401

    def test_cross_origin_api_authentication(self, client):
        """Test API authentication with CORS headers (simulating React app)."""
        # Simulate CORS preflight request
        response = client.options("/api/v1/auth/login")
        assert response.status_code == 200
        
        # Login with Origin header (as browser would send from React app)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "corsuser", "password": "corspass"},
            content_type="application/json",
            headers={"Origin": "http://localhost:3000"},  # Typical React dev server
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_authentication_error_handling_workflow(self, client):
        """Test error handling in authentication workflow."""
        # Test 1: Empty credentials via API
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": ""},
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Username is required" in data["error"]
        
        # Test 2: Missing JSON data
        response = client.post("/api/v1/auth/login")
        assert response.status_code == 415  # Unsupported Media Type
        
        # Test 3: Invalid content type
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test", "password": "test"},  # Form data instead of JSON
        )
        assert response.status_code == 415
        
        # Test 4: Empty credentials via HTML form
        response = client.post(
            "/auth/login",
            data={"username": "", "password": "test"},
            follow_redirects=False,
        )
        assert response.status_code == 200  # Stays on login page
        assert b"Username is required" in response.data

    def test_password_update_workflow(self, client, app):
        """Test that existing users get password updates during login."""
        # Create initial user with specific password
        with app.app_context():
            user = User(username="updatetestuser", email="update@example.com")
            user.set_password("initial_password")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Login with different password via API
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "updatetestuser", "password": "new_password"},
            content_type="application/json",
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Login successful"
        
        # Verify password was updated in database
        with app.app_context():
            updated_user = User.query.get(user_id)
            assert updated_user.check_password("new_password")
            assert not updated_user.check_password("initial_password")
            
            # Verify last_login_at was updated
            assert updated_user.last_login_at is not None
            
            # Check that last_login_at is recent (within the last 10 seconds)
            now = datetime.now(timezone.utc)
            last_login = updated_user.last_login_at
            if last_login.tzinfo is None:
                last_login = last_login.replace(tzinfo=timezone.utc)
            time_diff = now - last_login
            assert time_diff.total_seconds() < 10

    def test_session_persistence_across_requests(self, client):
        """Test that authentication session persists across multiple requests."""
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "persistentuser", "password": "persistentpass"},
            content_type="application/json",
        )
        assert response.status_code == 200
        
        # Make multiple API requests to verify session persistence
        endpoints_to_test = [
            "/api/v1/auth/user",
            "/api/v1/slideshows",
            "/api/v1/displays",
            "/api/v1/status",
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed to access {endpoint}"
            if endpoint != "/api/v1/status":  # Status endpoint doesn't require auth
                data = response.get_json()
                assert data["success"] is True

    def test_concurrent_login_sessions(self, client, app):
        """Test handling of concurrent login sessions for same user."""
        # First login
        response1 = client.post(
            "/api/v1/auth/login",
            json={"username": "concurrentuser", "password": "pass1"},
            content_type="application/json",
        )
        assert response1.status_code == 200
        
        # Verify first session works
        response = client.get("/api/v1/auth/user")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["username"] == "concurrentuser"
        
        # Second login with different password (should update password)
        response2 = client.post(
            "/api/v1/auth/login",
            json={"username": "concurrentuser", "password": "pass2"},
            content_type="application/json",
        )
        assert response2.status_code == 200
        
        # Verify session still works and password was updated
        response = client.get("/api/v1/auth/user")
        assert response.status_code == 200
        
        with app.app_context():
            user = User.query.filter_by(username="concurrentuser").first()
            assert user.check_password("pass2")
            assert not user.check_password("pass1")


class TestAuthenticationIntegrationEdgeCases:
    """Test edge cases in authentication integration."""

    def test_special_characters_in_credentials(self, client, app):
        """Test authentication with special characters in username/password."""
        test_cases = [
            ("user@domain.com", "p@ssw0rd!"),
            ("user-name_123", "complex!P@ss$123"),
            ("测试用户", "密码123"),  # Unicode characters
            ("user with spaces", "pass with spaces"),
        ]
        
        for username, password in test_cases:
            # Login via API
            response = client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
                content_type="application/json",
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["username"] == username
            
            # Verify user can access protected resources
            response = client.get("/api/v1/auth/user")
            assert response.status_code == 200
            
            # Logout for next test
            client.post("/api/v1/auth/logout")

    def test_very_long_credentials(self, client):
        """Test authentication with very long username/password."""
        long_username = "a" * 79  # Just under the 80 char limit
        long_password = "b" * 200  # Long password
        
        response = client.post(
            "/api/v1/auth/login",
            json={"username": long_username, "password": long_password},
            content_type="application/json",
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == long_username

    def test_username_too_long_validation(self, client):
        """Test that usernames over 80 characters are rejected."""
        too_long_username = "a" * 81  # Over the 80 char limit
        
        response = client.post(
            "/api/v1/auth/login",
            json={"username": too_long_username, "password": "password"},
            content_type="application/json",
        )
        
        # Should fail during user creation due to validation
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_case_sensitive_usernames(self, client, app):
        """Test that usernames are case-sensitive."""
        # Create user with lowercase username
        response1 = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password1"},
            content_type="application/json",
        )
        assert response1.status_code == 200
        
        # Logout
        client.post("/api/v1/auth/logout")
        
        # Try to login with uppercase username (should create new user)
        response2 = client.post(
            "/api/v1/auth/login",
            json={"username": "TESTUSER", "password": "password2"},
            content_type="application/json",
        )
        assert response2.status_code == 200
        
        # Verify two separate users were created
        with app.app_context():
            user1 = User.query.filter_by(username="testuser").first()
            user2 = User.query.filter_by(username="TESTUSER").first()
            assert user1 is not None
            assert user2 is not None
            assert user1.id != user2.id
            assert user1.check_password("password1")
            assert user2.check_password("password2")

    def test_whitespace_trimming_consistency(self, client, app):
        """Test consistent whitespace trimming between HTML and API login."""
        username_with_spaces = "  spaceuser  "
        trimmed_username = "spaceuser"
        
        # Login via API (should trim whitespace)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username_with_spaces, "password": "password"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["username"] == trimmed_username
        
        # Logout
        client.post("/api/v1/auth/logout")
        
        # Login via HTML form (should also trim whitespace and find existing user)
        response = client.post(
            "/auth/login",
            data={"username": username_with_spaces, "password": "newpassword"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        
        # Verify only one user was created and password was updated
        with app.app_context():
            users = User.query.filter_by(username=trimmed_username).all()
            assert len(users) == 1
            user = users[0]
            assert user.check_password("newpassword")
