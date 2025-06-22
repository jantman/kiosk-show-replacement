"""
End-to-end tests for Server-Sent Events (SSE) workflows.

Tests real-time update functionality across the entire application,
ensuring SSE events are properly broadcast and received.
"""

import pytest
import asyncio
import time
from playwright.async_api import Page, BrowserContext, expect

from kiosk_show_replacement.app import create_app
from kiosk_show_replacement.models import Display, Slideshow, db
from kiosk_show_replacement.database_utils import DatabaseUtils


class TestSSEWorkflows:
    """Test complete SSE workflows end-to-end."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page, context: BrowserContext):
        """Set up test environment with clean database and authentication."""
        self.page = page
        self.context = context
        
        # Initialize test database
        app = create_app()
        with app.app_context():
            DatabaseUtils.drop_all_tables()
            DatabaseUtils.create_all_tables()
            DatabaseUtils.create_admin_user()
            
            # Create test data
            self.test_slideshow = Slideshow(
                name="Test Slideshow",
                description="Test slideshow for SSE testing",
                owner_id=1
            )
            db.session.add(self.test_slideshow)
            
            self.test_display = Display(
                name="Test Display",
                location="Test Location",
                owner_id=1
            )
            db.session.add(self.test_display)
            db.session.commit()
            
            self.slideshow_id = self.test_slideshow.id
            self.display_id = self.test_display.id

    async def test_real_time_display_status_updates(self, live_server):
        """Test that display status changes are reflected in real-time."""
        
        # Navigate to admin dashboard
        await self.page.goto(f"{live_server.url}")
        
        # Login
        await self.page.fill('[data-testid="username"]', 'admin')
        await self.page.fill('[data-testid="password"]', 'admin')
        await self.page.click('[data-testid="login-button"]')
        
        # Wait for dashboard
        await expect(self.page.locator('h1')).to_contain_text('Dashboard')
        
        # Navigate to displays page
        await self.page.click('text=Displays')
        await expect(self.page.locator('h1')).to_contain_text('Displays')
        
        # Verify display is shown as offline initially
        display_row = self.page.locator(f'tr:has-text("Test Display")')
        await expect(display_row.locator('.badge-danger')).to_contain_text('Offline')
        
        # Simulate display coming online via API
        async with self.context.request.new_context() as api_context:
            # Login to get session - use API endpoint with JSON
            login_response = await api_context.post(f"{live_server.url}/api/v1/auth/login", json={
                'username': 'admin',
                'password': 'admin'
            })
            assert login_response.status == 200
            
            # Send heartbeat to make display online
            response = await api_context.post(
                f"{live_server.url}/api/v1/displays/{self.display_id}/heartbeat",
                json={'resolution': '1920x1080'}
            )
            assert response.status == 200
        
        # Wait for real-time update to show display as online
        await expect(display_row.locator('.badge-success')).to_contain_text('Online', timeout=5000)

    async def test_real_time_slideshow_assignment_updates(self, live_server):
        """Test that slideshow assignments update in real-time."""
        
        # Navigate to admin dashboard and login
        await self.page.goto(f"{live_server.url}")
        await self.page.fill('[data-testid="username"]', 'admin')
        await self.page.fill('[data-testid="password"]', 'admin')
        await self.page.click('[data-testid="login-button"]')
        
        # Navigate to displays page
        await self.page.click('text=Displays')
        await expect(self.page.locator('h1')).to_contain_text('Displays')
        
        # Initially no slideshow assigned
        display_row = self.page.locator(f'tr:has-text("Test Display")')
        await expect(display_row.locator('td:nth-child(4)')).to_contain_text('No slideshow assigned')
        
        # Assign slideshow via API
        async with self.context.request.new_context() as api_context:
            # Login to get session - use API endpoint with JSON
            login_response = await api_context.post(f"{live_server.url}/api/v1/auth/login", json={
                'username': 'admin',
                'password': 'admin'
            })
            assert login_response.status == 200
            
            # Assign slideshow to display
            response = await api_context.put(
                f"{live_server.url}/api/v1/displays/{self.display_id}",
                json={'current_slideshow_id': self.slideshow_id}
            )
            assert response.status == 200
        
        # Wait for real-time update to show slideshow assignment
        await expect(display_row.locator('td:nth-child(4)')).to_contain_text('Test Slideshow', timeout=5000)

    async def test_real_time_notifications(self, live_server):
        """Test that SSE events trigger real-time notifications."""
        
        # Navigate to admin dashboard and login
        await self.page.goto(f"{live_server.url}")
        await self.page.fill('[data-testid="username"]', 'admin')
        await self.page.fill('[data-testid="password"]', 'admin')
        await self.page.click('[data-testid="login-button"]')
        
        # Wait for dashboard
        await expect(self.page.locator('h1')).to_contain_text('Dashboard')
        
        # Trigger a display status change via API
        async with self.context.request.new_context() as api_context:
            # Login to get session - use API endpoint with JSON
            login_response = await api_context.post(f"{live_server.url}/api/v1/auth/login", json={
                'username': 'admin',
                'password': 'admin'
            })
            assert login_response.status == 200
            
            # Send heartbeat to trigger status change event
            response = await api_context.post(
                f"{live_server.url}/api/v1/displays/{self.display_id}/heartbeat",
                json={'resolution': '1920x1080'}
            )
            assert response.status == 200
        
        # Wait for notification to appear
        notification = self.page.locator('.toast')
        await expect(notification).to_be_visible(timeout=5000)
        await expect(notification).to_contain_text('Test Display is now online')

    async def test_sse_connection_status_indicator(self, live_server):
        """Test that SSE connection status is properly indicated."""
        
        # Navigate to admin dashboard and login
        await self.page.goto(f"{live_server.url}")
        await self.page.fill('[data-testid="username"]', 'admin')
        await self.page.fill('[data-testid="password"]', 'admin')
        await self.page.click('[data-testid="login-button"]')
        
        # Wait for dashboard
        await expect(self.page.locator('h1')).to_contain_text('Dashboard')
        
        # Check for SSE connection indicator
        # The LiveDataIndicator should show connection status
        connection_indicator = self.page.locator('[data-testid="sse-connection-status"]')
        if await connection_indicator.count() > 0:
            await expect(connection_indicator).to_contain_text('Connected')
        
        # Verify SSE events are working by checking console logs
        # The page should log SSE connection establishment
        console_messages = []
        self.page.on('console', lambda msg: console_messages.append(msg.text))
        
        # Wait a moment for SSE connection
        await self.page.wait_for_timeout(2000)
        
        # Check if SSE connection was established
        sse_connected = any('SSE connection established' in msg for msg in console_messages)
        assert sse_connected, f"SSE connection not established. Console: {console_messages}"


@pytest.mark.e2e
class TestSSEFallbackMechanisms:
    """Test SSE fallback mechanisms and error handling."""

    async def test_sse_reconnection_on_connection_loss(self, page: Page, live_server):
        """Test that SSE reconnects automatically after connection loss."""
        
        # Navigate to dashboard and login
        await page.goto(f"{live_server.url}")
        await page.fill('[data-testid="username"]', 'admin')
        await page.fill('[data-testid="password"]', 'admin')
        await page.click('[data-testid="login-button"]')
        
        # Wait for dashboard and initial SSE connection
        await expect(page.locator('h1')).to_contain_text('Dashboard')
        await page.wait_for_timeout(2000)
        
        # Set up console monitoring before navigation
        console_messages = []
        page.on('console', lambda msg: console_messages.append(msg.text))
        
        # Verify initial connection was established
        initial_connection_messages = [msg for msg in console_messages if 'SSE connection established' in msg]
        assert len(initial_connection_messages) > 0, f"Initial SSE connection not established. Console: {console_messages}"
        
        # Clear console messages to focus on reconnection
        console_messages.clear()
        
        # Simulate network interruption by navigating away and back
        await page.goto('about:blank')
        await page.wait_for_timeout(1000)
        
        # Navigate back to the app
        await page.goto(f"{live_server.url}")
        
        # Need to log in again since session was lost
        await page.fill('[data-testid="username"]', 'admin')
        await page.fill('[data-testid="password"]', 'admin')
        await page.click('[data-testid="login-button"]')
        
        # Wait for dashboard to load again
        await expect(page.locator('h1')).to_contain_text('Dashboard')
        
        # Wait for SSE reconnection with timeout
        max_wait_time = 10  # seconds
        start_time = time.time()
        reconnection_occurred = False
        
        while time.time() - start_time < max_wait_time:
            # Check recent console messages for reconnection
            recent_messages = console_messages[-10:] if len(console_messages) >= 10 else console_messages
            if any('SSE connection established' in msg for msg in recent_messages):
                reconnection_occurred = True
                break
            await page.wait_for_timeout(500)  # Check every 500ms
        
        # Verify reconnection occurred within timeout
        assert reconnection_occurred, f"SSE did not reconnect within {max_wait_time}s. Console: {console_messages[-10:]}"

    async def test_sse_error_handling(self, page: Page, live_server):
        """Test SSE error handling and user feedback."""
        
        # Navigate to dashboard and login
        await page.goto(f"{live_server.url}")
        await page.fill('[data-testid="username"]', 'admin')
        await page.fill('[data-testid="password"]', 'admin')
        await page.click('[data-testid="login-button"]')
        
        # Wait for dashboard
        await expect(page.locator('h1')).to_contain_text('Dashboard')
        
        # Monitor console for error handling
        console_messages = []
        page.on('console', lambda msg: console_messages.append(msg.text))
        
        # Wait for initial connection
        await page.wait_for_timeout(2000)
        
        # Check that no SSE errors are logged
        sse_errors = [msg for msg in console_messages if 'SSE' in msg and 'error' in msg.lower()]
        
        # Should be minimal or no errors in normal operation
        assert len(sse_errors) <= 1, f"Too many SSE errors: {sse_errors}"
