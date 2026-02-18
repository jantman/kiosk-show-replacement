import React, { useState, useEffect } from 'react';
import { Form, Button, Alert, Spinner, Row, Col } from 'react-bootstrap';
import { useApi } from '../hooks/useApi';
import { SlideshowItem, Display } from '../types';

interface SlideshowItemFormProps {
  slideshowId: number;
  item?: SlideshowItem | null;
  onSave: () => void;
  onCancel: () => void;
}

// Form state uses backend field names for consistency
interface SlideshowItemFormState {
  title: string;
  content_type: 'image' | 'video' | 'url' | 'text' | 'skedda';
  content_url: string;
  content_text: string;
  content_file_path: string;
  display_duration: number | null;
  is_active: boolean;
  // URL slide scaling: zoom percentage (10-100). null = no scaling (100%)
  scale_factor: number | null;
  // Skedda/iCal calendar fields
  ical_url: string;
  ical_refresh_minutes: number;
}

/**
 * Extract a title from a filename by removing the extension.
 * @param filename - The filename (e.g., "my-image.jpg")
 * @returns The filename without extension (e.g., "my-image")
 */
const extractTitleFromFilename = (filename: string): string => {
  // Remove the extension
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex > 0) {
    return filename.substring(0, lastDotIndex);
  }
  return filename;
};

/**
 * Extract a title from a URL.
 * If the URL has a filename in the path, use that (without extension).
 * Otherwise, return an empty string (don't use the full URL as title).
 * @param url - The URL (e.g., "https://example.com/path/to/image.jpg")
 * @returns The extracted title or empty string
 */
const extractTitleFromUrl = (url: string): string => {
  try {
    const parsedUrl = new URL(url);
    const pathname = parsedUrl.pathname;
    // Get the last segment of the path
    const segments = pathname.split('/').filter(s => s.length > 0);
    if (segments.length > 0) {
      const lastSegment = segments[segments.length - 1];
      // Only use it if it looks like a filename (has an extension)
      if (lastSegment.includes('.')) {
        return extractTitleFromFilename(lastSegment);
      }
    }
  } catch {
    // Invalid URL, return empty string
  }
  return '';
};

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
    scale_factor: null,
    ical_url: '',
    ical_refresh_minutes: 15,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [uploadingFile, setUploadingFile] = useState(false);
  // Track if duration was auto-detected from video (makes field read-only)
  const [videoDurationDetected, setVideoDurationDetected] = useState(false);
  // Track preview iframe state for URL slides
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  // Track video URL validation state
  const [validatingVideoUrl, setValidatingVideoUrl] = useState(false);
  const [videoUrlValidated, setVideoUrlValidated] = useState(false);
  const [videoUrlError, setVideoUrlError] = useState<string | null>(null);
  // Display selector for URL preview
  const [displays, setDisplays] = useState<Display[]>([]);
  const [selectedDisplayId, setSelectedDisplayId] = useState<number | null>(null);

  useEffect(() => {
    if (item) {
      setFormData({
        title: item.title || '',
        content_type: item.content_type as 'image' | 'video' | 'url' | 'text' | 'skedda',
        content_url: item.content_url || '',
        content_text: item.content_text || '',
        content_file_path: item.content_file_path || '',
        display_duration: item.display_duration ?? null,
        is_active: item.is_active,
        scale_factor: item.scale_factor ?? null,
        ical_url: item.ical_url || '',
        ical_refresh_minutes: item.ical_refresh_minutes ?? 15,
      });
    }
  }, [item]);

  // Fetch displays when content_type is 'url' (for preview display selector)
  useEffect(() => {
    if (formData.content_type === 'url') {
      const fetchDisplays = async () => {
        try {
          const response = await apiCall('/api/v1/displays');
          if (response.success && Array.isArray(response.data)) {
            // Filter to non-archived displays with resolution data
            const filtered = (response.data as Display[]).filter(
              d => !d.is_archived && d.resolution_width && d.resolution_height
            );
            setDisplays(filtered);
          }
        } catch {
          // Silently fail - display selector is optional
        }
      };
      fetchDisplays();
    } else {
      setDisplays([]);
      setSelectedDisplayId(null);
    }
  }, [formData.content_type]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Get effective dimensions for a display, accounting for rotation.
   * When rotation is 90 or 270, width and height are swapped.
   */
  const getEffectiveDimensions = (display: Display): { width: number; height: number } => {
    const w = display.resolution_width || 1920;
    const h = display.resolution_height || 1080;
    if (display.rotation === 90 || display.rotation === 270) {
      return { width: h, height: w };
    }
    return { width: w, height: h };
  };

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

    // Skedda validation
    if (formData.content_type === 'skedda') {
      if (!formData.ical_url.trim()) {
        errors.ical_url = 'iCal URL is required for Skedda calendar';
      } else {
        try {
          const url = new URL(formData.ical_url);
          if (url.protocol !== 'http:' && url.protocol !== 'https:') {
            errors.ical_url = 'URL must start with http:// or https://';
          }
        } catch {
          errors.ical_url = 'Please enter a valid URL';
        }
      }
    }

    // Check for video URL validation errors (when using URL, not file)
    if (formData.content_type === 'video' && formData.content_url && !formData.content_file_path) {
      if (videoUrlError) {
        errors.content = videoUrlError;
      } else if (!videoUrlValidated && !validatingVideoUrl) {
        // URL entered but not validated yet
        errors.content = 'Please wait for video URL validation to complete';
      }
    }

    if (formData.display_duration !== null && formData.display_duration <= 0) {
      errors.display_duration = 'Duration must be greater than 0';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Block submission while validating video URL
    if (validatingVideoUrl) {
      return;
    }

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Determine content_url based on content type
      const getContentUrl = (): string | null => {
        switch (formData.content_type) {
          case 'url':
            // URL type always uses content_url
            return formData.content_url.trim() || null;
          case 'text':
            // Text type never has a URL
            return null;
          case 'image':
          case 'video':
            // Image/video use URL only if no file was uploaded
            return formData.content_file_path ? null : (formData.content_url.trim() || null);
          default:
            return null;
        }
      };

      const submitData: Record<string, unknown> = {
        title: formData.title.trim(),
        content_type: formData.content_type,
        content_url: getContentUrl(),
        content_text: formData.content_type === 'text' ? formData.content_text.trim() : null,
        content_file_path: formData.content_file_path || null,
        display_duration: formData.display_duration,
        is_active: formData.is_active,
        // Only include scale_factor for URL content type
        scale_factor: formData.content_type === 'url' ? formData.scale_factor : null,
      };

      // Add skedda-specific fields
      if (formData.content_type === 'skedda') {
        submitData.ical_url = formData.ical_url.trim();
        submitData.ical_refresh_minutes = formData.ical_refresh_minutes;
      }

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
        const uploadData = response.data as {
          file_path: string;
          duration_seconds?: number;
        };
        const isVideo = file.type.startsWith('video/');

        setFormData(prev => {
          // Auto-populate title from filename if title is empty
          const autoTitle = prev.title.trim() === ''
            ? extractTitleFromFilename(file.name)
            : prev.title;

          return {
            ...prev,
            title: autoTitle,
            content_file_path: uploadData.file_path,
            content_type: isVideo ? 'video' : 'image',
            // For videos, set duration from ffprobe detection
            display_duration: isVideo && uploadData.duration_seconds
              ? uploadData.duration_seconds
              : prev.display_duration,
            // Clear any URL when file is uploaded
            content_url: '',
          };
        });

        // Track if video duration was auto-detected
        if (isVideo && uploadData.duration_seconds) {
          setVideoDurationDetected(true);
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

  /**
   * Handle URL field blur - auto-populate title from URL if title is empty
   */
  const handleUrlBlur = (url: string) => {
    if (formData.title.trim() === '' && url.trim() !== '') {
      const autoTitle = extractTitleFromUrl(url);
      if (autoTitle) {
        setFormData(prev => ({ ...prev, title: autoTitle }));
      }
    }
  };

  /**
   * Validate a video URL - check format and codec compatibility, extract duration
   */
  const validateVideoUrl = async (url: string) => {
    // Clear previous validation state
    setVideoUrlValidated(false);
    setVideoUrlError(null);

    // Skip validation if URL is empty or not a valid URL format
    if (!url.trim()) {
      return;
    }

    try {
      new URL(url);
    } catch {
      setVideoUrlError('Please enter a valid URL');
      return;
    }

    // Must be http or https
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setVideoUrlError('URL must start with http:// or https://');
      return;
    }

    setValidatingVideoUrl(true);

    try {
      const response = await apiCall('/api/v1/validate/video-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      if (response.success && response.data) {
        const data = response.data as {
          valid: boolean;
          duration_seconds: number | null;
          duration: number | null;
          codec_info: {
            video_codec: string | null;
            audio_codec: string | null;
            container_format: string | null;
          } | null;
        };

        setVideoUrlValidated(true);
        setVideoUrlError(null);

        // Auto-populate duration if detected and no duration is currently set
        if (data.duration_seconds !== null && formData.display_duration === null) {
          setFormData(prev => ({
            ...prev,
            display_duration: data.duration_seconds,
          }));
          setVideoDurationDetected(true);
        }
      } else {
        setVideoUrlValidated(false);
        setVideoUrlError(response.error || 'Video URL validation failed');
      }
    } catch (err) {
      setVideoUrlValidated(false);
      setVideoUrlError('Failed to validate video URL');
      console.error('Error validating video URL:', err);
    } finally {
      setValidatingVideoUrl(false);
    }
  };

  /**
   * Handle video URL field blur - validate the URL
   */
  const handleVideoUrlBlur = (url: string) => {
    // Auto-populate title first
    handleUrlBlur(url);

    // Then validate the video URL if content type is video and there's no uploaded file
    if (formData.content_type === 'video' && !formData.content_file_path && url.trim()) {
      validateVideoUrl(url);
    }
  };

  const renderContentFields = () => {
    switch (formData.content_type) {
      case 'url':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label htmlFor="url">URL *</Form.Label>
              <Form.Control
                id="url"
                type="url"
                value={formData.content_url}
                onChange={(e) => {
                  handleInputChange('content_url', e.target.value);
                  // Reset preview state when URL changes
                  setPreviewLoading(true);
                  setPreviewError(false);
                }}
                onBlur={(e) => handleUrlBlur(e.target.value)}
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

            <Form.Group className="mb-3">
              <Form.Label htmlFor="scale_factor">
                Zoom: {formData.scale_factor === null || formData.scale_factor === 100
                  ? 'Normal (100%)'
                  : `Zoomed out (${formData.scale_factor}%)`}
              </Form.Label>
              <Form.Range
                id="scale_factor"
                min={10}
                max={100}
                step={5}
                value={formData.scale_factor ?? 100}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  // Treat 100 as null (no scaling)
                  handleInputChange('scale_factor', value === 100 ? null : value);
                }}
              />
              <div className="d-flex justify-content-between text-muted small">
                <span>Zoomed out (10%)</span>
                <span>Normal (100%)</span>
              </div>
              <Form.Text className="text-muted">
                {formData.scale_factor !== null && formData.scale_factor < 100
                  ? `The webpage will be scaled to ${formData.scale_factor}% to show more content. Use this if the page is too tall to fit on the display.`
                  : 'Slide the zoom to the left to show more of the webpage content. Use this when the page is cut off.'}
              </Form.Text>
            </Form.Group>

            {/* Preview iframe for URL slides */}
            {formData.content_url.trim() && (
              <>
                {displays.length > 0 && (
                  <Form.Group className="mb-3">
                    <Form.Label htmlFor="preview_display">Preview Display</Form.Label>
                    <Form.Select
                      id="preview_display"
                      value={selectedDisplayId ?? ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSelectedDisplayId(val ? parseInt(val) : null);
                      }}
                      data-testid="preview-display-selector"
                    >
                      <option value="">Default (16:9)</option>
                      {displays.map(d => {
                        const eff = getEffectiveDimensions(d);
                        const rotated = d.rotation === 90 || d.rotation === 270;
                        const label = `${d.name}${d.location ? ` - ${d.location}` : ''} (${eff.width}x${eff.height}${rotated ? ', rotated' : ''})`;
                        return (
                          <option key={d.id} value={d.id}>{label}</option>
                        );
                      })}
                    </Form.Select>
                    {selectedDisplayId && (() => {
                      const display = displays.find(d => d.id === selectedDisplayId);
                      if (!display) return null;
                      const eff = getEffectiveDimensions(display);
                      return (
                        <Form.Text className="text-muted" data-testid="preview-display-info">
                          Resolution: {eff.width}x{eff.height}
                          {(display.rotation === 90 || display.rotation === 270) && ' (rotated)'}
                        </Form.Text>
                      );
                    })()}
                  </Form.Group>
                )}

                <Form.Group className="mb-3">
                  <Form.Label>Preview</Form.Label>
                  <div
                    className="border rounded position-relative"
                    style={(() => {
                      let aspectRatio = '16 / 9';
                      if (selectedDisplayId) {
                        const display = displays.find(d => d.id === selectedDisplayId);
                        if (display) {
                          const eff = getEffectiveDimensions(display);
                          aspectRatio = `${eff.width} / ${eff.height}`;
                        }
                      }
                      return {
                        width: '100%',
                        maxWidth: '400px',
                        aspectRatio,
                        overflow: 'hidden',
                        background: '#f8f9fa'
                      };
                    })()}
                    data-testid="url-preview-container"
                  >
                    {previewLoading && !previewError && (
                      <div
                        className="position-absolute top-50 start-50 translate-middle text-muted"
                        data-testid="preview-loading"
                      >
                        <Spinner animation="border" size="sm" className="me-2" />
                        Loading preview...
                      </div>
                    )}
                    {previewError && (
                      <div
                        className="position-absolute top-50 start-50 translate-middle text-center text-muted"
                        data-testid="preview-error"
                      >
                        <i className="bi bi-exclamation-triangle fs-4 d-block mb-1"></i>
                        <small>Preview unavailable<br />(page may block embedding)</small>
                      </div>
                    )}
                    {(() => {
                      // Calculate iframe scaling to match display template behavior
                      const scaleFactor = formData.scale_factor ?? 100;
                      const scale = scaleFactor / 100;
                      const inverseScale = 100 / scaleFactor;

                      return (
                        <iframe
                          src={formData.content_url}
                          title="URL Preview"
                          style={{
                            width: `${inverseScale * 100}%`,
                            height: `${inverseScale * 100}%`,
                            transform: `scale(${scale})`,
                            transformOrigin: '0 0',
                            border: 'none',
                            opacity: previewLoading && !previewError ? 0 : 1,
                            display: previewError ? 'none' : 'block'
                          }}
                          sandbox="allow-scripts allow-same-origin"
                          onLoad={() => {
                            setPreviewLoading(false);
                            setPreviewError(false);
                          }}
                          onError={() => {
                            setPreviewLoading(false);
                            setPreviewError(true);
                          }}
                          data-testid="url-preview-iframe"
                        />
                      );
                    })()}
                  </div>
                  <Form.Text className="text-muted">
                    {selectedDisplayId ? (() => {
                      const display = displays.find(d => d.id === selectedDisplayId);
                      if (!display) return 'Preview shows how the zoomed webpage will appear on the display';
                      const eff = getEffectiveDimensions(display);
                      return `Preview shows how the zoomed webpage will appear on ${display.name} (${eff.width}x${eff.height})`;
                    })() : 'Preview shows how the zoomed webpage will appear on the display'}
                  </Form.Text>
                </Form.Group>
              </>
            )}
          </>
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
              {item && formData.content_file_path ? (
                <>
                  <div className="mb-2">
                    <span className="badge bg-success">
                      <i className="bi bi-check-lg me-1"></i>
                      Current file: {formData.content_file_path}
                    </span>
                  </div>
                  <Form.Label htmlFor={`file_${formData.content_type}`}>Replace {formData.content_type} (optional)</Form.Label>
                </>
              ) : (
                <Form.Label htmlFor={`file_${formData.content_type}`}>Upload {formData.content_type} *</Form.Label>
              )}
              <Form.Control
                id={`file_${formData.content_type}`}
                type="file"
                accept={formData.content_type === 'image' ? 'image/*' : 'video/*'}
                onChange={(e) => {
                  const file = (e.target as HTMLInputElement).files?.[0];
                  if (file) {
                    handleFileUpload(file);
                    // Clear video URL validation state when file is uploaded
                    if (formData.content_type === 'video') {
                      setVideoUrlValidated(false);
                      setVideoUrlError(null);
                    }
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
              {formData.content_file_path && !item && (
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
                  // Reset video URL validation state when URL changes
                  if (formData.content_type === 'video') {
                    setVideoUrlValidated(false);
                    setVideoUrlError(null);
                  }
                }}
                onBlur={(e) => {
                  if (formData.content_type === 'video') {
                    handleVideoUrlBlur(e.target.value);
                  } else {
                    handleUrlBlur(e.target.value);
                  }
                }}
                placeholder={`https://example.com/${formData.content_type}.${formData.content_type === 'video' ? 'mp4' : 'jpg'}`}
                disabled={uploadingFile || validatingVideoUrl}
                isInvalid={formData.content_type === 'video' && !!videoUrlError}
                isValid={formData.content_type === 'video' && videoUrlValidated && !formData.content_file_path}
              />
              {formData.content_type === 'video' && validatingVideoUrl && (
                <div className="mt-2">
                  <Spinner animation="border" size="sm" className="me-2" />
                  Validating video URL...
                </div>
              )}
              {formData.content_type === 'video' && videoUrlValidated && !formData.content_file_path && (
                <div className="mt-2">
                  <span className="badge bg-success">
                    <i className="bi bi-check-lg me-1"></i>
                    Video URL validated
                  </span>
                </div>
              )}
              {formData.content_type === 'video' && videoUrlError && (
                <Form.Control.Feedback type="invalid">
                  {videoUrlError}
                </Form.Control.Feedback>
              )}
              <Form.Text className="text-muted">
                {formData.content_type === 'video'
                  ? 'Video URL will be validated for browser compatibility (H.264, VP8, VP9 codecs)'
                  : `Alternatively, provide a direct URL to the ${formData.content_type}`}
              </Form.Text>
            </Form.Group>
          </div>
        );

      case 'skedda':
        return (
          <>
            <Form.Group className="mb-3">
              <Form.Label htmlFor="ical_url">iCal/ICS Feed URL *</Form.Label>
              <Form.Control
                id="ical_url"
                type="url"
                value={formData.ical_url}
                onChange={(e) => handleInputChange('ical_url', e.target.value)}
                isInvalid={!!validationErrors.ical_url}
                placeholder="https://app.skedda.com/ical/..."
              />
              <Form.Control.Feedback type="invalid">
                {validationErrors.ical_url}
              </Form.Control.Feedback>
              <Form.Text className="text-muted">
                Enter the iCal/ICS feed URL from Skedda or another calendar system
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label htmlFor="ical_refresh_minutes">Refresh Interval</Form.Label>
              <Form.Select
                id="ical_refresh_minutes"
                value={formData.ical_refresh_minutes}
                onChange={(e) => handleInputChange('ical_refresh_minutes', parseInt(e.target.value))}
              >
                <option value={5}>Every 5 minutes</option>
                <option value={10}>Every 10 minutes</option>
                <option value={15}>Every 15 minutes (default)</option>
                <option value={30}>Every 30 minutes</option>
                <option value={60}>Every hour</option>
              </Form.Select>
              <Form.Text className="text-muted">
                How often to refresh the calendar data from the feed
              </Form.Text>
            </Form.Group>
          </>
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
                // Reset scale_factor when changing away from URL type
                handleInputChange('scale_factor', null);
                // Reset skedda fields when changing away from skedda type
                handleInputChange('ical_url', '');
                handleInputChange('ical_refresh_minutes', 15);
                // Reset video duration detection flag (but keep user-entered duration)
                setVideoDurationDetected(false);
                // Reset video URL validation state
                setVideoUrlValidated(false);
                setVideoUrlError(null);
              }}
            >
              <option value="image">Image</option>
              <option value="video">Video</option>
              <option value="url">Web Page</option>
              <option value="text">Text</option>
              <option value="skedda">Skedda Calendar</option>
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>

      {renderContentFields()}

      <Row>
        <Col md={6}>
          <Form.Group className="mb-3">
            <Form.Label htmlFor="duration">
              {formData.content_type === 'video' && videoDurationDetected
                ? 'Video Duration (auto-detected)'
                : 'Duration Override (seconds)'}
            </Form.Label>
            <Form.Control
              id="duration"
              type="number"
              min="1"
              max="3600"
              value={formData.display_duration || ''}
              onChange={(e) => handleInputChange('display_duration', e.target.value ? parseInt(e.target.value) : null)}
              isInvalid={!!validationErrors.display_duration}
              placeholder="Use slideshow default"
              readOnly={formData.content_type === 'video' && videoDurationDetected}
              disabled={formData.content_type === 'video' && videoDurationDetected}
            />
            <Form.Control.Feedback type="invalid">
              {validationErrors.display_duration}
            </Form.Control.Feedback>
            <Form.Text className="text-muted">
              {formData.content_type === 'video' && videoDurationDetected
                ? 'Duration is automatically set from the uploaded video'
                : 'Leave empty to use the slideshow\'s default duration'}
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
          disabled={loading || uploadingFile || validatingVideoUrl}
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
