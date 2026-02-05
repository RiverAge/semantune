import { useState, useEffect } from 'react';
import { Copy, AlertCircle, Music, Disc, FileText, RefreshCw, AlertTriangle } from 'lucide-react';
import { duplicateApi } from '../api/client';
import type { AllDuplicatesResponse } from '../types';

export default function Duplicate() {
  const [data, setData] = useState<AllDuplicatesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'songs' | 'albums' | 'songs-in-album'>('all');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadDuplicates();
  }, []);

  const loadDuplicates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await duplicateApi.getAllDuplicates();
      if (response.success && response.data) {
        setData(response.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载重复检测数据失败');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  };

  const renderDuplicateSongs = () => {
    if (!data || data.duplicate_songs.total_groups === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Music className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p>没有检测到重复歌曲</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {data.duplicate_songs.duplicates.map((group, idx) => {
          const groupId = `song-${idx}`;
          const isExpanded = expandedItems.has(groupId);
          return (
            <div key={idx} className="card">
              <div
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-4 rounded-lg"
                onClick={() => toggleExpand(groupId)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-gray-600">文件大小: {formatSize(group.size)}</p>
                      <p className="font-semibold text-gray-900">{group.count} 个重复文件</p>
                    </div>
                  </div>
                </div>
                <span className="text-2xl text-gray-400">{isExpanded ? '▼' : '▶'}</span>
              </div>
              {isExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  {group.songs.map((song, songIdx) => (
                    <div key={songIdx} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">{song.title}</p>
                          <p className="text-sm text-gray-600 truncate">
                            {song.artist} - {song.album}
                          </p>
                        </div>
                        <button
                          onClick={() => copyToClipboard(song.path)}
                          className="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-gray-700 ml-2"
                          title="复制路径"
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                      </div>
                      <p className="text-xs text-gray-400 font-mono truncate">{song.id}</p>
                      <p className="text-xs text-gray-400 truncate">{song.path}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderDuplicateAlbums = () => {
    if (!data || data.duplicate_albums.total_groups === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Disc className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p>没有检测到重复专辑</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {data.duplicate_albums.duplicates.map((group, idx) => {
          const groupId = `album-${idx}`;
          const isExpanded = expandedItems.has(groupId);
          return (
            <div key={idx} className="card">
              <div
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-4 rounded-lg"
                onClick={() => toggleExpand(groupId)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                    <div>
                      <p className="font-semibold text-gray-900">{group.album}</p>
                      <p className="text-sm text-gray-600">{group.album_artist}</p>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    <span>{group.count} 个专辑</span>
                    <span>共 {group.total_songs} 首歌</span>
                  </div>
                </div>
                <span className="text-2xl text-gray-400">{isExpanded ? '▼' : '▶'}</span>
              </div>
              {isExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  {group.albums.map((album, albumIdx) => (
                    <div key={albumIdx} className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-medium text-gray-900">专辑 ID: {album.id}</p>
                          <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                            <span>年份: {album.min_year} - {album.max_year}</span>
                            <span>歌曲数: {album.song_count}</span>
                            {album.date && <span>发布日期: {album.date}</span>}
                          </div>
                        </div>
                        <button
                          onClick={() => copyToClipboard(album.id)}
                          className="p-1 hover:bg-gray-200 rounded text-gray-500 hover:text-gray-700 ml-2"
                          title="复制专辑ID"
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderDuplicateSongsInAlbum = () => {
    if (!data || data.duplicate_songs_in_album.total_groups === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <p>没有检测到专辑内重复歌曲</p>
          <p className="text-sm mt-2">相同路径的文件没有重复</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {data.duplicate_songs_in_album.duplicates.map((group, idx) => {
          const groupId = `path-${idx}`;
          const isExpanded = expandedItems.has(groupId);
          return (
            <div key={idx} className="card">
              <div
                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-4 rounded-lg"
                onClick={() => toggleExpand(groupId)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">{group.path}</p>
                      <p className="text-sm text-red-600 mt-1">
                        检测到 {group.count} 条相同的路径记录（数据库脏数据）
                      </p>
                    </div>
                  </div>
                </div>
                <span className="text-2xl text-gray-400">{isExpanded ? '▼' : '▶'}</span>
              </div>
              {isExpanded && (
                <div className="px-4 pb-4 space-y-2">
                  {group.songs.map((song, songIdx) => (
                    <div key={songIdx} className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <div>
                        <p className="font-medium text-gray-900">{song.title}</p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                          <span>专辑: {song.album}</span>
                          <span>艺术家: {song.album_artist}</span>
                          <button
                            onClick={() => copyToClipboard(song.id)}
                            className="p-1 hover:bg-red-200 rounded text-gray-500 hover:text-gray-700"
                            title="复制歌曲ID"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">重复检测</h1>
          <p className="text-gray-600 mt-1">检测 Navidrome 数据库中的重复项</p>
        </div>
        <button
          onClick={loadDuplicates}
          disabled={loading}
          className="btn btn-primary flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          {error}
        </div>
      )}

      {/* 加载状态 */}
      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* 统计摘要 */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Music className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">重复歌曲组</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.summary.duplicate_song_groups}
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">基于文件大小检测</p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <Disc className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">重复专辑组</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.summary.duplicate_album_groups}
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">同艺术家同名专辑</p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <FileText className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">专辑内重复</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.summary.duplicate_songs_in_album_groups}
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">相同路径重复</p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${data.summary.total_issues > 0 ? 'bg-red-100' : 'bg-gray-100'}`}>
                <AlertTriangle className={`h-6 w-6 ${data.summary.total_issues > 0 ? 'text-red-600' : 'text-gray-600'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-600">总问题数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.summary.total_issues}
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">需要清理的问题</p>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            onClick={() => setActiveTab('all')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'all'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            全部
          </button>
          <button
            onClick={() => setActiveTab('songs')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'songs'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            重复歌曲 ({data?.summary.duplicate_song_groups || 0})
          </button>
          <button
            onClick={() => setActiveTab('albums')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'albums'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            重复专辑 ({data?.summary.duplicate_album_groups || 0})
          </button>
          <button
            onClick={() => setActiveTab('songs-in-album')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'songs-in-album'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            专辑内重复 ({data?.summary.duplicate_songs_in_album_groups || 0})
          </button>
        </nav>
      </div>

      {/* 内容区域 */}
      <div className="max-h-[600px] overflow-y-auto scroll-smooth pr-2">
        {activeTab === 'songs' && renderDuplicateSongs()}
        {activeTab === 'albums' && renderDuplicateAlbums()}
        {activeTab === 'songs-in-album' && renderDuplicateSongsInAlbum()}
        {activeTab === 'all' && (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Music className="h-5 w-5" />
                重复歌曲
              </h3>
              {renderDuplicateSongs()}
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Disc className="h-5 w-5" />
                重复专辑
              </h3>
              {renderDuplicateAlbums()}
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FileText className="h-5 w-5" />
                专辑内重复
              </h3>
              {renderDuplicateSongsInAlbum()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
