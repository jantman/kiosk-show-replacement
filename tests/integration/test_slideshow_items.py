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

Run with: nox -s test-integration
"""

import os
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

# Path to test assets
ASSETS_DIR = Path(__file__).parent.parent / "assets"


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
    ):
        """Test adding an image item by uploading a file.

        Tests the image file upload flow through the admin interface.
        """
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

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
        image_path = ASSETS_DIR / "smallPhoto.jpg"
        assert image_path.exists(), f"Test asset not found: {image_path}"
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

    def test_add_image_item_via_url(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test adding an image item by specifying a URL."""
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

        # Fill in the form with URL instead of file upload
        page.locator("#title").fill("Test Image URL")
        page.locator("#content_type").select_option("image")
        page.locator("#url_alternative").fill("https://example.com/image.jpg")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Image URL")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Image URL') .badge:has-text('image')")
        ).to_be_visible()

    def test_add_video_item_via_file_upload(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test adding a video item by uploading a file.

        Tests the video file upload flow through the admin interface.
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

        # Fill in the form
        page.locator("#title").fill("Test Video Upload")
        page.locator("#content_type").select_option("video")

        # Upload the video file
        video_path = ASSETS_DIR / "crash_into_pole.mpeg"
        assert video_path.exists(), f"Test asset not found: {video_path}"
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

    def test_add_video_item_via_url(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test adding a video item by specifying a URL."""
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

        # Fill in the form with URL instead of file upload
        page.locator("#title").fill("Test Video URL")
        page.locator("#content_type").select_option("video")
        page.locator("#url_alternative").fill("https://example.com/video.mp4")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Video URL")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Video URL') .badge:has-text('video')")
        ).to_be_visible()

    def test_add_url_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test adding a URL (webpage) item."""
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

        # Fill in the form for URL type
        page.locator("#title").fill("Test Web Page")
        page.locator("#content_type").select_option("url")
        page.locator("#url").fill("https://example.com")

        # Optionally set a custom duration
        page.locator("#duration").fill("30")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Web Page")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Web Page') .badge:has-text('url')")
        ).to_be_visible()

    def test_add_text_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
    ):
        """Test adding a text item."""
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

        # Fill in the form for text type
        page.locator("#title").fill("Test Text Slide")
        page.locator("#content_type").select_option("text")
        page.locator("#text_content").fill("This is a test message for the slideshow.")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify item appears in the table
        expect(page.locator("text=Test Text Slide")).to_be_visible(timeout=5000)
        expect(
            page.locator("tr:has-text('Test Text Slide') .badge:has-text('text')")
        ).to_be_visible()

    def test_edit_existing_item(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        test_slideshow: dict,
        http_client,
        auth_headers,
    ):
        """Test editing an existing slideshow item."""
        page = enhanced_page
        vite_url = servers["vite_url"]
        slideshow_id = test_slideshow["id"]

        # Create an item via API first
        response = http_client.post(
            f"/api/v1/slideshows/{slideshow_id}/items",
            json={
                "title": "Item To Edit",
                "content_type": "text",
                "text_content": "Original text content",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 201]

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

        # Verify form is pre-filled
        expect(page.locator("#title")).to_have_value("Item To Edit")

        # Update the title and content
        page.locator("#title").fill("Updated Item Title")
        page.locator("#text_content").fill("Updated text content")

        # Submit the form
        page.locator("button[type='submit']").click()

        # Wait for modal to close
        expect(modal).to_be_hidden(timeout=10000)

        # Verify updated item appears in the table
        expect(page.locator("text=Updated Item Title")).to_be_visible(timeout=5000)
        expect(page.locator("text=Item To Edit")).to_be_hidden()

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
                "text_content": "This item will be deleted",
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
                "text_content": "First",
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
                "text_content": "Second",
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
                "text_content": "Alpha",
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
                "text_content": "Beta",
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
