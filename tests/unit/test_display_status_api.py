"""
Unit tests for Display Status API endpoints.

Tests verify:
- GET /api/v1/displays/status returns list of display statuses
- GET /api/v1/displays/<id>/status returns single display status
- Display status includes required fields for frontend

These tests verify the missing endpoints needed by EnhancedDisplayStatus.tsx.

Run with: poetry run -- nox -s test-3.14 -- tests/unit/test_display_status_api.py
"""

from datetime import datetime, timedelta, timezone

from kiosk_show_replacement.models import Display, Slideshow, db


class TestDisplayStatusEndpoint:
    """Test GET /api/v1/displays/status endpoint.

    Frontend expects this endpoint to return a list of display status objects
    with enhanced status fields like connection_quality, sse_connected, etc.
    """

    def test_displays_status_requires_authentication(self, client):
        """Test that display status endpoint requires authentication."""
        response = client.get("/api/v1/displays/status")
        assert response.status_code == 401

    def test_displays_status_returns_empty_list_when_no_displays(
        self, client, authenticated_user
    ):
        """Test that endpoint returns empty list when no displays exist."""
        response = client.get("/api/v1/displays/status")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0

    def test_displays_status_returns_all_displays(
        self, client, authenticated_user, app
    ):
        """Test that endpoint returns status for all displays."""
        with app.app_context():
            # Create multiple displays
            display1 = Display(
                name="display-status-1",
                location="Lobby",
                owner_id=authenticated_user.id,
            )
            display2 = Display(
                name="display-status-2",
                location="Conference Room",
                owner_id=authenticated_user.id,
            )
            db.session.add_all([display1, display2])
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert data["success"] is True
            assert len(data["data"]) == 2

    def test_displays_status_includes_connection_quality(
        self, client, authenticated_user, app
    ):
        """Test that display status includes connection_quality field."""
        with app.app_context():
            display = Display(
                name="display-quality-test",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            assert "connection_quality" in status, (
                "Display status should include 'connection_quality' field"
            )
            assert status["connection_quality"] in [
                "excellent",
                "good",
                "poor",
                "offline",
            ]

    def test_displays_status_includes_sse_connected(
        self, client, authenticated_user, app
    ):
        """Test that display status includes sse_connected field."""
        with app.app_context():
            display = Display(
                name="display-sse-test",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            assert "sse_connected" in status, (
                "Display status should include 'sse_connected' field"
            )
            assert isinstance(status["sse_connected"], bool)

    def test_displays_status_includes_missed_heartbeats(
        self, client, authenticated_user, app
    ):
        """Test that display status includes missed_heartbeats field."""
        with app.app_context():
            display = Display(
                name="display-heartbeat-test",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            assert "missed_heartbeats" in status, (
                "Display status should include 'missed_heartbeats' field"
            )
            assert isinstance(status["missed_heartbeats"], int)

    def test_displays_status_includes_basic_display_info(
        self, client, authenticated_user, app
    ):
        """Test that display status includes basic display information."""
        with app.app_context():
            display = Display(
                name="display-basic-info",
                location="Test Location",
                heartbeat_interval=60,
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            # Check basic fields from Display model
            assert "id" in status
            assert "name" in status
            assert "location" in status
            assert "is_online" in status
            assert "heartbeat_interval" in status

    def test_displays_status_includes_current_slideshow(
        self, client, authenticated_user, app
    ):
        """Test that display status includes current_slideshow when assigned."""
        with app.app_context():
            slideshow = Slideshow(
                name="Test Slideshow",
                owner_id=authenticated_user.id,
            )
            db.session.add(slideshow)
            db.session.flush()

            display = Display(
                name="display-slideshow-test",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow.id,
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            assert "current_slideshow" in status
            if status["current_slideshow"] is not None:
                assert "id" in status["current_slideshow"]
                assert "name" in status["current_slideshow"]

    def test_displays_status_connection_quality_excellent_when_recent(
        self, client, authenticated_user, app
    ):
        """Test connection_quality is 'excellent' when heartbeat is recent."""
        with app.app_context():
            display = Display(
                name="display-excellent",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                last_seen_at=datetime.now(timezone.utc),  # Just now
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            assert status["connection_quality"] == "excellent"
            assert status["missed_heartbeats"] == 0

    def test_displays_status_connection_quality_offline_when_stale(
        self, client, authenticated_user, app
    ):
        """Test connection_quality is 'offline' when heartbeat is very old."""
        with app.app_context():
            display = Display(
                name="display-offline",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                # Last seen 10 minutes ago (way more than 3 intervals)
                last_seen_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            assert response.status_code == 200

            data = response.get_json()
            assert len(data["data"]) > 0
            status = data["data"][0]

            assert status["connection_quality"] == "offline"
            assert status["missed_heartbeats"] > 3


class TestSingleDisplayStatusEndpoint:
    """Test GET /api/v1/displays/<id>/status endpoint."""

    def test_single_display_status_requires_authentication(self, client):
        """Test that single display status endpoint requires authentication."""
        response = client.get("/api/v1/displays/1/status")
        assert response.status_code == 401

    def test_single_display_status_returns_404_for_nonexistent(
        self, client, authenticated_user
    ):
        """Test that endpoint returns 404 for non-existent display."""
        response = client.get("/api/v1/displays/99999/status")
        assert response.status_code == 404

    def test_single_display_status_returns_display_status(
        self, client, authenticated_user, app
    ):
        """Test that endpoint returns status for specific display."""
        with app.app_context():
            display = Display(
                name="single-display-test",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id

            response = client.get(f"/api/v1/displays/{display_id}/status")
            assert response.status_code == 200

            data = response.get_json()
            assert data["success"] is True
            assert "data" in data

            status = data["data"]
            assert status["id"] == display_id
            assert status["name"] == "single-display-test"

    def test_single_display_status_includes_all_required_fields(
        self, client, authenticated_user, app
    ):
        """Test that single display status includes all required fields."""
        with app.app_context():
            display = Display(
                name="single-display-fields",
                location="Test Location",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                last_seen_at=datetime.now(timezone.utc),
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id

            response = client.get(f"/api/v1/displays/{display_id}/status")
            assert response.status_code == 200

            data = response.get_json()
            status = data["data"]

            # All fields expected by frontend
            required_fields = [
                "id",
                "name",
                "location",
                "is_online",
                "last_seen_at",
                "connection_quality",
                "heartbeat_interval",
                "missed_heartbeats",
                "sse_connected",
            ]

            for field in required_fields:
                assert field in status, f"Status should include '{field}' field"


class TestDisplayConnectionQualityCalculation:
    """Test connection quality calculation logic."""

    def test_connection_quality_excellent_zero_missed(
        self, client, authenticated_user, app
    ):
        """Test excellent quality when 0 heartbeats missed."""
        with app.app_context():
            display = Display(
                name="display-calc-excellent",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                last_seen_at=datetime.now(timezone.utc),
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            data = response.get_json()
            status = data["data"][0]

            assert status["connection_quality"] == "excellent"

    def test_connection_quality_good_one_missed(
        self, client, authenticated_user, app
    ):
        """Test good quality when 1 heartbeat missed."""
        with app.app_context():
            display = Display(
                name="display-calc-good",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                # 90 seconds ago = 1.5 intervals missed
                last_seen_at=datetime.now(timezone.utc) - timedelta(seconds=90),
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            data = response.get_json()
            status = data["data"][0]

            assert status["connection_quality"] == "good"
            assert status["missed_heartbeats"] == 1

    def test_connection_quality_poor_two_missed(
        self, client, authenticated_user, app
    ):
        """Test poor quality when 2 heartbeats missed."""
        with app.app_context():
            display = Display(
                name="display-calc-poor",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                # 150 seconds ago = 2.5 intervals missed
                last_seen_at=datetime.now(timezone.utc) - timedelta(seconds=150),
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            data = response.get_json()
            status = data["data"][0]

            assert status["connection_quality"] == "poor"
            assert status["missed_heartbeats"] == 2

    def test_connection_quality_offline_three_plus_missed(
        self, client, authenticated_user, app
    ):
        """Test offline quality when 3+ heartbeats missed."""
        with app.app_context():
            display = Display(
                name="display-calc-offline",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                # 200 seconds ago = 3+ intervals missed
                last_seen_at=datetime.now(timezone.utc) - timedelta(seconds=200),
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            data = response.get_json()
            status = data["data"][0]

            assert status["connection_quality"] == "offline"
            assert status["missed_heartbeats"] >= 3

    def test_connection_quality_offline_when_never_seen(
        self, client, authenticated_user, app
    ):
        """Test offline quality when display has never been seen."""
        with app.app_context():
            display = Display(
                name="display-never-seen",
                owner_id=authenticated_user.id,
                heartbeat_interval=60,
                last_seen_at=None,  # Never seen
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            data = response.get_json()
            status = data["data"][0]

            assert status["connection_quality"] == "offline"
            assert status["is_online"] is False


class TestDisplaySSEConnectedField:
    """Test sse_connected field reflects actual SSE connection state."""

    def test_sse_connected_true_when_display_has_connection(
        self, client, authenticated_user, app
    ):
        """Test sse_connected is True when display has active SSE connection."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            display = Display(
                name="display-sse-connected",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id
            display_name = display.name

            # Create an SSE connection for this display
            connection = sse_manager.create_connection(
                user_id=None, connection_type="display"
            )
            connection.display_id = display_id
            connection.display_name = display_name

            try:
                response = client.get("/api/v1/displays/status")
                data = response.get_json()
                status = data["data"][0]

                assert status["sse_connected"] is True
            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_sse_connected_false_when_no_connection(
        self, client, authenticated_user, app
    ):
        """Test sse_connected is False when display has no SSE connection."""
        with app.app_context():
            display = Display(
                name="display-no-sse",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()

            response = client.get("/api/v1/displays/status")
            data = response.get_json()
            status = data["data"][0]

            assert status["sse_connected"] is False
