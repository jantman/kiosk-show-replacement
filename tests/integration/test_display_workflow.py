"""
Integration tests for display functionality.

Tests end-to-end display workflows including registration, slideshow assignment,
and playback cycles.
"""

import json
from datetime import datetime, timedelta, timezone

from kiosk_show_replacement.models import Display, Slideshow, SlideshowItem, db


class TestCompleteDisplayWorkflow:
    """Test complete display workflows from registration to playback."""

    def test_new_display_complete_workflow(self, auth_client, sample_user):
        """Test complete workflow for a new display."""
        display_name = "integration-test-display"

        # Step 1: First connection - should show configuration page
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Display Configuration Required" in response.data

        # Verify display was registered
        display = Display.query.filter_by(name=display_name).first()
        assert display is not None
        assert display.name == display_name

        # Step 2: Create a slideshow and set as default
        slideshow = Slideshow(
            name="Integration Test Slideshow",
            description="Test slideshow for integration testing",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(slideshow)
        db.session.flush()

        # Add slides to slideshow
        slides = [
            SlideshowItem(
                slideshow_id=slideshow.id,
                title="Welcome Slide",
                content_type="text",
                content_text="Welcome to our digital signage system!",
                display_duration=10,
                order_index=1,
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                title="Image Slide",
                content_type="image",
                content_url="https://example.com/welcome.jpg",
                display_duration=8,
                order_index=2,
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                title="Web Page",
                content_type="url",
                content_url="https://example.com/dashboard",
                display_duration=15,
                order_index=3,
            ),
        ]
        db.session.add_all(slides)
        db.session.commit()

        # Step 3: Reload display - should now show slideshow
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert slideshow.name.encode() in response.data
        assert b"SlideshowPlayer" in response.data

        # Verify slideshow was auto-assigned
        db.session.refresh(display)
        assert display.current_slideshow_id == slideshow.id

        # Step 4: Send heartbeat with resolution
        heartbeat_response = auth_client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )
        assert heartbeat_response.status_code == 200

        # Step 5: Check status
        status_response = auth_client.get(f"/display/{display_name}/status")
        assert status_response.status_code == 200

        status_data = status_response.get_json()
        assert status_data["name"] == display_name
        assert status_data["online"] is True
        assert status_data["slideshow"]["name"] == slideshow.name
        assert len(status_data["slideshow"]["slides"]) == 3

    def test_display_slideshow_change_workflow(self, auth_client, sample_user):
        """Test workflow when display slideshow is changed."""
        display_name = "slideshow-change-test"

        # Create initial slideshow
        initial_slideshow = Slideshow(
            name="Initial Slideshow",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(initial_slideshow)
        db.session.flush()

        slide1 = SlideshowItem(
            slideshow_id=initial_slideshow.id,
            content_type="text",
            content_text="Initial content",
            display_duration=5,
            order_index=1,
        )
        db.session.add(slide1)

        # Register display and verify initial assignment
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Initial Slideshow" in response.data

        # Create new slideshow
        new_slideshow = Slideshow(
            name="New Slideshow",
            owner_id=sample_user.id,
            is_active=True,
        )
        db.session.add(new_slideshow)
        db.session.flush()

        slide2 = SlideshowItem(
            slideshow_id=new_slideshow.id,
            content_type="text",
            content_text="New content",
            display_duration=7,
            order_index=1,
        )
        db.session.add(slide2)

        # Manually assign new slideshow to display
        display = Display.query.filter_by(name=display_name).first()
        display.current_slideshow_id = new_slideshow.id
        db.session.commit()

        # Reload display - should show new slideshow
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"New Slideshow" in response.data
        assert b"New content" in response.data
        assert b"Initial content" not in response.data

    def test_default_slideshow_change_workflow(self, auth_client, sample_user):
        """Test workflow when default slideshow changes."""
        # Create first default slideshow
        old_default = Slideshow(
            name="Old Default",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(old_default)
        db.session.flush()

        slide1 = SlideshowItem(
            slideshow_id=old_default.id,
            content_type="text",
            content_text="Old default content",
            display_duration=5,
            order_index=1,
        )
        db.session.add(slide1)

        # Register display with old default
        display_name = "default-change-test"
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Old Default" in response.data

        # Create new default slideshow
        new_default = Slideshow(
            name="New Default",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(new_default)
        db.session.flush()

        slide2 = SlideshowItem(
            slideshow_id=new_default.id,
            content_type="text",
            content_text="New default content",
            display_duration=7,
            order_index=1,
        )
        db.session.add(slide2)

        # Update old default to not be default anymore
        old_default.is_default = False
        db.session.commit()

        # Register new display - should get new default
        new_display_name = "new-display-default-test"
        response = auth_client.get(f"/display/{new_display_name}")
        assert response.status_code == 200
        assert b"New Default" in response.data

        # Existing display should keep old assignment until manually changed
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Old Default" in response.data

    def test_slideshow_deletion_workflow(self, auth_client, sample_user):
        """Test workflow when assigned slideshow is deleted."""
        display_name = "deletion-test-display"

        # Create slideshow
        slideshow = Slideshow(
            name="To Be Deleted",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(slideshow)
        db.session.flush()

        slide = SlideshowItem(
            slideshow_id=slideshow.id,
            content_type="text",
            content_text="This will be deleted",
            display_duration=5,
            order_index=1,
        )
        db.session.add(slide)
        db.session.commit()

        # Register display
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"To Be Deleted" in response.data

        # Delete slideshow (mark as inactive)
        slideshow.is_active = False
        slideshow.is_default = False
        db.session.commit()

        # Reload display - should show configuration page
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Display Configuration Required" in response.data


class TestDisplayMonitoringIntegration:
    """Test display monitoring and status tracking integration."""

    def test_display_online_offline_cycle(self, auth_client):
        """Test complete online/offline detection cycle."""
        display_name = "monitoring-test-display"

        # Register display
        auth_client.get(f"/display/{display_name}")

        # Send heartbeat - should be online
        auth_client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )

        # Check status - should be online
        response = auth_client.get(f"/display/{display_name}/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["online"] is True
        assert data["resolution"]["width"] == 1920

        # Simulate display going offline by updating last_seen_at to old timestamp
        display = Display.query.filter_by(name=display_name).first()
        display.last_seen_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        db.session.commit()

        # Check status - should be offline
        response = auth_client.get(f"/display/{display_name}/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["online"] is False

    def test_multiple_displays_status_tracking(self, auth_client):
        """Test status tracking for multiple displays."""
        display_names = ["multi-test-1", "multi-test-2", "multi-test-3"]

        # Register all displays
        for name in display_names:
            auth_client.get(f"/display/{name}")
            auth_client.post(
                f"/display/{name}/heartbeat",
                data=json.dumps({"width": 1920, "height": 1080}),
                content_type="application/json",
            )

        # Check status for all displays
        for name in display_names:
            response = auth_client.get(f"/display/{name}/status")
            assert response.status_code == 200

            data = response.get_json()
            assert data["name"] == name
            assert data["online"] is True

    def test_display_resolution_tracking_over_time(self, auth_client):
        """Test resolution tracking as it changes over time."""
        display_name = "resolution-tracking-test"

        # Register display
        auth_client.get(f"/display/{display_name}")

        # Initial resolution
        auth_client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )

        response = auth_client.get(f"/display/{display_name}/status")
        data = response.get_json()
        assert data["resolution"]["width"] == 1920
        assert data["resolution"]["height"] == 1080

        # Changed resolution
        auth_client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 2560, "height": 1440}),
            content_type="application/json",
        )

        response = auth_client.get(f"/display/{display_name}/status")
        data = response.get_json()
        assert data["resolution"]["width"] == 2560
        assert data["resolution"]["height"] == 1440


class TestErrorRecoveryIntegration:
    """Test error recovery and resilience in display workflows."""

    def test_display_recovery_after_server_restart(self, auth_client, sample_user):
        """Test display recovery after server restart simulation."""
        display_name = "recovery-test-display"

        # Create slideshow
        slideshow = Slideshow(
            name="Recovery Test Slideshow",
            owner_id=sample_user.id,
            is_default=True,
            is_active=True,
        )
        db.session.add(slideshow)
        db.session.flush()

        slide = SlideshowItem(
            slideshow_id=slideshow.id,
            content_type="text",
            content_text="Recovery test",
            display_duration=5,
            order_index=1,
        )
        db.session.add(slide)
        db.session.commit()

        # Initial connection
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Recovery Test Slideshow" in response.data

        # Simulate restart by clearing last_seen_at
        display = Display.query.filter_by(name=display_name).first()
        display.last_seen_at = None
        db.session.commit()

        # Reconnection should work properly
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Recovery Test Slideshow" in response.data

        # Heartbeat should restore monitoring
        auth_client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )

        response = auth_client.get(f"/display/{display_name}/status")
        data = response.get_json()
        assert data["online"] is True

    def test_graceful_handling_of_corrupted_display_data(self, auth_client):
        """Test graceful handling when display data is corrupted."""
        display_name = "corrupted-data-test"

        # Create display with invalid slideshow reference
        display = Display(
            name=display_name,
            owner_id=1,
            current_slideshow_id=99999,  # Non-existent slideshow
        )
        db.session.add(display)
        db.session.commit()

        # Should handle gracefully and show configuration page
        response = auth_client.get(f"/display/{display_name}")
        assert response.status_code == 200
        assert b"Display Configuration Required" in response.data

    def test_network_interruption_simulation(self, auth_client):
        """Test handling of network interruptions in heartbeat."""
        display_name = "network-test-display"

        # Register display
        auth_client.get(f"/display/{display_name}")

        # Send successful heartbeats
        for _ in range(3):
            response = auth_client.post(
                f"/display/{display_name}/heartbeat",
                data=json.dumps({"width": 1920, "height": 1080}),
                content_type="application/json",
            )
            assert response.status_code == 200

        # Simulate network interruption with malformed data
        response = auth_client.post(
            f"/display/{display_name}/heartbeat",
            data="malformed",
            content_type="application/json",
        )
        assert response.status_code == 400

        # Recovery should work with proper data
        response = auth_client.post(
            f"/display/{display_name}/heartbeat",
            data=json.dumps({"width": 1920, "height": 1080}),
            content_type="application/json",
        )
        assert response.status_code == 200
