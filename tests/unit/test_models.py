"""
Comprehensive unit tests for database models.

Tests all model methods, properties, validators, relationships, and business logic.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from kiosk_show_replacement import create_app, db
from kiosk_show_replacement.models import User, Display, Slideshow, SlideshowItem


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_display(app, sample_user):
    """Create a sample display for testing."""
    with app.app_context():
        display = Display(
            name="Test Display",
            location="Test Location",
            resolution="1920x1080",
            owner_id=sample_user.id
        )
        db.session.add(display)
        db.session.commit()
        return display


@pytest.fixture
def sample_slideshow(app, sample_user):
    """Create a sample slideshow with items for testing."""
    with app.app_context():
        slideshow = Slideshow(
            name="Test Slideshow",
            description="A slideshow for testing",
            default_duration=30,
            owner_id=sample_user.id
        )
        db.session.add(slideshow)
        db.session.commit()
        
        # Add some slideshow items
        items = [
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="image",
                content_source="https://example.com/image1.jpg",
                duration=30,
                order_index=0
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="url",
                content_source="https://example.com/page1",
                duration=45,
                order_index=1
            ),
            SlideshowItem(
                slideshow_id=slideshow.id,
                content_type="text",
                content_source="Test text content",
                duration=20,
                order_index=2
            )
        ]
        
        for item in items:
            db.session.add(item)
        
        db.session.commit()
        return slideshow


class TestUserModel:
    """Test cases for the User model."""

    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username="testuser",
                email="test@example.com",
                full_name="Test User"
            )
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.full_name == "Test User"
            assert user.is_active is True
            assert user.is_admin is False
            assert user.created_at is not None
            assert user.updated_at is not None
            assert user.password_hash is not None
            assert user.password_hash != "testpassword"  # Should be hashed

    def test_user_password_hashing(self, app):
        """Test password hashing and checking."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("testpassword")
            
            assert user.check_password("testpassword") is True
            assert user.check_password("wrongpassword") is False

    def test_user_repr(self, app):
        """Test user string representation."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            assert repr(user) == "<User testuser>"

    def test_user_to_dict(self, app, sample_user):
        """Test user serialization to dictionary."""
        with app.app_context():
            user_dict = sample_user.to_dict()

            assert "id" in user_dict
            assert user_dict["username"] == "testuser"
            assert user_dict["email"] == "test@example.com"
            assert user_dict["full_name"] == "Test User"
            assert user_dict["is_active"] is True
            assert user_dict["is_admin"] is False
            assert "created_at" in user_dict
            assert "updated_at" in user_dict
            # Password hash should not be included
            assert "password_hash" not in user_dict

    def test_username_validation(self, app):
        """Test username validation."""
        with app.app_context():
            # Valid username
            user1 = User(username="validuser", email="test1@example.com")
            db.session.add(user1)
            db.session.commit()

            # Invalid usernames should be caught by SQLAlchemy validators
            # Testing short username
            with pytest.raises(ValueError, match="Username must be between 3 and 30 characters"):
                user2 = User(username="ab", email="test2@example.com")
                db.session.add(user2)
                db.session.commit()

            # Testing username with invalid characters
            with pytest.raises(ValueError, match="Username can only contain letters, numbers, and underscores"):
                user3 = User(username="invalid-user!", email="test3@example.com")
                db.session.add(user3)
                db.session.commit()

    def test_email_validation(self, app):
        """Test email validation."""
        with app.app_context():
            # Valid email
            user1 = User(username="user1", email="valid@example.com")
            db.session.add(user1)
            db.session.commit()

            # Invalid email should be caught by validator
            with pytest.raises(ValueError, match="Invalid email address"):
                user2 = User(username="user2", email="invalid-email")
                db2.session.add(user2)
                db.session.commit()

    def test_unique_constraints(self, app):
        """Test unique constraints on username and email."""
        with app.app_context():
            # Create first user
            user1 = User(username="testuser", email="test@example.com")
            db.session.add(user1)
            db.session.commit()

            # Try to create user with same username
            user2 = User(username="testuser", email="other@example.com")
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()
            
            db.session.rollback()

            # Try to create user with same email
            user3 = User(username="otheruser", email="test@example.com")
            db.session.add(user3)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestDisplayModel:
    """Test cases for the Display model."""

    def test_create_display(self, app, sample_user):
        """Test creating a new display."""
        with app.app_context():
            display = Display(
                name="Test Display",
                location="Test Location",
                resolution="1920x1080",
                owner_id=sample_user.id
            )
            db.session.add(display)
            db.session.commit()

            assert display.id is not None
            assert display.name == "Test Display"
            assert display.location == "Test Location"
            assert display.resolution == "1920x1080"
            assert display.owner_id == sample_user.id
            assert display.is_active is True
            assert display.last_heartbeat is None
            assert display.created_at is not None
            assert display.updated_at is not None

    def test_display_repr(self, app, sample_display):
        """Test display string representation."""
        with app.app_context():
            assert repr(sample_display) == "<Display Test Display>"

    def test_display_to_dict(self, app, sample_display):
        """Test display serialization to dictionary."""
        with app.app_context():
            display_dict = sample_display.to_dict()

            assert "id" in display_dict
            assert display_dict["name"] == "Test Display"
            assert display_dict["location"] == "Test Location"
            assert display_dict["resolution"] == "1920x1080"
            assert display_dict["is_active"] is True
            assert display_dict["is_online"] is False  # No heartbeat yet
            assert "created_at" in display_dict
            assert "updated_at" in display_dict

    def test_display_online_status(self, app, sample_display):
        """Test display online status calculation."""
        with app.app_context():
            # Initially offline (no heartbeat)
            assert sample_display.is_online is False

            # Set recent heartbeat
            sample_display.last_heartbeat = datetime.utcnow()
            db.session.commit()
            assert sample_display.is_online is True

            # Set old heartbeat (more than 5 minutes ago)
            sample_display.last_heartbeat = datetime.utcnow() - timedelta(minutes=10)
            db.session.commit()
            assert sample_display.is_online is False

    def test_display_heartbeat_update(self, app, sample_display):
        """Test updating display heartbeat."""
        with app.app_context():
            initial_heartbeat = sample_display.last_heartbeat
            
            # Update heartbeat
            sample_display.update_heartbeat()
            db.session.commit()
            
            assert sample_display.last_heartbeat is not None
            assert sample_display.last_heartbeat != initial_heartbeat
            assert sample_display.is_online is True

    def test_display_unique_name_per_owner(self, app, sample_user):
        """Test that display names must be unique per owner."""
        with app.app_context():
            # Create first display
            display1 = Display(name="Unique Display", owner_id=sample_user.id)
            db.session.add(display1)
            db.session.commit()

            # Try to create second display with same name and owner
            display2 = Display(name="Unique Display", owner_id=sample_user.id)
            db.session.add(display2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_display_owner_relationship(self, app, sample_display, sample_user):
        """Test display-owner relationship."""
        with app.app_context():
            assert sample_display.owner == sample_user
            assert sample_display in sample_user.displays


class TestSlideshowModel:
    """Test cases for the Slideshow model."""

    def test_create_slideshow(self, app, sample_user):
        """Test creating a new slideshow."""
        with app.app_context():
            slideshow = Slideshow(
                name="Test Slideshow",
                description="A test slideshow",
                default_duration=30,
                owner_id=sample_user.id
            )
            db.session.add(slideshow)
            db.session.commit()

            assert slideshow.id is not None
            assert slideshow.name == "Test Slideshow"
            assert slideshow.description == "A test slideshow"
            assert slideshow.default_duration == 30
            assert slideshow.owner_id == sample_user.id
            assert slideshow.is_active is True
            assert slideshow.created_at is not None
            assert slideshow.updated_at is not None

    def test_slideshow_repr(self, app, sample_slideshow):
        """Test slideshow string representation."""
        with app.app_context():
            assert repr(sample_slideshow) == "<Slideshow Test Slideshow>"

    def test_slideshow_to_dict(self, app, sample_slideshow):
        """Test slideshow serialization to dictionary."""
        with app.app_context():
            slideshow_dict = sample_slideshow.to_dict()

            assert "id" in slideshow_dict
            assert slideshow_dict["name"] == "Test Slideshow"
            assert slideshow_dict["description"] == "A slideshow for testing"
            assert slideshow_dict["default_duration"] == 30
            assert slideshow_dict["is_active"] is True
            assert slideshow_dict["item_count"] == 3
            assert slideshow_dict["total_duration"] == 95  # 30+45+20
            assert "created_at" in slideshow_dict
            assert "updated_at" in slideshow_dict

    def test_slideshow_item_count_property(self, app, sample_slideshow):
        """Test slideshow item count property."""
        with app.app_context():
            assert sample_slideshow.item_count == 3

    def test_slideshow_total_duration_property(self, app, sample_slideshow):
        """Test slideshow total duration calculation."""
        with app.app_context():
            # 30 + 45 + 20 = 95 seconds
            assert sample_slideshow.total_duration == 95

    def test_slideshow_items_relationship(self, app, sample_slideshow):
        """Test slideshow-items relationship."""
        with app.app_context():
            assert len(sample_slideshow.items) == 3

            # Test that items are properly related and ordered
            items = sample_slideshow.items
            assert items[0].order_index == 0
            assert items[1].order_index == 1
            assert items[2].order_index == 2

            for item in items:
                assert item.slideshow_id == sample_slideshow.id
                assert item.slideshow == sample_slideshow

    def test_slideshow_unique_name_per_owner(self, app, sample_user):
        """Test that slideshow names must be unique per owner."""
        with app.app_context():
            # Create first slideshow
            slideshow1 = Slideshow(name="Unique Slideshow", owner_id=sample_user.id)
            db.session.add(slideshow1)
            db.session.commit()

            # Try to create second slideshow with same name and owner
            slideshow2 = Slideshow(name="Unique Slideshow", owner_id=sample_user.id)
            db.session.add(slideshow2)
            
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_slideshow_owner_relationship(self, app, sample_slideshow, sample_user):
        """Test slideshow-owner relationship."""
        with app.app_context():
            assert sample_slideshow.owner == sample_user
            assert sample_slideshow in sample_user.slideshows


class TestSlideshowItemModel:
    """Test cases for the SlideshowItem model."""

    def test_create_slideshow_item(self, app, sample_slideshow):
        """Test creating a new slideshow item."""
        with app.app_context():
            item = SlideshowItem(
                slideshow_id=sample_slideshow.id,
                content_type="image",
                content_source="https://example.com/image.jpg",
                duration=60,
                order_index=10
            )
            db.session.add(item)
            db.session.commit()

            assert item.id is not None
            assert item.slideshow_id == sample_slideshow.id
            assert item.content_type == "image"
            assert item.content_source == "https://example.com/image.jpg"
            assert item.duration == 60
            assert item.order_index == 10
            assert item.is_active is True
            assert item.created_at is not None
            assert item.updated_at is not None

    def test_slideshow_item_repr(self, app, sample_slideshow):
        """Test slideshow item string representation."""
        with app.app_context():
            item = SlideshowItem(
                slideshow_id=sample_slideshow.id,
                content_type="image",
                content_source="https://example.com/image.jpg"
            )
            assert repr(item) == "<SlideshowItem image>"

    def test_slideshow_item_to_dict(self, app, sample_slideshow):
        """Test slideshow item serialization to dictionary."""
        with app.app_context():
            item = sample_slideshow.items[0]  # First item from fixture
            item_dict = item.to_dict()

            assert "id" in item_dict
            assert item_dict["slideshow_id"] == sample_slideshow.id
            assert item_dict["content_type"] == "image"
            assert item_dict["content_source"] == "https://example.com/image1.jpg"
            assert item_dict["duration"] == 30
            assert item_dict["order_index"] == 0
            assert item_dict["is_active"] is True
            assert "created_at" in item_dict
            assert "updated_at" in item_dict

    def test_slideshow_item_content_types(self, app, sample_slideshow):
        """Test different content types for slideshow items."""
        with app.app_context():
            items = sample_slideshow.items
            content_types = [item.content_type for item in items]

            assert "image" in content_types
            assert "url" in content_types
            assert "text" in content_types

    def test_slideshow_item_content_type_validation(self, app, sample_slideshow):
        """Test content type validation."""
        with app.app_context():
            # Valid content type
            item1 = SlideshowItem(
                slideshow_id=sample_slideshow.id,
                content_type="image",
                content_source="https://example.com/image.jpg"
            )
            db.session.add(item1)
            db.session.commit()

            # Invalid content type should be caught by validator
            with pytest.raises(ValueError, match="Content type must be one of"):
                item2 = SlideshowItem(
                    slideshow_id=sample_slideshow.id,
                    content_type="invalid_type",
                    content_source="some content"
                )
                db.session.add(item2)
                db.session.commit()

    def test_slideshow_item_url_validation(self, app, sample_slideshow):
        """Test URL validation for URL content type."""
        with app.app_context():
            # Valid URL
            item1 = SlideshowItem(
                slideshow_id=sample_slideshow.id,
                content_type="url",
                content_source="https://example.com/page"
            )
            db.session.add(item1)
            db.session.commit()

            # Invalid URL should be caught by validator
            with pytest.raises(ValueError, match="Invalid URL format"):
                item2 = SlideshowItem(
                    slideshow_id=sample_slideshow.id,
                    content_type="url",
                    content_source="not-a-valid-url"
                )
                db.session.add(item2)
                db.session.commit()

    def test_slideshow_item_slideshow_relationship(self, app, sample_slideshow):
        """Test slideshow item-slideshow relationship."""
        with app.app_context():
            item = sample_slideshow.items[0]
            assert item.slideshow == sample_slideshow


class TestModelRelationships:
    """Test model relationships and constraints."""

    def test_cascade_delete_slideshow_items(self, app, sample_slideshow):
        """Test that deleting a slideshow deletes its items."""
        with app.app_context():
            slideshow_id = sample_slideshow.id

            # Verify items exist
            assert SlideshowItem.query.filter_by(slideshow_id=slideshow_id).count() == 3

            # Delete slideshow
            db.session.delete(sample_slideshow)
            db.session.commit()

            # Verify items are also deleted (cascade)
            assert SlideshowItem.query.filter_by(slideshow_id=slideshow_id).count() == 0

    def test_cascade_delete_user_displays(self, app, sample_user, sample_display):
        """Test that deleting a user deletes their displays.""" 
        with app.app_context():
            user_id = sample_user.id

            # Verify display exists
            assert Display.query.filter_by(owner_id=user_id).count() == 1

            # Delete user
            db.session.delete(sample_user)
            db.session.commit()

            # Verify displays are also deleted (cascade)
            assert Display.query.filter_by(owner_id=user_id).count() == 0

    def test_cascade_delete_user_slideshows(self, app, sample_user, sample_slideshow):
        """Test that deleting a user deletes their slideshows and items."""
        with app.app_context():
            user_id = sample_user.id
            slideshow_id = sample_slideshow.id

            # Verify slideshow and items exist
            assert Slideshow.query.filter_by(owner_id=user_id).count() == 1
            assert SlideshowItem.query.filter_by(slideshow_id=slideshow_id).count() == 3

            # Delete user
            db.session.delete(sample_user)
            db.session.commit()

            # Verify slideshows and items are also deleted (cascade)
            assert Slideshow.query.filter_by(owner_id=user_id).count() == 0
            assert SlideshowItem.query.filter_by(slideshow_id=slideshow_id).count() == 0

    def test_audit_fields_auto_update(self, app, sample_user):
        """Test that audit fields are automatically updated."""
        with app.app_context():
            # Test creation timestamps
            user = User(username="audituser", email="audit@example.com")
            db.session.add(user)
            db.session.commit()

            assert user.created_at is not None
            assert user.updated_at is not None
            assert user.created_at == user.updated_at

            # Test update timestamp
            original_updated_at = user.updated_at
            user.full_name = "Updated Name"
            db.session.commit()

            assert user.updated_at > original_updated_at

    def test_foreign_key_constraints(self, app):
        """Test foreign key constraints."""
        with app.app_context():
            # Try to create display with invalid owner_id
            display = Display(name="Invalid Display", owner_id=99999)
            db.session.add(display)
            
            with pytest.raises(IntegrityError):
                db.session.commit()
            
            db.session.rollback()

            # Try to create slideshow item with invalid slideshow_id
            item = SlideshowItem(
                slideshow_id=99999,
                content_type="image",
                content_source="https://example.com/image.jpg"
            )
            db.session.add(item)
            
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestDatabaseUtilityMethods:
    """Test utility methods and business logic."""

    def test_user_password_methods(self, app):
        """Test user password utility methods."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            
            # Test password setting and checking
            user.set_password("mypassword")
            assert user.password_hash is not None
            assert user.check_password("mypassword") is True
            assert user.check_password("wrongpassword") is False

    def test_display_heartbeat_methods(self, app, sample_display):
        """Test display heartbeat utility methods."""
        with app.app_context():
            # Test heartbeat update
            assert sample_display.last_heartbeat is None
            sample_display.update_heartbeat()
            assert sample_display.last_heartbeat is not None
            assert sample_display.is_online is True

    def test_model_serialization(self, app, sample_user, sample_display, sample_slideshow):
        """Test that all models can be serialized to dict."""
        with app.app_context():
            # Test all models have to_dict method and return dict
            user_dict = sample_user.to_dict()
            display_dict = sample_display.to_dict()
            slideshow_dict = sample_slideshow.to_dict()
            item_dict = sample_slideshow.items[0].to_dict()

            assert isinstance(user_dict, dict)
            assert isinstance(display_dict, dict)
            assert isinstance(slideshow_dict, dict)
            assert isinstance(item_dict, dict)

            # Test that sensitive information is not included
            assert "password_hash" not in user_dict

    def test_model_string_representations(self, app, sample_user, sample_display, sample_slideshow):
        """Test that all models have proper string representations."""
        with app.app_context():
            assert "testuser" in repr(sample_user)
            assert "Test Display" in repr(sample_display)
            assert "Test Slideshow" in repr(sample_slideshow)
            assert "image" in repr(sample_slideshow.items[0])
