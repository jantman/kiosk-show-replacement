import React, { useState, useEffect } from 'react';
import { Form, Button, Alert, Spinner, Row, Col } from 'react-bootstrap';
import { useApi } from '../hooks/useApi';
import { SlideshowItem } from '../types';

interface SlideshowItemFormProps {
  slideshowId: number;
  item?: SlideshowItem | null;
  onSave: () => void;
  onCancel: () => void;
}

// Form state uses backend field names for consistency
interface SlideshowItemFormState {
  title: string;
  content_type: 'image' | 'video' | 'url' | 'text';
  content_url: string;
  content_text: string;
  content_file_path: string;
  display_duration: number | null;
  is_active: boolean;
}

const SlideshowItemForm: React.FC<SlideshowItemFormProps> = ({
  slideshowId,
  item,
  onSave,
  onCancel
}) => {
  const { apiCall } = useApi();
  const isEditing = Boolean(item);

  const [formData, setFormData] = useState<SlideshowItemFormState>({
    title: '',
    content_type: 'image',
    content_url: '',
    content_text: '',
    content_file_path: '',
    display_duration: null,
    is_active: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [uploadingFile, setUploadingFile] = useState(false);

  useEffect(() => {
    if (item) {
      setFormData({
        title: item.title || '',
        content_type: item.content_type as 'image' | 'video' | 'url' | 'text',
        content_url: item.content_url || '',
        content_text: item.content_text || '',
        content_file_path: item.content_file_path || '',
        display_duration: item.display_duration ?? null,
        is_active: item.is_active,
      });
    }
  }, [item]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.title.trim()) {
      errors.title = 'Title is required';
    }

    if (formData.content_type === 'url' && !formData.content_url.trim()) {
      errors.content_url = 'URL is required for URL content type';
    } else if (formData.content_type === 'url' && formData.content_url.trim()) {
      try {
        new URL(formData.content_url);
      } catch {
        errors.content_url = 'Please enter a valid URL';
      }
    }

    if (formData.content_type === 'text' && !formData.content_text.trim()) {
      errors.content_text = 'Text content is required for text content type';
    }

    if ((formData.content_type === 'image' || formData.content_type === 'video') &&
        !formData.content_file_path && !formData.content_url) {
      errors.content = `Please upload a ${formData.content_type} file or provide a URL`;
    }

    if (formData.display_duration !== null && formData.display_duration <= 0) {
      errors.display_duration = 'Duration must be greater than 0';
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
        title: formData.title.trim(),
        content_type: formData.content_type,
        content_url:
          formData.content_type === 'url'
            ? (formData.content_url.trim() || null)
            : formData.content_type === 'text'
            ? null
            : formData.content_file_path
            ? null
            : (formData.content_url.trim() || null),
        content_text: formData.content_type === 'text' ? formData.content_text.trim() : null,
        content_file_path: formData.content_file_path || null,
        display_duration: formData.display_duration,
        is_active: formData.is_active,
      };

      let response;
      if (isEditing) {
        response = await apiCall(`/api/v1/slideshow-items/${item!.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });
      } else {
        response = await apiCall(`/api/v1/slideshows/${slideshowId}/items`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submitData),
        });
      }

      if (response.success) {
        onSave();
      } else {
        setError(response.error || 'Failed to save item');
      }
    } catch (err) {
      setError('Failed to save item');
      console.error('Error saving item:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file) return;

    try {
      setUploadingFile(true);
      setError(null);

      const uploadFormData = new FormData();
      uploadFormData.append('file', file);
      uploadFormData.append('slideshow_id', slideshowId.toString());

      const endpoint = file.type.startsWith('image/') ? 
        '/api/v1/uploads/image' : 
        '/api/v1/uploads/video';

      const response = await apiCall(endpoint, {
        method: 'POST',
        body: uploadFormData,
      });

      if (response.success) {
        const uploadData = response.data as { file_path: string };
        setFormData(prev => ({
          ...prev,
          content_file_path: uploadData.file_path,
          content_type: file.type.startsWith('image/') ? 'image' : 'video',
        }));
        // Clear any URL when file is uploaded
        if (formData.content_url) {
          setFormData(prev => ({ ...prev, content_url: '' }));
        }
      } else {
        setError(response.error || 'Failed to upload file');
      }
    } catch (err) {
      setError('Failed to upload file');
      console.error('Error uploading file:', err);
    } finally {
      setUploadingFile(false);
    }
  };

  const handleInputChange = (field: keyof SlideshowItemFormState, value: string | number | boolean | null) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const renderContentFields = () => {
    switch (formData.content_type) {
      case 'url':
        return (
          <Form.Group className="mb-3">
            <Form.Label htmlFor="url">URL *</Form.Label>
            <Form.Control
              id="url"
              type="url"
              value={formData.content_url}
              onChange={(e) => handleInputChange('content_url', e.target.value)}
              isInvalid={!!validationErrors.content_url}
              placeholder="https://example.com"
            />
            <Form.Control.Feedback type="invalid">
              {validationErrors.content_url}
            </Form.Control.Feedback>
            <Form.Text className="text-muted">
              Enter the URL of the webpage to display
            </Form.Text>
          </Form.Group>
        );

      case 'text':
        return (
          <Form.Group className="mb-3">
            <Form.Label htmlFor="text_content">Text Content *</Form.Label>
            <Form.Control
              id="text_content"
              as="textarea"
              rows={4}
              value={formData.content_text}
              onChange={(e) => handleInputChange('content_text', e.target.value)}
              isInvalid={!!validationErrors.content_text}
              placeholder="Enter the text to display"
            />
            <Form.Control.Feedback type="invalid">
              {validationErrors.content_text}
            </Form.Control.Feedback>
          </Form.Group>
        );

      case 'image':
      case 'video':
        return (
          <div>
            <Form.Group className="mb-3">
              <Form.Label htmlFor={`file_${formData.content_type}`}>Upload {formData.content_type} *</Form.Label>
              <Form.Control
                id={`file_${formData.content_type}`}
                type="file"
                accept={formData.content_type === 'image' ? 'image/*' : 'video/*'}
                onChange={(e) => {
                  const file = (e.target as HTMLInputElement).files?.[0];
                  if (file) {
                    handleFileUpload(file);
                  }
                }}
                disabled={uploadingFile}
              />
              {uploadingFile && (
                <div className="mt-2">
                  <Spinner animation="border" size="sm" className="me-2" />
                  Uploading...
                </div>
              )}
              {formData.content_file_path && (
                <div className="mt-2">
                  <span className="badge bg-success">
                    <i className="bi bi-check-lg me-1"></i>
                    File uploaded: {formData.content_file_path}
                  </span>
                </div>
              )}
              {validationErrors.content && (
                <div className="invalid-feedback d-block">
                  {validationErrors.content}
                </div>
              )}
            </Form.Group>

            <div className="text-center text-muted mb-3">
              <small>— OR —</small>
            </div>

            <Form.Group className="mb-3">
              <Form.Label htmlFor="url_alternative">Or use URL</Form.Label>
              <Form.Control
                id="url_alternative"
                type="url"
                value={formData.content_url}
                onChange={(e) => {
                  handleInputChange('content_url', e.target.value);
                  // Clear file path when URL is entered
                  if (e.target.value && formData.content_file_path) {
                    handleInputChange('content_file_path', '');
                  }
                }}
                placeholder={`https://example.com/${formData.content_type}.jpg`}
                disabled={uploadingFile}
              />
              <Form.Text className="text-muted">
                Alternatively, provide a direct URL to the {formData.content_type}
              </Form.Text>
            </Form.Group>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      {error && (
        <Alert variant="danger" className="mb-3">
          {error}
        </Alert>
      )}

      <Row>
        <Col md={6}>
          <Form.Group className="mb-3">
            <Form.Label htmlFor="title">Title *</Form.Label>
            <Form.Control
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              isInvalid={!!validationErrors.title}
              placeholder="Enter item title"
            />
            <Form.Control.Feedback type="invalid">
              {validationErrors.title}
            </Form.Control.Feedback>
          </Form.Group>
        </Col>
        <Col md={6}>
          <Form.Group className="mb-3">
            <Form.Label htmlFor="content_type">Content Type</Form.Label>
            <Form.Select
              id="content_type"
              value={formData.content_type}
              onChange={(e) => {
                handleInputChange('content_type', e.target.value);
                // Clear content-specific fields when type changes
                handleInputChange('content_url', '');
                handleInputChange('content_text', '');
                handleInputChange('content_file_path', '');
              }}
            >
              <option value="image">Image</option>
              <option value="video">Video</option>
              <option value="url">Web Page</option>
              <option value="text">Text</option>
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>

      {renderContentFields()}

      <Row>
        <Col md={6}>
          <Form.Group className="mb-3">
            <Form.Label htmlFor="duration">Duration Override (seconds)</Form.Label>
            <Form.Control
              id="duration"
              type="number"
              min="1"
              max="300"
              value={formData.display_duration || ''}
              onChange={(e) => handleInputChange('display_duration', e.target.value ? parseInt(e.target.value) : null)}
              isInvalid={!!validationErrors.display_duration}
              placeholder="Use slideshow default"
            />
            <Form.Control.Feedback type="invalid">
              {validationErrors.display_duration}
            </Form.Control.Feedback>
            <Form.Text className="text-muted">
              Leave empty to use the slideshow's default duration
            </Form.Text>
          </Form.Group>
        </Col>
        <Col md={6} className="d-flex align-items-center">
          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              id="is_active"
              label="Active"
              checked={formData.is_active}
              onChange={(e) => handleInputChange('is_active', e.target.checked)}
            />
            <Form.Text className="text-muted d-block">
              Only active items will be displayed
            </Form.Text>
          </Form.Group>
        </Col>
      </Row>

      <div className="d-flex gap-2 justify-content-end">
        <Button 
          type="button" 
          variant="outline-secondary"
          onClick={onCancel}
          disabled={loading || uploadingFile}
        >
          Cancel
        </Button>
        <Button 
          type="submit" 
          variant="primary" 
          disabled={loading || uploadingFile}
        >
          {loading ? (
            <>
              <Spinner animation="border" size="sm" className="me-2" />
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            <>
              <i className={`bi ${isEditing ? 'bi-check-lg' : 'bi-plus-circle'} me-2`}></i>
              {isEditing ? 'Update Item' : 'Add Item'}
            </>
          )}
        </Button>
      </div>
    </Form>
  );
};

export default SlideshowItemForm;
