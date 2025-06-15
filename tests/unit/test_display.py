"""
Tests for display views and functionality.

Tests the core display interface including registration, slideshow assignment,
resolution detection, heartbeat monitoring, and slideshow rendering.
"""

import json
from datetime import datetime, timedelta, timezone

from kiosk_show_replacement.models import Display, Slideshow, SlideshowItem, db


class TestDisplayRegistration:
    """Test display auto-registration functionality."""

    def test_display_auto_registration(self, client):
        """Test that displays are automatically registered on first connection."""
        display_name = "test-kiosk-01"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200

        # Verify display was created in database
        display = Display.query.filter_by(name=display_name).first()
        assert display is not None
        assert display.name == display_name
        assert display.owner_id is None  # No owner for auto-registered displays

    def test_display_resolution_detection(self, client):
        """Test resolution detection via heartbeat."""
        display_name = "test-kiosk-02"

        # First, visit display to register it
        client.get(f"/display/{display_name}")

        # Send heartbeat with resolution
        resolution_data = {"width": 1920, "height": 1080}
        response = client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps(resolution_data),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify resolution was stored
        display = Display.query.filter_by(name=display_name).first()
        assert display.resolution_width == 1920
        assert display.resolution_height == 1080
        assert display.last_seen_at is not None

    def test_display_heartbeat_updates_last_seen(self, client):
        """Test that heartbeat updates last_seen timestamp."""
        display_name = "test-kiosk-03"

        # Register display
        client.get(f"/display/{display_name}")
        display = Display.query.filter_by(name=display_name).first()
        original_last_seen = display.last_seen_at

        # Wait a moment and send heartbeat
        import time

        time.sleep(0.1)

        response = client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify last_seen was updated
        db.session.refresh(display)
        assert display.last_seen_at > original_last_seen


class TestSlideshowAssignment:
    """Test slideshow assignment logic."""

    def test_default_slideshow_assignment(self, client, sample_slideshow):
        """Test automatic assignment of default slideshow to new displays."""
        # Set slideshow as default
        sample_slideshow.is_default = True
        db.session.commit()

        display_name = "test-kiosk-04"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200
        assert sample_slideshow.name.encode() in response.data

        # Verify assignment in database
        display = Display.query.filter_by(name=display_name).first()
        assert display.current_slideshow_id == sample_slideshow.id

    def test_no_default_shows_configuration_page(self, client):
        """Test that displays show config page when no default slideshow exists."""
        display_name = "test-kiosk-05"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200
        assert b"Display Configuration Required" in response.data
        assert display_name.encode() in response.data

    def test_specific_slideshow_assignment_overrides_default(
        self, client, sample_slideshow
    ):
        """Test that specific slideshow assignment overrides default."""
        # Create default slideshow
        from kiosk_show_replacement.models import User

        user = User(username="testuser_override", email="testoverride@example.com")
        user.set_password("testpass")
        db.session.add(user)
        db.session.flush()

        default_slideshow = Slideshow(
            name="Default Slideshow",
            description="Default",
            owner_id=user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(default_slideshow)

        # Create display and assign specific slideshow
        display = Display(
            name="test-kiosk-06",
            owner_id=None,
            current_slideshow_id=sample_slideshow.id,
        )
        db.session.add(display)
        db.session.commit()

        response = client.get(f"/display/{display.name}")

        assert response.status_code == 200
        assert sample_slideshow.name.encode() in response.data
        assert default_slideshow.name.encode() not in response.data

    def test_empty_slideshow_shows_no_content_page(self, client, sample_slideshow):
        """Test that empty slideshows show no content page."""
        # Remove all slides from slideshow
        SlideshowItem.query.filter_by(slideshow_id=sample_slideshow.id).delete()
        sample_slideshow.is_default = True
        db.session.commit()

        display_name = "test-kiosk-07"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200
        assert b"No Content Available" in response.data
        assert sample_slideshow.name.encode() in response.data


class TestSlideshowRendering:
    """Test slideshow rendering and display."""

    def test_slideshow_rendering_with_slides(self, client, sample_slideshow_with_items):
        """Test that slideshows with content render properly."""
        slideshow, items = sample_slideshow_with_items
        slideshow.is_default = True
        db.session.commit()

        display_name = "test-kiosk-08"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200
        assert slideshow.name.encode() in response.data
        assert b"SlideshowPlayer" in response.data

        # Check that slide data is included
        for item in items:
            assert item.content_type.encode() in response.data

    def test_slideshow_includes_resolution_detection(
        self, client, sample_slideshow_with_items
    ):
        """Test that slideshow includes resolution detection JavaScript."""
        slideshow, _ = sample_slideshow_with_items
        slideshow.is_default = True
        db.session.commit()

        display_name = "test-kiosk-09"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200
        assert b"screen.width" in response.data
        assert b"screen.height" in response.data
        assert b"sendHeartbeat" in response.data

    def test_slideshow_content_types_rendered(self, client, sample_user):
        """Test that different content types are rendered correctly."""
        # Create slideshow with different content types
        slideshow = Slideshow(
            name="Mixed Content",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(slideshow)
        db.session.flush()

        # Add different content types
        items = [
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                content_url="https://example.com/image.jpg",
                display_duration=5,
                order_index=1,
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="video",
                content_url="https://example.com/video.mp4",
                display_duration=10,
                order_index=2,
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="url",
                content_url="https://example.com",
                display_duration=15,
                order_index=3,
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="text",
                content_text="Sample text content",
                display_duration=8,
                order_index=4,
            ),
        ]
        db.session.add_all(items)
        db.session.commit()

        display_name = "test-kiosk-10"
        response = client.get(f"/display/{display_name}")

        assert response.status_code == 200

        # Check that all content types are handled
        assert b"case 'image'" in response.data
        assert b"case 'video'" in response.data
        assert b"case 'url'" in response.data
        assert b"case 'text'" in response.data


class TestDisplayStatus:
    """Test display status and monitoring functionality."""

    def test_display_status_endpoint(self, client):
        """Test display status endpoint returns correct information."""
        display_name = "test-kiosk-11"

        # Register display and send heartbeat
        client.get(f"/display/{display_name}")
        client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )

        response = client.get(f"/display/{display_name}/status")

        assert response.status_code == 200
        data = response.get_json()

        assert data["name"] == display_name
        assert data["resolution"]["width"] == 1920
        assert data["resolution"]["height"] == 1080
        assert data["online"] is True
        assert "last_seen_at" in data

    def test_offline_display_status(self, client):
        """Test that displays are marked offline after timeout."""
        display_name = "test-kiosk-12"

        # Create display with old last_seen_at timestamp
        display = Display(
            name=display_name,
            owner_id=None,
            last_seen_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        db.session.add(display)
        db.session.commit()

        response = client.get(f"/display/{display_name}/status")

        assert response.status_code == 200
        data = response.get_json()
        assert data["online"] is False

    def test_display_info_page(self, client, sample_slideshow_with_items):
        """Test display info page shows correct information."""
        slideshow, items = sample_slideshow_with_items
        display_name = "test-kiosk-13"

        # Create display with slideshow assignment
        display = Display(
            name=display_name,
            owner_id=None,
            current_slideshow_id=slideshow.id,
            resolution_width=1920,
            resolution_height=1080,
            last_seen_at=datetime.now(timezone.utc),
        )
        db.session.add(display)
        db.session.commit()

        response = client.get(f"/display/{display_name}/info")

        assert response.status_code == 200
        assert display_name.encode() in response.data
        assert slideshow.name.encode() in response.data
        assert b"1920" in response.data
        assert b"1080" in response.data
        assert b"Online" in response.data


class TestErrorHandling:
    """Test error handling and resilience."""

    def test_invalid_heartbeat_data(self, client):
        """Test handling of invalid heartbeat data."""
        display_name = "test-kiosk-14"

        # Register display first
        client.get(f"/display/{display_name}")

        # Send invalid JSON
        response = client.post(
            f"/display/{display_name}/heartbeat",
            data="invalid json",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_missing_display_graceful_handling(self, client):
        """Test that missing displays are handled gracefully."""
        response = client.get("/display/nonexistent-display/status")

        # Should create the display and return status
        assert response.status_code == 200

        # Verify display was created
        display = Display.query.filter_by(name="nonexistent-display").first()
        assert display is not None

    def test_inactive_slideshow_not_rendered(self, client):
        """Test that inactive slideshows are not rendered."""
        from kiosk_show_replacement.models import User

        user = User(username="testuser_inactive", email="testinactive@example.com")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.flush()

        # Create inactive slideshow
        slideshow = Slideshow(
            name="Inactive Slideshow",
            owner_id=user.id,
            is_default=True,
            is_active=False,  # Inactive
        )
        db.session.add(slideshow)
        db.session.commit()

        display_name = "test-kiosk-15"
        response = client.get(f"/display/{display_name}")

        # Should show configuration page since inactive slideshow ignored
        assert response.status_code == 200
        assert b"Display Configuration Required" in response.data


class TestHeartbeatSystem:
    """Test the heartbeat and monitoring system."""

    def test_heartbeat_without_resolution(self, client):
        """Test heartbeat without resolution data."""
        display_name = "test-kiosk-16"

        # Register display
        client.get(f"/display/{display_name}")

        # Send heartbeat without resolution
        response = client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify last_seen_at was updated but resolution remains None
        display = Display.query.filter_by(name=display_name).first()
        assert display.last_seen_at is not None
        assert display.resolution_width is None
        assert display.resolution_height is None

    def test_partial_resolution_data(self, client):
        """Test heartbeat with partial resolution data."""
        display_name = "test-kiosk-17"

        # Register display
        client.get(f"/display/{display_name}")

        # Send heartbeat with only width
        response = client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify only width was stored
        display = Display.query.filter_by(name=display_name).first()
        assert display.resolution_width == 1920
        assert display.resolution_height is None

    def test_resolution_update_overwrites_previous(self, client):
        """Test that new resolution data overwrites previous values."""
        display_name = "test-kiosk-18"

        # Register display
        client.get(f"/display/{display_name}")

        # Send initial resolution
        client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )

        # Send updated resolution
        response = client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 2560, "height": 1440}),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify resolution was updated
        display = Display.query.filter_by(name=display_name).first()
        assert display.resolution_width == 2560
        assert display.resolution_height == 1440
