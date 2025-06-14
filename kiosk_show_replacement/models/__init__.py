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

__all__ = []

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..app import db


class Slideshow(db.Model):
    """Model representing a slideshow collection."""

    __tablename__ = "slideshows"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to slide items
    slides = relationship(
        "SlideItem", back_populates="slideshow", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Slideshow {self.name}>"

    def to_dict(self):
        """Convert slideshow to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "slide_count": len(self.slides),
        }


class SlideItem(db.Model):
    """Model representing individual slide items within a slideshow."""

    __tablename__ = "slide_items"

    id = Column(Integer, primary_key=True)
    slideshow_id = Column(Integer, ForeignKey("slideshows.id"), nullable=False)
    title = Column(String(200))
    content_type = Column(String(50), nullable=False)  # 'image', 'url', 'text'
    content_url = Column(String(500))  # URL for images or web content
    content_text = Column(Text)  # Text content for text slides
    display_duration = Column(Integer, default=30)  # Duration in seconds
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to slideshow
    slideshow = relationship("Slideshow", back_populates="slides")

    def __repr__(self):
        return f"<SlideItem {self.title or self.content_type}>"

    def to_dict(self):
        """Convert slide item to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "slideshow_id": self.slideshow_id,
            "title": self.title,
            "content_type": self.content_type,
            "content_url": self.content_url,
            "content_text": self.content_text,
            "display_duration": self.display_duration,
            "order_index": self.order_index,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
