import { Settings } from 'lucide-react';

interface TaggingHeaderProps {
  onResetConfig: () => void;
}

export default function TaggingHeader({ onResetConfig }: TaggingHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">语义标签生成</h1>
        <p className="text-gray-600 mt-1">使用 LLM 为音乐库中的歌曲生成语义标签</p>
      </div>
      <button
        onClick={onResetConfig}
        className="text-sm text-gray-500 hover:text-primary-600 flex items-center"
      >
        <Settings className="h-4 w-4 mr-1" />
        重新配置
      </button>
    </div>
  );
}
