import { useState } from 'react';
import { TestTube, AlertCircle, CheckCircle } from 'lucide-react';
import { TagDisplay } from '../../components/TagDisplay';
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
            <div className="mb-3">
              <span className="font-medium text-gray-900">
                {testResult.artist} - {testResult.title}
              </span>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
              {testResult.tags.mood && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">情绪:</span>
                  <TagDisplay value={testResult.tags.mood} emptyLabel="N/A" />
                </div>
              )}
              {testResult.tags.energy && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">能量:</span>
                  <span className="text-green-700 font-medium">{testResult.tags.energy}</span>
                </div>
              )}
              {testResult.tags.genre && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">流派:</span>
                  <TagDisplay value={testResult.tags.genre} emptyLabel="N/A" />
                </div>
              )}
              {testResult.tags.style && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">风格:</span>
                  <TagDisplay value={testResult.tags.style} emptyLabel="N/A" />
                </div>
              )}
              {testResult.tags.scene && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">场景:</span>
                  <TagDisplay value={testResult.tags.scene} emptyLabel="N/A" />
                </div>
              )}
              {testResult.tags.region && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">地区:</span>
                  <span className="text-gray-700">{testResult.tags.region}</span>
                </div>
              )}
              {testResult.tags.culture && testResult.tags.culture !== 'None' && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">文化:</span>
                  <span className="text-gray-700">{testResult.tags.culture}</span>
                </div>
              )}
              {testResult.tags.language && testResult.tags.language !== 'None' && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">语言:</span>
                  <span className="text-gray-700">{testResult.tags.language}</span>
                </div>
              )}
              {testResult.tags.confidence && (
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-xs">置信度:</span>
                  <span className="text-gray-700">{(testResult.tags.confidence * 100).toFixed(1)}%</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
