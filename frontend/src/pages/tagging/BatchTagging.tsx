import { Tag, Play, Clock, AlertCircle, CheckCircle, History } from 'lucide-react';
import { taggingApi } from '../../api/client';
import type { TaggingStatus } from '../../types';

interface BatchTaggingProps {
  status: TaggingStatus | null;
  isGenerating: boolean;
  config: { model: string };
  history: any[];
  historyTotal: number;
  historyLimit: number;
  historyOffset: number;
  error: string | null;
  successMessage: string | null;
  onStartTagging: () => void;
  onStopTagging: () => void;
  onLoadHistory: () => void;
  onHistoryOffsetChange: (offset: number) => void;
}

export default function BatchTagging({
  status,
  isGenerating,
  config,
  history,
  historyTotal,
  historyLimit,
  historyOffset,
  error,
  successMessage,
  onStartTagging,
  onStopTagging,
  onLoadHistory,
  onHistoryOffsetChange,
}: BatchTaggingProps) {
  return (
    <>
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
              使用 {config.model} 模型为未标签的歌曲生成语义标签
            </p>
          </div>
          {isGenerating ? (
            <button onClick={onStopTagging} className="btn btn-danger">
              中止
            </button>
          ) : (
            <button
              onClick={onStartTagging}
              disabled={status?.pending === 0}
              className="btn btn-primary"
            >
              开始生成
            </button>
          )}
        </div>
      </div>

      {/* 成功提示 */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center">
          <CheckCircle className="h-5 w-5 mr-2" />
          {successMessage}
        </div>
      )}

      {/* 历史记录 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <History className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold">标记历史</h2>
            <span className="ml-2 text-sm text-gray-500">({historyTotal} 条记录)</span>
          </div>
          {historyOffset > 0 && (
            <button
              onClick={() => {
                onHistoryOffsetChange(Math.max(0, historyOffset - historyLimit));
                onLoadHistory();
              }}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              上一页
            </button>
          )}
          {historyOffset + historyLimit < historyTotal && (
            <button
              onClick={() => {
                onHistoryOffsetChange(historyOffset + historyLimit);
                onLoadHistory();
              }}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              下一页
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无标记记录</div>
        ) : (
          <div className="overflow-y-auto pr-2 space-y-3 max-h-[calc(100vh-500px)]">
            {history.map((item, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="font-medium text-gray-900">
                    {item.artist} - {item.title}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(item.updated_at).toLocaleString('zh-CN')}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                    {item.tags.mood || 'N/A'}
                  </span>
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                    {item.tags.energy || 'N/A'}
                  </span>
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                    {item.tags.genre || 'N/A'}
                  </span>
                  <span className="px-2 py-0.5 bg-pink-100 text-pink-700 text-xs rounded-full">
                    {item.tags.scene || 'N/A'}
                  </span>
                  <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                    {item.tags.region || 'N/A'}
                  </span>
                  <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                    {item.tags.subculture || 'N/A'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          {error}
        </div>
      )}
    </>
  );
}
