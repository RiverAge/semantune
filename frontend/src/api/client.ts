import axios from 'axios';
import type {
  ApiResponse,
  Recommendation,
  RecommendRequest,
  Song,
  QueryRequest,
  TaggingStatus,
  TaggingPreview,
  AnalysisStats,
  UserStats,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 后端返回的错误格式: { success: false, error: { message: string, type: string, details: object } }
    const errorData = error.response?.data?.error;
    const message = errorData?.message || error.message || '请求失败';
    return Promise.reject(new Error(message));
  }
);

// 推荐相关 API
export const recommendApi = {
  // 获取推荐列表（POST 方法，使用 user_id）
  getRecommendations: async (params: RecommendRequest) => {
    const response = await api.post<ApiResponse<{ user_id: string; recommendations: Recommendation[]; stats: any }>>('/recommend', params);
    return response.data;
  },

  // 获取推荐列表（GET 方法，使用 username）
  getRecommendationsByUsername: async (username: string, limit: number = 30) => {
    const response = await api.get<ApiResponse<Recommendation[]>>('/recommend/list', { params: { username, limit } });
    return response.data;
  },

  // 获取用户画像
  getUserProfile: async (username: string) => {
    const response = await api.get<ApiResponse<UserStats>>(`/recommend/profile/${username}`);
    return response.data;
  },
};

// 查询相关 API
export const queryApi = {
  // 查询歌曲
  querySongs: async (params: QueryRequest) => {
    const response = await api.get<ApiResponse<Song[]>>('/query', { params });
    return response.data;
  },

  // 获取所有标签选项
  getTagOptions: async () => {
    const response = await api.get<ApiResponse<{
      moods: string[];
      energies: string[];
      genres: string[];
      regions: string[];
    }>>('/query/options');
    return response.data;
  },
};

// 标签生成相关 API
export const taggingApi = {
  // 获取标签生成状态
  getStatus: async () => {
    const response = await api.get<ApiResponse<TaggingStatus>>('/tagging/status');
    return response.data;
  },

  // 开始标签生成
  startTagging: async () => {
    const response = await api.post<ApiResponse<{ message: string }>>('/tagging/start');
    return response.data;
  },

  // 中止标签生成
  stopTagging: async () => {
    const response = await api.post<ApiResponse<{ message: string }>>('/tagging/stop');
    return response.data;
  },

  // 测试单首歌曲标签生成
  testTag: async (title: string, artist: string, album: string) => {
    const response = await api.post<ApiResponse<{
      title: string;
      artist: string;
      album: string;
      tags: any;
      raw_response: string;
    }>>('/tagging/generate', { title, artist, album });
    return response.data;
  },

  // 获取标签生成历史记录
  getHistory: async (limit: number = 20, offset: number = 0) => {
    const response = await api.get<ApiResponse<{
      items: any[];
      total: number;
      limit: number;
      offset: number;
    }>>('/tagging/history', { params: { limit, offset } });
    return response.data;
  },

  // SSE 流式获取进度
  streamProgress: (onProgress: (data: any) => void, onComplete: () => void, onError: (error: Error) => void) => {
    const eventSource = new EventSource('/api/v1/tagging/stream');
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        onComplete();
        return;
      }
      
      try {
        const data = JSON.parse(event.data);
        onProgress(data);
      } catch (e) {
        console.error('解析 SSE 数据失败:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      eventSource.close();
      onError(new Error('SSE 连接失败'));
    };
    
    return eventSource;
  },
};

// 分析相关 API
export const analyzeApi = {
  // 获取整体统计
  getStats: async () => {
    const response = await api.get<ApiResponse<AnalysisStats>>('/analyze/overview');
    return response.data;
  },

  // 获取用户统计
  getUserStats: async (username: string) => {
    const response = await api.get<ApiResponse<UserStats>>(`/recommend/profile/${username}`);
    return response.data;
  },

  // 获取所有用户列表
  getUsers: async () => {
    const response = await api.get<ApiResponse<{ users: string[] }>>('/recommend/users');
    return response.data;
  },
};

export default api;
