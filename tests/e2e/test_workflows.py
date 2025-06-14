"""
End-to-end tests for complete user workflows.

These tests simulate real user interactions with the application,
testing complete workflows from start to finish.
"""

from kiosk_show_replacement.models import Slideshow


class TestSlideshowCreationWorkflow:
    """Test complete slideshow creation workflow."""

    def test_create_slideshow_and_add_slides_workflow(self, client, app):
        """Test complete workflow: create slideshow, add slides, view result."""

        # Step 1: Start at homepage
        response = client.get("/")
        assert response.status_code == 200
        assert b"No Slideshows Available" in response.data

        # Step 2: Go to create slideshow page
        response = client.get("/slideshow/create")
        assert response.status_code == 200
        assert b"Create New Slideshow" in response.data

        # Step 3: Create a new slideshow
        response = client.post(
            "/slideshow/create",
            data={
                "name": "E2E Test Slideshow",
                "description": "End-to-end test slideshow",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Should be redirected to edit page
        assert b"Edit Slideshow: E2E Test Slideshow" in response.data

        # Get slideshow ID from database for API calls
        with app.app_context():
            slideshow = Slideshow.query.filter_by(name="E2E Test Slideshow").first()
            assert slideshow is not None
            slideshow_id = slideshow.id

        # Step 4: Add a text slide via API (simulating form submission)
        import json

        response = client.post(
            f"/api/slideshows/{slideshow_id}/slides",
            data=json.dumps(
                {
                    "title": "Welcome Slide",
                    "content_type": "text",
                    "content_text": "Welcome to our slideshow!",
                    "display_duration": 30,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Step 5: Add an image slide via API
        response = client.post(
            f"/api/slideshows/{slideshow_id}/slides",
            data=json.dumps(
                {
                    "title": "Sample Image",
                    "content_type": "image",
                    "content_url": "https://example.com/sample.jpg",
                    "display_duration": 45,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Step 6: View the slideshow in display mode
        response = client.get(f"/display/{slideshow_id}")
        assert response.status_code == 200
        assert b"E2E Test Slideshow" in response.data
        assert b"Welcome Slide" in response.data
        assert b"Sample Image" in response.data

        # Step 7: Verify slideshow appears on homepage
        response = client.get("/")
        assert response.status_code == 200
        assert b"E2E Test Slideshow" in response.data
        assert b"End-to-end test slideshow" in response.data
        assert b"2 slides" in response.data

        # Step 8: Verify slideshow management page
        response = client.get("/slideshow/")
        assert response.status_code == 200
        assert b"E2E Test Slideshow" in response.data
        assert b"2 slides" in response.data


class TestSlideshowManagementWorkflow:
    """Test slideshow management workflows."""

    def test_edit_slideshow_workflow(self, client, app, sample_slideshow):
        """Test editing slides in an existing slideshow."""

        # Step 1: Go to slideshow management
        response = client.get("/slideshow/")
        assert response.status_code == 200
        assert b"Test Slideshow" in response.data

        # Step 2: Go to edit slideshow
        response = client.get(f"/slideshow/{sample_slideshow.id}/edit")
        assert response.status_code == 200
        assert b"Test Image Slide" in response.data

        # Step 3: Update an existing slide via API
        with app.app_context():
            slide = sample_slideshow.slides[0]
            slide_id = slide.id

        import json

        response = client.put(
            f"/api/slides/{slide_id}",
            data=json.dumps({"title": "Updated Image Slide", "display_duration": 60}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Step 4: Verify update in display mode
        response = client.get(f"/display/{sample_slideshow.id}")
        assert response.status_code == 200
        assert b"Updated Image Slide" in response.data

        # Step 5: Delete a slide
        response = client.delete(f"/api/slides/{slide_id}")
        assert response.status_code == 200

        # Step 6: Verify slide is no longer in display
        response = client.get(f"/display/{sample_slideshow.id}")
        assert response.status_code == 200
        assert b"Updated Image Slide" not in response.data

    def test_slideshow_deletion_workflow(self, client, app, sample_slideshow):
        """Test deleting a slideshow."""
        slideshow_id = sample_slideshow.id

        # Step 1: Verify slideshow exists on homepage
        response = client.get("/")
        assert response.status_code == 200
        assert b"Test Slideshow" in response.data

        # Step 2: Delete slideshow
        response = client.post(
            f"/slideshow/{slideshow_id}/delete", follow_redirects=True
        )
        assert response.status_code == 200

        # Step 3: Verify slideshow no longer appears on homepage
        response = client.get("/")
        assert response.status_code == 200
        assert b"Test Slideshow" not in response.data

        # Step 4: Verify slideshow can't be displayed
        response = client.get(f"/display/{slideshow_id}")
        # Should either be 404 or show no slides (depending on implementation)
        assert response.status_code in [404, 200]


class TestContentTypeWorkflows:
    """Test workflows for different content types."""

    def test_text_slide_workflow(self, client, app, sample_slideshow):
        """Test creating and displaying text slides."""
        import json

        # Create text slide
        response = client.post(
            f"/api/slideshows/{sample_slideshow.id}/slides",
            data=json.dumps(
                {
                    "title": "Important Announcement",
                    "content_type": "text",
                    "content_text": "This is an important announcement for all users.",
                    "display_duration": 20,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Verify in display mode
        response = client.get(f"/display/{sample_slideshow.id}")
        assert response.status_code == 200
        assert b"Important Announcement" in response.data
        assert b"important announcement for all users" in response.data

    def test_image_slide_workflow(self, client, app, sample_slideshow):
        """Test creating and displaying image slides."""
        import json

        # Create image slide
        response = client.post(
            f"/api/slideshows/{sample_slideshow.id}/slides",
            data=json.dumps(
                {
                    "title": "Company Logo",
                    "content_type": "image",
                    "content_url": "https://example.com/logo.png",
                    "display_duration": 35,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Verify in display mode
        response = client.get(f"/display/{sample_slideshow.id}")
        assert response.status_code == 200
        assert b"Company Logo" in response.data
        assert b"https://example.com/logo.png" in response.data

    def test_webpage_slide_workflow(self, client, app, sample_slideshow):
        """Test creating and displaying webpage slides."""
        import json

        # Create webpage slide
        response = client.post(
            f"/api/slideshows/{sample_slideshow.id}/slides",
            data=json.dumps(
                {
                    "title": "Weather Dashboard",
                    "content_type": "url",
                    "content_url": "https://weather.example.com/dashboard",
                    "display_duration": 60,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Verify in display mode
        response = client.get(f"/display/{sample_slideshow.id}")
        assert response.status_code == 200
        assert b"Weather Dashboard" in response.data
        assert b"https://weather.example.com/dashboard" in response.data


class TestUserExperienceWorkflows:
    """Test complete user experience workflows."""

    def test_first_time_user_workflow(self, client, app):
        """Test complete workflow for first-time user."""

        # Step 1: First visit to homepage
        response = client.get("/")
        assert response.status_code == 200
        assert b"No Slideshows Available" in response.data
        assert b"Create Your First Slideshow" in response.data

        # Step 2: Click to create first slideshow
        response = client.get("/slideshow/create")
        assert response.status_code == 200

        # Step 3: Create slideshow
        response = client.post(
            "/slideshow/create",
            data={
                "name": "My First Slideshow",
                "description": "Getting started with digital signage",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Step 4: Add first slide
        with app.app_context():
            slideshow = Slideshow.query.filter_by(name="My First Slideshow").first()
            slideshow_id = slideshow.id

        import json

        response = client.post(
            f"/api/slideshows/{slideshow_id}/slides",
            data=json.dumps(
                {
                    "title": "Welcome",
                    "content_type": "text",
                    "content_text": "Welcome to digital signage!",
                    "display_duration": 30,
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

        # Step 5: Preview slideshow
        response = client.get(f"/display/{slideshow_id}")
        assert response.status_code == 200
        assert b"My First Slideshow" in response.data
        assert b"Welcome to digital signage!" in response.data

        # Step 6: Return to homepage - should now show slideshow
        response = client.get("/")
        assert response.status_code == 200
        assert b"My First Slideshow" in response.data
        assert b"Getting started with digital signage" in response.data
        assert b"1 slides" in response.data

    def test_error_recovery_workflow(self, client):
        """Test error recovery workflows."""

        # Test accessing non-existent slideshow
        response = client.get("/display/99999")
        assert response.status_code == 404

        # Test invalid API requests
        import json

        response = client.post(
            "/api/slideshows/99999/slides",
            data=json.dumps({"invalid": "data"}),
            content_type="application/json",
        )
        assert response.status_code == 404

        # Test malformed requests
        response = client.post(
            "/api/slideshows", data="invalid json", content_type="application/json"
        )
        assert response.status_code in [400, 422]
