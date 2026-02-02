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
