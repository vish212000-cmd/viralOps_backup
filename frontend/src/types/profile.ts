export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  username: string;
}

export interface Profile {
  avatar: string | null;
  banner: string | null;
  display_name: string;
  phone: string;
  country: string;
  state: string;
  city: string;
  timezone: string;
  language: string;
  job_title: string;
  company: string;
  website: string;
  bio: string;
}

export interface SocialLinks {
  linkedin: string;
  twitter: string;
  youtube: string;
  instagram: string;
  tiktok: string;
}

export interface CreatorProfile {
  niche: string;
  audience_size: string;
  primary_platform: string;
  content_frequency: string;
  preferred_tone: string;
  preferred_language: string;
  brand_voice: string;
  default_cta: string;
  target_audience: string;
}

export interface UserPreferences {
  default_ai_provider: string;
  preferred_model: string;
  temperature: number;
  creativity_level: string;
  default_output_language: string;
  caption_style: string;
  hook_style: string;
  title_style: string;
  emoji_preference: string;
  hashtag_preference: string;
  default_output_formats: string[];
}

export interface BrandDefaults {
  brand_colors: string[];
  logo: string | null;
  watermark: string | null;
  fonts: string[];
  brand_voice: string;
  default_intro: string;
  default_outro: string;
  default_cta: string;
}

export interface NotificationSettings {
  email_notifications: boolean;
  desktop_notifications: boolean;
  processing_complete: boolean;
  asset_ready: boolean;
  billing: boolean;
  product_updates: boolean;
  security_alerts: boolean;
  weekly_reports: boolean;
  marketing_emails: boolean;
  sms_notifications: boolean;
  push_notifications: boolean;
}

export interface SecuritySettings {
  phone_verified: boolean;
  recovery_codes: string[];
  last_password_change: string;
  failed_login_attempts: number;
  trusted_devices: string[];
}

export interface FullAccount {
  user: User;
  profile: Profile;
  social_links?: SocialLinks;
  creator_profile?: CreatorProfile;
  preferences?: UserPreferences;
  brand_defaults?: BrandDefaults;
  notification_settings?: NotificationSettings;
  security_settings?: SecuritySettings;
}

export interface APIToken {
  id: number;
  name: string;
  prefix: string;
  scopes: string[];
  last_used: string | null;
  expires_at: string | null;
  created_at: string;
  raw_token?: string; // Only present upon creation
}

export interface SessionHistory {
  id: number;
  device: string;
  browser: string;
  os: string;
  location: string;
  ip_address: string;
  is_active: boolean;
  created_at: string;
  last_activity: string;
}

export interface ConnectedAccount {
  id: number;
  provider: string;
  last_sync: string;
  created_at: string;
}
