import { Tag, Play, Clock, AlertCircle, CheckCircle, History, Download, Trash2 } from 'lucide-react';
import { TagDisplay } from '../../components/TagDisplay';
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
  onCleanup?: () => void;
  highlightProcessed?: boolean;
  onExportHistory?: () => void;
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
  onCleanup,
  highlightProcessed = false,
  onExportHistory,
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
                <p className={`text-2xl font-bold text-green-600 transition-all duration-300 ${
                  highlightProcessed ? 'scale-125 text-yellow-400' : ''
                }`}>
                  {status.processed}
                </p>
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
          <div className="flex items-center gap-2">
            {onCleanup && !isGenerating && (
              <button onClick={onCleanup} className="btn btn-secondary">
                <Trash2 className="h-4 w-4 mr-1" />
                清理孤儿
              </button>
            )}
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
            {historyTotal > 0 && onExportHistory && (
              <button
                onClick={onExportHistory}
                className="ml-4 flex items-center text-sm text-primary-600 hover:text-primary-700"
              >
                <Download className="h-4 w-4 mr-1" />
                导出
              </button>
            )}
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
          <div className="overflow-y-auto pr-2 space-y-3 max-h-[570px]">
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
