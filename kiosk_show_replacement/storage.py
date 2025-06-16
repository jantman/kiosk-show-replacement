"""
File storage management for kiosk-show-replacement.

This module handles file upload storage, directory management, and file operations
with proper security and organization.
"""

import hashlib
import logging
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages file storage operations for uploaded content.

    Handles file validation, secure storage, directory creation,
    and cleanup operations.
    """

    def __init__(self, upload_folder: Optional[str] = None):
        """
        Initialize the storage manager.

        Args:
            upload_folder: Base upload directory path. If None, uses Flask config.
        """
        self.upload_folder = upload_folder or current_app.config.get(
            "UPLOAD_FOLDER", "instance/uploads"
        )
        self.base_path = Path(self.upload_folder)

        # Ensure base upload directory exists
        self.ensure_directory(self.base_path)

    def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to ensure exists

        Raises:
            OSError: If directory cannot be created
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    def get_upload_path(
        self, content_type: str, user_id: int, slideshow_id: int
    ) -> Path:
        """
        Get the organized upload path for a file.

        Directory structure: uploads/{content_type}/{user_id}/{slideshow_id}/

        Args:
            content_type: Type of content ('images' or 'videos')
            user_id: ID of the user uploading the file
            slideshow_id: ID of the slideshow the file belongs to

        Returns:
            Path object for the upload directory
        """
        upload_path = self.base_path / content_type / str(user_id) / str(slideshow_id)
        self.ensure_directory(upload_path)
        return upload_path

    def validate_file(self, file: FileStorage, content_type: str) -> Tuple[bool, str]:
        """
        Validate an uploaded file for security and type constraints.

        Args:
            file: Uploaded file object
            content_type: Expected content type ('image' or 'video')

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "No file provided"

        filename = file.filename.lower()

        # Check file extension
        if "." not in filename:
            return False, "File must have an extension"

        extension = filename.rsplit(".", 1)[1]

        if content_type == "image":
            allowed_extensions = current_app.config.get(
                "ALLOWED_IMAGE_EXTENSIONS", {"jpg", "jpeg", "png", "gif"}
            )
            max_size = current_app.config.get("MAX_IMAGE_SIZE", 50 * 1024 * 1024)
        elif content_type == "video":
            allowed_extensions = current_app.config.get(
                "ALLOWED_VIDEO_EXTENSIONS", {"mp4", "webm", "avi"}
            )
            max_size = current_app.config.get("MAX_VIDEO_SIZE", 500 * 1024 * 1024)
        else:
            return False, f"Unsupported content type: {content_type}"

        if extension not in allowed_extensions:
            return False, f"File extension '{extension}' not allowed for {content_type}"

        # Check file size (seek to end to get size)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {size_mb:.1f}MB"

        # Basic MIME type validation
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            if content_type == "image" and not mime_type.startswith("image/"):
                return (
                    False,
                    f"File MIME type '{mime_type}' does not match expected image type",
                )
            elif content_type == "video" and not mime_type.startswith("video/"):
                return (
                    False,
                    f"File MIME type '{mime_type}' does not match expected video type",
                )

        return True, ""

    def generate_secure_filename(
        self, original_filename: str, user_id: int, slideshow_id: int
    ) -> str:
        """
        Generate a secure filename that prevents conflicts and security issues.

        Args:
            original_filename: Original uploaded filename
            user_id: ID of the user uploading
            slideshow_id: ID of the slideshow

        Returns:
            Secure filename with timestamp and hash
        """
        # Get file extension
        if "." in original_filename:
            name, ext = original_filename.rsplit(".", 1)
            ext = ext.lower()
        else:
            name, ext = original_filename, ""

        # Create a secure base name
        secure_name = secure_filename(name)[:50]  # Limit length

        # Add timestamp and hash for uniqueness
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        hash_input = f"{user_id}_{slideshow_id}_{original_filename}_{timestamp}"
        file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]

        # Construct final filename
        if ext:
            return f"{secure_name}_{timestamp}_{file_hash}.{ext}"
        else:
            return f"{secure_name}_{timestamp}_{file_hash}"

    def save_file(
        self, file: FileStorage, content_type: str, user_id: int, slideshow_id: int
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Save an uploaded file to the organized storage structure.

        Args:
            file: Uploaded file object
            content_type: Type of content ('image' or 'video')
            user_id: ID of the user uploading
            slideshow_id: ID of the slideshow

        Returns:
            Tuple of (success, message, file_info_dict)
        """
        try:
            # Validate the file
            is_valid, error_message = self.validate_file(file, content_type)
            if not is_valid:
                return False, error_message, None

            # Get upload path and create directories
            content_dir = "images" if content_type == "image" else "videos"
            upload_path = self.get_upload_path(content_dir, user_id, slideshow_id)

            # Generate secure filename
            secure_name = self.generate_secure_filename(
                file.filename, user_id, slideshow_id
            )
            file_path = upload_path / secure_name

            # Get file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            # Save the file
            file.save(str(file_path))

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))

            # Create file info
            file_info = {
                "filename": secure_name,
                "original_filename": file.filename,
                "file_path": str(file_path.relative_to(self.base_path)),
                "absolute_path": str(file_path),
                "content_type": content_type,
                "mime_type": mime_type,
                "file_size": file_size,
                "user_id": user_id,
                "slideshow_id": slideshow_id,
                "upload_date": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Successfully saved file: {secure_name} for user {user_id}, "
                f"slideshow {slideshow_id}"
            )
            return True, f"File '{file.filename}' uploaded successfully", file_info

        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {e}")
            return False, f"Failed to save file: {str(e)}", None

    def delete_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Delete a file from storage.

        Args:
            file_path: Relative path to the file from upload folder

        Returns:
            Tuple of (success, message)
        """
        try:
            full_path = self.base_path / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True, "File deleted successfully"
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False, "File not found"
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False, f"Failed to delete file: {str(e)}"

    def cleanup_slideshow_files(self, slideshow_id: int) -> Tuple[int, List[str]]:
        """
        Clean up all files associated with a slideshow.

        Args:
            slideshow_id: ID of the slideshow to clean up

        Returns:
            Tuple of (files_deleted_count, error_messages)
        """
        deleted_count = 0
        errors = []

        # Find all directories that might contain files for this slideshow
        for content_type in ["images", "videos"]:
            content_path = self.base_path / content_type
            if not content_path.exists():
                continue

            # Look through all user directories
            for user_dir in content_path.iterdir():
                if user_dir.is_dir():
                    slideshow_dir = user_dir / str(slideshow_id)
                    if slideshow_dir.exists():
                        try:
                            # Delete all files in the slideshow directory
                            for file_path in slideshow_dir.iterdir():
                                if file_path.is_file():
                                    file_path.unlink()
                                    deleted_count += 1

                            # Remove the directory if empty
                            slideshow_dir.rmdir()
                            logger.info(
                                f"Cleaned up slideshow {slideshow_id} files "
                                f"in {slideshow_dir}"
                            )

                        except Exception as e:
                            error_msg = f"Failed to cleanup {slideshow_dir}: {e}"
                            errors.append(error_msg)
                            logger.error(error_msg)

        return deleted_count, errors

    def get_file_url(self, file_path: str) -> str:
        """
        Generate a URL for accessing an uploaded file.

        Args:
            file_path: Relative path to the file from upload folder

        Returns:
            URL path for accessing the file
        """
        # URL-encode the file path for safety
        encoded_path = quote_plus(file_path.replace("\\", "/"))
        return f"/uploads/{encoded_path}"

    def get_directory_size(self, path: Optional[Path] = None) -> int:
        """
        Get the total size of files in a directory.

        Args:
            path: Directory path to measure. If None, measures entire upload folder.

        Returns:
            Total size in bytes
        """
        if path is None:
            path = self.base_path

        total_size = 0
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"Failed to calculate directory size for {path}: {e}")

        return total_size

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_size": 0,
            "image_size": 0,
            "video_size": 0,
            "total_files": 0,
            "image_files": 0,
            "video_files": 0,
            "users_with_files": set(),
            "slideshows_with_files": set(),
        }

        try:
            for content_type in ["images", "videos"]:
                content_path = self.base_path / content_type
                if not content_path.exists():
                    continue

                for user_dir in content_path.iterdir():
                    if user_dir.is_dir():
                        user_id = user_dir.name
                        stats["users_with_files"].add(user_id)

                        for slideshow_dir in user_dir.iterdir():
                            if slideshow_dir.is_dir():
                                slideshow_id = slideshow_dir.name
                                stats["slideshows_with_files"].add(slideshow_id)

                                for file_path in slideshow_dir.iterdir():
                                    if file_path.is_file():
                                        file_size = file_path.stat().st_size
                                        stats["total_size"] += file_size
                                        stats["total_files"] += 1

                                        if content_type == "images":
                                            stats["image_size"] += file_size
                                            stats["image_files"] += 1
                                        else:
                                            stats["video_size"] += file_size
                                            stats["video_files"] += 1

            # Convert sets to counts
            stats["users_with_files"] = len(stats["users_with_files"])
            stats["slideshows_with_files"] = len(stats["slideshows_with_files"])

        except Exception as e:
            logger.error(f"Failed to calculate storage stats: {e}")

        return stats


# Global storage manager instance
storage_manager = None


def get_storage_manager() -> StorageManager:
    """
    Get the global storage manager instance.

    Returns:
        StorageManager instance
    """
    global storage_manager
    if storage_manager is None:
        storage_manager = StorageManager()
    return storage_manager


def init_storage(app) -> None:
    """
    Initialize storage system with Flask app.

    Args:
        app: Flask application instance
    """
    global storage_manager
    upload_folder = app.config.get("UPLOAD_FOLDER", "instance/uploads")
    storage_manager = StorageManager(upload_folder)

    # Ensure base directories exist
    base_path = Path(upload_folder)
    for content_type in ["images", "videos"]:
        content_path = base_path / content_type
        storage_manager.ensure_directory(content_path)

    logger.info(f"Storage system initialized with upload folder: {upload_folder}")
