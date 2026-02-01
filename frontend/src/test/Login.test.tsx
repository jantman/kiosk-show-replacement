import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';
import Login from '../pages/Login';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

// Mock the useAuth hook
vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual('../contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

// Mock apiClient - the Login component uses it directly for health checks and login
// Also mock getCurrentUser since AuthProvider uses it
vi.mock('../utils/apiClient', () => ({
  default: {
    getHealthReady: vi.fn(),
    login: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

import apiClient from '../utils/apiClient';

const mockUseAuth = vi.mocked(useAuth);
const mockApiClient = vi.mocked(apiClient);

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Login', () => {
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockClear();

    // Default: system is ready (health check passes)
    mockApiClient.getHealthReady.mockResolvedValue({
      success: true,
      data: { status: 'ready' },
    });

    // Default: login succeeds
    mockApiClient.login.mockResolvedValue({
      success: true,
      data: { id: 1, username: 'testuser', is_admin: true, is_active: true, created_at: '2024-01-01T00:00:00Z' },
    });

    // Default: getCurrentUser fails (not authenticated yet)
    mockApiClient.getCurrentUser.mockResolvedValue({
      success: false,
      error: 'Not authenticated',
    });

    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: mockLogin,
      logout: vi.fn(),
      checkAuth: vi.fn(),
    });
  });

  it('renders login form correctly', async () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    // Wait for health check to complete and form to render
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /kiosk show replacement/i })).toBeInTheDocument();
    });

    expect(screen.getByPlaceholderText(/enter your username/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter your password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('handles form submission with valid data', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    // Wait for health check to complete
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/enter your username/i)).toBeInTheDocument();
    });

    const usernameInput = screen.getByPlaceholderText(/enter your username/i);
    const passwordInput = screen.getByPlaceholderText(/enter your password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  it('displays validation errors for empty fields', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    // Wait for health check to complete
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    // Should show validation error message
    await screen.findByText(/please enter both username and password/i);
    expect(screen.getByText(/please enter both username and password/i)).toBeInTheDocument();
  });

  it('shows loading state while checking system status', async () => {
    // Make health check hang indefinitely
    mockApiClient.getHealthReady.mockImplementation(() => new Promise(() => {}));

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    // Should show system check loading state
    expect(screen.getByText(/checking system status/i)).toBeInTheDocument();
  });

  it('shows loading state during authentication', async () => {
    // Health check resolves immediately
    mockApiClient.getHealthReady.mockResolvedValue({
      success: true,
      data: { status: 'ready' },
    });

    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: mockLogin,
      logout: vi.fn(),
      checkAuth: vi.fn(),
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    // Wait for health check to complete, then auth loading state should show
    await waitFor(() => {
      expect(screen.getByText(/checking authentication/i)).toBeInTheDocument();
    });
  });
});
