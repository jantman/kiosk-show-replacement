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
from datetime import datetime, timezone, timedelta

import pytest

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

    def test_list_slideshows_with_data(self, client, authenticated_user, sample_slideshow):
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
            "default_item_duration": 10
        }
        
        response = client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json"
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
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "errors" in data

    def test_create_slideshow_duplicate_name(self, client, authenticated_user, sample_slideshow):
        """Test slideshow creation with duplicate name."""
        slideshow_data = {
            "name": sample_slideshow.name,
            "description": "Duplicate name"
        }
        
        response = client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "already exists" in data["message"]

    def test_get_slideshow_success(self, client, authenticated_user, sample_slideshow_with_items):
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

    def test_update_slideshow_success(self, client, authenticated_user, sample_slideshow):
        """Test successful slideshow update."""
        update_data = {
            "name": "Updated Slideshow",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/v1/slideshows/{sample_slideshow.id}",
            data=json.dumps(update_data),
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Slideshow"
        assert data["data"]["description"] == "Updated description"

    def test_delete_slideshow_success(self, client, authenticated_user, sample_slideshow):
        """Test successful slideshow deletion."""
        response = client.delete(f"/api/v1/slideshows/{sample_slideshow.id}")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        
        # Verify slideshow is soft-deleted
        slideshow = Slideshow.query.get(sample_slideshow.id)
        assert slideshow.is_active is False

    def test_delete_slideshow_assigned_to_display(self, client, authenticated_user, sample_slideshow):
        """Test slideshow deletion when assigned to display."""
        # Create display assigned to slideshow
        display = Display(
            name="test-display",
            current_slideshow_id=sample_slideshow.id
        )
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

    def test_list_slideshow_items(self, client, authenticated_user, sample_slideshow_with_items):
        """Test listing slideshow items."""
        slideshow, items = sample_slideshow_with_items
        
        response = client.get(f"/api/v1/slideshows/{slideshow.id}/items")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == len(items)

    def test_create_slideshow_item_success(self, client, authenticated_user, sample_slideshow):
        """Test successful slideshow item creation."""
        item_data = {
            "title": "Test Item",
            "content_type": "image",
            "content_url": "https://example.com/image.jpg",
            "display_duration": 15
        }
        
        response = client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(item_data),
            content_type="application/json"
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Item"
        assert data["data"]["content_type"] == "image"

    def test_create_slideshow_item_missing_content_type(self, client, authenticated_user, sample_slideshow):
        """Test slideshow item creation with missing content type."""
        item_data = {"title": "Invalid Item"}
        
        response = client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(item_data),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "errors" in data

    def test_create_slideshow_item_invalid_content_type(self, client, authenticated_user, sample_slideshow):
        """Test slideshow item creation with invalid content type."""
        item_data = {
            "content_type": "invalid_type",
            "content_url": "https://example.com/test"
        }
        
        response = client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(item_data),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_update_slideshow_item(self, client, authenticated_user, sample_slideshow_with_items):
        """Test slideshow item update."""
        slideshow, items = sample_slideshow_with_items
        item = items[0]
        
        update_data = {
            "title": "Updated Item",
            "display_duration": 20
        }
        
        response = client.put(
            f"/api/v1/slideshow-items/{item.id}",
            data=json.dumps(update_data),
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Item"
        assert data["data"]["display_duration"] == 20

    def test_delete_slideshow_item(self, client, authenticated_user, sample_slideshow_with_items):
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

    def test_reorder_slideshow_item(self, client, authenticated_user, sample_slideshow_with_items):
        """Test slideshow item reordering."""
        slideshow, items = sample_slideshow_with_items
        item = items[0]  # First item
        
        reorder_data = {"new_order": 3}  # Move to position 3
        
        response = client.post(
            f"/api/v1/slideshow-items/{item.id}/reorder",
            data=json.dumps(reorder_data),
            content_type="application/json"
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

    def test_update_display_slideshow_assignment(self, client, authenticated_user, sample_slideshow):
        """Test updating display slideshow assignment."""
        display = Display(name="test-display", owner_id=authenticated_user.id)
        db.session.add(display)
        db.session.commit()
        
        update_data = {"slideshow_id": sample_slideshow.id}
        
        response = client.put(
            f"/api/v1/displays/{display.id}",
            data=json.dumps(update_data),
            content_type="application/json"
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
            assert response.status_code in [302, 401]  # Redirect to login or unauthorized

    def test_api_access_control(self, client, app):
        """Test API access control between users."""
        # Create two users
        with app.app_context():
            user1 = User(username="user1", email="user1@example.com")
            user1.set_password("password")
            user2 = User(username="user2", email="user2@example.com") 
            user2.set_password("password")
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # User 1 creates a slideshow
            slideshow = Slideshow(name="User1 Slideshow", owner_id=user1.id, is_active=True)
            db.session.add(slideshow)
            db.session.commit()
            slideshow_id = slideshow.id
        
        # Login as user2
        client.post("/auth/login", data={"username": "user2", "password": "password"})
        
        # User2 should not be able to access user1's slideshow
        response = client.get(f"/api/v1/slideshows/{slideshow_id}")
        assert response.status_code == 403


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
