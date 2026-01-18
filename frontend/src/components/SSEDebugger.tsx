import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Button, Modal, Alert } from 'react-bootstrap';
import { useSSE } from '../hooks/useSSE';

interface SSEConnection {
  id: string;
  type: 'admin' | 'display';
  user?: string;
  display?: string;
  connected_at: string;
  last_ping: string;
  events_sent: number;
}

interface SSEStats {
  total_connections: number;
  admin_connections: number;
  display_connections: number;
  events_sent_last_hour: number;
  connections: SSEConnection[];
}

export const SSEDebugger: React.FC = () => {
  const [stats, setStats] = useState<SSEStats | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Use SSE hook to listen for real-time updates
  const { connectionState, lastEvent } = useSSE('/api/v1/events/admin');

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/events/stats', {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch SSE stats: ${response.statusText}`);
      }
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const sendTestEvent = async () => {
    try {
      const response = await fetch('/api/v1/events/test', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: 'test_event',
          message: 'Test event from SSE debugger'
        })
      });
      if (!response.ok) {
        throw new Error(`Failed to send test event: ${response.statusText}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send test event');
    }
  };

  // Auto-refresh functionality
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    if (autoRefresh) {
      interval = setInterval(fetchStats, 5000); // Refresh every 5 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  // Update stats when receiving SSE events
  useEffect(() => {
    if (lastEvent && lastEvent.event_type === 'sse_stats_update') {
      setStats(lastEvent.data as SSEStats);
    }
  }, [lastEvent]);

  // Initial fetch
  useEffect(() => {
    fetchStats();
  }, []);

  const getConnectionStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge bg="success">Connected</Badge>;
      case 'disconnected':
        return <Badge bg="danger">Disconnected</Badge>;
      case 'connecting':
        return <Badge bg="warning">Connecting</Badge>;
      default:
        return <Badge bg="secondary">Unknown</Badge>;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ${diffHours % 24}h`;
    if (diffHours > 0) return `${diffHours}h ${diffMins % 60}m`;
    return `${diffMins}m`;
  };

  return (
    <>
      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">SSE Connection Monitor</h5>
          <div>
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className="me-2"
            >
              {autoRefresh ? 'Stop Auto-Refresh' : 'Start Auto-Refresh'}
            </Button>
            <Button
              variant="outline-secondary"
              size="sm"
              onClick={fetchStats}
              disabled={loading}
              className="me-2"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button
              variant="info"
              size="sm"
              onClick={() => setShowModal(true)}
            >
              Debug Tools
            </Button>
          </div>
        </Card.Header>
        <Card.Body>
          {error && (
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Connection Status */}
          <div className="mb-3">
            <strong>Your SSE Connection: </strong>
            {getConnectionStatusBadge(connectionState)}
            <span className="ms-2 text-muted">
              {connectionState === 'connected' ? 'Receiving real-time updates' : 'Not connected to SSE stream'}
            </span>
          </div>

          {/* Statistics Overview */}
          {stats && (
            <>
              <div className="row mb-4">
                <div className="col-md-3">
                  <div className="text-center">
                    <h4 className="text-primary">{stats.total_connections}</h4>
                    <p className="text-muted mb-0">Total Connections</p>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center">
                    <h4 className="text-success">{stats.admin_connections}</h4>
                    <p className="text-muted mb-0">Admin Connections</p>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center">
                    <h4 className="text-info">{stats.display_connections}</h4>
                    <p className="text-muted mb-0">Display Connections</p>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center">
                    <h4 className="text-warning">{stats.events_sent_last_hour}</h4>
                    <p className="text-muted mb-0">Events (Last Hour)</p>
                  </div>
                </div>
              </div>

              {/* Active Connections Table */}
              {stats.connections.length > 0 ? (
                <Table striped hover responsive>
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>User/Display</th>
                      <th>Connected</th>
                      <th>Duration</th>
                      <th>Last Ping</th>
                      <th>Events Sent</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.connections.map((conn) => (
                      <tr key={conn.id}>
                        <td>
                          <Badge bg={conn.type === 'admin' ? 'success' : 'info'}>
                            {conn.type}
                          </Badge>
                        </td>
                        <td>{conn.user || conn.display || 'Unknown'}</td>
                        <td className="text-muted small">
                          {formatTimestamp(conn.connected_at)}
                        </td>
                        <td>{formatDuration(conn.connected_at)}</td>
                        <td className="text-muted small">
                          {formatTimestamp(conn.last_ping)}
                        </td>
                        <td>{conn.events_sent}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                <Alert variant="info">No active SSE connections found.</Alert>
              )}
            </>
          )}
        </Card.Body>
      </Card>

      {/* Debug Tools Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>SSE Debug Tools</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <h6>Test Event Broadcasting</h6>
            <p className="text-muted">
              Send a test event to all connected SSE clients to verify the broadcasting system.
            </p>
            <Button variant="primary" onClick={sendTestEvent}>
              Send Test Event
            </Button>
          </div>

          <div className="mb-3">
            <h6>Connection Information</h6>
            <ul className="list-unstyled">
              <li><strong>Current Status:</strong> {connectionState}</li>
              <li><strong>Connected:</strong> {connectionState === 'connected' ? 'Yes' : 'No'}</li>
              <li><strong>Last Event:</strong> {lastEvent ? lastEvent.event_type : 'None'}</li>
              <li><strong>Auto-Refresh:</strong> {autoRefresh ? 'Enabled' : 'Disabled'}</li>
            </ul>
          </div>

          <div>
            <h6>Troubleshooting</h6>
            <ul className="small text-muted">
              <li>If connections show 0, check if SSE endpoints are accessible</li>
              <li>If admin connections are missing, verify authentication</li>
              <li>If display connections are missing, check display heartbeat system</li>
              <li>Events should be sent when displays/slideshows are updated</li>
            </ul>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default SSEDebugger;
