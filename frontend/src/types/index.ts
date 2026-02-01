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
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

// User with temporary password (returned from create/reset)
export interface UserWithPassword extends User {
  temporary_password: string;
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
  content_type: 'image' | 'video' | 'url' | 'text' | 'skedda';
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
  // Skedda/iCal calendar fields
  ical_feed_id?: number | null;
  ical_refresh_minutes?: number | null;
  ical_url?: string; // URL from linked feed, for display/editing
  created_at: string;
  updated_at: string;
}

// Skedda calendar data types (from /api/v1/slideshow-items/<id>/skedda-data)
export interface SkeddaTimeSlot {
  time: string; // "07:00", "07:30", etc.
  display: string; // "7:00 AM", "7:30 AM", etc.
}

export interface SkeddaEvent {
  id: number;
  uid: string;
  space: string;
  person_name: string;
  description: string;
  start_time: string; // "12:00"
  end_time: string; // "14:00"
  start_slot: number;
  row_span: number;
}

export interface SkeddaCalendarData {
  date: string; // "2026-01-28"
  date_display: string; // "Wednesday, January 28, 2026"
  spaces: string[];
  time_slots: SkeddaTimeSlot[];
  events: SkeddaEvent[];
  last_updated: string | null;
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
  content_type: 'image' | 'video' | 'url' | 'text' | 'skedda';
  content_source: string;
  duration?: number;
  // Skedda-specific fields
  ical_url?: string;
  ical_refresh_minutes?: number;
}

// Profile form types
export interface ProfileUpdateData {
  email?: string;
}

export interface PasswordChangeData {
  current_password: string;
  new_password: string;
}

// Video URL validation response
export interface VideoUrlValidationResult {
  valid: boolean;
  duration_seconds: number | null;
  duration: number | null;
  codec_info: {
    video_codec: string | null;
    audio_codec: string | null;
    container_format: string | null;
  } | null;
}
