"""
Unit tests for admin user management API endpoints.
"""

from kiosk_show_replacement.app import db
from kiosk_show_replacement.models import User


class TestListUsers:
    """Test GET /api/v1/admin/users endpoint."""

    def test_list_users_success(self, client, app):
        """Test admin can list all users."""
        with app.app_context():
            # Create admin user
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            # Create regular users
            user1 = User(username="user1", email="user1@example.com")
            user1.set_password("password")
            user2 = User(username="user2", email="user2@example.com")
            user2.set_password("password")

            db.session.add_all([admin, user1, user2])
            db.session.commit()

        # Login as admin
        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.get("/api/v1/admin/users")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 3  # admin + 2 users

    def test_list_users_non_admin_forbidden(self, client, app):
        """Test non-admin cannot list users."""
        with app.app_context():
            user = User(username="regular", email="regular@example.com")
            user.set_password("password")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()

        # Login as non-admin
        client.post(
            "/api/v1/auth/login",
            json={"username": "regular", "password": "password"},
        )

        response = client.get("/api/v1/admin/users")

        assert response.status_code == 403

    def test_list_users_unauthenticated(self, client):
        """Test unauthenticated request returns 401."""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401


class TestCreateUser:
    """Test POST /api/v1/admin/users endpoint."""

    def test_create_user_success(self, client, app):
        """Test admin can create a new user."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.post(
            "/api/v1/admin/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "is_admin": False,
            },
        )

        assert response.status_code == 201  # 201 Created for new resources
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "newuser@example.com"
        assert data["data"]["is_admin"] is False
        # Temporary password is returned
        assert "temporary_password" in data["data"]
        assert len(data["data"]["temporary_password"]) >= 8

        # Verify user can login with temp password
        with app.app_context():
            new_user = User.query.filter_by(username="newuser").first()
            assert new_user is not None
            assert new_user.check_password(data["data"]["temporary_password"])

    def test_create_user_duplicate_username(self, client, app):
        """Test creating user with duplicate username fails."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            existing = User(username="existing", email="existing@example.com")
            existing.set_password("password")

            db.session.add_all([admin, existing])
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.post(
            "/api/v1/admin/users",
            json={"username": "existing", "email": "new@example.com"},
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "already exists" in data["error"].lower()

    def test_create_user_duplicate_email(self, client, app):
        """Test creating user with duplicate email fails."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            existing = User(username="existing", email="taken@example.com")
            existing.set_password("password")

            db.session.add_all([admin, existing])
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.post(
            "/api/v1/admin/users",
            json={"username": "newuser", "email": "taken@example.com"},
        )

        assert response.status_code == 409
        data = response.get_json()
        assert "already in use" in data["error"].lower()

    def test_create_user_missing_username(self, client, app):
        """Test creating user without username fails."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.post(
            "/api/v1/admin/users",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Username is required" in data["error"]

    def test_create_user_non_admin_forbidden(self, client, app):
        """Test non-admin cannot create users."""
        with app.app_context():
            user = User(username="regular", email="regular@example.com")
            user.set_password("password")
            user.is_admin = False
            db.session.add(user)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "regular", "password": "password"},
        )

        response = client.post(
            "/api/v1/admin/users",
            json={"username": "newuser"},
        )

        assert response.status_code == 403


class TestGetUser:
    """Test GET /api/v1/admin/users/<id> endpoint."""

    def test_get_user_success(self, client, app):
        """Test admin can get user details."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            target = User(username="target", email="target@example.com")
            target.set_password("password")

            db.session.add_all([admin, target])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.get(f"/api/v1/admin/users/{target_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == "target"
        assert data["data"]["email"] == "target@example.com"

    def test_get_user_not_found(self, client, app):
        """Test getting non-existent user returns 404."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.get("/api/v1/admin/users/99999")

        assert response.status_code == 404


class TestUpdateUser:
    """Test PUT /api/v1/admin/users/<id> endpoint."""

    def test_update_user_email(self, client, app):
        """Test admin can update user email."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            target = User(username="target", email="old@example.com")
            target.set_password("password")

            db.session.add_all([admin, target])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            f"/api/v1/admin/users/{target_id}",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["email"] == "new@example.com"

    def test_update_user_is_admin(self, client, app):
        """Test admin can update user's admin status."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            target = User(username="target", email="target@example.com")
            target.set_password("password")
            target.is_admin = False

            db.session.add_all([admin, target])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            f"/api/v1/admin/users/{target_id}",
            json={"is_admin": True},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_admin"] is True

    def test_update_user_is_active(self, client, app):
        """Test admin can deactivate a user."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            target = User(username="target", email="target@example.com")
            target.set_password("password")
            target.is_active = True

            db.session.add_all([admin, target])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            f"/api/v1/admin/users/{target_id}",
            json={"is_active": False},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["is_active"] is False

    def test_cannot_change_own_admin_status(self, client, app):
        """Test admin cannot change their own admin status."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            f"/api/v1/admin/users/{admin_id}",
            json={"is_admin": False},
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "own admin status" in data["error"].lower()

    def test_cannot_deactivate_self(self, client, app):
        """Test admin cannot deactivate their own account."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            admin_id = admin.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            f"/api/v1/admin/users/{admin_id}",
            json={"is_active": False},
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "deactivate your own" in data["error"].lower()

    def test_update_user_email_conflict(self, client, app):
        """Test updating to an existing email fails."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            target = User(username="target", email="target@example.com")
            target.set_password("password")

            other = User(username="other", email="taken@example.com")
            other.set_password("password")

            db.session.add_all([admin, target, other])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            f"/api/v1/admin/users/{target_id}",
            json={"email": "taken@example.com"},
        )

        assert response.status_code == 409

    def test_update_user_not_found(self, client, app):
        """Test updating non-existent user returns 404."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.put(
            "/api/v1/admin/users/99999",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 404


class TestResetPassword:
    """Test POST /api/v1/admin/users/<id>/reset-password endpoint."""

    def test_reset_password_success(self, client, app):
        """Test admin can reset a user's password."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True

            target = User(username="target", email="target@example.com")
            target.set_password("oldpassword")

            db.session.add_all([admin, target])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.post(f"/api/v1/admin/users/{target_id}/reset-password")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "temporary_password" in data["data"]
        temp_password = data["data"]["temporary_password"]
        assert len(temp_password) >= 8

        # Verify the new password works
        with app.app_context():
            target_user = db.session.get(User, target_id)
            assert target_user.check_password(temp_password)
            assert not target_user.check_password("oldpassword")

    def test_reset_password_not_found(self, client, app):
        """Test resetting password for non-existent user returns 404."""
        with app.app_context():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("password")
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()

        client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "password"},
        )

        response = client.post("/api/v1/admin/users/99999/reset-password")

        assert response.status_code == 404

    def test_reset_password_non_admin_forbidden(self, client, app):
        """Test non-admin cannot reset passwords."""
        with app.app_context():
            regular = User(username="regular", email="regular@example.com")
            regular.set_password("password")
            regular.is_admin = False

            target = User(username="target", email="target@example.com")
            target.set_password("password")

            db.session.add_all([regular, target])
            db.session.commit()
            target_id = target.id

        client.post(
            "/api/v1/auth/login",
            json={"username": "regular", "password": "password"},
        )

        response = client.post(f"/api/v1/admin/users/{target_id}/reset-password")

        assert response.status_code == 403
