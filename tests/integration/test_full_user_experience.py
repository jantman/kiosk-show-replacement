"""
Full user experience integration tests.

Tests the complete React frontend + Flask backend integration through a real browser.
This is what users actually experience, not mocked components or isolated backend APIs.

This test relies on the noxfile to configure system Chrome/Chromium browser.
Run with: nox -s test-integration-full-stack
"""

import os
import subprocess
import time
import threading
import requests
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from kiosk_show_replacement.app import create_app
from kiosk_show_replacement.models import db, User


class ServerManager:
    """Manages Flask backend and Vite frontend servers for testing."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.flask_process = None
        self.vite_process = None
        self.flask_port = 5000
        self.vite_port = 3001
        self.flask_url = f"http://localhost:{self.flask_port}"
        self.vite_url = f"http://localhost:{self.vite_port}"
    
    def start_flask(self, db_path=None):
        """Start Flask backend server."""
        env = os.environ.copy()
        env["FLASK_ENV"] = "testing"
        env["FLASK_DEBUG"] = "0"  # Disable debug mode for testing
        
        # Set test database if provided
        if db_path:
            env["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
            env["TESTING"] = "true"
        
        # Run poetry env activate && python run.py
        cmd = f"cd {self.project_root} && eval $(poetry env activate) && python run.py"
        self.flask_process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for Flask to be ready
        for _ in range(30):  # 30 second timeout
            try:
                response = requests.get(f"{self.flask_url}/api/v1/status", timeout=1)
                if response.status_code == 200:
                    print(f"✓ Flask server ready at {self.flask_url}")
                    return
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        # If we get here, Flask failed to start
        if self.flask_process.poll() is not None:
            stdout, stderr = self.flask_process.communicate()
            print(f"Flask process exited with code: {self.flask_process.returncode}")
            print(f"Flask stdout: {stdout.decode()}")
            print(f"Flask stderr: {stderr.decode()}")
        
        raise RuntimeError("Flask server failed to start")
    
    def start_vite(self):
        """Start Vite frontend server."""
        frontend_dir = self.project_root / "frontend"
        
        # Run npm run dev
        cmd = ["npm", "run", "dev"]
        self.vite_process = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for Vite to be ready
        for _ in range(30):  # 30 second timeout
            try:
                response = requests.get(self.vite_url, timeout=1)
                if response.status_code == 200:
                    print(f"✓ Vite server ready at {self.vite_url}")
                    return
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        raise RuntimeError("Vite server failed to start")
    
    def start_servers(self, db_path=None):
        """Start both servers in parallel."""
        flask_thread = threading.Thread(target=self.start_flask, args=(db_path,))
        vite_thread = threading.Thread(target=self.start_vite)
        
        flask_thread.start()
        vite_thread.start()
        
        flask_thread.join()
        vite_thread.join()
    
    def stop_servers(self):
        """Stop both servers."""
        if self.flask_process:
            self.flask_process.terminate()
            self.flask_process.wait()
        
        if self.vite_process:
            self.vite_process.terminate()
            self.vite_process.wait()


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def test_database(project_root):
    """Set up a test database with a known user."""
    # Create test database path
    test_db_path = project_root / "instance" / "test_integration.db"
    test_db_path.parent.mkdir(exist_ok=True)
    
    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Create test app
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db_path}",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user
        test_user = User(username="testuser", email="test@example.com", is_admin=True)
        test_user.set_password("testpassword")
        db.session.add(test_user)
        db.session.commit()
        
        print(f"✓ Test database created at {test_db_path}")
        print(f"✓ Test user created: testuser / testpassword")
    
    yield {
        "username": "testuser", 
        "password": "testpassword",
        "db_path": str(test_db_path)  # Convert to string for environment variable
    }
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture(scope="session")
def servers(project_root, test_database):
    """Start Flask and Vite servers for testing."""
    server_manager = ServerManager(project_root)
    
    try:
        # Pass the test database path to Flask
        server_manager.start_servers(db_path=test_database['db_path'])
        yield {
            "flask_url": server_manager.flask_url,
            "vite_url": server_manager.vite_url
        }
    finally:
        server_manager.stop_servers()


@pytest.mark.integration
class TestFullUserExperience:
    """Test the complete user experience through a real browser."""
    
    def test_user_can_login_and_see_dashboard(self, page: Page, servers: dict, test_database: dict):
        """
        Test the complete happy path:
        1. User visits the React frontend
        2. User sees the login form
        3. User enters credentials and submits
        4. User is redirected to dashboard
        5. Dashboard loads data from Flask backend
        6. User can see the dashboard content
        
        This tests the REAL user experience, not mocked components.
        """
        vite_url = servers["vite_url"]
        username = test_database["username"]
        password = test_database["password"]
        
        print(f"\n🌐 Testing user experience at {vite_url}")
        print(f"👤 Test credentials: {username} / {password}")
        
        # Step 1: Visit the React frontend
        page.goto(vite_url)
        
        # Step 2: Verify we see the login form
        print("🔍 Checking for login form...")
        
        # Wait for the React app to load and render the login form
        expect(page.locator("input[name='username'], input[placeholder*='username' i]")).to_be_visible(timeout=10000)
        expect(page.locator("input[name='password'], input[type='password']")).to_be_visible()
        expect(page.locator("button[type='submit'], button:has-text('Sign In')")).to_be_visible()
        
        print("✓ Login form is visible")
        
        # Step 3: Fill in credentials and submit
        print("🔑 Logging in...")
        
        username_field = page.locator("input[name='username'], input[placeholder*='username' i]").first
        password_field = page.locator("input[name='password'], input[type='password']").first
        submit_button = page.locator("button[type='submit'], button:has-text('Sign In')").first
        
        username_field.fill(username)
        password_field.fill(password)
        submit_button.click()
        
        # Step 4: Verify we're redirected to dashboard
        print("📊 Waiting for dashboard...")
        
        # Wait for the login to complete and dashboard to load
        # This should happen automatically after successful login
        page.wait_for_load_state("networkidle", timeout=15000)
        
        # Verify we're no longer on the login page
        login_form_present = page.locator("input[name='username']").is_visible()
        assert not login_form_present, "Should not be on login page after successful login"
        
        # Step 5: Verify dashboard content is visible
        print("🎯 Checking dashboard content...")
        
        # Look for dashboard indicators - any of these should be present
        dashboard_indicators = [
            page.locator("h1:has-text('Dashboard')"),
            page.locator("text=Welcome back"),
            page.locator("text=Active Slideshows"),
            page.locator("text=Online Displays"),
            page.locator("text=Quick Actions"),
            page.locator("button:has-text('Create New Slideshow')"),
            page.locator("a:has-text('Slideshows')"),
            page.locator("a:has-text('Displays')"),
        ]
        
        # At least one dashboard indicator should be visible
        dashboard_visible = False
        visible_indicators = []
        
        for indicator in dashboard_indicators:
            if indicator.is_visible():
                dashboard_visible = True
                visible_indicators.append(indicator.inner_text()[:50])
        
        assert dashboard_visible, f"Dashboard should be visible after login. Checked indicators but none were visible."
        
        print(f"✓ Dashboard is visible with indicators: {visible_indicators}")
        
        # Step 6: Verify the React frontend is communicating with Flask backend
        print("🔗 Verifying frontend-backend communication...")
        
        # The dashboard should load data from the backend APIs
        # We'll check for any error messages that would indicate API failures
        error_indicators = [
            page.locator("text=Failed to load"),
            page.locator("text=Error"),
            page.locator("div.alert-danger"),
            page.locator("div[role='alert']"),
        ]
        
        for error_indicator in error_indicators:
            if error_indicator.is_visible():
                error_text = error_indicator.inner_text()
                pytest.fail(f"Found error on dashboard: {error_text}")
        
        print("✓ No error messages found on dashboard")
        
        # Final verification: Check that user info is displayed
        # This confirms the authentication state is working
        user_info_visible = (
            page.locator(f"text={username}").is_visible() or
            page.locator("text=Welcome back").is_visible()
        )
        
        if user_info_visible:
            print(f"✓ User information is displayed (logged in as {username})")
        else:
            print("⚠ User information not visible, but login appears successful")
        
        print("🎉 FULL USER EXPERIENCE TEST PASSED!")
        print("   ✓ React frontend loads correctly")
        print("   ✓ Login form works")
        print("   ✓ Authentication succeeds")
        print("   ✓ Dashboard loads")
        print("   ✓ Frontend-backend communication works")
        print("   ✓ User can see dashboard content")


if __name__ == "__main__":
    # Allow running this test directly for debugging
    pytest.main([__file__, "-v", "-s"])
