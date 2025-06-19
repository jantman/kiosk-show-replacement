import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DisplayDetail from '../pages/DisplayDetail';
import { apiClient } from '../utils/apiClient';

// Mock the apiClient
vi.mock('../utils/apiClient', () => ({
  apiClient: {
    getDisplay: vi.fn(),
    getSlideshows: vi.fn(),
    updateDisplay: vi.fn(),
    deleteDisplay: vi.fn(),
    getDisplayAssignmentHistory: vi.fn(),
  }
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: '123' }),
    useNavigate: () => mockNavigate,
  };
});

const mockDisplay = {
  id: 123,
  name: 'Test Display',
  location: 'Main Lobby',
  description: 'Primary display in main lobby',
  resolution: '1920x1080',
  resolution_width: 1920,
  resolution_height: 1080,
  current_slideshow_id: 456,
  is_online: true,
  last_seen_at: new Date().toISOString(),
  heartbeat_interval: 30,
  rotation: 0,
  is_default: false,
  created_at: '2025-06-01T12:00:00Z',
  updated_at: '2025-06-17T12:00:00Z',
};

const mockSlideshows = [
  { 
    id: 456, 
    name: 'Main Slideshow', 
    description: 'Primary slideshow',
    is_active: true,
    is_default: false,
    default_item_duration: 10,
    created_at: '2025-06-01T12:00:00Z',
    updated_at: '2025-06-17T12:00:00Z',
  },
  { 
    id: 789, 
    name: 'Secondary Slideshow', 
    description: 'Backup slideshow',
    is_active: true,
    is_default: false,
    default_item_duration: 8,
    created_at: '2025-06-01T12:00:00Z',
    updated_at: '2025-06-17T12:00:00Z',
  },
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('DisplayDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('renders display details correctly', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });
    vi.mocked(apiClient.getDisplayAssignmentHistory).mockResolvedValue({ 
      success: true, 
      data: [] 
    });

    renderWithRouter(<DisplayDetail />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Check display information
    expect(screen.getByText('Display Details')).toBeInTheDocument();
    expect(screen.getAllByText('Test Display')[1]).toBeInTheDocument(); // Get the one in the table, not breadcrumb
    expect(screen.getByText('Main Lobby')).toBeInTheDocument();
    expect(screen.getByText('Primary display in main lobby')).toBeInTheDocument();
    expect(screen.getByText('1920x1080')).toBeInTheDocument();
    
    // Check status
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Just now')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    vi.mocked(apiClient.getDisplay).mockImplementation(() => new Promise(() => {}));
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    vi.mocked(apiClient.getDisplay).mockRejectedValue(new Error('API Error'));
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch display details/)).toBeInTheDocument();
    });
  });

  it('enters edit mode when edit button is clicked', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Click edit button
    fireEvent.click(screen.getByText('Edit Display'));

    // Check edit form elements appear
    expect(screen.getByDisplayValue('Test Display')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Main Lobby')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Primary display in main lobby')).toBeInTheDocument();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('saves display changes successfully', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });
    vi.mocked(apiClient.updateDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Display'));

    // Change display name
    const nameInput = screen.getByDisplayValue('Test Display');
    fireEvent.change(nameInput, { target: { value: 'Updated Display' } });

    // Save changes
    fireEvent.click(screen.getByText('Save Changes'));

    await waitFor(() => {
      expect(apiClient.updateDisplay).toHaveBeenCalledWith(123, {
        name: 'Updated Display',
        location: 'Main Lobby',
        description: 'Primary display in main lobby',
        current_slideshow_id: 456,
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Display updated successfully')).toBeInTheDocument();
    });
  });

  it('handles update errors gracefully', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });
    vi.mocked(apiClient.updateDisplay).mockRejectedValue(new Error('Update failed'));

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Enter edit mode and save
    fireEvent.click(screen.getByText('Edit Display'));
    fireEvent.click(screen.getByText('Save Changes'));

    await waitFor(() => {
      expect(screen.getByText(/Failed to update display/)).toBeInTheDocument();
    });
  });

  it('cancels edit mode correctly', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit Display'));

    // Change name
    const nameInput = screen.getByDisplayValue('Test Display');
    fireEvent.change(nameInput, { target: { value: 'Changed Name' } });

    // Cancel
    fireEvent.click(screen.getByText('Cancel'));

    // Should be back to view mode
    expect(screen.getByText('Edit Display')).toBeInTheDocument();
    expect(screen.queryByText('Save Changes')).not.toBeInTheDocument();
  });

  it('opens delete confirmation modal', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Click delete button
    fireEvent.click(screen.getByText('Delete Display'));

    // Check modal appears
    expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
    expect(screen.getByText('"Test Display"')).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
  });

  it('deletes display successfully', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });
    vi.mocked(apiClient.deleteDisplay).mockResolvedValue({ 
      success: true 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Open delete modal and confirm
    const initialDeleteButton = screen.getByRole('button', { name: /Delete Display/i });
    fireEvent.click(initialDeleteButton);
    
    // Wait for modal to appear and find the confirmation button
    await waitFor(() => {
      expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument();
    });
    
    // Find all delete buttons and get the one in the modal (should be the danger button)
    const deleteButtons = screen.getAllByText('Delete Display');
    const modalDeleteButton = deleteButtons.find(button => 
      button.classList.contains('btn-danger')
    );
    fireEvent.click(modalDeleteButton!);

    await waitFor(() => {
      expect(apiClient.deleteDisplay).toHaveBeenCalledWith(123);
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin/displays', {
        state: { message: 'Display "Test Display" deleted successfully' }
      });
    });
  });

  it('formats last seen time correctly', async () => {
    const pastDate = new Date();
    pastDate.setHours(pastDate.getHours() - 2); // 2 hours ago
    
    const displayWithPastDate = {
      ...mockDisplay,
      last_seen_at: pastDate.toISOString(),
    };

    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: displayWithPastDate 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    expect(screen.getByText('2h ago')).toBeInTheDocument();
  });

  it('shows slideshow assignment correctly', async () => {
    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: mockDisplay 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    // Should show link to assigned slideshow
    const slideshowLink = screen.getByText('Main Slideshow');
    expect(slideshowLink).toBeInTheDocument();
    expect(slideshowLink.closest('a')).toHaveAttribute('href', '/admin/slideshows/456');
  });

  it('handles display without slideshow assignment', async () => {
    const displayNoSlideshow = {
      ...mockDisplay,
      current_slideshow_id: null,
    };

    vi.mocked(apiClient.getDisplay).mockResolvedValue({ 
      success: true, 
      data: displayNoSlideshow 
    });
    vi.mocked(apiClient.getSlideshows).mockResolvedValue({ 
      success: true, 
      data: mockSlideshows 
    });

    renderWithRouter(<DisplayDetail />);

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    expect(screen.getByText('None')).toBeInTheDocument();
  });
});
