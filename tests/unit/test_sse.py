"""
Unit tests for SSE (Server-Sent Events) API endpoints.

Tests verify:
- SSE stats endpoint returns correct field names matching frontend expectations
- SSE connection information is properly formatted
- Events sent tracking works correctly

Run with: poetry run -- nox -s test-3.14 -- tests/unit/test_sse.py
"""


class TestSSEStatsEndpoint:
    """Test /api/v1/events/stats endpoint response format.

    These tests verify that the SSE stats endpoint returns data in the format
    expected by the frontend (SSEDebugger.tsx).

    Frontend expects:
    - connections[].id (not connection_id)
    - connections[].type (not connection_type)
    - connections[].user (username string, not user_id number)
    - connections[].last_ping (not last_activity)
    - connections[].display (not display_name)
    - events_sent_last_hour (top-level field)
    """

    def test_sse_stats_requires_authentication(self, client):
        """Test that SSE stats endpoint requires authentication."""
        response = client.get("/api/v1/events/stats")
        assert response.status_code == 401

    def test_sse_stats_returns_events_sent_last_hour(self, client, authenticated_user):
        """Test that SSE stats includes events_sent_last_hour field."""
        response = client.get("/api/v1/events/stats")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert (
            "events_sent_last_hour" in data["data"]
        ), "Response should include 'events_sent_last_hour' field"
        # Should be a number (int)
        assert isinstance(data["data"]["events_sent_last_hour"], int)

    def test_sse_stats_connection_has_id_field(self, client, authenticated_user, app):
        """Test that connections array items have 'id' field (not 'connection_id')."""
        from kiosk_show_replacement.sse import sse_manager

        # Create a real SSE connection
        with app.app_context():
            connection = sse_manager.create_connection(
                user_id=authenticated_user.id, connection_type="admin"
            )
            try:
                response = client.get("/api/v1/events/stats")
                assert response.status_code == 200

                data = response.get_json()
                assert data["success"] is True
                assert "connections" in data["data"]
                assert len(data["data"]["connections"]) > 0

                conn = data["data"]["connections"][0]
                assert (
                    "id" in conn
                ), "Connection should have 'id' field, not 'connection_id'"
                assert (
                    "connection_id" not in conn
                ), "Connection should not have 'connection_id' field"
            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_sse_stats_connection_has_type_field(self, client, authenticated_user, app):
        """Test that connections have 'type' field (not 'connection_type')."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            connection = sse_manager.create_connection(
                user_id=authenticated_user.id, connection_type="admin"
            )
            try:
                response = client.get("/api/v1/events/stats")
                assert response.status_code == 200

                data = response.get_json()
                assert len(data["data"]["connections"]) > 0

                conn = data["data"]["connections"][0]
                assert (
                    "type" in conn
                ), "Connection should have 'type' field, not 'connection_type'"
                assert (
                    "connection_type" not in conn
                ), "Connection should not have 'connection_type' field"
            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_sse_stats_connection_has_user_as_string(
        self, client, authenticated_user, app
    ):
        """Test that connections have 'user' field as username string (not user_id)."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            connection = sse_manager.create_connection(
                user_id=authenticated_user.id, connection_type="admin"
            )
            try:
                response = client.get("/api/v1/events/stats")
                assert response.status_code == 200

                data = response.get_json()
                assert len(data["data"]["connections"]) > 0

                conn = data["data"]["connections"][0]
                assert (
                    "user" in conn
                ), "Connection should have 'user' field with username"
                assert (
                    "user_id" not in conn
                ), "Connection should not have 'user_id' field"
                # User should be a string (username), not an integer
                if conn["user"] is not None:
                    assert isinstance(
                        conn["user"], str
                    ), "'user' field should be a string (username)"
                    assert conn["user"] == authenticated_user.username
            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_sse_stats_connection_has_last_ping_field(
        self, client, authenticated_user, app
    ):
        """Test that connections have 'last_ping' field (not 'last_activity')."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            connection = sse_manager.create_connection(
                user_id=authenticated_user.id, connection_type="admin"
            )
            try:
                response = client.get("/api/v1/events/stats")
                assert response.status_code == 200

                data = response.get_json()
                assert len(data["data"]["connections"]) > 0

                conn = data["data"]["connections"][0]
                assert "last_ping" in conn, "Connection should have 'last_ping' field"
                assert (
                    "last_activity" not in conn
                ), "Connection should not have 'last_activity' field"
            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_sse_stats_display_connection_has_display_field(
        self, client, authenticated_user, app
    ):
        """Test that display connections have 'display' field (not 'display_name')."""
        from kiosk_show_replacement.models import Display, db
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a test display
            display = Display(
                name="test-display-sse",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()

            # Create a display SSE connection
            connection = sse_manager.create_connection(
                user_id=None, connection_type="display"
            )
            connection.display_name = display.name
            connection.display_id = display.id

            try:
                response = client.get("/api/v1/events/stats")
                assert response.status_code == 200

                data = response.get_json()
                assert len(data["data"]["connections"]) > 0

                # Find the display connection
                display_conn = None
                for conn in data["data"]["connections"]:
                    if (
                        conn.get("type") == "display"
                        or conn.get("connection_type") == "display"
                    ):
                        display_conn = conn
                        break

                assert display_conn is not None, "Should have a display connection"
                assert (
                    "display" in display_conn
                ), "Display connection should have 'display' field"
                assert (
                    "display_name" not in display_conn
                ), "Connection should not have 'display_name' field"
            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_sse_stats_basic_fields_present(self, client, authenticated_user):
        """Test that SSE stats includes basic required fields."""
        response = client.get("/api/v1/events/stats")
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        stats = data["data"]

        # Check required top-level fields
        assert "total_connections" in stats
        assert "admin_connections" in stats
        assert "display_connections" in stats
        assert "connections" in stats
        assert isinstance(stats["connections"], list)


class TestSSEDisconnectEndpoint:
    """Test /api/v1/events/disconnect endpoint for explicit SSE cleanup.

    This endpoint allows clients to notify the server when they're disconnecting,
    enabling immediate cleanup rather than waiting for the next failed write.
    """

    def test_disconnect_requires_connection_id(self, client):
        """Test that disconnect endpoint requires connection_id parameter."""
        response = client.post(
            "/api/v1/events/disconnect",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "connection_id is required" in data.get("error", "")

    def test_disconnect_requires_json_body(self, client):
        """Test that disconnect endpoint requires JSON body."""
        response = client.post(
            "/api/v1/events/disconnect",
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "No data provided" in data.get("error", "")

    def test_disconnect_removes_existing_connection(self, client, authenticated_user, app):
        """Test that disconnect endpoint removes an existing SSE connection."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a connection
            connection = sse_manager.create_connection(
                user_id=authenticated_user.id, connection_type="admin"
            )
            connection_id = connection.connection_id

            # Verify connection exists
            with sse_manager.connections_lock:
                assert connection_id in sse_manager.connections

            # Call disconnect endpoint
            response = client.post(
                "/api/v1/events/disconnect",
                json={"connection_id": connection_id},
                content_type="application/json",
            )
            assert response.status_code == 200

            data = response.get_json()
            assert data["success"] is True
            assert data["data"]["connection_id"] == connection_id
            assert data["data"]["disconnected"] is True

            # Verify connection was removed
            with sse_manager.connections_lock:
                assert connection_id not in sse_manager.connections

    def test_disconnect_handles_nonexistent_connection(self, client):
        """Test that disconnect endpoint handles non-existent connection gracefully."""
        response = client.post(
            "/api/v1/events/disconnect",
            json={"connection_id": "nonexistent-connection-id-12345"},
            content_type="application/json",
        )
        # Should still succeed - connection may already be cleaned up
        assert response.status_code == 200

        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["disconnected"] is False
        assert "not found" in data["message"].lower() or "disconnected" in data["message"].lower()

    def test_disconnect_is_idempotent(self, client, authenticated_user, app):
        """Test that calling disconnect multiple times is safe (idempotent)."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a connection
            connection = sse_manager.create_connection(
                user_id=authenticated_user.id, connection_type="admin"
            )
            connection_id = connection.connection_id

            # First disconnect - should succeed and remove connection
            response1 = client.post(
                "/api/v1/events/disconnect",
                json={"connection_id": connection_id},
                content_type="application/json",
            )
            assert response1.status_code == 200
            assert response1.get_json()["data"]["disconnected"] is True

            # Second disconnect - should still succeed (idempotent)
            response2 = client.post(
                "/api/v1/events/disconnect",
                json={"connection_id": connection_id},
                content_type="application/json",
            )
            assert response2.status_code == 200
            assert response2.get_json()["data"]["disconnected"] is False

    def test_disconnect_does_not_require_authentication(self, client, app):
        """Test that disconnect endpoint works without authentication.

        The connection_id serves as an authentication token - only the client
        that received this ID can disconnect it.
        """
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a connection (simulating one created by an authenticated session)
            connection = sse_manager.create_connection(user_id=1, connection_type="admin")
            connection_id = connection.connection_id

            # Call disconnect without being authenticated
            # Note: client fixture doesn't have authenticated session by default
            response = client.post(
                "/api/v1/events/disconnect",
                json={"connection_id": connection_id},
                content_type="application/json",
            )
            assert response.status_code == 200
            assert response.get_json()["data"]["disconnected"] is True


class TestSSEEventsTracking:
    """Test SSE event tracking functionality."""

    def test_sse_manager_tracks_events_sent(self, app):
        """Test that SSEManager tracks events sent per hour."""
        from kiosk_show_replacement.sse import sse_manager

        # This test verifies the SSEManager has the capability to track
        # events sent in the last hour for the events_sent_last_hour field
        assert hasattr(sse_manager, "get_events_sent_last_hour") or hasattr(
            sse_manager, "events_sent_last_hour"
        ), "SSEManager should track events sent in the last hour"
