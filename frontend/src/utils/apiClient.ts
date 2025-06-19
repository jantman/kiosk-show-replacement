import type { 
  ApiResponse, 
  User, 
  Display, 
  Slideshow, 
  SlideshowItem,
  SlideshowFormData,
  SlideshowItemFormData,
  AssignmentHistory
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
    return this.request<User>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.request<void>('/api/v1/auth/logout', {
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
      body: JSON.stringify({ new_order: newOrder }),
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

  // Assignment History methods
  async getAssignmentHistory(params?: {
    limit?: number;
    offset?: number;
    display_id?: number;
    action?: string;
    user_id?: number;
  }): Promise<ApiResponse<AssignmentHistory[]>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.display_id) searchParams.append('display_id', params.display_id.toString());
    if (params?.action) searchParams.append('action', params.action);
    if (params?.user_id) searchParams.append('user_id', params.user_id.toString());
    
    const query = searchParams.toString();
    const endpoint = query ? `/api/v1/assignment-history?${query}` : '/api/v1/assignment-history';
    
    return this.request<AssignmentHistory[]>(endpoint);
  }

  async getDisplayAssignmentHistory(displayId: number): Promise<ApiResponse<AssignmentHistory[]>> {
    return this.request<AssignmentHistory[]>(`/api/v1/displays/${displayId}/assignment-history`);
  }

  async createAssignmentHistory(data: {
    display_id: number;
    previous_slideshow_id?: number | null;
    new_slideshow_id?: number | null;
    action: 'assign' | 'unassign' | 'change';
    reason?: string;
  }): Promise<ApiResponse<AssignmentHistory>> {
    return this.request<AssignmentHistory>('/api/v1/assignment-history', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // File upload methods
  async uploadImage(file: File, slideshowId?: number): Promise<ApiResponse<{ file_path: string; url: string }>> {
    const formData = new FormData();
    formData.append('file', file);
    if (slideshowId) {
      formData.append('slideshow_id', slideshowId.toString());
    }

    return this.request<{ file_path: string; url: string }>('/api/v1/uploads/image', {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    });
  }

  async uploadVideo(file: File, slideshowId?: number): Promise<ApiResponse<{ file_path: string; url: string }>> {
    const formData = new FormData();
    formData.append('file', file);
    if (slideshowId) {
      formData.append('slideshow_id', slideshowId.toString());
    }

    return this.request<{ file_path: string; url: string }>('/api/v1/uploads/video', {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    });
  }

  // Health check
  async getStatus(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request<{ status: string; timestamp: string }>('/api/v1/status');
  }
}

// Create singleton instance
export const apiClient = new ApiClient();
export default apiClient;
