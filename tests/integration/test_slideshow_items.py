"""
Integration tests for slideshow item management in the admin interface.

Tests adding, editing, deleting, and reordering slideshow items:
- Add image item via file upload
- Add image item via URL
- Add video item via file upload
- Add video item via URL
- Add URL item (webpage)
- Add text item
- Edit existing item
- Delete item with confirmation
- Reorder items (move up/down)
- Icon visibility (Bootstrap Icons CSS import)
- Auto-title from filename/URL

These tests verify that data is actually persisted by checking via API calls,
not just verifying UI display.

Run with: nox -s test-integration
"""

import os
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

# Path to test assets
ASSETS_DIR = Path(__file__).parent.parent / "assets"


def get_item_by_title(
    http_client, auth_headers, slideshow_id: int, title: str
) -> dict | None:
    """Helper to fetch a slideshow item by title via API."""
    response = http_client.get(
        f"/api/v1/slideshows/{slideshow_id}/items",
        headers=auth_headers,
    )
    assert response.status_code == 200, f"Failed to fetch items: {response.text}"
    data = response.json()
    items = data.get("data", data)
    for item in items:
        if item.get("title") == title:
            return item
    return None


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_BROWSER_TESTS", "false").lower() == "true",
    reason="Browser tests skipped",
)
class TestSlideshowItems:
    """Test slideshow item management through the admin interface."""

    def test_add_image_item_via_file_upload(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding an image item by uploading a file.

        Tests the image file upload flow through the admin interface.
        Verifies via API that content_file_path is persisted and file size matches.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Get the image path for upload
        image_path = ASSETS_DIR / "smallPhoto.jpg"
        assert image_path.exists(), f"Test asset not found: {image_path}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        add_button = page.locator("button:has-text('Add Item')")
        expect(add_button).to_be_visible(timeout=10000)
        add_button.click()

        # Wait for modal to appear
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form
        page.locator("#title").fill("Test Image Upload")
        page.locator("#content_type").select_option("image")

        # Upload the image file
        page.locator("#file_image").set_input_files(str(image_path))

        # Wait for upload to complete (success badge with "File uploaded:" appears)
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=10000)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Image Upload")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Image Upload') .badge:has-text('image')")
        ).to_be_visible()

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Test Image Upload"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "image"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_file_path"), f"content_file_path not persisted: {item}"

    def test_add_image_item_via_url(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding an image item by specifying a URL.

        Verifies via API that content_url is persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_url = "https://example.com/image.jpg"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form with URL instead of file upload
        page.locator("#title").fill("Test Image URL")
        page.locator("#content_type").select_option("image")
        page.locator("#url_alternative").fill(test_url)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Image URL")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Image URL') .badge:has-text('image')")
        ).to_be_visible()

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Test Image URL"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "image"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_url") == test_url, (
            f"content_url not persisted correctly: expected '{test_url}', "
            f"got '{item.get('content_url')}'"
        )

    def test_add_video_item_via_file_upload(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding a video item by uploading a file.

        Tests the video file upload flow through the admin interface.
        Verifies via API that content_file_path is persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Get the video path for upload
        video_path = ASSETS_DIR / "crash_into_pole.mpeg"
        assert video_path.exists(), f"Test asset not found: {video_path}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form
        page.locator("#title").fill("Test Video Upload")
        page.locator("#content_type").select_option("video")

        # Upload the video file
        page.locator("#file_video").set_input_files(str(video_path))

        # Wait for upload to complete (success badge with "File uploaded:" appears)
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=30000)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Video Upload")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Video Upload') .badge:has-text('video')")
        ).to_be_visible()

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Test Video Upload"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "video"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_file_path"), f"content_file_path not persisted: {item}"

    def test_video_upload_auto_detects_duration(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that video upload automatically detects and sets duration.

        When a video file is uploaded, the backend should use ffprobe to detect
        the video duration. This duration should be:
        1. Returned in the upload response
        2. Auto-populated in the duration field (which becomes read-only)
        3. Persisted as display_duration when the item is saved

        Uses test_video_5s.mp4 which is a 5-second test video.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Get the test video with known duration (5 seconds)
        video_path = ASSETS_DIR / "test_video_5s.mp4"
        assert video_path.exists(), f"Test asset not found: {video_path}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form
        page.locator("#title").fill("Video With Auto Duration")
        page.locator("#content_type").select_option("video")

        # Upload the video file
        page.locator("#file_video").set_input_files(str(video_path))

        # Wait for upload to complete
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=30000)

        # Verify the duration field is auto-populated (should show ~5 seconds)
        duration_field = page.locator("#duration")
        # The field should have a value now (auto-detected duration)
        expect(duration_field).to_have_value("5", timeout=5000)

        # Verify the duration field is read-only for auto-detected video duration
        expect(duration_field).to_be_disabled()

        # Verify the label indicates auto-detection
        expect(
            page.locator("label:has-text('Video Duration (auto-detected)')")
        ).to_be_visible()

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Video With Auto Duration")).to_be_visible(
            timeout=5000
        )

        # CRITICAL: Verify via API that display_duration was automatically set
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Video With Auto Duration"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "video"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_file_path"), f"content_file_path not persisted: {item}"

        # The display_duration should be set to 5 seconds (auto-detected from video)
        assert item.get("display_duration") == 5, (
            f"display_duration should be auto-set to 5 seconds from video, "
            f"got: {item.get('display_duration')}"
        )

    def test_add_video_item_via_url(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding a video item by specifying a URL.

        Verifies via API that content_url is persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_url = "https://example.com/video.mp4"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form with URL instead of file upload
        page.locator("#title").fill("Test Video URL")
        page.locator("#content_type").select_option("video")
        page.locator("#url_alternative").fill(test_url)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Video URL")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Video URL') .badge:has-text('video')")
        ).to_be_visible()

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Test Video URL"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "video"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_url") == test_url, (
            f"content_url not persisted correctly: expected '{test_url}', "
            f"got '{item.get('content_url')}'"
        )

    def test_add_url_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding a URL (webpage) item.

        Verifies via API that content_url and display_duration are persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_url = "https://example.com"
        test_duration = 30

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form for URL type
        page.locator("#title").fill("Test Web Page")
        page.locator("#content_type").select_option("url")
        page.locator("#url").fill(test_url)

        # Set a custom duration
        page.locator("#duration").fill(str(test_duration))

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Web Page")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Web Page') .badge:has-text('url')")
        ).to_be_visible()

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Test Web Page"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "url"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_url") == test_url, (
            f"content_url not persisted correctly: expected '{test_url}', "
            f"got '{item.get('content_url')}'"
        )
        assert item.get("display_duration") == test_duration, (
            f"display_duration not persisted correctly: expected {test_duration}, "
            f"got {item.get('display_duration')}"
        )

    def test_add_text_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding a text item.

        Verifies via API that content_text is persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_text = "This is a test message for the slideshow."

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form for text type
        page.locator("#title").fill("Test Text Slide")
        page.locator("#content_type").select_option("text")
        page.locator("#text_content").fill(test_text)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Text Slide")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Text Slide') .badge:has-text('text')")
        ).to_be_visible()

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Test Text Slide"
        )
        assert item is not None, "Item not found via API after creation"
        assert (
            item.get("content_type") == "text"
        ), f"content_type not persisted correctly: {item.get('content_type')}"
        assert item.get("content_text") == test_text, (
            f"content_text not persisted correctly: expected '{test_text}', "
            f"got '{item.get('content_text')}'"
        )

    def test_add_text_item_with_duration_override(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding a text item with a custom duration override.

        Verifies via API that display_duration is persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_text = "Text with custom duration."
        test_duration = 45

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form for text type with duration
        page.locator("#title").fill("Text With Duration")
        page.locator("#content_type").select_option("text")
        page.locator("#text_content").fill(test_text)
        page.locator("#duration").fill(str(test_duration))

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Text With Duration")).to_be_visible(timeout=5000)

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Text With Duration"
        )
        assert item is not None, "Item not found via API after creation"
        assert item.get("content_text") == test_text, (
            f"content_text not persisted correctly: expected '{test_text}', "
            f"got '{item.get('content_text')}'"
        )
        assert item.get("display_duration") == test_duration, (
            f"display_duration not persisted correctly: expected {test_duration}, "
            f"got {item.get('display_duration')}"
        )

    def test_edit_existing_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test editing an existing slideshow item.

        Verifies via API that all field changes are persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        original_text = "Original text content"
        updated_text = "Updated text content"

        # Create an item via API first (using correct backend field names)
        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Item To Edit",
                "content_type": "text",
                "content_text": original_text,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]

        # Verify item was created with correct content
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Item To Edit"
        )
        assert item is not None, "Created item not found via API"
        assert (
            item.get("content_text") == original_text
        ), f"Original content_text not set correctly: {item.get('content_text')}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Find the item row and click Edit
        row = page.locator("tr:has-text('Item To Edit')")
        expect(row).to_be_visible(timeout=10000)
        row.locator("button[title='Edit']").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Verify form is pre-filled with existing values
        expect(page.locator("#title")).to_have_value("Item To Edit")
        # Note: This assertion may fail if the form doesn't properly load saved values
        # due to the field name mismatch bug we're testing for
        expect(page.locator("#text_content")).to_have_value(original_text)

        # Update the title and content
        page.locator("#title").fill("Updated Item Title")
        page.locator("#text_content").fill(updated_text)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify updated item appears in the table
        expect(page.locator("text=Updated Item Title")).to_be_visible(timeout=5000)
        expect(page.locator("text=Item To Edit")).to_be_hidden()

        # CRITICAL: Verify via API that changes were actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Updated Item Title"
        )
        assert item is not None, "Updated item not found via API"
        assert item.get("content_text") == updated_text, (
            f"content_text not updated correctly: expected '{updated_text}', "
            f"got '{item.get('content_text')}'"
        )

    def test_edit_file_upload_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test editing an existing file upload item to change the file.

        This tests the flow of editing an image item that was created via file upload
        and uploading a different file.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # First, create an image item via the UI with one file
        image_path_1 = ASSETS_DIR / "smallPhoto.jpg"
        image_path_2 = ASSETS_DIR / "bigPhoto.jpg"
        assert image_path_1.exists(), f"Test asset not found: {image_path_1}"
        assert image_path_2.exists(), f"Test asset not found: {image_path_2}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Create the initial image item
        page.locator("button:has-text('Add Item')").click()
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        page.locator("#title").fill("Image To Edit")
        page.locator("#content_type").select_option("image")
        page.locator("#file_image").set_input_files(str(image_path_1))
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=10000)
        page.locator("button[type='submit']").click()
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item was created
        expect(page.locator("text=Image To Edit")).to_be_visible(timeout=5000)

        # Get the original file path via API
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Image To Edit"
        )
        assert item is not None, "Created item not found via API"
        original_file_path = item.get("content_file_path")
        assert original_file_path, "Original content_file_path not set"

        # Now edit the item and upload a different file
        row = page.locator("tr:has-text('Image To Edit')")
        expect(row).to_be_visible(timeout=10000)
        row.locator("button[title='Edit']").click()

        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Upload a different file
        page.locator("#file_image").set_input_files(str(image_path_2))
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=10000)

        page.locator("button[type='submit']").click()
        expect(modal).to_be_hidden(timeout=10000)

        # CRITICAL: Verify via API that the file path was updated
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Image To Edit"
        )
        assert item is not None, "Updated item not found via API"
        new_file_path = item.get("content_file_path")
        assert new_file_path, "content_file_path not set after edit"
        assert new_file_path != original_file_path, (
            f"content_file_path should have changed: "
            f"original='{original_file_path}', new='{new_file_path}'"
        )

    def test_delete_item_with_confirmation(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test deleting a slideshow item with confirmation dialog."""
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create an item via API first
        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Item To Delete",
                "content_type": "text",
                "content_text": "This item will be deleted",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Find the item row
        row = page.locator("tr:has-text('Item To Delete')")
        expect(row).to_be_visible(timeout=10000)

        # Set up dialog handler to accept the confirmation
        page.on("dialog", lambda dialog: dialog.accept())

        # Click Delete button
        row.locator("button[title='Delete']").click()

        # Wait for the item to be removed from the list
        expect(page.locator("text=Item To Delete")).to_be_hidden(timeout=10000)

    def test_reorder_items_move_up(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test reordering items by moving an item up."""
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create two items via API
        response1 = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "First Item",
                "content_type": "text",
                "content_text": "First",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response1.status_code in [200, 201]

        response2 = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Second Item",
                "content_type": "text",
                "content_text": "Second",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response2.status_code in [200, 201]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify initial order - First Item should be first
        rows = page.locator("table tbody tr")
        expect(rows).to_have_count(2, timeout=10000)

        # Get initial order
        first_row_text = rows.nth(0).inner_text()
        assert "First Item" in first_row_text, "First Item should be in position 1"

        # Move Second Item up
        second_row = page.locator("tr:has-text('Second Item')")
        expect(second_row).to_be_visible(timeout=5000)
        second_row.locator("button[title='Move Up']").click()

        # Wait for reorder to complete and verify new order
        page.wait_for_timeout(1000)  # Allow time for API call and re-render

        # Reload to ensure we see the updated order
        page.reload()
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify new order - Second Item should now be first
        rows = page.locator("table tbody tr")
        first_row_text = rows.nth(0).inner_text()
        assert (
            "Second Item" in first_row_text
        ), "Second Item should now be in position 1"

    def test_reorder_items_move_down(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test reordering items by moving an item down."""
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create two items via API
        response1 = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Alpha Item",
                "content_type": "text",
                "content_text": "Alpha",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response1.status_code in [200, 201]

        response2 = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Beta Item",
                "content_type": "text",
                "content_text": "Beta",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response2.status_code in [200, 201]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify initial order
        rows = page.locator("table tbody tr")
        expect(rows).to_have_count(2, timeout=10000)

        first_row_text = rows.nth(0).inner_text()
        assert "Alpha Item" in first_row_text, "Alpha Item should be in position 1"

        # Move Alpha Item down
        first_row = page.locator("tr:has-text('Alpha Item')")
        expect(first_row).to_be_visible(timeout=5000)
        first_row.locator("button[title='Move Down']").click()

        # Wait for reorder to complete
        page.wait_for_timeout(1000)

        # Reload to ensure we see the updated order
        page.reload()
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify new order - Beta Item should now be first
        rows = page.locator("table tbody tr")
        first_row_text = rows.nth(0).inner_text()
        assert "Beta Item" in first_row_text, "Beta Item should now be in position 1"

    def _login(self, page: Page, vite_url: str, test_database: dict):
        """Helper method to log in to the admin interface."""
        page.goto(f"{vite_url}/admin/login")
        page.wait_for_selector("input[name='username']", timeout=10000)

        user = test_database["users"][0]
        page.locator("input[name='username']").fill(user["username"])
        page.locator("input[name='password']").fill(user["password"])
        page.locator("button[type='submit']").click()

        page.wait_for_selector("h1:has-text('Dashboard')", timeout=10000)

    def test_slideshow_item_action_icons_are_visible(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that Bootstrap Icons are properly displayed on action buttons.

        This test verifies that the Bootstrap Icons CSS is properly imported,
        making icons visible on action buttons (Move Up, Move Down, Edit, Delete).

        Without the CSS import, the <i class="bi bi-xxx"> elements exist but
        render as invisible/empty, making the buttons appear blank.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create at least one item so we can see the action buttons
        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Icon Test Item",
                "content_type": "text",
                "content_text": "Testing icon visibility",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Verify the item row is visible
        row = page.locator("tr:has-text('Icon Test Item')")
        expect(row).to_be_visible(timeout=10000)

        # Verify the edit button icon is visible and has non-zero dimensions
        # The edit button uses class="bi bi-pencil"
        edit_icon = row.locator("button[title='Edit'] i.bi-pencil")
        expect(edit_icon).to_be_visible(timeout=5000)

        # Get the bounding box of the icon to verify it has dimensions
        # (without Bootstrap Icons CSS, the icon would be 0x0)
        edit_icon_box = edit_icon.bounding_box()
        assert edit_icon_box is not None, "Edit icon should have a bounding box"
        assert edit_icon_box["width"] > 0, (
            f"Edit icon width should be > 0 (got {edit_icon_box['width']}). "
            "This usually means Bootstrap Icons CSS is not imported."
        )
        assert edit_icon_box["height"] > 0, (
            f"Edit icon height should be > 0 (got {edit_icon_box['height']}). "
            "This usually means Bootstrap Icons CSS is not imported."
        )

        # Verify the delete button icon is also visible
        delete_icon = row.locator("button[title='Delete'] i.bi-trash")
        expect(delete_icon).to_be_visible(timeout=5000)
        delete_icon_box = delete_icon.bounding_box()
        assert delete_icon_box is not None, "Delete icon should have a bounding box"
        assert (
            delete_icon_box["width"] > 0
        ), f"Delete icon width should be > 0 (got {delete_icon_box['width']})"
        assert (
            delete_icon_box["height"] > 0
        ), f"Delete icon height should be > 0 (got {delete_icon_box['height']})"

    def test_auto_title_from_file_upload(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that title is auto-populated from uploaded filename.

        When a file is uploaded and the title field is empty, the title should
        be auto-populated with the filename (without extension).
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Get the image path for upload
        image_path = ASSETS_DIR / "smallPhoto.jpg"
        assert image_path.exists(), f"Test asset not found: {image_path}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        add_button = page.locator("button:has-text('Add Item')")
        expect(add_button).to_be_visible(timeout=10000)
        add_button.click()

        # Wait for modal to appear
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Ensure content type is image
        page.locator("#content_type").select_option("image")

        # Verify title is empty
        title_field = page.locator("#title")
        expect(title_field).to_have_value("")

        # Upload the image file
        page.locator("#file_image").set_input_files(str(image_path))

        # Wait for upload to complete
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=10000)

        # Verify title was auto-populated with filename (without extension)
        expect(title_field).to_have_value("smallPhoto", timeout=5000)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table with auto-generated title
        # Use specific locator to find the row by title (in fw-bold div)
        row = page.locator("tr").filter(
            has=page.locator("div.fw-bold", has_text="smallPhoto")
        )
        expect(row).to_be_visible(timeout=5000)

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(http_client, auth_headers, slideshow_id, "smallPhoto")
        assert item is not None, "Item with auto-generated title not found via API"
        assert item.get("content_type") == "image"

    def test_auto_title_from_url(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that title is auto-populated from URL.

        When a URL is entered and the title field is empty, the title should
        be auto-populated with the filename from the URL path (if present),
        excluding the file extension.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_url = "https://example.com/path/to/my-awesome-image.jpg"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Select image type
        page.locator("#content_type").select_option("image")

        # Verify title is empty
        title_field = page.locator("#title")
        expect(title_field).to_have_value("")

        # Enter the URL
        page.locator("#url_alternative").fill(test_url)

        # Blur the URL field to trigger auto-title
        page.locator("#url_alternative").blur()

        # Verify title was auto-populated with filename from URL (without extension)
        expect(title_field).to_have_value("my-awesome-image", timeout=5000)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        # Use specific locator to find the row by title (in fw-bold div)
        row = page.locator("tr").filter(
            has=page.locator("div.fw-bold", has_text="my-awesome-image")
        )
        expect(row).to_be_visible(timeout=5000)

        # CRITICAL: Verify via API that data was actually persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "my-awesome-image"
        )
        assert item is not None, "Item with auto-generated title from URL not found"
        assert item.get("content_url") == test_url

    def test_auto_title_does_not_overwrite_existing_title(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that auto-title does not overwrite an existing title.

        If the user has already entered a title, uploading a file or entering
        a URL should not change it.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Get the image path for upload
        image_path = ASSETS_DIR / "smallPhoto.jpg"
        assert image_path.exists(), f"Test asset not found: {image_path}"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Select image type
        page.locator("#content_type").select_option("image")

        # Enter a custom title FIRST
        title_field = page.locator("#title")
        custom_title = "My Custom Title"
        title_field.fill(custom_title)

        # Upload the image file
        page.locator("#file_image").set_input_files(str(image_path))

        # Wait for upload to complete
        expect(
            page.locator(".badge.bg-success:has-text('File uploaded')")
        ).to_be_visible(timeout=10000)

        # Verify title was NOT changed (should still be the custom title)
        expect(title_field).to_have_value(custom_title, timeout=2000)

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears with the custom title, not the filename
        expect(page.locator(f"text={custom_title}")).to_be_visible(timeout=5000)

        # CRITICAL: Verify via API
        item = get_item_by_title(http_client, auth_headers, slideshow_id, custom_title)
        assert item is not None, "Item with custom title not found"
        assert item.get("content_file_path"), "File was not uploaded"

    def test_text_item_preview_renders_html(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that text item preview renders HTML formatting tags.

        This test:
        1. Creates a text item with HTML tags via API
        2. Views the slideshow detail page
        3. Verifies the HTML is rendered (not shown as literal text)

        This tests the admin preview functionality for HTML in text slides.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create a text item with HTML content via API
        html_content = "This is <b>bold</b> and <i>italic</i> text"

        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "HTML Preview Test",
                "content_type": "text",
                "content_text": html_content,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Find the row with our test item
        row = page.locator("tr").filter(
            has=page.locator("div.fw-bold", has_text="HTML Preview Test")
        )
        expect(row).to_be_visible(timeout=5000)

        # Get the preview text cell (the text-muted small div)
        preview_cell = row.locator("div.text-muted.small")
        expect(preview_cell).to_be_visible()

        # Get the innerHTML to verify HTML tags are rendered
        inner_html = preview_cell.inner_html()

        # Verify HTML tags are present (rendered, not escaped)
        assert "<b>" in inner_html, (
            f"<b> tag should be rendered in preview. " f"Got innerHTML: {inner_html}"
        )
        assert "<i>" in inner_html, (
            f"<i> tag should be rendered in preview. " f"Got innerHTML: {inner_html}"
        )

        # Verify the user sees the formatted text, not literal tags
        visible_text = preview_cell.inner_text()
        assert "<b>" not in visible_text, (
            f"Literal <b> tag should not be visible. "
            f"Got visible text: {visible_text}"
        )
        assert "&lt;b&gt;" not in visible_text, (
            f"Escaped <b> tag should not be visible. "
            f"Got visible text: {visible_text}"
        )

    def test_text_item_preview_strips_unsafe_html(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that text item preview strips unsafe HTML tags.

        This test:
        1. Creates a text item with unsafe HTML via API
        2. Views the slideshow detail page
        3. Verifies unsafe HTML is stripped in the preview

        This ensures XSS prevention in the admin preview.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create a text item with unsafe HTML content via API
        unsafe_content = '<script>alert("XSS")</script><b>Safe bold</b>'

        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "XSS Preview Test",
                "content_type": "text",
                "content_text": unsafe_content,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Find the row with our test item
        row = page.locator("tr").filter(
            has=page.locator("div.fw-bold", has_text="XSS Preview Test")
        )
        expect(row).to_be_visible(timeout=5000)

        # Get the preview text cell
        preview_cell = row.locator("div.text-muted.small")
        expect(preview_cell).to_be_visible()

        # Get the innerHTML
        inner_html = preview_cell.inner_html()

        # Verify unsafe tags are stripped
        assert "<script>" not in inner_html.lower(), (
            f"<script> tag should be stripped from preview. "
            f"Got innerHTML: {inner_html}"
        )
        assert "alert(" not in inner_html, (
            f"JavaScript should be stripped from preview. "
            f"Got innerHTML: {inner_html}"
        )

        # Verify safe tags are preserved
        assert "<b>" in inner_html, (
            f"Safe <b> tag should be preserved in preview. "
            f"Got innerHTML: {inner_html}"
        )

    def test_url_item_zoom_slider_visible(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test that zoom slider is visible for URL content type.

        The zoom slider (scale_factor) should only appear when content_type
        is 'url' (Web Page). It should not appear for other content types.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Select image type - zoom slider should NOT be visible
        page.locator("#content_type").select_option("image")
        zoom_slider = page.locator("#scale_factor")
        expect(zoom_slider).not_to_be_visible()

        # Select url type - zoom slider SHOULD be visible
        page.locator("#content_type").select_option("url")
        expect(zoom_slider).to_be_visible(timeout=2000)

        # Verify label shows "Normal (100%)" by default
        zoom_label = page.locator("label[for='scale_factor']")
        expect(zoom_label).to_contain_text("Normal (100%)")

        # Select text type - zoom slider should NOT be visible
        page.locator("#content_type").select_option("text")
        expect(zoom_slider).not_to_be_visible()

    def test_add_url_item_with_zoom_scale(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test adding a URL item with zoom (scale_factor) set.

        Verifies via API that scale_factor is persisted correctly.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]
        test_url = "https://example.com/tall-page"

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Click "Add Item" button
        page.locator("button:has-text('Add Item')").click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Fill in the form for URL type
        page.locator("#title").fill("Zoomed Web Page")
        page.locator("#content_type").select_option("url")
        page.locator("#url").fill(test_url)

        # Set zoom to 50% using the slider
        zoom_slider = page.locator("#scale_factor")
        expect(zoom_slider).to_be_visible()

        # Set slider value to 50 using JavaScript
        # React uses 'input' event for range inputs, and needs special handling
        # to properly trigger React's synthetic event system
        page.evaluate("""() => {
            const slider = document.querySelector('#scale_factor');
            // Use native value setter to bypass React's controlled input
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(slider, '50');
            // Dispatch input event to trigger React onChange
            slider.dispatchEvent(new Event('input', { bubbles: true }));
        }""")

        # Verify label updated
        zoom_label = page.locator("label[for='scale_factor']")
        expect(zoom_label).to_contain_text("Zoomed out (50%)")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Zoomed Web Page")).to_be_visible(timeout=5000)

        # CRITICAL: Verify via API that scale_factor was persisted
        item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Zoomed Web Page"
        )
        assert item is not None, "Item not found via API after creation"
        assert item.get("scale_factor") == 50, (
            f"scale_factor not persisted correctly: expected 50, "
            f"got {item.get('scale_factor')}"
        )
        assert item.get("content_url") == test_url

    def test_edit_url_item_zoom_scale(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test editing an existing URL item's zoom scale.

        Creates a URL item via API, then edits the scale_factor via UI.
        Verifies via API that the update was persisted.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create a URL item via API first (no scale_factor)
        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Edit Zoom Test",
                "content_type": "url",
                "content_url": "https://example.com/edit-test",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]
        item_data = response.json().get("data", response.json())
        assert item_data.get("scale_factor") is None  # Initially no scale

        # Login and navigate to slideshow detail page
        self._login(page, vite_url, test_database)
        page.goto(f"{vite_url}/admin/slideshows/{slideshow_id}")
        page.wait_for_load_state("domcontentloaded", timeout=10000)

        # Wait for the items table to be populated with the item we created
        # The React frontend needs time to fetch and render the data
        expect(page.locator("text=Edit Zoom Test")).to_be_visible(timeout=10000)

        # Find the row with our test item and click edit
        row = page.locator("tr").filter(
            has=page.locator("div.fw-bold", has_text="Edit Zoom Test")
        )
        expect(row).to_be_visible(timeout=5000)

        # Click the edit button - use longer timeout as table may still be loading
        edit_button = row.locator("button[title='Edit']")
        expect(edit_button).to_be_visible(timeout=5000)
        edit_button.click()

        # Wait for modal
        modal = page.locator(".modal")
        expect(modal).to_be_visible(timeout=5000)

        # Verify zoom slider is visible and at 100%
        zoom_slider = page.locator("#scale_factor")
        expect(zoom_slider).to_be_visible()

        # Set zoom to 25% using JavaScript
        # React uses 'input' event for range inputs, and needs special handling
        # to properly trigger React's synthetic event system
        page.evaluate("""() => {
            const slider = document.querySelector('#scale_factor');
            // Use native value setter to bypass React's controlled input
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(slider, '25');
            // Dispatch input event to trigger React onChange
            slider.dispatchEvent(new Event('input', { bubbles: true }));
        }""")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # CRITICAL: Verify via API that scale_factor was updated
        updated_item = get_item_by_title(
            http_client, auth_headers, slideshow_id, "Edit Zoom Test"
        )
        assert updated_item is not None
        assert updated_item.get("scale_factor") == 25, (
            f"scale_factor not updated correctly: expected 25, "
            f"got {updated_item.get('scale_factor')}"
        )
