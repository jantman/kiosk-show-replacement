"""
Unit tests for database models.

Tests the Slideshow and SlideItem models including
relationships, validation, and serialization.
"""

import pytest

from kiosk_show_replacement.app import db
from kiosk_show_replacement.models import SlideItem, Slideshow


class TestSlideshowModel:
    """Test cases for the Slideshow model."""

    def test_create_slideshow(self, app):
        """Test creating a new slideshow."""
        with app.app_context():
            slideshow = Slideshow(name="Test Slideshow", description="A test slideshow")
            db.session.add(slideshow)
            db.session.commit()

            assert slideshow.id is not None
            assert slideshow.name == "Test Slideshow"
            assert slideshow.description == "A test slideshow"
            assert slideshow.is_active is True
            assert slideshow.created_at is not None
            assert slideshow.updated_at is not None

    def test_slideshow_repr(self, app):
        """Test slideshow string representation."""
        with app.app_context():
            slideshow = Slideshow(name="Test Slideshow")
            assert repr(slideshow) == "<Slideshow Test Slideshow>"

    def test_slideshow_to_dict(self, app, sample_slideshow):
        """Test slideshow serialization to dictionary."""
        with app.app_context():
            slideshow_dict = sample_slideshow.to_dict()

            assert "id" in slideshow_dict
            assert slideshow_dict["name"] == "Test Slideshow"
            assert slideshow_dict["description"] == "A slideshow for testing"
            assert slideshow_dict["is_active"] is True
            assert "created_at" in slideshow_dict
            assert "updated_at" in slideshow_dict
            assert slideshow_dict["slide_count"] == 3  # From sample_slideshow fixture

    def test_slideshow_slides_relationship(self, app, sample_slideshow):
        """Test slideshow-slides relationship."""
        with app.app_context():
            assert len(sample_slideshow.slides) == 3

            # Test that slides are properly related
            for slide in sample_slideshow.slides:
                assert slide.slideshow_id == sample_slideshow.id
                assert slide.slideshow == sample_slideshow


class TestSlideItemModel:
    """Test cases for the SlideItem model."""

    def test_create_slide_item(self, app, sample_slideshow):
        """Test creating a new slide item."""
        with app.app_context():
            slide = SlideItem(
                slideshow_id=sample_slideshow.id,
                title="Test Slide",
                content_type="text",
                content_text="Test content",
                display_duration=30,
                order_index=0,
            )
            db.session.add(slide)
            db.session.commit()

            assert slide.id is not None
            assert slide.slideshow_id == sample_slideshow.id
            assert slide.title == "Test Slide"
            assert slide.content_type == "text"
            assert slide.content_text == "Test content"
            assert slide.display_duration == 30
            assert slide.order_index == 0
            assert slide.is_active is True
            assert slide.created_at is not None
            assert slide.updated_at is not None

    def test_slide_item_repr(self, app, sample_slideshow):
        """Test slide item string representation."""
        with app.app_context():
            slide = SlideItem(
                slideshow_id=sample_slideshow.id,
                title="Test Slide",
                content_type="text",
            )
            assert repr(slide) == "<SlideItem Test Slide>"

            # Test repr without title
            slide_no_title = SlideItem(
                slideshow_id=sample_slideshow.id, content_type="image"
            )
            assert repr(slide_no_title) == "<SlideItem image>"

    def test_slide_item_to_dict(self, app, sample_slideshow):
        """Test slide item serialization to dictionary."""
        with app.app_context():
            slide = sample_slideshow.slides[0]  # First slide from fixture
            slide_dict = slide.to_dict()

            assert "id" in slide_dict
            assert slide_dict["slideshow_id"] == sample_slideshow.id
            assert slide_dict["title"] == "Test Image Slide"
            assert slide_dict["content_type"] == "image"
            assert slide_dict["content_url"] == "https://example.com/image.jpg"
            assert slide_dict["display_duration"] == 30
            assert slide_dict["order_index"] == 0
            assert slide_dict["is_active"] is True
            assert "created_at" in slide_dict
            assert "updated_at" in slide_dict

    def test_slide_item_content_types(self, app, sample_slideshow):
        """Test different content types for slide items."""
        with app.app_context():
            # Test image slide
            image_slide = SlideItem(
                slideshow_id=sample_slideshow.id,
                content_type="image",
                content_url="https://example.com/image.jpg",
            )
            db.session.add(image_slide)

            # Test text slide
            text_slide = SlideItem(
                slideshow_id=sample_slideshow.id,
                content_type="text",
                content_text="Test text content",
            )
            db.session.add(text_slide)

            # Test URL slide
            url_slide = SlideItem(
                slideshow_id=sample_slideshow.id,
                content_type="url",
                content_url="https://example.com/webpage",
            )
            db.session.add(url_slide)

            db.session.commit()

            # Verify all slides were created
            slides = SlideItem.query.filter_by(slideshow_id=sample_slideshow.id).all()
            content_types = [slide.content_type for slide in slides]

            assert "image" in content_types
            assert "text" in content_types
            assert "url" in content_types


class TestModelRelationships:
    """Test model relationships and constraints."""

    def test_cascade_delete(self, app):
        """Test that deleting a slideshow deletes its slides."""
        with app.app_context():
            # Create slideshow
            slideshow = Slideshow(name="Test Slideshow")
            db.session.add(slideshow)
            db.session.commit()

            # Add slides
            slide1 = SlideItem(slideshow_id=slideshow.id, content_type="text")
            slide2 = SlideItem(slideshow_id=slideshow.id, content_type="image")
            db.session.add(slide1)
            db.session.add(slide2)
            db.session.commit()

            slideshow_id = slideshow.id

            # Verify slides exist
            assert SlideItem.query.filter_by(slideshow_id=slideshow_id).count() == 2

            # Delete slideshow
            db.session.delete(slideshow)
            db.session.commit()

            # Verify slides are also deleted (cascade)
            assert SlideItem.query.filter_by(slideshow_id=slideshow_id).count() == 0

    def test_unique_slideshow_names(self, app):
        """Test that slideshow names must be unique."""
        with app.app_context():
            # Create first slideshow
            slideshow1 = Slideshow(name="Unique Name")
            db.session.add(slideshow1)
            db.session.commit()

            # Try to create second slideshow with same name
            slideshow2 = Slideshow(name="Unique Name")
            db.session.add(slideshow2)

            # This should raise an integrity error
            with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
                db.session.commit()
