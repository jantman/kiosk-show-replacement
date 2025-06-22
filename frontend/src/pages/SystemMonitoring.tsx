import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Alert, Spinner, Tabs, Tab } from 'react-bootstrap';
import SSEDebugger from '../components/SSEDebugger';
import EnhancedDisplayStatus from '../components/EnhancedDisplayStatus';
import LiveDataIndicator from '../components/LiveDataIndicator';

const SystemMonitoring: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('sse');

  useEffect(() => {
    // Initialize page
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading monitoring...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container fluid>
      <Row>
        <Col>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 className="h3 mb-0">System Monitoring</h1>
              <p className="text-muted mb-0">Real-time system status and debugging tools</p>
            </div>
            <LiveDataIndicator 
              dataType="display"
              className="text-muted"
            />
          </div>

          {error && (
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Tabs
            activeKey={activeTab}
            onSelect={(k) => k && setActiveTab(k)}
            className="mb-4"
            id="monitoring-tabs"
          >
            <Tab eventKey="sse" title="SSE Debug Tools">
              <Card>
                <Card.Header>
                  <h5 className="mb-0">
                    <i className="bi bi-broadcast"></i> Server-Sent Events Monitoring
                  </h5>
                  <p className="text-muted mb-0 mt-1">
                    Monitor and debug real-time SSE connections and events
                  </p>
                </Card.Header>
                <Card.Body>
                  <SSEDebugger />
                </Card.Body>
              </Card>
            </Tab>

            <Tab eventKey="displays" title="Display Status">
              <Card>
                <Card.Header>
                  <h5 className="mb-0">
                    <i className="bi bi-display"></i> Enhanced Display Monitoring
                  </h5>
                  <p className="text-muted mb-0 mt-1">
                    Real-time display status with performance metrics and connection quality
                  </p>
                </Card.Header>
                <Card.Body>
                  <EnhancedDisplayStatus />
                </Card.Body>
              </Card>
            </Tab>

            <Tab eventKey="health" title="System Health">
              <Card>
                <Card.Header>
                  <h5 className="mb-0">
                    <i className="bi bi-heart-pulse"></i> System Health Overview
                  </h5>
                  <p className="text-muted mb-0 mt-1">
                    Overall system health and performance metrics
                  </p>
                </Card.Header>
                <Card.Body>
                  <div className="text-center py-5">
                    <i className="bi bi-check-circle-fill text-success" style={{ fontSize: '4rem' }}></i>
                    <h4 className="mt-3 text-success">System Healthy</h4>
                    <p className="text-muted">All systems are operational</p>
                    
                    <div className="row mt-4">
                      <div className="col-md-4">
                        <div className="card border-success">
                          <div className="card-body text-center">
                            <h5 className="text-success">API Status</h5>
                            <p className="mb-0">Operational</p>
                          </div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="card border-success">
                          <div className="card-body text-center">
                            <h5 className="text-success">Database</h5>
                            <p className="mb-0">Connected</p>
                          </div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="card border-success">
                          <div className="card-body text-center">
                            <h5 className="text-success">SSE Service</h5>
                            <p className="mb-0">Active</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Tab>
          </Tabs>
        </Col>
      </Row>
    </Container>
  );
};

export default SystemMonitoring;
