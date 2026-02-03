import type { RecommendConfig } from '../../types';

interface TagWeightsProps {
  recommendConfig: RecommendConfig;
  setRecommendConfig: (config: RecommendConfig) => void;
}

export default function TagWeights({
  recommendConfig,
  setRecommendConfig,
}: TagWeightsProps) {
  return (
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
  );
}
