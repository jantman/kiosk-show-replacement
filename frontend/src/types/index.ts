// API response types based on Flask backend
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// User types
export interface User {
  id: number;
  username: string;
  email?: string;
  is_admin: boolean;
  created_at: string;
  last_login_at?: string;
}

// Display types
export interface Display {
  id: number;
  name: string;
  location?: string;
  resolution_width?: number;
  resolution_height?: number;
  assigned_slideshow_id?: number;
  assigned_slideshow?: Slideshow;
  last_seen_at?: string;
  created_at: string;
  updated_at: string;
  online: boolean;
}

// Slideshow types
export interface Slideshow {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  is_default: boolean;
  default_item_duration: number;
  transition_type?: string;
  created_at: string;
  updated_at: string;
  total_duration?: number;
  item_count?: number;
  items?: SlideshowItem[];
}

// Slideshow item types
export interface SlideshowItem {
  id: number;
  slideshow_id: number;
  title?: string;
  content_type: 'image' | 'video' | 'url' | 'text';
  url?: string;
  file_path?: string;
  text_content?: string;
  display_url?: string;
  duration?: number;
  order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Authentication context types
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

// API client types
export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
}

// Form types
export interface LoginFormData {
  username: string;
  password: string;
}

export interface SlideshowFormData {
  name: string;
  description?: string;
  default_item_duration: number;
}

export interface SlideshowItemFormData {
  title: string;
  content_type: 'image' | 'video' | 'url' | 'text';
  content_source: string;
  duration?: number;
}
