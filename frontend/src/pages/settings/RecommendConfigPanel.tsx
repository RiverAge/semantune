import type { RecommendConfig, UserProfileConfig, AlgorithmConfig } from '../../types';

interface RecommendConfigProps {
  recommendConfig: RecommendConfig;
  setRecommendConfig: (config: RecommendConfig) => void;
  userProfileConfig: UserProfileConfig;
  setUserProfileConfig: (config: UserProfileConfig) => void;
  algorithmConfig: AlgorithmConfig;
  setAlgorithmConfig: (config: AlgorithmConfig) => void;
}

export default function RecommendConfig({
  recommendConfig,
  setRecommendConfig,
  userProfileConfig,
  setUserProfileConfig,
  algorithmConfig,
  setAlgorithmConfig,
}: RecommendConfigProps) {
  return (
    <div className="space-y-6">
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

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">标签权重</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">情绪权重</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={recommendConfig.tag_weights.mood}
              onChange={(e) => setRecommendConfig({
                ...recommendConfig,
                tag_weights: { ...recommendConfig.tag_weights, mood: parseFloat(e.target.value) }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">能量权重</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={recommendConfig.tag_weights.energy}
              onChange={(e) => setRecommendConfig({
                ...recommendConfig,
                tag_weights: { ...recommendConfig.tag_weights, energy: parseFloat(e.target.value) }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">流派权重</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={recommendConfig.tag_weights.genre}
              onChange={(e) => setRecommendConfig({
                ...recommendConfig,
                tag_weights: { ...recommendConfig.tag_weights, genre: parseFloat(e.target.value) }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">地区权重</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={recommendConfig.tag_weights.region}
              onChange={(e) => setRecommendConfig({
                ...recommendConfig,
                tag_weights: { ...recommendConfig.tag_weights, region: parseFloat(e.target.value) }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">用户画像权重</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">播放次数权重</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={userProfileConfig.play_count}
              onChange={(e) => setUserProfileConfig({ ...userProfileConfig, play_count: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">收藏加分</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={userProfileConfig.starred}
              onChange={(e) => setUserProfileConfig({ ...userProfileConfig, starred: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">歌单加分</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={userProfileConfig.in_playlist}
              onChange={(e) => setUserProfileConfig({ ...userProfileConfig, in_playlist: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">时间衰减周期（天）</label>
            <input
              type="number"
              min="1"
              value={userProfileConfig.time_decay_days}
              onChange={(e) => setUserProfileConfig({ ...userProfileConfig, time_decay_days: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">最小衰减系数</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={userProfileConfig.min_decay}
              onChange={(e) => setUserProfileConfig({ ...userProfileConfig, min_decay: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">算法配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">利用型候选池倍数</label>
            <input
              type="number"
              min="1"
              value={algorithmConfig.exploitation_pool_multiplier}
              onChange={(e) => setAlgorithmConfig({ ...algorithmConfig, exploitation_pool_multiplier: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">探索型池起始位置</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={algorithmConfig.exploration_pool_start}
              onChange={(e) => setAlgorithmConfig({ ...algorithmConfig, exploration_pool_start: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">探索型池结束位置</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={algorithmConfig.exploration_pool_end}
              onChange={(e) => setAlgorithmConfig({ ...algorithmConfig, exploration_pool_end: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">随机扰动系数</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={algorithmConfig.randomness}
              onChange={(e) => setAlgorithmConfig({ ...algorithmConfig, randomness: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
