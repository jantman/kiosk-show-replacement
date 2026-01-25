import React, { useState, useEffect, useCallback } from 'react';
import { Card, Badge, ProgressBar, Table, Alert, Button, Modal } from 'react-bootstrap';
import { useSSEContext } from '../hooks/useSSE';

interface DisplayStatus {
  id: number;
  name: string;
  location?: string;
  is_online: boolean;
  last_seen_at?: string;
  current_slideshow?: {
    id: number;
    name: string;
  };
  connection_quality: 'excellent' | 'good' | 'poor' | 'offline';
  heartbeat_interval: number;
  missed_heartbeats: number;
  sse_connected: boolean;
  last_sse_event?: string;
  performance_metrics?: {
    cpu_usage: number;
    memory_usage: number;
    network_latency: number;
  };
}

interface EnhancedDisplayStatusProps {
  displayId?: number;
  showAll?: boolean;
  compact?: boolean;
}

export const EnhancedDisplayStatus: React.FC<EnhancedDisplayStatusProps> = ({
  displayId,
  compact = false
}) => {
  const [displays, setDisplays] = useState<DisplayStatus[]>([]);
  const [selectedDisplay, setSelectedDisplay] = useState<DisplayStatus | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use SSE context to share the connection from SSEProvider
  const { connectionState, lastEvent } = useSSEContext();

  const fetchDisplayStatuses = useCallback(async () => {
    try {
      const url = displayId
        ? `/api/v1/displays/${displayId}/status`
        : '/api/v1/displays/status';

      const response = await fetch(url, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch display status: ${response.statusText}`);
      }

      const result = await response.json();
      // API returns {success: true, data: [...]} format
      const data = result.data;
      setDisplays(Array.isArray(data) ? data : [data]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [displayId]);

  // Update display status from SSE events
  useEffect(() => {
    if (lastEvent) {
      switch (lastEvent.event_type) {
        case 'display_status_update':
        case 'display_heartbeat':
        case 'display_performance': {
          const updatedDisplay = lastEvent.data as DisplayStatus;
          setDisplays(prev =>
            prev.map(display =>
              display.id === updatedDisplay.id
                ? { ...display, ...updatedDisplay }
                : display
            )
          );
          break;
        }
      }
    }
  }, [lastEvent]);

  useEffect(() => {
    fetchDisplayStatuses();
    // Set up periodic refresh as fallback
    const interval = setInterval(fetchDisplayStatuses, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [fetchDisplayStatuses]);

  const getConnectionQualityBadge = (quality: string) => {
    const badges = {
      excellent: <Badge bg="success">Excellent</Badge>,
      good: <Badge bg="info">Good</Badge>,
      poor: <Badge bg="warning">Poor</Badge>,
      offline: <Badge bg="danger">Offline</Badge>
    };
    return badges[quality as keyof typeof badges] || <Badge bg="secondary">Unknown</Badge>;
  };

  const getConnectionQualityProgress = (quality: string) => {
    const variants = {
      excellent: { variant: 'success', value: 100 },
      good: { variant: 'info', value: 75 },
      poor: { variant: 'warning', value: 40 },
      offline: { variant: 'danger', value: 0 }
    };
    const config = variants[quality as keyof typeof variants] || { variant: 'secondary', value: 0 };
    return <ProgressBar variant={config.variant} now={config.value} className="mt-1" style={{ height: '6px' }} />;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const getPerformanceColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value <= thresholds.good) return 'success';
    if (value <= thresholds.warning) return 'warning';
    return 'danger';
  };

  const showDisplayDetail = (display: DisplayStatus) => {
    setSelectedDisplay(display);
    setShowDetailModal(true);
  };

  if (error) {
    return (
      <Alert variant="danger">
        <strong>Error loading display status:</strong> {error}
      </Alert>
    );
  }

  if (compact) {
    // Compact view for dashboard widgets
    return (
      <div className="display-status-compact">
        {displays.map(display => (
          <div key={display.id} className="d-flex justify-content-between align-items-center mb-2">
            <div>
              <strong>{display.name}</strong>
              {display.location && <small className="text-muted ms-2">({display.location})</small>}
            </div>
            <div className="d-flex align-items-center">
              {getConnectionQualityBadge(display.connection_quality)}
              {display.sse_connected && (
                <Badge bg="secondary" className="ms-1" title="SSE Connected">SSE</Badge>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <>
      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">
            {displayId ? 'Display Status' : 'Display Status Overview'}
          </h5>
          <div className="d-flex align-items-center">
            {connectionState === 'connected' ? (
              <Badge bg="success" className="me-2">Live Updates</Badge>
            ) : (
              <Badge bg="warning" className="me-2">No Real-time Updates</Badge>
            )}
            <Button variant="outline-secondary" size="sm" onClick={fetchDisplayStatuses}>
              Refresh
            </Button>
          </div>
        </Card.Header>
        <Card.Body>
          {displays.length === 0 ? (
            <Alert variant="info">No displays found.</Alert>
          ) : (
            <Table hover responsive>
              <thead>
                <tr>
                  <th>Display</th>
                  <th>Status</th>
                  <th>Connection</th>
                  <th>Last Seen</th>
                  <th>Current Slideshow</th>
                  <th>SSE</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {displays.map(display => (
                  <tr key={display.id}>
                    <td>
                      <div>
                        <strong>{display.name}</strong>
                        {display.location && (
                          <div className="small text-muted">{display.location}</div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div>
                        <Badge bg={display.is_online ? 'success' : 'danger'}>
                          {display.is_online ? 'Online' : 'Offline'}
                        </Badge>
                        {display.missed_heartbeats > 0 && (
                          <div className="small text-warning mt-1">
                            {display.missed_heartbeats} missed heartbeats
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div>
                        {getConnectionQualityBadge(display.connection_quality)}
                        {getConnectionQualityProgress(display.connection_quality)}
                      </div>
                    </td>
                    <td className="small text-muted">
                      {formatTimestamp(display.last_seen_at)}
                    </td>
                    <td>
                      {display.current_slideshow ? (
                        <Badge bg="info" pill>
                          {display.current_slideshow.name}
                        </Badge>
                      ) : (
                        <span className="text-muted">None assigned</span>
                      )}
                    </td>
                    <td>
                      {display.sse_connected ? (
                        <Badge bg="success" title="SSE Connection Active">
                          Connected
                        </Badge>
                      ) : (
                        <Badge bg="secondary" title="No SSE Connection">
                          Disconnected
                        </Badge>
                      )}
                    </td>
                    <td>
                      <Button
                        variant="outline-primary"
                        size="sm"
                        onClick={() => showDisplayDetail(display)}
                      >
                        Details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Display Detail Modal */}
      <Modal show={showDetailModal} onHide={() => setShowDetailModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            Display Details: {selectedDisplay?.name}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedDisplay && (
            <div>
              {/* Basic Information */}
              <div className="row mb-4">
                <div className="col-md-6">
                  <h6>Basic Information</h6>
                  <ul className="list-unstyled">
                    <li><strong>Name:</strong> {selectedDisplay.name}</li>
                    <li><strong>Location:</strong> {selectedDisplay.location || 'Not specified'}</li>
                    <li><strong>Status:</strong> {getConnectionQualityBadge(selectedDisplay.connection_quality)}</li>
                    <li><strong>Online:</strong> {selectedDisplay.is_online ? 'Yes' : 'No'}</li>
                  </ul>
                </div>
                <div className="col-md-6">
                  <h6>Connection Details</h6>
                  <ul className="list-unstyled">
                    <li><strong>Last Seen:</strong> {formatTimestamp(selectedDisplay.last_seen_at)}</li>
                    <li><strong>Heartbeat Interval:</strong> {selectedDisplay.heartbeat_interval}s</li>
                    <li><strong>Missed Heartbeats:</strong> {selectedDisplay.missed_heartbeats}</li>
                    <li><strong>SSE Connected:</strong> {selectedDisplay.sse_connected ? 'Yes' : 'No'}</li>
                  </ul>
                </div>
              </div>

              {/* Performance Metrics */}
              {selectedDisplay.performance_metrics && (
                <div className="mb-4">
                  <h6>Performance Metrics</h6>
                  <div className="row">
                    <div className="col-md-4">
                      <div className="text-center">
                        <div className={`text-${getPerformanceColor(selectedDisplay.performance_metrics.cpu_usage, { good: 50, warning: 80 })}`}>
                          <h4>{selectedDisplay.performance_metrics.cpu_usage}%</h4>
                        </div>
                        <p className="text-muted mb-0">CPU Usage</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="text-center">
                        <div className={`text-${getPerformanceColor(selectedDisplay.performance_metrics.memory_usage, { good: 60, warning: 85 })}`}>
                          <h4>{selectedDisplay.performance_metrics.memory_usage}%</h4>
                        </div>
                        <p className="text-muted mb-0">Memory Usage</p>
                      </div>
                    </div>
                    <div className="col-md-4">
                      <div className="text-center">
                        <div className={`text-${getPerformanceColor(selectedDisplay.performance_metrics.network_latency, { good: 100, warning: 500 })}`}>
                          <h4>{selectedDisplay.performance_metrics.network_latency}ms</h4>
                        </div>
                        <p className="text-muted mb-0">Network Latency</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Assignment */}
              <div className="mb-4">
                <h6>Current Assignment</h6>
                {selectedDisplay.current_slideshow ? (
                  <Alert variant="info">
                    <strong>Slideshow:</strong> {selectedDisplay.current_slideshow.name}
                  </Alert>
                ) : (
                  <Alert variant="warning">
                    No slideshow currently assigned to this display.
                  </Alert>
                )}
              </div>

              {/* Recent SSE Activity */}
              {selectedDisplay.last_sse_event && (
                <div>
                  <h6>Recent SSE Activity</h6>
                  <Alert variant="light">
                    <strong>Last Event:</strong> {selectedDisplay.last_sse_event}
                  </Alert>
                </div>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDetailModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default EnhancedDisplayStatus;
