import { useCallback } from 'react';
import { apiClient } from '../utils/apiClient';
import type { ApiResponse } from '../types';

export interface UseApiResult {
  apiCall: (endpoint: string, options?: RequestInit) => Promise<ApiResponse>;
}

export const useApi = (): UseApiResult => {
  const apiCall = useCallback(async (endpoint: string, options?: RequestInit): Promise<ApiResponse> => {
    // This is a generic wrapper around the apiClient request method
    // For now, we'll use the apiClient's private request method functionality
    // by routing through the appropriate specific methods
    
    try {
      const method = options?.method || 'GET';
      const url = endpoint;
      
      // Handle different endpoints by routing to appropriate apiClient methods
      if (url === '/api/v1/slideshows' && method === 'GET') {
        return await apiClient.getSlideshows();
      }
      
      if (url.startsWith('/api/v1/slideshows/') && url.endsWith('/items') && method === 'GET') {
        const slideshowId = parseInt(url.split('/')[3]);
        return await apiClient.getSlideshowItems(slideshowId);
      }
      
      if (url.startsWith('/api/v1/slideshows/') && !url.includes('/') && method === 'GET') {
        const slideshowId = parseInt(url.split('/')[3]);
        return await apiClient.getSlideshow(slideshowId);
      }
      
      if (url === '/api/v1/slideshows' && method === 'POST') {
        const data = JSON.parse(options?.body as string);
        return await apiClient.createSlideshow(data);
      }
      
      if (url.startsWith('/api/v1/slideshows/') && method === 'PUT') {
        const slideshowId = parseInt(url.split('/')[3]);
        const data = JSON.parse(options?.body as string);
        return await apiClient.updateSlideshow(slideshowId, data);
      }
      
      if (url.startsWith('/api/v1/slideshows/') && method === 'DELETE') {
        const slideshowId = parseInt(url.split('/')[3]);
        return await apiClient.deleteSlideshow(slideshowId);
      }
      
      if (url.endsWith('/set-default') && method === 'POST') {
        const slideshowId = parseInt(url.split('/')[3]);
        return await apiClient.setDefaultSlideshow(slideshowId);
      }
      
      if (url.startsWith('/api/v1/slideshows/') && url.includes('/items') && method === 'POST') {
        const slideshowId = parseInt(url.split('/')[3]);
        const data = JSON.parse(options?.body as string);
        return await apiClient.createSlideshowItem(slideshowId, data);
      }
      
      if (url.startsWith('/api/v1/slideshow-items/') && method === 'PUT') {
        const itemId = parseInt(url.split('/')[3]);
        const data = JSON.parse(options?.body as string);
        return await apiClient.updateSlideshowItem(itemId, data);
      }
      
      if (url.startsWith('/api/v1/slideshow-items/') && method === 'DELETE') {
        const itemId = parseInt(url.split('/')[3]);
        return await apiClient.deleteSlideshowItem(itemId);
      }
      
      if (url.endsWith('/reorder') && method === 'POST') {
        const itemId = parseInt(url.split('/')[3]);
        const data = JSON.parse(options?.body as string);
        return await apiClient.reorderSlideshowItem(itemId, data.new_order);
      }
      
      if (url.startsWith('/api/v1/uploads/')) {
        const uploadType = url.split('/')[3];
        if (uploadType === 'image') {
          const formData = options?.body as FormData;
          const file = formData.get('file') as File;
          const slideshowId = formData.get('slideshow_id') ? parseInt(formData.get('slideshow_id') as string) : undefined;
          return await apiClient.uploadImage(file, slideshowId);
        } else if (uploadType === 'video') {
          const formData = options?.body as FormData;
          const file = formData.get('file') as File;
          const slideshowId = formData.get('slideshow_id') ? parseInt(formData.get('slideshow_id') as string) : undefined;
          return await apiClient.uploadVideo(file, slideshowId);
        }
      }
      
      if (url === '/api/v1/auth/user' && method === 'GET') {
        return await apiClient.getCurrentUser();
      }
      
      if (url === '/api/v1/auth/login' && method === 'POST') {
        const data = JSON.parse(options?.body as string);
        return await apiClient.login(data.username, data.password);
      }
      
      if (url === '/api/v1/auth/logout' && method === 'POST') {
        return await apiClient.logout();
      }
      
      if (url === '/api/v1/displays' && method === 'GET') {
        return await apiClient.getDisplays();
      }
      
      // Fallback for unknown endpoints - make a direct request
      const baseURL = '';
      const fullUrl = `${baseURL}${endpoint}`;
      
      const config: RequestInit = {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        credentials: 'include',
        ...options,
      };

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(fullUrl, {
          ...config,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        const data = await response.json();

        if (!response.ok) {
          return {
            success: false,
            error: data.error || `HTTP ${response.status}: ${response.statusText}`,
          };
        }

        return data;
      } catch (error) {
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            return {
              success: false,
              error: 'Request timeout',
            };
          }
          return {
            success: false,
            error: error.message,
          };
        }
        return {
          success: false,
          error: 'Unknown error occurred',
        };
      }
      
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }, []);

  return { apiCall };
};
