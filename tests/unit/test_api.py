"""
Unit tests for the API v1 endpoints.

Tests all REST API functionality including:
- Slideshow CRUD operations
- Slideshow item management
- Display management
- Authentication and authorization
- Error handling and validation
"""

import json
from datetime import datetime, timezone

from kiosk_show_replacement.models import Display, Slideshow, SlideshowItem, User, db


class TestSlideshowAPI:
    """Test slideshow CRUD API endpoints."""

    def test_list_slideshows_requires_auth(self, client):
        """Test that listing slideshows requires authentication."""
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 401  # API returns 401 Unauthorized

    def test_list_slideshows_empty(self, client, authenticated_user):
        """Test listing slideshows when none exist."""
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"] == []
        assert "message" in data

    def test_list_slideshows_with_data(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test listing slideshows with existing data."""
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == sample_slideshow.name
        assert "item_count" in data["data"][0]

    def test_create_slideshow_success(self, client, authenticated_user):
        """Test successful slideshow creation."""
        slideshow_data = {
            "name": "Test Slideshow",
            "description": "A test slideshow",
            "default_item_duration": 10,
        }

        response = client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Slideshow"
        assert data["data"]["description"] == "A test slideshow"
        assert data["data"]["default_item_duration"] == 10

    def test_create_slideshow_missing_name(self, client, authenticated_user):
        """Test slideshow creation with missing name."""
        slideshow_data = {"description": "No name provided"}

        response = client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "errors" in data

    def test_create_slideshow_duplicate_name(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test slideshow creation with duplicate name."""
        slideshow_data = {
            "name": sample_slideshow.name,
            "description": "Duplicate name",
        }

        response = client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "already exists" in data["message"]

    def test_get_slideshow_success(
        self, client, authenticated_user, sample_slideshow_with_items
    ):
        """Test successful slideshow retrieval."""
        slideshow, items = sample_slideshow_with_items

        response = client.get(f"/api/v1/slideshows/{slideshow.id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == slideshow.name
        assert "items" in data["data"]
        assert len(data["data"]["items"]) == len(items)

    def test_get_slideshow_not_found(self, client, authenticated_user):
        """Test slideshow retrieval with non-existent ID."""
        response = client.get("/api/v1/slideshows/999")
        assert response.status_code == 404

        data = response.get_json()
        assert data["success"] is False

    def test_update_slideshow_success(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test successful slideshow update."""
        update_data = {
            "name": "Updated Slideshow",
            "description": "Updated description",
        }

        response = client.put(
            f"/api/v1/slideshows/{sample_slideshow.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Slideshow"
        assert data["data"]["description"] == "Updated description"

    def test_delete_slideshow_success(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test successful slideshow deletion."""
        response = client.delete(f"/api/v1/slideshows/{sample_slideshow.id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

        # Verify slideshow is soft-deleted
        slideshow = Slideshow.query.get(sample_slideshow.id)
        assert slideshow.is_active is False

    def test_delete_slideshow_assigned_to_display(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test slideshow deletion when assigned to display."""
        # Create display assigned to slideshow
        display = Display(name="test-display", current_slideshow_id=sample_slideshow.id)
        db.session.add(display)
        db.session.commit()

        response = client.delete(f"/api/v1/slideshows/{sample_slideshow.id}")
        assert response.status_code == 400

        data = response.get_json()
        assert data["success"] is False
        assert "assigned to displays" in data["message"]

    def test_set_default_slideshow(self, client, authenticated_user, sample_slideshow):
        """Test setting slideshow as default."""
        response = client.post(f"/api/v1/slideshows/{sample_slideshow.id}/set-default")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

        # Verify slideshow is marked as default
        slideshow = Slideshow.query.get(sample_slideshow.id)
        assert slideshow.is_default is True


class TestSlideshowItemAPI:
    """Test slideshow item management API endpoints."""

    def test_list_slideshow_items(
        self, client, authenticated_user, sample_slideshow_with_items
    ):
        """Test listing slideshow items."""
        slideshow, items = sample_slideshow_with_items

        response = client.get(f"/api/v1/slideshows/{slideshow.id}/items")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == len(items)

    def test_create_slideshow_item_success(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test successful slideshow item creation."""
        item_data = {
            "title": "Test Item",
            "content_type": "image",
            "content_url": "https://example.com/image.jpg",
            "display_duration": 15,
        }

        response = client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(item_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Item"
        assert data["data"]["content_type"] == "image"

    def test_create_slideshow_item_missing_content_type(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test slideshow item creation with missing content type."""
        item_data = {"title": "Invalid Item"}

        response = client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(item_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "errors" in data

    def test_create_slideshow_item_invalid_content_type(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test slideshow item creation with invalid content type."""
        item_data = {
            "content_type": "invalid_type",
            "content_url": "https://example.com/test",
        }

        response = client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(item_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_update_slideshow_item(
        self, client, authenticated_user, sample_slideshow_with_items
    ):
        """Test slideshow item update."""
        slideshow, items = sample_slideshow_with_items
        item = items[0]

        update_data = {"title": "Updated Item", "display_duration": 20}

        response = client.put(
            f"/api/v1/slideshow-items/{item.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Item"
        assert data["data"]["display_duration"] == 20

    def test_delete_slideshow_item(
        self, client, authenticated_user, sample_slideshow_with_items
    ):
        """Test slideshow item deletion."""
        slideshow, items = sample_slideshow_with_items
        item = items[0]

        response = client.delete(f"/api/v1/slideshow-items/{item.id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

        # Verify item is soft-deleted
        deleted_item = SlideshowItem.query.get(item.id)
        assert deleted_item.is_active is False

    def test_reorder_slideshow_item(
        self, client, authenticated_user, sample_slideshow_with_items
    ):
        """Test slideshow item reordering."""
        slideshow, items = sample_slideshow_with_items
        item = items[0]  # First item

        reorder_data = {"new_order": 3}  # Move to position 3

        response = client.post(
            f"/api/v1/slideshow-items/{item.id}/reorder",
            data=json.dumps(reorder_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True


class TestDisplayAPI:
    """Test display management API endpoints."""

    def test_list_displays(self, client, authenticated_user):
        """Test listing displays."""
        # Create test display
        display = Display(name="test-display", owner_id=authenticated_user.id)
        db.session.add(display)
        db.session.commit()

        response = client.get("/api/v1/displays")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "test-display"

    def test_get_display(self, client, authenticated_user):
        """Test getting display details."""
        display = Display(name="test-display", owner_id=authenticated_user.id)
        db.session.add(display)
        db.session.commit()

        response = client.get(f"/api/v1/displays/{display.id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "test-display"
        assert "online" in data["data"]

    def test_update_display_slideshow_assignment(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test updating display slideshow assignment."""
        display = Display(name="test-display", owner_id=authenticated_user.id)
        db.session.add(display)
        db.session.commit()

        update_data = {"slideshow_id": sample_slideshow.id}

        response = client.put(
            f"/api/v1/displays/{display.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["current_slideshow_id"] == sample_slideshow.id

    def test_delete_display(self, client, authenticated_user):
        """Test display deletion."""
        display = Display(name="test-display", owner_id=authenticated_user.id)
        db.session.add(display)
        db.session.commit()
        display_id = display.id

        response = client.delete(f"/api/v1/displays/{display_id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True

        # Verify display is deleted
        deleted_display = Display.query.get(display_id)
        assert deleted_display is None


class TestAPIAuthentication:
    """Test API authentication and authorization."""

    def test_api_requires_authentication(self, client):
        """Test that all API endpoints require authentication."""
        endpoints = [
            ("/api/v1/slideshows", "GET"),
            ("/api/v1/slideshows", "POST"),
            ("/api/v1/slideshows/1", "GET"),
            ("/api/v1/displays", "GET"),
        ]

        for endpoint, method in endpoints:
            response = getattr(client, method.lower())(endpoint)
            assert response.status_code in [
                302,
                401,
            ]  # Redirect to login or unauthorized

    def test_api_access_control(self, client, app):
        """Test API access control - global access model allows all users to see all data."""  # noqa: E501
        # Create two users
        with app.app_context():
            user1 = User(username="user1", email="user1@example.com")
            user1.set_password("password")
            user2 = User(username="user2", email="user2@example.com")
            user2.set_password("password")
            db.session.add_all([user1, user2])
            db.session.commit()

            # User 1 creates a slideshow
            slideshow = Slideshow(
                name="User1 Slideshow", owner_id=user1.id, is_active=True
            )
            db.session.add(slideshow)
            db.session.commit()
            slideshow_id = slideshow.id

        # Login as user2
        client.post("/auth/login", data={"username": "user2", "password": "password"})

        # User2 should be able to access user1's slideshow (global access model)
        response = client.get(f"/api/v1/slideshows/{slideshow_id}")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "User1 Slideshow"


class TestAPIStatusEndpoint:
    """Test API status and health endpoints."""

    def test_api_status_endpoint(self, client):
        """Test API status endpoint."""
        response = client.get("/api/v1/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["api_version"] == "v1"
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]


class TestAPIAuthenticationEndpoints:
    """Test API authentication endpoints."""

    def test_api_login_success_new_user(self, client, app):
        """Test successful API login creates new user."""
        with app.app_context():
            # Ensure user doesn't exist
            existing_user = User.query.filter_by(username="newuser").first()
            assert existing_user is None

            # Test login with new credentials
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "newuser", "password": "newpass"},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["message"] == "User created and login successful"
            assert "data" in data

            user_data = data["data"]
            assert user_data["username"] == "newuser"
            assert user_data["is_admin"] is True
            assert "id" in user_data
            assert "created_at" in user_data

            # Verify user was created in database
            created_user = User.query.filter_by(username="newuser").first()
            assert created_user is not None
            assert created_user.username == "newuser"
            assert created_user.is_admin is True
            assert created_user.check_password("newpass")

    def test_api_login_success_existing_user(self, client, app):
        """Test successful API login with existing user."""
        with app.app_context():
            from kiosk_show_replacement.models import User, db

            # Create existing user
            user = User(username="existinguser", email="test@example.com")
            user.set_password("oldpass")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Test login with existing user but different password
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "existinguser", "password": "newpass"},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["message"] == "Login successful"

            user_data = data["data"]
            assert user_data["username"] == "existinguser"
            assert user_data["id"] == user_id

            # Verify password was updated
            updated_user = User.query.get(user_id)
            assert updated_user.check_password("newpass")
            assert not updated_user.check_password("oldpass")

    def test_api_login_session_creation(self, client):
        """Test API login creates proper session."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "sessionuser", "password": "sessionpass"},
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify session was created
        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["username"] == "sessionuser"
            assert sess["is_admin"] is True

    def test_api_login_no_json_data(self, client):
        """Test API login fails with no JSON data."""
        response = client.post("/api/v1/auth/login")

        assert response.status_code == 415  # Flask returns 415 for missing JSON content type
        # Flask's 415 error doesn't include JSON response body
        assert response.content_type != "application/json"

    def test_api_login_empty_username(self, client):
        """Test API login fails with empty username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": "password"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Username is required"

    def test_api_login_missing_username(self, client):
        """Test API login fails with missing username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "password"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Username is required"

    def test_api_login_empty_password(self, client):
        """Test API login fails with empty password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": ""},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Password is required"

    def test_api_login_missing_password(self, client):
        """Test API login fails with missing password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Password is required"

    def test_api_login_whitespace_username(self, client):
        """Test API login trims whitespace from username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "  trimuser  ", "password": "password"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == "trimuser"

    def test_api_login_permissive_authentication(self, client, app):
        """Test permissive authentication accepts any username/password combination."""
        test_cases = [
            ("admin", "admin"),
            ("user", "password123"),
            ("test@example.com", "complex!Pass"),
            ("newuser123", "simple"),
            ("special-user", "pass with spaces"),
        ]

        with app.app_context():
            for username, password in test_cases:
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": username, "password": password},
                    content_type="application/json",
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data["success"] is True
                assert data["data"]["username"] == username
                assert data["data"]["is_admin"] is True

    def test_api_login_password_update_for_existing_user(self, client, app):
        """Test that existing users get their passwords updated during login."""
        with app.app_context():
            from kiosk_show_replacement.models import User, db

            # Create user with initial password
            user = User(username="updateuser", email="update@example.com")
            user.set_password("initial_password")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Verify initial password works
            assert user.check_password("initial_password")

            # Login with different password
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "updateuser", "password": "new_password"},
                content_type="application/json",
            )

            assert response.status_code == 200

            # Verify password was updated
            updated_user = User.query.get(user_id)
            assert updated_user.check_password("new_password")
            assert not updated_user.check_password("initial_password")

    def test_api_login_last_login_timestamp_updated(self, client, app):
        """Test that last_login_at timestamp is updated on successful login."""
        with app.app_context():
            from kiosk_show_replacement.models import User, db

            # Create user
            user = User(username="timestampuser", email="timestamp@example.com")
            user.set_password("password")
            original_last_login = user.last_login_at  # Should be None initially
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            assert original_last_login is None

            # Login
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "timestampuser", "password": "password"},
                content_type="application/json",
            )

            assert response.status_code == 200

            # Verify last_login_at was updated
            updated_user = User.query.get(user_id)
            assert updated_user.last_login_at is not None
            # Check that last_login_at is recent (within the last 5 seconds)
            # Convert to UTC timezone-aware datetime for comparison
            now = datetime.now(timezone.utc)
            last_login = updated_user.last_login_at
            if last_login.tzinfo is None:
                # If the stored datetime is naive, assume it's UTC
                last_login = last_login.replace(tzinfo=timezone.utc)
            time_diff = now - last_login
            assert time_diff.total_seconds() < 5

    def test_api_login_content_type_requirement(self, client):
        """Test API login requires JSON content type."""
        # Test with form data instead of JSON
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "password"},
        )

        assert response.status_code == 415  # Flask returns 415 for wrong content type
        # Flask's 415 error doesn't include JSON response body
        assert response.content_type != "application/json"

    def test_get_current_user_info_success(self, client, authenticated_user):
        """Test successful retrieval of current user info."""
        response = client.get("/api/v1/auth/user")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "User information retrieved successfully"
        assert data["data"]["username"] == authenticated_user.username
        assert data["data"]["id"] == authenticated_user.id

    def test_get_current_user_info_requires_auth(self, client):
        """Test that getting current user info requires authentication."""
        response = client.get("/api/v1/auth/user")

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Authentication required"

    def test_api_logout_success(self, client, authenticated_user):
        """Test successful API logout."""
        # Verify user is authenticated
        with client.session_transaction() as sess:
            assert "user_id" in sess

        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Successfully logged out"

        # Verify session was cleared
        with client.session_transaction() as sess:
            assert "user_id" not in sess
            assert "username" not in sess
            assert "is_admin" not in sess

    def test_api_logout_requires_auth(self, client):
        """Test that API logout requires authentication."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"] == "Authentication required"

    def test_api_login_integration_with_other_endpoints(self, client):
        """Test that API login enables access to other protected endpoints."""
        # First, verify we can't access protected endpoint without auth
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 401

        # Login via API
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "integrationuser", "password": "password"},
            content_type="application/json",
        )
        assert login_response.status_code == 200

        # Now verify we can access protected endpoint
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_api_login_race_condition_handling(self, client, app):
        """Test that race condition during user creation is handled gracefully."""
        # This test simulates the scenario where two requests try to create
        # the same user simultaneously
        with app.app_context():
            from kiosk_show_replacement.models import User, db
            from unittest.mock import patch

            # Create a user manually to simulate race condition
            user = User(username="raceuser", email="race@example.com")
            user.set_password("password")
            db.session.add(user)
            db.session.commit()

            # The API login should still work even if user exists
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "raceuser", "password": "password"},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["username"] == "raceuser"
