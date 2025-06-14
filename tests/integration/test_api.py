"""
Integration tests for API endpoints.

Tests the REST API endpoints for slideshow and slide management
including proper HTTP status codes, JSON responses, and database integration.
"""

import json

from kiosk_show_replacement.models import SlideItem, Slideshow


class TestSlideshowAPI:
    """Integration tests for slideshow API endpoints."""

    def test_list_slideshows_empty(self, client):
        """Test listing slideshows when none exist."""
        response = client.get("/api/slideshows")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_slideshows_with_data(self, client, sample_slideshow):
        """Test listing slideshows with existing data."""
        response = client.get("/api/slideshows")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

        slideshow_data = data[0]
        assert slideshow_data["name"] == "Test Slideshow"
        assert slideshow_data["description"] == "A slideshow for testing"
        assert slideshow_data["is_active"] is True

    def test_create_slideshow_valid(self, client, app):
        """Test creating a new slideshow with valid data."""
        slideshow_data = {
            "name": "New Test Slideshow",
            "description": "A newly created slideshow",
        }

        response = client.post(
            "/api/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["name"] == slideshow_data["name"]
        assert data["description"] == slideshow_data["description"]
        assert "id" in data

        # Verify in database
        with app.app_context():
            slideshow = Slideshow.query.get(data["id"])
            assert slideshow is not None
            assert slideshow.name == slideshow_data["name"]

    def test_create_slideshow_missing_name(self, client):
        """Test creating slideshow without required name field."""
        slideshow_data = {"description": "Missing name field"}

        response = client.post(
            "/api/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_slideshow_duplicate_name(self, client, sample_slideshow):
        """Test creating slideshow with duplicate name."""
        slideshow_data = {
            "name": "Test Slideshow",  # Same as sample_slideshow
            "description": "Duplicate name",
        }

        response = client.post(
            "/api/slideshows",
            data=json.dumps(slideshow_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_get_slideshow_details(self, client, sample_slideshow):
        """Test getting slideshow details including slides."""
        response = client.get(f"/api/slideshows/{sample_slideshow.id}")

        assert response.status_code == 200
        data = response.get_json()

        assert data["name"] == sample_slideshow.name
        assert data["description"] == sample_slideshow.description
        assert "slides" in data
        assert len(data["slides"]) == 3  # From sample_slideshow fixture

        # Check slide data structure
        slide = data["slides"][0]
        assert "id" in slide
        assert "title" in slide
        assert "content_type" in slide
        assert "display_duration" in slide

    def test_get_nonexistent_slideshow(self, client):
        """Test getting details for non-existent slideshow."""
        response = client.get("/api/slideshows/99999")

        assert response.status_code == 404


class TestSlideAPI:
    """Integration tests for slide management API endpoints."""

    def test_add_text_slide(self, client, app, sample_slideshow):
        """Test adding a text slide to a slideshow."""
        slide_data = {
            "title": "New Text Slide",
            "content_type": "text",
            "content_text": "This is new text content",
            "display_duration": 25,
        }

        response = client.post(
            f"/api/slideshows/{sample_slideshow.id}/slides",
            data=json.dumps(slide_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["title"] == slide_data["title"]
        assert data["content_type"] == slide_data["content_type"]
        assert data["content_text"] == slide_data["content_text"]
        assert data["display_duration"] == slide_data["display_duration"]
        assert data["slideshow_id"] == sample_slideshow.id

        # Verify in database
        with app.app_context():
            slide = SlideItem.query.get(data["id"])
            assert slide is not None
            assert slide.title == slide_data["title"]

    def test_add_image_slide(self, client, app, sample_slideshow):
        """Test adding an image slide to a slideshow."""
        slide_data = {
            "title": "New Image Slide",
            "content_type": "image",
            "content_url": "https://example.com/new-image.jpg",
            "display_duration": 40,
        }

        response = client.post(
            f"/api/slideshows/{sample_slideshow.id}/slides",
            data=json.dumps(slide_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data["content_type"] == "image"
        assert data["content_url"] == slide_data["content_url"]

    def test_add_slide_missing_content_type(self, client, sample_slideshow):
        """Test adding slide without required content_type."""
        slide_data = {"title": "Invalid Slide"}

        response = client.post(
            f"/api/slideshows/{sample_slideshow.id}/slides",
            data=json.dumps(slide_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_update_slide(self, client, app, sample_slideshow):
        """Test updating an existing slide."""
        # Get first slide from sample slideshow
        with app.app_context():
            slide = sample_slideshow.slides[0]
            slide_id = slide.id

        update_data = {"title": "Updated Slide Title", "display_duration": 60}

        response = client.put(
            f"/api/slides/{slide_id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["title"] == update_data["title"]
        assert data["display_duration"] == update_data["display_duration"]

        # Verify in database
        with app.app_context():
            updated_slide = SlideItem.query.get(slide_id)
            assert updated_slide.title == update_data["title"]
            assert updated_slide.display_duration == update_data["display_duration"]

    def test_delete_slide(self, client, app, sample_slideshow):
        """Test deleting a slide (soft delete)."""
        # Get first slide from sample slideshow
        with app.app_context():
            slide = sample_slideshow.slides[0]
            slide_id = slide.id

        response = client.delete(f"/api/slides/{slide_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data

        # Verify slide is soft deleted (is_active = False)
        with app.app_context():
            deleted_slide = SlideItem.query.get(slide_id)
            assert deleted_slide is not None  # Still exists in DB
            assert deleted_slide.is_active is False  # But marked inactive

    def test_update_nonexistent_slide(self, client):
        """Test updating a non-existent slide."""
        update_data = {"title": "Updated Title"}

        response = client.put(
            "/api/slides/99999",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_nonexistent_slide(self, client):
        """Test deleting a non-existent slide."""
        response = client.delete("/api/slides/99999")

        assert response.status_code == 404


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_json(self, client):
        """Test API response to invalid JSON."""
        response = client.post(
            "/api/slideshows", data="invalid json", content_type="application/json"
        )

        # Should handle invalid JSON gracefully
        assert response.status_code in [400, 422]

    def test_missing_content_type_header(self, client):
        """Test API response when Content-Type header is missing."""
        slideshow_data = {"name": "Test Slideshow"}

        response = client.post(
            "/api/slideshows",
            data=json.dumps(slideshow_data),
            # No content_type specified
        )

        # Should still work or give appropriate error
        assert response.status_code in [200, 201, 400, 415]
