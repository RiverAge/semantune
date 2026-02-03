import { useState } from 'react';
import { TestTube, AlertCircle, CheckCircle } from 'lucide-react';
import { taggingApi } from '../../api/client';

interface TagTestProps {
  onTestSuccess: () => void;
}

export default function TagTest({ onTestSuccess }: TagTestProps) {
  const [testTitle, setTestTitle] = useState('夜曲');
  const [testArtist, setTestArtist] = useState('周杰伦');
  const [testAlbum, setTestAlbum] = useState('十一月的肖邦');
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testSuccessMessage, setTestSuccessMessage] = useState<string | null>(null);

  const handleTestTag = async () => {
    if (!testTitle || !testArtist) {
      setTestError('请输入歌曲标题和歌手名称');
      return;
    }

    try {
      setIsTesting(true);
      setTestError(null);
      setTestResult(null);

      const response = await taggingApi.testTag(testTitle, testArtist, testAlbum);
      if (response.data) {
        setTestResult(response.data);
        setTestSuccessMessage('标签生成成功');
        setTimeout(() => setTestSuccessMessage(null), 3000);
        onTestSuccess();
      }
    } catch (err) {
      setTestError(err instanceof Error ? err.message : '标签生成失败');
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <>
      {/* 测试表单 */}
      <div className="card">
        <div className="flex items-center mb-4">
          <TestTube className="h-5 w-5 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold">输入歌曲信息</h2>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">歌曲标题 *</label>
              <input
                type="text"
                value={testTitle}
                onChange={(e) => setTestTitle(e.target.value)}
                placeholder="例如：晴天"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">歌手名称 *</label>
              <input
                type="text"
                value={testArtist}
                onChange={(e) => setTestArtist(e.target.value)}
                placeholder="例如：周杰伦"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">专辑名称</label>
              <input
                type="text"
                value={testAlbum}
                onChange={(e) => setTestAlbum(e.target.value)}
                placeholder="例如：叶惠美"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
          <button
            onClick={handleTestTag}
            disabled={isTesting || !testTitle || !testArtist}
            className="btn btn-primary"
          >
            {isTesting ? '生成中...' : '测试标签生成'}
          </button>
        </div>
      </div>

      {/* 成功提示 */}
      {testSuccessMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center">
          <CheckCircle className="h-5 w-5 mr-2" />
          {testSuccessMessage}
        </div>
      )}

      {/* 错误提示 */}
      {testError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          {testError}
        </div>
      )}

      {/* 测试结果 */}
      {testResult && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">生成结果</h2>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-gray-900">
                {testResult.artist} - {testResult.title}
              </span>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                情绪: {testResult.tags.mood || 'N/A'}
              </span>
              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                能量: {testResult.tags.energy || 'N/A'}
              </span>
              <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                流派: {testResult.tags.genre || 'N/A'}
              </span>
              <span className="px-2 py-1 bg-pink-100 text-pink-700 text-xs rounded-full">
                场景: {testResult.tags.scene || 'N/A'}
              </span>
              <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
                地区: {testResult.tags.region || 'N/A'}
              </span>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                亚文化: {testResult.tags.subculture || 'N/A'}
              </span>
              {testResult.tags.confidence && (
                <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded-full">
                  置信度: {(testResult.tags.confidence * 100).toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
