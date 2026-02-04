import { useState, useEffect } from 'react';
import { FileText, RefreshCw, Filter, X, Search, AlertCircle } from 'lucide-react';
import { logsApi } from '../api/client';
import type { LogFileInfo, LogLine } from '../types';

export default function Logs() {
  const [logFiles, setLogFiles] = useState<LogFileInfo[]>([]);
  const [selectedLog, setSelectedLog] = useState<string | null>(null);
  const [logContent, setLogContent] = useState<LogLine[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalLines, setTotalLines] = useState(0);
  
  // 过滤选项
  const [filterLevel, setFilterLevel] = useState<string>('');
  const [tailLines, setTailLines] = useState(100);
  const [useHead, setUseHead] = useState(false);
  
  // 自动刷新
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadLogFiles();
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, []);

  useEffect(() => {
    if (autoRefresh && selectedLog) {
      loadLogContent();
      
      const interval = setInterval(() => {
        loadLogContent();
      }, 3000);
      
      setRefreshInterval(interval);
      
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, selectedLog]);

  const loadLogFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await logsApi.listLogs() as any;
      if (response.success && response.data) {
        setLogFiles(response.data);
      }
    } catch (err: any) {
      setError(err.message || '加载日志列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadLogContent = async () => {
    if (!selectedLog) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await logsApi.getLogContent(
        selectedLog,
        useHead ? undefined : tailLines,
        useHead ? tailLines : undefined,
        filterLevel || undefined
      ) as any;
      
      if (response.success && response.data) {
        setLogContent(response.data.lines);
        setTotalLines(response.data.total_lines);
      }
    } catch (err: any) {
      setError(err.message || '加载日志内容失败');
    } finally {
      setLoading(false);
    }
  };

  const handleLogSelect = (fileName: string) => {
    setSelectedLog(fileName);
    setLogContent([]);
    setError(null);
  };

  const applyFilter = () => {
    loadLogContent();
  };

  const clearFilter = () => {
    setFilterLevel('');
    setTailLines(100);
    setUseHead(false);
    if (selectedLog) {
      loadLogContent();
    }
  };

  const getLevelColor = (level: string | null) => {
    switch (level?.toUpperCase()) {
      case 'DEBUG': return 'text-gray-500';
      case 'INFO': return 'text-blue-600';
      case 'WARNING': return 'text-yellow-600';
      case 'ERROR': return 'text-red-600';
      case 'CRITICAL': return 'text-red-800 font-bold';
      default: return 'text-gray-600';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <FileText className="h-6 w-6 mr-2" />
          日志查看
        </h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={loadLogFiles}
            disabled={loading}
            className="flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新列表
          </button>
          {selectedLog && (
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center px-4 py-2 border rounded-md text-sm font-medium ${
                autoRefresh
                  ? 'border-green-500 text-green-700 bg-green-50'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
              {autoRefresh ? '自动刷新中' : '自动刷新'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 日志文件列表 */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">日志文件</h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
              {logFiles.map((file) => (
                <button
                  key={file.name}
                  onClick={() => handleLogSelect(file.name)}
                  className={`w-full text-left p-3 rounded-md border transition-colors ${
                    selectedLog === file.name
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium">{file.name}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatFileSize(file.size)} · {file.lines} 行
                  </div>
                </button>
              ))}
              {logFiles.length === 0 && !loading && (
                <div className="text-center text-gray-500 py-8">
                  暂无日志文件
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 日志内容 */}
        <div className="lg:col-span-3">
          {!selectedLog ? (
            <div className="card">
              <div className="flex items-center justify-center h-64 text-gray-500">
                <Search className="h-8 w-8 mr-3" />
                请选择一个日志文件查看内容
              </div>
            </div>
          ) : (
            <div className="card flex flex-col">
              {/* 过滤器 */}
              <div className="border-b border-gray-200 p-4 space-y-3 shrink-0">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm font-medium text-gray-700">过滤级别:</label>
                    <select
                      value={filterLevel}
                      onChange={(e) => setFilterLevel(e.target.value)}
                      className="input text-sm w-32"
                    >
                      <option value="">全部</option>
                      <option value="DEBUG">DEBUG</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <label className="text-sm font-medium text-gray-700">行数:</label>
                    <input
                      type="number"
                      value={tailLines}
                      onChange={(e) => setTailLines(Number(e.target.value))}
                      min={1}
                      max={10000}
                      className="input text-sm w-24"
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="useHead"
                      checked={useHead}
                      onChange={(e) => setUseHead(e.target.checked)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <label htmlFor="useHead" className="text-sm text-gray-700">
                      读取前N行
                    </label>
                  </div>

                  <button
                    onClick={applyFilter}
                    className="btn btn-primary text-sm"
                  >
                    <Filter className="h-4 w-4 mr-1" />
                    应用
                  </button>
                  
                  <button
                    onClick={clearFilter}
                    className="btn btn-secondary text-sm"
                  >
                    <X className="h-4 w-4 mr-1" />
                    清除
                  </button>

                  <button
                    onClick={loadLogContent}
                    disabled={loading}
                    className="btn btn-secondary text-sm"
                  >
                    <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                    刷新
                  </button>
                </div>

                <div className="text-sm text-gray-500">
                  文件: {selectedLog} · 总行数: {totalLines} · 
                  显示: {logContent.length} 行{filterLevel ? ' (已过滤)' : ''}
                </div>
              </div>

              {/* 日志内容列表 */}
              <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
                {loading && logContent.length === 0 ? (
                  <div className="flex items-center justify-center py-12">
                    <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
                  </div>
                ) : logContent.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    暂无日志内容
                  </div>
                ) : (
                  <div className="space-y-1 font-mono text-sm">
                    {logContent.map((log) => (
                      <div
                        key={log.line_number}
                        className="flex hover:bg-gray-50 rounded px-2 py-0.5"
                      >
                        <span className="text-gray-400 w-16 flex-shrink-0">
                          {log.line_number}
                        </span>
                        {log.timestamp && (
                          <span className="text-gray-400 w-24 flex-shrink-0">
                            {log.timestamp}
                          </span>
                        )}
                        {log.level && (
                          <span className={`w-10 flex-shrink-0 ${getLevelColor(log.level)}`}>
                            {log.level}
                          </span>
                        )}
                        {log.module && (
                          <span className="text-gray-400 w-20 flex-shrink-0">
                            {log.module}
                          </span>
                        )}
                        <span className="flex-1 text-gray-700 break-all">
                          {log.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}