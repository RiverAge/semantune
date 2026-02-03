import { useState, useEffect, useRef } from 'react';
import { Tag, TestTube, Settings } from 'lucide-react';
import { taggingApi, configApi } from '../api/client';
import type { TaggingStatus } from '../types';
import TaggingConfig from './tagging/TaggingConfig';
import BatchTagging from './tagging/BatchTagging';
import TagTest from './tagging/TagTest';

type TabType = 'batch' | 'test';

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

export default function Tagging() {
  const [activeTab, setActiveTab] = useState<TabType>('batch');

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

  const loadConfig = async () => {
    try {
      const response = await configApi.getConfig();
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
      const response = await configApi.resetConfig();
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
        },
        // onComplete
        () => {
          setIsGenerating(false);
          loadStatus(); // 刷新最终状态
          loadHistory(); // 刷新历史记录
        },
        // onError
        (err) => {
          setError(err.message);
          setIsGenerating(false);
        }
      );
    }
  }, [status]);

  const loadStatus = async () => {
    try {
      const response = await taggingApi.getStatus();
      if (response.success && response.data) {
        setStatus(response.data);
      }
    } catch (err) {
      console.error('加载状态失败:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await taggingApi.getHistory(historyLimit, historyOffset);
      if (response.success && response.data) {
        setHistory(response.data.items);
        setHistoryTotal(response.data.total);
      }
    } catch (err) {
      console.error('加载历史记录失败:', err);
    }
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
        },
        // onComplete
        () => {
          setIsGenerating(false);
          loadStatus(); // 刷新最终状态
          loadHistory(); // 刷新历史记录
          // 显示成功消息
          if (status && status.processed > 0) {
            setSuccessMessage(`成功处理了 ${status.processed} 首歌曲`);
          } else {
            setSuccessMessage('标签生成任务已完成');
          }
          // 3秒后自动隐藏成功消息
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
      const response = await taggingApi.startTagging();
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
      const response = await taggingApi.stopTagging();
      if (response.success) {
        setSuccessMessage('任务已中止');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '中止任务失败');
    }
  };

  // 配置页面
  if (showConfig) {
    return (
      <TaggingConfig
        config={config}
        setConfig={setConfig}
        setIsConfigured={setIsConfigured}
        setShowConfig={setShowConfig}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">语义标签生成</h1>
          <p className="text-gray-600 mt-1">使用 LLM 为音乐库中的歌曲生成语义标签</p>
        </div>
        <button
          onClick={handleResetConfig}
          className="text-sm text-gray-500 hover:text-primary-600 flex items-center"
        >
          <Settings className="h-4 w-4 mr-1" />
          重新配置
        </button>
      </div>

      {/* 标签页切换 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('batch')}
            className={`flex items-center px-1 py-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'batch'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Tag className="h-4 w-4 mr-2" />
            批量生成
          </button>
          <button
            onClick={() => setActiveTab('test')}
            className={`flex items-center px-1 py-2 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'test'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <TestTube className="h-4 w-4 mr-2" />
            标签测试
          </button>
        </nav>
      </div>

      {/* 批量生成标签页 */}
      {activeTab === 'batch' && (
        <BatchTagging
          status={status}
          isGenerating={isGenerating}
          config={config}
          history={history}
          historyTotal={historyTotal}
          historyLimit={historyLimit}
          historyOffset={historyOffset}
          error={error}
          successMessage={successMessage}
          onStartTagging={handleStartTagging}
          onStopTagging={handleStopTagging}
          onLoadHistory={loadHistory}
          onHistoryOffsetChange={setHistoryOffset}
        />
      )}

      {/* 标签测试标签页 */}
      {activeTab === 'test' && (
        <TagTest onTestSuccess={() => {}} />
      )}
    </div>
  );
}
