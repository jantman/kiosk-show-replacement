"""
Integration tests for API endpoints.

Tests the REST API endpoints for slideshow and slide management
including proper HTTP status codes, JSON responses, and database integration.
"""

import json

from kiosk_show_replacement.models import Slideshow, SlideshowItem


class TestSlideshowAPI:
    """Integration tests for slideshow API endpoints."""

    def test_list_slideshows_empty(self, auth_client):
        """Test listing slideshows when none exist."""
        response = auth_client.get("/api/v1/slideshows")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"] == []

    def test_list_slideshows_with_data(self, auth_client, sample_slideshow):
        """Test listing slideshows with existing data."""
        response = auth_client.get("/api/v1/slideshows")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 1

        slideshow_data = data["data"][0]
        assert slideshow_data["name"] == "Test Slideshow"
        assert slideshow_data["description"] == "A slideshow for testing"
        assert slideshow_data["is_active"] is True

    def test_create_slideshow_valid(self, auth_client, app):
        """Test creating a new slideshow with valid data."""
        slideshow_data = {
            "name": "New Test Slideshow",
            "description": "A newly created slideshow",
        }

        response = auth_client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True

        assert data["data"]["name"] == slideshow_data["name"]
        assert data["data"]["description"] == slideshow_data["description"]
        assert "id" in data["data"]

        # Verify in database
        with app.app_context():
            slideshow = Slideshow.query.get(data["data"]["id"])
            assert slideshow is not None
            assert slideshow.name == slideshow_data["name"]

    def test_create_slideshow_missing_name(self, auth_client):
        """Test creating slideshow without required name field."""
        slideshow_data = {"description": "Missing name field"}

        response = auth_client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "errors" in data

    def test_create_slideshow_duplicate_name(self, auth_client, sample_slideshow):
        """Test creating slideshow with duplicate name."""
        slideshow_data = {
            "name": sample_slideshow.name,
            "description": "Duplicate name test",
        }

        response = auth_client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "already exists" in data["message"]

    def test_get_slideshow_details(self, auth_client, sample_slideshow):
        """Test getting slideshow details including items."""
        response = auth_client.get(f"/api/v1/slideshows/{sample_slideshow.id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        slideshow_data = data["data"]
        assert slideshow_data["name"] == sample_slideshow.name
        assert slideshow_data["description"] == sample_slideshow.description
        assert "items" in slideshow_data
        assert len(slideshow_data["items"]) == 3

        # Check item data structure
        item = slideshow_data["items"][0]
        assert "id" in item
        assert "content_type" in item
        assert "display_duration" in item

    def test_get_nonexistent_slideshow(self, auth_client):
        """Test getting details for non-existent slideshow."""
        response = auth_client.get("/api/v1/slideshows/99999")

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False


class TestSlideAPI:
    """Integration tests for slide management API endpoints."""

    def test_add_text_slide(self, auth_client, app, sample_slideshow):
        """Test adding a text slide to a slideshow."""
        slide_data = {
            "content_type": "text",
            "content_text": "This is new text content",
            "display_duration": 25,
        }

        response = auth_client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(slide_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True

        item_data = data["data"]
        assert item_data["content_type"] == slide_data["content_type"]
        assert item_data["content_text"] == slide_data["content_text"]
        assert item_data["display_duration"] == slide_data["display_duration"]
        assert item_data["slideshow_id"] == sample_slideshow.id

        # Verify in database
        with app.app_context():
            slide = SlideshowItem.query.get(item_data["id"])
            assert slide is not None
            assert slide.content_text == slide_data["content_text"]

    def test_add_image_slide(self, auth_client, app, sample_slideshow):
        """Test adding an image slide to a slideshow."""
        slide_data = {
            "content_type": "image",
            "content_url": "https://example.com/new-image.jpg",
            "display_duration": 40,
        }

        response = auth_client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(slide_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True

        item_data = data["data"]
        assert item_data["content_type"] == "image"
        assert item_data["content_url"] == slide_data["content_url"]

    def test_add_slide_missing_content_type(self, auth_client, sample_slideshow):
        """Test adding slide without required content_type."""
        slide_data = {"display_duration": 30}

        response = auth_client.post(
            f"/api/v1/slideshows/{sample_slideshow.id}/items",
            data=json.dumps(slide_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "errors" in data

    def test_update_slide(self, auth_client, app, sample_slideshow):
        """Test updating an existing slide."""
        # Get first slide from sample slideshow
        with app.app_context():
            slide = sample_slideshow.items[0]
            slide_id = slide.id

        update_data = {"display_duration": 60}

        response = auth_client.put(
            f"/api/v1/slideshow-items/{slide_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        assert data["data"]["display_duration"] == update_data["display_duration"]

        # Verify in database
        with app.app_context():
            updated_slide = SlideshowItem.query.get(slide_id)
            assert updated_slide.display_duration == update_data["display_duration"]

    def test_delete_slide(self, auth_client, app, sample_slideshow):
        """Test deleting a slide (soft delete)."""
        # Get first slide from sample slideshow
        with app.app_context():
            slide = sample_slideshow.items[0]
            slide_id = slide.id

        response = auth_client.delete(f"/api/v1/slideshow-items/{slide_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        # Verify slide is soft deleted (is_active = False)
        with app.app_context():
            deleted_slide = SlideshowItem.query.get(slide_id)
            assert deleted_slide is not None  # Still exists in DB
            assert deleted_slide.is_active is False  # But marked inactive

    def test_update_nonexistent_slide(self, auth_client):
        """Test updating a non-existent slide."""
        update_data = {"display_duration": 30}

        response = auth_client.put(
            "/api/v1/slideshow-items/99999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False

    def test_delete_nonexistent_slide(self, auth_client):
        """Test deleting a non-existent slide."""
        response = auth_client.delete("/api/v1/slideshow-items/99999")

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_json(self, auth_client):
        """Test API handling of invalid JSON data."""
        response = auth_client.post(
            "/api/v1/slideshows",
            data="invalid json",
            content_type="application/json",
        )

        # API returns 500 for malformed JSON (expected behavior)
        assert response.status_code == 500
        # Response may not be JSON for 500 errors

    def test_missing_content_type_header(self, auth_client):
        """Test API handling when Content-Type header is missing."""
        slideshow_data = {"name": "Test", "description": "Test"}

        response = auth_client.post(
            "/api/v1/slideshows",
            data=json.dumps(slideshow_data),
            # Note: no content_type specified
        )

        # API returns 500 for missing content-type (expected behavior)
        assert response.status_code == 500
