import type { 
  ApiResponse, 
  User, 
  Display, 
  Slideshow, 
  SlideshowItem,
  SlideshowFormData,
  SlideshowItemFormData
} from '../types';

class ApiClient {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL = '', timeout = 10000) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session-based auth
      ...options,
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
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
  }

  // Authentication methods
  async login(username: string, password: string): Promise<ApiResponse<User>> {
    return this.request<User>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.request<void>('/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>('/api/v1/auth/user');
  }

  // Slideshow methods
  async getSlideshows(): Promise<ApiResponse<Slideshow[]>> {
    return this.request<Slideshow[]>('/api/v1/slideshows');
  }

  async getSlideshow(id: number): Promise<ApiResponse<Slideshow>> {
    return this.request<Slideshow>(`/api/v1/slideshows/${id}`);
  }

  async createSlideshow(data: SlideshowFormData): Promise<ApiResponse<Slideshow>> {
    return this.request<Slideshow>('/api/v1/slideshows', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSlideshow(id: number, data: Partial<SlideshowFormData>): Promise<ApiResponse<Slideshow>> {
    return this.request<Slideshow>(`/api/v1/slideshows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteSlideshow(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/slideshows/${id}`, {
      method: 'DELETE',
    });
  }

  async setDefaultSlideshow(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/slideshows/${id}/set-default`, {
      method: 'POST',
    });
  }

  // Slideshow item methods
  async getSlideshowItems(slideshowId: number): Promise<ApiResponse<SlideshowItem[]>> {
    return this.request<SlideshowItem[]>(`/api/v1/slideshows/${slideshowId}/items`);
  }

  async createSlideshowItem(
    slideshowId: number, 
    data: SlideshowItemFormData
  ): Promise<ApiResponse<SlideshowItem>> {
    return this.request<SlideshowItem>(`/api/v1/slideshows/${slideshowId}/items`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSlideshowItem(
    id: number, 
    data: Partial<SlideshowItemFormData>
  ): Promise<ApiResponse<SlideshowItem>> {
    return this.request<SlideshowItem>(`/api/v1/slideshow-items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteSlideshowItem(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/slideshow-items/${id}`, {
      method: 'DELETE',
    });
  }

  async reorderSlideshowItem(id: number, newOrder: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/slideshow-items/${id}/reorder`, {
      method: 'POST',
      body: JSON.stringify({ order_index: newOrder }),
    });
  }

  // Display methods
  async getDisplays(): Promise<ApiResponse<Display[]>> {
    return this.request<Display[]>('/api/v1/displays');
  }

  async getDisplay(id: number): Promise<ApiResponse<Display>> {
    return this.request<Display>(`/api/v1/displays/${id}`);
  }

  async updateDisplay(id: number, data: Partial<Display>): Promise<ApiResponse<Display>> {
    return this.request<Display>(`/api/v1/displays/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteDisplay(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/displays/${id}`, {
      method: 'DELETE',
    });
  }

  async assignSlideshowToDisplay(
    displayName: string, 
    slideshowId: number
  ): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/v1/displays/${displayName}/assign-slideshow`, {
      method: 'POST',
      body: JSON.stringify({ slideshow_id: slideshowId }),
    });
  }

  // File upload methods
  async uploadImage(file: File, slideshowId?: number): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    if (slideshowId) {
      formData.append('slideshow_id', slideshowId.toString());
    }

    return this.request<any>('/api/v1/uploads/image', {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    });
  }

  async uploadVideo(file: File, slideshowId?: number): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    if (slideshowId) {
      formData.append('slideshow_id', slideshowId.toString());
    }

    return this.request<any>('/api/v1/uploads/video', {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    });
  }

  // Health check
  async getStatus(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/status');
  }
}

// Create singleton instance
export const apiClient = new ApiClient();
export default apiClient;
