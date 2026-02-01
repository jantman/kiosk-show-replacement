import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Table,
  Button,
  Badge,
  Modal,
  Form,
  Alert,
  Spinner,
} from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../utils/apiClient';
import type { User } from '../types';

const UserManagement: React.FC = () => {
  const { user: currentUser } = useAuth();

  // Users list state
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create user modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createUsername, setCreateUsername] = useState('');
  const [createEmail, setCreateEmail] = useState('');
  const [createIsAdmin, setCreateIsAdmin] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Edit user modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editEmail, setEditEmail] = useState('');
  const [editIsAdmin, setEditIsAdmin] = useState(false);
  const [editIsActive, setEditIsActive] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  // Password modal state
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [tempPassword, setTempPassword] = useState('');
  const [passwordUsername, setPasswordUsername] = useState('');

  // Reset password confirmation modal
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetUserId, setResetUserId] = useState<number | null>(null);
  const [resetUsername, setResetUsername] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  // Load users
  const loadUsers = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.getUsers();
      if (response.success && response.data) {
        setUsers(response.data);
      } else {
        setError(response.error || 'Failed to load users');
      }
    } catch {
      setError('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Create user
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    setCreateError(null);

    try {
      const response = await apiClient.createUser({
        username: createUsername,
        email: createEmail || undefined,
        is_admin: createIsAdmin,
      });

      if (response.success && response.data) {
        // Show password modal
        setTempPassword(response.data.temporary_password);
        setPasswordUsername(createUsername);
        setShowCreateModal(false);
        setShowPasswordModal(true);
        // Reset form
        setCreateUsername('');
        setCreateEmail('');
        setCreateIsAdmin(false);
        // Reload users
        loadUsers();
      } else {
        setCreateError(response.error || 'Failed to create user');
      }
    } catch {
      setCreateError('Failed to create user');
    } finally {
      setIsCreating(false);
    }
  };

  // Open edit modal
  const openEditModal = (user: User) => {
    setEditUser(user);
    setEditEmail(user.email || '');
    setEditIsAdmin(user.is_admin);
    setEditIsActive(user.is_active);
    setEditError(null);
    setShowEditModal(true);
  };

  // Update user
  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;

    setIsEditing(true);
    setEditError(null);

    try {
      const response = await apiClient.updateUser(editUser.id, {
        email: editEmail || undefined,
        is_admin: editIsAdmin,
        is_active: editIsActive,
      });

      if (response.success) {
        setShowEditModal(false);
        loadUsers();
      } else {
        setEditError(response.error || 'Failed to update user');
      }
    } catch {
      setEditError('Failed to update user');
    } finally {
      setIsEditing(false);
    }
  };

  // Open reset password confirmation
  const openResetConfirm = (user: User) => {
    setResetUserId(user.id);
    setResetUsername(user.username);
    setShowResetConfirm(true);
  };

  // Reset password
  const handleResetPassword = async () => {
    if (!resetUserId) return;

    setIsResetting(true);

    try {
      const response = await apiClient.resetUserPassword(resetUserId);

      if (response.success && response.data) {
        setShowResetConfirm(false);
        setTempPassword(response.data.temporary_password);
        setPasswordUsername(resetUsername);
        setShowPasswordModal(true);
      } else {
        setError(response.error || 'Failed to reset password');
        setShowResetConfirm(false);
      }
    } catch {
      setError('Failed to reset password');
      setShowResetConfirm(false);
    } finally {
      setIsResetting(false);
    }
  };

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (isLoading) {
    return (
      <Container className="text-center py-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>User Management</h1>
        <Button variant="primary" onClick={() => setShowCreateModal(true)}>
          <i className="bi bi-plus-lg me-2"></i>
          Create User
        </Button>
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Table striped hover responsive>
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last Login</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id} className={!user.is_active ? 'text-muted' : ''}>
              <td>
                {user.username}
                {user.id === currentUser?.id && (
                  <Badge bg="secondary" className="ms-2">You</Badge>
                )}
              </td>
              <td>{user.email || '-'}</td>
              <td>
                {user.is_admin ? (
                  <Badge bg="primary">Admin</Badge>
                ) : (
                  <Badge bg="secondary">User</Badge>
                )}
              </td>
              <td>
                {user.is_active ? (
                  <Badge bg="success">Active</Badge>
                ) : (
                  <Badge bg="danger">Inactive</Badge>
                )}
              </td>
              <td>{formatDate(user.last_login_at)}</td>
              <td>
                <Button
                  variant="outline-primary"
                  size="sm"
                  className="me-2"
                  onClick={() => openEditModal(user)}
                >
                  Edit
                </Button>
                <Button
                  variant="outline-warning"
                  size="sm"
                  onClick={() => openResetConfirm(user)}
                >
                  Reset Password
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Create User Modal */}
      <Modal show={showCreateModal} onHide={() => setShowCreateModal(false)}>
        <Form onSubmit={handleCreate}>
          <Modal.Header closeButton>
            <Modal.Title>Create User</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {createError && <Alert variant="danger">{createError}</Alert>}

            <Form.Group className="mb-3">
              <Form.Label>Username *</Form.Label>
              <Form.Control
                type="text"
                value={createUsername}
                onChange={(e) => setCreateUsername(e.target.value)}
                placeholder="Enter username"
                required
                disabled={isCreating}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                value={createEmail}
                onChange={(e) => setCreateEmail(e.target.value)}
                placeholder="Enter email (optional)"
                disabled={isCreating}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Check
                type="checkbox"
                label="Administrator"
                checked={createIsAdmin}
                onChange={(e) => setCreateIsAdmin(e.target.checked)}
                disabled={isCreating}
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowCreateModal(false)} disabled={isCreating}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={isCreating || !createUsername.trim()}>
              {isCreating ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Creating...
                </>
              ) : (
                'Create User'
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Edit User Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
        <Form onSubmit={handleUpdate}>
          <Modal.Header closeButton>
            <Modal.Title>Edit User: {editUser?.username}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {editError && <Alert variant="danger">{editError}</Alert>}

            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                placeholder="Enter email (optional)"
                disabled={isEditing}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Check
                type="checkbox"
                label="Administrator"
                checked={editIsAdmin}
                onChange={(e) => setEditIsAdmin(e.target.checked)}
                disabled={isEditing || editUser?.id === currentUser?.id}
              />
              {editUser?.id === currentUser?.id && (
                <Form.Text className="text-muted">
                  You cannot change your own admin status.
                </Form.Text>
              )}
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Check
                type="checkbox"
                label="Active"
                checked={editIsActive}
                onChange={(e) => setEditIsActive(e.target.checked)}
                disabled={isEditing || editUser?.id === currentUser?.id}
              />
              {editUser?.id === currentUser?.id && (
                <Form.Text className="text-muted">
                  You cannot deactivate your own account.
                </Form.Text>
              )}
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowEditModal(false)} disabled={isEditing}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={isEditing}>
              {isEditing ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Password Display Modal */}
      <Modal show={showPasswordModal} onHide={() => setShowPasswordModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Temporary Password</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="warning">
            <strong>Important:</strong> This password will only be shown once.
            Please copy it and share it securely with the user.
          </Alert>
          <p>User: <strong>{passwordUsername}</strong></p>
          <p>Temporary Password:</p>
          <div className="bg-light p-3 rounded border">
            <code className="fs-5 user-select-all">{tempPassword}</code>
          </div>
          <p className="mt-3 text-muted small">
            The user should change this password after their first login.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="outline-primary"
            onClick={() => navigator.clipboard.writeText(tempPassword)}
          >
            <i className="bi bi-clipboard me-2"></i>
            Copy to Clipboard
          </Button>
          <Button variant="primary" onClick={() => setShowPasswordModal(false)}>
            Done
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Reset Password Confirmation Modal */}
      <Modal show={showResetConfirm} onHide={() => setShowResetConfirm(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Reset Password</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>
            Are you sure you want to reset the password for user <strong>{resetUsername}</strong>?
          </p>
          <p className="text-muted">
            A new temporary password will be generated and displayed.
            The user will need to use this new password to log in.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowResetConfirm(false)} disabled={isResetting}>
            Cancel
          </Button>
          <Button variant="warning" onClick={handleResetPassword} disabled={isResetting}>
            {isResetting ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Resetting...
              </>
            ) : (
              'Reset Password'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default UserManagement;
