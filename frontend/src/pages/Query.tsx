import { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';
import { queryApi, asApiResponse } from '../api/client';
import { TagDisplay } from '../components/TagDisplay';
import type { Song, QueryRequest } from '../types';

export default function Query() {
  const [filters, setFilters] = useState<QueryRequest>({});
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tagOptions, setTagOptions] = useState<{
    moods: string[];
    energies: string[];
    genres: string[];
    styles: string[];
    scenes: string[];
    regions: string[];
    cultures: string[];
    languages: string[];
  } | null>(null);

  useEffect(() => {
    loadTagOptions();
  }, []);

  const loadTagOptions = async () => {
    try {
      const response = await queryApi.getTagOptions();
      const responseData = asApiResponse<{
        moods: string[];
        energies: string[];
        genres: string[];
        styles: string[];
        scenes: string[];
        regions: string[];
        cultures: string[];
        languages: string[];
      }>(response);
      if (responseData.success && responseData.data) {
        setTagOptions(responseData.data);
      }
    } catch (err) {
      console.error('加载标签选项失败:', err);
    }
  };

  const handleQuery = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await queryApi.querySongs(filters);
      const responseData = asApiResponse<Song[]>(response);
      if (responseData.success && responseData.data) {
        setSongs(responseData.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFilters({});
    setSongs([]);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">歌曲查询</h1>
        <p className="text-gray-600 mt-1">根据语义标签搜索音乐库中的歌曲</p>
      </div>

      {/* 筛选器 */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Filter className="h-5 w-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold">筛选条件</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {tagOptions && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  情绪
                </label>
                <select
                  value={filters.mood || ''}
                  onChange={(e) => setFilters({ ...filters, mood: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.moods.map((mood) => (
                    <option key={mood} value={mood}>{mood}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  能量
                </label>
                <select
                  value={filters.energy || ''}
                  onChange={(e) => setFilters({ ...filters, energy: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.energies.map((energy) => (
                    <option key={energy} value={energy}>{energy}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  流派
                </label>
                <select
                  value={filters.genre || ''}
                  onChange={(e) => setFilters({ ...filters, genre: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.genres.map((genre) => (
                    <option key={genre} value={genre}>{genre}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风格
                </label>
                <select
                  value={filters.style || ''}
                  onChange={(e) => setFilters({ ...filters, style: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.styles.map((style) => (
                    <option key={style} value={style}>{style}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  场景
                </label>
                <select
                  value={filters.scene || ''}
                  onChange={(e) => setFilters({ ...filters, scene: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.scenes.map((scene) => (
                    <option key={scene} value={scene}>{scene}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  地区
                </label>
                <select
                  value={filters.region || ''}
                  onChange={(e) => setFilters({ ...filters, region: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.regions.map((region) => (
                    <option key={region} value={region}>{region}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  文化
                </label>
                <select
                  value={filters.culture || ''}
                  onChange={(e) => setFilters({ ...filters, culture: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.cultures.map((culture) => (
                    <option key={culture} value={culture}>{culture}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  语言
                </label>
                <select
                  value={filters.language || ''}
                  onChange={(e) => setFilters({ ...filters, language: e.target.value || undefined })}
                  className="input"
                >
                  <option value="">全部</option>
                  {tagOptions.languages.map((language) => (
                    <option key={language} value={language}>{language}</option>
                  ))}
                </select>
              </div>
            </>
          )}
        </div>
        <div className="mt-4 flex gap-3">
          <button
            onClick={handleQuery}
            disabled={loading}
            className="btn btn-primary"
          >
            <Search className="h-4 w-4 mr-2 inline" />
            查询
          </button>
          <button
            onClick={handleReset}
            className="btn btn-secondary"
          >
            重置
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* 查询结果 */}
      {songs.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">查询结果</h2>
            <span className="text-sm text-gray-500">共 {songs.length} 首</span>
          </div>
          <div className="max-h-[600px] overflow-y-auto pr-2 space-y-3 scroll-smooth">
            {songs.map((song) => (
              <div
                key={song.file_id}
                className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{song.title}</h3>
                    <p className="text-sm text-gray-600">
                      {song.artist} · {song.album}
                    </p>
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
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">置信度</p>
                    <p className="text-sm font-medium text-gray-700">
                      {(song.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {!loading && songs.length === 0 && !error && (
        <div className="text-center py-12 text-gray-500">
          <Search className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>选择筛选条件后点击查询按钮</p>
        </div>
      )}
    </div>
  );
}
