import type { AlgorithmConfig } from '../../types';

interface AlgorithmConfigPanelProps {
  algorithmConfig: AlgorithmConfig;
  setAlgorithmConfig: (config: AlgorithmConfig) => void;
}

export default function AlgorithmConfigPanel({
  algorithmConfig,
  setAlgorithmConfig,
}: AlgorithmConfigPanelProps) {
  return (
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
  );
}
