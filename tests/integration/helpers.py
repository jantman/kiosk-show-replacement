"""
Helper utilities for integration tests.

This module provides reusable helper functions for common test operations
like waiting for UI elements, handling dialogs, and form interactions.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)


def wait_for_toast(
    page: Page,
    message_contains: Optional[str] = None,
    toast_type: Optional[str] = None,
    timeout: int = 5000,
) -> str:
    """
    Wait for a toast notification to appear and return its text.

    Args:
        page: Playwright page object
        message_contains: Optional text that the toast should contain
        toast_type: Optional toast type ('success', 'error', 'warning', 'info')
        timeout: Maximum time to wait in milliseconds

    Returns:
        The text content of the toast message

    Raises:
        TimeoutError: If no matching toast appears within the timeout
    """
    # Common toast selectors for Bootstrap/React toast libraries
    toast_selectors = [
        ".toast",
        ".toast-body",
        "[role='alert']",
        ".alert",
        ".notification",
        ".Toastify__toast",
    ]

    # If a specific type is requested, prioritize type-specific selectors
    if toast_type:
        type_selectors = [
            f".toast-{toast_type}",
            f".alert-{toast_type}",
            f".bg-{toast_type}",
            f"[class*='{toast_type}']",
        ]
        toast_selectors = type_selectors + toast_selectors

    # Try each selector
    for selector in toast_selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)

            toast_text = locator.inner_text()

            # If message_contains is specified, verify it matches
            if message_contains and message_contains.lower() not in toast_text.lower():
                continue

            logger.info(f"Toast found: {toast_text[:100]}")
            return toast_text
        except Exception:
            continue

    # If we get here, no toast was found
    raise TimeoutError(
        f"No toast notification found within {timeout}ms"
        + (f" containing '{message_contains}'" if message_contains else "")
    )


def wait_for_toast_to_disappear(page: Page, timeout: int = 10000) -> None:
    """
    Wait for any visible toast notification to disappear.

    Args:
        page: Playwright page object
        timeout: Maximum time to wait in milliseconds
    """
    toast_selectors = [".toast", "[role='alert']", ".alert", ".Toastify__toast"]

    for selector in toast_selectors:
        try:
            locator = page.locator(selector)
            if locator.is_visible():
                locator.wait_for(state="hidden", timeout=timeout)
                logger.info(f"Toast disappeared: {selector}")
        except Exception:
            pass


def fill_form(page: Page, fields: Dict[str, Union[str, bool, int]]) -> None:
    """
    Fill a form with the provided field values.

    Args:
        page: Playwright page object
        fields: Dictionary mapping field identifiers to values.
                Field identifiers can be:
                - name attribute: "username"
                - id attribute: "#email"
                - label text: "Email Address"
                - placeholder: "[placeholder='Enter email']"

    Supports text inputs, textareas, checkboxes, and select dropdowns.
    """
    for field_id, value in fields.items():
        try:
            # Determine the locator based on field_id format
            if field_id.startswith("#"):
                # ID selector
                locator = page.locator(field_id)
            elif field_id.startswith("["):
                # Attribute selector
                locator = page.locator(field_id)
            elif field_id.startswith("."):
                # Class selector
                locator = page.locator(field_id)
            else:
                # Try name attribute first, then label text
                locator = page.locator(f"[name='{field_id}']")
                if not locator.is_visible():
                    # Try finding by label
                    locator = page.get_by_label(field_id)

            # Handle different input types
            element_type = locator.evaluate("el => el.type || el.tagName.toLowerCase()")

            if element_type == "checkbox":
                if value:
                    locator.check()
                else:
                    locator.uncheck()
            elif element_type == "select" or element_type == "SELECT":
                locator.select_option(str(value))
            else:
                # Text input or textarea
                locator.fill(str(value))

            logger.debug(f"Filled field '{field_id}' with value: {value}")

        except Exception as e:
            logger.warning(f"Failed to fill field '{field_id}': {e}")
            raise


def confirm_dialog(
    page: Page,
    confirm: bool = True,
    dialog_selector: Optional[str] = None,
    timeout: int = 5000,
) -> None:
    """
    Handle a confirmation dialog by clicking confirm or cancel.

    Args:
        page: Playwright page object
        confirm: True to confirm, False to cancel
        dialog_selector: Optional specific selector for the dialog
        timeout: Maximum time to wait for the dialog

    Handles common dialog patterns including Bootstrap modals,
    browser confirm dialogs, and custom confirmation components.
    """

    # First, try to handle browser-native dialogs
    def handle_native_dialog(dialog):
        if confirm:
            dialog.accept()
        else:
            dialog.dismiss()
        logger.info(f"Handled native dialog: {'accepted' if confirm else 'dismissed'}")

    page.on("dialog", handle_native_dialog)

    # For custom dialogs (Bootstrap modals, etc.)
    modal_selectors = [
        dialog_selector,
        ".modal.show",
        "[role='dialog']",
        ".modal-dialog",
        ".confirmation-dialog",
    ]

    for selector in modal_selectors:
        if not selector:
            continue

        try:
            modal = page.locator(selector).first
            if modal.is_visible():
                if confirm:
                    # Try common confirm button patterns
                    confirm_buttons = [
                        modal.locator("button:has-text('Confirm')"),
                        modal.locator("button:has-text('Yes')"),
                        modal.locator("button:has-text('Delete')"),
                        modal.locator("button:has-text('OK')"),
                        modal.locator(".btn-danger"),
                        modal.locator(".btn-primary"),
                    ]
                    for btn in confirm_buttons:
                        if btn.is_visible():
                            btn.click()
                            logger.info("Clicked confirm button in modal")
                            return
                else:
                    # Try common cancel button patterns
                    cancel_buttons = [
                        modal.locator("button:has-text('Cancel')"),
                        modal.locator("button:has-text('No')"),
                        modal.locator("button:has-text('Close')"),
                        modal.locator(".btn-secondary"),
                        modal.locator("[data-dismiss='modal']"),
                        modal.locator("[data-bs-dismiss='modal']"),
                    ]
                    for btn in cancel_buttons:
                        if btn.is_visible():
                            btn.click()
                            logger.info("Clicked cancel button in modal")
                            return

        except Exception:
            continue

    # Remove the dialog handler after a brief wait
    time.sleep(0.5)
    page.remove_listener("dialog", handle_native_dialog)


def wait_for_navigation(page: Page, url_contains: str, timeout: int = 10000) -> None:
    """
    Wait for the page to navigate to a URL containing the specified string.

    Args:
        page: Playwright page object
        url_contains: String that the URL should contain
        timeout: Maximum time to wait in milliseconds
    """
    page.wait_for_url(f"**/*{url_contains}*", timeout=timeout)
    logger.info(f"Navigated to URL containing: {url_contains}")


def wait_for_loading_complete(page: Page, timeout: int = 10000) -> None:
    """
    Wait for page loading indicators to disappear.

    Args:
        page: Playwright page object
        timeout: Maximum time to wait in milliseconds
    """
    loading_selectors = [
        ".loading",
        ".spinner",
        ".spinner-border",
        "[aria-busy='true']",
        ".loading-indicator",
        ".skeleton",
    ]

    for selector in loading_selectors:
        try:
            locator = page.locator(selector)
            if locator.is_visible():
                locator.wait_for(state="hidden", timeout=timeout)
                logger.debug(f"Loading indicator hidden: {selector}")
        except Exception:
            pass


def get_table_rows(page: Page, table_selector: str = "table") -> List[Dict[str, str]]:
    """
    Extract data from a table as a list of dictionaries.

    Args:
        page: Playwright page object
        table_selector: CSS selector for the table

    Returns:
        List of dictionaries, one per row, with header names as keys
    """
    table = page.locator(table_selector).first

    # Get headers
    headers = []
    header_cells = table.locator("thead th, thead td")
    for i in range(header_cells.count()):
        headers.append(header_cells.nth(i).inner_text().strip())

    # Get rows
    rows = []
    body_rows = table.locator("tbody tr")
    for row_idx in range(body_rows.count()):
        row = body_rows.nth(row_idx)
        cells = row.locator("td")
        row_data = {}
        for col_idx in range(min(cells.count(), len(headers))):
            header = headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}"
            row_data[header] = cells.nth(col_idx).inner_text().strip()
        rows.append(row_data)

    return rows


def click_table_row_action(
    page: Page,
    row_text: str,
    action_name: str,
    table_selector: str = "table",
) -> None:
    """
    Click an action button/link in a table row that contains specific text.

    Args:
        page: Playwright page object
        row_text: Text that identifies the target row
        action_name: Text or aria-label of the action button to click
        table_selector: CSS selector for the table
    """
    table = page.locator(table_selector).first
    row = table.locator(f"tbody tr:has-text('{row_text}')").first

    # Try to find the action button
    action_selectors = [
        f"button:has-text('{action_name}')",
        f"a:has-text('{action_name}')",
        f"[aria-label='{action_name}']",
        f"[title='{action_name}']",
        f".btn:has-text('{action_name}')",
    ]

    for selector in action_selectors:
        try:
            button = row.locator(selector).first
            if button.is_visible():
                button.click()
                logger.info(
                    f"Clicked '{action_name}' action in row containing '{row_text}'"
                )
                return
        except Exception:
            continue

    raise ValueError(
        f"Could not find action '{action_name}' in row containing '{row_text}'"
    )


def upload_file(page: Page, file_input_selector: str, file_path: Path) -> None:
    """
    Upload a file using a file input element.

    Args:
        page: Playwright page object
        file_input_selector: CSS selector for the file input
        file_path: Path to the file to upload
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Test asset not found: {file_path}")

    file_input = page.locator(file_input_selector)
    file_input.set_input_files(str(file_path))
    logger.info(f"Uploaded file: {file_path.name}")


def select_dropdown_option(
    page: Page, dropdown_selector: str, option_text: str
) -> None:
    """
    Select an option from a dropdown by its visible text.

    Args:
        page: Playwright page object
        dropdown_selector: CSS selector for the select element
        option_text: The visible text of the option to select
    """
    dropdown = page.locator(dropdown_selector)
    dropdown.select_option(label=option_text)
    logger.info(f"Selected dropdown option: {option_text}")


def get_element_text(page: Page, selector: str, timeout: int = 5000) -> str:
    """
    Get the text content of an element, waiting for it to be visible.

    Args:
        page: Playwright page object
        selector: CSS selector for the element
        timeout: Maximum time to wait in milliseconds

    Returns:
        The text content of the element
    """
    element = page.locator(selector).first
    element.wait_for(state="visible", timeout=timeout)
    return element.inner_text()


def assert_element_contains_text(
    page: Page,
    selector: str,
    expected_text: str,
    timeout: int = 5000,
) -> None:
    """
    Assert that an element contains specific text.

    Args:
        page: Playwright page object
        selector: CSS selector for the element
        expected_text: Text that should be contained in the element
        timeout: Maximum time to wait in milliseconds
    """
    element = page.locator(selector).first
    expect(element).to_contain_text(expected_text, timeout=timeout)


def navigate_to(page: Page, path: str, base_url: str) -> None:
    """
    Navigate to a specific path within the application.

    Args:
        page: Playwright page object
        path: The path to navigate to (e.g., "/admin/slideshows")
        base_url: The base URL of the application
    """
    full_url = f"{base_url.rstrip('/')}{path}"
    page.goto(full_url)
    logger.info(f"Navigated to: {full_url}")


def wait_for_api_response(
    page: Page,
    url_pattern: str,
    timeout: int = 10000,
) -> dict:
    """
    Wait for an API request matching the URL pattern and return its response.

    Args:
        page: Playwright page object
        url_pattern: Pattern to match in the request URL
        timeout: Maximum time to wait in milliseconds

    Returns:
        The JSON response from the API
    """
    with page.expect_response(
        lambda response: url_pattern in response.url,
        timeout=timeout,
    ) as response_info:
        pass

    response = response_info.value
    return response.json()
