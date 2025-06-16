"""
Test file upload and storage functionality.

Tests for file upload API endpoints, storage management, and file serving.
"""

import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import FileStorage

from kiosk_show_replacement.storage import (
    StorageManager,
    get_storage_manager,
    init_storage,
)


class TestStorageManager:
    """Test the StorageManager class functionality."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage_manager(self, temp_storage_dir):
        """Create a StorageManager instance with temporary directory."""
        return StorageManager(temp_storage_dir)

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for testing."""
        # Create a minimal PNG file (1x1 pixel)
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
            b"\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        file_obj = BytesIO(png_data)
        return FileStorage(
            file_obj, filename="test_image.png", content_type="image/png"
        )

    @pytest.fixture
    def sample_video_file(self):
        """Create a sample video file for testing."""
        # Create a minimal MP4 file header
        mp4_data = (
            b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x20mp41mp42isom"
            b"\x00\x00\x00\x08free\x00\x00\x00\x28mdat"
        )
        file_obj = BytesIO(mp4_data)
        return FileStorage(
            file_obj, filename="test_video.mp4", content_type="video/mp4"
        )

    def test_ensure_directory(self, storage_manager, temp_storage_dir):
        """Test directory creation."""
        test_dir = Path(temp_storage_dir) / "test" / "nested" / "directory"
        storage_manager.ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_get_upload_path(self, storage_manager, temp_storage_dir):
        """Test upload path generation."""
        path = storage_manager.get_upload_path("images", 1, 2)
        expected_path = Path(temp_storage_dir) / "images" / "1" / "2"

        assert path == expected_path
        assert path.exists()
        assert path.is_dir()

    def test_validate_file_image_success(self, storage_manager, sample_image_file, app):
        """Test successful image file validation."""
        with app.app_context():
            is_valid, error = storage_manager.validate_file(sample_image_file, "image")
            assert is_valid
            assert error == ""

    def test_validate_file_video_success(self, storage_manager, sample_video_file, app):
        """Test successful video file validation."""
        with app.app_context():
            is_valid, error = storage_manager.validate_file(sample_video_file, "video")
            assert is_valid
            assert error == ""

    def test_validate_file_no_file(self, storage_manager, app):
        """Test validation with no file."""
        with app.app_context():
            is_valid, error = storage_manager.validate_file(None, "image")
            assert not is_valid
            assert "No file provided" in error

    def test_validate_file_empty_filename(self, storage_manager, app):
        """Test validation with empty filename."""
        with app.app_context():
            file_obj = FileStorage(BytesIO(b"test"), filename="")
            is_valid, error = storage_manager.validate_file(file_obj, "image")
            assert not is_valid
            assert "No file provided" in error

    def test_validate_file_no_extension(self, storage_manager, app):
        """Test validation with no file extension."""
        with app.app_context():
            file_obj = FileStorage(BytesIO(b"test"), filename="noextension")
            is_valid, error = storage_manager.validate_file(file_obj, "image")
            assert not is_valid
            assert "must have an extension" in error

    def test_validate_file_invalid_extension(self, storage_manager, app):
        """Test validation with invalid extension."""
        with app.app_context():
            file_obj = FileStorage(BytesIO(b"test"), filename="test.exe")
            is_valid, error = storage_manager.validate_file(file_obj, "image")
            assert not is_valid
            assert "extension 'exe' not allowed" in error

    def test_validate_file_unsupported_type(
        self, storage_manager, sample_image_file, app
    ):
        """Test validation with unsupported content type."""
        with app.app_context():
            is_valid, error = storage_manager.validate_file(
                sample_image_file, "document"
            )
            assert not is_valid
            assert "Unsupported content type" in error

    def test_generate_secure_filename(self, storage_manager):
        """Test secure filename generation."""
        filename = storage_manager.generate_secure_filename("test file.jpg", 1, 2)

        assert filename.endswith(".jpg")
        assert "test_file" in filename
        assert len(filename.split("_")) >= 3  # name, timestamp, hash

    def test_save_file_success(self, storage_manager, sample_image_file, app):
        """Test successful file saving."""
        with app.app_context():
            success, message, file_info = storage_manager.save_file(
                sample_image_file, "image", 1, 2
            )

            assert success
            assert "uploaded successfully" in message
            assert file_info is not None
            assert file_info["content_type"] == "image"
            assert file_info["original_filename"] == "test_image.png"
            assert file_info["user_id"] == 1
            assert file_info["slideshow_id"] == 2

    def test_save_file_validation_failure(self, storage_manager, app):
        """Test file saving with validation failure."""
        with app.app_context():
            invalid_file = FileStorage(BytesIO(b"test"), filename="test.exe")
            success, message, file_info = storage_manager.save_file(
                invalid_file, "image", 1, 2
            )

            assert not success
            assert "not allowed" in message
            assert file_info is None

    def test_delete_file_success(self, storage_manager, sample_image_file, app):
        """Test successful file deletion."""
        with app.app_context():
            # First save a file
            success, _, file_info = storage_manager.save_file(
                sample_image_file, "image", 1, 2
            )
            assert success

            # Then delete it
            file_path = file_info["file_path"]
            success, message = storage_manager.delete_file(file_path)

            assert success
            assert "deleted successfully" in message

    def test_delete_file_not_found(self, storage_manager):
        """Test deleting non-existent file."""
        success, message = storage_manager.delete_file("non/existent/file.jpg")

        assert not success
        assert "not found" in message

    def test_cleanup_slideshow_files(self, storage_manager, sample_image_file, app):
        """Test cleanup of slideshow files."""
        with app.app_context():
            # Save some files for slideshow
            storage_manager.save_file(sample_image_file, "image", 1, 2)
            sample_image_file.seek(0)  # Reset file pointer
            storage_manager.save_file(sample_image_file, "image", 3, 2)

            # Cleanup slideshow 2
            deleted_count, errors = storage_manager.cleanup_slideshow_files(2)

            assert deleted_count >= 2
            assert len(errors) == 0

    def test_get_file_url(self, storage_manager):
        """Test file URL generation."""
        url = storage_manager.get_file_url("images/1/2/test.jpg")
        assert url == "/uploads/images%2F1%2F2%2Ftest.jpg"

    def test_get_storage_stats(self, storage_manager, sample_image_file, app):
        """Test storage statistics."""
        with app.app_context():
            # Save some files
            storage_manager.save_file(sample_image_file, "image", 1, 2)
            sample_image_file.seek(0)
            storage_manager.save_file(sample_image_file, "image", 1, 3)

            stats = storage_manager.get_storage_stats()

            assert stats["total_files"] >= 2
            assert stats["image_files"] >= 2
            assert stats["video_files"] == 0
            assert stats["users_with_files"] >= 1
            assert stats["slideshows_with_files"] >= 2


class TestFileUploadAPI:
    """Test file upload API endpoints."""

    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data for upload."""
        # Minimal PNG data
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
            b"\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    @pytest.fixture
    def sample_video_data(self):
        """Create sample video data for upload."""
        # Minimal MP4 header
        return (
            b"\x00\x00\x00\x20ftypmp42\x00\x00\x00\x20mp41mp42isom"
            b"\x00\x00\x00\x08free\x00\x00\x00\x28mdat"
        )

    def test_upload_image_success(
        self, client, authenticated_user, sample_slideshow, sample_image_data
    ):
        """Test successful image upload."""
        data = {
            "file": (BytesIO(sample_image_data), "test.png"),
            "slideshow_id": str(sample_slideshow.id),
        }

        response = client.post(
            "/api/v1/uploads/image", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "data" in json_data
        assert json_data["data"]["content_type"] == "image"
        assert json_data["data"]["original_filename"] == "test.png"

    def test_upload_image_no_auth(self, client, sample_image_data):
        """Test image upload without authentication."""
        data = {"file": (BytesIO(sample_image_data), "test.png"), "slideshow_id": "1"}

        response = client.post(
            "/api/v1/uploads/image", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["success"] is False

    def test_upload_image_no_file(self, client, authenticated_user, sample_slideshow):
        """Test image upload without file."""
        data = {"slideshow_id": str(sample_slideshow.id)}

        response = client.post(
            "/api/v1/uploads/image", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "No file provided" in json_data["error"]

    def test_upload_image_no_slideshow_id(
        self, client, authenticated_user, sample_image_data
    ):
        """Test image upload without slideshow_id."""
        data = {"file": (BytesIO(sample_image_data), "test.png")}

        response = client.post(
            "/api/v1/uploads/image", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "slideshow_id is required" in json_data["error"]

    def test_upload_image_invalid_slideshow_id(
        self, client, authenticated_user, sample_image_data
    ):
        """Test image upload with invalid slideshow_id."""
        data = {
            "file": (BytesIO(sample_image_data), "test.png"),
            "slideshow_id": "invalid",
        }

        response = client.post(
            "/api/v1/uploads/image", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "Invalid slideshow_id" in json_data["error"]

    def test_upload_image_nonexistent_slideshow(
        self, client, authenticated_user, sample_image_data
    ):
        """Test image upload with non-existent slideshow."""
        data = {
            "file": (BytesIO(sample_image_data), "test.png"),
            "slideshow_id": "99999",
        }

        response = client.post(
            "/api/v1/uploads/image", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "Slideshow not found" in json_data["error"]

    def test_upload_video_success(
        self, client, authenticated_user, sample_slideshow, sample_video_data
    ):
        """Test successful video upload."""
        data = {
            "file": (BytesIO(sample_video_data), "test.mp4"),
            "slideshow_id": str(sample_slideshow.id),
        }

        response = client.post(
            "/api/v1/uploads/video", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "data" in json_data
        assert json_data["data"]["content_type"] == "video"
        assert json_data["data"]["original_filename"] == "test.mp4"

    def test_upload_video_invalid_extension(
        self, client, authenticated_user, sample_slideshow
    ):
        """Test video upload with invalid extension."""
        data = {
            "file": (BytesIO(b"fake video data"), "test.txt"),
            "slideshow_id": str(sample_slideshow.id),
        }

        response = client.post(
            "/api/v1/uploads/video", data=data, content_type="multipart/form-data"
        )

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "not allowed" in json_data["error"]

    def test_get_upload_stats(self, client, authenticated_user):
        """Test upload statistics endpoint."""
        response = client.get("/api/v1/uploads/stats")

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "data" in json_data

        # Check that all expected fields are present
        data = json_data["data"]
        expected_fields = [
            "total_size",
            "total_size_formatted",
            "image_size",
            "image_size_formatted",
            "video_size",
            "video_size_formatted",
            "total_files",
            "image_files",
            "video_files",
            "users_with_files",
            "slideshows_with_files",
        ]
        for field in expected_fields:
            assert field in data

    def test_get_upload_stats_no_auth(self, client):
        """Test upload statistics endpoint without authentication."""
        response = client.get("/api/v1/uploads/stats")

        assert response.status_code == 401
        json_data = response.get_json()
        assert json_data["success"] is False

    def test_file_info_endpoint_not_implemented(self, client, authenticated_user):
        """Test file info endpoint (placeholder)."""
        response = client.get("/api/v1/uploads/1")

        assert response.status_code == 501
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "not yet implemented" in json_data["error"]

    def test_delete_file_endpoint_not_implemented(self, client, authenticated_user):
        """Test file deletion endpoint (placeholder)."""
        response = client.delete("/api/v1/uploads/1")

        assert response.status_code == 501
        json_data = response.get_json()
        assert json_data["success"] is False
        assert "not yet implemented" in json_data["error"]


class TestFileServing:
    """Test file serving functionality."""

    def test_file_serving_route_exists(self, app):
        """Test that file serving route is registered."""
        with app.test_request_context():
            # The route should exist
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            assert "/uploads/<path:filename>" in rules

    @patch("kiosk_show_replacement.app.send_from_directory")
    def test_file_serving_success(self, mock_send, client):
        """Test successful file serving."""
        mock_send.return_value = MagicMock()

        client.get("/uploads/images/1/2/test.jpg")

        # The route should call send_from_directory
        mock_send.assert_called_once()

    def test_file_serving_not_found(self, client):
        """Test file serving with non-existent file."""
        response = client.get("/uploads/nonexistent/file.jpg")

        assert response.status_code == 404


class TestStorageInitialization:
    """Test storage system initialization."""

    def test_init_storage(self, app):
        """Test storage initialization."""
        with app.app_context():
            # Storage should initialize without error
            init_storage(app)

            # Should be able to get storage manager
            manager = get_storage_manager()
            assert manager is not None
            assert isinstance(manager, StorageManager)

    def test_storage_directories_created(self, app):
        """Test that required directories are created during initialization."""
        with app.app_context():
            init_storage(app)

            upload_folder = Path(app.config["UPLOAD_FOLDER"])
            assert (upload_folder / "images").exists()
            assert (upload_folder / "videos").exists()
