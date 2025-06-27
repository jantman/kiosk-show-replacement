"""
Server-Sent Events (SSE) infrastructure for real-time updates.

This module provides comprehensive SSE functionality for real-time communication
between the admin interface and displays, including event management, connection
handling, and authentication integration.
"""

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from queue import Empty, Queue
from threading import Lock
from typing import Any, Dict, Generator, List, Optional, Set

from flask import Response, current_app, request
from werkzeug.exceptions import Unauthorized

from kiosk_show_replacement.auth.decorators import get_current_user

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """Represents a Server-Sent Event."""

    event_type: str
    data: Dict[str, Any]
    event_id: Optional[str] = None
    retry: Optional[int] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Initialize event with defaults."""
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_sse_format(self) -> str:
        """Convert event to SSE wire format."""
        lines = []

        if self.event_id:
            lines.append(f"id: {self.event_id}")

        if self.event_type:
            lines.append(f"event: {self.event_type}")

        if self.retry:
            lines.append(f"retry: {self.retry}")

        # Add timestamp to data
        event_data = dict(self.data)
        event_data["timestamp"] = self.timestamp.isoformat()

        data_json = json.dumps(event_data)
        lines.append(f"data: {data_json}")

        # SSE format requires double newline at end
        lines.append("")
        lines.append("")

        return "\n".join(lines)


class SSEConnection:
    """Manages a single SSE connection."""

    def __init__(
        self,
        connection_id: str,
        user_id: Optional[int] = None,
        connection_type: str = "admin",
    ):
        """Initialize SSE connection.

        Args:
            connection_id: Unique connection identifier
            user_id: User ID for authenticated connections
            connection_type: Type of connection (admin, display)
        """
        self.connection_id = connection_id
        self.user_id = user_id
        self.connection_type = connection_type
        self.connected_at = datetime.now(timezone.utc)
        self.last_ping = self.connected_at
        self.event_queue: Queue[SSEEvent] = Queue()
        self.events_sent_count = 0  # Track events sent to this connection
        self.is_active = True

    def add_event(self, event: SSEEvent) -> None:
        """Add event to connection queue."""
        if self.is_active:
            try:
                self.event_queue.put_nowait(event)
                self.events_sent_count += 1  # Increment counter when event is queued
            except Exception as e:
                logger.warning(
                    f"Failed to queue event for connection {self.connection_id}: {e}"
                )
                self.is_active = False

    def get_events(self) -> Generator[SSEEvent, None, None]:
        """Get events from queue."""
        while self.is_active:
            try:
                # Wait for event with timeout to allow periodic pings
                event = self.event_queue.get(timeout=30)
                yield event
            except Empty:
                # Send ping event to keep connection alive
                ping_event = SSEEvent(event_type="ping", data={"message": "keep-alive"})
                yield ping_event
                self.last_ping = datetime.now(timezone.utc)

    def disconnect(self) -> None:
        """Mark connection as disconnected."""
        self.is_active = False


class SSEManager:
    """Manages all SSE connections and event broadcasting."""

    def __init__(self):
        """Initialize SSE manager."""
        self.connections: Dict[str, SSEConnection] = {}
        self.connections_lock = Lock()

    def create_connection(
        self, user_id: Optional[int] = None, connection_type: str = "admin"
    ) -> SSEConnection:
        """Create new SSE connection.

        Args:
            user_id: User ID for authenticated connections
            connection_type: Type of connection (admin, display)

        Returns:
            New SSE connection
        """
        connection_id = str(uuid.uuid4())
        connection = SSEConnection(connection_id, user_id, connection_type)

        with self.connections_lock:
            self.connections[connection_id] = connection

        logger.info(
            f"Created SSE connection {connection_id} for user {user_id} "
            f"(type: {connection_type})"
        )

        return connection

    def remove_connection(self, connection_id: str) -> None:
        """Remove SSE connection.

        Args:
            connection_id: Connection to remove
        """
        with self.connections_lock:
            if connection_id in self.connections:
                connection = self.connections.pop(connection_id)
                connection.disconnect()
                logger.info(f"Removed SSE connection {connection_id}")

    def broadcast_event(
        self,
        event: SSEEvent,
        connection_type: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """Broadcast event to connections.

        Args:
            event: Event to broadcast
            connection_type: Filter by connection type (optional)
            user_id: Filter by user ID (optional)

        Returns:
            Number of connections that received the event
        """
        sent_count = 0

        with self.connections_lock:
            # Clean up inactive connections
            inactive_connections = [
                conn_id
                for conn_id, conn in self.connections.items()
                if not conn.is_active
            ]
            for conn_id in inactive_connections:
                self.connections.pop(conn_id, None)

            # Send event to matching connections
            for connection in self.connections.values():
                if connection_type and connection.connection_type != connection_type:
                    continue
                if user_id and connection.user_id != user_id:
                    continue

                connection.add_event(event)
                sent_count += 1

        logger.debug(f"Broadcast event {event.event_type} to {sent_count} connections")
        return sent_count

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics.

        Returns:
            Dictionary with connection statistics
        """
        with self.connections_lock:
            total_connections = len(self.connections)
            admin_connections = sum(
                1
                for conn in self.connections.values()
                if conn.connection_type == "admin"
            )
            display_connections = sum(
                1
                for conn in self.connections.values()
                if conn.connection_type == "display"
            )

            # Calculate connection ages
            now = datetime.now(timezone.utc)
            connection_ages = [
                (now - conn.connected_at).total_seconds()
                for conn in self.connections.values()
            ]

            avg_age = (
                sum(connection_ages) / len(connection_ages) if connection_ages else 0
            )

        return {
            "total_connections": total_connections,
            "admin_connections": admin_connections,
            "display_connections": display_connections,
            "average_connection_age_seconds": avg_age,
            "active_connection_ids": list(self.connections.keys()),
        }


# Global SSE manager instance
sse_manager = SSEManager()


def create_sse_response(connection: SSEConnection) -> Response:
    """Create Flask response for SSE connection.

    Args:
        connection: SSE connection to stream

    Returns:
        Flask response with SSE stream
    """

    def event_stream():
        """Generate SSE event stream."""
        try:
            # Send initial connection event
            welcome_event = SSEEvent(
                event_type="connected",
                data={
                    "message": "SSE connection established",
                    "connection_id": connection.connection_id,
                    "connection_type": connection.connection_type,
                },
            )
            yield welcome_event.to_sse_format()

            # Stream events
            for event in connection.get_events():
                yield event.to_sse_format()

        except GeneratorExit:
            # Client disconnected
            logger.info(f"SSE connection {connection.connection_id} disconnected")
        except Exception as e:
            logger.error(f"SSE connection {connection.connection_id} error: {e}")
        finally:
            # Clean up connection
            sse_manager.remove_connection(connection.connection_id)

    response = Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

    return response


def require_sse_auth() -> Optional[int]:
    """Require authentication for SSE endpoints.

    Returns:
        User ID if authenticated, raises Unauthorized if not

    Raises:
        Unauthorized: If user is not authenticated
    """
    user = get_current_user()
    if not user:
        raise Unauthorized("Authentication required for SSE")
    return user.id


def create_display_event(
    event_type: str, display_id: int, data: Dict[str, Any]
) -> SSEEvent:
    """Create display-related SSE event.

    Args:
        event_type: Type of display event
        display_id: Display ID
        data: Event data

    Returns:
        SSE event for display updates
    """
    event_data = dict(data)
    event_data["display_id"] = display_id

    return SSEEvent(event_type=f"display.{event_type}", data=event_data)


def create_slideshow_event(
    event_type: str, slideshow_id: int, data: Dict[str, Any]
) -> SSEEvent:
    """Create slideshow-related SSE event.

    Args:
        event_type: Type of slideshow event
        slideshow_id: Slideshow ID
        data: Event data

    Returns:
        SSE event for slideshow updates
    """
    event_data = dict(data)
    event_data["slideshow_id"] = slideshow_id

    return SSEEvent(event_type=f"slideshow.{event_type}", data=event_data)


def create_system_event(event_type: str, data: Dict[str, Any]) -> SSEEvent:
    """Create system-related SSE event.

    Args:
        event_type: Type of system event
        data: Event data

    Returns:
        SSE event for system updates
    """
    return SSEEvent(event_type=f"system.{event_type}", data=data)
