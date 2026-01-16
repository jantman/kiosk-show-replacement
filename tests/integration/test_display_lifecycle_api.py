"""
Integration tests for display lifecycle and configuration template API endpoints.

Tests cover:
- Display archive/restore API endpoints
- Display configuration template CRUD operations
- Template application to displays
- Bulk template application

INTEGRATION TEST APPROACH:
This file demonstrates the correct hybrid approach for integration testing:

1. **Database Setup**: Use direct database access (db_session, db_models fixtures) to create
   test data that needs to exist before the HTTP request. This allows precise control over
   the test setup and ensures the Flask server can see the data.

2. **HTTP Testing**: Use real HTTP requests (client fixture) to test the actual API endpoints.
   This tests the full HTTP layer including routing, authentication, serialization, etc.

3. **Database Isolation**: The db_session and db_models fixtures are configured to use the
   same database file as the running Flask server, ensuring data consistency between test
   setup and HTTP requests.

KEY FIXTURES USED:
- client: Real HTTP client that makes requests to the running Flask server
- auth_headers: Authentication headers for API requests
- admin_user/regular_user: User dictionaries (not objects) for test authentication
- db_session: SQLAlchemy session connected to the same database as Flask server
- db_models: Dictionary of model classes for creating test data

PATTERN TO FOLLOW:
1. Use db_session.add() and db_session.commit() to create test data
2. Use client.post/get/put/delete() to make HTTP requests
3. Assert on HTTP response status codes and JSON data
4. Use db_session queries to verify database state changes if needed

This approach gives us true integration testing - testing the real HTTP layer while
maintaining easy test data setup through direct database access.
"""

import uuid

import pytest


class TestDisplayArchiveAPI:
    """Test display archive and restore API endpoints."""

    def test_archive_display_success(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test successful display archiving."""
        # Create test display with unique name using direct database access
        unique_id = str(uuid.uuid4())[:8]
        display = db_models["Display"](
            name=f"Test Display Archive {unique_id}",
            description="Display to archive",
            location="Test Location",
            is_active=True,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()
        db_session.refresh(display)  # Ensure we have the latest data
        display_id = display.id

        # Test the archive functionality via HTTP API
        response = client.post(
            f"/api/v1/displays/{display_id}/archive", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Display archived successfully"
        assert data["data"]["is_archived"] is True
        assert data["data"]["archived_at"] is not None
        assert data["data"]["archived_by_id"] == admin_user["id"]
        assert data["data"]["is_active"] is False
        assert data["data"]["current_slideshow_id"] is None

    def test_archive_nonexistent_display(self, client, auth_headers):
        """Test archiving nonexistent display returns 404."""
        response = client.post("/api/v1/displays/99999/archive", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_archive_already_archived_display(self, client, auth_headers, admin_user):
        """Test archiving already archived display returns error."""
        # Create and archive a display via API
        unique_id = str(uuid.uuid4())[:8]
        display_data = {
            "name": f"Already Archived {unique_id}",
            "description": "Display to archive twice",
            "location": "Test Location",
            "is_active": True,
        }

        create_response = client.post(
            "/api/v1/displays", json=display_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        display_id = create_response.json()["data"]["id"]

        # First archive - should succeed
        archive_response = client.post(
            f"/api/v1/displays/{display_id}/archive", headers=auth_headers
        )
        assert archive_response.status_code == 200

        # Second archive - should fail
        response = client.post(
            f"/api/v1/displays/{display_id}/archive", headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "already archived" in data["error"].lower()

    def test_restore_display_success(self, client, auth_headers, admin_user):
        """Test successful display restoration."""
        # Create and archive a display via API
        unique_id = str(uuid.uuid4())[:8]
        display_data = {
            "name": f"Archived Display Restore Test {unique_id}",
            "description": "Display to archive then restore",
            "location": "Test Location",
            "is_active": True,
        }

        create_response = client.post(
            "/api/v1/displays", json=display_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        display_id = create_response.json()["data"]["id"]

        # Archive the display first
        archive_response = client.post(
            f"/api/v1/displays/{display_id}/archive", headers=auth_headers
        )
        assert archive_response.status_code == 200

        # Restore the display
        response = client.post(
            f"/api/v1/displays/{display_id}/restore", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Display restored successfully"
        assert data["data"]["is_archived"] is False
        assert data["data"]["archived_at"] is None
        assert data["data"]["archived_by_id"] is None
        assert data["data"]["is_active"] is True

    def test_restore_non_archived_display(self, client, auth_headers, admin_user):
        """Test restoring non-archived display returns error."""
        # Create active display via API
        unique_id = str(uuid.uuid4())[:8]
        display_data = {
            "name": f"Active Display {unique_id}",
            "description": "Display that is not archived",
            "location": "Test Location",
            "is_active": True,
        }

        create_response = client.post(
            "/api/v1/displays", json=display_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        display_id = create_response.json()["data"]["id"]

        response = client.post(
            f"/api/v1/displays/{display_id}/restore", headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "not archived" in data["error"].lower()

    def test_list_archived_displays(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test listing archived displays."""
        # Create mix of archived and active displays with unique names using direct database access
        unique_id = str(uuid.uuid4())[:8]

        archived_display1_name = f"Archived Display 1 {unique_id}"
        archived_display2_name = f"Archived Display 2 {unique_id}"
        active_display_name = f"Active Display List Test {unique_id}"

        active_display = db_models["Display"](
            name=active_display_name,
            is_active=True,
            is_archived=False,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        archived_display1 = db_models["Display"](
            name=archived_display1_name,
            is_active=False,
            is_archived=True,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        archived_display2 = db_models["Display"](
            name=archived_display2_name,
            is_active=False,
            is_archived=True,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )

        db_session.add_all([active_display, archived_display1, archived_display2])
        db_session.commit()

        response = client.get("/api/v1/displays/archived", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 2  # Only archived displays
        archived_names = [d["name"] for d in data["data"]]
        assert archived_display1_name in archived_names
        assert archived_display2_name in archived_names
        assert active_display_name not in archived_names


class TestDisplayTemplateAPI:
    """Test display configuration template API endpoints."""

    def test_create_template_success(self, client, auth_headers, admin_user):
        """Test creating a display configuration template."""
        template_data = {
            "name": "Office Template",
            "description": "Standard office display setup",
            "template_resolution_width": 1920,
            "template_resolution_height": 1080,
            "template_rotation": 0,
            "template_heartbeat_interval": 30,
            "template_location": "Office Building",
            "is_default": True,
        }

        response = client.post(
            "/api/v1/display-templates", json=template_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Display template created successfully"
        assert data["data"]["name"] == "Office Template"
        assert data["data"]["template_resolution_width"] == 1920
        assert data["data"]["template_resolution_height"] == 1080
        assert data["data"]["is_default"] is True
        assert data["data"]["owner_id"] == admin_user["id"]

    def test_create_template_duplicate_name(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test creating template with duplicate name fails."""
        # Create first template with unique base name
        unique_id = str(uuid.uuid4())[:8]
        template_name = f"Duplicate Name {unique_id}"
        template1 = db_models["DisplayConfigurationTemplate"](
            name=template_name,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template1)
        db_session.commit()

        # Try to create second template with same name
        template_data = {
            "name": template_name,
            "description": "This should fail",
        }

        response = client.post(
            "/api/v1/display-templates", json=template_data, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_create_template_missing_name(self, client, auth_headers):
        """Test creating template without name fails."""
        template_data = {
            "description": "Template without name",
        }

        response = client.post(
            "/api/v1/display-templates", json=template_data, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "name is required" in data["error"].lower()

    def test_list_templates(
        self, client, auth_headers, admin_user, regular_user, db_session, db_models
    ):
        """Test listing display templates."""
        # Create templates for different users
        admin_template = db_models["DisplayConfigurationTemplate"](
            name="Admin Template",
            description="Admin's template",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
            is_active=True,
        )
        user_template = db_models["DisplayConfigurationTemplate"](
            name="User Template",
            description="Regular user's template",
            owner_id=regular_user["id"],
            created_by_id=regular_user["id"],
            is_active=True,
        )
        inactive_template = db_models["DisplayConfigurationTemplate"](
            name="Inactive Template",
            description="Inactive template",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
            is_active=False,
        )

        db_session.add_all([admin_template, user_template, inactive_template])
        db_session.commit()

        response = client.get("/api/v1/display-templates", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # Should see the default template plus admin user's active templates
        assert len(data["data"]) == 2
        template_names = [t["name"] for t in data["data"]]
        assert "Admin Template" in template_names
        assert "Office Template" in template_names  # Default template

    def test_get_template_success(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test getting a specific template."""
        template = db_models["DisplayConfigurationTemplate"](
            name="Test Template Get",
            description="Template for testing",
            template_resolution_width=1920,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)
        db_session.commit()
        template_id = template.id

        response = client.get(
            f"/api/v1/display-templates/{template_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["name"] == "Test Template Get"
        assert data["data"]["template_resolution_width"] == 1920

    def test_get_template_access_denied(
        self, client, auth_headers, admin_user, regular_user, db_session, db_models
    ):
        """Test accessing another user's template is denied."""
        # Create template owned by regular user
        template = db_models["DisplayConfigurationTemplate"](
            name="Other User Template",
            owner_id=regular_user["id"],
            created_by_id=regular_user["id"],
        )
        db_session.add(template)
        db_session.commit()
        template_id = template.id

        # Try to access with admin user auth
        response = client.get(
            f"/api/v1/display-templates/{template_id}", headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "access denied" in data["error"].lower()

    def test_update_template_success(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test updating a display template."""
        template = db_models["DisplayConfigurationTemplate"](
            name="Original Name",
            description="Original description",
            template_resolution_width=800,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)
        db_session.commit()
        template_id = template.id

        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "template_resolution_width": 1920,
            "template_resolution_height": 1080,
        }

        response = client.put(
            f"/api/v1/display-templates/{template_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["description"] == "Updated description"
        assert data["data"]["template_resolution_width"] == 1920
        assert data["data"]["template_resolution_height"] == 1080
        assert data["data"]["updated_by_id"] == admin_user["id"]

    def test_delete_template_success(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test deleting a display template."""
        template = db_models["DisplayConfigurationTemplate"](
            name="Template to Delete",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)
        db_session.commit()
        template_id = template.id

        response = client.delete(
            f"/api/v1/display-templates/{template_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Template deleted successfully"

        # Verify template is deleted - refresh session to see latest state
        db_session.expire_all()  # Clear any cached objects
        deleted_template = db_session.get(
            db_models["DisplayConfigurationTemplate"], template_id
        )
        assert deleted_template is None


class TestTemplateApplication:
    """Test applying templates to displays."""

    def test_apply_template_to_display_success(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test applying a template to a display."""
        # Create template
        template = db_models["DisplayConfigurationTemplate"](
            name="Test Template Apply",
            template_resolution_width=1920,
            template_resolution_height=1080,
            template_rotation=90,
            template_heartbeat_interval=45,
            template_location="New Location",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)

        # Create display
        display = db_models["Display"](
            name="Test Display Apply Template",
            resolution_width=800,
            resolution_height=600,
            rotation=0,
            heartbeat_interval=60,
            location="Old Location",
            is_active=True,
            is_archived=False,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()

        response = client.post(
            f"/api/v1/displays/{display.id}/apply-template/{template.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Template applied successfully"

        # Check display was updated
        updated_display = data["data"]
        assert updated_display["resolution_width"] == 1920
        assert updated_display["resolution_height"] == 1080
        assert updated_display["rotation"] == 90
        assert updated_display["heartbeat_interval"] == 45
        assert updated_display["location"] == "New Location"

    def test_apply_template_to_archived_display_fails(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test applying template to archived display fails."""
        # Create template
        template = db_models["DisplayConfigurationTemplate"](
            name="Test Template Archived",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)

        # Create archived display
        display = db_models["Display"](
            name="Archived Display Template Test",
            is_active=False,
            is_archived=True,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()

        response = client.post(
            f"/api/v1/displays/{display.id}/apply-template/{template.id}",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "archived display" in data["error"].lower()

    def test_bulk_apply_template_success(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test bulk applying template to multiple displays."""
        # Create template
        template = db_models["DisplayConfigurationTemplate"](
            name="Bulk Template",
            template_resolution_width=1920,
            template_rotation=180,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)

        # Create multiple displays
        display1 = db_models["Display"](
            name="Display 1",
            resolution_width=800,
            rotation=0,
            is_active=True,
            is_archived=False,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        display2 = db_models["Display"](
            name="Display 2",
            resolution_width=1024,
            rotation=90,
            is_active=True,
            is_archived=False,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        archived_display = db_models["Display"](
            name="Archived Display",
            is_active=False,
            is_archived=True,
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )

        db_session.add_all([display1, display2, archived_display])
        db_session.commit()

        bulk_data = {
            "display_ids": [display1.id, display2.id, archived_display.id],
            "template_id": template.id,
        }

        response = client.post(
            "/api/v1/displays/bulk-apply-template", json=bulk_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["total_applied"] == 2  # Two successful
        assert data["data"]["total_failed"] == 1  # One failed (archived)

        # Check applied displays were updated
        applied_displays = data["data"]["applied_displays"]
        assert len(applied_displays) == 2
        for display_data in applied_displays:
            assert display_data["resolution_width"] == 1920
            assert display_data["rotation"] == 180

        # Check failed display info
        failed_displays = data["data"]["failed_displays"]
        assert len(failed_displays) == 1
        assert "archived" in failed_displays[0]["error"].lower()

    def test_bulk_apply_template_no_displays(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test bulk apply with no display IDs fails."""
        template = db_models["DisplayConfigurationTemplate"](
            name="Test Template",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(template)
        db_session.commit()

        bulk_data = {
            "display_ids": [],
            "template_id": template.id,
        }

        response = client.post(
            "/api/v1/displays/bulk-apply-template", json=bulk_data, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "no display ids" in data["error"].lower()
