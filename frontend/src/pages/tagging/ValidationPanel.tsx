import { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw, BarChart3, FileText } from 'lucide-react';
import { validationApi } from '../../api/client';
import type { ValidationStats, InvalidSong } from '../../types';
import { TagDisplay } from '../../components/TagDisplay';

export default function ValidationPanel() {
  const [stats, setStats] = useState<ValidationStats | null>(null);
  const [invalidSongs, setInvalidSongs] = useState<InvalidSong[]>([]);
  const [totalInvalid, setTotalInvalid] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const [loading, setLoading] = useState(true);
  const [revalidating, setRevalidating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    try {
      const response = await validationApi.getStats();
      setStats(response.data);
    } catch (err) {
      console.error('加载验证统计失败:', err);
      setError(err instanceof Error ? err.message : '加载验证统计失败');
    }
  };

  const loadInvalidSongs = async () => {
    try {
      setLoading(true);
      const response = await validationApi.getInvalidSongs(limit, offset);
      setInvalidSongs(response.data);
      setTotalInvalid(response.total);
    } catch (err) {
      console.error('加载无效歌曲失败:', err);
      setError(err instanceof Error ? err.message : '加载无效歌曲失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRevalidate = async (fileId: string, title: string) => {
    try {
      setRevalidating(fileId);
      const response = await validationApi.revalidateSong(fileId);
      
      if (response.success && response.is_valid) {
        loadStats();
        loadInvalidSongs();
      }
    } catch (err) {
      console.error('重新验证失败:', err);
      setError(err instanceof Error ? err.message : '重新验证失败');
    } finally {
      setRevalidating(null);
    }
  };

  useEffect(() => {
    loadStats();
    loadInvalidSongs();
  }, [offset]);

  const getHealthColor = (rate: number) => {
    if (rate >= 99) return 'text-green-600';
    if (rate >= 95) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总歌曲</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-gray-600" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">有效</p>
                <p className="text-2xl font-bold text-green-600">{stats.valid}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">无效</p>
                <p className="text-2xl font-bold text-red-600">{stats.invalid}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">合规率</p>
                <p className={`text-2xl font-bold ${getHealthColor(stats.valid_rate)}`}>
                  {stats.valid_rate.toFixed(1)}%
                </p>
              </div>
              <BarChart3 className={`h-8 w-8 ${getHealthColor(stats.valid_rate)}`} />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">违规维度</p>
                <p className="text-2xl font-bold text-orange-600">
                  {Object.keys(stats.invalid_by_dimension).length}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-600" />
            </div>
          </div>
        </div>
      )}

      {/* 按维度统计 */}
      {stats && stats.invalid > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-3">违规标签分布</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.invalid_by_dimension).map(([dimension, count]) => (
              <span
                key={dimension}
                className="inline-flex items-center px-3 py-1 bg-red-50 border border-red-200 rounded-full text-sm text-red-700"
              >
                <span className="font-medium">{dimension}:</span>
                <span className="ml-1 font-bold">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 无效歌曲列表 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <XCircle className="h-5 w-5 text-red-600 mr-2" />
            <h2 className="text-lg font-semibold">无效标签歌曲</h2>
            {totalInvalid > 0 && (
              <span className="ml-2 text-sm text-gray-500">({totalInvalid} 条)</span>
            )}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : invalidSongs.length === 0 ? (
          <div className="text-center py-8 text-green-600 flex items-center justify-center">
            <CheckCircle2 className="h-6 w-6 mr-2" />
            <span>所有歌曲标签均符合白名单规范</span>
          </div>
        ) : (
          <>
            <div className="overflow-y-auto pr-2 space-y-3 max-h-[570px]">
              {invalidSongs.map((item) => (
                <div key={item.file_id} className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900">
                          {item.artist} - {item.title}
                        </span>
                        <XCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                      </div>
                      <div className="text-xs text-gray-600 mb-2">
                        专辑: {item.album} | 置信度: {item.confidence.toFixed(2)} | 
                        {new Date(item.updated_at).toLocaleString('zh-CN')}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRevalidate(item.file_id, item.title)}
                      disabled={revalidating === item.file_id}
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-md text-sm transition-colors"
                    >
                      <RefreshCw className={`h-4 w-4 ${revalidating === item.file_id ? 'animate-spin' : ''}`} />
                      重新验证
                    </button>
                  </div>

                  {/* 无效标签 */}
                  <div className="mb-3 p-2 bg-red-100 rounded-md">
                    <div className="text-xs font-semibold text-red-700 mb-1">违规标签:</div>
                    <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
                      {Object.entries(item.invalid_tags).map(([dimension, tags]) => (
                        <div key={dimension} className="flex items-start gap-1">
                          <span className="text-red-600 font-medium">{dimension}:</span>
                          <span className="text-red-700">
                            {Array.isArray(tags) ? tags.join(', ') : tags}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 当前标签 */}
                  <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
                    {item.tags.mood && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">情绪:</span>
                        <TagDisplay value={item.tags.mood} emptyLabel="N/A" />
                      </div>
                    )}
                    {item.tags.energy && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">能量:</span>
                        <span className="text-green-700 font-medium">{item.tags.energy}</span>
                      </div>
                    )}
                    {item.tags.genre && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">流派:</span>
                        <TagDisplay value={item.tags.genre} emptyLabel="N/A" />
                      </div>
                    )}
                    {item.tags.style && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">风格:</span>
                        <TagDisplay value={item.tags.style} emptyLabel="N/A" />
                      </div>
                    )}
                    {item.tags.scene && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">场景:</span>
                        <TagDisplay value={item.tags.scene} emptyLabel="N/A" />
                      </div>
                    )}
                    {item.tags.region && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">地区:</span>
                        <span className="text-gray-700">{item.tags.region}</span>
                      </div>
                    )}
                    {item.tags.culture && item.tags.culture !== 'None' && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">文化:</span>
                        <span className="text-gray-700">{item.tags.culture}</span>
                      </div>
                    )}
                    {item.tags.language && item.tags.language !== 'None' && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-400 text-xs">语言:</span>
                        <span className="text-gray-700">{item.tags.language}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 分页 */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-gray-500">
                显示 {offset + 1} - {Math.min(offset + limit, totalInvalid)} / 共 {totalInvalid} 条
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                  disabled={offset === 0}
                  className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-300 rounded-md text-sm transition-colors"
                >
                  上一页
                </button>
                <button
                  onClick={() => setOffset(offset + limit)}
                  disabled={offset + limit >= totalInvalid}
                  className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-300 rounded-md text-sm transition-colors"
                >
                  下一页
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
          <XCircle className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}
    </div>
  );
}
