// API 响应类型
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 推荐相关类型
export interface Recommendation {
  file_id: string;
  title: string;
  artist: string;
  album: string;
  mood: string;
  energy: string;
  genre: string;
  similarity: number;
  reason: string;
}

export interface RecommendRequest {
  user_id?: string;
  limit?: number;
  filter_recent?: boolean;
  diversity?: boolean;
}

export interface RecommendRequestGet {
  username: string;
  limit?: number;
}

// 查询相关类型
export interface Song {
  file_id: string;
  title: string;
  artist: string;
  album: string;
  mood: string;
  energy: string;
  scene: string;
  region: string;
  subculture: string;
  genre: string;
  confidence: number;
}

export interface QueryRequest {
  mood?: string;
  energy?: string;
  genre?: string;
  region?: string;
  limit?: number;
}

// 标签生成相关类型
export interface TaggingStatus {
  total: number;
  processed: number;
  pending: number;
  failed: number;
  progress: number;
  task_status?: 'idle' | 'processing' | 'completed' | 'failed';
}

export interface TaggingPreview {
  title: string;
  artist: string;
  tags: {
    mood: string;
    energy: string;
    scene: string;
    region: string;
    subculture: string;
    genre: string;
  };
}

// 分析相关类型
export interface AnalysisStats {
  total_songs: number;
  tagged_songs: number;
  untagged_songs: number;
  tag_coverage: number;
  mood_distribution: Record<string, number>;
  energy_distribution: Record<string, number>;
  genre_distribution: Record<string, number>;
  region_distribution: Record<string, number>;
}

export interface UserStats {
  username: string;
  total_plays: number;
  unique_songs: number;
  starred_count: number;
  playlist_count: number;
  top_artists: Array<{ artist: string; count: number }>;
  top_genres: Array<{ genre: string; count: number }>;
  top_moods: Array<{ mood: string; count: number }>;
}

// 配置相关类型
export interface RecommendConfig {
  default_limit: number;
  recent_filter_count: number;
  diversity_max_per_artist: number;
  diversity_max_per_album: number;
  exploration_ratio: number;
  tag_weights: {
    mood: number;
    energy: number;
    genre: number;
    region: number;
  };
}

export interface UserProfileConfig {
  play_count: number;
  starred: number;
  in_playlist: number;
  time_decay_days: number;
  min_decay: number;
}

export interface AlgorithmConfig {
  exploitation_pool_multiplier: number;
  exploration_pool_start: number;
  exploration_pool_end: number;
  randomness: number;
}

export interface AllowedLabels {
  mood: string[];
  energy: string[];
  scene: string[];
  region: string[];
  subculture: string[];
  genre: string[];
}

export interface ScenePresets {
  [key: string]: {
    mood: string[];
    energy: string[];
  };
}

export interface TaggingApiConfig {
  timeout: number;
  max_tokens: number;
  temperature: number;
  retry_delay: number;
  max_retries: number;
  retry_backoff: number;
}

export interface AllConfig {
  recommend: RecommendConfig;
  user_profile: UserProfileConfig;
  algorithm: AlgorithmConfig;
  allowed_labels: AllowedLabels;
  scene_presets: ScenePresets;
  api_config: TaggingApiConfig;
}
