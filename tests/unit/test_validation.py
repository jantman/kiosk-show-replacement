"""
Tests for data validation utilities.

This module tests:
- DataValidator class
- StorageIntegrityChecker class
- Slideshow and display validation functions
"""

import pytest

from kiosk_show_replacement.exceptions import ValidationError
from kiosk_show_replacement.validation import (
    DataValidator,
    validate_display_data,
    validate_slideshow_data,
)


class TestDataValidator:
    """Tests for the DataValidator class."""

    def test_validate_required_all_present(self):
        """Test validation passes when all required fields present."""
        data = {"name": "Test", "description": "A description"}
        # Should not raise
        DataValidator.validate_required(data, ["name", "description"])

    def test_validate_required_missing_fields(self):
        """Test validation fails when fields are missing."""
        data = {"name": "Test"}
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_required(data, ["name", "description"])
        assert "Missing required fields" in str(exc_info.value)
        assert "description" in str(exc_info.value.details["missing_fields"])

    def test_validate_required_empty_fields(self):
        """Test validation fails when fields are empty."""
        data = {"name": "", "description": "test"}
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_required(data, ["name", "description"])
        assert "Empty required fields" in str(exc_info.value)

    def test_validate_required_none_fields(self):
        """Test validation fails when fields are None."""
        data = {"name": None, "description": "test"}
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_required(data, ["name"])
        assert "Empty required fields" in str(exc_info.value)

    def test_validate_string_length_valid(self):
        """Test string length validation passes for valid length."""
        DataValidator.validate_string_length(
            "hello", "field", min_length=1, max_length=10
        )

    def test_validate_string_length_too_short(self):
        """Test validation fails when string too short."""
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_string_length("hi", "name", min_length=3)
        assert "at least 3 characters" in str(exc_info.value)

    def test_validate_string_length_too_long(self):
        """Test validation fails when string too long."""
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_string_length("hello world", "name", max_length=5)
        assert "at most 5 characters" in str(exc_info.value)

    def test_validate_integer_range_valid(self):
        """Test integer range validation passes for valid value."""
        DataValidator.validate_integer_range(5, "count", min_value=1, max_value=10)

    def test_validate_integer_range_too_low(self):
        """Test validation fails when value too low."""
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_integer_range(0, "count", min_value=1)
        assert "at least 1" in str(exc_info.value)

    def test_validate_integer_range_too_high(self):
        """Test validation fails when value too high."""
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_integer_range(100, "count", max_value=50)
        assert "at most 50" in str(exc_info.value)

    def test_validate_email_valid(self):
        """Test email validation passes for valid email."""
        DataValidator.validate_email("user@example.com")

    def test_validate_email_invalid(self):
        """Test validation fails for invalid email."""
        with pytest.raises(ValidationError):
            DataValidator.validate_email("not-an-email")

    def test_validate_email_no_domain(self):
        """Test validation fails for email without domain."""
        with pytest.raises(ValidationError):
            DataValidator.validate_email("user@")

    def test_validate_username_valid(self):
        """Test username validation passes for valid username."""
        DataValidator.validate_username("test_user-123")

    def test_validate_username_too_short(self):
        """Test validation fails for username too short."""
        with pytest.raises(ValidationError):
            DataValidator.validate_username("ab")

    def test_validate_username_invalid_chars(self):
        """Test validation fails for username with invalid characters."""
        with pytest.raises(ValidationError):
            DataValidator.validate_username("user@name")

    def test_validate_choice_valid(self):
        """Test choice validation passes for valid choice."""
        DataValidator.validate_choice("red", "color", {"red", "green", "blue"})

    def test_validate_choice_invalid(self):
        """Test validation fails for invalid choice."""
        with pytest.raises(ValidationError) as exc_info:
            DataValidator.validate_choice("yellow", "color", {"red", "green", "blue"})
        assert "Invalid value" in str(exc_info.value)


class TestValidateSlideshowData:
    """Tests for slideshow data validation."""

    def test_valid_slideshow_data(self):
        """Test validation passes for valid slideshow data."""
        data = {
            "name": "My Slideshow",
            "description": "A test slideshow",
            "default_item_duration": 30,
        }
        # Should not raise
        validate_slideshow_data(data)

    def test_name_too_long(self):
        """Test validation fails for name too long."""
        data = {"name": "x" * 101}
        with pytest.raises(ValidationError):
            validate_slideshow_data(data)

    def test_name_empty(self):
        """Test validation fails for empty name."""
        data = {"name": ""}
        with pytest.raises(ValidationError) as exc_info:
            validate_slideshow_data(data)
        assert "at least 1" in str(exc_info.value)

    def test_name_whitespace_only(self):
        """Test validation fails for whitespace-only name."""
        data = {"name": "   "}
        with pytest.raises(ValidationError):
            validate_slideshow_data(data)

    def test_description_too_long(self):
        """Test validation fails for description too long."""
        data = {"name": "Test", "description": "x" * 1001}
        with pytest.raises(ValidationError):
            validate_slideshow_data(data)

    def test_duration_too_low(self):
        """Test validation fails for duration too low."""
        data = {"name": "Test", "default_item_duration": 0}
        with pytest.raises(ValidationError) as exc_info:
            validate_slideshow_data(data)
        assert "at least 1" in str(exc_info.value)

    def test_duration_too_high(self):
        """Test validation fails for duration too high."""
        data = {"name": "Test", "default_item_duration": 3601}
        with pytest.raises(ValidationError) as exc_info:
            validate_slideshow_data(data)
        assert "at most 3600" in str(exc_info.value)

    def test_duration_not_integer(self):
        """Test validation fails for non-integer duration."""
        data = {"name": "Test", "default_item_duration": "30"}
        with pytest.raises(ValidationError):
            validate_slideshow_data(data)


class TestValidateDisplayData:
    """Tests for display data validation."""

    def test_valid_display_data(self):
        """Test validation passes for valid display data."""
        data = {
            "name": "Display 1",
            "description": "Main lobby display",
        }
        # Should not raise
        validate_display_data(data)

    def test_name_too_long(self):
        """Test validation fails for name too long."""
        data = {"name": "x" * 101}
        with pytest.raises(ValidationError):
            validate_display_data(data)

    def test_name_empty(self):
        """Test validation fails for empty name."""
        data = {"name": ""}
        with pytest.raises(ValidationError):
            validate_display_data(data)

    def test_description_too_long(self):
        """Test validation fails for description too long."""
        data = {"name": "Test", "description": "x" * 1001}
        with pytest.raises(ValidationError):
            validate_display_data(data)


class TestStorageIntegrityChecker:
    """Tests for StorageIntegrityChecker class."""

    def test_find_orphaned_files(self, app):
        """Test finding orphaned files."""
        from kiosk_show_replacement.validation import StorageIntegrityChecker

        with app.app_context():
            checker = StorageIntegrityChecker()
            # Should not raise, returns list
            result = checker.find_orphaned_files()
            assert isinstance(result, list)

    def test_find_missing_files(self, app):
        """Test finding missing files."""
        from kiosk_show_replacement.validation import StorageIntegrityChecker

        with app.app_context():
            checker = StorageIntegrityChecker()
            # Should not raise, returns list
            result = checker.find_missing_files()
            assert isinstance(result, list)

    def test_check_storage_consistency(self, app):
        """Test storage consistency check."""
        from kiosk_show_replacement.validation import StorageIntegrityChecker

        with app.app_context():
            checker = StorageIntegrityChecker()
            result = checker.check_storage_consistency()

            assert "is_consistent" in result
            assert "total_files" in result
            assert "total_size_bytes" in result
            assert "orphaned_files" in result
            assert "missing_files" in result

    def test_cleanup_orphaned_files_dry_run(self, app):
        """Test orphaned files cleanup in dry run mode."""
        from kiosk_show_replacement.validation import StorageIntegrityChecker

        with app.app_context():
            checker = StorageIntegrityChecker()
            result = checker.cleanup_orphaned_files(dry_run=True)

            assert result["dry_run"] is True
            assert "deleted_count" in result
            assert "error_count" in result
