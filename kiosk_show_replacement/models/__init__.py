"""
Database models module for the Kiosk.show Replacement application.

This module contains SQLAlchemy model definitions for:
- User: Authentication and audit information
- Display: Connected kiosk device information
- Slideshow: Collection of slideshow items with metadata
- SlideshowItem: Individual content items within slideshows

All models include proper relationships, constraints, and audit fields
for tracking creation and modification. Designed for easy migration
between different database engines (SQLite, PostgreSQL, MariaDB).
"""

__all__ = [
    "User",
    "Display",
    "Slideshow",
    "SlideshowItem",
    "AssignmentHistory",
    "DisplayConfigurationTemplate",
]

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from werkzeug.security import check_password_hash, generate_password_hash

from ..app import db

if TYPE_CHECKING:
    pass  # Forward references for type checking


class User(db.Model):
    """Model representing a user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Self-referential relationships for audit tracking
    created_by: Mapped[Optional["User"]] = relationship(
        "User", remote_side="User.id", foreign_keys=[created_by_id]
    )
    updated_by: Mapped[Optional["User"]] = relationship(
        "User", remote_side="User.id", foreign_keys=[updated_by_id]
    )

    # Relationships to owned entities
    slideshows: Mapped[List["Slideshow"]] = relationship(
        "Slideshow",
        back_populates="owner",
        foreign_keys="Slideshow.owner_id",
        cascade="all, delete-orphan",
    )
    displays: Mapped[List["Display"]] = relationship(
        "Display",
        back_populates="owner",
        foreign_keys="Display.owner_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def set_password(self, password: str) -> None:
        """Set password hash from plain text password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": (
                self.last_login_at.isoformat() if self.last_login_at else None
            ),
        }

        if include_sensitive:
            data.update(
                {
                    "created_by_id": self.created_by_id,
                    "updated_by_id": self.updated_by_id,
                }
            )

        return data

    @validates("username")
    def validate_username(self, key: str, username: str) -> str:
        """Validate username format and length."""
        if not username or len(username.strip()) < 2:
            raise ValueError("Username must be at least 2 characters long")
        if len(username) > 80:
            raise ValueError("Username must be 80 characters or less")
        return username.strip()

    @validates("email")
    def validate_email(self, key: str, email: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if email and "@" not in email:
            raise ValueError("Invalid email format")
        return email


class Display(db.Model):
    """Model representing a display device/kiosk."""

    __tablename__ = "displays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    resolution_width: Mapped[Optional[int]] = mapped_column(Integer)
    resolution_height: Mapped[Optional[int]] = mapped_column(Integer)
    rotation: Mapped[int] = mapped_column(
        Integer, default=0
    )  # 0, 90, 180, or 270 degrees
    location: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    archived_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Connection tracking
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    heartbeat_interval: Mapped[int] = mapped_column(Integer, default=60)  # seconds

    # Ownership and audit fields (nullable for auto-registered displays)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Current slideshow assignment
    current_slideshow_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("slideshows.id")
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship(
        "User", back_populates="displays", foreign_keys=[owner_id]
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_id]
    )
    updated_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[updated_by_id]
    )
    archived_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[archived_by_id]
    )
    current_slideshow: Mapped[Optional["Slideshow"]] = relationship(
        "Slideshow", foreign_keys=[current_slideshow_id]
    )

    # Unique constraint: display names must be globally unique
    # (since owner_id can be NULL for auto-registered displays)
    __table_args__ = (UniqueConstraint("name", name="unique_display_name"),)

    def __repr__(self) -> str:
        return f"<Display {self.name}>"

    @property
    def is_online(self) -> bool:
        """Check if display is considered online based on last heartbeat."""
        if not self.last_seen_at:
            return False

        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        last_seen = self.last_seen_at

        # If last_seen is naive, assume it's UTC
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        time_since_last_seen = now - last_seen
        threshold_seconds = self.heartbeat_interval * 3  # Allow 3 missed heartbeats
        return time_since_last_seen.total_seconds() <= threshold_seconds

    @property
    def resolution_string(self) -> Optional[str]:
        """Get display resolution as formatted string."""
        if self.resolution_width and self.resolution_height:
            return f"{self.resolution_width}x{self.resolution_height}"
        return None

    @property
    def resolution(self) -> Optional[str]:
        """Alias for resolution_string for backward compatibility."""
        return self.resolution_string

    def update_heartbeat(self) -> None:
        """Update the last seen timestamp to current time."""
        self.last_seen_at = datetime.now(timezone.utc)

    @property
    def last_heartbeat(self) -> Optional[datetime]:
        """Alias for last_seen_at for backward compatibility."""
        return self.last_seen_at

    def to_dict(self) -> dict:
        """Convert display to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "resolution_string": self.resolution_string,
            "resolution": self.resolution,
            "rotation": self.rotation,
            "location": self.location,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "archived_at": (self.archived_at.isoformat() if self.archived_at else None),
            "archived_by_id": self.archived_by_id,
            "is_online": self.is_online,
            "online": self.is_online,  # Alias for API consistency
            "last_seen_at": (
                self.last_seen_at.isoformat() if self.last_seen_at else None
            ),
            "heartbeat_interval": self.heartbeat_interval,
            "owner_id": self.owner_id,
            "current_slideshow_id": self.current_slideshow_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate display name format and length."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Display name must be at least 2 characters long")
        if len(name) > 100:
            raise ValueError("Display name must be 100 characters or less")
        return name.strip()

    @validates("resolution_width", "resolution_height")
    def validate_resolution(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate resolution values."""
        if value is not None and (value < 1 or value > 10000):
            raise ValueError(f"{key} must be between 1 and 10000 pixels")
        return value

    @validates("rotation")
    def validate_rotation(self, key: str, rotation: int) -> int:
        """Validate rotation value."""
        allowed_rotations = [0, 90, 180, 270]
        if rotation not in allowed_rotations:
            raise ValueError(
                f"Rotation must be one of: {', '.join(map(str, allowed_rotations))}"
            )
        return rotation

    def archive(self, archived_by_user: "User") -> None:
        """Archive this display."""
        self.is_archived = True
        self.archived_at = datetime.now(timezone.utc)
        self.archived_by_id = archived_by_user.id
        self.is_active = False  # Archived displays are also inactive
        # Clear slideshow assignment when archiving
        self.current_slideshow_id = None

    def restore(self) -> None:
        """Restore this display from archive."""
        self.is_archived = False
        self.archived_at = None
        self.archived_by_id = None
        self.is_active = True  # Restored displays are active by default

    @property
    def can_be_assigned(self) -> bool:
        """Check if display can be assigned a slideshow."""
        return self.is_active and not self.is_archived

    def get_configuration_dict(self) -> dict:
        """Get display configuration for templates and migration."""
        return {
            "name": self.name,
            "description": self.description,
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "rotation": self.rotation,
            "location": self.location,
            "heartbeat_interval": self.heartbeat_interval,
        }

    def apply_configuration(self, config: dict, updated_by_user: "User") -> None:
        """Apply configuration from template or migration."""
        self.name = config.get("name", self.name)
        self.description = config.get("description", self.description)
        self.resolution_width = config.get("resolution_width", self.resolution_width)
        self.resolution_height = config.get("resolution_height", self.resolution_height)
        self.rotation = config.get("rotation", self.rotation)
        self.location = config.get("location", self.location)
        self.heartbeat_interval = config.get(
            "heartbeat_interval", self.heartbeat_interval
        )
        self.updated_by_id = updated_by_user.id
        self.updated_at = datetime.now(timezone.utc)


class Slideshow(db.Model):
    """Model representing a slideshow collection."""

    __tablename__ = "slideshows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Display settings
    default_item_duration: Mapped[int] = mapped_column(Integer, default=30)  # seconds
    transition_type: Mapped[str] = mapped_column(String(50), default="fade")

    # Ownership and audit fields
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", back_populates="slideshows", foreign_keys=[owner_id]
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_id]
    )
    updated_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[updated_by_id]
    )
    items: Mapped[List["SlideshowItem"]] = relationship(
        "SlideshowItem",
        back_populates="slideshow",
        cascade="all, delete-orphan",
        order_by="SlideshowItem.order_index",
    )

    # Unique constraint: slideshow names must be unique per owner
    __table_args__ = (
        UniqueConstraint("name", "owner_id", name="unique_slideshow_name_per_owner"),
    )

    def __repr__(self) -> str:
        return f"<Slideshow {self.name}>"

    @property
    def total_duration(self) -> int:
        """Calculate total slideshow duration in seconds."""
        total = 0
        for item in self.items:
            if item.is_active:
                duration = item.display_duration or self.default_item_duration
                total += duration
        return total

    @property
    def active_items_count(self) -> int:
        """Get count of active slideshow items."""
        return sum(1 for item in self.items if item.is_active)

    @property
    def item_count(self) -> int:
        """Alias for active_items_count for backward compatibility."""
        return self.active_items_count

    @property
    def default_duration(self) -> int:
        """Alias for default_item_duration for backward compatibility."""
        return self.default_item_duration

    def to_dict(self, include_items: bool = False) -> dict:
        """Convert slideshow to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "default_item_duration": self.default_item_duration,
            "transition_type": self.transition_type,
            "total_duration": self.total_duration,
            "active_items_count": self.active_items_count,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_items:
            data["slides"] = [item.to_dict() for item in self.items if item.is_active]

        return data

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate slideshow name format and length."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Slideshow name must be at least 2 characters long")
        if len(name) > 100:
            raise ValueError("Slideshow name must be 100 characters or less")
        return name.strip()

    @validates("default_item_duration")
    def validate_default_duration(self, key: str, duration: int) -> int:
        """Validate default item duration."""
        if duration < 1 or duration > 3600:  # 1 second to 1 hour
            raise ValueError("Default item duration must be between 1 and 3600 seconds")
        return duration

    @validates("transition_type")
    def validate_transition_type(self, key: str, transition_type: str) -> str:
        """Validate transition type."""
        allowed_transitions = ["none", "fade", "slide", "zoom"]
        if transition_type not in allowed_transitions:
            raise ValueError(
                f"Transition type must be one of: {', '.join(allowed_transitions)}"
            )
        return transition_type

    @property
    def slides(self) -> List["SlideshowItem"]:
        """Alias for items to maintain backward compatibility with templates."""
        return self.items


class SlideshowItem(db.Model):
    """Model representing individual slideshow items."""

    __tablename__ = "slideshow_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slideshow_id: Mapped[int] = mapped_column(Integer, ForeignKey("slideshows.id"))

    # Content identification
    title: Mapped[Optional[str]] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(
        String(50)
    )  # 'image', 'video', 'url', 'text'

    # Content sources (only one should be populated based on content_type)
    content_url: Mapped[Optional[str]] = mapped_column(
        String(500)
    )  # URL for images, videos, or web content
    content_text: Mapped[Optional[str]] = mapped_column(
        Text
    )  # Text content for text slides
    content_file_path: Mapped[Optional[str]] = mapped_column(
        String(500)
    )  # Local file path for uploaded content

    # Display settings
    display_duration: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # Duration in seconds, NULL uses slideshow default
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Relationships
    slideshow: Mapped["Slideshow"] = relationship("Slideshow", back_populates="items")
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_id]
    )
    updated_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[updated_by_id]
    )

    def __repr__(self) -> str:
        return f"<SlideshowItem {self.title or self.content_type}>"

    @property
    def effective_duration(self) -> int:
        """Get effective display duration (item-specific or slideshow default)."""
        if self.display_duration:
            return self.display_duration
        return self.slideshow.default_item_duration if self.slideshow else 30

    @property
    def content_source(self) -> Optional[str]:
        """Get the active content source based on content type."""
        if self.content_type in ["image", "video"] and self.content_file_path:
            return self.content_file_path
        elif self.content_type in ["image", "video", "url"] and self.content_url:
            return self.content_url
        elif self.content_type == "text" and self.content_text:
            return self.content_text
        return None

    @property
    def display_url(self) -> Optional[str]:
        """Get the URL for displaying this content in the slideshow."""
        if self.content_type in ["image", "video"] and self.content_file_path:
            # Convert file path to /uploads/ URL
            # Remove any leading path separators and ensure proper format
            file_path = self.content_file_path.lstrip("/")
            # Check if the path already starts with 'uploads/'
            if file_path.startswith("uploads/"):
                return f"/{file_path}"
            else:
                return f"/uploads/{file_path}"
        elif self.content_type in ["image", "video", "url"] and self.content_url:
            return self.content_url
        elif self.content_type == "text":
            # Text content doesn't need a URL
            return None
        return None

    def to_dict(self) -> dict:
        """Convert slideshow item to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "slideshow_id": self.slideshow_id,
            "title": self.title,
            "content_type": self.content_type,
            "content_url": self.content_url,
            "content_text": self.content_text,
            "content_file_path": self.content_file_path,
            "content_source": self.content_source,
            "display_url": self.display_url,
            "display_duration": self.display_duration,
            "effective_duration": self.effective_duration,
            "order_index": self.order_index,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @validates("content_type")
    def validate_content_type(self, key: str, content_type: str) -> str:
        """Validate content type."""
        allowed_types = ["image", "video", "url", "text"]
        if content_type not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        return content_type

    @validates("content_url")
    def validate_content_url(
        self, key: str, content_url: Optional[str]
    ) -> Optional[str]:
        """Validate content URL format."""
        if content_url:
            # Basic URL validation - must start with http:// or https://
            if not (
                content_url.startswith("http://") or content_url.startswith("https://")
            ):
                raise ValueError("Invalid URL format")
        return content_url

    @validates("display_duration")
    def validate_display_duration(
        self, key: str, duration: Optional[int]
    ) -> Optional[int]:
        """Validate display duration."""
        if duration is not None and (duration < 1 or duration > 3600):
            raise ValueError("Display duration must be between 1 and 3600 seconds")
        return duration

    @validates("order_index")
    def validate_order_index(self, key: str, order_index: int) -> int:
        """Validate order index."""
        if order_index < 0:
            raise ValueError("Order index must be non-negative")
        return order_index


class AssignmentHistory(db.Model):
    """Model for tracking slideshow assignment history and audit trail."""

    __tablename__ = "assignment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_id: Mapped[int] = mapped_column(Integer, ForeignKey("displays.id"))
    previous_slideshow_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("slideshows.id")
    )
    new_slideshow_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("slideshows.id")
    )
    action: Mapped[str] = mapped_column(String(50))  # 'assign', 'unassign', 'change'
    reason: Mapped[Optional[str]] = mapped_column(
        Text
    )  # Optional reason for the change

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Relationships
    display: Mapped["Display"] = relationship("Display", backref="assignment_history")
    previous_slideshow: Mapped[Optional["Slideshow"]] = relationship(
        "Slideshow",
        foreign_keys=[previous_slideshow_id],
        backref="previous_assignments",
    )
    new_slideshow: Mapped[Optional["Slideshow"]] = relationship(
        "Slideshow", foreign_keys=[new_slideshow_id], backref="new_assignments"
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_id]
    )

    def __repr__(self) -> str:
        return f"<AssignmentHistory {self.display_id}: {self.action}>"

    @validates("action")
    def validate_action(self, key: str, action: str) -> str:
        """Validate assignment action type."""
        valid_actions = ["assign", "unassign", "change"]
        if action not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return action

    def to_dict(self) -> dict:
        """Convert assignment history to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "display_id": self.display_id,
            "display_name": self.display.name if self.display else None,
            "previous_slideshow_id": self.previous_slideshow_id,
            "previous_slideshow_name": (
                self.previous_slideshow.name if self.previous_slideshow else None
            ),
            "new_slideshow_id": self.new_slideshow_id,
            "new_slideshow_name": (
                self.new_slideshow.name if self.new_slideshow else None
            ),
            "action": self.action,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by_id": self.created_by_id,
            "created_by_username": (
                self.created_by.username if self.created_by else None
            ),
        }

    @classmethod
    def create_assignment_record(
        cls,
        display_id: int,
        previous_slideshow_id: Optional[int],
        new_slideshow_id: Optional[int],
        created_by_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> "AssignmentHistory":
        """Create an assignment history record based on the change type."""
        # Determine action type
        if previous_slideshow_id is None and new_slideshow_id is not None:
            action = "assign"
        elif previous_slideshow_id is not None and new_slideshow_id is None:
            action = "unassign"
        elif previous_slideshow_id != new_slideshow_id:
            action = "change"
        else:
            # No actual change
            return None

        return cls(
            display_id=display_id,
            previous_slideshow_id=previous_slideshow_id,
            new_slideshow_id=new_slideshow_id,
            action=action,
            reason=reason,
            created_by_id=created_by_id,
        )


# For backward compatibility with existing code
SlideItem = SlideshowItem


class DisplayConfigurationTemplate(db.Model):
    """Model for storing display configuration templates."""

    __tablename__ = "display_configuration_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Configuration fields
    template_resolution_width: Mapped[Optional[int]] = mapped_column(Integer)
    template_resolution_height: Mapped[Optional[int]] = mapped_column(Integer)
    template_rotation: Mapped[int] = mapped_column(Integer, default=0)
    template_heartbeat_interval: Mapped[int] = mapped_column(Integer, default=60)
    template_location: Mapped[Optional[str]] = mapped_column(String(200))

    # Template metadata
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Ownership and audit fields
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id")
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    updated_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[updated_by_id]
    )

    # Unique constraint: template names must be unique per owner
    __table_args__ = (
        UniqueConstraint("name", "owner_id", name="unique_template_name_per_owner"),
    )

    def __repr__(self) -> str:
        return f"<DisplayConfigurationTemplate {self.name}>"

    def to_dict(self) -> dict:
        """Convert template to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_resolution_width": self.template_resolution_width,
            "template_resolution_height": self.template_resolution_height,
            "template_rotation": self.template_rotation,
            "template_heartbeat_interval": self.template_heartbeat_interval,
            "template_location": self.template_location,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_id": self.created_by_id,
            "updated_by_id": self.updated_by_id,
        }

    def to_configuration_dict(self) -> dict:
        """Convert template to configuration dictionary for applying to displays."""
        return {
            "resolution_width": self.template_resolution_width,
            "resolution_height": self.template_resolution_height,
            "rotation": self.template_rotation,
            "heartbeat_interval": self.template_heartbeat_interval,
            "location": self.template_location,
        }

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate template name format and length."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Template name must be at least 2 characters long")
        if len(name) > 100:
            raise ValueError("Template name must be 100 characters or less")
        return name.strip()

    @validates("template_rotation")
    def validate_template_rotation(self, key: str, rotation: int) -> int:
        """Validate template rotation value."""
        allowed_rotations = [0, 90, 180, 270]
        if rotation not in allowed_rotations:
            raise ValueError(
                f"Template rotation must be one of: {', '.join(map(str, allowed_rotations))}"
            )
        return rotation

    @validates("template_resolution_width", "template_resolution_height")
    def validate_template_resolution(
        self, key: str, value: Optional[int]
    ) -> Optional[int]:
        """Validate template resolution values."""
        if value is not None and (value < 1 or value > 10000):
            raise ValueError(f"{key} must be between 1 and 10000 pixels")
        return value
