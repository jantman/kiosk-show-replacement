import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';
import Dashboard from '../pages/Dashboard';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

// Mock the API client
vi.mock('../utils/apiClient', () => ({
  default: {
    getSlideshows: vi.fn().mockResolvedValue({
      success: true,
      data: [
        { id: 1, name: 'Test Slideshow 1', item_count: 5 },
        { id: 2, name: 'Test Slideshow 2', item_count: 3 },
      ],
    }),
    getDisplays: vi.fn().mockResolvedValue({
      success: true,
      data: [
        { id: 1, name: 'Display 1', is_online: true },
        { id: 2, name: 'Display 2', is_online: false },
      ],
    }),
    getCurrentUser: vi.fn().mockResolvedValue({
      success: true,
      data: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_admin: true,
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
        last_login_at: '2023-01-01T00:00:00Z'
      },
    }),
  },
}));

// Mock the useAuth hook
vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual('../contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

const mockUseAuth = vi.mocked(useAuth);

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Dashboard', () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_admin: true,
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
        last_login_at: '2023-01-01T00:00:00Z'
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    });
  });

  it('renders dashboard header correctly', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    // Wait for loading to finish and dashboard content to appear
    await screen.findByRole('heading', { name: /dashboard/i });
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    expect(screen.getByText(/testuser/i)).toBeInTheDocument();
  });

  it('displays statistics cards', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    // Wait for data to load and check statistics - use more specific selectors
    await screen.findByRole('heading', { name: /dashboard/i });
    
    // Check statistics cards by looking for the specific card structure
    const statisticsSection = screen.getByText('Active Slideshows').closest('.card-body');
    expect(statisticsSection).toBeInTheDocument();
    expect(screen.getByText('Online Displays')).toBeInTheDocument();
    expect(screen.getByText('Assigned Displays')).toBeInTheDocument();
    expect(screen.getByText('Offline Displays')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });
});
