import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card, Alert, Spinner, Badge, Table, Form } from 'react-bootstrap';
import { Link } from 'react-router-dom';

interface AssignmentHistoryRecord {
  id: number;
  display_id: number;
  display_name: string;
  previous_slideshow_id?: number;
  previous_slideshow_name?: string;
  new_slideshow_id?: number;
  new_slideshow_name?: string;
  action: 'assign' | 'unassign' | 'change';
  reason?: string;
  created_at: string;
  created_by_id?: number;
  created_by_username?: string;
}

const AssignmentHistory: React.FC = () => {
  const [history, setHistory] = useState<AssignmentHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  
  // Filters
  const [displayFilter, setDisplayFilter] = useState<string>('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [userFilter, setUserFilter] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);

  const loadAssignmentHistory = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (displayFilter) params.append('display_id', displayFilter);
      if (actionFilter !== 'all') params.append('action', actionFilter);
      if (userFilter) params.append('user_id', userFilter);

      const response = await fetch(`/api/v1/assignment-history?${params.toString()}`);
      const data = await response.json();

      if (data.success && data.data) {
        setHistory(data.data);
      } else {
        setError('Failed to load assignment history');
      }
    } catch (err) {
      console.error('Assignment history loading error:', err);
      setError('Failed to load assignment history. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [displayFilter, actionFilter, userFilter, limit]);

  useEffect(() => {
    loadAssignmentHistory();
  }, [loadAssignmentHistory]);

  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getActionBadgeVariant = (action: string): string => {
    switch (action) {
      case 'assign': return 'success';
      case 'unassign': return 'warning';
      case 'change': return 'info';
      default: return 'secondary';
    }
  };

  const getActionDescription = (record: AssignmentHistoryRecord): string => {
    switch (record.action) {
      case 'assign':
        return `Assigned "${record.new_slideshow_name}" to display`;
      case 'unassign':
        return `Unassigned "${record.previous_slideshow_name}" from display`;
      case 'change':
        return `Changed from "${record.previous_slideshow_name}" to "${record.new_slideshow_name}"`;
      default:
        return 'Unknown action';
    }
  };

  if (loading && history.length === 0) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <div className="mt-2">Loading assignment history...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Assignment History & Audit Trail</h1>
        <div className="text-muted">
          <small>Showing {history.length} records</small>
          {loading && <Spinner animation="border" size="sm" className="ms-2" />}
        </div>
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Card className="mb-4">
        <Card.Header>
          <h5 className="mb-0">Filters</h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Display ID</Form.Label>
                <Form.Control
                  type="number"
                  placeholder="Filter by display ID"
                  value={displayFilter}
                  onChange={(e) => setDisplayFilter(e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Action</Form.Label>
                <Form.Select
                  value={actionFilter}
                  onChange={(e) => setActionFilter(e.target.value)}
                >
                  <option value="all">All Actions</option>
                  <option value="assign">Assign</option>
                  <option value="unassign">Unassign</option>
                  <option value="change">Change</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>User ID</Form.Label>
                <Form.Control
                  type="number"
                  placeholder="Filter by user ID"
                  value={userFilter}
                  onChange={(e) => setUserFilter(e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col md={3}>
              <Form.Group className="mb-3">
                <Form.Label>Limit</Form.Label>
                <Form.Select
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                >
                  <option value={25}>25 records</option>
                  <option value={50}>50 records</option>
                  <option value={100}>100 records</option>
                  <option value={200}>200 records</option>
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Assignment History Table */}
      <Card>
        <Card.Header>
          <h5 className="mb-0">Assignment History</h5>
        </Card.Header>
        <Card.Body>
          <Table responsive striped>
            <thead>
              <tr>
                <th>Date & Time</th>
                <th>Display</th>
                <th>Action</th>
                <th>Change Details</th>
                <th>User</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {history.map((record) => (
                <tr key={record.id}>
                  <td>
                    <span className="text-muted">
                      {formatDateTime(record.created_at)}
                    </span>
                  </td>
                  <td>
                    <Link
                      to={`/admin/displays/${record.display_id}`}
                      className="text-decoration-none"
                    >
                      {record.display_name}
                    </Link>
                    <br />
                    <small className="text-muted">ID: {record.display_id}</small>
                  </td>
                  <td>
                    <Badge bg={getActionBadgeVariant(record.action)}>
                      {record.action.charAt(0).toUpperCase() + record.action.slice(1)}
                    </Badge>
                  </td>
                  <td>
                    <div className="small">
                      {getActionDescription(record)}
                    </div>
                    {record.action === 'change' && (
                      <div className="mt-1">
                        <small className="text-muted">
                          Previous: {record.previous_slideshow_name || 'None'} →{' '}
                          New: {record.new_slideshow_name || 'None'}
                        </small>
                      </div>
                    )}
                  </td>
                  <td>
                    {record.created_by_username ? (
                      <div>
                        <strong>{record.created_by_username}</strong>
                        <br />
                        <small className="text-muted">ID: {record.created_by_id}</small>
                      </div>
                    ) : (
                      <span className="text-muted">System</span>
                    )}
                  </td>
                  <td>
                    <span className="text-muted">
                      {record.reason || 'No reason provided'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          {history.length === 0 && !loading && (
            <div className="text-center text-muted py-4">
              <i className="bi bi-clock-history fs-1"></i>
              <div className="mt-2">
                <p>No assignment history found.</p>
                <small>Assignment changes will appear here when they occur.</small>
              </div>
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default AssignmentHistory;
