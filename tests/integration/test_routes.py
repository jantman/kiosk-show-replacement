"""
Integration tests for web interface routes.

Tests the HTML interfaces for slideshow management and display,
including form handling and template rendering.
"""

from kiosk_show_replacement.models import Slideshow


class TestDisplayRoutes:
    """Integration tests for display interface routes."""

    def test_homepage_no_slideshows(self, auth_client):
        """Test homepage when no slideshows exist."""
        response = auth_client.get("/")

        assert response.status_code == 200
        assert b"No slideshows found." in response.data
        assert b"Manage Slideshows" in response.data

    def test_homepage_with_slideshows(self, auth_client, sample_slideshow):
        """Test homepage with existing slideshows."""
        response = auth_client.get("/")

        assert response.status_code == 200
        assert b"Test Slideshow" in response.data
        assert b"A slideshow for testing" in response.data
        assert b"slides" in response.data

    def test_display_slideshow(self, client, sample_slideshow):
        """Test slideshow display interface."""
        response = client.get(f"/display/slideshow/{sample_slideshow.id}")

        assert response.status_code == 200
        assert b"Test Slideshow" in response.data
        assert b"slideshow-container" in response.data
        # Check that slide data is embedded in the template
        assert b"Test Image Slide" in response.data
        assert b"Test Text Slide" in response.data

    def test_display_nonexistent_slideshow(self, auth_client):
        """Test displaying non-existent slideshow."""
        response = auth_client.get("/display/slideshow/99999")

        assert response.status_code == 404

    def test_slideshow_slides_api_endpoint(self, auth_client, sample_slideshow):
        """Test the AJAX endpoint for getting slideshow slides."""
        response = auth_client.get(f"/api/v1/slideshows/{sample_slideshow.id}/items")

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 3  # sample_slideshow has 3 items


class TestSlideshowManagementRoutes:
    """Integration tests for slideshow management interface."""

    def test_slideshow_list_empty(self, client):
        """Test slideshow management page when empty."""
        response = client.get("/slideshow/")

        assert response.status_code == 200
        assert b"No Slideshows Found" in response.data
        assert b"Create Your First Slideshow" in response.data

    def test_slideshow_list_with_data(self, auth_client, sample_slideshow):
        """Test slideshow management page with data."""
        response = auth_client.get("/slideshow/")

        assert response.status_code == 200
        assert b"Test Slideshow" in response.data
        assert b"A slideshow for testing" in response.data
        assert b"3 slides" in response.data
        assert b"Active" in response.data

    def test_create_slideshow_get(self, auth_client):
        """Test GET request to create slideshow page."""
        response = auth_client.get("/slideshow/create")

        assert response.status_code == 200
        assert b"Create New Slideshow" in response.data
        assert b'name="name"' in response.data
        assert b'name="description"' in response.data

    def test_create_slideshow_post_valid(self, auth_client, app):
        """Test POST request to create slideshow with valid data."""
        response = auth_client.post(
            "/slideshow/create",
            data={
                "name": "New Slideshow",
                "description": "A new slideshow for testing",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that slideshow was created in database
        with app.app_context():
            slideshow = Slideshow.query.filter_by(name="New Slideshow").first()
            assert slideshow is not None
            assert slideshow.description == "A new slideshow for testing"

    def test_create_slideshow_post_missing_name(self, client):
        """Test POST request to create slideshow without name."""
        response = client.post(
            "/slideshow/create", data={"description": "Missing name"}
        )

        assert response.status_code == 200
        assert b"Name is required" in response.data or b"error" in response.data

    def test_edit_slideshow(self, auth_client, sample_slideshow):
        """Test slideshow edit page."""
        response = auth_client.get(f"/slideshow/{sample_slideshow.id}/edit")

        assert response.status_code == 200
        assert b"Edit Slideshow: Test Slideshow" in response.data
        assert b"Test Image Slide" in response.data
        assert b"Test Text Slide" in response.data
        assert b"Test Web Slide" in response.data

        # Check that add slide form is present
        assert b"Add New Slide" in response.data
        assert b"contentType" in response.data

    def test_edit_nonexistent_slideshow(self, client):
        """Test editing non-existent slideshow."""
        response = client.get("/slideshow/99999/edit")

        assert response.status_code == 404

    def test_delete_slideshow(self, client, app, sample_slideshow):
        """Test slideshow deletion (soft delete)."""
        slideshow_id = sample_slideshow.id

        response = client.post(
            f"/slideshow/{slideshow_id}/delete", follow_redirects=True
        )

        assert response.status_code == 200

        # Check that slideshow is soft deleted
        with app.app_context():
            slideshow = Slideshow.query.get(slideshow_id)
            assert slideshow is not None  # Still exists
            assert slideshow.is_active is False  # But marked inactive

    def test_delete_nonexistent_slideshow(self, client):
        """Test deleting non-existent slideshow."""
        response = client.post("/slideshow/99999/delete")

        assert response.status_code == 404


class TestTemplateRendering:
    """Test template rendering and context variables."""

    def test_base_template_elements(self, auth_client):
        """Test that base template elements are rendered."""
        response = auth_client.get("/")

        assert response.status_code == 200
        assert b"Kiosk Show Replacement" in response.data
        assert b"navbar" in response.data
        assert b"Bootstrap" in response.data or b"bootstrap" in response.data

    def test_responsive_design_meta_tags(self, auth_client):
        """Test that responsive design meta tags are present."""
        response = auth_client.get("/")

        assert response.status_code == 200
        assert b"viewport" in response.data
        assert b"width=device-width" in response.data

    def test_navigation_links(self, auth_client):
        """Test that navigation links are present."""
        response = auth_client.get("/")

        assert response.status_code == 200
        assert b"Home" in response.data
        assert b"Manage Slideshows" in response.data

    def test_slideshow_display_template_structure(self, client, sample_slideshow):
        """Test slideshow display template has required structure."""
        response = client.get(f"/display/slideshow/{sample_slideshow.id}")

        assert response.status_code == 200

        # Check for required CSS classes and IDs
        assert b"slideshow-container" in response.data
        assert b"slide-info" in response.data
        assert b"progress-bar" in response.data

        # Check for JavaScript functionality
        assert b"SlideshowPlayer" in response.data
        assert b"showSlide" in response.data


class TestFormHandling:
    """Test form handling and validation."""

    def test_csrf_protection_disabled_in_tests(self, client):
        """Test that CSRF protection is disabled for testing."""
        # This test ensures our test configuration is correct
        response = client.post(
            "/slideshow/create",
            data={"name": "Test CSRF", "description": "Testing CSRF"},
        )

        # Should not get CSRF error
        assert response.status_code != 403

    def test_form_validation_messages(self, client):
        """Test that form validation messages are displayed."""
        response = client.post(
            "/slideshow/create", data={"description": "Missing name field"}
        )

        assert response.status_code == 200
        # Should show validation error
        assert b"required" in response.data or b"error" in response.data
