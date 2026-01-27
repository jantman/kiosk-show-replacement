import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Badge, Button, Spinner, Alert, Modal, Form } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { useDisplayEvents } from '../hooks/useSSE';
import LiveDataIndicator from '../components/LiveDataIndicator';
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
  
  // Bulk operations state
  const [selectedDisplayIds, setSelectedDisplayIds] = useState<Set<number>>(new Set());
  const [showBulkAssignModal, setShowBulkAssignModal] = useState(false);
  const [bulkAssigningSlideshowId, setBulkAssigningSlideshowId] = useState<number | null>(null);
  const [bulkSubmitting, setBulkSubmitting] = useState(false);
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'offline'>('all');
  const [assignmentFilter, setAssignmentFilter] = useState<'all' | 'assigned' | 'unassigned'>('all');

  // SSE integration for real-time updates
  const handleDisplayUpdate = (updatedDisplay: Display) => {
    setDisplays(prevDisplays => 
      prevDisplays.map(display => 
        display.id === updatedDisplay.id ? updatedDisplay : display
      )
    );
  };

  useDisplayEvents(handleDisplayUpdate);

  useEffect(() => {
    loadData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
        setDisplays(displaysResponse.data as Display[]);
      } else {
        throw new Error(displaysResponse.error || 'Failed to load displays');
      }

      if (slideshowsResponse.success) {
        setSlideshows(slideshowsResponse.data as Slideshow[]);
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
    setAssigningSlideshowId(display.current_slideshow_id || null);
    setShowAssignModal(true);
  };

  // Bulk operations methods
  const handleSelectDisplay = (displayId: number, checked: boolean) => {
    const newSelected = new Set(selectedDisplayIds);
    if (checked) {
      newSelected.add(displayId);
    } else {
      newSelected.delete(displayId);
    }
    setSelectedDisplayIds(newSelected);
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = new Set(filteredDisplays.map(d => d.id));
      setSelectedDisplayIds(allIds);
    } else {
      setSelectedDisplayIds(new Set());
    }
  };

  const handleBulkAssign = () => {
    if (selectedDisplayIds.size === 0) return;
    setBulkAssigningSlideshowId(null);
    setShowBulkAssignModal(true);
  };

  const handleBulkAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedDisplayIds.size === 0) return;

    try {
      setBulkSubmitting(true);
      
      // Assign slideshow to all selected displays
      const promises = Array.from(selectedDisplayIds).map(displayId => {
        const display = displays.find(d => d.id === displayId);
        if (!display) throw new Error(`Display with ID ${displayId} not found`);
        return apiCall(`/api/v1/displays/${display.name}/assign-slideshow`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slideshow_id: bulkAssigningSlideshowId })
        });
      });

      const results = await Promise.all(promises);
      const failures = results.filter(result => !result.success);
      
      if (failures.length > 0) {
        throw new Error(`Failed to assign slideshow to ${failures.length} displays`);
      }

      setShowBulkAssignModal(false);
      setSelectedDisplayIds(new Set());
      await loadData(); // Reload to get updated data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to bulk assign slideshow');
    } finally {
      setBulkSubmitting(false);
    }
  };

  // Filter displays based on search and filter criteria
  const filteredDisplays = (displays || []).filter(display => {
    const matchesSearch = display.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (display.location || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'online' && display.is_online) ||
                         (statusFilter === 'offline' && !display.is_online);
    
    const matchesAssignment = assignmentFilter === 'all' ||
                             (assignmentFilter === 'assigned' && display.current_slideshow_id) ||
                             (assignmentFilter === 'unassigned' && !display.current_slideshow_id);
    
    return matchesSearch && matchesStatus && matchesAssignment;
  });

  const handleSubmitAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDisplay) return;

    try {
      setSubmitting(true);
      
      const response = await apiCall(`/api/v1/displays/${selectedDisplay.name}/assign-slideshow`, {
        method: 'POST',
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

  const handleReloadDisplay = async (display: Display) => {
    try {
      const response = await apiCall(`/api/v1/displays/${display.id}/reload`, {
        method: 'POST'
      });

      if (response.success) {
        // Show a temporary success message - we can use the error state with a different color
        // or just log it. For simplicity, we'll use a console log and could add a toast later
        console.log(`Reload command sent to display "${display.name}"`);
        // Clear any existing error since the operation succeeded
        setError(null);
      } else {
        throw new Error(response.error || 'Failed to send reload command');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reload command');
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
      <Badge bg="success" className="badge-success">Online</Badge>
    ) : (
      <Badge bg="danger" className="badge-danger">Offline</Badge>
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
              <Row className="align-items-center">
                <Col>
                  <div className="d-flex align-items-center">
                    <h5 className="mb-0">
                      <i className="bi bi-display me-2"></i>
                      All Displays ({filteredDisplays.length} of {displays.length})
                    </h5>
                    <LiveDataIndicator 
                      dataType="display"
                      className="ms-2"
                    />
                  </div>
                </Col>
                <Col xs="auto">
                  {selectedDisplayIds.size > 0 && (
                    <Button 
                      variant="primary" 
                      size="sm" 
                      onClick={handleBulkAssign}
                      className="me-2"
                    >
                      <i className="bi bi-collection me-1"></i>
                      Bulk Assign ({selectedDisplayIds.size})
                    </Button>
                  )}
                </Col>
              </Row>
            </Card.Header>
            <Card.Body>
              {/* Search and Filter Controls */}
              <Row className="mb-3">
                <Col md={4}>
                  <Form.Control
                    type="text"
                    placeholder="Search displays..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </Col>
                <Col md={3}>
                  <Form.Select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as 'all' | 'online' | 'offline')}
                  >
                    <option value="all">All Status</option>
                    <option value="online">Online Only</option>
                    <option value="offline">Offline Only</option>
                  </Form.Select>
                </Col>
                <Col md={3}>
                  <Form.Select
                    value={assignmentFilter}
                    onChange={(e) => setAssignmentFilter(e.target.value as 'all' | 'assigned' | 'unassigned')}
                  >
                    <option value="all">All Assignments</option>
                    <option value="assigned">Assigned Only</option>
                    <option value="unassigned">Unassigned Only</option>
                  </Form.Select>
                </Col>
                <Col md={2}>
                  <Button variant="outline-secondary" onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('all');
                    setAssignmentFilter('all');
                  }}>
                    Clear
                  </Button>
                </Col>
              </Row>

              {filteredDisplays.length === 0 ? (
                <div className="text-center py-5">
                  {displays.length === 0 ? (
                    <>
                      <i className="bi bi-display" style={{ fontSize: '3rem', color: '#6c757d' }}></i>
                      <h4 className="mt-3 text-muted">No Displays Found</h4>
                      <p className="text-muted">
                        Displays will appear here automatically when they connect to the system.
                      </p>
                      <p className="text-muted">
                        To add a display, navigate to <code>/display/[display-name]</code> in a browser.
                      </p>
                    </>
                  ) : (
                    <>
                      <i className="bi bi-search" style={{ fontSize: '3rem', color: '#6c757d' }}></i>
                      <h4 className="mt-3 text-muted">No Displays Match Your Filters</h4>
                      <p className="text-muted">
                        Try adjusting your search terms or filters to find displays.
                      </p>
                    </>
                  )}
                </div>
              ) : (
                <Table responsive hover>
                  <thead>
                    <tr>
                      <th>
                        <Form.Check
                          type="checkbox"
                          checked={selectedDisplayIds.size === filteredDisplays.length && filteredDisplays.length > 0}
                          onChange={(e) => handleSelectAll(e.target.checked)}
                        />
                      </th>
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
                    {filteredDisplays.map((display) => (
                      <tr key={display.id}>
                        <td>
                          <Form.Check
                            type="checkbox"
                            checked={selectedDisplayIds.has(display.id)}
                            onChange={(e) => handleSelectDisplay(display.id, e.target.checked)}
                          />
                        </td>
                        <td>
                          <div className="d-flex align-items-center">
                            <strong>{display.name}</strong>
                            {display.is_default && (
                              <Badge bg="info" className="ms-2">Default</Badge>
                            )}
                            <LiveDataIndicator 
                              dataType="display" 
                              dataId={display.id} 
                              className="ms-2"
                            />
                          </div>
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
                            {formatLastSeen(display.last_seen_at || null)}
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
                              variant="outline-warning"
                              size="sm"
                              onClick={() => handleReloadDisplay(display)}
                              title="Reload Display"
                            >
                              <i className="bi bi-arrow-clockwise"></i>
                            </Button>
                            <Button
                              variant="outline-info"
                              size="sm"
                              as="a"
                              href={`/display/${display.name || 'unknown'}`}
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
                {(slideshows || [])
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

      {/* Bulk Assignment Modal */}
      <Modal show={showBulkAssignModal} onHide={() => setShowBulkAssignModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>
            Bulk Assign Slideshow to {selectedDisplayIds.size} Displays
          </Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleBulkAssignSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Select Slideshow</Form.Label>
              <Form.Select
                value={bulkAssigningSlideshowId || ''}
                onChange={(e) => setBulkAssigningSlideshowId(e.target.value ? parseInt(e.target.value) : null)}
                required
              >
                <option value="">Remove slideshow assignment</option>
                {slideshows.filter(s => s.is_active).map((slideshow) => (
                  <option key={slideshow.id} value={slideshow.id}>
                    {slideshow.name}
                  </option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                This will assign the selected slideshow to all {selectedDisplayIds.size} selected displays.
              </Form.Text>
            </Form.Group>

            <div className="mb-3">
              <strong>Selected Displays:</strong>
              <ul className="mt-2">
                {Array.from(selectedDisplayIds).map(displayId => {
                  const display = displays.find(d => d.id === displayId);
                  return display ? (
                    <li key={displayId}>
                      {display.name} {display.location && `(${display.location})`}
                    </li>
                  ) : null;
                })}
              </ul>
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button 
              variant="secondary" 
              onClick={() => setShowBulkAssignModal(false)}
              disabled={bulkSubmitting}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              type="submit"
              disabled={bulkSubmitting}
            >
              {bulkSubmitting ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Assigning...
                </>
              ) : (
                `Assign to ${selectedDisplayIds.size} Displays`
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
};

export default Displays;
