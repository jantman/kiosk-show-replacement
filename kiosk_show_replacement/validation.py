"""
Data integrity validation utilities for the Kiosk Show Replacement application.

This module provides:
- Request data validation
- Orphaned file detection
- Storage consistency checks
- Database integrity validation
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from flask import current_app

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


# Common validation patterns
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")


class DataValidator:
    """Validator for request data and model fields."""

    @staticmethod
    def validate_required(data: Dict[str, Any], fields: List[str]) -> None:
        """Validate that required fields are present and non-empty.

        Args:
            data: Dictionary of data to validate
            fields: List of required field names

        Raises:
            ValidationError: If any required field is missing or empty
        """
        missing = []
        empty = []

        for field in fields:
            if field not in data:
                missing.append(field)
            elif data[field] is None or (
                isinstance(data[field], str) and not data[field].strip()
            ):
                empty.append(field)

        if missing:
            raise ValidationError(
                message=f"Missing required fields: {', '.join(missing)}",
                details={"missing_fields": missing},
            )

        if empty:
            raise ValidationError(
                message=f"Empty required fields: {', '.join(empty)}",
                details={"empty_fields": empty},
            )

    @staticmethod
    def validate_string_length(
        value: str,
        field_name: str,
        min_length: int = 0,
        max_length: int = 255,
    ) -> None:
        """Validate string length constraints.

        Args:
            value: String value to validate
            field_name: Name of the field (for error messages)
            min_length: Minimum allowed length
            max_length: Maximum allowed length

        Raises:
            ValidationError: If length constraints are violated
        """
        if len(value) < min_length:
            raise ValidationError(
                message=f"{field_name} must be at least {min_length} characters",
                field=field_name,
                details={"min_length": min_length, "actual_length": len(value)},
            )

        if len(value) > max_length:
            raise ValidationError(
                message=f"{field_name} must be at most {max_length} characters",
                field=field_name,
                details={"max_length": max_length, "actual_length": len(value)},
            )

    @staticmethod
    def validate_integer_range(
        value: int,
        field_name: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> None:
        """Validate integer range constraints.

        Args:
            value: Integer value to validate
            field_name: Name of the field
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Raises:
            ValidationError: If range constraints are violated
        """
        if min_value is not None and value < min_value:
            raise ValidationError(
                message=f"{field_name} must be at least {min_value}",
                field=field_name,
                details={"min_value": min_value, "actual_value": value},
            )

        if max_value is not None and value > max_value:
            raise ValidationError(
                message=f"{field_name} must be at most {max_value}",
                field=field_name,
                details={"max_value": max_value, "actual_value": value},
            )

    @staticmethod
    def validate_email(value: str, field_name: str = "email") -> None:
        """Validate email format.

        Args:
            value: Email string to validate
            field_name: Name of the field

        Raises:
            ValidationError: If email format is invalid
        """
        if not EMAIL_PATTERN.match(value):
            raise ValidationError(
                message=f"Invalid email format for {field_name}",
                field=field_name,
            )

    @staticmethod
    def validate_username(value: str, field_name: str = "username") -> None:
        """Validate username format.

        Args:
            value: Username string to validate
            field_name: Name of the field

        Raises:
            ValidationError: If username format is invalid
        """
        if not USERNAME_PATTERN.match(value):
            raise ValidationError(
                message=f"{field_name} must be 3-50 characters, using only letters, "
                "numbers, underscores, and hyphens",
                field=field_name,
            )

    @staticmethod
    def validate_choice(
        value: Any,
        field_name: str,
        allowed_values: Set[Any],
    ) -> None:
        """Validate value is in allowed choices.

        Args:
            value: Value to validate
            field_name: Name of the field
            allowed_values: Set of allowed values

        Raises:
            ValidationError: If value is not in allowed choices
        """
        if value not in allowed_values:
            raise ValidationError(
                message=f"Invalid value for {field_name}. "
                f"Allowed values: {', '.join(str(v) for v in allowed_values)}",
                field=field_name,
                details={"allowed_values": list(allowed_values)},
            )


class StorageIntegrityChecker:
    """Checker for storage integrity and consistency."""

    def __init__(self, upload_folder: Optional[str] = None):
        """Initialize the storage integrity checker.

        Args:
            upload_folder: Base upload directory path
        """
        self.upload_folder = upload_folder or current_app.config.get(
            "UPLOAD_FOLDER", "instance/uploads"
        )
        self.base_path = Path(self.upload_folder)

    def find_orphaned_files(self) -> List[Dict[str, Any]]:
        """Find files in storage that aren't referenced by any slideshow item.

        Returns:
            List of dictionaries describing orphaned files
        """
        from .models import SlideshowItem

        orphaned = []

        # Get all file paths from database
        items = SlideshowItem.query.filter(
            SlideshowItem.content_type.in_(["image", "video"])
        ).all()

        db_files: Set[str] = set()
        for item in items:
            if item.content_url:
                # Normalize path
                db_files.add(item.content_url.replace("/uploads/", ""))

        # Scan storage directories
        for content_type in ["images", "videos"]:
            content_path = self.base_path / content_type
            if not content_path.exists():
                continue

            for file_path in content_path.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(self.base_path))
                    if relative_path not in db_files:
                        orphaned.append(
                            {
                                "path": str(file_path),
                                "relative_path": relative_path,
                                "size": file_path.stat().st_size,
                                "content_type": content_type,
                            }
                        )

        logger.info(f"Found {len(orphaned)} orphaned files")
        return orphaned

    def find_missing_files(self) -> List[Dict[str, Any]]:
        """Find slideshow items that reference non-existent files.

        Returns:
            List of dictionaries describing items with missing files
        """
        from .models import SlideshowItem

        missing = []

        items = SlideshowItem.query.filter(
            SlideshowItem.content_type.in_(["image", "video"]),
            SlideshowItem.is_active == True,  # noqa: E712
        ).all()

        for item in items:
            if item.content_url:
                # Convert URL to file path
                relative_path = item.content_url.replace("/uploads/", "")
                file_path = self.base_path / relative_path

                if not file_path.exists():
                    missing.append(
                        {
                            "item_id": item.id,
                            "slideshow_id": item.slideshow_id,
                            "content_url": item.content_url,
                            "expected_path": str(file_path),
                        }
                    )

        logger.info(f"Found {len(missing)} items with missing files")
        return missing

    def check_storage_consistency(self) -> Dict[str, Any]:
        """Perform comprehensive storage consistency check.

        Returns:
            Dictionary with consistency check results
        """
        orphaned_files = self.find_orphaned_files()
        missing_files = self.find_missing_files()

        # Calculate storage statistics
        total_size = 0
        total_files = 0

        for content_type in ["images", "videos"]:
            content_path = self.base_path / content_type
            if content_path.exists():
                for file_path in content_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        total_files += 1

        orphaned_size = sum(f["size"] for f in orphaned_files)

        return {
            "is_consistent": len(orphaned_files) == 0 and len(missing_files) == 0,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "orphaned_files": {
                "count": len(orphaned_files),
                "total_size_bytes": orphaned_size,
                "files": orphaned_files[:10],  # Limit to first 10
            },
            "missing_files": {
                "count": len(missing_files),
                "items": missing_files[:10],  # Limit to first 10
            },
        }

    def cleanup_orphaned_files(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up orphaned files from storage.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            Dictionary with cleanup results
        """
        orphaned = self.find_orphaned_files()
        deleted = []
        errors = []

        for file_info in orphaned:
            file_path = Path(file_info["path"])
            if dry_run:
                deleted.append(file_info)
            else:
                try:
                    file_path.unlink()
                    deleted.append(file_info)
                    logger.info(f"Deleted orphaned file: {file_path}")
                except Exception as e:
                    errors.append(
                        {
                            "path": str(file_path),
                            "error": str(e),
                        }
                    )
                    logger.error(f"Failed to delete orphaned file {file_path}: {e}")

        return {
            "dry_run": dry_run,
            "deleted_count": len(deleted),
            "deleted_size_bytes": sum(f["size"] for f in deleted),
            "error_count": len(errors),
            "errors": errors,
        }


def validate_slideshow_data(data: Dict[str, Any]) -> None:
    """Validate slideshow creation/update data.

    Args:
        data: Slideshow data to validate

    Raises:
        ValidationError: If validation fails
    """
    validator = DataValidator()

    if "name" in data:
        name = data["name"]
        if isinstance(name, str):
            name = name.strip()
            validator.validate_string_length(name, "name", min_length=1, max_length=100)
        else:
            raise ValidationError("Slideshow name must be a string", field="name")

    if "description" in data and data["description"]:
        validator.validate_string_length(
            data["description"], "description", max_length=1000
        )

    if "default_item_duration" in data:
        duration = data["default_item_duration"]
        if isinstance(duration, int):
            validator.validate_integer_range(
                duration, "default_item_duration", min_value=1, max_value=3600
            )
        else:
            raise ValidationError(
                "default_item_duration must be an integer",
                field="default_item_duration",
            )


def validate_display_data(data: Dict[str, Any]) -> None:
    """Validate display creation/update data.

    Args:
        data: Display data to validate

    Raises:
        ValidationError: If validation fails
    """
    validator = DataValidator()

    if "name" in data:
        name = data["name"]
        if isinstance(name, str):
            name = name.strip()
            validator.validate_string_length(name, "name", min_length=1, max_length=100)
        else:
            raise ValidationError("Display name must be a string", field="name")

    if "description" in data and data["description"]:
        validator.validate_string_length(
            data["description"], "description", max_length=1000
        )
