import { Tag, TestTube, CheckCircle2 } from 'lucide-react';

interface TaggingTabsProps {
  activeTab: 'batch' | 'test' | 'validation';
  setActiveTab: (tab: 'batch' | 'test' | 'validation') => void;
}

export default function TaggingTabs({ activeTab, setActiveTab }: TaggingTabsProps) {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8">
        <button
          onClick={() => setActiveTab('batch')}
          className={`flex items-center px-1 py-2 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'batch'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <Tag className="h-4 w-4 mr-2" />
          批量生成
        </button>
        <button
          onClick={() => setActiveTab('test')}
          className={`flex items-center px-1 py-2 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'test'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <TestTube className="h-4 w-4 mr-2" />
          标签测试
        </button>
        <button
          onClick={() => setActiveTab('validation')}
          className={`flex items-center px-1 py-2 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'validation'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <CheckCircle2 className="h-4 w-4 mr-2" />
          标签验证
        </button>
      </nav>
    </div>
  );
}

