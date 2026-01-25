"""
Unit tests for SSE broadcast functionality.

These tests verify that SSE events are properly broadcast to displays
when display settings or slideshows are modified via the API.

Regression tests for:
- bug-display-settings-not-realtime
- bug-sse-slideshow-edit (slide item CRUD operations)

Run with: poetry run -- nox -s test-3.14 -- tests/unit/test_sse_broadcast.py
"""

import json
from unittest.mock import patch

from kiosk_show_replacement.app import db
from kiosk_show_replacement.models import Display, Slideshow


class TestDisplaySettingsBroadcast:
    """Test SSE broadcast when display settings are updated.

    Regression tests for: Display settings changes not pushed to displays in real-time.

    The update_display() endpoint should broadcast a 'configuration_changed' event
    to both admin connections AND the specific display connection when settings
    like show_info_overlay, name, location, or description are changed.
    """

    def test_update_display_settings_broadcasts_configuration_changed(
        self, app, client, authenticated_user
    ):
        """Test that updating display settings broadcasts configuration_changed event."""
        with app.app_context():
            # Create a display
            display = Display(
                name="test-display-broadcast",
                owner_id=authenticated_user.id,
                show_info_overlay=False,
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id

            # Mock the broadcast function
            with patch(
                "kiosk_show_replacement.api.v1.broadcast_display_update"
            ) as mock_broadcast:
                # Update display settings (not slideshow assignment)
                response = client.put(
                    f"/api/v1/displays/{display_id}",
                    data=json.dumps({"show_info_overlay": True}),
                    content_type="application/json",
                )

                assert response.status_code == 200

                # Verify broadcast_display_update was called with configuration_changed
                mock_broadcast.assert_called_once()
                call_args = mock_broadcast.call_args

                # First positional arg is the display object
                assert call_args[0][0].id == display_id

                # Second positional arg is the event type
                assert call_args[0][1] == "configuration_changed"

    def test_update_display_name_broadcasts_configuration_changed(
        self, app, client, authenticated_user
    ):
        """Test that updating display name broadcasts configuration_changed event."""
        with app.app_context():
            # Create a display
            display = Display(
                name="test-display-name-change",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id

            with patch(
                "kiosk_show_replacement.api.v1.broadcast_display_update"
            ) as mock_broadcast:
                response = client.put(
                    f"/api/v1/displays/{display_id}",
                    data=json.dumps({"name": "new-display-name"}),
                    content_type="application/json",
                )

                assert response.status_code == 200
                mock_broadcast.assert_called_once()
                assert mock_broadcast.call_args[0][1] == "configuration_changed"

    def test_update_display_location_broadcasts_configuration_changed(
        self, app, client, authenticated_user
    ):
        """Test that updating display location broadcasts configuration_changed event."""
        with app.app_context():
            display = Display(
                name="test-display-location",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id

            with patch(
                "kiosk_show_replacement.api.v1.broadcast_display_update"
            ) as mock_broadcast:
                response = client.put(
                    f"/api/v1/displays/{display_id}",
                    data=json.dumps({"location": "Main Lobby"}),
                    content_type="application/json",
                )

                assert response.status_code == 200
                mock_broadcast.assert_called_once()
                assert mock_broadcast.call_args[0][1] == "configuration_changed"

    def test_update_display_slideshow_broadcasts_assignment_changed(
        self, app, client, authenticated_user
    ):
        """Test that changing slideshow assignment broadcasts assignment_changed event."""
        with app.app_context():
            # Create a slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()
            slideshow_id = slideshow.id

            # Create a display
            display = Display(
                name="test-display-assignment",
                owner_id=authenticated_user.id,
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id

            with patch(
                "kiosk_show_replacement.api.v1.broadcast_display_update"
            ) as mock_broadcast:
                response = client.put(
                    f"/api/v1/displays/{display_id}",
                    data=json.dumps({"current_slideshow_id": slideshow_id}),
                    content_type="application/json",
                )

                assert response.status_code == 200
                mock_broadcast.assert_called_once()
                # Slideshow assignment changes should use assignment_changed event
                assert mock_broadcast.call_args[0][1] == "assignment_changed"


class TestBroadcastDisplayUpdateSendsToDisplay:
    """Test that broadcast_display_update sends events to display connections.

    Regression tests for: Display not receiving configuration_changed events.

    The broadcast_display_update() function should send events to the specific
    display connection for both 'assignment_changed' AND 'configuration_changed'
    event types, not just 'assignment_changed'.
    """

    def test_broadcast_display_update_sends_to_display_for_configuration_changed(
        self, app, authenticated_user
    ):
        """Test that configuration_changed events are sent to display connections."""
        from kiosk_show_replacement.api.v1 import broadcast_display_update
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a display
            display = Display(
                name="test-display-conn",
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
                # Broadcast a configuration_changed event
                count = broadcast_display_update(
                    display, "configuration_changed", {"test": "data"}
                )

                # The display connection should have received the event
                # Check that the event was added to the connection's queue
                assert (
                    count > 0
                ), "configuration_changed should be sent to display connections"

                # Verify the event is in the queue
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                # Should have at least one event (besides any ping events)
                config_events = [
                    e
                    for e in events_in_queue
                    if "configuration_changed" in e.event_type
                ]
                assert (
                    len(config_events) > 0
                ), "Display connection should receive configuration_changed event"

            finally:
                sse_manager.remove_connection(connection.connection_id)


class TestSlideshowUpdateBroadcastToDisplays:
    """Test SSE broadcast to displays when slideshows are updated.

    Regression tests for: Slideshow changes not reaching displays.

    The broadcast_slideshow_update() function should send 'slideshow.updated'
    events to display connections, NOT 'display.slideshow_changed' events.
    The display page JavaScript listens for 'slideshow.updated' events.
    """

    def test_slideshow_update_sends_slideshow_updated_to_displays(
        self, app, authenticated_user
    ):
        """Test that slideshow updates send slideshow.updated events to displays."""
        from kiosk_show_replacement.api.v1 import broadcast_slideshow_update
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Create a display assigned to this slideshow
            display = Display(
                name="test-display-slideshow",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow.id,
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
                # Broadcast a slideshow update
                broadcast_slideshow_update(slideshow, "updated", {"test": "data"})

                # Check what events the display received
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                # Display should receive slideshow.updated, NOT display.slideshow_changed
                event_types = [e.event_type for e in events_in_queue]

                # Should have slideshow.updated event
                assert any("slideshow.updated" in et for et in event_types), (
                    f"Display should receive 'slideshow.updated' event, "
                    f"got: {event_types}"
                )

                # Should NOT have display.slideshow_changed event
                assert not any("slideshow_changed" in et for et in event_types), (
                    f"Display should NOT receive 'display.slideshow_changed' event, "
                    f"got: {event_types}"
                )

            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_slideshow_update_includes_slideshow_id_for_display(
        self, app, authenticated_user
    ):
        """Test that slideshow update events include slideshow_id for display matching."""
        from kiosk_show_replacement.api.v1 import broadcast_slideshow_update
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a slideshow
            slideshow = Slideshow(
                name="Test Slideshow ID",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()
            slideshow_id = slideshow.id

            # Create a display assigned to this slideshow
            display = Display(
                name="test-display-id-match",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow_id,
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
                broadcast_slideshow_update(slideshow, "updated", {})

                # Get the event
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                slideshow_events = [
                    e for e in events_in_queue if "slideshow" in e.event_type.lower()
                ]

                assert len(slideshow_events) > 0, "Should have slideshow event"

                # Access the event data directly (it's already a dict)
                event = slideshow_events[0]
                data = event.data

                # The event should include the slideshow_id for display-side matching
                assert (
                    "id" in data or "slideshow_id" in data
                ), f"Event data should include slideshow id for matching, got: {data}"

            finally:
                sse_manager.remove_connection(connection.connection_id)


class TestSlideItemCRUDBroadcastToDisplays:
    """Test SSE broadcast to displays when slide items are created, updated, deleted, or reordered.

    Regression tests for: bug-sse-slideshow-edit

    When slide items are modified (create, update, delete, reorder), a 'slideshow.updated'
    event should be broadcast to all displays that are currently showing the affected slideshow.
    """

    def test_create_slide_item_broadcasts_slideshow_updated_to_display(
        self, app, client, authenticated_user
    ):
        """Test that creating a slide item broadcasts slideshow.updated event to displays."""
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a slideshow
            slideshow = Slideshow(
                name="Test Slideshow for Create",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()
            slideshow_id = slideshow.id

            # Create a display assigned to this slideshow
            display = Display(
                name="test-display-create-item",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow_id,
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
                # Create a new slide item via API
                response = client.post(
                    f"/api/v1/slideshows/{slideshow_id}/items",
                    data=json.dumps(
                        {
                            "title": "New Test Slide",
                            "content_type": "text",
                            "content_text": "Test content",
                            "display_duration": 10,
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 201

                # Check what events the display received
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                # Display should receive slideshow.updated event
                event_types = [e.event_type for e in events_in_queue]
                assert any("slideshow.updated" in et for et in event_types), (
                    f"Display should receive 'slideshow.updated' event when slide item "
                    f"is created, got: {event_types}"
                )

            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_update_slide_item_broadcasts_slideshow_updated_to_display(
        self, app, client, authenticated_user
    ):
        """Test that updating a slide item broadcasts slideshow.updated event to displays."""
        from kiosk_show_replacement.models import SlideshowItem
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a slideshow with an existing slide
            slideshow = Slideshow(
                name="Test Slideshow for Update",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()

            slide_item = SlideshowItem(
                slideshow_id=slideshow.id,
                title="Existing Slide",
                content_type="text",
                content_text="Original content",
                display_duration=10,
                order_index=1,
                is_active=True,
            )
            db.session.add(slide_item)
            db.session.commit()
            item_id = slide_item.id

            # Create a display assigned to this slideshow
            display = Display(
                name="test-display-update-item",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow.id,
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
                # Update the slide item via API
                response = client.put(
                    f"/api/v1/slideshow-items/{item_id}",
                    data=json.dumps(
                        {
                            "title": "Updated Slide Title",
                            "content_text": "Updated content",
                        }
                    ),
                    content_type="application/json",
                )

                assert response.status_code == 200

                # Check what events the display received
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                # Display should receive slideshow.updated event
                event_types = [e.event_type for e in events_in_queue]
                assert any("slideshow.updated" in et for et in event_types), (
                    f"Display should receive 'slideshow.updated' event when slide item "
                    f"is updated, got: {event_types}"
                )

            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_delete_slide_item_broadcasts_slideshow_updated_to_display(
        self, app, client, authenticated_user
    ):
        """Test that deleting a slide item broadcasts slideshow.updated event to displays."""
        from kiosk_show_replacement.models import SlideshowItem
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a slideshow with an existing slide
            slideshow = Slideshow(
                name="Test Slideshow for Delete",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()

            slide_item = SlideshowItem(
                slideshow_id=slideshow.id,
                title="Slide to Delete",
                content_type="text",
                content_text="Content to delete",
                display_duration=10,
                order_index=1,
                is_active=True,
            )
            db.session.add(slide_item)
            db.session.commit()
            item_id = slide_item.id

            # Create a display assigned to this slideshow
            display = Display(
                name="test-display-delete-item",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow.id,
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
                # Delete the slide item via API
                response = client.delete(f"/api/v1/slideshow-items/{item_id}")

                assert response.status_code == 200

                # Check what events the display received
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                # Display should receive slideshow.updated event
                event_types = [e.event_type for e in events_in_queue]
                assert any("slideshow.updated" in et for et in event_types), (
                    f"Display should receive 'slideshow.updated' event when slide item "
                    f"is deleted, got: {event_types}"
                )

            finally:
                sse_manager.remove_connection(connection.connection_id)

    def test_reorder_slide_item_broadcasts_slideshow_updated_to_display(
        self, app, client, authenticated_user
    ):
        """Test that reordering a slide item broadcasts slideshow.updated event to displays."""
        from kiosk_show_replacement.models import SlideshowItem
        from kiosk_show_replacement.sse import sse_manager

        with app.app_context():
            # Create a slideshow with multiple slides
            slideshow = Slideshow(
                name="Test Slideshow for Reorder",
                owner_id=authenticated_user.id,
                is_active=True,
            )
            db.session.add(slideshow)
            db.session.commit()

            slide_item1 = SlideshowItem(
                slideshow_id=slideshow.id,
                title="Slide 1",
                content_type="text",
                content_text="Content 1",
                display_duration=10,
                order_index=1,
                is_active=True,
            )
            slide_item2 = SlideshowItem(
                slideshow_id=slideshow.id,
                title="Slide 2",
                content_type="text",
                content_text="Content 2",
                display_duration=10,
                order_index=2,
                is_active=True,
            )
            db.session.add(slide_item1)
            db.session.add(slide_item2)
            db.session.commit()
            item1_id = slide_item1.id

            # Create a display assigned to this slideshow
            display = Display(
                name="test-display-reorder-item",
                owner_id=authenticated_user.id,
                current_slideshow_id=slideshow.id,
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
                # Reorder the slide item via API
                response = client.post(
                    f"/api/v1/slideshow-items/{item1_id}/reorder",
                    data=json.dumps({"new_order": 2}),
                    content_type="application/json",
                )

                assert response.status_code == 200

                # Check what events the display received
                events_in_queue = []
                while not connection.event_queue.empty():
                    events_in_queue.append(connection.event_queue.get_nowait())

                # Display should receive slideshow.updated event
                event_types = [e.event_type for e in events_in_queue]
                assert any("slideshow.updated" in et for et in event_types), (
                    f"Display should receive 'slideshow.updated' event when slide item "
                    f"is reordered, got: {event_types}"
                )

            finally:
                sse_manager.remove_connection(connection.connection_id)
