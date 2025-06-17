"""
Basic E2E test to verify infrastructure is working.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_basic_server_access(page: Page, live_server_url: str):
    """Test that we can access the live server and see the login page."""

    # Visit the application
    page.goto(live_server_url)

    # Should see the login page
    expect(page).to_have_title("Login - Kiosk Show Replacement")

    # Should see login form
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("h4:has-text('Login')")).to_be_visible()

    print(f"✓ Successfully accessed live server at {live_server_url}")
    print("✓ Login page is rendering correctly")


@pytest.mark.e2e
def test_basic_form_interaction(page: Page, live_server_url: str):
    """Test that we can interact with form elements."""

    page.goto(live_server_url)

    # Fill in some test data
    username_field = page.locator("input[name='username']")
    password_field = page.locator("input[name='password']")

    username_field.fill("testuser")
    password_field.fill("testpass")

    # Verify the values were entered
    expect(username_field).to_have_value("testuser")
    expect(password_field).to_have_value("testpass")

    print("✓ Form interaction working correctly")
