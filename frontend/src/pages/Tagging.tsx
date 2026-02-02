import { useState, useEffect } from 'react';
import { Tag, Play, Clock, AlertCircle, Eye } from 'lucide-react';
import { taggingApi } from '../api/client';
import type { TaggingStatus, TaggingPreview } from '../types';

export default function Tagging() {
  const [status, setStatus] = useState<TaggingStatus | null>(null);
  const [previews, setPreviews] = useState<TaggingPreview[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    loadStatus();
    loadPreviews();
  }, []);

  const loadStatus = async () => {
    try {
      const response = await taggingApi.getStatus();
      if (response.success && response.data) {
        setStatus(response.data);
      }
    } catch (err) {
      console.error('加载状态失败:', err);
    }
  };

  const loadPreviews = async () => {
    try {
      const response = await taggingApi.previewTagging(5);
      if (response.success && response.data) {
        setPreviews(response.data);
      }
    } catch (err) {
      console.error('加载预览失败:', err);
    }
  };

  const handleStartTagging = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      const response = await taggingApi.startTagging();
      if (response.success) {
        // 开始轮询状态
        const interval = setInterval(async () => {
          await loadStatus();
        }, 2000);
        // 5分钟后停止轮询
        setTimeout(() => clearInterval(interval), 300000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动标签生成失败');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">语义标签生成</h1>
        <p className="text-gray-600 mt-1">使用 LLM 为音乐库中的歌曲生成语义标签</p>
      </div>

      {/* 状态卡片 */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总歌曲数</p>
                <p className="text-2xl font-bold">{status.total}</p>
              </div>
              <Tag className="h-8 w-8 text-primary-600" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">已处理</p>
                <p className="text-2xl font-bold text-green-600">{status.processed}</p>
              </div>
              <Play className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">待处理</p>
                <p className="text-2xl font-bold text-orange-600">{status.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </div>
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">失败</p>
                <p className="text-2xl font-bold text-red-600">{status.failed}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
          </div>
        </div>
      )}

      {/* 进度条 */}
      {status && status.total > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">处理进度</span>
            <span className="text-sm text-gray-600">{status.progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-primary-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${status.progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">开始生成标签</h3>
            <p className="text-sm text-gray-600 mt-1">
              使用 NVIDIA Llama-3.3-70B 模型为未标签的歌曲生成语义标签
            </p>
          </div>
          <button
            onClick={handleStartTagging}
            disabled={isGenerating || (status && status.pending === 0)}
            className="btn btn-primary"
          >
            {isGenerating ? '生成中...' : '开始生成'}
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* 标签预览 */}
      {previews.length > 0 && (
        <div className="card">
          <div className="flex items-center mb-4">
            <Eye className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold">标签生成预览</h2>
          </div>
          <div className="space-y-4">
            {previews.map((preview, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-medium text-gray-900">{preview.title}</h3>
                    <p className="text-sm text-gray-600">{preview.artist}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">情绪</p>
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                      {preview.tags.mood}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">能量</p>
                    <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                      {preview.tags.energy}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">流派</p>
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                      {preview.tags.genre}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">场景</p>
                    <span className="px-2 py-1 bg-pink-100 text-pink-700 text-xs rounded-full">
                      {preview.tags.scene}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">地区</p>
                    <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
                      {preview.tags.region}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">亚文化</p>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                      {preview.tags.subculture}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
