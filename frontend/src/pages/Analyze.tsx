import { useState, useEffect } from 'react';
import { Users } from 'lucide-react';
import { analyzeApi } from '../api/client';
import type { UserStats } from '../types';

export default function Analyze() {
  const [users, setUsers] = useState<string[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await analyzeApi.getUsers();

      if (response.success && response.data) {
        setUsers(response.data.users);
      }
    } catch (err) {
      console.error('加载用户列表失败:', err);
    }
  };

  const handleSelectUser = async (username: string) => {
    setSelectedUser(username);
    try {
      setLoading(true);
      setError(null);
      const response = await analyzeApi.getUserStats(username);

      if (response.success && response.data) {
        setUserStats(response.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载用户统计失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">用户分析</h1>
        <p className="text-gray-600 mt-1">查看用户的音乐偏好和统计数据</p>
      </div>

      {/* 用户选择 */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Users className="h-5 w-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold">选择用户</h2>
        </div>
        <div>
          <select
            value={selectedUser}
            onChange={(e) => handleSelectUser(e.target.value)}
            className="input"
          >
            <option value="">请选择用户</option>
            {users.map((user) => (
              <option key={user} value={user}>{user}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* 用户统计数据 */}
      {userStats && (
        <>
          {/* 基础统计 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">基础统计</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">总播放次数</p>
                <p className="text-xl font-bold">{userStats.total_plays}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">听过歌曲</p>
                <p className="text-xl font-bold">{userStats.unique_songs}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">收藏歌曲</p>
                <p className="text-xl font-bold">{userStats.starred_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">歌单数量</p>
                <p className="text-xl font-bold">{userStats.playlist_count}</p>
              </div>
            </div>
          </div>

          {/* 偏好分析 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 喜欢的歌手 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">喜欢的歌手</h3>
              <div className="space-y-2">
                {userStats.top_artists.length > 0 ? (
                  userStats.top_artists.map((artist) => (
                    <div key={artist.artist} className="flex items-center justify-between">
                      <span className="text-gray-700">{artist.artist}</span>
                      <span className="text-sm text-gray-500">{artist.count} 次</span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">暂无数据</p>
                )}
              </div>
            </div>

            {/* 喜欢的流派 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">喜欢的流派</h3>
              <div className="space-y-2">
                {userStats.top_genres.length > 0 ? (
                  userStats.top_genres.map((genre) => (
                    <div key={genre.genre} className="flex items-center justify-between">
                      <span className="text-gray-700">{genre.genre}</span>
                      <span className="text-sm text-gray-500">{genre.count} 首</span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">暂无数据</p>
                )}
              </div>
            </div>

            {/* 喜欢的情绪 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">喜欢的情绪</h3>
              <div className="space-y-2">
                {userStats.top_moods.length > 0 ? (
                  userStats.top_moods.map((mood) => (
                    <div key={mood.mood} className="flex items-center justify-between">
                      <span className="text-gray-700">{mood.mood}</span>
                      <span className="text-sm text-gray-500">{mood.count} 首</span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">暂无数据</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* 加载状态 */}
      {loading && !userStats && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}
    </div>
  );
}
