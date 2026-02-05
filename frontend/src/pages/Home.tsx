import { useState, useEffect } from 'react';
import {
  Sparkles,
  Search,
  Target,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { analyzeApi, asApiResponse } from '../api/client';
import type { AnalysisStats, HealthData } from '../types';

export default function Home() {
  const [stats, setStats] = useState<AnalysisStats | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsResponse, healthResponse] = await Promise.all([
        analyzeApi.getStats(),
        analyzeApi.getHealth()
      ]);

      const statsData = asApiResponse<AnalysisStats>(statsResponse);
      const healthData = asApiResponse<HealthData>(healthResponse);
      if (statsData.success && statsData.data) {
        setStats(statsData.data);
      }
      if (healthData.success && healthData.data) {
        setHealth(healthData.data);
      }
      // @ts-expect-error response.data type issue
      if (healthResponse.success && healthResponse.data) {
        // @ts-expect-error type mismatch
        setHealth(healthResponse.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const getHealthIcon = (level: string) => {
    switch (level) {
      case 'excellent':
        return <CheckCircle2 className="h-8 w-8 text-green-600" />;
      case 'good':
        return <CheckCircle2 className="h-8 w-8 text-blue-600" />;
      case 'warning':
        return <AlertCircle className="h-8 w-8 text-yellow-600" />;
      case 'error':
        return <XCircle className="h-8 w-8 text-red-600" />;
      default:
        return <AlertCircle className="h-8 w-8 text-gray-600" />;
    }
  };

  const getHealthColor = (level: string) => {
    switch (level) {
      case 'excellent':
        return 'bg-green-50 border-green-200';
      case 'good':
        return 'bg-blue-50 border-blue-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getHealthTextColor = (level: string) => {
    switch (level) {
      case 'excellent':
        return 'text-green-700';
      case 'good':
        return 'text-blue-700';
      case 'warning':
        return 'text-yellow-700';
      case 'error':
        return 'text-red-700';
      default:
        return 'text-gray-700';
    }
  };

  const quickActions = [
    {
      title: '生成标签',
      description: '为未标签的歌曲生成语义标签',
      icon: Sparkles,
      count: stats?.untagged_songs || 0,
      link: '/tagging',
      color: 'from-purple-500 to-purple-600',
      borderColor: 'border-purple-200',
    },
    {
      title: '获取推荐',
      description: '基于你的偏好获取个性化推荐',
      icon: Target,
      count: 0,
      link: '/recommend',
      color: 'from-green-500 to-green-600',
      borderColor: 'border-green-200',
    },
    {
      title: '检测重复',
      description: '检查数据库中的重复项',
      icon: AlertTriangle,
      count: health?.duplicate_count || 0,
      link: '/duplicate',
      color: 'from-red-500 to-red-600',
      borderColor: 'border-red-200',
    },
    {
      title: '搜索歌曲',
      description: '根据语义标签搜索音乐',
      icon: Search,
      count: 0,
      link: '/query',
      color: 'from-blue-500 to-blue-600',
      borderColor: 'border-blue-200',
    },
  ];

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
          onClick={loadData}
          className="mt-4 btn btn-primary flex items-center gap-2 mx-auto"
        >
          <RefreshCw className="h-4 w-4" />
          重试
        </button>
      </div>
    );
  }

  if (!stats || !health) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* 欢迎横幅 - 简化版 */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1">欢迎回来</h1>
            <p className="text-blue-100">Navidrome+ 智能增强平台</p>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
          >
            <RefreshCw className={`h-4 w-4`} />
            刷新
          </button>
        </div>
      </div>

      {/* 健康度概览 - 核心指标 */}
      {health && (
        <div className={`border-2 rounded-lg p-6 ${getHealthColor(health.health_level)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-4 rounded-full bg-white ${getHealthColor(health.health_level).split(' ')[1]}`}>
                {getHealthIcon(health.health_level)}
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">系统健康度</h2>
                <p className={`text-sm ${getHealthTextColor(health.health_level)}`}>
                  {health.health_level === 'excellent' && '优秀 - 系统运行良好'}
                  {health.health_level === 'good' && '良好 - 系统状态正常'}
                  {health.health_level === 'warning' && '警告 - 存在需要关注的问题'}
                  {health.health_level === 'error' && '错误 - 需要立即处理'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-4xl font-bold text-gray-900">{health.health_score}</p>
              <p className="text-sm text-gray-500">健康分</p>
            </div>
          </div>

          {/* 健康度详情 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">标签覆盖率</span>
                <span className={`font-bold ${health.tag_coverage >= 80 ? 'text-green-600' : health.tag_coverage >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {health.tag_coverage}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${health.tag_coverage >= 80 ? 'bg-green-500' : health.tag_coverage >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${health.tag_coverage}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-400 mt-2">{health.tagged_songs} / {health.total_songs} 首已标签</p>
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">平均置信度</span>
                <span className={`font-bold ${health.average_confidence >= 0.8 ? 'text-green-600' : health.average_confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {(health.average_confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${health.average_confidence >= 0.8 ? 'bg-green-500' : health.average_confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${health.average_confidence * 100}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-400 mt-2">AI 标签质量分数</p>
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">重复项数量</span>
                <span className={`font-bold ${health.duplicate_count === 0 ? 'text-green-600' : health.duplicate_count <= 5 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {health.duplicate_count}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {health.duplicate_count === 0 ? (
                  <span className="text-xs text-green-600">✓ 无重复</span>
                ) : (
                  <span className="text-xs text-yellow-600">需要处理</span>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-2">
                歌曲: {health.issues.duplicate_songs} | 专辑: {health.issues.duplicate_albums} | 路径: {health.issues.duplicate_songs_in_album}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 快速操作 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-900">快速操作</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <a
                key={action.title}
                href={action.link}
                className={`card group hover:shadow-lg transition-all duration-200 cursor-pointer border-2 ${action.borderColor}`}
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${action.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
                  {action.title}
                </h4>
                <p className="text-sm text-gray-600 mb-2">{action.description}</p>
                {action.count > 0 && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                    {action.count}
                  </span>
                )}
                <div className="flex items-center text-sm text-primary-600 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>开始</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </div>
              </a>
            );
          })}
        </div>
      </div>

      {/* 统计卡片 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-900">数据统计</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总歌曲数</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_songs}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <span className="text-2xl">🎵</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">已标签歌曲</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.tagged_songs}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <span className="text-2xl">🏷️</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">标签覆盖率</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {stats.tag_coverage.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <span className="text-2xl">📊</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">未标签歌曲</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.untagged_songs}</p>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <span className="text-2xl">⏳</span>
              </div>
            </div>
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
              .slice(0, 5)
              .map(([mood, count]) => (
                <div key={mood} className="flex items-center justify-between">
                  <span className="text-gray-700">{mood}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
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
