import { useState } from 'react';
import { Music, User, Sparkles, Download } from 'lucide-react';
import { recommendApi } from '../api/client';
import { TagDisplay } from '../components/TagDisplay';
import type { Recommendation, UserStats } from '../types';

export default function Recommend() {
  const [username, setUsername] = useState('');
  const [limit, setLimit] = useState(30);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [userProfile, setUserProfile] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const handleExportReport = async () => {
    if (!username.trim()) {
      setError('请先获取推荐');
      return;
    }
    try {
      setExporting(true);
      await recommendApi.exportReport(username, limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : '导出报告失败');
    } finally {
      setExporting(false);
    }
  };

  const handleGetRecommendations = async () => {
    if (!username.trim()) {
      setError('请输入用户名');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // 分别处理两个请求，避免一个失败导致另一个也失败
      try {
        const recResponse = await recommendApi.getRecommendationsByUsername(username, limit);

        if (recResponse.success && recResponse.data) {
          setRecommendations(recResponse.data);
        } else {
          setError(recResponse.error || '获取推荐失败');
        }
      } catch (recErr) {
        setError(recErr instanceof Error ? recErr.message : '获取推荐失败');
      }

      try {
        const profileResponse = await recommendApi.getUserProfile(username);

        if (profileResponse.success && profileResponse.data) {
          setUserProfile(profileResponse.data);
        }
      } catch (profileErr) {
        // 用户画像失败不影响推荐显示
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">个性化推荐</h1>
        <p className="text-gray-600 mt-1">基于您的音乐偏好，为您推荐可能喜欢的歌曲</p>
      </div>

      {/* 输入表单 */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleGetRecommendations()}
              placeholder="输入 Navidrome 用户名"
              className="input"
            />
          </div>
          <div className="w-full sm:w-32">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              推荐数量
            </label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              min={1}
              max={100}
              className="input"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleGetRecommendations}
              disabled={loading}
              className="btn btn-primary w-full sm:w-auto"
            >
              {loading ? '生成中...' : '获取推荐'}
            </button>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* 用户画像 */}
      {userProfile && (
        <div className="card">
          <div className="flex items-center mb-4">
            <User className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold">用户画像</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">总播放次数</p>
              <p className="text-xl font-bold">{userProfile.total_plays}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">听过歌曲</p>
              <p className="text-xl font-bold">{userProfile.unique_songs}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">收藏歌曲</p>
              <p className="text-xl font-bold">{userProfile.starred_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">歌单数量</p>
              <p className="text-xl font-bold">{userProfile.playlist_count}</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">喜欢的歌手</p>
              <div className="space-y-1">
                {userProfile.top_artists.slice(0, 3).map((artist) => (
                  <p key={artist.artist} className="text-sm text-gray-600">
                    {artist.artist} ({artist.count})
                  </p>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">喜欢的流派</p>
              <div className="space-y-1">
                {userProfile.top_genres.slice(0, 3).map((genre) => (
                  <p key={genre.genre} className="text-sm text-gray-600">
                    {genre.genre} ({genre.count})
                  </p>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">喜欢的情绪</p>
              <div className="space-y-1">
                {userProfile.top_moods.slice(0, 3).map((mood) => (
                  <p key={mood.mood} className="text-sm text-gray-600">
                    {mood.mood} ({mood.count})
                  </p>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">语言分布</p>
              <div className="space-y-1">
                {userProfile.top_languages.slice(0, 3).map((lang) => (
                  <p key={lang.language} className="text-sm text-gray-600">
                    {lang.language} ({lang.count})
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 推荐列表 */}
      {recommendations.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Sparkles className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-lg font-semibold">推荐歌曲</h2>
              <span className="ml-2 text-sm text-gray-500">
                ({recommendations.length} 首)
              </span>
            </div>
            <button
              onClick={handleExportReport}
              disabled={exporting}
              className="btn btn-secondary text-sm"
            >
              <Download className="h-4 w-4 mr-1" />
              {exporting ? '导出中...' : '导出报告'}
            </button>
          </div>
          <div className="max-h-[600px] overflow-y-auto pr-2 space-y-3 scroll-smooth">
            {recommendations.map((song, index) => (
              <div
                key={song.file_id}
                className="flex items-start justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-500 w-6">
                      #{index + 1}
                    </span>
                    <div>
                      <h3 className="font-medium text-gray-900">{song.title}</h3>
                      <p className="text-sm text-gray-600">
                        {song.artist} · {song.album}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 space-y-1">
                    <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
                      {song.mood && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">情绪:</span>
                          <TagDisplay value={song.mood} />
                        </div>
                      )}
                      {song.energy && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">能量:</span>
                          <span className="text-green-700 font-medium">{song.energy}</span>
                        </div>
                      )}
                      {song.genre && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">流派:</span>
                          <TagDisplay value={song.genre} />
                        </div>
                      )}
                      {song.style && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">风格:</span>
                          <TagDisplay value={song.style} />
                        </div>
                      )}
                      {song.scene && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">场景:</span>
                          <TagDisplay value={song.scene} />
                        </div>
                      )}
                      {song.region && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">地区:</span>
                          <span className="text-gray-700">{song.region}</span>
                        </div>
                      )}
                      {song.culture && song.culture !== 'None' && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">文化:</span>
                          <span className="text-gray-700">{song.culture}</span>
                        </div>
                      )}
                      {song.language && song.language !== 'None' && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-400 text-xs">语言:</span>
                          <span className="text-gray-700">{song.language}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  {song.reason && (
                    <p className="mt-2 text-sm text-gray-500">{song.reason}</p>
                  )}
                </div>
                <div className="text-right">
                  <div className="flex items-center text-primary-600">
                    <Music className="h-4 w-4 mr-1" />
                    <span className="font-medium">
                      {song.similarity ? (song.similarity * 100).toFixed(1) + '%' : '-'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">相似度</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
