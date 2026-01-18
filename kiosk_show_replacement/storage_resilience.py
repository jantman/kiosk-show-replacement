"""
Storage resilience utilities for the Kiosk Show Replacement application.

This module provides enhanced storage operations with:
- Atomic file writes (write to temp, then rename)
- Disk space checking before uploads
- File integrity validation (checksum)
- Exception-based error handling
- Cleanup on partial failures
"""

import hashlib
import logging
import os
import shutil
import tempfile
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Callable, Dict, Optional, TypeVar

from flask import current_app
from werkzeug.datastructures import FileStorage

from .exceptions import StorageError
from .metrics import record_storage_error

logger = logging.getLogger(__name__)

T = TypeVar("T")


def check_disk_space(
    path: Path,
    required_bytes: int,
    min_free_bytes: Optional[int] = None,
) -> None:
    """Check if sufficient disk space is available.

    Args:
        path: Path to check disk space for
        required_bytes: Number of bytes needed for the operation
        min_free_bytes: Minimum free bytes to maintain after operation

    Raises:
        StorageError: If insufficient disk space is available
    """
    if min_free_bytes is None:
        min_free_bytes = current_app.config.get(
            "STORAGE_MIN_FREE_BYTES", 100 * 1024 * 1024  # 100MB default
        )

    try:
        disk_usage = shutil.disk_usage(path)
        available = disk_usage.free - required_bytes

        if available < min_free_bytes:
            record_storage_error()
            raise StorageError(
                message="Insufficient disk space",
                operation="disk_check",
                details={
                    "required_bytes": required_bytes,
                    "available_bytes": disk_usage.free,
                    "min_free_bytes": min_free_bytes,
                },
            )
    except OSError as e:
        record_storage_error()
        raise StorageError(
            message=f"Failed to check disk space: {e}",
            operation="disk_check",
        )


def calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate file checksum.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (sha256, md5, etc.)

    Returns:
        Hexadecimal checksum string

    Raises:
        StorageError: If checksum calculation fails
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        record_storage_error()
        raise StorageError(
            message=f"Failed to calculate checksum: {e}",
            operation="checksum",
            file_path=str(file_path),
        )


def calculate_stream_checksum(file: FileStorage, algorithm: str = "sha256") -> str:
    """Calculate checksum for a file stream.

    Args:
        file: FileStorage object
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal checksum string
    """
    hash_obj = hashlib.new(algorithm)
    file.seek(0)
    for chunk in iter(lambda: file.read(8192), b""):
        hash_obj.update(chunk)
    file.seek(0)  # Reset for subsequent reads
    return hash_obj.hexdigest()


def verify_checksum(
    file_path: Path, expected_checksum: str, algorithm: str = "sha256"
) -> bool:
    """Verify file integrity using checksum.

    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm used

    Returns:
        True if checksum matches

    Raises:
        StorageError: If verification fails or checksum doesn't match
    """
    actual_checksum = calculate_checksum(file_path, algorithm)
    if actual_checksum != expected_checksum:
        record_storage_error()
        raise StorageError(
            message="File integrity check failed: checksum mismatch",
            operation="verify_checksum",
            file_path=str(file_path),
            details={
                "expected": expected_checksum,
                "actual": actual_checksum,
            },
        )
    return True


class AtomicFileWriter:
    """Context manager for atomic file writes.

    Writes to a temporary file first, then atomically renames to the target
    path. If an error occurs, the temporary file is cleaned up and the
    original file (if any) remains unchanged.
    """

    def __init__(self, target_path: Path, mode: str = "wb"):
        """Initialize atomic file writer.

        Args:
            target_path: Final destination path for the file
            mode: File open mode (default: binary write)
        """
        self.target_path = target_path
        self.mode = mode
        self.temp_path: Optional[Path] = None
        self.file: Optional[IO[Any]] = None

    def __enter__(self) -> IO[Any]:
        """Create temporary file and return file handle."""
        # Create temp file in same directory to ensure same filesystem
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(
            dir=self.target_path.parent,
            prefix=".tmp_",
            suffix=self.target_path.suffix,
        )
        self.temp_path = Path(temp_path)

        # Open the temp file
        os.close(fd)  # Close the file descriptor
        self.file = open(self.temp_path, self.mode)
        return self.file

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Finalize write or cleanup on error."""
        if self.file:
            self.file.close()

        if exc_type is not None:
            # Error occurred - cleanup temp file
            if self.temp_path and self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {self.temp_path}: {e}")
            return  # Re-raise the exception

        # Success - atomically rename temp to target
        try:
            if self.temp_path:
                self.temp_path.rename(self.target_path)
        except Exception as e:
            # Cleanup temp file on rename failure
            if self.temp_path and self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except Exception:
                    pass
            record_storage_error()
            raise StorageError(
                message=f"Failed to finalize file write: {e}",
                operation="atomic_write",
                file_path=str(self.target_path),
            )


def save_file_atomic(
    file: FileStorage,
    target_path: Path,
    calculate_hash: bool = True,
) -> Dict[str, Any]:
    """Save a file atomically with integrity checking.

    Args:
        file: FileStorage object to save
        target_path: Destination path for the file
        calculate_hash: Whether to calculate and return checksum

    Returns:
        Dictionary with file info including checksum

    Raises:
        StorageError: If save fails
    """
    # Get file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    # Check disk space
    check_disk_space(target_path.parent, file_size)

    # Calculate checksum before save (if requested)
    checksum = None
    if calculate_hash:
        checksum = calculate_stream_checksum(file)

    # Write file atomically
    try:
        with AtomicFileWriter(target_path) as f:
            # Copy in chunks
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    except StorageError:
        raise
    except Exception as e:
        record_storage_error()
        raise StorageError(
            message=f"Failed to save file: {e}",
            operation="save",
            file_path=str(target_path),
        )

    # Verify file was written correctly
    if checksum and calculate_hash:
        verify_checksum(target_path, checksum)

    return {
        "path": str(target_path),
        "size": file_size,
        "checksum": checksum,
        "checksum_algorithm": "sha256" if checksum else None,
    }


def delete_file_safe(file_path: Path) -> None:
    """Safely delete a file with proper error handling.

    Args:
        file_path: Path to the file to delete

    Raises:
        StorageError: If deletion fails
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        else:
            logger.debug(f"File not found for deletion: {file_path}")
    except Exception as e:
        record_storage_error()
        raise StorageError(
            message=f"Failed to delete file: {e}",
            operation="delete",
            file_path=str(file_path),
        )


def cleanup_directory(
    directory: Path,
    remove_empty_parents: bool = True,
    stop_at: Optional[Path] = None,
) -> int:
    """Clean up a directory and optionally remove empty parent directories.

    Args:
        directory: Directory to clean up
        remove_empty_parents: Whether to remove empty parent directories
        stop_at: Stop removing parents at this path

    Returns:
        Number of files deleted

    Raises:
        StorageError: If cleanup fails
    """
    deleted_count = 0

    try:
        if not directory.exists():
            return 0

        # Delete all files in directory
        for item in directory.iterdir():
            if item.is_file():
                item.unlink()
                deleted_count += 1
            elif item.is_dir():
                deleted_count += cleanup_directory(item, remove_empty_parents=False)

        # Try to remove the directory itself if empty
        try:
            directory.rmdir()
        except OSError:
            pass  # Directory not empty or permission denied

        # Remove empty parent directories
        if remove_empty_parents and stop_at:
            parent = directory.parent
            while parent != stop_at and parent.exists():
                try:
                    parent.rmdir()
                    parent = parent.parent
                except OSError:
                    break  # Directory not empty

        return deleted_count

    except Exception as e:
        record_storage_error()
        raise StorageError(
            message=f"Failed to cleanup directory: {e}",
            operation="cleanup",
            file_path=str(directory),
        )


def with_storage_cleanup(
    cleanup_paths: list[Path],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that cleans up files on exception.

    Args:
        cleanup_paths: List of paths to clean up on error

    Returns:
        Decorator function
    """
    import functools

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                # Clean up files on error
                for path in cleanup_paths:
                    try:
                        if path.exists():
                            if path.is_file():
                                path.unlink()
                            elif path.is_dir():
                                shutil.rmtree(path)
                            logger.info(f"Cleaned up {path} after error")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {path}: {e}")
                raise

        return wrapper

    return decorator
