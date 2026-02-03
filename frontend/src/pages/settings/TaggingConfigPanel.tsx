import { X } from 'lucide-react';
import type { AllowedLabels, TaggingApiConfig } from '../../types';

interface TaggingConfigProps {
  allowedLabels: AllowedLabels;
  setAllowedLabels: (labels: AllowedLabels) => void;
  taggingApiConfig: TaggingApiConfig;
  setTaggingApiConfig: (config: TaggingApiConfig) => void;
}

export default function TaggingConfig({
  allowedLabels,
  setAllowedLabels,
  taggingApiConfig,
  setTaggingApiConfig,
}: TaggingConfigProps) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">标签白名单</h3>
        <div className="space-y-6">
          {Object.entries(allowedLabels).map(([key, labels]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">
                {key}
              </label>
              <div className="flex flex-wrap gap-2">
                {labels.map((label: string) => (
                  <span
                    key={label}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-700"
                  >
                    {label}
                    <button
                      onClick={() => {
                        setAllowedLabels({
                          ...allowedLabels,
                          [key]: labels.filter((l: string) => l !== label)
                        });
                      }}
                      className="ml-2 hover:text-primary-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="mt-2 flex gap-2">
                <input
                  type="text"
                  placeholder={`Add ${key} tag...`}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const value = (e.target as HTMLInputElement).value.trim();
                      if (value && !labels.includes(value)) {
                        setAllowedLabels({
                          ...allowedLabels,
                          [key]: [...labels, value]
                        });
                        (e.target as HTMLInputElement).value = '';
                      }
                    }
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">API 配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">超时时间（秒）</label>
            <input
              type="number"
              min="1"
              value={taggingApiConfig.timeout}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, timeout: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">最大 Token 数</label>
            <input
              type="number"
              min="1"
              value={taggingApiConfig.max_tokens}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, max_tokens: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">温度参数</label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={taggingApiConfig.temperature}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, temperature: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">重试延迟（秒）</label>
            <input
              type="number"
              min="0"
              value={taggingApiConfig.retry_delay}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, retry_delay: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">最大重试次数</label>
            <input
              type="number"
              min="0"
              value={taggingApiConfig.max_retries}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, max_retries: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">重试退避倍数</label>
            <input
              type="number"
              min="1"
              value={taggingApiConfig.retry_backoff}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, retry_backoff: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
