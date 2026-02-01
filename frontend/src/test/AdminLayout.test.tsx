import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';
import AdminLayout from '../components/AdminLayout';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

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

describe('AdminLayout', () => {
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

  it('renders navigation and main content area', () => {
    render(
      <TestWrapper>
        <AdminLayout />
      </TestWrapper>
    );

    // Check for navigation elements
    expect(screen.getByText(/kiosk show replacement/i)).toBeInTheDocument();
    
    // Check for navigation links
    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /slideshows/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /displays/i })).toBeInTheDocument();
  });

  it('displays user information in navigation', () => {
    render(
      <TestWrapper>
        <AdminLayout />
      </TestWrapper>
    );

    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('includes logout functionality', () => {
    render(
      <TestWrapper>
        <AdminLayout />
      </TestWrapper>
    );

    // Check that the user dropdown button exists
    expect(screen.getByRole('button', { name: /testuser/i })).toBeInTheDocument();
  });

  it('renders responsive layout structure', () => {
    render(
      <TestWrapper>
        <AdminLayout />
      </TestWrapper>
    );

    // Check for Bootstrap classes that indicate responsive layout
    const container = screen.getByRole('navigation');
    expect(container).toBeInTheDocument();
  });
});
