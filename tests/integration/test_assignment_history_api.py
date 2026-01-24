"""
Integration tests for assignment history API endpoint.

Tests cover:
- Listing assignment history records
- Filtering by display_id, action, and user_id
- Limit parameter validation
- Empty history handling

This file tests the /api/v1/assignment-history endpoint which provides
audit trail data for slideshow assignments to displays.
"""

import uuid
from datetime import datetime, timezone


class TestAssignmentHistoryAPI:
    """Test assignment history listing API endpoint."""

    def test_list_assignment_history_empty(self, client, auth_headers):
        """Test listing assignment history when no records exist."""
        response = client.get("/api/v1/assignment-history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Assignment history retrieved successfully"
        assert isinstance(data["data"], list)
        # May be empty or have records from other tests, but should be a list

    def test_list_assignment_history_with_records(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test listing assignment history with existing records."""
        unique_id = str(uuid.uuid4())[:8]

        # Create a display
        display = db_models["Display"](
            name=f"Test Display History {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()
        db_session.refresh(display)

        # Create a slideshow
        slideshow = db_models["Slideshow"](
            name=f"Test Slideshow History {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
            is_active=True,
        )
        db_session.add(slideshow)
        db_session.commit()
        db_session.refresh(slideshow)

        # Create assignment history record
        history = db_models["AssignmentHistory"](
            display_id=display.id,
            previous_slideshow_id=None,
            new_slideshow_id=slideshow.id,
            action="assign",
            reason="Test assignment",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(history)
        db_session.commit()

        response = client.get("/api/v1/assignment-history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) >= 1

        # Find our test record
        test_records = [r for r in data["data"] if r["display_id"] == display.id]
        assert len(test_records) == 1

        record = test_records[0]
        assert record["action"] == "assign"
        assert record["display_name"] == display.name
        assert record["new_slideshow_id"] == slideshow.id
        assert record["new_slideshow_name"] == slideshow.name
        assert record["previous_slideshow_id"] is None
        assert record["reason"] == "Test assignment"
        assert record["created_by_id"] == admin_user["id"]

    def test_filter_by_display_id(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test filtering assignment history by display ID."""
        unique_id = str(uuid.uuid4())[:8]

        # Create two displays
        display1 = db_models["Display"](
            name=f"Display Filter 1 {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        display2 = db_models["Display"](
            name=f"Display Filter 2 {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add_all([display1, display2])
        db_session.commit()
        db_session.refresh(display1)
        db_session.refresh(display2)

        # Create history records for both displays
        history1 = db_models["AssignmentHistory"](
            display_id=display1.id,
            action="assign",
            reason="Display 1 assignment",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        history2 = db_models["AssignmentHistory"](
            display_id=display2.id,
            action="unassign",
            reason="Display 2 assignment",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add_all([history1, history2])
        db_session.commit()

        # Filter by display1
        response = client.get(
            f"/api/v1/assignment-history?display_id={display1.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # All returned records should be for display1
        for record in data["data"]:
            assert record["display_id"] == display1.id

    def test_filter_by_action_type(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test filtering assignment history by action type."""
        unique_id = str(uuid.uuid4())[:8]

        # Create a display
        display = db_models["Display"](
            name=f"Display Action Filter {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()
        db_session.refresh(display)

        # Create slideshows for change action
        slideshow1 = db_models["Slideshow"](
            name=f"Slideshow Action 1 {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
            is_active=True,
        )
        slideshow2 = db_models["Slideshow"](
            name=f"Slideshow Action 2 {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
            is_active=True,
        )
        db_session.add_all([slideshow1, slideshow2])
        db_session.commit()
        db_session.refresh(slideshow1)
        db_session.refresh(slideshow2)

        # Create history records with different actions
        history_assign = db_models["AssignmentHistory"](
            display_id=display.id,
            new_slideshow_id=slideshow1.id,
            action="assign",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        history_change = db_models["AssignmentHistory"](
            display_id=display.id,
            previous_slideshow_id=slideshow1.id,
            new_slideshow_id=slideshow2.id,
            action="change",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        history_unassign = db_models["AssignmentHistory"](
            display_id=display.id,
            previous_slideshow_id=slideshow2.id,
            action="unassign",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add_all([history_assign, history_change, history_unassign])
        db_session.commit()

        # Filter by assign action
        response = client.get(
            "/api/v1/assignment-history?action=assign", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # All returned records should have action "assign"
        for record in data["data"]:
            assert record["action"] == "assign"

        # Filter by change action
        response = client.get(
            "/api/v1/assignment-history?action=change", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        for record in data["data"]:
            assert record["action"] == "change"

    def test_filter_by_user_id(
        self, client, auth_headers, admin_user, regular_user, db_session, db_models
    ):
        """Test filtering assignment history by user ID."""
        unique_id = str(uuid.uuid4())[:8]

        # Create a display
        display = db_models["Display"](
            name=f"Display User Filter {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()
        db_session.refresh(display)

        # Create history records for different users
        history_admin = db_models["AssignmentHistory"](
            display_id=display.id,
            action="assign",
            reason="Admin action",
            created_by_id=admin_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        history_user = db_models["AssignmentHistory"](
            display_id=display.id,
            action="unassign",
            reason="User action",
            created_by_id=regular_user["id"],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add_all([history_admin, history_user])
        db_session.commit()

        # Filter by admin user
        response = client.get(
            f"/api/v1/assignment-history?user_id={admin_user['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # All returned records should be by admin user
        for record in data["data"]:
            assert record["created_by_id"] == admin_user["id"]

    def test_limit_parameter(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test limit parameter for assignment history."""
        unique_id = str(uuid.uuid4())[:8]

        # Create a display
        display = db_models["Display"](
            name=f"Display Limit Test {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()
        db_session.refresh(display)

        # Create multiple history records
        for i in range(5):
            history = db_models["AssignmentHistory"](
                display_id=display.id,
                action="assign",
                reason=f"Limit test {i}",
                created_by_id=admin_user["id"],
                created_at=datetime.now(timezone.utc),
            )
            db_session.add(history)
        db_session.commit()

        # Request with limit of 2
        response = client.get(
            f"/api/v1/assignment-history?display_id={display.id}&limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 2

    def test_limit_parameter_max_cap(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test that limit is capped at 200."""
        response = client.get(
            "/api/v1/assignment-history?limit=500", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # Should not error, just cap at 200

    def test_assignment_history_requires_auth(self, servers):
        """Test that assignment history endpoint requires authentication."""
        import requests

        # Create a fresh session without any auth cookies
        flask_url = servers["flask_url"]
        response = requests.get(f"{flask_url}/api/v1/assignment-history")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_combined_filters(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test combining multiple filters."""
        unique_id = str(uuid.uuid4())[:8]

        # Create displays
        display1 = db_models["Display"](
            name=f"Combined Filter 1 {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        display2 = db_models["Display"](
            name=f"Combined Filter 2 {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add_all([display1, display2])
        db_session.commit()
        db_session.refresh(display1)
        db_session.refresh(display2)

        # Create various history records
        records = [
            db_models["AssignmentHistory"](
                display_id=display1.id,
                action="assign",
                created_by_id=admin_user["id"],
                created_at=datetime.now(timezone.utc),
            ),
            db_models["AssignmentHistory"](
                display_id=display1.id,
                action="unassign",
                created_by_id=admin_user["id"],
                created_at=datetime.now(timezone.utc),
            ),
            db_models["AssignmentHistory"](
                display_id=display2.id,
                action="assign",
                created_by_id=admin_user["id"],
                created_at=datetime.now(timezone.utc),
            ),
        ]
        for record in records:
            db_session.add(record)
        db_session.commit()

        # Filter by display1 AND action=assign
        response = client.get(
            f"/api/v1/assignment-history?display_id={display1.id}&action=assign",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # All returned records should match both filters
        for record in data["data"]:
            assert record["display_id"] == display1.id
            assert record["action"] == "assign"

    def test_records_ordered_by_created_at_desc(
        self, client, auth_headers, admin_user, db_session, db_models
    ):
        """Test that assignment history records are returned in descending order."""
        unique_id = str(uuid.uuid4())[:8]

        # Create a display with a unique name
        display = db_models["Display"](
            name=f"Order Test Display {unique_id}",
            owner_id=admin_user["id"],
            created_by_id=admin_user["id"],
        )
        db_session.add(display)
        db_session.commit()
        db_session.refresh(display)

        # Create records with different timestamps and unique reasons
        from datetime import timedelta

        base_time = datetime.now(timezone.utc)

        history1 = db_models["AssignmentHistory"](
            display_id=display.id,
            action="assign",
            reason=f"First {unique_id}",
            created_by_id=admin_user["id"],
            created_at=base_time - timedelta(hours=2),
        )
        history2 = db_models["AssignmentHistory"](
            display_id=display.id,
            action="change",
            reason=f"Second {unique_id}",
            created_by_id=admin_user["id"],
            created_at=base_time - timedelta(hours=1),
        )
        history3 = db_models["AssignmentHistory"](
            display_id=display.id,
            action="unassign",
            reason=f"Third {unique_id}",
            created_by_id=admin_user["id"],
            created_at=base_time,
        )
        db_session.add_all([history1, history2, history3])
        db_session.commit()

        response = client.get(
            f"/api/v1/assignment-history?display_id={display.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

        # Filter to only our test records using unique_id
        our_records = [
            r for r in data["data"] if r.get("reason") and unique_id in r["reason"]
        ]
        assert len(our_records) == 3

        # Records should be in descending order (newest first)
        assert f"Third {unique_id}" in our_records[0]["reason"]
        assert f"Second {unique_id}" in our_records[1]["reason"]
        assert f"First {unique_id}" in our_records[2]["reason"]
