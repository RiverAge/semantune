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
    const message = error.response?.data?.error || error.message || '请求失败';
    return Promise.reject(new Error(message));
  }
);

// 推荐相关 API
export const recommendApi = {
  // 获取推荐列表
  getRecommendations: async (params: RecommendRequest) => {
    const response = await api.get<ApiResponse<Recommendation[]>>('/recommend/list', { params });
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

  // 预览标签生成
  previewTagging: async (limit: number = 5) => {
    const response = await api.get<ApiResponse<TaggingPreview[]>>('/tagging/preview', { params: { limit } });
    return response.data;
  },
};

// 分析相关 API
export const analyzeApi = {
  // 获取整体统计
  getStats: async () => {
    const response = await api.get<ApiResponse<AnalysisStats>>('/analyze/stats');
    return response.data;
  },

  // 获取用户统计
  getUserStats: async (username: string) => {
    const response = await api.get<ApiResponse<UserStats>>(`/analyze/user/${username}`);
    return response.data;
  },

  // 获取所有用户列表
  getUsers: async () => {
    const response = await api.get<ApiResponse<string[]>>('/analyze/users');
    return response.data;
  },
};

export default api;
