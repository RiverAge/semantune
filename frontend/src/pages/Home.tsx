import { useState, useEffect } from 'react';
import { Music, Users, Tag, TrendingUp } from 'lucide-react';
import { analyzeApi } from '../api/client';
import type { AnalysisStats } from '../types';

export default function Home() {
  const [stats, setStats] = useState<AnalysisStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
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

  if (loading) {
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

  if (!stats) {
    return null;
  }

  const statCards = [
    {
      title: '总歌曲数',
      value: stats.total_songs,
      icon: Music,
      color: 'bg-blue-500',
    },
    {
      title: '已标签歌曲',
      value: stats.tagged_songs,
      icon: Tag,
      color: 'bg-green-500',
    },
    {
      title: '标签覆盖率',
      value: `${stats.tag_coverage.toFixed(1)}%`,
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
    {
      title: '未标签歌曲',
      value: stats.untagged_songs,
      icon: Users,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-8">
      {/* 欢迎横幅 */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          欢迎使用 Navidrome 语义音乐推荐系统
        </h1>
        <p className="text-primary-100">
          基于 LLM 语义标签的个性化音乐推荐，为您发现更多喜爱的音乐
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{card.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{card.value}</p>
                </div>
                <div className={`${card.color} p-3 rounded-lg`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 标签分布 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 情绪分布 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">情绪分布</h3>
          <div className="space-y-3">
            {Object.entries(stats.mood_distribution)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
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

        {/* 流派分布 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">流派分布</h3>
          <div className="space-y-3">
            {Object.entries(stats.genre_distribution)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([genre, count]) => (
                <div key={genre} className="flex items-center justify-between">
                  <span className="text-gray-700">{genre}</span>
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
      </div>
    </div>
  );
}
