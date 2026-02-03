import type { RecommendConfig } from '../../types';

interface BasicConfigProps {
  recommendConfig: RecommendConfig;
  setRecommendConfig: (config: RecommendConfig) => void;
}

export default function BasicConfig({
  recommendConfig,
  setRecommendConfig,
}: BasicConfigProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">推荐基础配置</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">默认推荐数量</label>
          <input
            type="number"
            min="1"
            max="100"
            value={recommendConfig.default_limit}
            onChange={(e) => setRecommendConfig({ ...recommendConfig, default_limit: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">过滤最近听过的歌曲数</label>
          <input
            type="number"
            min="0"
            value={recommendConfig.recent_filter_count}
            onChange={(e) => setRecommendConfig({ ...recommendConfig, recent_filter_count: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">每个歌手最多推荐数</label>
          <input
            type="number"
            min="1"
            value={recommendConfig.diversity_max_per_artist}
            onChange={(e) => setRecommendConfig({ ...recommendConfig, diversity_max_per_artist: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">每张专辑最多推荐数</label>
          <input
            type="number"
            min="1"
            value={recommendConfig.diversity_max_per_album}
            onChange={(e) => setRecommendConfig({ ...recommendConfig, diversity_max_per_album: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">探索型歌曲占比</label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={recommendConfig.exploration_ratio}
            onChange={(e) => setRecommendConfig({ ...recommendConfig, exploration_ratio: parseFloat(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>
    </div>
  );
}
