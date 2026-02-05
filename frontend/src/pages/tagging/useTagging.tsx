import { useState, useEffect, useRef } from 'react';
import { taggingApi, configApi } from '../../api/client';
import type { TaggingStatus } from '../../types';

interface ApiConfig {
  apiKey: string;
  baseUrl: string;
  model: string;
}

const DEFAULT_CONFIG: ApiConfig = {
  apiKey: '',
  baseUrl: 'https://integrate.api.nvidia.com/v1/chat/completions',
  model: 'meta/llama-3.3-70b-instruct',
};

export function useTagging() {
  const [activeTab, setActiveTab] = useState<'batch' | 'test'>('batch');

  // 配置状态
  const [config, setConfig] = useState<ApiConfig>(DEFAULT_CONFIG);
  const [isConfigured, setIsConfigured] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // 批量生成状态
  const [status, setStatus] = useState<TaggingStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // 历史记录状态
  const [history, setHistory] = useState<any[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyOffset, setHistoryOffset] = useState(0);
  const historyLimit = 20;

  const loadConfig = async () => {
    try {
      const response = await configApi.getConfig() as any;
      if (response.success && response.data) {
        const { api_key, base_url, model, is_configured } = response.data;
        setConfig({
          apiKey: api_key || '',
          baseUrl: base_url,
          model: model,
        });
        setIsConfigured(is_configured);
        if (!is_configured) {
          setShowConfig(true);
        }
      } else {
        setShowConfig(true);
      }
    } catch (err) {
      console.error('加载配置失败:', err);
      setShowConfig(true);
    }
  };

  const handleResetConfig = async () => {
    try {
      const response = await configApi.resetConfig() as any;
      if (response.success) {
        setConfig(DEFAULT_CONFIG);
        setIsConfigured(false);
        setShowConfig(true);
      }
    } catch (err: any) {
      console.error('重置配置失败:', err);
      setError(err.message || '重置配置失败');
    }
  };

  const loadStatus = async () => {
    try {
      const response = await taggingApi.getStatus() as any;
      if (response.success && response.data) {
        setStatus(response.data);
      }
    } catch (err) {
      console.error('加载状态失败:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await taggingApi.getHistory(historyLimit, historyOffset) as any;
      if (response.success && response.data) {
        setHistory(response.data.items);
        setHistoryTotal(response.data.total);
      }
    } catch (err) {
      console.error('加载历史记录失败:', err);
    }
  };

  const refreshStatusAndHistory = async () => {
    await Promise.all([loadStatus(), loadHistory()]);
  };

  const handleStartTagging = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      setSuccessMessage(null);

      // 先建立 SSE 连接
      eventSourceRef.current = taggingApi.streamProgress(
        // onProgress
        (data) => {
          setStatus({
            total: data.total,
            processed: data.processed,
            pending: data.total - data.processed,
            failed: 0,
            progress: data.total > 0 ? (data.processed / data.total * 100) : 0,
            task_status: data.status
          });
          loadHistory(); // 每次进度更新时刷新历史记录
        },
        // onComplete
        () => {
          setIsGenerating(false);
          refreshStatusAndHistory(); // 刷新最终状态和历史记录
          // 显示成功消息
          const currentProcessed = status?.processed || 0;
          const msg = currentProcessed > 0
            ? `成功处理了 ${currentProcessed} 首歌曲`
            : '标签生成任务已完成';
          setSuccessMessage(msg);
          setTimeout(() => setSuccessMessage(null), 3000);
        },
        // onError
        (err) => {
          setError(err.message);
          setIsGenerating(false);
        }
      );

      // 等待一小段时间确保 SSE 连接建立
      await new Promise(resolve => setTimeout(resolve, 100));

      // 然后启动任务
      const response = await taggingApi.startTagging() as any;
      if (!response.success) {
        setError('启动标签生成失败');
        setIsGenerating(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动标签生成失败');
      setIsGenerating(false);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    }
  };

  const handleStopTagging = async () => {
    try {
      const response = await taggingApi.stopTagging() as any;
      if (response.success) {
        setSuccessMessage('任务已中止');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '中止任务失败');
    }
  };

  // 监听状态变化，如果任务正在运行则建立SSE连接
  useEffect(() => {
    if (status && status.task_status === 'processing' && !eventSourceRef.current && !isGenerating) {
      // 建立SSE连接
      setIsGenerating(true);
      eventSourceRef.current = taggingApi.streamProgress(
        // onProgress
        (data) => {
          setStatus({
            total: data.total,
            processed: data.processed,
            pending: data.total - data.processed,
            failed: 0,
            progress: data.total > 0 ? (data.processed / data.total * 100) : 0,
            task_status: data.status
          });
          loadHistory(); // 每次进度更新时刷新历史记录
        },
        // onComplete
        () => {
          setIsGenerating(false);
          refreshStatusAndHistory(); // 刷新最终状态和历史记录
        },
        // onError
        (err) => {
          setError(err.message);
          setIsGenerating(false);
        }
      );
    }
  }, [status, isGenerating]);

  useEffect(() => {
    // 加载配置
    loadConfig();
  }, []);

  useEffect(() => {
    if (isConfigured) {
      loadStatus();
      loadHistory();
    }

    // 清理函数
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [isConfigured]);

  return {
    activeTab,
    setActiveTab,
    config,
    setConfig,
    isConfigured,
    setIsConfigured,
    showConfig,
    setShowConfig,
    status,
    isGenerating,
    error,
    successMessage,
    history,
    historyTotal,
    historyLimit,
    historyOffset,
    setHistoryOffset,
    handleResetConfig,
    handleStartTagging,
    handleStopTagging,
    loadHistory,
  };
}
