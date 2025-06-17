import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Button, Spinner, Alert, Modal, Form } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { Display, Slideshow } from '../types';

const Displays: React.FC = () => {
  const { apiCall } = useApi();
  const [displays, setDisplays] = useState<Display[]>([]);
  const [slideshows, setSlideshows] = useState<Slideshow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedDisplay, setSelectedDisplay] = useState<Display | null>(null);
  const [assigningSlideshowId, setAssigningSlideshowId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load displays and slideshows in parallel
      const [displaysResponse, slideshowsResponse] = await Promise.all([
        apiCall('/api/v1/displays'),
        apiCall('/api/v1/slideshows')
      ]);

      if (displaysResponse.success) {
        setDisplays(displaysResponse.data);
      } else {
        throw new Error(displaysResponse.error || 'Failed to load displays');
      }

      if (slideshowsResponse.success) {
        setSlideshows(slideshowsResponse.data);
      } else {
        throw new Error(slideshowsResponse.error || 'Failed to load slideshows');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignSlideshow = (display: Display) => {
    setSelectedDisplay(display);
    setAssigningSlideshowId(display.current_slideshow_id);
    setShowAssignModal(true);
  };

  const handleSubmitAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDisplay) return;

    try {
      setSubmitting(true);
      
      const response = await apiCall(`/api/v1/displays/${selectedDisplay.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slideshow_id: assigningSlideshowId })
      });

      if (response.success) {
        setShowAssignModal(false);
        await loadData(); // Reload to get updated data
      } else {
        throw new Error(response.error || 'Failed to assign slideshow');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign slideshow');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteDisplay = async (display: Display) => {
    if (!window.confirm(`Are you sure you want to delete display "${display.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await apiCall(`/api/v1/displays/${display.id}`, {
        method: 'DELETE'
      });

      if (response.success) {
        await loadData(); // Reload to get updated data
      } else {
        throw new Error(response.error || 'Failed to delete display');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete display');
    }
  };

  const formatLastSeen = (lastSeenAt: string | null) => {
    if (!lastSeenAt) return 'Never';
    
    const date = new Date(lastSeenAt);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getStatusBadge = (display: Display) => {
    return display.is_online ? (
      <Badge bg="success">Online</Badge>
    ) : (
      <Badge bg="secondary">Offline</Badge>
    );
  };

  const getSlideshowName = (slideshowId: number | null) => {
    if (!slideshowId) return 'None';
    const slideshow = slideshows.find(s => s.id === slideshowId);
    return slideshow ? slideshow.name : 'Unknown';
  };

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading displays...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container fluid>
      <Row>
        <Col>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h1>Display Management</h1>
            <Button variant="outline-primary" onClick={loadData} disabled={loading}>
              <i className="bi bi-arrow-clockwise me-2"></i>
              Refresh
            </Button>
          </div>

          {error && (
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <i className="bi bi-display me-2"></i>
                All Displays ({displays.length})
              </h5>
            </Card.Header>
            <Card.Body>
              {displays.length === 0 ? (
                <div className="text-center py-5">
                  <i className="bi bi-display" style={{ fontSize: '3rem', color: '#6c757d' }}></i>
                  <h4 className="mt-3 text-muted">No Displays Found</h4>
                  <p className="text-muted">
                    Displays will appear here automatically when they connect to the system.
                  </p>
                  <p className="text-muted">
                    To add a display, navigate to <code>/display/[display-name]</code> in a browser.
                  </p>
                </div>
              ) : (
                <Table responsive hover>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Resolution</th>
                      <th>Current Slideshow</th>
                      <th>Last Seen</th>
                      <th>Location</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displays.map((display) => (
                      <tr key={display.id}>
                        <td>
                          <strong>{display.name}</strong>
                          {display.is_default && (
                            <Badge bg="info" className="ms-2">Default</Badge>
                          )}
                        </td>
                        <td>{getStatusBadge(display)}</td>
                        <td>
                          {display.resolution_width && display.resolution_height ? (
                            `${display.resolution_width} × ${display.resolution_height}`
                          ) : (
                            <span className="text-muted">Not detected</span>
                          )}
                        </td>
                        <td>
                          {display.current_slideshow_id ? (
                            <Link 
                              to={`/slideshows/${display.current_slideshow_id}`}
                              className="text-decoration-none"
                            >
                              {getSlideshowName(display.current_slideshow_id)}
                            </Link>
                          ) : (
                            <span className="text-muted">None assigned</span>
                          )}
                        </td>
                        <td>
                          <span className="text-muted">
                            {formatLastSeen(display.last_seen_at)}
                          </span>
                        </td>
                        <td>
                          {display.location || (
                            <span className="text-muted">No location set</span>
                          )}
                        </td>
                        <td>
                          <div className="btn-group btn-group-sm">
                            <Link
                              to={`/admin/displays/${display.id}`}
                              className="btn btn-outline-secondary btn-sm"
                              title="View Details"
                            >
                              <i className="bi bi-eye"></i>
                            </Link>
                            <Button
                              variant="outline-primary"
                              size="sm"
                              onClick={() => handleAssignSlideshow(display)}
                              title="Assign Slideshow"
                            >
                              <i className="bi bi-collection"></i>
                            </Button>
                            <Button
                              variant="outline-info"
                              size="sm"
                              as="a"
                              href={`/display/${display.name}`}
                              target="_blank"
                              title="Open Display"
                            >
                              <i className="bi bi-box-arrow-up-right"></i>
                            </Button>
                            <Button
                              variant="outline-danger"
                              size="sm"
                              onClick={() => handleDeleteDisplay(display)}
                              title="Delete Display"
                            >
                              <i className="bi bi-trash"></i>
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Slideshow Assignment Modal */}
      <Modal show={showAssignModal} onHide={() => setShowAssignModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            Assign Slideshow to {selectedDisplay?.name}
          </Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleSubmitAssignment}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label htmlFor="slideshow-select">Slideshow</Form.Label>
              <Form.Select
                id="slideshow-select"
                value={assigningSlideshowId || ''}
                onChange={(e) => setAssigningSlideshowId(e.target.value ? parseInt(e.target.value) : null)}
              >
                <option value="">No slideshow (unassign)</option>
                {slideshows
                  .filter(s => s.is_active)
                  .map((slideshow) => (
                    <option key={slideshow.id} value={slideshow.id}>
                      {slideshow.name}
                      {slideshow.is_default && ' (Default)'}
                    </option>
                  ))}
              </Form.Select>
              <Form.Text className="text-muted">
                Select a slideshow to display on this device, or choose "No slideshow" to unassign.
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button 
              variant="secondary" 
              onClick={() => setShowAssignModal(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              type="submit"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Assigning...
                </>
              ) : (
                'Assign Slideshow'
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
};

export default Displays;
