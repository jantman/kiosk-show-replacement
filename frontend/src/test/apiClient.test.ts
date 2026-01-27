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
      const newSlideshow = { 
        name: 'New Slideshow', 
        description: 'Test description',
        default_item_duration: 10
      };
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

  describe('Video URL Validation', () => {
    it('validates video URL successfully', async () => {
      const mockValidationResult = {
        valid: true,
        duration_seconds: 120,
        duration: 120.5,
        codec_info: {
          video_codec: 'h264',
          audio_codec: 'aac',
          container_format: 'mov,mp4,m4a,3gp,3g2,mj2'
        }
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          data: mockValidationResult
        })
      });

      const result = await apiClient.validateVideoUrl('https://example.com/video.mp4');

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/validate/video-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ url: 'https://example.com/video.mp4' }),
        signal: expect.any(AbortSignal)
      });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockValidationResult);
    });

    it('handles invalid video codec error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          success: false,
          error: "Video codec 'mpeg2video' is not supported by web browsers."
        })
      });

      const result = await apiClient.validateVideoUrl('https://example.com/video.mpeg');

      expect(result.success).toBe(false);
      expect(result.error).toContain('mpeg2video');
    });

    it('handles inaccessible URL error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          success: false,
          error: 'Could not retrieve video information from the URL.'
        })
      });

      const result = await apiClient.validateVideoUrl('https://example.com/nonexistent.mp4');

      expect(result.success).toBe(false);
      expect(result.error).toContain('Could not retrieve');
    });
  });

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      // Non-retryable network error (doesn't match retry patterns)
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await apiClient.getSlideshows();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });

    it('handles non-retryable HTTP errors', async () => {
      // 400 Bad Request is not retryable
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: () => Promise.resolve({ error: 'Invalid request data' })
      } as Response);

      const result = await apiClient.getSlideshows();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid request data');
      // Should only be called once (no retries for 400)
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('handles abort/timeout errors', async () => {
      // Simulate AbortError (what happens when request times out)
      // AbortError is retryable, so mock all retry attempts
      const abortError = new Error('The operation was aborted');
      abortError.name = 'AbortError';
      mockFetch.mockRejectedValue(abortError);

      const result = await apiClient.getSlideshows();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Request timeout');
      // Should be called 4 times (initial + 3 retries)
      expect(mockFetch).toHaveBeenCalledTimes(4);
    }, 20000); // Increase timeout for retry delays
  });
});
