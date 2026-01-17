"""
Tests for storage resilience utilities.

This module tests:
- Atomic file writes
- Disk space checking
- Checksum calculation and verification
- Safe file operations
"""

import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from kiosk_show_replacement.exceptions import StorageError
from kiosk_show_replacement.storage_resilience import (
    AtomicFileWriter,
    calculate_checksum,
    calculate_stream_checksum,
    check_disk_space,
    cleanup_directory,
    delete_file_safe,
    save_file_atomic,
    verify_checksum,
)


class TestCheckDiskSpace:
    """Tests for disk space checking."""

    def test_passes_with_sufficient_space(self, app):
        """Test check passes when sufficient space available."""
        with app.app_context():
            # Should not raise with small required size
            check_disk_space(Path(tempfile.gettempdir()), 1000)

    def test_raises_on_insufficient_space(self, app):
        """Test check raises when insufficient space."""
        with app.app_context():
            with pytest.raises(StorageError) as exc_info:
                # Request an impossibly large amount of space
                check_disk_space(
                    Path(tempfile.gettempdir()),
                    required_bytes=10**18,  # 1 exabyte
                )
            assert "Insufficient disk space" in str(exc_info.value)


class TestCalculateChecksum:
    """Tests for checksum calculation."""

    def test_calculates_sha256(self, app):
        """Test SHA256 checksum calculation."""
        with app.app_context():
            # Create a temp file with known content
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_path = Path(f.name)

            try:
                checksum = calculate_checksum(temp_path, "sha256")
                # Known SHA256 of "test content"
                expected = (
                    "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
                )
                assert checksum == expected
            finally:
                temp_path.unlink()

    def test_calculates_md5(self, app):
        """Test MD5 checksum calculation."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_path = Path(f.name)

            try:
                checksum = calculate_checksum(temp_path, "md5")
                # Known MD5 of "test content" (no newline)
                expected = "9473fdd0d880a43c21b7778d34872157"
                assert checksum == expected
            finally:
                temp_path.unlink()

    def test_raises_on_missing_file(self, app):
        """Test raises StorageError for missing file."""
        with app.app_context():
            with pytest.raises(StorageError):
                calculate_checksum(Path("/nonexistent/file.txt"))


class TestCalculateStreamChecksum:
    """Tests for stream checksum calculation."""

    def test_calculates_from_file_storage(self, app):
        """Test checksum calculation from FileStorage."""
        with app.app_context():
            content = b"test stream content"
            file = FileStorage(
                stream=BytesIO(content),
                filename="test.txt",
            )

            checksum = calculate_stream_checksum(file)

            # Verify checksum matches expected value
            import hashlib

            expected = hashlib.sha256(content).hexdigest()
            assert checksum == expected

    def test_resets_stream_position(self, app):
        """Test stream position is reset after checksum."""
        with app.app_context():
            content = b"test content"
            file = FileStorage(
                stream=BytesIO(content),
                filename="test.txt",
            )

            calculate_stream_checksum(file)

            # Stream should be at beginning
            assert file.read() == content


class TestVerifyChecksum:
    """Tests for checksum verification."""

    def test_passes_with_matching_checksum(self, app):
        """Test verification passes with correct checksum."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_path = Path(f.name)

            try:
                expected = (
                    "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
                )
                result = verify_checksum(temp_path, expected)
                assert result is True
            finally:
                temp_path.unlink()

    def test_raises_on_mismatch(self, app):
        """Test verification raises on checksum mismatch."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_path = Path(f.name)

            try:
                with pytest.raises(StorageError) as exc_info:
                    verify_checksum(temp_path, "wrong_checksum")
                assert "checksum mismatch" in str(exc_info.value)
            finally:
                temp_path.unlink()


class TestAtomicFileWriter:
    """Tests for AtomicFileWriter context manager."""

    def test_writes_file_atomically(self, app):
        """Test file is written atomically."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = Path(tmpdir) / "test.txt"

                with AtomicFileWriter(target_path, "w") as f:
                    f.write("test content")

                assert target_path.exists()
                assert target_path.read_text() == "test content"

    def test_cleans_up_on_error(self, app):
        """Test temp file is cleaned up on error."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = Path(tmpdir) / "test.txt"

                with pytest.raises(ValueError):
                    with AtomicFileWriter(target_path, "w") as f:
                        f.write("partial content")
                        raise ValueError("Simulated error")

                # Target should not exist
                assert not target_path.exists()
                # No temp files should remain
                assert len(list(Path(tmpdir).iterdir())) == 0

    def test_preserves_original_on_error(self, app):
        """Test original file is preserved if write fails."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = Path(tmpdir) / "test.txt"
                target_path.write_text("original content")

                with pytest.raises(ValueError):
                    with AtomicFileWriter(target_path, "w") as f:
                        f.write("new content")
                        raise ValueError("Simulated error")

                # Original content should be preserved
                assert target_path.read_text() == "original content"


class TestSaveFileAtomic:
    """Tests for atomic file saving."""

    def test_saves_file_with_checksum(self, app):
        """Test file is saved with checksum."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = Path(tmpdir) / "test.txt"
                content = b"test file content"

                file = FileStorage(
                    stream=BytesIO(content),
                    filename="test.txt",
                )

                result = save_file_atomic(file, target_path)

                assert target_path.exists()
                assert target_path.read_bytes() == content
                assert "checksum" in result
                assert result["size"] == len(content)

    def test_skips_checksum_when_disabled(self, app):
        """Test checksum can be disabled."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                target_path = Path(tmpdir) / "test.txt"

                file = FileStorage(
                    stream=BytesIO(b"content"),
                    filename="test.txt",
                )

                result = save_file_atomic(file, target_path, calculate_hash=False)

                assert result["checksum"] is None


class TestDeleteFileSafe:
    """Tests for safe file deletion."""

    def test_deletes_existing_file(self, app):
        """Test existing file is deleted."""
        with app.app_context():
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_path = Path(f.name)

            delete_file_safe(temp_path)
            assert not temp_path.exists()

    def test_handles_missing_file(self, app):
        """Test handles missing file gracefully."""
        with app.app_context():
            # Should not raise
            delete_file_safe(Path("/nonexistent/file.txt"))


class TestCleanupDirectory:
    """Tests for directory cleanup."""

    def test_removes_all_files(self, app):
        """Test all files in directory are removed."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                dir_path = Path(tmpdir) / "cleanup_test"
                dir_path.mkdir()
                (dir_path / "file1.txt").write_text("content1")
                (dir_path / "file2.txt").write_text("content2")

                count = cleanup_directory(dir_path)

                assert count == 2
                # Directory should be removed too
                assert not dir_path.exists()

    def test_handles_nested_directories(self, app):
        """Test handles nested directory structure."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                dir_path = Path(tmpdir) / "parent"
                nested_path = dir_path / "child"
                nested_path.mkdir(parents=True)
                (nested_path / "file.txt").write_text("content")

                count = cleanup_directory(dir_path)

                assert count == 1
                assert not nested_path.exists()

    def test_handles_empty_directory(self, app):
        """Test handles empty directory."""
        with app.app_context():
            with tempfile.TemporaryDirectory() as tmpdir:
                dir_path = Path(tmpdir) / "empty"
                dir_path.mkdir()

                count = cleanup_directory(dir_path)

                assert count == 0
                assert not dir_path.exists()
