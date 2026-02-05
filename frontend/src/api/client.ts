import axios from 'axios';
import type {
  ApiResponse,
  Recommendation,
  RecommendRequest,
  Song,
  QueryRequest,
  TaggingStatus,
  AnalysisStats,
  UserStats,
  RecommendConfig,
  UserProfileConfig,
  AlgorithmConfig,
  TaggingApiConfig,
  AllConfig,
  LogFileInfo,
  LogContentResponse,
  AllDuplicatesResponse,
  DuplicateSongsResponse,
  DuplicateAlbumsResponse,
  DuplicateSongsInAlbumResponse,
  HealthData,
} from '../types';

/**
 * 类型辅助函数：确保响应是 ApiResponse<T>
 * 由于 axios 响应拦截器的类型限制，我们需要这个函数来提供类型安全
 */
export function asApiResponse<T>(response: unknown): ApiResponse<T> {
  return response as ApiResponse<T>;
}

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

// 响应拦截器 - 拦截器返回的是 AxiosResponse，但我们返回其中的 data
api.interceptors.response.use(
  (response: any) => {
    // response.data 是后端返回的 ApiResponse<T>
    return response.data;
  },
  (error) => {
    // 后端返回的错误格式: { success: false, error: { message: string, type: string, details: object } }
    const errorData = error.response?.data?.error;
    const message = errorData?.message || error.message || '请求失败';
    const errorType = errorData?.type;
    const details = errorData?.details;

    // 创建包含完整错误信息的 Error 对象
    const enhancedError = new Error(message) as any;
    enhancedError.type = errorType;
    enhancedError.details = details;
    enhancedError.status = error.response?.status;

    return Promise.reject(enhancedError);
  }
);

// 推荐相关 API
export const recommendApi = {
  // 获取推荐列表（POST 方法，使用 user_id）
  getRecommendations: async (params: RecommendRequest): Promise<ApiResponse<{ user_id: string; recommendations: Recommendation[]; stats: any }>> => {
    return await api.post<ApiResponse<{ user_id: string; recommendations: Recommendation[]; stats: any }>>('/recommend', params) as any;
  },

  // 获取推荐列表（GET 方法，使用 username）
  getRecommendationsByUsername: async (username: string, limit: number = 30): Promise<ApiResponse<Recommendation[]>> => {
    return await api.get<ApiResponse<Recommendation[]>>('/recommend/list', { params: { username, limit } }) as any;
  },

  // 获取用户画像
  getUserProfile: async (username: string): Promise<ApiResponse<UserStats>> => {
    return await api.get<ApiResponse<UserStats>>(`/recommend/profile/${username}`) as any;
  },

  // 导出推荐报告（包含推荐歌曲和用户画像）
  exportReport: async (username: string, limit: number = 30): Promise<void> => {
    // 使用原始 axios 而不是 api 实例，以获取完整的 response 对象（包括 headers）
    const axios = (await import('axios')).default;
    const response = await axios.get('/api/v1/recommend/export', {
      params: { username, limit },
      responseType: 'blob'
    });
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/markdown;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // 从响应头获取文件名
    const contentDisposition = response.headers?.['content-disposition'];
    let filename = `recommendation_report_${username}.md`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

// 查询相关 API
export const queryApi = {
  // 查询歌曲
  querySongs: async (params: QueryRequest) => {
    return await api.get<ApiResponse<Song[]>>('/query', { params });
  },

  // 获取所有标签选项
  getTagOptions: async () => {
    return await api.get<ApiResponse<{
      moods: string[];
      energies: string[];
      genres: string[];
      regions: string[];
    }>>('/query/options');
  },
};

// 标签生成相关 API
export const taggingApi = {
  // 获取标签生成状态
  getStatus: async () => {
    return await api.get<ApiResponse<TaggingStatus>>('/tagging/status');
  },

  // 开始标签生成
  startTagging: async () => {
    return await api.post<ApiResponse<{ message: string }>>('/tagging/start');
  },

  // 中止标签生成
  stopTagging: async () => {
    return await api.post<ApiResponse<{ message: string }>>('/tagging/stop');
  },

  // 测试单首歌曲标签生成
  testTag: async (title: string, artist: string, album: string) => {
    return await api.post<ApiResponse<{
      title: string;
      artist: string;
      album: string;
      tags: any;
      raw_response: string;
    }>>('/tagging/generate', { title, artist, album });
  },

  // 获取标签生成历史记录
  getHistory: async (limit: number = 20, offset: number = 0) => {
    return await api.get<ApiResponse<{
      items: any[];
      total: number;
      limit: number;
      offset: number;
    }>>('/tagging/history', { params: { limit, offset } });
  },

  // SSE 流式获取进度
    streamProgress: (onProgress: (data: any) => void, onComplete: () => void, onError: (_error: Error) => void) => {
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
      } catch {
        console.error('解析 SSE 数据失败');
      }
    };

    eventSource.onerror = (_error) => {
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
    return await api.get<ApiResponse<AnalysisStats>>('/analyze/overview');
  },

  // 获取系统健康度
  getHealth: async () => {
    return await api.get<ApiResponse<HealthData>>('/analyze/health');
  },

  // 获取用户统计
  getUserStats: async (username: string) => {
    return await api.get<ApiResponse<UserStats>>(`/recommend/profile/${username}`);
  },

  // 获取所有用户列表
  getUsers: async () => {
    return await api.get<ApiResponse<{ users: string[] }>>('/recommend/users');
  },
};

// 配置管理相关 API
export const configApi = {
  // 获取 API 配置
  getConfig: async () => {
    return await api.get<ApiResponse<{
      api_key: string;
      base_url: string;
      model: string;
      is_configured: boolean;
    }>>('/config/api');
  },

  // 更新 API 配置
  updateConfig: async (config: { apiKey: string; baseUrl?: string; model?: string }) => {
    return await api.post<ApiResponse<{ message: string; api_key: string }>>('/config/api', {
      api_key: config.apiKey,
      base_url: config.baseUrl,
      model: config.model,
    });
  },

  // 重置 API 配置
  resetConfig: async () => {
    return await api.delete<ApiResponse<{ message: string }>>('/config/api');
  },

  // 获取推荐配置
  getRecommendConfig: async () => {
    return await api.get<ApiResponse<{
      recommend: RecommendConfig;
      user_profile: UserProfileConfig;
      algorithm: AlgorithmConfig;
    }>>('/config/recommend');
  },

  // 更新推荐配置
  updateRecommendConfig: async (params: {
    recommend?: RecommendConfig;
    user_profile?: UserProfileConfig;
    algorithm?: AlgorithmConfig;
  }) => {
    return await api.put<ApiResponse<{ message: string }>>('/config/recommend', params);
  },

  // 获取标签配置
  getTaggingConfig: async () => {
    return await api.get<ApiResponse<{
      api_config: TaggingApiConfig;
    }>>('/config/tagging');
  },

  // 更新标签配置
  updateTaggingConfig: async (params: {
    api_config?: TaggingApiConfig;
  }) => {
    return await api.put<ApiResponse<{ message: string }>>('/config/tagging', params);
  },

  // 获取所有配置
  getAllConfig: async () => {
    return await api.get<ApiResponse<AllConfig>>('/config/all');
  },
};

// 日志查看相关 API
export const logsApi = {
  // 列出所有日志文件
  listLogs: async () => {
    return await api.get<ApiResponse<LogFileInfo[]>>('/logs');
  },

  // 获取日志文件内容
  getLogContent: async (
    logFile: string,
    tail?: number,
    head?: number,
    filterLevel?: string
  ) => {
    return await api.get<ApiResponse<LogContentResponse>>(`/logs/${logFile}`, {
      params: { tail, head, filter_level: filterLevel }
    });
  },

  // 获取日志文件信息
  getLogFileInfo: async (logFile: string) => {
    return await api.get<ApiResponse<LogFileInfo>>(`/logs/${logFile}/size`);
  },
};

// 重复检测相关 API
export const duplicateApi = {
  // 检测所有重复项
  getAllDuplicates: async (): Promise<ApiResponse<AllDuplicatesResponse>> => {
    return await api.get('/duplicate/all');
  },

  // 检测重复歌曲
  getDuplicateSongs: async (): Promise<ApiResponse<DuplicateSongsResponse>> => {
    return await api.get('/duplicate/songs');
  },

  // 检测重复专辑
  getDuplicateAlbums: async (): Promise<ApiResponse<DuplicateAlbumsResponse>> => {
    return await api.get('/duplicate/albums');
  },

  // 检测专辑内重复
  getDuplicateSongsInAlbum: async (): Promise<ApiResponse<DuplicateSongsInAlbumResponse>> => {
    return await api.get('/duplicate/songs-in-album');
  },
};

export default api;
