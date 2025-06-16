"""
Tests for enhanced display interface functionality.

This module tests the enhanced display interface features including:
- Uploaded file integration with display interface
- Enhanced video playback management
- Content scaling and responsive design
- Performance optimizations and caching
- Web page embedding improvements
"""

import pytest

from kiosk_show_replacement import create_app, db
from kiosk_show_replacement.models import Display, Slideshow, SlideshowItem, User


class TestEnhancedDisplayInterface:
    """Test enhanced display interface functionality."""

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

    @pytest.fixture
    def user(self, app):
        """Create test user."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            db.session.close()

        def get_user():
            with app.app_context():
                return db.session.get(User, user_id)

        return get_user

    @pytest.fixture
    def display(self, app):
        """Create test display."""
        with app.app_context():
            display = Display(
                name="test-display", location="Test Location", is_active=True
            )
            db.session.add(display)
            db.session.commit()
            display_id = display.id
            db.session.close()

        def get_display():
            with app.app_context():
                return db.session.get(Display, display_id)

        return get_display

    @pytest.fixture
    def slideshow(self, app, user, display):
        """Create test slideshow."""
        with app.app_context():
            user_obj = user()
            slideshow = Slideshow(
                name="Test Slideshow",
                description="Test Description",
                is_active=True,
                owner_id=user_obj.id,
            )
            db.session.add(slideshow)
            db.session.commit()
            slideshow_id = slideshow.id

            # Assign slideshow to display
            display_obj = display()
            display_obj.current_slideshow_id = slideshow_id
            db.session.commit()
            db.session.close()

        def get_slideshow():
            with app.app_context():
                return db.session.get(Slideshow, slideshow_id)

        return get_slideshow

    @pytest.fixture
    def uploaded_file_slide(self, app, slideshow):
        """Create slideshow item for uploaded file."""
        with app.app_context():
            slideshow_obj = slideshow()
            item = SlideshowItem(
                slideshow_id=slideshow_obj.id,
                content_type="image",
                content_file_path="uploads/test-image.jpg",
                title="Test Uploaded Image",
                display_duration=10,
                order_index=1,
                is_active=True,
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id
            db.session.close()

        def get_item():
            with app.app_context():
                return db.session.get(SlideshowItem, item_id)

        return get_item

    def test_simple_enhanced_features(
        self, auth_client, display, slideshow, uploaded_file_slide
    ):
        """Test basic enhanced display features work correctly."""
        with auth_client.application.app_context():
            display_obj = display()
            slideshow_obj = slideshow()
            response = auth_client.get(
                f"/display/{display_obj.name}/slideshow/{slideshow_obj.id}"
            )

            assert response.status_code == 200
            html_content = response.data.decode()

            # Check for enhanced features
            assert "SlideshowPlayer" in html_content
            assert "preloadedContent" in html_content
            assert "contentCache" in html_content
