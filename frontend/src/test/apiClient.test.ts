import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../utils/apiClient';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('Authentication', () => {
    it('gets current user successfully', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_admin: true
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockUser
        })
      });

      const result = await apiClient.getCurrentUser();

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/auth/user', {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        signal: expect.any(AbortSignal)
      });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockUser);
    });

    it('handles authentication errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          success: false,
          error: 'Unauthorized'
        })
      });

      const result = await apiClient.getCurrentUser();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Unauthorized');
    });
  });

  describe('Slideshows', () => {
    it('fetches slideshows successfully', async () => {
      const mockSlideshows = [
        { id: 1, name: 'Test Slideshow 1', item_count: 5 },
        { id: 2, name: 'Test Slideshow 2', item_count: 3 },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockSlideshows
        })
      });

      const result = await apiClient.getSlideshows();

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/slideshows', {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        signal: expect.any(AbortSignal)
      });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockSlideshows);
    });

    it('creates slideshow successfully', async () => {
      const newSlideshow = { name: 'New Slideshow', description: 'Test description' };
      const createdSlideshow = { id: 1, ...newSlideshow, item_count: 0 };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: createdSlideshow
        })
      });

      const result = await apiClient.createSlideshow(newSlideshow);

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/slideshows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(newSlideshow),
        signal: expect.any(AbortSignal)
      });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(createdSlideshow);
    });
  });

  describe('Displays', () => {
    it('fetches displays successfully', async () => {
      const mockDisplays = [
        { id: 1, name: 'Display 1', is_online: true },
        { id: 2, name: 'Display 2', is_online: false },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockDisplays
        })
      });

      const result = await apiClient.getDisplays();

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/displays', {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        signal: expect.any(AbortSignal)
      });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockDisplays);
    });
  });

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await apiClient.getSlideshows();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });

    it('handles timeout errors', async () => {
      // Simulate timeout by making fetch return a response that hangs
      mockFetch.mockImplementationOnce(() => {
        return Promise.resolve({
          ok: false,
          status: 408,
          statusText: 'Request Timeout',
          json: () => Promise.resolve({ error: 'Request timeout' })
        } as Response);
      });

      const result = await apiClient.getSlideshows();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Request timeout');
    });
  });
});
