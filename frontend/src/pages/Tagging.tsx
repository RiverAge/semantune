import { useState, useEffect, useRef } from 'react';
import { Tag, Play, Clock, AlertCircle, CheckCircle, History, TestTube, Settings, Save } from 'lucide-react';
import { taggingApi } from '../api/client';
import type { TaggingStatus } from '../types';

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
  const [configError, setConfigError] = useState<string | null>(null);
  const [configSuccess, setConfigSuccess] = useState<string | null>(null);
  
  // 批量生成状态
  const [status, setStatus] = useState<TaggingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // 历史记录状态
  const [history, setHistory] = useState<any[]>([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyOffset, setHistoryOffset] = useState(0);
  const historyLimit = 20;

  // 标签测试状态
  const [testTitle, setTestTitle] = useState('');
  const [testArtist, setTestArtist] = useState('');
  const [testAlbum, setTestAlbum] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testSuccessMessage, setTestSuccessMessage] = useState<string | null>(null);

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

  const loadConfig = () => {
    try {
      const savedConfig = localStorage.getItem('tagging_config');
      if (savedConfig) {
        const parsed = JSON.parse(savedConfig);
        setConfig(parsed);
        setIsConfigured(true);
      } else {
        setShowConfig(true);
      }
    } catch (err) {
      console.error('加载配置失败:', err);
      setShowConfig(true);
    }
  };

  const handleSaveConfig = () => {
    setConfigError(null);
    setConfigSuccess(null);

    if (!config.apiKey.trim()) {
      setConfigError('请输入 API Key');
      return;
    }

    if (!config.baseUrl.trim()) {
      setConfigError('请输入 API Base URL');
      return;
    }

    if (!config.model.trim()) {
      setConfigError('请输入模型名称');
      return;
    }

    try {
      localStorage.setItem('tagging_config', JSON.stringify(config));
      setIsConfigured(true);
      setShowConfig(false);
      setConfigSuccess('配置已保存');
      setTimeout(() => setConfigSuccess(null), 3000);
    } catch (err) {
      setConfigError('保存配置失败');
    }
  };

  const handleResetConfig = () => {
    localStorage.removeItem('tagging_config');
    setConfig(DEFAULT_CONFIG);
    setIsConfigured(false);
    setShowConfig(true);
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
        setError(response.message || '启动标签生成失败');
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

  const handleTestTag = async () => {
    if (!testTitle || !testArtist) {
      setTestError('请输入歌曲标题和歌手名称');
      return;
    }
    
    try {
      setIsTesting(true);
      setTestError(null);
      setTestResult(null);
      
      const response = await taggingApi.testTag(testTitle, testArtist, testAlbum);
      if (response.success && response.data) {
        setTestResult(response.data);
        setTestSuccessMessage('标签生成成功');
        setTimeout(() => setTestSuccessMessage(null), 3000);
      }
    } catch (err) {
      setTestError(err instanceof Error ? err.message : '标签生成失败');
    } finally {
      setIsTesting(false);
    }
  };

  // 配置页面
  if (showConfig) {
    return (
      <div className="space-y-6">
        {/* 标题 */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API 配置</h1>
          <p className="text-gray-600 mt-1">配置 LLM API 以使用标签生成功能</p>
        </div>

        {/* 配置表单 */}
        <div className="card">
          <div className="flex items-center mb-6">
            <Settings className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold">API 设置</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key *</label>
              <input
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                placeholder="输入您的 API Key"
                className="input"
              />
              <p className="text-xs text-gray-500 mt-1">您的 API Key 将安全地保存在浏览器本地存储中</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL *</label>
              <input
                type="text"
                value={config.baseUrl}
                onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
                placeholder="例如：https://integrate.api.nvidia.com/v1/chat/completions"
                className="input"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">模型名称 *</label>
              <input
                type="text"
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
                placeholder="例如：meta/llama-3.3-70b-instruct"
                className="input"
              />
            </div>

            {/* 错误提示 */}
            {configError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
                <AlertCircle className="h-5 w-5 mr-2" />
                {configError}
              </div>
            )}

            {/* 成功提示 */}
            {configSuccess && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2" />
                {configSuccess}
              </div>
            )}

            <button
              onClick={handleSaveConfig}
              className="btn btn-primary flex items-center"
            >
              <Save className="h-4 w-4 mr-2" />
              保存配置
            </button>
          </div>
        </div>
      </div>
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
        <>
          {/* 状态卡片 */}
          {status && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">总歌曲数</p>
                    <p className="text-2xl font-bold">{status.total}</p>
                  </div>
                  <Tag className="h-8 w-8 text-primary-600" />
                </div>
              </div>
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">已处理</p>
                    <p className="text-2xl font-bold text-green-600">{status.processed}</p>
                  </div>
                  <Play className="h-8 w-8 text-green-600" />
                </div>
              </div>
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">待处理</p>
                    <p className="text-2xl font-bold text-orange-600">{status.pending}</p>
                  </div>
                  <Clock className="h-8 w-8 text-orange-600" />
                </div>
              </div>
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">失败</p>
                    <p className="text-2xl font-bold text-red-600">{status.failed}</p>
                  </div>
                  <AlertCircle className="h-8 w-8 text-red-600" />
                </div>
              </div>
            </div>
          )}

          {/* 进度条 */}
          {status && status.total > 0 && (
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">处理进度</span>
                <span className="text-sm text-gray-600">{status.progress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${status.progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">开始生成标签</h3>
                <p className="text-sm text-gray-600 mt-1">
                  使用 {config.model} 模型为未标签的歌曲生成语义标签
                </p>
              </div>
              {isGenerating ? (
                <button
                  onClick={handleStopTagging}
                  className="btn btn-danger"
                >
                  中止
                </button>
              ) : (
                <button
                  onClick={handleStartTagging}
                  disabled={status?.pending === 0}
                  className="btn btn-primary"
                >
                  开始生成
                </button>
              )}
            </div>
          </div>

          {/* 成功提示 */}
          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center">
              <CheckCircle className="h-5 w-5 mr-2" />
              {successMessage}
            </div>
          )}

          {/* 历史记录 */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <History className="h-5 w-5 text-primary-600 mr-2" />
                <h2 className="text-lg font-semibold">标记历史</h2>
                <span className="ml-2 text-sm text-gray-500">
                  ({historyTotal} 条记录)
                </span>
              </div>
              {historyOffset > 0 && (
                <button
                  onClick={() => {
                    setHistoryOffset(Math.max(0, historyOffset - historyLimit));
                    loadHistory();
                  }}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  上一页
                </button>
              )}
              {historyOffset + historyLimit < historyTotal && (
                <button
                  onClick={() => {
                    setHistoryOffset(historyOffset + historyLimit);
                    loadHistory();
                  }}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  下一页
                </button>
              )}
            </div>
            
            {history.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                暂无标记记录
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((item, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="font-medium text-gray-900">
                        {item.artist} - {item.title}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(item.updated_at).toLocaleString('zh-CN')}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                        {item.tags.mood || 'N/A'}
                      </span>
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                        {item.tags.energy || 'N/A'}
                      </span>
                      <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                        {item.tags.genre || 'N/A'}
                      </span>
                      <span className="px-2 py-0.5 bg-pink-100 text-pink-700 text-xs rounded-full">
                        {item.tags.scene || 'N/A'}
                      </span>
                      <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                        {item.tags.region || 'N/A'}
                      </span>
                      <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                        {item.tags.subculture || 'N/A'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
              <AlertCircle className="h-5 w-5 mr-2" />
              {error}
            </div>
          )}
        </>
      )}

      {/* 标签测试标签页 */}
      {activeTab === 'test' && (
        <>
          {/* 测试表单 */}
          <div className="card">
            <div className="flex items-center mb-4">
              <TestTube className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">输入歌曲信息</h2>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">歌曲标题 *</label>
                  <input
                    type="text"
                    value={testTitle}
                    onChange={(e) => setTestTitle(e.target.value)}
                    placeholder="例如：晴天"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">歌手名称 *</label>
                  <input
                    type="text"
                    value={testArtist}
                    onChange={(e) => setTestArtist(e.target.value)}
                    placeholder="例如：周杰伦"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">专辑名称</label>
                  <input
                    type="text"
                    value={testAlbum}
                    onChange={(e) => setTestAlbum(e.target.value)}
                    placeholder="例如：叶惠美"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              <button
                onClick={handleTestTag}
                disabled={isTesting || !testTitle || !testArtist}
                className="btn btn-primary"
              >
                {isTesting ? '生成中...' : '测试标签生成'}
              </button>
            </div>
          </div>

          {/* 成功提示 */}
          {testSuccessMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center">
              <CheckCircle className="h-5 w-5 mr-2" />
              {testSuccessMessage}
            </div>
          )}

          {/* 错误提示 */}
          {testError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
              <AlertCircle className="h-5 w-5 mr-2" />
              {testError}
            </div>
          )}

          {/* 测试结果 */}
          {testResult && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">生成结果</h2>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-gray-900">
                    {testResult.artist} - {testResult.title}
                  </span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                    情绪: {testResult.tags.mood || 'N/A'}
                  </span>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                    能量: {testResult.tags.energy || 'N/A'}
                  </span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                    流派: {testResult.tags.genre || 'N/A'}
                  </span>
                  <span className="px-2 py-1 bg-pink-100 text-pink-700 text-xs rounded-full">
                    场景: {testResult.tags.scene || 'N/A'}
                  </span>
                  <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
                    地区: {testResult.tags.region || 'N/A'}
                  </span>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                    亚文化: {testResult.tags.subculture || 'N/A'}
                  </span>
                  {testResult.tags.confidence && (
                    <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded-full">
                      置信度: {(testResult.tags.confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
