import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import SlideshowForm from '../pages/SlideshowForm';
import AuthContext from '../contexts/AuthContext';

// Mock react-router-dom hooks
const mockNavigate = vi.fn();
const mockUseParams = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockUseParams()
  };
});

// Mock the useApi hook
const mockApiCall = vi.fn();
vi.mock('../hooks/useApi', () => ({
  useApi: () => ({
    apiCall: mockApiCall
  })
}));

const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  is_admin: true,
  created_at: '2023-01-01T00:00:00Z',
  last_login_at: '2023-01-01T00:00:00Z'
};

const mockAuthContext = {
  user: mockUser,
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  checkAuth: vi.fn()
};

const mockSlideshow = {
  id: 1,
  name: 'Test Slideshow',
  description: 'A test slideshow',
  is_active: true,
  is_default: false,
  default_item_duration: 10,
  transition_type: 'fade',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  total_duration: 60,
  item_count: 6,
  items: []
};

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthContext.Provider value={mockAuthContext}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </AuthContext.Provider>
);

describe('SlideshowForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('renders create form correctly', () => {
    mockUseParams.mockReturnValue({});

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    expect(screen.getByText('Create New Slideshow')).toBeInTheDocument();
    expect(screen.getByLabelText('Slideshow Name *')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Default Item Duration (seconds)')).toBeInTheDocument();
    expect(screen.getByLabelText('Transition Type')).toBeInTheDocument();
    expect(screen.getByText('Create Slideshow')).toBeInTheDocument();
  });

  it('renders edit form correctly', async () => {
    mockUseParams.mockReturnValue({ id: '1' });
    mockApiCall.mockResolvedValueOnce({
      success: true,
      data: mockSlideshow
    });

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Slideshow')).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('Test Slideshow')).toBeInTheDocument();
    expect(screen.getByDisplayValue('A test slideshow')).toBeInTheDocument();
    expect(screen.getByDisplayValue('10')).toBeInTheDocument();
    expect(screen.getByText('Update Slideshow')).toBeInTheDocument();
  });

  it('handles form submission for create', async () => {
    mockUseParams.mockReturnValue({});
    mockApiCall.mockResolvedValueOnce({
      success: true,
      data: { id: 1, ...mockSlideshow }
    });

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    // Fill out the form
    fireEvent.change(screen.getByLabelText('Slideshow Name *'), {
      target: { value: 'New Slideshow' }
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'New slideshow description' }
    });
    fireEvent.change(screen.getByLabelText('Default Item Duration (seconds)'), {
      target: { value: '15' }
    });

    // Submit the form
    fireEvent.click(screen.getByText('Create Slideshow'));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/slideshows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'New Slideshow',
          description: 'New slideshow description',
          default_item_duration: 15,
          transition_type: 'fade',
          is_active: true,
          is_default: false
        })
      });
    });

    expect(mockNavigate).toHaveBeenCalledWith('/admin/slideshows/1');
  });

  it('handles form submission for edit', async () => {
    mockUseParams.mockReturnValue({ id: '1' });
    mockApiCall
      .mockResolvedValueOnce({ success: true, data: mockSlideshow })
      .mockResolvedValueOnce({ success: true, data: mockSlideshow });

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Slideshow')).toBeInTheDocument();
    });

    // Modify the form
    fireEvent.change(screen.getByLabelText('Slideshow Name *'), {
      target: { value: 'Updated Slideshow' }
    });

    // Submit the form
    fireEvent.click(screen.getByText('Update Slideshow'));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith('/api/v1/slideshows/1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Updated Slideshow',
          description: 'A test slideshow',
          default_item_duration: 10,
          transition_type: 'fade',
          is_active: true,
          is_default: false
        })
      });
    });

    expect(mockNavigate).toHaveBeenCalledWith('/admin/slideshows/1');
  });

  it('handles validation errors', async () => {
    mockUseParams.mockReturnValue({});
    mockApiCall.mockResolvedValueOnce({
      success: false,
      error: 'Slideshow name is required'
    });

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    // Submit empty form
    fireEvent.click(screen.getByText('Create Slideshow'));

    await waitFor(() => {
      expect(screen.getByText('Slideshow name is required')).toBeInTheDocument();
    });
  });

  it('shows loading state when fetching slideshow for edit', () => {
    mockUseParams.mockReturnValue({ id: '1' });
    mockApiCall.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    expect(screen.getByText('Loading slideshow...')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('handles cancel button', () => {
    mockUseParams.mockReturnValue({});

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockNavigate).toHaveBeenCalledWith('/admin/slideshows');
  });

  it('validates required fields', async () => {
    mockUseParams.mockReturnValue({});

    render(
      <TestWrapper>
        <SlideshowForm />
      </TestWrapper>
    );

    // Try to submit without required fields
    fireEvent.click(screen.getByText('Create Slideshow'));

    // Form should not submit if name is empty
    expect(mockApiCall).not.toHaveBeenCalled();
  });
});
