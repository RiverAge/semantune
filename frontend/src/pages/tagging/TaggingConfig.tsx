import { useState } from 'react';
import { Settings, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { configApi } from '../../api/client';

interface ApiConfig {
  apiKey: string;
  baseUrl: string;
  model: string;
}

interface TaggingConfigProps {
  config: ApiConfig;
  setConfig: (config: ApiConfig) => void;
  setIsConfigured: (configured: boolean) => void;
  setShowConfig: (show: boolean) => void;
}

export default function TaggingConfig({
  config,
  setConfig,
  setIsConfigured,
  setShowConfig,
}: TaggingConfigProps) {
  const [configError, setConfigError] = useState<string | null>(null);
  const [configSuccess, setConfigSuccess] = useState<string | null>(null);

  const handleSaveConfig = async () => {
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
      const response = await configApi.updateConfig({
        apiKey: config.apiKey,
        baseUrl: config.baseUrl,
        model: config.model,
      });
      const responseData = response as any;
      if (responseData.success) {
        setIsConfigured(true);
        setShowConfig(false);
        setConfigSuccess('配置已保存');
        setTimeout(() => setConfigSuccess(null), 3000);
      } else {
        setConfigError('保存配置失败');
      }
    } catch (err: any) {
      console.error('保存配置失败:', err);
      setConfigError(err.message || '保存配置失败');
    }
  };

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
