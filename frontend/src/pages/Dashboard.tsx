import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Alert, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useDisplayEvents, useSlideshowEvents } from '../hooks/useSSE';
import apiClient from '../utils/apiClient';
import type { Slideshow, Display } from '../types';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [slideshows, setSlideshows] = useState<Slideshow[]>([]);
  const [displays, setDisplays] = useState<Display[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Real-time updates via SSE
  const handleDisplayUpdate = (updatedDisplay: Display) => {
    setDisplays(prevDisplays => 
      prevDisplays.map(display => 
        display.id === updatedDisplay.id ? updatedDisplay : display
      )
    );
  };

  const handleSlideshowUpdate = (updatedSlideshow: Slideshow) => {
    setSlideshows(prevSlideshows => 
      prevSlideshows.map(slideshow => 
        slideshow.id === updatedSlideshow.id ? updatedSlideshow : slideshow
      )
    );
  };

  useDisplayEvents(handleDisplayUpdate);
  useSlideshowEvents(handleSlideshowUpdate);

  const loadDashboardData = async () => {
    setLoading(true);
    setError('');

    try {
      const [slideshowsResponse, displaysResponse] = await Promise.all([
        apiClient.getSlideshows(),
        apiClient.getDisplays(),
      ]);

      if (slideshowsResponse.success && slideshowsResponse.data) {
        setSlideshows(slideshowsResponse.data);
      } else {
        console.error('Failed to load slideshows:', slideshowsResponse.error);
      }

      if (displaysResponse.success && displaysResponse.data) {
        setDisplays(displaysResponse.data);
      } else {
        console.error('Failed to load displays:', displaysResponse.error);
      }
    } catch (err) {
      console.error('Dashboard data loading error:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const activeSlideShows = slideshows.filter(s => s.is_active);
  const onlineDisplays = displays.filter(d => d.is_online);
  const assignedDisplays = displays.filter(d => d.current_slideshow_id);

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <div className="mt-2">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Dashboard</h1>
        <div className="text-muted">
          Welcome back, <strong>{user?.username}</strong>
        </div>
      </div>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-primary">{activeSlideShows.length}</h3>
              <p className="text-muted mb-0">Active Slideshows</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-success">{onlineDisplays.length}</h3>
              <p className="text-muted mb-0">Online Displays</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-info">{assignedDisplays.length}</h3>
              <p className="text-muted mb-0">Assigned Displays</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <h3 className="text-warning">{displays.length - onlineDisplays.length}</h3>
              <p className="text-muted mb-0">Offline Displays</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        {/* Recent Slideshows */}
        <Col md={6}>
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Recent Slideshows</h5>
              <Link to="/admin/slideshows" className="btn btn-outline-primary btn-sm">
                View All
              </Link>
            </Card.Header>
            <Card.Body>
              {activeSlideShows.length === 0 ? (
                <div className="text-center text-muted py-3">
                  <p>No active slideshows found.</p>
                  <Link to="/admin/slideshows/new" className="btn btn-primary btn-sm">
                    Create First Slideshow
                  </Link>
                </div>
              ) : (
                <div className="list-group list-group-flush">
                  {activeSlideShows.slice(0, 5).map((slideshow) => (
                    <div key={slideshow.id} className="list-group-item border-0 px-0">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <h6 className="mb-1">{slideshow.name}</h6>
                          <p className="mb-1 text-muted small">
                            {slideshow.item_count} items • {slideshow.total_duration}s total
                          </p>
                          <small className="text-muted">
                            Updated {new Date(slideshow.updated_at).toLocaleDateString()}
                          </small>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Display Status */}
        <Col md={6}>
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Display Status</h5>
              <Link to="/admin/displays" className="btn btn-outline-primary btn-sm">
                View All
              </Link>
            </Card.Header>
            <Card.Body>
              {displays.length === 0 ? (
                <div className="text-center text-muted py-3">
                  <p>No displays registered yet.</p>
                  <small>Displays will appear here when they connect to the system.</small>
                </div>
              ) : (
                <div className="list-group list-group-flush">
                  {displays.slice(0, 5).map((display) => (
                    <div key={display.id} className="list-group-item border-0 px-0">
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          <h6 className="mb-1">{display.name}</h6>
                          <small className="text-muted">
                            {display.location && `${display.location} • `}
                            {display.resolution_width}x{display.resolution_height}
                          </small>
                        </div>
                        <span 
                          className={`badge ${display.is_online ? 'bg-success' : 'bg-secondary'}`}
                        >
                          {display.is_online ? 'Online' : 'Offline'}
                        </span>
                      </div>
                      {display.assigned_slideshow && (
                        <small className="text-info d-block mt-1">
                          Showing: {display.assigned_slideshow.name}
                        </small>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Quick Actions</h5>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={4}>
                  <Link to="/admin/slideshows/new" className="btn btn-primary w-100 mb-2">
                    Create New Slideshow
                  </Link>
                </Col>
                <Col md={4}>
                  <Link to="/admin/slideshows" className="btn btn-outline-primary w-100 mb-2">
                    Manage Slideshows
                  </Link>
                </Col>
                <Col md={4}>
                  <Link to="/admin/displays" className="btn btn-outline-secondary w-100 mb-2">
                    Monitor Displays
                  </Link>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
