import type { UserProfileConfig } from '../../types';

interface UserProfileConfigPanelProps {
  userProfileConfig: UserProfileConfig;
  setUserProfileConfig: (config: UserProfileConfig) => void;
}

export default function UserProfileConfigPanel({
  userProfileConfig,
  setUserProfileConfig,
}: UserProfileConfigPanelProps) {
  return (
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
  );
}
