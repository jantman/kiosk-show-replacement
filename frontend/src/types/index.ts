// API response types based on Flask backend
export interface ApiResponse<T = unknown> {
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
  description?: string;
  resolution?: string;
  resolution_width?: number;
  resolution_height?: number;
  current_slideshow_id?: number | null;
  assigned_slideshow?: Slideshow;
  last_seen_at?: string;
  created_at: string;
  updated_at: string;
  is_online: boolean;
  heartbeat_interval?: number;
  rotation?: number;
  is_default?: boolean;
  show_info_overlay?: boolean;
}

// Assignment History types
export interface AssignmentHistory {
  id: number;
  display_id: number;
  display?: Display;
  previous_slideshow_id?: number | null;
  previous_slideshow?: Slideshow | null;
  new_slideshow_id?: number | null;
  new_slideshow?: Slideshow | null;
  action: 'assign' | 'unassign' | 'change';
  reason?: string;
  user_id?: number | null;
  user?: User | null;
  created_at: string;
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
// Field names match backend/database schema for consistency
export interface SlideshowItem {
  id: number;
  slideshow_id: number;
  title?: string;
  content_type: 'image' | 'video' | 'url' | 'text';
  content_url?: string;
  content_file_path?: string;
  content_text?: string;
  content_source?: string;
  display_url?: string;
  display_duration?: number;
  effective_duration?: number;
  order_index: number;
  is_active: boolean;
  // URL slide scaling: zoom percentage (10-100). NULL or 100 = no scaling.
  // Lower values zoom out to show more content.
  scale_factor?: number | null;
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
