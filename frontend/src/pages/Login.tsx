import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../utils/apiClient';

interface SystemStatus {
  isReady: boolean;
  isInitialized: boolean;
  message: string | null;
}

const Login: React.FC = () => {
  const { login, isAuthenticated, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    isReady: true, // Assume ready until proven otherwise
    isInitialized: true,
    message: null,
  });
  const [isCheckingSystem, setIsCheckingSystem] = useState(true);

  // Check system health on mount
  useEffect(() => {
    const checkSystemHealth = async () => {
      try {
        const response = await apiClient.getHealthReady();
        if (response.success) {
          setSystemStatus({
            isReady: true,
            isInitialized: true,
            message: null,
          });
        } else {
          // Parse error response for initialization status
          const errorData = response as unknown as {
            reason?: string;
            message?: string;
            database_initialized?: boolean;
          };

          if (errorData.reason === 'database_not_initialized' ||
              errorData.database_initialized === false) {
            setSystemStatus({
              isReady: false,
              isInitialized: false,
              message: errorData.message ||
                "Database not initialized. Run 'flask cli init-db' to set up the system.",
            });
          } else {
            setSystemStatus({
              isReady: false,
              isInitialized: true,
              message: errorData.message || 'System is temporarily unavailable.',
            });
          }
        }
      } catch {
        // Network error - system might be down
        setSystemStatus({
          isReady: false,
          isInitialized: true,
          message: 'Unable to connect to the server. Please check if the backend is running.',
        });
      } finally {
        setIsCheckingSystem(false);
      }
    };

    checkSystemHealth();
  }, []);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/admin" replace />;
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    // Don't allow login if system isn't ready
    if (!systemStatus.isReady) {
      setError(systemStatus.message || 'System is not ready. Please wait and try again.');
      setIsSubmitting(false);
      return;
    }

    if (!formData.username.trim() || !formData.password.trim()) {
      setError('Please enter both username and password');
      setIsSubmitting(false);
      return;
    }

    try {
      // Try to login via apiClient directly to get detailed error
      const response = await apiClient.login(formData.username, formData.password);

      if (response.success && response.data) {
        // Login was successful, let AuthContext know
        await login(formData.username, formData.password);
      } else {
        // Check for specific error codes
        const errorResponse = response as unknown as {
          error?: string;
          error_info?: { code?: string; message?: string };
        };

        if (errorResponse.error_info?.code === 'DATABASE_NOT_INITIALIZED') {
          setSystemStatus({
            isReady: false,
            isInitialized: false,
            message: errorResponse.error_info?.message || errorResponse.error ||
              "Database not initialized. Run 'flask cli init-db' to set up the system.",
          });
          setError('');
        } else {
          setError(errorResponse.error || 'Login failed. Please check your credentials.');
        }
      }
    } catch {
      setError('An error occurred during login. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading || isCheckingSystem) {
    return (
      <Container className="d-flex justify-content-center align-items-center min-vh-100">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <div className="mt-2">
            {isCheckingSystem ? 'Checking system status...' : 'Checking authentication...'}
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container className="d-flex justify-content-center align-items-center min-vh-100">
      <Row className="w-100">
        <Col md={6} lg={4} className="mx-auto">
          <Card>
            <Card.Header className="text-center">
              <h4>Kiosk Show Replacement</h4>
              <p className="text-muted mb-0">Admin Interface</p>
            </Card.Header>
            <Card.Body>
              {/* System status alert - show database initialization issues prominently */}
              {!systemStatus.isReady && (
                <Alert variant={systemStatus.isInitialized ? 'warning' : 'danger'}>
                  <Alert.Heading className="h6">
                    {systemStatus.isInitialized ? 'System Unavailable' : 'Database Not Initialized'}
                  </Alert.Heading>
                  <p className="mb-2">{systemStatus.message}</p>
                  {!systemStatus.isInitialized && (
                    <small className="text-muted">
                      <strong>To initialize:</strong> Run{' '}
                      <code>poetry run flask cli init-db</code> in the project directory.
                    </small>
                  )}
                </Alert>
              )}

              {error && <Alert variant="danger">{error}</Alert>}

              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Username</Form.Label>
                  <Form.Control
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    placeholder="Enter any username"
                    disabled={isSubmitting}
                    autoFocus
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="Enter any password"
                    disabled={isSubmitting}
                  />
                </Form.Group>

                <div className="d-grid">
                  <Button 
                    variant="primary" 
                    type="submit" 
                    disabled={isSubmitting}
                    size="lg"
                  >
                    {isSubmitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" />
                        Signing in...
                      </>
                    ) : (
                      'Sign In'
                    )}
                  </Button>
                </div>
              </Form>

              <div className="text-center mt-3">
                <small className="text-muted">
                  Note: Any username and password combination is accepted
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Login;
