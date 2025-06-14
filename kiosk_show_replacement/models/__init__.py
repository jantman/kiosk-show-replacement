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

__all__ = ['User', 'Display', 'Slideshow', 'SlideshowItem']

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from werkzeug.security import check_password_hash, generate_password_hash

from ..app import db


class User(db.Model):
    """Model representing a user account."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Self-referential relationships for audit tracking
    created_by = relationship("User", remote_side=[id], foreign_keys=[created_by_id])
    updated_by = relationship("User", remote_side=[id], foreign_keys=[updated_by_id])
    
    # Relationships to owned entities
    slideshows = relationship("Slideshow", back_populates="owner", foreign_keys="Slideshow.owner_id", cascade="all, delete-orphan")
    displays = relationship("Display", back_populates="owner", foreign_keys="Display.owner_id", cascade="all, delete-orphan")
    
    def __repr__(self):
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
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if include_sensitive:
            data.update({
                "created_by_id": self.created_by_id,
                "updated_by_id": self.updated_by_id,
            })
            
        return data
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format and length."""
        if not username or len(username.strip()) < 2:
            raise ValueError("Username must be at least 2 characters long")
        if len(username) > 80:
            raise ValueError("Username must be 80 characters or less")
        return username.strip()
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email


class Display(db.Model):
    """Model representing a display device/kiosk."""
    
    __tablename__ = "displays"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)
    location = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Connection tracking
    last_seen_at = Column(DateTime, nullable=True)
    heartbeat_interval = Column(Integer, default=60, nullable=False)  # seconds
    
    # Ownership and audit fields
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Current slideshow assignment
    current_slideshow_id = Column(Integer, ForeignKey("slideshows.id"), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="displays", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    current_slideshow = relationship("Slideshow", foreign_keys=[current_slideshow_id])
    
    # Unique constraint: display names must be unique per owner
    __table_args__ = (
        UniqueConstraint('name', 'owner_id', name='unique_display_name_per_owner'),
    )
    
    def __repr__(self):
        return f"<Display {self.name}>"
    
    @property
    def is_online(self) -> bool:
        """Check if display is considered online based on last heartbeat."""
        if not self.last_seen_at:
            return False
        
        time_since_last_seen = datetime.utcnow() - self.last_seen_at
        threshold_seconds = self.heartbeat_interval * 3  # Allow 3 missed heartbeats
        return time_since_last_seen.total_seconds() <= threshold_seconds
    
    @property 
    def resolution_string(self) -> Optional[str]:
        """Get display resolution as formatted string."""
        if self.resolution_width and self.resolution_height:
            return f"{self.resolution_width}x{self.resolution_height}"
        return None
    
    def update_heartbeat(self) -> None:
        """Update the last seen timestamp to current time."""
        self.last_seen_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert display to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "resolution_string": self.resolution_string,
            "location": self.location,
            "is_active": self.is_active,
            "is_online": self.is_online,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "heartbeat_interval": self.heartbeat_interval,
            "owner_id": self.owner_id,
            "current_slideshow_id": self.current_slideshow_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate display name format and length."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Display name must be at least 2 characters long")
        if len(name) > 100:
            raise ValueError("Display name must be 100 characters or less")
        return name.strip()
    
    @validates('resolution_width', 'resolution_height')
    def validate_resolution(self, key, value):
        """Validate resolution values."""
        if value is not None and (value < 1 or value > 10000):
            raise ValueError(f"{key} must be between 1 and 10000 pixels")
        return value


class Slideshow(db.Model):
    """Model representing a slideshow collection."""

    __tablename__ = "slideshows"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Display settings
    default_item_duration = Column(Integer, default=30, nullable=False)  # seconds
    transition_type = Column(String(50), default='fade', nullable=False)
    
    # Ownership and audit fields
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="slideshows", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    items = relationship("SlideshowItem", back_populates="slideshow", cascade="all, delete-orphan", order_by="SlideshowItem.order_index")
    
    # Unique constraint: slideshow names must be unique per owner
    __table_args__ = (
        UniqueConstraint('name', 'owner_id', name='unique_slideshow_name_per_owner'),
    )

    def __repr__(self):
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
            data["items"] = [item.to_dict() for item in self.items if item.is_active]
            
        return data
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate slideshow name format and length."""
        if not name or len(name.strip()) < 2:
            raise ValueError("Slideshow name must be at least 2 characters long")
        if len(name) > 100:
            raise ValueError("Slideshow name must be 100 characters or less")
        return name.strip()
    
    @validates('default_item_duration')
    def validate_default_duration(self, key, duration):
        """Validate default item duration."""
        if duration < 1 or duration > 3600:  # 1 second to 1 hour
            raise ValueError("Default item duration must be between 1 and 3600 seconds")
        return duration
    
    @validates('transition_type')
    def validate_transition_type(self, key, transition_type):
        """Validate transition type."""
        allowed_transitions = ['none', 'fade', 'slide', 'zoom']
        if transition_type not in allowed_transitions:
            raise ValueError(f"Transition type must be one of: {', '.join(allowed_transitions)}")
        return transition_type


class SlideshowItem(db.Model):
    """Model representing individual slideshow items."""

    __tablename__ = "slideshow_items"

    id = Column(Integer, primary_key=True)
    slideshow_id = Column(Integer, ForeignKey("slideshows.id"), nullable=False)
    
    # Content identification
    title = Column(String(200), nullable=True)
    content_type = Column(String(50), nullable=False)  # 'image', 'video', 'url', 'text'
    
    # Content sources (only one should be populated based on content_type)
    content_url = Column(String(500), nullable=True)  # URL for images, videos, or web content
    content_text = Column(Text, nullable=True)  # Text content for text slides
    content_file_path = Column(String(500), nullable=True)  # Local file path for uploaded content
    
    # Display settings
    display_duration = Column(Integer, nullable=True)  # Duration in seconds, NULL uses slideshow default
    order_index = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    slideshow = relationship("Slideshow", back_populates="items")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self):
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
        if self.content_type in ['image', 'video'] and self.content_file_path:
            return self.content_file_path
        elif self.content_type in ['image', 'video', 'url'] and self.content_url:
            return self.content_url
        elif self.content_type == 'text' and self.content_text:
            return self.content_text
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
            "display_duration": self.display_duration,
            "effective_duration": self.effective_duration,
            "order_index": self.order_index,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @validates('content_type')
    def validate_content_type(self, key, content_type):
        """Validate content type."""
        allowed_types = ['image', 'video', 'url', 'text']
        if content_type not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        return content_type
    
    @validates('display_duration')
    def validate_display_duration(self, key, duration):
        """Validate display duration."""
        if duration is not None and (duration < 1 or duration > 3600):
            raise ValueError("Display duration must be between 1 and 3600 seconds")
        return duration
    
    @validates('order_index')
    def validate_order_index(self, key, order_index):
        """Validate order index."""
        if order_index < 0:
            raise ValueError("Order index must be non-negative")
        return order_index


# For backward compatibility with existing code
SlideItem = SlideshowItem
