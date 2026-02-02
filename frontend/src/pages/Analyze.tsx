import { useState, useEffect } from 'react';
import { BarChart3, Users, Music, TrendingUp } from 'lucide-react';
import { analyzeApi } from '../api/client';
import type { AnalysisStats, UserStats } from '../types';

export default function Analyze() {
  const [stats, setStats] = useState<AnalysisStats | null>(null);
  const [users, setUsers] = useState<string[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    loadUsers();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await analyzeApi.getStats();
      if (response.success && response.data) {
        setStats(response.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await analyzeApi.getUsers();
      if (response.success && response.data) {
        setUsers(response.data);
      }
    } catch (err) {
      console.error('加载用户列表失败:', err);
    }
  };

  const handleSelectUser = async (username: string) => {
    setSelectedUser(username);
    try {
      setLoading(true);
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

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadStats}
          className="mt-4 btn btn-primary"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">数据分析</h1>
        <p className="text-gray-600 mt-1">查看音乐库和用户的统计数据</p>
      </div>

      {/* 整体统计 */}
      {stats && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">总歌曲数</p>
                  <p className="text-2xl font-bold">{stats.total_songs}</p>
                </div>
                <Music className="h-8 w-8 text-primary-600" />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">已标签歌曲</p>
                  <p className="text-2xl font-bold text-green-600">{stats.tagged_songs}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">标签覆盖率</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {stats.tag_coverage.toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-600" />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">未标签歌曲</p>
                  <p className="text-2xl font-bold text-orange-600">{stats.untagged_songs}</p>
                </div>
                <Music className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </div>

          {/* 标签分布 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 情绪分布 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">情绪分布</h3>
              <div className="space-y-3">
                {Object.entries(stats.mood_distribution)
                  .sort(([, a], [, b]) => b - a)
                  .map(([mood, count]) => (
                    <div key={mood} className="flex items-center justify-between">
                      <span className="text-gray-700">{mood}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full"
                            style={{
                              width: `${(count / stats.tagged_songs) * 100}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* 能量分布 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">能量分布</h3>
              <div className="space-y-3">
                {Object.entries(stats.energy_distribution)
                  .sort(([, a], [, b]) => b - a)
                  .map(([energy, count]) => (
                    <div key={energy} className="flex items-center justify-between">
                      <span className="text-gray-700">{energy}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{
                              width: `${(count / stats.tagged_songs) * 100}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* 流派分布 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">流派分布</h3>
              <div className="space-y-3">
                {Object.entries(stats.genre_distribution)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 10)
                  .map(([genre, count]) => (
                    <div key={genre} className="flex items-center justify-between">
                      <span className="text-gray-700">{genre}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-500 h-2 rounded-full"
                            style={{
                              width: `${(count / stats.tagged_songs) * 100}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* 地区分布 */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">地区分布</h3>
              <div className="space-y-3">
                {Object.entries(stats.region_distribution)
                  .sort(([, a], [, b]) => b - a)
                  .map(([region, count]) => (
                    <div key={region} className="flex items-center justify-between">
                      <span className="text-gray-700">{region}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-orange-500 h-2 rounded-full"
                            style={{
                              width: `${(count / stats.tagged_songs) * 100}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* 用户分析 */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Users className="h-5 w-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold">用户分析</h2>
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            选择用户
          </label>
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

        {userStats && (
          <div className="space-y-4">
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

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">喜欢的歌手</p>
                <div className="space-y-1">
                  {userStats.top_artists.map((artist) => (
                    <p key={artist.artist} className="text-sm text-gray-600">
                      {artist.artist} ({artist.count})
                    </p>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">喜欢的流派</p>
                <div className="space-y-1">
                  {userStats.top_genres.map((genre) => (
                    <p key={genre.genre} className="text-sm text-gray-600">
                      {genre.genre} ({genre.count})
                    </p>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">喜欢的情绪</p>
                <div className="space-y-1">
                  {userStats.top_moods.map((mood) => (
                    <p key={mood.mood} className="text-sm text-gray-600">
                      {mood.mood} ({mood.count})
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
