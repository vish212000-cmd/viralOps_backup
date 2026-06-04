export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  created_at: string;
}

export type RoleType = 'MEMBER' | 'ADMIN' | 'SUPER_ADMIN';

export interface Membership {
  id: number;
  user: User;
  organization: Organization;
  role: RoleType;
  joined_at: string;
}

export type ProjectStatus = 'ACTIVE' | 'COMPLETED' | 'ARCHIVED';

export interface Project {
  id: number;
  organization: number;
  name: string;
  description: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export type SourceType = 'VIDEO' | 'AUDIO' | 'YOUTUBE' | 'ARTICLE' | 'TRANSCRIPT' | 'SCRIPT' | 'PDF';
export type SourceStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface SourceInput {
  id: number;
  project: number;
  type: SourceType;
  title: string;
  source_url: string;
  file_name: string;
  file_size?: number | null;
  text_content: string;
  status: SourceStatus;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  speaker: string;
  text: string;
}

export interface TranscriptRecord {
  id: number;
  source_input: number;
  raw_text: string;
  normalized_text: string;
  segments: TranscriptSegment[];
  created_at: string;
}

export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface ProcessingJob {
  id: number;
  task_id: string | null;
  source_input: number;
  project: number;
  status: JobStatus;
  error_log: string;
  created_at: string;
  updated_at: string;
}

export type AssetType = 'HOOK' | 'TITLE' | 'CAPTION' | 'CTA' | 'HASHTAG' | 'THUMBNAIL' | 'SCRIPT' | 'PLATFORM_PACK';
export type PlatformType = 'SHORTS' | 'REELS' | 'TIKTOK' | 'MULTI';

export interface GeneratedAssetVersion {
  id: number;
  asset: number;
  content: string;
  edited_by: number | null;
  edited_by_username?: string;
  created_at: string;
}

export type PublishPlatformType = 'TWITTER' | 'YOUTUBE' | 'TIKTOK' | 'INSTAGRAM';
export type PublishStatusType = 'PENDING' | 'SUCCESS' | 'FAILED';

export interface SocialPublishRecord {
  id: number;
  asset: number;
  platform: PublishPlatformType;
  status: PublishStatusType;
  published_url: string;
  error_message: string;
  published_by: number | null;
  published_by_username?: string;
  created_at: string;
  updated_at: string;
}

export interface GeneratedAsset {
  id: number;
  project: number;
  type: AssetType;
  platform: PlatformType;
  content: string;
  metadata: Record<string, any>;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  versions?: GeneratedAssetVersion[];
  publish_records?: SocialPublishRecord[];
}

export type TemplateType = 'HOOK' | 'CTA' | 'SCRIPT';

export interface Template {
  id: number;
  organization: number;
  name: string;
  type: TemplateType;
  content: string;
  created_at: string;
}

export type MemoryKey = 'BRAND_TONE' | 'STYLE_GUIDE' | 'PREFERRED_HOOKS' | 'PAST_APPROVED_PATTERNS';

export interface MemoryRecord {
  id: number;
  organization: number;
  key: MemoryKey;
  value: Record<string, any>;
  updated_at: string;
}

export type UsageEventType = 'TRANSCRIPTION_MINUTES' | 'AI_GENERATION';

export interface UsageEvent {
  id: number;
  organization: number;
  user: number | null;
  username?: string;
  event_type: UsageEventType;
  quantity: number;
  created_at: string;
}

export interface AuditLog {
  id: number;
  organization: number | null;
  user: number | null;
  username?: string;
  action: string;
  details: Record<string, any>;
  ip_address: string | null;
  created_at: string;
}
