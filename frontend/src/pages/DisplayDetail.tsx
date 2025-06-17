import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../utils/apiClient';
import { Display, Slideshow } from '../types';

const DisplayDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [display, setDisplay] = useState<Display | null>(null);
  const [slideshows, setSlideshows] = useState<Slideshow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    description: '',
    current_slideshow_id: null as number | null,
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        setError(null);

        // Fetch display and slideshows in parallel
        const [displayResponse, slideshowsResponse] = await Promise.all([
          apiClient.getDisplay(parseInt(id)),
          apiClient.getSlideshows()
        ]);

        if (displayResponse.success && slideshowsResponse.success && displayResponse.data && slideshowsResponse.data) {
          setDisplay(displayResponse.data);
          setSlideshows(slideshowsResponse.data);
          
          // Initialize form data
          setFormData({
            name: displayResponse.data.name,
            location: displayResponse.data.location || '',
            description: displayResponse.data.description || '',
            current_slideshow_id: displayResponse.data.current_slideshow_id ?? null,
          });
        } else {
          setError('Failed to fetch display details');
        }
      } catch (err) {
        setError('Failed to fetch display details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleEdit = () => {
    setIsEditing(true);
    setMessage(null);
  };

  const handleCancel = () => {
    if (display) {
      setFormData({
        name: display.name,
        location: display.location || '',
        description: display.description || '',
        current_slideshow_id: display.current_slideshow_id ?? null,
      });
    }
    setIsEditing(false);
    setMessage(null);
  };

  const handleSave = async () => {
    if (!display) return;

    try {
      const response = await apiClient.updateDisplay(display.id, formData);
      
      if (response.success && response.data) {
        setDisplay(response.data);
        setIsEditing(false);
        setMessage('Display updated successfully');
      } else {
        setError('Failed to update display');
      }
    } catch (err) {
      setError('Failed to update display');
    }
  };

  const handleDelete = async () => {
    if (!display) return;

    try {
      const response = await apiClient.deleteDisplay(display.id);
      
      if (response.success) {
        navigate('/admin/displays', {
          state: { message: `Display "${display.name}" deleted successfully` }
        });
      } else {
        setError('Failed to delete display');
      }
    } catch (err) {
      setError('Failed to delete display');
    } finally {
      setShowDeleteModal(false);
    }
  };

  const formatLastSeen = (lastSeenAt: string | null | undefined) => {
    if (!lastSeenAt) return 'Never';
    
    const lastSeen = new Date(lastSeenAt);
    const now = new Date();
    const diffMs = now.getTime() - lastSeen.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getCurrentSlideshow = () => {
    if (!display?.current_slideshow_id) return null;
    return slideshows.find(s => s.id === display.current_slideshow_id);
  };

  const calculateDaysOnline = () => {
    if (!display?.created_at) return 0;
    const created = new Date(display.created_at);
    const now = new Date();
    const diffMs = now.getTime() - created.getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '200px' }}>
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (error && !display) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
      </div>
    );
  }

  if (!display) {
    return (
      <div className="alert alert-danger" role="alert">
        Display not found
      </div>
    );
  }

  const currentSlideshow = getCurrentSlideshow();

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col">
          {/* Header */}
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <nav aria-label="breadcrumb">
                <ol className="breadcrumb">
                  <li className="breadcrumb-item">
                    <Link to="/admin/displays">Displays</Link>
                  </li>
                  <li className="breadcrumb-item active" aria-current="page">
                    {display.name}
                  </li>
                </ol>
              </nav>
              <h1 className="h3 mb-0">Display Details</h1>
            </div>
            
            <div className="btn-group" role="group">
              <a 
                href={`/display/${display.name}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline-primary"
                title="View Display"
              >
                <i className="bi bi-box-arrow-up-right"></i> View Display
              </a>
              <button 
                className="btn btn-outline-secondary"
                onClick={() => window.location.reload()}
                title="Refresh Status"
              >
                <i className="bi bi-arrow-clockwise"></i> Refresh
              </button>
            </div>
          </div>

          {/* Messages */}
          {message && (
            <div className="alert alert-success alert-dismissible fade show" role="alert">
              {message}
              <button 
                type="button" 
                className="btn-close" 
                onClick={() => setMessage(null)}
                aria-label="Close"
              ></button>
            </div>
          )}

          {error && (
            <div className="alert alert-danger alert-dismissible fade show" role="alert">
              {error}
              <button 
                type="button" 
                className="btn-close" 
                onClick={() => setError(null)}
                aria-label="Close"
              ></button>
            </div>
          )}

          <div className="row">
            {/* Main Info Card */}
            <div className="col-lg-8">
              <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <h5 className="card-title mb-0">Display Information</h5>
                  <div className="btn-group btn-group-sm">
                    {!isEditing ? (
                      <>
                        <button 
                          className="btn btn-outline-primary"
                          onClick={handleEdit}
                        >
                          <i className="bi bi-pencil"></i> Edit Display
                        </button>
                        <button 
                          className="btn btn-outline-danger"
                          onClick={() => setShowDeleteModal(true)}
                        >
                          <i className="bi bi-trash"></i> Delete Display
                        </button>
                      </>
                    ) : (
                      <>
                        <button 
                          className="btn btn-success"
                          onClick={handleSave}
                        >
                          <i className="bi bi-check"></i> Save Changes
                        </button>
                        <button 
                          className="btn btn-secondary"
                          onClick={handleCancel}
                        >
                          <i className="bi bi-x"></i> Cancel
                        </button>
                      </>
                    )}
                  </div>
                </div>
                <div className="card-body">
                  {!isEditing ? (
                    <div className="table-responsive">
                      <table className="table table-borderless">
                        <tbody>
                          <tr>
                            <td className="fw-bold" style={{ width: '200px' }}>Name:</td>
                            <td>{display.name}</td>
                          </tr>
                          <tr>
                            <td className="fw-bold">Location:</td>
                            <td>{display.location || <span className="text-muted">Not specified</span>}</td>
                          </tr>
                          <tr>
                            <td className="fw-bold">Description:</td>
                            <td>{display.description || <span className="text-muted">No description</span>}</td>
                          </tr>
                          <tr>
                            <td className="fw-bold">Resolution:</td>
                            <td>{display.resolution}</td>
                          </tr>
                          <tr>
                            <td className="fw-bold">Current Slideshow:</td>
                            <td>
                              {currentSlideshow ? (
                                <Link 
                                  to={`/admin/slideshows/${currentSlideshow.id}`}
                                  className="text-decoration-none"
                                >
                                  {currentSlideshow.name}
                                </Link>
                              ) : (
                                <span className="text-muted">None</span>
                              )}
                            </td>
                          </tr>
                          <tr>
                            <td className="fw-bold">Created:</td>
                            <td>{new Date(display.created_at).toLocaleString()}</td>
                          </tr>
                          <tr>
                            <td className="fw-bold">Last Updated:</td>
                            <td>{new Date(display.updated_at).toLocaleString()}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <form>
                      <div className="row">
                        <div className="col-md-6">
                          <div className="mb-3">
                            <label htmlFor="name" className="form-label">Name</label>
                            <input
                              type="text"
                              className="form-control"
                              id="name"
                              value={formData.name}
                              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                              required
                            />
                          </div>
                        </div>
                        <div className="col-md-6">
                          <div className="mb-3">
                            <label htmlFor="location" className="form-label">Location</label>
                            <input
                              type="text"
                              className="form-control"
                              id="location"
                              value={formData.location}
                              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                            />
                          </div>
                        </div>
                      </div>
                      
                      <div className="mb-3">
                        <label htmlFor="description" className="form-label">Description</label>
                        <textarea
                          className="form-control"
                          id="description"
                          rows={3}
                          value={formData.description}
                          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        />
                      </div>

                      <div className="mb-3">
                        <label htmlFor="slideshow" className="form-label">Assigned Slideshow</label>
                        <select
                          className="form-select"
                          id="slideshow"
                          value={formData.current_slideshow_id || ''}
                          onChange={(e) => setFormData({ 
                            ...formData, 
                            current_slideshow_id: e.target.value ? parseInt(e.target.value) : null 
                          })}
                        >
                          <option value="">No slideshow assigned</option>
                          {slideshows.filter(s => s.is_active).map(slideshow => (
                            <option key={slideshow.id} value={slideshow.id}>
                              {slideshow.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="col-lg-4">
              {/* Status Card */}
              <div className="card mb-3">
                <div className="card-header">
                  <h6 className="card-title mb-0">Status</h6>
                </div>
                <div className="card-body">
                  <div className="d-flex align-items-center mb-2">
                    <span className="me-2">Connection:</span>
                    <span className={`badge ${display.is_online ? 'bg-success' : 'bg-secondary'}`}>
                      {display.is_online ? 'Online' : 'Offline'}
                    </span>
                  </div>
                  <div className="d-flex align-items-center mb-2">
                    <span className="me-2">Last Seen:</span>
                    <span className="text-muted">{formatLastSeen(display.last_seen_at)}</span>
                  </div>
                  <div className="d-flex align-items-center">
                    <span className="me-2">Heartbeat:</span>
                    <span className="text-muted">{display.heartbeat_interval}s</span>
                  </div>
                </div>
              </div>

              {/* Statistics Card */}
              <div className="card">
                <div className="card-header">
                  <h6 className="card-title mb-0">Statistics</h6>
                </div>
                <div className="card-body">
                  <div className="d-flex align-items-center mb-2">
                    <span className="me-2">Display ID:</span>
                    <span className="text-muted">#{display.id}</span>
                  </div>
                  <div className="d-flex align-items-center mb-2">
                    <span className="me-2">Days Online:</span>
                    <span className="text-muted">{calculateDaysOnline()}</span>
                  </div>
                  <div className="d-flex align-items-center">
                    <span className="me-2">Rotation:</span>
                    <span className="text-muted">{display.rotation}°</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal fade show" style={{ display: 'block' }} tabIndex={-1}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Delete Display</h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowDeleteModal(false)}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                <p>Are you sure you want to delete display <strong>"{display.name}"</strong>?</p>
                <p className="text-muted">This action cannot be undone.</p>
              </div>
              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowDeleteModal(false)}
                >
                  Cancel
                </button>
                <button 
                  type="button" 
                  className="btn btn-danger"
                  onClick={handleDelete}
                >
                  Delete Display
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal backdrop */}
      {showDeleteModal && (
        <div 
          className="modal-backdrop fade show"
          onClick={() => setShowDeleteModal(false)}
        ></div>
      )}
    </div>
  );
};

export default DisplayDetail;
