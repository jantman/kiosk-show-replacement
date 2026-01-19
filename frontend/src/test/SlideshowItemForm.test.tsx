import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import SlideshowItemForm from '../components/SlideshowItemForm';

// Mock the useApi hook
const mockApiCall = vi.fn();
vi.mock('../hooks/useApi', () => ({
  useApi: () => ({
    apiCall: mockApiCall
  })
}));

const mockItem = {
  id: 1,
  slideshow_id: 1,
  title: 'Test Item',
  content_type: 'image' as const,
  content_url: undefined,
  content_file_path: 'images/test.jpg',
  content_text: undefined,
  display_url: '/uploads/images/test.jpg',
  display_duration: 10,
  order_index: 1,
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z'
};

describe('SlideshowItemForm', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create form correctly', () => {
    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Add Item')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter item title')).toBeInTheDocument();
    expect(screen.getByLabelText('Content Type')).toHaveValue('image'); // Content Type default
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('renders edit form correctly', () => {
    render(
      <SlideshowItemForm
        slideshowId={1}
        item={mockItem}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Update Item')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Item')).toBeInTheDocument();
    expect(screen.getByDisplayValue('10')).toBeInTheDocument();
    expect(screen.getByText('Update Item')).toBeInTheDocument();
  });

  it('handles content type change', () => {
    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const contentTypeSelect = screen.getByLabelText('Content Type');
    
    // Default should be image
    expect(contentTypeSelect).toHaveValue('image');
    expect(screen.getByLabelText(/Upload image/)).toBeInTheDocument();

    // Change to URL
    fireEvent.change(contentTypeSelect, { target: { value: 'url' } });
    expect(screen.getByLabelText('URL *')).toBeInTheDocument();

    // Change to text
    fireEvent.change(contentTypeSelect, { target: { value: 'text' } });
    expect(screen.getByLabelText('Text Content *')).toBeInTheDocument();

    // Change to video
    fireEvent.change(contentTypeSelect, { target: { value: 'video' } });
    expect(screen.getByLabelText(/Upload video/)).toBeInTheDocument();
  });

  it('handles form submission for create', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: true,
      data: { ...mockItem }
    });

    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Fill out the form
    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'New Item' }
    });
    fireEvent.change(screen.getByLabelText('Duration Override (seconds)'), {
      target: { value: '15' }
    });

    // For URL content type
    fireEvent.change(screen.getByLabelText('Content Type'), {
      target: { value: 'url' }
    });
    fireEvent.change(screen.getByLabelText('URL *'), {
      target: { value: 'https://example.com' }
    });

    // Submit the form
    fireEvent.click(screen.getByText('Add Item'));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/slideshows/1/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'New Item',
          content_type: 'url',
          content_url: 'https://example.com',
          content_text: null,
          content_file_path: null,
          display_duration: 15,
          is_active: true
        })
      });
    });

    expect(mockOnSave).toHaveBeenCalled();
  });

  it('handles form submission for edit', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: true,
      data: mockItem
    });

    render(
      <SlideshowItemForm
        slideshowId={1}
        item={mockItem}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Modify the title
    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'Updated Item' }
    });

    // Submit the form
    fireEvent.click(screen.getByText('Update Item'));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/slideshow-items/1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Updated Item',
          content_type: 'image',
          content_url: null,
          content_text: null,
          content_file_path: 'images/test.jpg',
          display_duration: 10,
          is_active: true
        })
      });
    });

    expect(mockOnSave).toHaveBeenCalled();
  });

  it('handles text content submission', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: true,
      data: { id: 1, content_type: 'text', text_content: 'Hello World' }
    });

    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Set up for text content
    fireEvent.change(screen.getByLabelText('Content Type'), {
      target: { value: 'text' }
    });
    fireEvent.change(screen.getByLabelText('Title *'), {
      target: { value: 'Text Item' }
    });
    fireEvent.change(screen.getByLabelText('Text Content *'), {
      target: { value: 'Hello World' }
    });

    fireEvent.click(screen.getByText('Add Item'));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/slideshows/1/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Text Item',
          content_type: 'text',
          content_url: '', // This will be empty string, not null, when content type is changed
          content_text: 'Hello World',
          content_file_path: null,
          display_duration: null,
          is_active: true
        })
      });
    });
  });

  it('handles file upload', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: true,
      data: { id: 1, file_path: 'images/uploaded.jpg' }
    });

    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const fileInput = screen.getByLabelText('Upload image *');
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/uploads/image', {
        method: 'POST',
        body: expect.any(FormData)
      });
    });
  });

  it('handles validation errors', async () => {
    mockApiCall.mockResolvedValueOnce({
      success: false,
      error: 'Title is required'
    });

    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Submit empty form
    fireEvent.click(screen.getByText('Add Item'));

    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument();
    });
  });

  it('handles cancel button', () => {
    render(
      <SlideshowItemForm
        slideshowId={1}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockOnCancel).toHaveBeenCalled();
  });
});
