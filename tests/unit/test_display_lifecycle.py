"""
Unit tests for display lifecycle management features (archive/restore).

Tests cover:
- Display archive functionality
- Display restore functionality
- Display configuration templates
- Display configuration migration tools
"""

from datetime import datetime, timezone

import pytest

from kiosk_show_replacement.models import (
    Display,
    DisplayConfigurationTemplate,
    Slideshow,
    db,
)


class TestDisplayArchive:
    """Test display archive functionality."""

    def test_archive_display_sets_correct_fields(self, app, admin_user):
        """Test that archiving a display sets all correct fields."""
        with app.app_context():
            # Create a slideshow to assign to the display
            slideshow = Slideshow(
                name="Test Slideshow",
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(slideshow)
            db.session.commit()

            # Create test display with slideshow assigned
            display = Display(
                name="Test Display",
                description="Test display for archiving",
                is_active=True,
                is_archived=False,
                current_slideshow_id=slideshow.id,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(display)
            db.session.commit()

            # Archive the display
            display.archive(admin_user)

            # Check all archive fields are set correctly
            assert display.is_archived is True
            assert display.archived_at is not None
            assert display.archived_by_id == admin_user.id
            assert display.is_active is False  # Should be deactivated
            assert display.current_slideshow_id is None  # Should clear slideshow

            # Check archived_at is recent
            time_diff = datetime.now(timezone.utc) - display.archived_at
            assert time_diff.total_seconds() < 5  # Within 5 seconds

    def test_restore_display_clears_archive_fields(self, app, admin_user):
        """Test that restoring a display clears archive fields."""
        with app.app_context():
            # Create archived display
            display = Display(
                name="Archived Display",
                description="Test archived display",
                is_active=False,
                is_archived=True,
                archived_at=datetime.now(timezone.utc),
                archived_by_id=admin_user.id,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(display)
            db.session.commit()

            # Restore the display
            display.restore()

            # Check all archive fields are cleared
            assert display.is_archived is False
            assert display.archived_at is None
            assert display.archived_by_id is None
            assert display.is_active is True  # Should be reactivated

    def test_can_be_assigned_property(self, app, admin_user):
        """Test the can_be_assigned property logic."""
        with app.app_context():
            # Active, non-archived display - can be assigned
            display = Display(
                name="Active Display",
                is_active=True,
                is_archived=False,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            assert display.can_be_assigned is True

            # Inactive display - cannot be assigned
            display.is_active = False
            assert display.can_be_assigned is False

            # Archived display - cannot be assigned
            display.is_active = True
            display.is_archived = True
            assert display.can_be_assigned is False

            # Both inactive and archived - cannot be assigned
            display.is_active = False
            display.is_archived = True
            assert display.can_be_assigned is False

    def test_display_to_dict_includes_archive_fields(self, app, admin_user):
        """Test that to_dict includes archive fields."""
        with app.app_context():
            display = Display(
                name="Test Display",
                is_archived=True,
                archived_at=datetime.now(timezone.utc),
                archived_by_id=admin_user.id,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(display)
            db.session.commit()

            result = display.to_dict()

            assert "is_archived" in result
            assert "archived_at" in result
            assert "archived_by_id" in result
            assert result["is_archived"] is True
            assert result["archived_at"] is not None
            assert result["archived_by_id"] == admin_user.id


class TestDisplayConfiguration:
    """Test display configuration management."""

    def test_get_configuration_dict(self, app, admin_user):
        """Test getting display configuration as dictionary."""
        with app.app_context():
            display = Display(
                name="Test Display",
                description="Test description",
                resolution_width=1920,
                resolution_height=1080,
                rotation=90,
                location="Office A",
                heartbeat_interval=30,
                show_info_overlay=True,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )

            config = display.get_configuration_dict()

            expected_config = {
                "name": "Test Display",
                "description": "Test description",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "rotation": 90,
                "location": "Office A",
                "heartbeat_interval": 30,
                "show_info_overlay": True,
            }

            assert config == expected_config

    def test_apply_configuration_updates_fields(self, app, admin_user):
        """Test applying configuration updates display fields."""
        with app.app_context():
            display = Display(
                name="Old Name",
                description="Old description",
                resolution_width=800,
                resolution_height=600,
                rotation=0,
                location="Old Location",
                heartbeat_interval=60,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(display)
            db.session.commit()

            new_config = {
                "name": "New Name",
                "description": "New description",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "rotation": 180,
                "location": "New Location",
                "heartbeat_interval": 30,
            }

            original_updated_at = display.updated_at

            # Add a small delay to ensure updated_at changes
            import time

            time.sleep(0.01)

            display.apply_configuration(new_config, admin_user)

            # Check all fields were updated
            assert display.name == "New Name"
            assert display.description == "New description"
            assert display.resolution_width == 1920
            assert display.resolution_height == 1080
            assert display.rotation == 180
            assert display.location == "New Location"
            assert display.heartbeat_interval == 30
            assert display.updated_by_id == admin_user.id

            # Ensure both datetimes are timezone-aware for comparison
            from datetime import timezone

            if original_updated_at.tzinfo is None:
                original_updated_at = original_updated_at.replace(tzinfo=timezone.utc)
            if display.updated_at.tzinfo is None:
                display.updated_at = display.updated_at.replace(tzinfo=timezone.utc)
            assert display.updated_at > original_updated_at

    def test_apply_configuration_partial_update(self, app, admin_user):
        """Test applying partial configuration only updates specified fields."""
        with app.app_context():
            display = Display(
                name="Original Name",
                description="Original description",
                resolution_width=800,
                rotation=90,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(display)
            db.session.commit()

            # Only update some fields
            partial_config = {
                "name": "Updated Name",
                "resolution_width": 1920,
            }

            display.apply_configuration(partial_config, admin_user)

            # Check only specified fields were updated
            assert display.name == "Updated Name"
            assert display.resolution_width == 1920
            # These should remain unchanged
            assert display.description == "Original description"
            assert display.rotation == 90


class TestDisplayConfigurationTemplate:
    """Test display configuration template functionality."""

    def test_create_template_with_all_fields(self, app, admin_user):
        """Test creating a complete configuration template."""
        with app.app_context():
            template = DisplayConfigurationTemplate(
                name="Office Template",
                description="Standard office display configuration",
                template_resolution_width=1920,
                template_resolution_height=1080,
                template_rotation=0,
                template_heartbeat_interval=30,
                template_location="Office Building",
                is_default=True,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(template)
            db.session.commit()

            assert template.id is not None
            assert template.name == "Office Template"
            assert template.template_resolution_width == 1920
            assert template.is_default is True

    def test_template_to_dict_serialization(self, app, admin_user):
        """Test template serialization to dictionary."""
        with app.app_context():
            template = DisplayConfigurationTemplate(
                name="Test Template",
                description="Test template description",
                template_resolution_width=1920,
                template_resolution_height=1080,
                template_rotation=90,
                template_heartbeat_interval=45,
                template_location="Test Location",
                is_default=False,
                is_active=True,
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(template)
            db.session.commit()

            result = template.to_dict()

            assert result["name"] == "Test Template"
            assert result["template_resolution_width"] == 1920
            assert result["template_resolution_height"] == 1080
            assert result["template_rotation"] == 90
            assert result["template_heartbeat_interval"] == 45
            assert result["template_location"] == "Test Location"
            assert result["is_default"] is False
            assert result["is_active"] is True
            assert result["owner_id"] == admin_user.id

    def test_template_to_configuration_dict(self, app, admin_user):
        """Test converting template to configuration dictionary."""
        with app.app_context():
            template = DisplayConfigurationTemplate(
                name="Test Template",
                template_resolution_width=1920,
                template_resolution_height=1080,
                template_rotation=180,
                template_heartbeat_interval=20,
                template_location="Conference Room",
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )

            config = template.to_configuration_dict()

            expected_config = {
                "resolution_width": 1920,
                "resolution_height": 1080,
                "rotation": 180,
                "heartbeat_interval": 20,
                "location": "Conference Room",
            }

            assert config == expected_config

    def test_template_name_validation(self, app, admin_user):
        """Test template name validation."""
        with app.app_context():
            template = DisplayConfigurationTemplate(
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )

            # Test too short name
            with pytest.raises(ValueError, match="must be at least 2 characters"):
                template.name = "a"

            # Test too long name
            with pytest.raises(ValueError, match="must be 100 characters or less"):
                template.name = "x" * 101

            # Test valid name
            template.name = "Valid Template Name"
            assert template.name == "Valid Template Name"

    def test_template_rotation_validation(self, app, admin_user):
        """Test template rotation validation."""
        with app.app_context():
            template = DisplayConfigurationTemplate(
                name="Test Template",
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )

            # Test invalid rotation
            with pytest.raises(ValueError, match="must be one of"):
                template.template_rotation = 45

            # Test valid rotations
            for rotation in [0, 90, 180, 270]:
                template.template_rotation = rotation
                assert template.template_rotation == rotation

    def test_template_resolution_validation(self, app, admin_user):
        """Test template resolution validation."""
        with app.app_context():
            template = DisplayConfigurationTemplate(
                name="Test Template",
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )

            # Test invalid resolutions
            with pytest.raises(ValueError, match="must be between 1 and 10000"):
                template.template_resolution_width = 0

            with pytest.raises(ValueError, match="must be between 1 and 10000"):
                template.template_resolution_height = 10001

            # Test valid resolutions
            template.template_resolution_width = 1920
            template.template_resolution_height = 1080
            assert template.template_resolution_width == 1920
            assert template.template_resolution_height == 1080

    def test_unique_template_name_per_owner_constraint(
        self, app, admin_user, regular_user
    ):
        """Test that template names must be unique per owner."""
        with app.app_context():
            # Create first template
            template1 = DisplayConfigurationTemplate(
                name="Shared Name",
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(template1)
            db.session.commit()

            # Different user can use same name
            template2 = DisplayConfigurationTemplate(
                name="Shared Name",
                owner_id=regular_user.id,
                created_by_id=regular_user.id,
            )
            db.session.add(template2)
            db.session.commit()  # Should succeed

            # Same user cannot use same name again
            template3 = DisplayConfigurationTemplate(
                name="Shared Name",
                owner_id=admin_user.id,
                created_by_id=admin_user.id,
            )
            db.session.add(template3)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
