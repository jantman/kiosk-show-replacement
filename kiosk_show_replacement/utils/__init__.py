"""
Utility functions for kiosk-show-replacement.

This module contains helper functions for file handling, URL validation,
and other common operations.
"""

import mimetypes
import os
from typing import Optional
from urllib.parse import urlparse

import requests
from PIL import Image


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid and accessible.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid and accessible
    """
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False

        # Try to make a HEAD request to check if URL is accessible
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False


def is_image_url(url: str) -> bool:
    """
    Check if a URL points to an image file.

    Args:
        url (str): URL to check

    Returns:
        bool: True if URL appears to be an image
    """
    try:
        # Check by file extension first
        parsed = urlparse(url)
        path = parsed.path.lower()
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}

        if any(path.endswith(ext) for ext in image_extensions):
            return True

        # Check by making a HEAD request and checking content-type
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get("content-type", "").lower()
        return content_type.startswith("image/")
    except Exception:
        return False


def validate_image_file(file_path: str) -> bool:
    """
    Validate that a file is a valid image.

    Args:
        file_path (str): Path to the image file

    Returns:
        bool: True if file is a valid image
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def get_file_mimetype(file_path: str) -> Optional[str]:
    """
    Get the MIME type of a file.

    Args:
        file_path (str): Path to the file

    Returns:
        str: MIME type of the file
    """
    mimetype, _ = mimetypes.guess_type(file_path)
    return mimetype or "application/octet-stream"


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        directory_path (str): Path to the directory
    """
    os.makedirs(directory_path, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing potentially dangerous characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename
    """
    # Remove potentially dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(". ")

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"

    return filename
