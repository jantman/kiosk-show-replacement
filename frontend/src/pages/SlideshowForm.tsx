import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useApi } from '../hooks/useApi';
import { Slideshow } from '../types';

interface SlideshowFormData {
  name: string;
  description: string;
  default_item_duration: number;
  transition_type: string;
  is_active: boolean;
  is_default: boolean;
}

const SlideshowForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { apiCall } = useApi();
  const isEditing = Boolean(id);

  const [formData, setFormData] = useState<SlideshowFormData>({
    name: '',
    description: '',
    default_item_duration: 10,
    transition_type: 'fade',
    is_active: true,
    is_default: false,
  });
  
  const [loading, setLoading] = useState(false);
  const [loadingSlideshow, setLoadingSlideshow] = useState(isEditing);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isEditing && id) {
      fetchSlideshow(parseInt(id));
    }
  }, [id, isEditing]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchSlideshow = async (slideshowId: number) => {
    try {
      setLoadingSlideshow(true);
      setError(null);
      const response = await apiCall(`/api/v1/slideshows/${slideshowId}`);
      if (response.success) {
        const slideshow = response.data as Slideshow;
        setFormData({
          name: slideshow.name,
          description: slideshow.description || '',
          default_item_duration: slideshow.default_item_duration,
          transition_type: slideshow.transition_type || 'fade',
          is_active: slideshow.is_active,
          is_default: slideshow.is_default,
        });
      } else {
        setError(response.error || 'Failed to fetch slideshow');
      }
    } catch (err) {
      setError('Failed to fetch slideshow');
      console.error('Error fetching slideshow:', err);
    } finally {
      setLoadingSlideshow(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.name.trim()) {
      errors.name = 'Slideshow name is required';
    } else if (formData.name.length > 255) {
      errors.name = 'Slideshow name must be 255 characters or less';
    }

    if (formData.description.length > 1000) {
      errors.description = 'Description must be 1000 characters or less';
    }

    if (formData.default_item_duration <= 0) {
      errors.default_item_duration = 'Duration must be greater than 0';
    } else if (formData.default_item_duration > 300) {
      errors.default_item_duration = 'Duration must be 300 seconds or less';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const submitData = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        default_item_duration: formData.default_item_duration,
        transition_type: formData.transition_type,
        is_active: formData.is_active,
        is_default: formData.is_default,
      };

      let response;
      if (isEditing) {
        response = await apiCall(`/api/v1/slideshows/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });
      } else {
        response = await apiCall('/api/v1/slideshows', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });
      }

      if (response.success) {
        // Navigate to the slideshow detail page
        const slideshowId = isEditing ? id : (response.data as { id: number }).id;
        navigate(`/admin/slideshows/${slideshowId}`);
      } else {
        setError(response.error || 'Failed to save slideshow');
      }
    } catch (err) {
      setError('Failed to save slideshow');
      console.error('Error saving slideshow:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof SlideshowFormData, value: string | number | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  if (loadingSlideshow) {
    return (
      <Container className="mt-4">
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
          <p className="mt-2">Loading slideshow...</p>
        </div>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <Row className="mb-4">
        <Col>
          <div className="d-flex justify-content-between align-items-center">
            <h1>{isEditing ? 'Edit Slideshow' : 'Create New Slideshow'}</h1>
            <Button 
              variant="outline-secondary" 
              onClick={() => navigate('/admin/slideshows')}
            >
              <i className="bi bi-arrow-left me-2"></i>
              Back to Slideshows
            </Button>
          </div>
        </Col>
      </Row>

      {error && (
        <Row className="mb-3">
          <Col>
            <Alert variant="danger" dismissible onClose={() => setError(null)}>
              {error}
            </Alert>
          </Col>
        </Row>
      )}

      <Row>
        <Col lg={8}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Slideshow Details</h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label htmlFor="slideshow-name">Slideshow Name *</Form.Label>
                      <Form.Control
                        id="slideshow-name"
                        type="text"
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        isInvalid={!!validationErrors.name}
                        placeholder="Enter slideshow name"
                        maxLength={255}
                      />
                      <Form.Control.Feedback type="invalid">
                        {validationErrors.name}
                      </Form.Control.Feedback>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label htmlFor="default-item-duration">Default Item Duration (seconds)</Form.Label>
                      <Form.Control
                        id="default-item-duration"
                        type="number"
                        min="1"
                        max="300"
                        value={formData.default_item_duration}
                        onChange={(e) => handleInputChange('default_item_duration', parseInt(e.target.value) || 1)}
                        isInvalid={!!validationErrors.default_item_duration}
                      />
                      <Form.Control.Feedback type="invalid">
                        {validationErrors.default_item_duration}
                      </Form.Control.Feedback>
                      <Form.Text className="text-muted">
                        How long each slide should display by default
                      </Form.Text>
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <Form.Label htmlFor="description">Description</Form.Label>
                  <Form.Control
                    id="description"
                    as="textarea"
                    rows={3}
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    isInvalid={!!validationErrors.description}
                    placeholder="Optional description of this slideshow"
                    maxLength={1000}
                  />
                  <Form.Control.Feedback type="invalid">
                    {validationErrors.description}
                  </Form.Control.Feedback>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label htmlFor="transition-type">Transition Type</Form.Label>
                  <Form.Select
                    id="transition-type"
                    value={formData.transition_type}
                    onChange={(e) => handleInputChange('transition_type', e.target.value)}
                  >
                    <option value="fade">Fade</option>
                    <option value="slide">Slide</option>
                    <option value="none">None</option>
                  </Form.Select>
                  <Form.Text className="text-muted">
                    Animation between slides
                  </Form.Text>
                </Form.Group>

                <div className="mb-3">
                  <Form.Check
                    type="checkbox"
                    id="is_active"
                    label="Active"
                    checked={formData.is_active}
                    onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  />
                  <Form.Text className="text-muted d-block">
                    Only active slideshows can be assigned to displays
                  </Form.Text>
                </div>

                <div className="mb-4">
                  <Form.Check
                    type="checkbox"
                    id="is_default"
                    label="Set as Default Slideshow"
                    checked={formData.is_default}
                    onChange={(e) => handleInputChange('is_default', e.target.checked)}
                  />
                  <Form.Text className="text-muted d-block">
                    Default slideshow is automatically assigned to new displays
                  </Form.Text>
                </div>

                <div className="d-flex gap-2">
                  <Button 
                    type="submit" 
                    variant="primary" 
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        {isEditing ? 'Updating...' : 'Creating...'}
                      </>
                    ) : (
                      <>
                        <i className={`bi ${isEditing ? 'bi-check-lg' : 'bi-plus-circle'} me-2`}></i>
                        {isEditing ? 'Update Slideshow' : 'Create Slideshow'}
                      </>
                    )}
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline-secondary"
                    onClick={() => navigate('/admin/slideshows')}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        <Col lg={4}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Tips</h6>
            </Card.Header>
            <Card.Body>
              <div className="small text-muted">
                <p><strong>Name:</strong> Choose a descriptive name that makes it easy to identify this slideshow.</p>
                <p><strong>Duration:</strong> The default duration for each slide. Individual slides can override this setting.</p>
                <p><strong>Transitions:</strong> Smooth animations between slides can improve the viewing experience.</p>
                <p><strong>Default Slideshow:</strong> New displays will automatically use the default slideshow until manually assigned.</p>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default SlideshowForm;
