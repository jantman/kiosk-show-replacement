# Add Real Authentication

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Until now this project has used a very permissive authentication method where any username and password was accepted and the user was added to the database at first login; this was intended only for early development of the project and it's now time to add "real" user authentication to the application. We still want to keep username/password auth, we just want to disable the automatic creation of users. The new auth process that we'd like is:

1. Users can change their own passwords and email addresses via the admin UI.
2. Users who have `is_admin` set to True can access a new "Manage Users" page in the admin UI that lets them:
   1. Add a new user by specifying the username and email address; an 8-character random alphanumeric password will be generated in the UI, and displayed so they can send it to the new user. This user can be created as an admin or not (default).
   2. Reset the password of any existing user to a new random password, which they will be shown (to send to the user).
   3. Activate and deactivate users.
   4. Set or unset `is_admin` for other users.
3. Only users that are active can log in.
4. All users can edit all slideshows, slides, and displays (current behavior); only admins can manage users.
5. When a new database is first initialized for the application (i.e. empty database with no users) we must create a single initial admin user with username `admin`, password `admin`, and an email address of `admin@example.com`; the installation and deployment guides must be updated to include the very important necessity of changing the password and email address for this user once installation is complete (or, even better, creating admin user accounts for all people that need them and then deactivating the default `admin` user).

Unit and integration tests must be added/updated to cover this new functionality. Integration tests must be added to verify all user flows described above.

We will need to also update all documentation to take these changes into account (`README.md`, `CLAUDE.md`, `docs/*.rst`).

---

## Implementation Plan

### Current State Analysis

**Backend:**
- User model (`kiosk_show_replacement/models/__init__.py`) already has: `username`, `email`, `password_hash`, `is_active`, `is_admin`, `created_at`, `updated_at`, `last_login_at`, `created_by_id`, `updated_by_id`
- Password hashing uses werkzeug's PBKDF2-SHA256 via `set_password()` and `check_password()`
- Auth views (`kiosk_show_replacement/auth/views.py`) has permissive auth in `_get_or_create_user()` that accepts any credentials
- Auth decorators: `@login_required` and `@admin_required` exist
- Exceptions (`kiosk_show_replacement/exceptions.py`) already has `AuthenticationError` (401) and `AuthorizationError` (403)

**Frontend:**
- Login page: `frontend/src/pages/Login.tsx`
- AuthContext: `frontend/src/contexts/AuthContext.tsx`
- Navigation: `frontend/src/components/Navigation.tsx` with user dropdown
- API client: `frontend/src/utils/apiClient.ts`
- Types: `frontend/src/types/index.ts`

---

### Milestone 1: Backend - Real Authentication Logic
**Prefix**: `Real Auth - 1`

Disable auto-user creation and enforce credential validation.

#### Task 1.1: Modify API Login Endpoint
**File**: `kiosk_show_replacement/api/v1.py` (lines ~1820-1980)

Replace permissive logic with:
1. Query user by username
2. Return 401 if user not found or password incorrect
3. Return 403 if user is inactive (`is_active=False`)
4. On success: update `last_login_at`, set session

#### Task 1.2: Modify Web Login View
**File**: `kiosk_show_replacement/auth/views.py`

Replace `_get_or_create_user()` with `_authenticate_user()` that only validates credentials (no creation, no password updates).

#### Task 1.3: Update Default Admin User in Database Init
**File**: `kiosk_show_replacement/cli/init_db.py`

Set default email to `admin@example.com` (line 121, change `default=None` to `default="admin@example.com"`).

#### Task 1.4: Unit Tests for Authentication Changes
**File**: `tests/unit/test_auth.py`

Update/add tests:
- Login fails for non-existent user (401)
- Login fails for wrong password (401)
- Login fails for inactive user (403)
- Login succeeds for valid active user
- Session created correctly on success

---

### Milestone 2: User Self-Service API
**Prefix**: `Real Auth - 2`

Allow users to update their own email and password.

#### Task 2.1: Create Profile API Endpoints
**File**: `kiosk_show_replacement/api/v1.py`

Add endpoints:
- `PUT /api/v1/auth/profile` - Update email
- `PUT /api/v1/auth/password` - Change password (requires current password)

#### Task 2.2: Unit Tests for Profile Endpoints
**File**: `tests/unit/test_auth.py` or new `tests/unit/test_user_profile.py`

Tests:
- Update email successfully
- Update email fails if already used by another user
- Change password successfully
- Change password fails with wrong current password
- Unauthenticated requests return 401

---

### Milestone 3: Admin User Management API
**Prefix**: `Real Auth - 3`

Allow admins to create and manage users.

#### Task 3.1: Create Password Generator Utility
**File**: `kiosk_show_replacement/utils.py` (new file)

```python
import secrets
import string

def generate_random_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```

#### Task 3.2: Create Admin User Management Endpoints
**File**: `kiosk_show_replacement/api/v1.py`

Add endpoints (all require admin):
- `GET /api/v1/admin/users` - List all users
- `POST /api/v1/admin/users` - Create user (returns temp password)
- `GET /api/v1/admin/users/<id>` - Get user details
- `PUT /api/v1/admin/users/<id>` - Update user (email, is_admin, is_active)
- `POST /api/v1/admin/users/<id>/reset-password` - Reset password (returns new temp password)

Security rules:
- Cannot change own `is_admin` status
- Cannot deactivate self

#### Task 3.3: Unit Tests for Admin Endpoints
**File**: `tests/unit/test_user_management.py` (new file)

Tests:
- List users (admin only)
- Create user with auto-generated password
- Create user fails for duplicate username
- Update user email/is_admin/is_active
- Cannot change own admin status (403)
- Cannot deactivate self (403)
- Reset password returns new password
- Non-admin gets 403

---

### Milestone 4: Frontend - Profile Settings Page
**Prefix**: `Real Auth - 4`

Allow users to change their email and password via UI.

#### Task 4.1: Add Profile API Methods
**File**: `frontend/src/utils/apiClient.ts`

Add methods: `updateProfile()`, `changePassword()`

#### Task 4.2: Update TypeScript Types
**File**: `frontend/src/types/index.ts`

Add: `ProfileUpdateData`, `PasswordChangeData` interfaces

#### Task 4.3: Create Profile Page Component
**File**: `frontend/src/pages/Profile.tsx` (new file)

Two sections:
1. Profile info form (email)
2. Change password form (current password, new password, confirm)

#### Task 4.4: Add Route and Navigation
**Files**:
- `frontend/src/App.tsx` - Add route `profile`
- `frontend/src/components/Navigation.tsx` - Add "Profile Settings" to user dropdown

#### Task 4.5: Update Login Page
**File**: `frontend/src/pages/Login.tsx`

Remove the "Note: Any username and password combination is accepted" message.

---

### Milestone 5: Frontend - Admin User Management Page
**Prefix**: `Real Auth - 5`

Admin page to create, list, and manage users.

#### Task 5.1: Add Admin API Methods
**File**: `frontend/src/utils/apiClient.ts`

Add methods: `getUsers()`, `getUser()`, `createUser()`, `updateUser()`, `resetUserPassword()`

#### Task 5.2: Update User Type
**File**: `frontend/src/types/index.ts`

Add `is_active` field to User interface. Add `UserWithPassword` interface.

#### Task 5.3: Create User Management Page
**File**: `frontend/src/pages/UserManagement.tsx` (new file)

Features:
- User table with columns: username, email, admin badge, active status, last login
- Create user button → modal with username/email/is_admin fields → shows temp password
- Edit user button → modal for email/is_admin/is_active
- Reset password button → confirmation → shows new password
- Inactive users shown with muted styling

#### Task 5.4: Add Route and Navigation (Admin Only)
**Files**:
- `frontend/src/App.tsx` - Add route `users`
- `frontend/src/components/Navigation.tsx` - Add "User Management" nav link (admin only)

---

### Milestone 6: Integration Tests
**Prefix**: `Real Auth - 6`

End-to-end tests for new authentication features.

#### Task 6.1: Update Integration Test Database Setup
**File**: `tests/integration/conftest.py`

Ensure test users are created with known passwords.

#### Task 6.2: Auth Flow Integration Tests
**File**: `tests/integration/test_auth_flow.py` (new file)

Tests:
- Login with valid credentials
- Login fails with invalid credentials
- Login fails for inactive user
- Profile update works
- Password change works

#### Task 6.3: User Management Integration Tests
**File**: `tests/integration/test_user_management.py` (new file)

Tests:
- Admin can access user management page
- Non-admin cannot access user management page
- Create user shows temporary password
- Edit user settings
- Reset password shows new password
- Cannot deactivate self
- Cannot remove own admin status

---

### Milestone 7: Acceptance Criteria (Documentation & Final Verification)
**Prefix**: `Real Auth - 7`

#### Task 7.1: Update Documentation
**Files**:
- `README.md` - Update auth description, document default admin credentials
- `CLAUDE.md` - Update first-time setup section
- `docs/deployment.rst` - Add security note about changing default admin password
- `docs/getting-started.rst` - Document user management

#### Task 7.2: Run All Tests
Ensure all nox sessions pass: `test-3.14`, `test-integration`, `lint`, `type_check`

#### Task 7.3: Move Feature File
Move `docs/features/real-auth.md` to `docs/features/completed/`

---

### Key Files Reference

| Component | Path |
|-----------|------|
| API endpoints | `kiosk_show_replacement/api/v1.py` |
| Web auth views | `kiosk_show_replacement/auth/views.py` |
| Auth decorators | `kiosk_show_replacement/auth/decorators.py` |
| User model | `kiosk_show_replacement/models/__init__.py` |
| Exceptions | `kiosk_show_replacement/exceptions.py` |
| DB init | `kiosk_show_replacement/cli/init_db.py` |
| Frontend API client | `frontend/src/utils/apiClient.ts` |
| Frontend types | `frontend/src/types/index.ts` |
| Navigation | `frontend/src/components/Navigation.tsx` |
| App routes | `frontend/src/App.tsx` |
| Auth unit tests | `tests/unit/test_auth.py` |

---

### Verification Checklist

After each milestone:
1. Run `poetry run -- nox -s format && poetry run -- nox -s lint`
2. Run `poetry run -- nox -s test-3.14` (unit tests)
3. After Milestone 5: Run `poetry run -- nox -s test-integration`
4. Manual testing of UI flows

Final verification:
- [ ] Fresh database init creates admin user with `admin/admin/admin@example.com`
- [ ] Cannot login with non-existent user
- [ ] Cannot login with wrong password
- [ ] Cannot login when inactive
- [ ] Users can change their own email and password
- [ ] Admins can create users and see temporary passwords
- [ ] Admins can reset passwords and see new passwords
- [ ] Admins can activate/deactivate users
- [ ] Admins cannot demote themselves or deactivate themselves
