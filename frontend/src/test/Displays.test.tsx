import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import Displays from '../pages/Displays';

// Mock the useApi hook
const mockApiCall = vi.fn();
vi.mock('../hooks/useApi', () => ({
  useApi: () => ({
    apiCall: mockApiCall
  })
}));

// Mock data
const mockDisplays = [
  {
    id: 1,
    name: 'lobby-display',
    location: 'Main Lobby',
    resolution_width: 1920,
    resolution_height: 1080,
    current_slideshow_id: 1,
    last_seen_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    is_online: true,
    is_default: false
  },
  {
    id: 2,
    name: 'conference-room-a',
    location: 'Conference Room A',
    resolution_width: 1920,
    resolution_height: 1080,
    current_slideshow_id: null,
    last_seen_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    is_online: false,
    is_default: false
  }
];

const mockSlideshows = [
  {
    id: 1,
    name: 'Welcome Slideshow',
    description: 'Main welcome slideshow',
    is_active: true,
    is_default: true,
    default_item_duration: 5,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: 'Announcements',
    description: 'Company announcements',
    is_active: true,
    is_default: false,
    default_item_duration: 8,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  }
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Displays', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders displays list correctly', async () => {
    mockApiCall
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    // Check loading state
    expect(screen.getByText('Loading displays...')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Display Management')).toBeInTheDocument();
    });

    // Check displays are rendered
    expect(screen.getByText('lobby-display')).toBeInTheDocument();
    expect(screen.getByText('conference-room-a')).toBeInTheDocument();
    expect(screen.getByText('Main Lobby')).toBeInTheDocument();
    expect(screen.getByText('Conference Room A')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Offline')).toBeInTheDocument();

    // Check resolution display
    expect(screen.getAllByText('1920 × 1080')).toHaveLength(2);

    // Check slideshow assignment
    expect(screen.getByText('Welcome Slideshow')).toBeInTheDocument();
    expect(screen.getByText('None assigned')).toBeInTheDocument();
  });

  it('shows empty state when no displays exist', async () => {
    mockApiCall
      .mockResolvedValueOnce({ success: true, data: [] })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('No Displays Found')).toBeInTheDocument();
    });

    expect(screen.getByText('Displays will appear here automatically when they connect to the system.')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    mockApiCall
      .mockRejectedValueOnce(new Error('Failed to load displays'))
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load displays')).toBeInTheDocument();
    });
  });

  it('opens slideshow assignment modal', async () => {
    mockApiCall
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('lobby-display')).toBeInTheDocument();
    });

    // Click the assign slideshow button for the first display
    const assignButtons = screen.getAllByTitle('Assign Slideshow');
    fireEvent.click(assignButtons[0]);

    // Check modal is open
    await waitFor(() => {
      expect(screen.getByText('Assign Slideshow to lobby-display')).toBeInTheDocument();
    });

    // Check slideshow options are available
    expect(screen.getByText('Welcome Slideshow (Default)')).toBeInTheDocument();
    expect(screen.getByText('Announcements')).toBeInTheDocument();
  });

  it('assigns slideshow to display', async () => {
    mockApiCall
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows })
      .mockResolvedValueOnce({ success: true, data: { ...mockDisplays[1], current_slideshow_id: 2 } })
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('conference-room-a')).toBeInTheDocument();
    });

    // Open assignment modal for second display (no slideshow assigned)
    const assignButtons = screen.getAllByTitle('Assign Slideshow');
    fireEvent.click(assignButtons[1]);

    await waitFor(() => {
      expect(screen.getByText('Assign Slideshow to conference-room-a')).toBeInTheDocument();
    });

    // Select a slideshow
    const select = screen.getByLabelText('Slideshow');
    fireEvent.change(select, { target: { value: '2' } });

    // Submit assignment
    const assignButton = screen.getByText('Assign Slideshow');
    fireEvent.click(assignButton);

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/displays/conference-room-a/assign-slideshow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slideshow_id: 2 })
      });
    });
  });

  it('deletes display with confirmation', async () => {
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);

    mockApiCall
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows })
      .mockResolvedValueOnce({ success: true, data: null })
      .mockResolvedValueOnce({ success: true, data: [mockDisplays[0]] })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('lobby-display')).toBeInTheDocument();
    });

    // Click delete button for first display
    const deleteButtons = screen.getAllByTitle('Delete Display');
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/displays/1', {
        method: 'DELETE'
      });
    });

    // Restore window.confirm
    window.confirm = originalConfirm;
  });

  it('formats last seen timestamps correctly', async () => {
    const now = new Date();
    const recentDisplay = {
      ...mockDisplays[0],
      last_seen_at: new Date(now.getTime() - 30 * 1000).toISOString() // 30 seconds ago
    };
    const oldDisplay = {
      ...mockDisplays[1],
      last_seen_at: new Date(now.getTime() - 25 * 60 * 60 * 1000).toISOString() // 25 hours ago
    };

    mockApiCall
      .mockResolvedValueOnce({ success: true, data: [recentDisplay, oldDisplay] })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('Just now')).toBeInTheDocument();
    });

    // Check that old timestamp shows as date
    const datePattern = /\d{1,2}\/\d{1,2}\/\d{4}/;
    expect(screen.getByText(datePattern)).toBeInTheDocument();
  });

  it('refreshes data when refresh button is clicked', async () => {
    mockApiCall
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows })
      .mockResolvedValueOnce({ success: true, data: mockDisplays })
      .mockResolvedValueOnce({ success: true, data: mockSlideshows });

    renderWithRouter(<Displays />);

    await waitFor(() => {
      expect(screen.getByText('lobby-display')).toBeInTheDocument();
    });

    // Click refresh button
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledTimes(4);
    });
  });
});
