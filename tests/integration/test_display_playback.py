"""
Integration tests for display view slideshow playback.

Tests verify that slideshows play correctly on display views:
- All slides display in correct order
- Slide durations are respected (both default and overridden)
- Different content types render properly
- Uploaded images load successfully
- SSE events trigger display reload on assignment change
- Text slides only show content, not title
- Text slides preserve line breaks
- Info overlay visibility based on display settings

Run with: nox -s test-integration
"""

import os
import time
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
class TestDisplayPlayback:
    """Test slideshow playback on display views."""

    def test_all_slides_display_with_mixed_durations(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test that all slides display correctly with mixed default and override durations.

        Creates a slideshow with 3 text slides:
        - Slide 1: uses default duration (10 seconds from slideshow)
        - Slide 2: has 2-second override duration
        - Slide 3: uses default duration (10 seconds from slideshow)

        The test verifies that all 3 slides are shown, not just the one with
        an override duration. This tests the bug where slides with null
        display_duration were being skipped (0ms timeout).

        We use short durations and verify slide transitions occur.
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Create a slideshow with a short default duration for faster testing
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "Duration Test Slideshow",
                "description": "Test slideshow for duration handling",
                "default_item_duration": 2,  # 2 second default
                "transition_type": "fade",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [
            200,
            201,
        ], f"Failed to create slideshow: {slideshow_response.text}"
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create 3 text slides with mixed durations
            # Slide 1: NO duration override (uses slideshow default)
            slide1_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Slide One",
                    "content_type": "text",
                    "content_text": "This is the first slide with DEFAULT duration",
                    "is_active": True,
                    # No display_duration - should use slideshow default (2s)
                },
                headers=auth_headers,
            )
            assert slide1_response.status_code in [200, 201]

            # Slide 2: Has 1-second override duration
            slide2_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Slide Two",
                    "content_type": "text",
                    "content_text": "This is the second slide with OVERRIDE duration",
                    "display_duration": 1,  # 1 second override
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert slide2_response.status_code in [200, 201]

            # Slide 3: NO duration override (uses slideshow default)
            slide3_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Slide Three",
                    "content_type": "text",
                    "content_text": "This is the third slide with DEFAULT duration",
                    "is_active": True,
                    # No display_duration - should use slideshow default (2s)
                },
                headers=auth_headers,
            )
            assert slide3_response.status_code in [200, 201]

            # Create a display
            display_name = f"test-duration-display-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for duration testing",
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Navigate to display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Wait for slideshow to initialize
                page.wait_for_selector("#slideshowContainer", timeout=10000)

                # Track which slides we see
                slides_seen = set()

                # Watch for slide changes over 8 seconds
                # With durations of 2s, 1s, 2s we should see all 3 slides cycle
                start_time = time.time()
                max_wait = (
                    8  # 8 seconds should be enough for 2+1+2 = 5 seconds of slides
                )

                while time.time() - start_time < max_wait and len(slides_seen) < 3:
                    # Check for each slide's content
                    if page.locator("text=first slide with DEFAULT").is_visible():
                        slides_seen.add("Slide One")
                    if page.locator("text=second slide with OVERRIDE").is_visible():
                        slides_seen.add("Slide Two")
                    if page.locator("text=third slide with DEFAULT").is_visible():
                        slides_seen.add("Slide Three")

                    # Small delay between checks
                    time.sleep(0.2)

                # Verify all 3 slides were displayed
                assert "Slide One" in slides_seen, (
                    f"Slide One (default duration) was never shown. "
                    f"Slides seen: {slides_seen}"
                )
                assert "Slide Two" in slides_seen, (
                    f"Slide Two (override duration) was never shown. "
                    f"Slides seen: {slides_seen}"
                )
                assert "Slide Three" in slides_seen, (
                    f"Slide Three (default duration) was never shown. "
                    f"Slides seen: {slides_seen}"
                )

            finally:
                # Cleanup display (test_all_slides_display_with_mixed_durations)
                http_client.delete(
                    f"/api/v1/displays/{display_id}",
                    headers=auth_headers,
                )

        finally:
            # Cleanup slideshow (test_all_slides_display_with_mixed_durations)
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )

    def test_uploaded_image_displays_on_display_view(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test that uploaded images display correctly on the display view.

        This test:
        1. Creates a slideshow
        2. Uploads an image file via the API
        3. Creates a slideshow item with the uploaded image
        4. Assigns the slideshow to a display
        5. Navigates to the display view
        6. Verifies the image loads successfully (no error shown)

        This tests the bug where uploaded images showed "Failed to load image"
        even though the files existed on the server.
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Verify test asset exists
        image_path = ASSETS_DIR / "smallPhoto.jpg"
        assert image_path.exists(), f"Test asset not found: {image_path}"

        # Create a slideshow
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "Image Display Test Slideshow",
                "description": "Test slideshow for image display",
                "default_item_duration": 10,
                "transition_type": "fade",
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Upload an image
            with open(image_path, "rb") as f:
                files = {"file": ("smallPhoto.jpg", f, "image/jpeg")}
                data = {"slideshow_id": str(slideshow_id)}
                # Need to remove Content-Type from headers for multipart
                upload_headers = {
                    k: v for k, v in auth_headers.items() if k != "Content-Type"
                }
                upload_response = http_client.post(
                    "/api/v1/uploads/image",
                    files=files,
                    data=data,
                    headers=upload_headers,
                )

            assert upload_response.status_code in [
                200,
                201,
            ], f"Failed to upload image: {upload_response.text}"
            upload_data = upload_response.json().get("data", upload_response.json())
            file_path = upload_data.get("file_path")
            assert file_path, f"No file_path in upload response: {upload_data}"

            # Create a slideshow item with the uploaded image
            item_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Test Uploaded Image",
                    "content_type": "image",
                    "content_file_path": file_path,
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert item_response.status_code in [200, 201]

            # Verify the item was created with the file path
            item_data = item_response.json().get("data", item_response.json())
            assert item_data.get("content_file_path") == file_path
            assert item_data.get(
                "display_url"
            ), f"display_url should be set for uploaded image: {item_data}"

            # Create a display
            display_name = f"test-image-display-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for image display testing",
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Track network requests to detect image loading
                image_requests = []
                failed_requests = []

                def track_request(request):
                    if "/uploads/" in request.url:
                        image_requests.append(request.url)

                def track_failed(request):
                    if "/uploads/" in request.url:
                        failed_requests.append(
                            {"url": request.url, "failure": request.failure}
                        )

                def track_response(response):
                    if "/uploads/" in response.url and response.status >= 400:
                        failed_requests.append(
                            {"url": response.url, "status": response.status}
                        )

                page.on("request", track_request)
                page.on("requestfailed", track_failed)
                page.on("response", track_response)

                # Navigate to display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Wait for slideshow to initialize
                page.wait_for_selector("#slideshowContainer", timeout=10000)

                # Wait a moment for image to load
                time.sleep(2)

                # Check that the image element exists and doesn't show error
                img_element = page.locator("img").first
                assert img_element.is_visible(), "Image element should be visible"

                # Check that we don't see the error message
                error_visible = page.locator("text=Failed to load image").is_visible()
                assert not error_visible, (
                    f"Image failed to load. "
                    f"Image requests: {image_requests}, "
                    f"Failed requests: {failed_requests}"
                )

                # Verify an image request was made to /uploads/
                assert (
                    len(image_requests) > 0
                ), "No image requests were made to /uploads/ endpoint"

                # Verify no requests failed
                assert (
                    len(failed_requests) == 0
                ), f"Image request(s) failed: {failed_requests}"

            finally:
                # Cleanup display (test_uploaded_image_displays_on_display_view)
                http_client.delete(
                    f"/api/v1/displays/{display_id}",
                    headers=auth_headers,
                )

        finally:
            # Cleanup slideshow (test_uploaded_image_displays_on_display_view)
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )

    def test_display_reloads_on_slideshow_assignment_change(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test that display automatically reloads when slideshow assignment changes.

        This test:
        1. Creates two slideshows with different content
        2. Creates a display and assigns the first slideshow
        3. Navigates to the display view
        4. Changes the slideshow assignment via API
        5. Verifies the display view automatically updates to show new slideshow content

        This tests the bug where slideshow assignment changes didn't reach displays
        via SSE, requiring manual page refresh.
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Create first slideshow
        slideshow1_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "SSE Test Slideshow 1",
                "description": "First slideshow for SSE test",
                "default_item_duration": 30,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow1_response.status_code in [200, 201]
        slideshow1_data = slideshow1_response.json().get(
            "data", slideshow1_response.json()
        )
        slideshow1_id = slideshow1_data["id"]

        # Create second slideshow
        slideshow2_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "SSE Test Slideshow 2",
                "description": "Second slideshow for SSE test",
                "default_item_duration": 30,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow2_response.status_code in [200, 201]
        slideshow2_data = slideshow2_response.json().get(
            "data", slideshow2_response.json()
        )
        slideshow2_id = slideshow2_data["id"]

        try:
            # Add a text slide to first slideshow with distinctive content
            http_client.post(
                f"/api/v1/slideshows/{slideshow1_id}/items",
                json={
                    "title": "First Slideshow Unique Content",
                    "content_type": "text",
                    "content_text": "THIS IS SLIDESHOW ONE - ORIGINAL ASSIGNMENT",
                    "is_active": True,
                },
                headers=auth_headers,
            )

            # Add a text slide to second slideshow with different distinctive content
            http_client.post(
                f"/api/v1/slideshows/{slideshow2_id}/items",
                json={
                    "title": "Second Slideshow Unique Content",
                    "content_type": "text",
                    "content_text": "THIS IS SLIDESHOW TWO - NEW ASSIGNMENT",
                    "is_active": True,
                },
                headers=auth_headers,
            )

            # Create a display
            display_name = f"test-sse-display-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for SSE assignment change",
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign first slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow1_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Navigate to display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_selector("#slideshowContainer", timeout=10000)

                # Verify first slideshow content is visible
                first_content_visible = page.locator(
                    "text=THIS IS SLIDESHOW ONE"
                ).is_visible()
                assert (
                    first_content_visible
                ), "First slideshow content should be visible"

                # Wait for SSE connection to establish
                time.sleep(1)

                # Now change the slideshow assignment via API
                reassign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow2_id},
                    headers=auth_headers,
                )
                assert reassign_response.status_code == 200

                # Wait for SSE event to trigger page reload
                # The display should receive the assignment_changed event and reload
                max_wait = 10  # 10 seconds should be plenty for SSE
                start_time = time.time()
                second_content_visible = False

                while (
                    time.time() - start_time < max_wait and not second_content_visible
                ):
                    # Check if second slideshow content becomes visible
                    try:
                        second_content_visible = page.locator(
                            "text=THIS IS SLIDESHOW TWO"
                        ).is_visible()
                    except Exception:
                        # Page might be reloading
                        pass
                    time.sleep(0.5)

                # Verify the display now shows the second slideshow
                assert second_content_visible, (
                    "Display should have automatically switched to second slideshow "
                    "via SSE after assignment change. "
                    "If this fails, SSE events are not reaching the display."
                )

            finally:
                # Cleanup display (test_display_reloads_on_slideshow_assignment_change)
                http_client.delete(
                    f"/api/v1/displays/{display_id}",
                    headers=auth_headers,
                )

        finally:
            # Cleanup slideshows (test_display_reloads_on_slideshow_assignment_change)
            http_client.delete(
                f"/api/v1/slideshows/{slideshow1_id}",
                headers=auth_headers,
            )
            http_client.delete(
                f"/api/v1/slideshows/{slideshow2_id}",
                headers=auth_headers,
            )

    def test_text_slide_shows_only_content_not_title(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test that text slides only display content_text, not the title.

        This test:
        1. Creates a slideshow with a text slide that has both title and content_text
        2. Assigns the slideshow to a display
        3. Navigates to the display view
        4. Verifies the content_text is shown
        5. Verifies the title is NOT shown

        This tests the bug where text slides were incorrectly displaying both
        the title and the text content, when they should only show content_text.
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Create a slideshow
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "Text Title Test Slideshow",
                "description": "Test slideshow for text title display",
                "default_item_duration": 30,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create a text slide with BOTH title AND content_text
            # The title should NOT be displayed on the display view
            distinctive_title = "TITLE_SHOULD_NOT_BE_DISPLAYED_XYZ123"
            distinctive_content = "CONTENT_SHOULD_BE_DISPLAYED_ABC789"

            item_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": distinctive_title,
                    "content_type": "text",
                    "content_text": distinctive_content,
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert item_response.status_code in [200, 201]

            # Create a display
            display_name = f"test-text-title-display-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for text title testing",
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Navigate to display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Wait for slideshow to initialize
                page.wait_for_selector("#slideshowContainer", timeout=10000)

                # Wait a moment for content to render
                time.sleep(1)

                # Verify the content_text IS displayed
                content_visible = page.locator(
                    f"text={distinctive_content}"
                ).is_visible()
                assert content_visible, (
                    f"Text content '{distinctive_content}' should be displayed on "
                    "the display view"
                )

                # Verify the title is NOT displayed
                title_visible = page.locator(f"text={distinctive_title}").is_visible()
                assert not title_visible, (
                    f"Title '{distinctive_title}' should NOT be displayed on "
                    "the display view for text slides. Only content_text should "
                    "be shown."
                )

            finally:
                # Cleanup display (test_text_slide_shows_only_content_not_title)
                http_client.delete(
                    f"/api/v1/displays/{display_id}",
                    headers=auth_headers,
                )

        finally:
            # Cleanup slideshow (test_text_slide_shows_only_content_not_title)
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )

    def test_text_slide_preserves_line_breaks(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test that text slides preserve line breaks/newlines.

        This test:
        1. Creates a slideshow with a text slide that has multiple lines
        2. Assigns the slideshow to a display
        3. Navigates to the display view
        4. Verifies the line breaks are preserved (text appears on separate lines)

        This tests the bug where text slides collapsed all line breaks.
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Create a slideshow
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "Text Formatting Test Slideshow",
                "description": "Test slideshow for text formatting",
                "default_item_duration": 30,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create a text slide with multiple lines
            # Each line has distinctive content so we can verify they're on separate lines
            line1 = "LINE_ONE_CONTENT"
            line2 = "LINE_TWO_CONTENT"
            line3 = "LINE_THREE_CONTENT"
            multiline_content = f"{line1}\n{line2}\n{line3}"

            item_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Multiline Test",
                    "content_type": "text",
                    "content_text": multiline_content,
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert item_response.status_code in [200, 201]

            # Create a display
            display_name = f"test-text-format-display-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for text formatting testing",
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Navigate to display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)

                # Wait for slideshow to initialize
                page.wait_for_selector("#slideshowContainer", timeout=10000)

                # Wait a moment for content to render
                time.sleep(1)

                # Verify all three lines are visible
                for line in [line1, line2, line3]:
                    assert page.locator(
                        f"text={line}"
                    ).is_visible(), f"Line '{line}' should be visible in the text slide"

                # Verify lines are on separate lines by checking that the content element
                # has line breaks preserved (via CSS white-space or <br> tags)
                content_element = page.locator(".text-content .content")
                expect(content_element).to_be_visible()

                # Get the computed style to verify white-space is set to preserve line breaks
                # or check that text appears on multiple lines by examining bounding boxes
                html_content = content_element.inner_html()

                # Check if line breaks are preserved either by <br> tags or by CSS
                # The content should either have <br> tags between lines, or the
                # white-space CSS property should be 'pre-wrap' or 'pre-line'
                has_br_tags = "<br" in html_content.lower()

                # Get computed style
                computed_style = page.evaluate(
                    """(el) => window.getComputedStyle(el).whiteSpace""",
                    content_element.element_handle(),
                )
                has_whitespace_css = computed_style in ["pre-wrap", "pre-line", "pre"]

                assert has_br_tags or has_whitespace_css, (
                    f"Text content should preserve line breaks. "
                    f"HTML content: '{html_content}', "
                    f"computed white-space: '{computed_style}'. "
                    f"Expected <br> tags or white-space: pre-wrap/pre-line/pre."
                )

            finally:
                # Cleanup display (test_text_slide_preserves_line_breaks)
                http_client.delete(
                    f"/api/v1/displays/{display_id}",
                    headers=auth_headers,
                )

        finally:
            # Cleanup slideshow (test_text_slide_preserves_line_breaks)
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )

    def test_info_overlay_respects_display_setting(
        self,
        enhanced_page: Page,
        servers: dict,
        test_database: dict,
        http_client,
        auth_headers,
    ):
        """Test that info overlay visibility respects the display's show_info_overlay setting.

        This test:
        1. Creates a display with show_info_overlay=False
        2. Creates a slideshow and assigns it to the display
        3. Navigates to the display view
        4. Verifies the info overlay is NOT visible
        5. Updates the display to show_info_overlay=True
        6. Reloads and verifies the info overlay IS visible

        The info overlay shows slideshow name, slide counter, and display name.
        """
        page = enhanced_page
        flask_url = servers["flask_url"]

        # Create a slideshow
        slideshow_response = http_client.post(
            "/api/v1/slideshows",
            json={
                "name": "Info Overlay Test Slideshow",
                "description": "Test slideshow for info overlay",
                "default_item_duration": 30,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert slideshow_response.status_code in [200, 201]
        slideshow_data = slideshow_response.json().get(
            "data", slideshow_response.json()
        )
        slideshow_id = slideshow_data["id"]

        try:
            # Create a text slide
            item_response = http_client.post(
                f"/api/v1/slideshows/{slideshow_id}/items",
                json={
                    "title": "Test Slide",
                    "content_type": "text",
                    "content_text": "Test content for info overlay test",
                    "is_active": True,
                },
                headers=auth_headers,
            )
            assert item_response.status_code in [200, 201]

            # Create a display with show_info_overlay=False (default)
            display_name = f"test-overlay-display-{int(time.time() * 1000)}"
            display_response = http_client.post(
                "/api/v1/displays",
                json={
                    "name": display_name,
                    "description": "Test display for info overlay testing",
                    "show_info_overlay": False,  # Explicitly disable
                },
                headers=auth_headers,
            )
            assert display_response.status_code in [200, 201]
            display_data = display_response.json().get("data", display_response.json())
            display_id = display_data["id"]

            try:
                # Assign slideshow to display
                assign_response = http_client.post(
                    f"/api/v1/displays/{display_name}/assign-slideshow",
                    json={"slideshow_id": slideshow_id},
                    headers=auth_headers,
                )
                assert assign_response.status_code == 200

                # Navigate to display view
                page.goto(f"{flask_url}/display/{display_name}")
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_selector("#slideshowContainer", timeout=10000)
                time.sleep(1)

                # Verify the info overlay is NOT visible when show_info_overlay=False
                slide_info = page.locator("#slideInfo")
                overlay_visible = slide_info.is_visible()
                assert (
                    not overlay_visible
                ), "Info overlay should NOT be visible when show_info_overlay=False"

                # Update the display to show_info_overlay=True
                update_response = http_client.put(
                    f"/api/v1/displays/{display_id}",
                    json={"show_info_overlay": True},
                    headers=auth_headers,
                )
                assert update_response.status_code == 200

                # Reload the page to pick up the change
                page.reload()
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_selector("#slideshowContainer", timeout=10000)
                time.sleep(1)

                # Verify the info overlay IS visible when show_info_overlay=True
                slide_info = page.locator("#slideInfo")
                overlay_visible = slide_info.is_visible()
                assert (
                    overlay_visible
                ), "Info overlay should be visible when show_info_overlay=True"

                # Verify the overlay contains expected information
                expect(slide_info).to_contain_text(display_name)
                expect(slide_info).to_contain_text("Info Overlay Test Slideshow")

            finally:
                # Cleanup display (test_info_overlay_respects_display_setting)
                http_client.delete(
                    f"/api/v1/displays/{display_id}",
                    headers=auth_headers,
                )

        finally:
            # Cleanup slideshow (test_info_overlay_respects_display_setting)
            http_client.delete(
                f"/api/v1/slideshows/{slideshow_id}",
                headers=auth_headers,
            )
