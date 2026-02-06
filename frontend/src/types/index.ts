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
  year?: string;
  mood: string | string[];
  energy: string;
  genre: string | string[];
  style?: string | string[];
  scene?: string | string[];
  region: string;
  culture: string;
  language: string;
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
  mood: string | string[];
  energy: string;
  genre: string | string[];
  style?: string | string[];
  scene?: string | string[];
  region: string;
  culture: string;
  language: string;
  confidence: number;
}

export interface QueryRequest {
  mood?: string;
  energy?: string;
  genre?: string;
  style?: string;
  scene?: string;
  region?: string;
  culture?: string;
  language?: string;
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
    mood: string | string[];
    energy: string;
    genre: string | string[];
    style?: string | string[];
    scene?: string | string[];
    region: string;
    culture: string;
    language: string;
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
  style_distribution: Record<string, number>;
  scene_distribution: Record<string, number>;
  region_distribution: Record<string, number>;
  culture_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
}

export interface HealthData {
  health_score: number;
  health_level: 'excellent' | 'good' | 'warning' | 'error';
  total_songs: number;
  tagged_songs: number;
  tag_coverage: number;
  average_confidence: number;
  duplicate_count: number;
  issues: {
    duplicate_songs: number;
    duplicate_albums: number;
    duplicate_songs_in_album: number;
  };
}

export interface UserStats {
  username: string;
  total_plays: number;
  unique_songs: number;
  starred_count: number;
  playlist_count: number;
  top_artists: Array<{ artist: string; count: number }>;
  top_moods: Array<{ mood: string; count: number }>;
  top_energies: Array<{ energy: string; count: number }>;
  top_genres: Array<{ genre: string; count: number }>;
  top_styles: Array<{ style: string; count: number }>;
  top_scenes: Array<{ scene: string; count: number }>;
  top_regions: Array<{ region: string; count: number }>;
  top_cultures: Array<{ culture: string; count: number }>;
  top_languages: Array<{ language: string; count: number }>;
}

// 配置相关类型
export interface RecommendConfig {
  default_limit: number;
  recent_filter_count: number;
  diversity_max_per_artist: number;
  diversity_max_per_album: number;
  exploration_ratio: number;
  tag_weights: {
    genre: number;
    mood: number;
    energy: number;
    style: number;
    scene: number;
    culture: number;
    language: number;
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

export interface TaggingApiConfig {
  timeout: number;
  max_tokens: number;
  temperature: number;
  top_p?: number;
  retry_delay: number;
  max_retries: number;
  retry_backoff: number;
}

export interface AllConfig {
  recommend: RecommendConfig;
  user_profile: UserProfileConfig;
  algorithm: AlgorithmConfig;
  api_config: TaggingApiConfig;
}

// 验证相关类型
export interface ValidationStats {
  total: number;
  valid: number;
  invalid: number;
  valid_rate: number;
  invalid_by_dimension: Record<string, number>;
}

export interface InvalidSong {
  file_id: string;
  title: string;
  artist: string;
  album: string;
  tags: Record<string, string | string[]>;
  confidence: number;
  model: string;
  updated_at: string;
  invalid_tags: Record<string, string[]>;
}

export interface InvalidSongsResponse {
  total: number;
  limit: number;
  offset: number;
  data: InvalidSong[];
}

export interface RevalidateResponse {
  success: boolean;
  is_valid: boolean;
  validation_result: {
    is_valid: boolean;
    invalid_tags: Record<string, string[]>;
    all_valid: boolean;
  };
  tags: Record<string, string | string[]>;
}

// 日志相关类型
export interface LogFileInfo {
  name: string;
  path: string;
  size: number;
  lines: number;
}

export interface LogLine {
  line_number: number;
  timestamp: string | null;
  level: string | null;
  module: string | null;
  message: string;
}

export interface LogContentResponse {
  file: string;
  total_lines: number;
  lines: LogLine[];
  filtered: boolean;
}

// 重复检测相关类型
export interface DuplicateSong {
  id: string;
  path: string;
  title: string;
  artist: string;
  album: string;
}

export interface DuplicateSongGroup {
  size: number;
  count: number;
  songs: DuplicateSong[];
}

export interface DuplicateAlbum {
  id: string;
  name: string;
  album_artist: string;
  min_year: number;
  max_year: number;
  song_count: number;
  date: string;
}

export interface DuplicateAlbumGroup {
  album: string;
  album_artist: string;
  count: number;
  total_songs: number;
  albums: DuplicateAlbum[];
}

export interface DuplicateSongInAlbum {
  id: string;
  album_id: string;
  album: string;
  album_artist: string;
  title: string;
}

export interface DuplicateSongInAlbumGroup {
  path: string;
  count: number;
  songs: DuplicateSongInAlbum[];
}

export interface DuplicateSongsResponse {
  type: string;
  total_groups: number;
  duplicates: DuplicateSongGroup[];
}

export interface DuplicateAlbumsResponse {
  type: string;
  total_groups: number;
  duplicates: DuplicateAlbumGroup[];
}

export interface DuplicateSongsInAlbumResponse {
  type: string;
  total_groups: number;
  duplicates: DuplicateSongInAlbumGroup[];
}

export interface AllDuplicatesResponse {
  duplicate_songs: DuplicateSongsResponse;
  duplicate_albums: DuplicateAlbumsResponse;
  duplicate_songs_in_album: DuplicateSongsInAlbumResponse;
  summary: {
    duplicate_song_groups: number;
    duplicate_album_groups: number;
    duplicate_songs_in_album_groups: number;
    total_issues: number;
  };
}
