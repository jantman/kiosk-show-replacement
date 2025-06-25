"""
Integration tests for display lifecycle and configuration template API endpoints.

Tests cover:
- Display archive/restore API endpoints
- Display configuration template CRUD operations
- Template application to displays
- Bulk template application
"""

import json
import uuid

import pytest

from kiosk_show_replacement.models import Display, DisplayConfigurationTemplate, db


class TestDisplayArchiveAPI:
    """Test display archive and restore API endpoints."""

    def test_archive_display_success(self, client, auth_headers, admin_user):
        """Test successful display archiving."""
        # Create test display with unique name
        unique_id = str(uuid.uuid4())[:8]
        display = Display(
            name=f"Test Display Archive {unique_id}",
            description="Display to archive",
            is_active=True,
            is_archived=False,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(display)
        db.session.commit()
        display_id = display.id

        # Archive the display
        response = client.post(
            f"/api/v1/displays/{display_id}/archive",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["message"] == "Display archived successfully"
        assert data["data"]["is_archived"] is True
        assert data["data"]["archived_at"] is not None
        assert data["data"]["archived_by_id"] == admin_user.id
        assert data["data"]["is_active"] is False
        assert data["data"]["current_slideshow_id"] is None

    def test_archive_nonexistent_display(self, client, auth_headers):
        """Test archiving nonexistent display returns 404."""
        response = client.post(
            "/api/v1/displays/99999/archive",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_archive_already_archived_display(self, client, auth_headers, admin_user):
        """Test archiving already archived display returns error."""
        # Create already archived display with unique name
        unique_id = str(uuid.uuid4())[:8]
        display = Display(
            name=f"Already Archived {unique_id}",
            is_active=False,
            is_archived=True,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(display)
        db.session.commit()
        display_id = display.id

        response = client.post(
            f"/api/v1/displays/{display_id}/archive",
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "already archived" in data["error"].lower()

    def test_restore_display_success(self, client, auth_headers, admin_user):
        """Test successful display restoration."""
        # Create archived display with unique name
        unique_id = str(uuid.uuid4())[:8]
        display = Display(
            name=f"Archived Display Restore Test {unique_id}",
            is_active=False,
            is_archived=True,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(display)
        db.session.commit()
        display_id = display.id

        # Restore the display
        response = client.post(
            f"/api/v1/displays/{display_id}/restore",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["message"] == "Display restored successfully"
        assert data["data"]["is_archived"] is False
        assert data["data"]["archived_at"] is None
        assert data["data"]["archived_by_id"] is None
        assert data["data"]["is_active"] is True

    def test_restore_non_archived_display(self, client, auth_headers, admin_user):
        """Test restoring non-archived display returns error."""
        # Create active display with unique name
        unique_id = str(uuid.uuid4())[:8]
        display = Display(
            name=f"Active Display {unique_id}",
            is_active=True,
            is_archived=False,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(display)
        db.session.commit()
        display_id = display.id

        response = client.post(
            f"/api/v1/displays/{display_id}/restore",
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "not archived" in data["error"].lower()

    def test_list_archived_displays(self, client, auth_headers, admin_user):
        """Test listing archived displays."""
        # Create mix of archived and active displays with unique names
        unique_id = str(uuid.uuid4())[:8]
        active_display = Display(
            name=f"Active Display List Test {unique_id}",
            is_active=True,
            is_archived=False,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        archived_display1 = Display(
            name=f"Archived Display 1 {unique_id}",
            is_active=False,
            is_archived=True,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        archived_display2 = Display(
            name=f"Archived Display 2 {unique_id}",
            is_active=False,
            is_archived=True,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )

        db.session.add_all([active_display, archived_display1, archived_display2])
        db.session.commit()

        response = client.get("/api/v1/displays/archived", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert len(data["data"]) == 2  # Only archived displays
        archived_names = [d["name"] for d in data["data"]]
        assert "Archived Display 1" in archived_names
        assert "Archived Display 2" in archived_names
        assert "Active Display List Test" not in archived_names


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
            "/api/v1/display-templates",
            json=template_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["message"] == "Display template created successfully"
        assert data["data"]["name"] == "Office Template"
        assert data["data"]["template_resolution_width"] == 1920
        assert data["data"]["template_resolution_height"] == 1080
        assert data["data"]["is_default"] is True
        assert data["data"]["owner_id"] == admin_user.id

    def test_create_template_duplicate_name(self, client, auth_headers, admin_user):
        """Test creating template with duplicate name fails."""
        # Create first template with unique base name
        unique_id = str(uuid.uuid4())[:8]
        template_name = f"Duplicate Name {unique_id}"
        template1 = DisplayConfigurationTemplate(
            name=template_name,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template1)
        db.session.commit()

        # Try to create second template with same name
        template_data = {
            "name": template_name,
            "description": "This should fail",
        }

        response = client.post(
            "/api/v1/display-templates",
            json=template_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_create_template_missing_name(self, client, auth_headers):
        """Test creating template without name fails."""
        template_data = {
            "description": "Template without name",
        }

        response = client.post(
            "/api/v1/display-templates",
            json=template_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "name is required" in data["error"].lower()

    def test_list_templates(self, client, auth_headers, admin_user, regular_user):
        """Test listing display templates."""
        # Create templates for different users
        admin_template = DisplayConfigurationTemplate(
            name="Admin Template",
            description="Admin's template",
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
            is_active=True,
        )
        user_template = DisplayConfigurationTemplate(
            name="User Template",
            description="Regular user's template",
            owner_id=regular_user.id,
            created_by_id=regular_user.id,
            is_active=True,
        )
        inactive_template = DisplayConfigurationTemplate(
            name="Inactive Template",
            description="Inactive template",
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
            is_active=False,
        )

        db.session.add_all([admin_template, user_template, inactive_template])
        db.session.commit()

        response = client.get("/api/v1/display-templates", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        # Should only see admin user's active templates
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Admin Template"

    def test_get_template_success(self, client, auth_headers, admin_user):
        """Test getting a specific template."""
        template = DisplayConfigurationTemplate(
            name="Test Template Get",
            description="Template for testing",
            template_resolution_width=1920,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)
        db.session.commit()
        template_id = template.id

        response = client.get(
            f"/api/v1/display-templates/{template_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["name"] == "Test Template"
        assert data["data"]["template_resolution_width"] == 1920

    def test_get_template_access_denied(self, client, auth_headers, admin_user, regular_user):
        """Test accessing another user's template is denied."""
        # Create template owned by regular user
        template = DisplayConfigurationTemplate(
            name="Other User Template",
            owner_id=regular_user.id,
            created_by_id=regular_user.id,
        )
        db.session.add(template)
        db.session.commit()
        template_id = template.id

        # Try to access with admin user auth
        response = client.get(
            f"/api/v1/display-templates/{template_id}",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["success"] is False
        assert "access denied" in data["error"].lower()

    def test_update_template_success(self, client, auth_headers, admin_user):
        """Test updating a display template."""
        template = DisplayConfigurationTemplate(
            name="Original Name",
            description="Original description",
            template_resolution_width=800,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)
        db.session.commit()
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
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["description"] == "Updated description"
        assert data["data"]["template_resolution_width"] == 1920
        assert data["data"]["template_resolution_height"] == 1080
        assert data["data"]["updated_by_id"] == admin_user.id

    def test_delete_template_success(self, client, auth_headers, admin_user):
        """Test deleting a display template."""
        template = DisplayConfigurationTemplate(
            name="Template to Delete",
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)
        db.session.commit()
        template_id = template.id

        response = client.delete(
            f"/api/v1/display-templates/{template_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["message"] == "Template deleted successfully"

        # Verify template is deleted
        deleted_template = db.session.get(DisplayConfigurationTemplate, template_id)
        assert deleted_template is None


class TestTemplateApplication:
    """Test applying templates to displays."""

    def test_apply_template_to_display_success(self, client, auth_headers, admin_user):
        """Test applying a template to a display."""
        # Create template
        template = DisplayConfigurationTemplate(
            name="Test Template Apply",
            template_resolution_width=1920,
            template_resolution_height=1080,
            template_rotation=90,
            template_heartbeat_interval=45,
            template_location="New Location",
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)

        # Create display
        display = Display(
            name="Test Display Apply Template",
            resolution_width=800,
            resolution_height=600,
            rotation=0,
            heartbeat_interval=60,
            location="Old Location",
            is_active=True,
            is_archived=False,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(display)
        db.session.commit()

        response = client.post(
            f"/api/v1/displays/{display.id}/apply-template/{template.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["message"] == "Template applied successfully"
        
        # Check display was updated
        updated_display = data["data"]
        assert updated_display["resolution_width"] == 1920
        assert updated_display["resolution_height"] == 1080
        assert updated_display["rotation"] == 90
        assert updated_display["heartbeat_interval"] == 45
        assert updated_display["location"] == "New Location"

    def test_apply_template_to_archived_display_fails(self, client, auth_headers, admin_user):
        """Test applying template to archived display fails."""
        # Create template
        template = DisplayConfigurationTemplate(
            name="Test Template Archived",
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)

        # Create archived display
        display = Display(
            name="Archived Display Template Test",
            is_active=False,
            is_archived=True,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(display)
        db.session.commit()

        response = client.post(
            f"/api/v1/displays/{display.id}/apply-template/{template.id}",
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "archived display" in data["error"].lower()

    def test_bulk_apply_template_success(self, client, auth_headers, admin_user):
        """Test bulk applying template to multiple displays."""
        # Create template
        template = DisplayConfigurationTemplate(
            name="Bulk Template",
            template_resolution_width=1920,
            template_rotation=180,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)

        # Create multiple displays
        display1 = Display(
            name="Display 1",
            resolution_width=800,
            rotation=0,
            is_active=True,
            is_archived=False,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        display2 = Display(
            name="Display 2",
            resolution_width=1024,
            rotation=90,
            is_active=True,
            is_archived=False,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        archived_display = Display(
            name="Archived Display",
            is_active=False,
            is_archived=True,
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )

        db.session.add_all([display1, display2, archived_display])
        db.session.commit()

        bulk_data = {
            "display_ids": [display1.id, display2.id, archived_display.id],
            "template_id": template.id,
        }

        response = client.post(
            "/api/v1/displays/bulk-apply-template",
            json=bulk_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["total_applied"] == 2  # Two successful
        assert data["data"]["total_failed"] == 1   # One failed (archived)
        
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

    def test_bulk_apply_template_no_displays(self, client, auth_headers, admin_user):
        """Test bulk apply with no display IDs fails."""
        template = DisplayConfigurationTemplate(
            name="Test Template",
            owner_id=admin_user.id,
            created_by_id=admin_user.id,
        )
        db.session.add(template)
        db.session.commit()

        bulk_data = {
            "display_ids": [],
            "template_id": template.id,
        }

        response = client.post(
            "/api/v1/displays/bulk-apply-template",
            json=bulk_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "no display ids" in data["error"].lower()
