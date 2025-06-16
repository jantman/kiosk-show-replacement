"""
Simple test for enhanced display interface functionality.

Tests key features without complex session management.
"""

import pytest

from kiosk_show_replacement import create_app, db
from kiosk_show_replacement.models import Display, Slideshow, SlideshowItem, User


class TestEnhancedDisplaySimple:
    """Simple test for enhanced display interface functionality."""

    @pytest.fixture
    def app(self, tmp_path):
        """Create test app."""
        app = create_app()

        # Configure for testing
        upload_folder = tmp_path / "uploads"
        upload_folder.mkdir()

        app.config.update(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SECRET_KEY": "test-secret-key",
                "UPLOAD_FOLDER": str(upload_folder),
                "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16MB
                "WTF_CSRF_ENABLED": False,
            }
        )

        with app.app_context():
            db.create_all()
            yield app
            try:
                db.session.rollback()
                db.session.close()
                db.session.remove()
                db.drop_all()
                db.engine.dispose()
            except Exception:
                pass

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_slideshow_item_display_url_property_uploaded_file(self, app):
        """Test SlideshowItem display_url property for uploaded files."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            # Create slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Test uploaded file
            uploaded_item = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                content_file_path="uploads/test.jpg",
                title="Test Image",
                display_duration=10,
                order_index=1,
                is_active=True,
            )

            assert uploaded_item.display_url == "/uploads/test.jpg"

    def test_slideshow_item_display_url_property_external_url(self, app):
        """Test SlideshowItem display_url property for external URLs."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            # Create slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Test external URL
            url_item = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="url",
                content_url="https://example.com",
                title="Test URL",
                display_duration=10,
                order_index=2,
                is_active=True,
            )

            assert url_item.display_url == "https://example.com"

    def test_slideshow_item_display_url_property_text_content(self, app):
        """Test SlideshowItem display_url property for text content."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            # Create slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Test text content (no URL)
            text_item = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="text",
                content_text="Test text content",
                title="Test Text",
                display_duration=10,
                order_index=3,
                is_active=True,
            )

            assert text_item.display_url is None

    def test_slideshow_item_to_dict_includes_display_url(self, app):
        """Test SlideshowItem.to_dict() includes display_url field."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            # Create slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            item = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                content_file_path="uploads/test.jpg",
                title="Test Image",
                display_duration=10,
                order_index=1,
                is_active=True,
            )

            item_dict = item.to_dict()

            assert "display_url" in item_dict
            assert item_dict["display_url"] == "/uploads/test.jpg"
            assert item_dict["content_type"] == "image"
            assert item_dict["title"] == "Test Image"

    def test_display_slideshow_endpoint_with_uploaded_files(self, client, app):
        """Test slideshow display endpoint properly handles uploaded files."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            # Create display
            display = Display(
                name="test-display", location="Test Location", is_active=True
            )
            db.session.add(display)
            db.session.commit()

            # Create slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Assign slideshow to display
            display.current_slideshow_id = slideshow.id
            db.session.commit()

            # Create slideshow item
            item = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                content_file_path="uploads/test-image.jpg",
                title="Test Uploaded Image",
                display_duration=10,
                order_index=1,
                is_active=True,
            )
            db.session.add(item)
            db.session.commit()

            response = client.get(f"/display/slideshow/{slideshow.id}")

            assert response.status_code == 200
            assert b"Test Slideshow" in response.data
            assert b"display_url" in response.data

            # Check that the slide data includes display_url
            html_content = response.data.decode()
            assert "/uploads/test-image.jpg" in html_content

    def test_enhanced_template_features_present(self, client, app):
        """Test that enhanced template features are present in the response."""
        with app.app_context():
            # Create user
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            # Create display
            display = Display(
                name="test-display", location="Test Location", is_active=True
            )
            db.session.add(display)
            db.session.commit()

            # Create slideshow
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Assign slideshow to display
            display.current_slideshow_id = slideshow.id
            db.session.commit()

            # Create slideshow item
            item = SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                content_file_path="uploads/test.jpg",
                title="Test Image",
                display_duration=10,
                order_index=1,
                is_active=True,
            )
            db.session.add(item)
            db.session.commit()

            response = client.get(f"/display/slideshow/{slideshow.id}")

            assert response.status_code == 200

            html_content = response.data.decode()

            # Check for enhanced features
            assert "preloadedContent" in html_content
            assert "contentCache" in html_content
            assert "SlideshowPlayer" in html_content
            assert "preload-indicator" in html_content
            assert "object-fit: contain" in html_content
            assert "@media (max-aspect-ratio: 16/9)" in html_content
