import type { TaggingApiConfig } from '../../types';

interface TaggingConfigProps {
  taggingApiConfig: TaggingApiConfig;
  setTaggingApiConfig: (config: TaggingApiConfig) => void;
}

export default function TaggingConfig({
  taggingApiConfig,
  setTaggingApiConfig,
}: TaggingConfigProps) {
  return (
    <div className="space-y-6">
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Top-p 参数</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={(taggingApiConfig as any).top_p ?? 0.9}
              onChange={(e) => setTaggingApiConfig({ ...taggingApiConfig, top_p: parseFloat(e.target.value) } as any)}
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

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">标签白名单说明</h4>
        <p className="text-sm text-blue-700">
          标签白名单（mood、energy、genre、style、scene、region、culture、language）现在通过后台配置文件 <code className="bg-blue-100 px-1 rounded">config/tagging_config.yaml</code> 进行管理。
          请直接编辑该配置文件来修改标签列表。
        </p>
      </div>
    </div>
  );
}
