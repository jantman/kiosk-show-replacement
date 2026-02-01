import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../utils/apiClient';

const Profile: React.FC = () => {
  const { user, checkAuth } = useAuth();

  // Profile form state
  const [email, setEmail] = useState('');
  const [profileMessage, setProfileMessage] = useState<{ type: 'success' | 'danger'; text: string } | null>(null);
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'danger'; text: string } | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Initialize email from user data
  useEffect(() => {
    if (user) {
      setEmail(user.email || '');
    }
  }, [user]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);
    setIsUpdatingProfile(true);

    try {
      const response = await apiClient.updateProfile({ email });

      if (response.success) {
        setProfileMessage({ type: 'success', text: 'Profile updated successfully.' });
        // Refresh user data in auth context
        await checkAuth();
      } else {
        setProfileMessage({ type: 'danger', text: response.error || 'Failed to update profile.' });
      }
    } catch {
      setProfileMessage({ type: 'danger', text: 'An error occurred while updating profile.' });
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'danger', text: 'New passwords do not match.' });
      return;
    }

    // Validate new password is not empty
    if (!newPassword.trim()) {
      setPasswordMessage({ type: 'danger', text: 'New password cannot be empty.' });
      return;
    }

    setIsChangingPassword(true);

    try {
      const response = await apiClient.changePassword(currentPassword, newPassword);

      if (response.success) {
        setPasswordMessage({ type: 'success', text: 'Password changed successfully.' });
        // Clear the form
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        setPasswordMessage({ type: 'danger', text: response.error || 'Failed to change password.' });
      }
    } catch {
      setPasswordMessage({ type: 'danger', text: 'An error occurred while changing password.' });
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <Container>
      <h1 className="mb-4">Profile Settings</h1>

      <Row>
        {/* Profile Information */}
        <Col md={6} className="mb-4">
          <Card>
            <Card.Header>
              <h5 className="mb-0">Profile Information</h5>
            </Card.Header>
            <Card.Body>
              {profileMessage && (
                <Alert
                  variant={profileMessage.type}
                  dismissible
                  onClose={() => setProfileMessage(null)}
                >
                  {profileMessage.text}
                </Alert>
              )}

              <Form onSubmit={handleProfileSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Username</Form.Label>
                  <Form.Control
                    type="text"
                    value={user?.username || ''}
                    disabled
                    readOnly
                  />
                  <Form.Text className="text-muted">
                    Username cannot be changed.
                  </Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Email Address</Form.Label>
                  <Form.Control
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email address"
                    disabled={isUpdatingProfile}
                  />
                </Form.Group>

                <Button
                  variant="primary"
                  type="submit"
                  disabled={isUpdatingProfile}
                >
                  {isUpdatingProfile ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" />
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        {/* Change Password */}
        <Col md={6} className="mb-4">
          <Card>
            <Card.Header>
              <h5 className="mb-0">Change Password</h5>
            </Card.Header>
            <Card.Body>
              {passwordMessage && (
                <Alert
                  variant={passwordMessage.type}
                  dismissible
                  onClose={() => setPasswordMessage(null)}
                >
                  {passwordMessage.text}
                </Alert>
              )}

              <Form onSubmit={handlePasswordSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Current Password</Form.Label>
                  <Form.Control
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    disabled={isChangingPassword}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>New Password</Form.Label>
                  <Form.Control
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    disabled={isChangingPassword}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Confirm New Password</Form.Label>
                  <Form.Control
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    disabled={isChangingPassword}
                    required
                    isInvalid={confirmPassword !== '' && newPassword !== confirmPassword}
                  />
                  <Form.Control.Feedback type="invalid">
                    Passwords do not match.
                  </Form.Control.Feedback>
                </Form.Group>

                <Button
                  variant="primary"
                  type="submit"
                  disabled={isChangingPassword || !currentPassword || !newPassword || !confirmPassword}
                >
                  {isChangingPassword ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" />
                      Changing...
                    </>
                  ) : (
                    'Change Password'
                  )}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Profile;
